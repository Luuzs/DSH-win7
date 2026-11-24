param([string]$ToolsDir)
$ErrorActionPreference='Stop'
$profileDir=Join-Path $env:USERPROFILE '.dsh-intranet-win7'
$installed=Join-Path $profileDir 'tools'
[IO.Directory]::CreateDirectory($installed) | Out-Null
$workspace=Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'DSH-Office'
[IO.Directory]::CreateDirectory($workspace) | Out-Null
foreach($name in @('make-documents.py','office-tool.py')){
    Copy-Item -LiteralPath (Join-Path $ToolsDir $name) -Destination $installed -Force
    (Get-Item -LiteralPath (Join-Path $installed $name)).IsReadOnly=$false
}
$python=Join-Path $env:LOCALAPPDATA 'Programs\DSH-Win7\resources\runtime\primary-runtime\dependencies\python\python.exe'
$server=Join-Path $installed 'office-tool.py'
$source=[IO.File]::ReadAllText((Join-Path $ToolsDir 'cordis.patch.yml'))
$source=$source.Replace('__OFFICE_PYTHON__',$python.Replace('\','\\')).Replace('__OFFICE_TOOL__',$server.Replace('\','\\')).Replace('__OFFICE_FOLDER__',$workspace.Replace('\','\\')).Replace('__OFFICE_LOCALAPPDATA__',$env:LOCALAPPDATA.Replace('\','\\'))
$target=Join-Path $profileDir 'cordis.patch.yml'
if(Test-Path -LiteralPath $target){(Get-Item -LiteralPath $target).IsReadOnly=$false}
[IO.File]::WriteAllText($target,$source,(New-Object Text.UTF8Encoding $false))
