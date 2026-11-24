@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\install-archive.ps1"
set "rc=%errorlevel%"
pause
exit /b %rc%
