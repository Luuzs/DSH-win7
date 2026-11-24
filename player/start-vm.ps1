param([string]$OvaPath)
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $root
$state=Join-Path $root 'state'
[IO.Directory]::CreateDirectory($state)|Out-Null
$guard=[IO.File]::Open((Join-Path $state 'player.lock'),'OpenOrCreate','ReadWrite','None')
try {
    if (!(Test-Path 'state\work.qcow2')) {
        if (!$OvaPath) {
            $items=@(Get-ChildItem -LiteralPath $root,(Split-Path -Parent $root) -Filter 'DSH-Win7*.ova' -File | Sort-Object FullName -Unique)
            if ($items.Count -eq 1) {$OvaPath=$items[0].FullName}
            else {
                Add-Type -AssemblyName System.Windows.Forms
                $picker=New-Object Windows.Forms.OpenFileDialog
                $picker.Title='Select the DSH Windows 7 appliance';$picker.Filter='OVF appliance (*.ova)|*.ova'
                if ($picker.ShowDialog() -ne [Windows.Forms.DialogResult]::OK){return}
                $OvaPath=$picker.FileName
            }
        }
        $OvaPath=(Resolve-Path -LiteralPath $OvaPath).Path
        $expected=(Get-Content -LiteralPath (Join-Path $root 'appliance.sha256') -TotalCount 1).Trim()
        $inputStream=[IO.File]::OpenRead($OvaPath)
        $hasher=[Security.Cryptography.SHA256]::Create()
        try {$actual=[BitConverter]::ToString($hasher.ComputeHash($inputStream)).Replace('-','')} finally {$inputStream.Dispose();$hasher.Dispose()}
        if ($actual -ne $expected){throw 'The OVA digest differs from this player release.'}
        & '.\extract\7z.exe' e -y -bso0 '-ostate' $OvaPath 'Win7-DSH-disk1.vmdk'
        if ($LASTEXITCODE -ne 0 -or !(Test-Path 'state\Win7-DSH-disk1.vmdk')){throw 'Cannot extract the base disk.'}
        Push-Location state
        try {
            & '..\qemu\qemu-img.exe' create -q -f qcow2 -F vmdk -b 'Win7-DSH-disk1.vmdk' 'first-boot.tmp'
            if ($LASTEXITCODE -ne 0){throw 'Cannot create the writable user disk.'}
            Move-Item -LiteralPath 'first-boot.tmp' -Destination 'work.qcow2'
        } finally {Pop-Location}
    }
    if (!(Test-Path -LiteralPath 'state\office-files.vhd')) {Copy-Item -LiteralPath 'exchange-template.vhd' -Destination 'state\office-files.vhd'}
    try {$bridge=[IO.File]::Open((Join-Path $state 'office-files.vhd'),'Open','ReadWrite','None');$bridge.Close()}
    catch {throw 'Eject the DSH-FILES exchange disk on the host before starting Windows 7.'}
    $settings=@('-name','DSH Win7','-L','qemu/share','-machine','pc,accel=tcg','-cpu','max','-smp','2','-m','3584',
        '-drive','file=state/work.qcow2,if=ide,index=0,format=qcow2','-drive','file=state/office-files.vhd,if=ide,index=1,format=vpc','-boot','order=c','-vga','std',
        '-usb','-device','usb-tablet','-nic','user,model=e1000,mac=52:54:00:20:26:72','-display','sdl',
        '-rtc','base=localtime','-monitor','none','-serial','none')
    & '.\qemu\qemu-system-x86_64.exe' @settings
    if ($LASTEXITCODE -ne 0){throw 'QEMU exited with an error. Check available memory and the console output.'}
} finally {$guard.Dispose()}
