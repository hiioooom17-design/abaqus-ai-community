@echo off
setlocal
title Abaqus MCP - Verify Files
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Verify_Files.ps1"
set "rc=%ERRORLEVEL%"
echo.
pause
exit /b %rc%
