@echo off
setlocal
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\install-policy.ps1" Account
set "rc=%errorlevel%"
pause
exit /b %rc%
