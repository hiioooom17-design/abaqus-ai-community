@echo off
setlocal
title Abaqus + Claude MCP - CHECK_CONNECTION
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Check.ps1" 
set "result=%ERRORLEVEL%"
echo.
pause
exit /b %result%
