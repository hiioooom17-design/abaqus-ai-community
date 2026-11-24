@echo off
setlocal
SET "SCRIPT="
TITLE Connect ABAQUS to Claude
if exist "%~dp0SELECT_CLAUDE_CONFIG.bat" set "SCRIPT=%~dp0SELECT_CLAUDE_CONFIG.bat"
if not defined SCRIPT if exist "%~dp0Abaqus_Claude_MCP_Installer\SELECT_CLAUDE_CONFIG.bat" set "SCRIPT=%~dp0Abaqus_Claude_MCP_Installer\SELECT_CLAUDE_CONFIG.bat"
if defined SCRIPT goto EXECUTE
echo ERROR: Required installer files were not found.
echo Extract the full Abaqus_Claude_MCP_2024_With_CONNECT.zip archive first.
echo This BAT is a shortcut to SELECT_CLAUDE_CONFIG.bat; it cannot configure Claude alone.
echo.
pause
exit /b 1
:EXECUTE
echo Opening Claude Desktop configuration selector for Abaqus...
call "%SCRIPT%"
exit /b %ERRORLEVEL%
