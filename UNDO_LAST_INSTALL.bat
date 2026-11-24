@echo off
setlocal
title Abaqus + Claude MCP - UNDO_LAST_INSTALL
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Undo.ps1" 
set "result=%ERRORLEVEL%"
echo.
pause
exit /b %result%
