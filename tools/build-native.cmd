@echo off
setlocal
set "ROOT=%~dp0.."
set "KIT=%~1"
if not defined KIT set "KIT=%ROOT%\out\kit"
set "UPSTREAM=%~2"
if not defined UPSTREAM set "UPSTREAM=%ROOT%\dsh-win7"
if not exist "%KIT%\tools\network-policy.c" exit /b 2
for /f "usebackq tokens=*" %%i in (`"%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do set "VS=%%i"
if not defined VS if exist "%ProgramFiles(x86)%\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" set "VS=%ProgramFiles(x86)%\Microsoft Visual Studio\18\BuildTools"
if not defined VS exit /b 3
call "%VS%\VC\Auxiliary\Build\vcvars64.bat" >nul || exit /b 1
if not exist "%KIT%\native" mkdir "%KIT%\native"
pushd "%KIT%\native" || exit /b 1
cl /nologo /O2 /MD /W4 /DUNICODE /D_UNICODE /std:c11 "%KIT%\tools\network-policy.c" /Fe:network-policy.exe /link /SUBSYSTEM:CONSOLE,6.01 || exit /b 1
copy /y network-policy.exe "%KIT%\tools\network-policy.exe" >nul || exit /b 1
cl /nologo /O2 /MT /W4 /LD "%UPSTREAM%\shim\dshw7.c" /link /DEF:"%UPSTREAM%\shim\dshw7.def" /OUT:dshw7.dll /SUBSYSTEM:WINDOWS,6.01 kernel32.lib user32.lib bcrypt.lib version.lib winmm.lib shlwapi.lib || exit /b 1
popd
exit /b 0
