@echo off
setlocal
cd /d "%~dp0"
if exist "Win7-Player\start-vm.ps1" goto boot
powershell.exe -NoProfile -Command "$ErrorActionPreference='Stop';$p=@(Get-ChildItem -LiteralPath . -Filter 'Win7-*.zip' -File);if($p.Count -ne 1){throw 'Keep the player zip beside this launcher'};$f=[IO.File]::OpenRead($p[0].FullName);$sha=[Security.Cryptography.SHA256]::Create();try{$actual=[BitConverter]::ToString($sha.ComputeHash($f)).Replace('-','')}finally{$f.Dispose();$sha.Dispose()};if($actual -ne '714fbb0cd309f10fa8bf8449bb3d9f9a7a207ff8ad8fcbc677e7f3fc69091204'){throw 'Player digest mismatch'};Add-Type -AssemblyName System.IO.Compression.FileSystem;$tmp=Join-Path (Get-Location).Path ([Guid]::NewGuid().ToString('N'));[IO.Compression.ZipFile]::ExtractToDirectory($p[0].FullName,$tmp);[IO.Directory]::Move((Join-Path $tmp 'Win7-Player'),(Join-Path (Get-Location).Path 'Win7-Player'));[IO.Directory]::Delete($tmp)"
if errorlevel 1 goto failed
:boot
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Win7-Player\start-vm.ps1"
if errorlevel 1 goto failed
exit /b 0
:failed
pause
exit /b 1
