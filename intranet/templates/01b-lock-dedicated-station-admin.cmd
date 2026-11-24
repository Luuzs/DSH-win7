@echo off
setlocal
echo Dedicated workstation only. All Windows accounts and services on this PC will be restricted.
echo Keep using the account installation on shared computers.
choice /c YN /n /m "Apply the dedicated workstation policy [Y/N]? "
if errorlevel 2 exit /b 1
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\install-policy.ps1" Station
set "rc=%errorlevel%"
pause
exit /b %rc%
