$ErrorActionPreference = 'Stop'
try {
    $root = $PSScriptRoot
    $manifestPath = Join-Path $root 'SHA256.json'
    if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) { throw 'SHA256 manifest missing.' }
    $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
    $count = 0
    foreach ($prop in $manifest.PSObject.Properties) {
        $path = Join-Path $root $prop.Name
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw ('Missing: ' + $prop.Name) }
        $actual = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actual -ne [string]$prop.Value) { throw ('Corrupt or modified: ' + $prop.Name) }
        $count += 1
    }
    foreach ($file in @('Setup.ps1', 'Select_Config.ps1', 'manager.py', 'INSTALL.bat', 'SELECT_CLAUDE_CONFIG.bat', 'CHECK_CONNECTION.bat')) {
        if (-not (Test-Path -LiteralPath (Join-Path $root $file) -PathType Leaf)) { throw ('Missing installer component: ' + $file) }
    }
    Write-Host ('PASS: ' + $count + ' payload SHA256 checks and installer entrypoints present.') -ForegroundColor Green
    $uv = Get-Command uv -ErrorAction SilentlyContinue
    if ($uv) { Write-Host ('uv available: ' + $uv.Source) } else { Write-Host 'NOTE: uv is not in PATH. The installer needs uv.' -ForegroundColor Yellow }
    if (Test-Path -LiteralPath 'C:\SIMULIA\Commands\abq2024.bat') { Write-Host 'Abaqus 2024 launcher found.' }
    else { Write-Host 'NOTE: Abaqus 2024 launcher not found at the configured path.' -ForegroundColor Yellow }
    Write-Host 'File verification only. Windows installation, Claude MCP handshake and Abaqus GUI are not tested here.' -ForegroundColor Yellow
    exit 0
} catch {
    Write-Host ('FAIL: ' + $_.Exception.Message) -ForegroundColor Red
    exit 1
}
