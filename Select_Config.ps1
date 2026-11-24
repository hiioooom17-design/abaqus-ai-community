$ErrorActionPreference = 'Stop'
try {
    Add-Type -AssemblyName System.Windows.Forms
    if (Get-Process -Name 'Claude' -ErrorAction SilentlyContinue) { throw 'Close Claude Desktop including the tray icon first.' }
    $dialog = New-Object System.Windows.Forms.OpenFileDialog
    $dialog.Title = 'Choose claude_desktop_config.json from Claude Desktop > Edit Config'
    $dialog.Filter = 'Claude Desktop configuration|claude_desktop_config.json'
    $dialog.FileName = 'claude_desktop_config.json'
    $dialog.InitialDirectory = Join-Path $env:APPDATA 'Claude'
    if ($dialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) { throw 'Selection cancelled; nothing changed.' }
    if ([IO.Path]::GetFileName($dialog.FileName) -ine 'claude_desktop_config.json') { throw 'Please select the exact Claude config filename.' }
    & (Join-Path $PSScriptRoot 'Setup.ps1') -Mode desktop -ConfigPath $dialog.FileName
    exit $LASTEXITCODE
} catch {
    Write-Host ('FAILED: ' + $_.Exception.Message) -ForegroundColor Red
    exit 1
}
