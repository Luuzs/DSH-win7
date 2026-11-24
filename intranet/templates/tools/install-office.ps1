$ErrorActionPreference = 'Stop'
try {
    $role=New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    if (!$role.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Run as administrator.' }
    $kit=Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
    $root=Join-Path $kit 'office'
    $files=@('LibreOffice_25.2.7.2_Win_x86-64.msi','LibreOffice_25.2.7.2_Win_x86-64_helppack_zh-CN.msi')
    $hashes=@('9fdd22f8ea7a92a67de5beaa08588ef6da58c1930ac86fd57c46b0c6d7ca9d34','392845402229abe0026685f7a2e0e9b1d7669d301813549a0847de98b04a8805')
    $restart=$false
    for($i=0;$i -lt $files.Length;$i++){
        $file=Join-Path $root $files[$i]
        $stream=[IO.File]::OpenRead($file);$alg=[Security.Cryptography.SHA256]::Create()
        try {$hash=[BitConverter]::ToString($alg.ComputeHash($stream)).Replace('-','')} finally {$stream.Dispose();$alg.Clear()}
        if($hash -ne $hashes[$i]){throw 'Office package checksum mismatch.'}
        $options=('/i "{0}" /qn /norestart /L*v "{1}"' -f $file,(Join-Path $env:TEMP ("DSH-office-" + $i + ".log")))
        if($i -eq 0){$options+=' UI_LANGS=en_US,zh_CN ISCHECKFORPRODUCTUPDATES=0 REGISTER_NO_MSO_TYPES=1'}
        $p=Start-Process msiexec.exe -ArgumentList $options -PassThru -Wait
        if($p.ExitCode -eq 3010){$restart=$true} elseif($p.ExitCode -ne 0){throw ("Office MSI returned "+$p.ExitCode+"; see DSH-office logs under TEMP.")}
        Write-Host ("Installed " + $files[$i])
    }
    if(!(Test-Path (Join-Path $env:ProgramFiles 'LibreOffice\program\soffice.exe'))){throw 'Missing LibreOffice executable.'}
    if($restart){Write-Host 'Restart Windows after completing installation.'}
} catch {Write-Host $_.Exception.Message;exit 1}
