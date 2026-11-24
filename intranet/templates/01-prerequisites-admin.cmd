@echo off
setlocal
set "PS=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if defined PROCESSOR_ARCHITEW6432 set "PS=%SystemRoot%\Sysnative\WindowsPowerShell\v1.0\powershell.exe"
"%PS%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\setup.ps1" Prerequisites
set "rc=%errorlevel%"
if "%rc%"=="3010" echo Restart Windows and run this step again.
if not "%rc%"=="0" echo Exit code %rc%
pause
exit /b %rc%
