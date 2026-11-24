@echo off
setlocal
if not "%~1"=="" goto custom
set "out=%USERPROFILE%\Documents\DSH-Office"
"%LOCALAPPDATA%\Programs\DSH-Win7\resources\runtime\primary-runtime\dependencies\python\python.exe" "%~dp0tools\make-documents.py" --out "%out%"
set "rc=%errorlevel%"
if "%rc%"=="0" start "" explorer.exe "%out%"
pause
exit /b %rc%
:custom
"%LOCALAPPDATA%\Programs\DSH-Win7\resources\runtime\primary-runtime\dependencies\python\python.exe" "%~dp0tools\make-documents.py" %*
exit /b %errorlevel%
