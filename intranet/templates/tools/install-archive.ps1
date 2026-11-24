$ErrorActionPreference='Stop'
try {
    $principal=New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    if (!$principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {throw 'Run as administrator.'}
    $kit=Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
    $src=Join-Path $kit 'office\7z2606-x64.exe'
    $f=[IO.File]::OpenRead($src);$alg=[Security.Cryptography.SHA256]::Create()
    try {$digest=[BitConverter]::ToString($alg.ComputeHash($f)).Replace('-','')} finally {$f.Close();$alg.Clear()}
    if ($digest -ne '9b697f65ecc2d9b0152f5ee96d72dde522a7827690349d9307935dacf40f42ec'){throw '7-Zip digest mismatch.'}
    $p=Start-Process -FilePath $src -ArgumentList '/S' -Wait -PassThru
    if ($p.ExitCode -ne 0 -or !(Test-Path "$env:ProgramFiles\7-Zip\7zFM.exe")){throw '7-Zip setup failed.'}
    Write-Host 'Installed 7-Zip 26.06 x64.'
} catch {Write-Host $_.Exception.Message;exit 1}
