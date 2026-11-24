param([ValidateSet('Account','Station')][string]$Mode)
$ErrorActionPreference = 'Stop'
try {
    $admin = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    if (!$admin.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Run as administrator.' }
    $os = Get-WmiObject Win32_OperatingSystem
    if ($os.BuildNumber -ne '7601' -or $os.ProductType -ne 1 -or [IntPtr]::Size -ne 8) { throw 'Requires Windows 7 SP1 x64.' }
    $source = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) 'network-policy.exe'
    $dir = Join-Path $env:ProgramFiles 'DSH Intranet Policy'
    [IO.Directory]::CreateDirectory($dir) | Out-Null
    $exe = Join-Path $dir 'network-policy.exe'
    Copy-Item -LiteralPath $source $exe -Force
    if ($Mode -eq 'Account') {
        $user = Get-WmiObject Win32_UserAccount -Filter "LocalAccount=True AND Name='DSHWork'"
        if (!$user) {
            Write-Host 'Set the password for the dedicated, standard DSHWork Windows account.'
            & net.exe user DSHWork '*' /add
            if ($LASTEXITCODE -ne 0) { throw 'Could not create the local account.' }
        } elseif (!(Test-Path (Join-Path $dir 'account.sid'))) { throw 'An unrelated DSHWork account already exists. Resolve the name collision before installation.' }
        $user = Get-WmiObject Win32_UserAccount -Filter "LocalAccount=True AND Name='DSHWork'"
        if (!$user) { throw 'Account lookup failed.' }
        $sidFile = Join-Path $dir 'account.sid'
        if ((Test-Path $sidFile) -and (([IO.File]::ReadAllText($sidFile)).Trim() -ne $user.SID)) { throw 'The account SID has changed.' }
        [IO.File]::WriteAllText($sidFile,$user.SID)
        & $exe install-account
    } else { & $exe install-station }
    if ($LASTEXITCODE -ne 0) { throw 'The firewall policy could not be installed.' }
    Write-Host 'Policy installed. Use step 02 in the designated Windows login.'
} catch { Write-Host $_.Exception.Message; exit 1 }
