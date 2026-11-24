$ErrorActionPreference = 'Stop'
try {
    $candidate = 'C:\SIMULIA\Commands\abq2024.bat'
    if (!(Test-Path -LiteralPath $candidate -PathType Leaf)) { throw 'Abaqus 2024 launcher not found at C:\SIMULIA\Commands\abq2024.bat' }
    Write-Host 'Starting your installed licensed Abaqus/CAE 2024...'
    Write-Host 'When loaded, select Plug-ins > Abaqus-Control-MCP > Start MCP Bridge.'
    & $candidate cae
    exit $LASTEXITCODE
} catch {
    Write-Host ('FAILED: ' + $_.Exception.Message) -ForegroundColor Red
    exit 1
}
