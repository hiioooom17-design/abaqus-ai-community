import base64
import json
import tempfile
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import manager


class ManagerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.app = self.root / 'app'
        (self.app / '.venv' / 'Scripts').mkdir(parents=True)
        (self.app / '.venv' / 'Scripts' / 'python.exe').write_bytes(b'not an executable - fixture')
        (self.app / 'abaqus_mcp_bridge').mkdir()
        (self.app / 'abaqus_mcp_bridge' / 'gui_plugin.py').write_bytes(b'bridge file __INSTALL_TOKEN_PLACEHOLDER__')
        self.config = self.root / 'Claude' / 'claude_desktop_config.json'
        self.plugin = self.root / 'abaqus_plugins' / 'abaqus_mcp_gui_plugin.py'
        self.state = self.root / 'receipts'

    def setup_content(self):
        self.config.parent.mkdir()
        self.config.write_text(json.dumps({'mcpServers': {
            'solidworks': {'command': 'existing'}, 'blender': {'command': 'original'}
        }, 'otherSetting': 4}), encoding='utf-8')
        self.plugin.parent.mkdir()
        self.plugin.write_bytes(b'original gui plugin')

    def install(self):
        return manager.install(app=self.app, config=self.config,
                               plugin=self.plugin, state=self.state, mode='desktop')

    def test_preserves_unrelated_servers_and_settings(self):
        self.setup_content()
        before = self.config.read_bytes()
        receipt_path = self.install()
        updated = json.loads(self.config.read_bytes())
        self.assertEqual(updated['mcpServers']['blender']['command'], 'original')
        self.assertEqual(updated['mcpServers']['solidworks']['command'], 'existing')
        self.assertEqual(updated['otherSetting'], 4)
        self.assertEqual(updated['mcpServers']['abaqus_control_mcp']['env']['ABAQUS_MCP_HOST'], '127.0.0.1')
        receipt = json.loads(receipt_path.read_text())
        self.assertEqual(base64.b64decode(receipt['before_config_b64']), before)
        token = updated['mcpServers']['abaqus_control_mcp']['env']['ABAQUS_MCP_TOKEN']
        self.assertRegex(token, r'^[0-9a-f]{64}$')
        self.assertEqual(self.plugin.read_bytes(), b'bridge file ' + token.encode())

    def test_undo_restores_exact_bytes(self):
        self.setup_content()
        before = self.config.read_bytes()
        original = self.plugin.read_bytes()
        self.install()
        manager.undo(state=self.state)
        self.assertEqual(self.config.read_bytes(), before)
        self.assertEqual(self.plugin.read_bytes(), original)
        self.assertEqual(len(list(self.state.glob('receipt-*.json'))), 0)

    def test_refuses_invalid_json_without_writing_plugin(self):
        self.config.parent.mkdir()
        self.config.write_text('{ broken json')
        with self.assertRaises(json.JSONDecodeError):
            self.install()
        self.assertFalse(self.plugin.exists())
        self.assertFalse(self.state.exists())

    def test_refuses_bad_mcp_servers_type(self):
        self.config.parent.mkdir()
        self.config.write_text('{"mcpServers": []}')
        with self.assertRaises(ValueError):
            self.install()
        self.assertFalse(self.plugin.exists())

    def test_new_config_new_plugin_undo_removes_only_ours(self):
        self.install()
        self.assertTrue(self.config.exists())
        self.assertTrue(self.plugin.exists())
        manager.undo(state=self.state)
        self.assertFalse(self.config.exists())
        self.assertFalse(self.plugin.exists())

    def test_undo_refuses_if_config_changed_after_install(self):
        self.setup_content()
        self.install()
        self.config.write_text(self.config.read_text() + '\n')
        with self.assertRaises(RuntimeError):
            manager.undo(state=self.state)
        self.assertTrue(self.config.exists())

    def test_undo_refuses_if_plugin_changed_after_install(self):
        self.setup_content()
        self.install()
        self.plugin.write_bytes(b'changed since install')
        with self.assertRaises(RuntimeError):
            manager.undo(state=self.state)
        self.assertTrue(self.plugin.exists())

    def test_reinstall_undo_is_last_in_first_out(self):
        self.setup_content()
        before = self.config.read_bytes()
        self.install()
        mid = self.config.read_bytes()
        self.install()
        manager.undo(state=self.state)
        self.assertEqual(self.config.read_bytes(), mid)
        manager.undo(state=self.state)
        self.assertEqual(self.config.read_bytes(), before)


if __name__ == '__main__':
    unittest.main(verbosity=2)
