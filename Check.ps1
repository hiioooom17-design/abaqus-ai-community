$ErrorActionPreference = 'Stop'
try {
    $state = Join-Path $env:LOCALAPPDATA 'AbaqusClaudeMCP\state'
    $receipts = @(Get-ChildItem -LiteralPath $state -Filter 'receipt-*.json' -ErrorAction Stop | Sort-Object Name)
    if ($receipts.Count -eq 0) { throw 'No successful installation found. Run INSTALL.bat first.' }
    $info = Get-Content -LiteralPath $receipts[-1].FullName -Raw | ConvertFrom-Json
    $python = Join-Path $info.release '.venv\Scripts\python.exe'
    Write-Host ('Python: ' + $python)
    Write-Host ('Claude config: ' + $info.config)
    Write-Host ('Abaqus plugin: ' + $info.plugin)
    & $python -m abaqus_mcp_bridge.cli doctor
    if ($LASTEXITCODE -ne 0) { throw 'Static server check failed.' }
    Write-Host 'Checking running Abaqus/CAE bridge on localhost:48152...'
    $config = Get-Content -LiteralPath $info.config -Raw | ConvertFrom-Json
    $env:ABAQUS_MCP_TOKEN = $config.mcpServers.abaqus_control_mcp.env.ABAQUS_MCP_TOKEN
    try { & $python -m abaqus_mcp_bridge.cli check; $checkExit = $LASTEXITCODE }
    finally { Remove-Item Env:ABAQUS_MCP_TOKEN -ErrorAction SilentlyContinue }
    $LASTEXITCODE = $checkExit
    if ($LASTEXITCODE -ne 0) { throw 'Bridge not connected. Open Abaqus/CAE > Plug-ins > Abaqus-Control-MCP > Start MCP Bridge.' }
    Write-Host 'SUCCESS: local Abaqus bridge responded.' -ForegroundColor Green
    exit 0
} catch {
    Write-Host ('CHECK INCOMPLETE: ' + $_.Exception.Message) -ForegroundColor Yellow
    exit 1
}
