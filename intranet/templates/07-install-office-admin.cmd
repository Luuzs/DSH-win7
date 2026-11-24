@echo off
setlocal
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\install-office.ps1"
set "rc=%errorlevel%"
pause
exit /b %rc%
