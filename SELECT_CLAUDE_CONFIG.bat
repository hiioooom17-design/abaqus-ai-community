@echo off
setlocal
title Abaqus + Claude MCP - SELECT_CLAUDE_CONFIG
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Select_Config.ps1" 
set "result=%ERRORLEVEL%"
echo.
pause
exit /b %result%
