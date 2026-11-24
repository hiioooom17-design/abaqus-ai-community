param(
    [ValidateSet('desktop','code')][string]$Mode = 'desktop',
    [string]$ConfigPath = ''
)
$ErrorActionPreference = 'Stop'
try {
    if (-not [Environment]::Is64BitOperatingSystem) { throw '64-bit Windows is required.' }
    if (Get-Process -Name 'Claude' -ErrorAction SilentlyContinue) {
        throw 'Close Claude Desktop completely, including the system tray icon, and retry.'
    }
    $uv = Get-Command 'uv.exe' -ErrorAction SilentlyContinue
    if (-not $uv) { $uv = Get-Command 'uv' -ErrorAction SilentlyContinue }
    if (-not $uv) { throw 'uv is not in PATH. Open a fresh PowerShell window and confirm uv --version.' }
    $uvExe = $uv.Source
    $homePath = [Environment]::GetFolderPath('UserProfile')
    $root = Join-Path $env:LOCALAPPDATA 'AbaqusClaudeMCP'
    $state = Join-Path $root 'state'
    if (-not $ConfigPath) {
        if ($Mode -eq 'desktop') {
            $claudeDir = Join-Path $env:APPDATA 'Claude'
            if (-not (Test-Path -LiteralPath $claudeDir -PathType Container)) {
                throw 'No Claude Desktop config folder found. Launch Claude Desktop once or use SELECT_CLAUDE_CONFIG.bat.'
            }
            $ConfigPath = Join-Path $claudeDir 'claude_desktop_config.json'
        } else {
            $project = Join-Path $homePath 'abaqus-ai'
            if (-not (Test-Path -LiteralPath $project -PathType Container)) {
                throw 'Abaqus AI project folder not found. Expected: ' + $project
            }
            $ConfigPath = Join-Path $project '.mcp.json'
        }
    }
    $plugin = Join-Path $homePath 'abaqus_plugins\abaqus_mcp_gui_plugin.py'
    $id = [guid]::NewGuid().ToString('N')
    $release = Join-Path $root ('versions\' + $id)
    New-Item -ItemType Directory -Path $release -Force | Out-Null
    Write-Host 'Verifying source bundle hashes...'
    $manifest = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'SHA256.json') -Raw | ConvertFrom-Json
    foreach ($entry in $manifest.PSObject.Properties) {
        $file = Join-Path $PSScriptRoot $entry.Name
        if (!(Test-Path -LiteralPath $file -PathType Leaf)) { throw ('Missing package file: ' + $entry.Name) }
        $hash = (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($hash -ne $entry.Value) { throw ('Source integrity check failed: ' + $entry.Name) }
    }
    Copy-Item -Path (Join-Path $PSScriptRoot 'payload\app\*') -Destination $release -Recurse -Force
    Write-Host 'Creating separate Python 3.12 environment; this may download free packages once...'
    & $uvExe sync --project $release --python 3.12 --locked --no-dev
    if ($LASTEXITCODE -ne 0) { throw 'uv sync failed. No Claude configuration was changed.' }
    $python = Join-Path $release '.venv\Scripts\python.exe'
    if (!(Test-Path -LiteralPath $python -PathType Leaf)) { throw 'Python executable not found inside isolated environment.' }
    & $python -m abaqus_mcp_bridge.cli doctor
    if ($LASTEXITCODE -ne 0) { throw 'MCP server import validation failed. Claude settings were not changed.' }
    & $python (Join-Path $PSScriptRoot 'manager.py') install --app $release --config $ConfigPath --plugin $plugin --state $state --mode $Mode
    if ($LASTEXITCODE -ne 0) { throw 'MCP registration failed. Review error and backups; settings were not intentionally overwritten.' }
    Write-Host 'DONE. Restart Abaqus/CAE and Claude.' -ForegroundColor Green
    exit 0
} catch {
    Write-Host ('FAILED: ' + $_.Exception.Message) -ForegroundColor Red
    exit 1
}
