@echo off
setlocal
title Abaqus + Claude MCP - START_ABAQUS_2024
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start_Abaqus.ps1" 
set "result=%ERRORLEVEL%"
echo.
pause
exit /b %result%
