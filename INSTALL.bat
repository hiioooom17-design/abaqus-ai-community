@echo off
setlocal
title Abaqus + Claude MCP - INSTALL
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Setup.ps1" 
set "result=%ERRORLEVEL%"
echo.
pause
exit /b %result%
