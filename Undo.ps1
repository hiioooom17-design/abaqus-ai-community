$ErrorActionPreference = 'Stop'
try {
    if (Get-Process -Name 'Claude' -ErrorAction SilentlyContinue) { throw 'Close Claude Desktop completely first.' }
    $root = Join-Path $env:LOCALAPPDATA 'AbaqusClaudeMCP'
    $state = Join-Path $root 'state'
    $receipts = @(Get-ChildItem -LiteralPath $state -Filter 'receipt-*.json' -ErrorAction Stop | Sort-Object Name)
    if ($receipts.Count -eq 0) { throw 'No undo receipt found.' }
    $info = Get-Content -LiteralPath $receipts[-1].FullName -Raw | ConvertFrom-Json
    $python = Join-Path $info.release '.venv\Scripts\python.exe'
    if (!(Test-Path -LiteralPath $python)) { throw 'Installed Python missing. Use the .before-abaqus-mcp-*.bak backups or restore manually.' }
    & $python (Join-Path $PSScriptRoot 'manager.py') undo --state $state
    exit $LASTEXITCODE
} catch {
    Write-Host ('FAILED: ' + $_.Exception.Message) -ForegroundColor Red
    exit 1
}
