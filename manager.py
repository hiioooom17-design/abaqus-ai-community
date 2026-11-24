"""Reversible Claude Desktop/Claude Code MCP registration for Abaqus-Control-MCP.

This module never launches Abaqus, executes CAE code, or contacts a remote host.
Run from Setup.ps1 after an isolated local environment has been prepared.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
import secrets
from pathlib import Path
import sys
import uuid

SERVER_KEY = 'abaqus_control_mcp'


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with temp.open('xb') as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def json_object(data: bytes | None) -> dict:
    if data is None:
        return {}
    raw = json.loads(data.decode('utf-8-sig'))
    if not isinstance(raw, dict):
        raise ValueError('Config must be a JSON object; no settings changed.')
    if 'mcpServers' in raw and not isinstance(raw['mcpServers'], dict):
        raise ValueError('mcpServers must be an object; no settings changed.')
    return raw


def backup_name(path: Path, uid: str) -> Path:
    return path.with_name(path.name + '.before-abaqus-mcp-' + uid + '.bak')


def assert_no_links(path: Path) -> None:
    for part in (path, *path.parents):
        if part.is_symlink():
            raise RuntimeError('Refusing to modify symlinked config/plugin paths: ' + str(part))


def install(*, app: Path, config: Path, plugin: Path, state: Path, mode: str) -> Path:
    app = app.resolve(strict=True)
    config, plugin, state = (p.absolute() for p in (config, plugin, state))
    for candidate in (config, plugin, state):
        assert_no_links(candidate)
    python = app / '.venv' / 'Scripts' / 'python.exe'
    if not python.is_file():
        raise FileNotFoundError('Isolated Windows Python was not installed: ' + str(python))
    gui_source = app / 'abaqus_mcp_bridge' / 'gui_plugin.py'
    if not gui_source.is_file():
        raise FileNotFoundError('GUI plugin missing: ' + str(gui_source))
    current_config = config.read_bytes() if config.exists() else None
    parsed = json_object(current_config)
    current_gui = plugin.read_bytes() if plugin.exists() else None
    uid = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-' + uuid.uuid4().hex[:8]
    token = secrets.token_hex(32)
    source = gui_source.read_bytes()
    marker = b"__INSTALL_TOKEN_PLACEHOLDER__"
    if source.count(marker) != 1:
        raise ValueError("GUI plugin authentication placeholder missing or duplicated")
    new_gui = source.replace(marker, token.encode("ascii"))
    server = {
        'command': str(python),
        'args': ['-u', '-m', 'abaqus_mcp_bridge'],
        'env': {'ABAQUS_MCP_HOST': '127.0.0.1', 'ABAQUS_MCP_PORT': '48152',
                'ABAQUS_MCP_TIMEOUT': '120', 'PYTHONUTF8': '1', 'ABAQUS_MCP_TOKEN': token},
    }
    parsed.setdefault('mcpServers', {})[SERVER_KEY] = server
    encoded = (json.dumps(parsed, indent=2, ensure_ascii=False) + '\n').encode('utf-8')
    receipt = {
        'id': uid, 'mode': mode, 'config': str(config), 'plugin': str(plugin),
        'release': str(app),
        'before_config_b64': None if current_config is None else base64.b64encode(current_config).decode(),
        'before_plugin_b64': None if current_gui is None else base64.b64encode(current_gui).decode(),
        'after_config_sha256': digest(encoded), 'after_plugin_sha256': digest(new_gui),
        'server_key': SERVER_KEY,
    }
    state.mkdir(parents=True, exist_ok=True)
    result = state / ('receipt-' + uid + '.json')
    config_backup = backup_name(config, uid) if current_config is not None else None
    plugin_backup = backup_name(plugin, uid) if current_gui is not None else None
    # An independent recovery receipt exists before either of the two writes.
    atomic_write(result, (json.dumps(receipt, indent=2) + '\n').encode())
    written = []
    try:
        if config_backup:
            atomic_write(config_backup, current_config)
        if plugin_backup:
            atomic_write(plugin_backup, current_gui)
        atomic_write(plugin, new_gui)
        written.append('plugin')
        atomic_write(config, encoded)
        written.append('config')
    except Exception:
        for what, previous, target in [('config', current_config, config), ('plugin', current_gui, plugin)]:
            if what in written:
                try:
                    if previous is None:
                        target.unlink(missing_ok=True)
                    else:
                        atomic_write(target, previous)
                except OSError:
                    pass
        # If a single write was partially interrupted, adjacent backups and
        # the receipt preserve recovery data. Do not silently remove the receipt.
        raise
    print('SUCCESS: Abaqus-Control-MCP registered for', mode)
    print('Claude configuration:', config)
    print('GUI plugin:', plugin)
    print('Server Python:', python)
    print('Backup receipt (PRIVATE; do not share):', result)
    print('Restart Abaqus/CAE and select Plug-ins > Abaqus-Control-MCP > Start MCP Bridge.')
    print('Restart Claude fully, then try ping.')
    return result


def restore_bytes(path: Path, encoded: str | None) -> None:
    if encoded is None:
        path.unlink(missing_ok=True)
    else:
        atomic_write(path, base64.b64decode(encoded, validate=True))


def undo(*, state: Path) -> Path:
    items = sorted(state.glob('receipt-*.json'))
    if not items:
        raise RuntimeError('No installation receipt found.')
    receipt_path = items[-1]
    receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
    config, plugin = Path(receipt['config']), Path(receipt['plugin'])
    assert_no_links(config)
    assert_no_links(plugin)
    if not config.is_file() or digest(config.read_bytes()) != receipt['after_config_sha256']:
        raise RuntimeError('Claude config changed after installation. Refusing automatic undo; use backup manually.')
    if not plugin.is_file() or digest(plugin.read_bytes()) != receipt['after_plugin_sha256']:
        raise RuntimeError('GUI plugin changed after installation. Refusing automatic undo; use backup manually.')
    restore_bytes(config, receipt['before_config_b64'])
    restore_bytes(plugin, receipt['before_plugin_b64'])
    receipt_path.rename(receipt_path.with_suffix('.undone'))
    print('UNDO SUCCESS: original Claude config and Abaqus GUI plugin restored.')
    print('Isolated application files and your Abaqus models were not removed.')
    return receipt_path


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='action', required=True)
    q = sub.add_parser('install')
    for arg in ('app', 'config', 'plugin', 'state'):
        q.add_argument('--' + arg, type=Path, required=True)
    q.add_argument('--mode', choices=['desktop', 'code'], required=True)
    q = sub.add_parser('undo')
    q.add_argument('--state', type=Path, required=True)
    a = p.parse_args()
    try:
        if a.action == 'install':
            install(app=a.app, config=a.config, plugin=a.plugin, state=a.state, mode=a.mode)
        else:
            undo(state=a.state)
        return 0
    except Exception as exc:
        print('FAILED:', type(exc).__name__ + ':', str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
