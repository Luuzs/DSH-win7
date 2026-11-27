"""Package a source-built player against a specific appliance, excluding all user state."""
import argparse
import hashlib
from pathlib import Path
import re
import tempfile
import zipfile

def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def package(ova,media,out):
    root=Path(__file__).resolve().parent
    out.mkdir(exist_ok=True,parents=True)
    zipname='Win7-手动桌面播放器.zip';cmdname='双击打开Win7桌面.cmd'
    if (out/zipname).exists() or (out/cmdname).exists():raise FileExistsError('Select an empty output directory.')
    for name in ['qemu/qemu-system-x86_64.exe','qemu/qemu-img.exe','extract/7z.exe','extract/7z.dll','exchange-template.vhd']:
        if not (media/name).is_file():raise FileNotFoundError(name)
    with tempfile.TemporaryDirectory(dir=out) as stage:
        result=Path(stage)/zipname
        with zipfile.ZipFile(result,'w',zipfile.ZIP_DEFLATED,compresslevel=3) as z:
            for folder in ['qemu','extract']:
                for p in sorted((media/folder).rglob('*')):
                    if p.is_file() and p.name.lower() not in ['qemu-uninstall.exe','qemu-nbd.exe']:
                        z.write(p,'Win7-Player/'+p.relative_to(media).as_posix())
            for p in [root/'start-vm.ps1',root/'打开Win7桌面.cmd',media/'exchange-template.vhd']:
                z.write(p,'Win7-Player/'+p.name)
            if (media/'使用说明.txt').is_file():z.write(media/'使用说明.txt','Win7-Player/使用说明.txt')
            z.writestr('Win7-Player/appliance.sha256',digest(ova)+'\n')
        with zipfile.ZipFile(result) as z:
            failure=z.testzip()
            if failure:raise IOError(failure)
        launcher=(root/cmdname).read_bytes()
        launcher,count=re.subn(rb"(?<=actual -ne ')[a-f0-9]{64}(?=')",digest(result).encode(),launcher)
        if count!=1:raise ValueError('Launcher checksum field changed')
        result.rename(out/zipname)
        (out/cmdname).write_bytes(launcher)

if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('ova',type=Path);cli.add_argument('media',type=Path,help='Extracted Win7-Player media')
    cli.add_argument('output',type=Path)
    args=cli.parse_args();package(args.ova,args.media,args.output)
