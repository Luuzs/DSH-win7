param([ValidateSet('Verify','Prerequisites','Desktop','Graphics')][string]$Action = 'Verify')
$ErrorActionPreference = 'Stop'
$toolsDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$payload = Join-Path (Split-Path -Parent $toolsDir) 'payload'

function Check-Payload {
    foreach ($line in (Get-Content (Join-Path $payload 'SHA256SUMS'))) {
        if ($line -notmatch '^([0-9a-f]{64})  ([a-zA-Z0-9._-]+)$') { throw 'Invalid SHA256SUMS' }
        $expected = $matches[1]
        $name = $matches[2]
        $stream = [IO.File]::OpenRead((Join-Path $payload $name))
        $sha = [Security.Cryptography.SHA256]::Create()
        try { $actual = [BitConverter]::ToString($sha.ComputeHash($stream)).Replace('-','') }
        finally { $stream.Close(); $sha.Clear() }
        if ($expected -ne $actual) { throw "Checksum failed for $name" }
        Write-Host "Verified $name"
    }
}

function Is-Admin {
    $p = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Has-Hotfix($kb) {
    [bool](Get-HotFix -Id $kb -ErrorAction SilentlyContinue)
}

function Has-VC {
    $v = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64' -ErrorAction SilentlyContinue
    ($v -and $v.Installed -eq 1 -and ([version]($v.Version.TrimStart('v'))) -ge [version]'14.44.35211.0')
}

function Has-SHA2v3 {
    $manifest = "$env:windir\servicing\Packages\Package_for_KB4474419~31bf3856ad364e35~amd64~~6.1.3.2.mum"
    ((Test-Path $manifest) -and (Has-Hotfix 'KB4474419'))
}

function Update-Windows($file, $optionalIfSuperseded) {
    $path = Join-Path $payload $file
    Write-Host "Installing $file ..."
    $p = Start-Process "$env:windir\System32\wusa.exe" -ArgumentList ('"{0}" /quiet /norestart' -f $path) -Wait -PassThru
    $code = $p.ExitCode
    if ($code -eq 3010 -or $code -eq 1641) { Write-Host 'Restart Windows, then repeat this step.'; exit 3010 }
    if ($code -eq 0 -or $code -eq 2359302) { return }
    if ($code -eq -2145124329 -and $optionalIfSuperseded) { Write-Host 'Servicing update is not applicable; checking remaining prerequisites.'; return }
    throw ("WUSA {0} returned 0x{1:X8}. See Windows Logs / Setup." -f $file,$code)
}

try {
    Check-Payload
    if ($Action -eq 'Verify') { exit 0 }
    $os = Get-WmiObject Win32_OperatingSystem
    if ($os.BuildNumber -ne '7601' -or $os.ProductType -ne 1 -or [IntPtr]::Size -ne 8) { throw 'Requires Windows 7 SP1 x64 and 64-bit Windows PowerShell.' }
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class Win7Runtime {
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode)] static extern IntPtr GetModuleHandle(string name);
    [DllImport("kernel32.dll", CharSet=CharSet.Ansi, ExactSpelling=true)] static extern IntPtr GetProcAddress(IntPtr module, string name);
    public static bool Has(string module, string name) { return GetProcAddress(GetModuleHandle(module), name) != IntPtr.Zero; }
}
'@
    if ($Action -ne 'Desktop' -and !(Is-Admin)) { throw 'Run this step as administrator.' }
    if ($Action -eq 'Graphics') {
        if (!(Has-Hotfix 'KB2670838')) { Update-Windows 'KB2670838.msu' $false }
        exit 0
    }
    if ($Action -eq 'Prerequisites') {
        if (![Win7Runtime]::Has('kernel32.dll','AddDllDirectory')) { Update-Windows 'KB3063858.msu' $false }
        if (!(Has-SHA2v3) -and !(Has-Hotfix 'KB4490628')) { Update-Windows 'KB4490628.msu' $true }
        if (!(Has-SHA2v3)) { Update-Windows 'KB4474419-v3.msu' ([Win7Runtime]::Has('advapi32.dll','EventSetInformation')) }
        if (!(Test-Path "$env:windir\System32\ucrtbase.dll")) { Update-Windows 'KB2999226.msu' $false }
        if (!(Has-VC)) {
            $vc = Start-Process (Join-Path $payload 'vc_redist.x64.exe') -ArgumentList '/install /quiet /norestart' -Wait -PassThru
            if ($vc.ExitCode -eq 3010) { Write-Host 'Restart Windows, then repeat this step.'; exit 3010 }
            if ($vc.ExitCode -ne 0 -and !(Has-VC)) { throw "VC++ setup returned $($vc.ExitCode)" }
        }
    }
    if (![Win7Runtime]::Has('kernel32.dll','AddDllDirectory') -or ![Win7Runtime]::Has('advapi32.dll','EventSetInformation') -or !(Test-Path "$env:windir\System32\ucrtbase.dll") -or !(Has-VC)) {
        throw 'Required runtime is missing. Complete step 01 and restart Windows.'
    }
    if ($Action -eq 'Prerequisites') { Write-Host 'Prerequisites OK. Complete the network-policy step before installing the desktop.'; exit 0 }
    $policy = Join-Path $env:ProgramFiles 'DSH Intranet Policy\network-policy.exe'
    if (!(Test-Path -LiteralPath $policy)) { throw 'Install the network policy with step 01b first.' }
    $policyMessage = & $policy verify 2>&1
    $policyExit = $LASTEXITCODE
    Write-Host ($policyMessage -join [Environment]::NewLine)
    if ($policyExit -ne 0) { throw 'Network policy verification failed. Use the designated Windows account.' }
    $installDir = Join-Path $env:LOCALAPPDATA 'Programs\DSH-Win7'
    $app = Join-Path $installDir 'DeepSeek Harness.exe'
    $installer = Join-Path $payload 'DSH-Intranet-win7-x64.exe'
    $stage = $installDir + '.new-' + [Guid]::NewGuid().ToString('N')
    $install = Start-Process $installer -ArgumentList ('-y -o"{0}"' -f $stage) -Wait -PassThru
    if ($install.ExitCode -ne 0 -or !(Test-Path -LiteralPath (Join-Path $stage 'DeepSeek Harness.exe')) -or (Test-Path (Join-Path $stage 'resources\app-update.yml'))) { throw 'Incomplete offline desktop extraction.' }
    $backup = $installDir + '.old-' + [Guid]::NewGuid().ToString('N')
    if (Test-Path -LiteralPath $installDir) { [IO.Directory]::Move($installDir,$backup) }
    try { [IO.Directory]::Move($stage,$installDir) } catch {
        if (Test-Path -LiteralPath $backup) { [IO.Directory]::Move($backup,$installDir) }
        throw
    }
    if (Test-Path -LiteralPath $backup) { Remove-Item -LiteralPath $backup -Recurse -Force }
    $homeDir = Join-Path $env:USERPROFILE '.dsh-intranet-win7'
    if (!(Test-Path $homeDir)) { [IO.Directory]::CreateDirectory($homeDir) | Out-Null }
    $patch = Join-Path $homeDir 'cordis.patch.yml'
    if (Test-Path -LiteralPath $patch) { Copy-Item -LiteralPath $patch ($patch + '.before-intranet-' + [Guid]::NewGuid().ToString('N')) }
    & (Join-Path $toolsDir 'render-profile.ps1') $toolsDir
    Copy-Item (Join-Path $toolsDir 'start-intranet.cmd') $homeDir -Force
    (Get-Item -LiteralPath (Join-Path $homeDir 'start-intranet.cmd')).IsReadOnly=$false
    Copy-Item (Join-Path (Split-Path -Parent $toolsDir) '06-create-documents.cmd') (Join-Path $homeDir 'make-documents.cmd') -Force
    (Get-Item -LiteralPath (Join-Path $homeDir 'make-documents.cmd')).IsReadOnly=$false
    $officeWorkspace=Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'DSH-Office'
    [IO.Directory]::CreateDirectory($officeWorkspace) | Out-Null
    $guide=Join-Path $officeWorkspace 'AGENTS.md'
    if (!(Test-Path -LiteralPath $guide)) { Copy-Item (Join-Path $toolsDir 'office-workspace.md') $guide; (Get-Item -LiteralPath $guide).IsReadOnly=$false }
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut((Join-Path ([Environment]::GetFolderPath('DesktopDirectory')) 'DSH Intranet.lnk'))
    $shortcut.TargetPath = Join-Path $homeDir 'start-intranet.cmd'
    $shortcut.WorkingDirectory = $env:USERPROFILE
    $shortcut.IconLocation = $app + ',0'
    $shortcut.Save()
    $docShortcut=$shell.CreateShortcut((Join-Path ([Environment]::GetFolderPath('DesktopDirectory')) 'DSH Office Files.lnk'))
    $docShortcut.TargetPath=Join-Path $homeDir 'make-documents.cmd'
    $docShortcut.WorkingDirectory=$env:USERPROFILE
    $docShortcut.Save()
    Write-Host 'Desktop installed. Open the DSH Intranet desktop shortcut.'
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host $_.InvocationInfo.PositionMessage
    exit 1
}
exit 0
