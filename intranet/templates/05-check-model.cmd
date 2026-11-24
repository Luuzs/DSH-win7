@echo off
setlocal
"%LOCALAPPDATA%\Programs\DSH-Win7\resources\runtime\primary-runtime\dependencies\python\python.exe" "%~dp0tools\check-model.py"
set "rc=%errorlevel%"
if not "%rc%"=="0" echo Model check failed, exit code %rc%.
pause
exit /b %rc%
