@echo off
setlocal
title Abaqus + Claude MCP - INSTALL_CLAUDE_CODE
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Setup.ps1" -Mode code
set "result=%ERRORLEVEL%"
echo.
pause
exit /b %result%
