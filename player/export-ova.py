"""Export a shut-down disk to the same stream-optimized OVA layout as the offline desktop."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile
import xml.etree.ElementTree as ET

def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def export(source,output,qemu):
    if output.exists():raise FileExistsError(output)
    with tempfile.TemporaryDirectory(dir=output.parent) as work:
        root=Path(work)
        disk=root/'Win7-DSH-disk1.vmdk'
        subprocess.run([qemu,'convert','-O','vmdk','-o','subformat=streamOptimized,adapter_type=ide,compat6',source,disk],check=True)
        subprocess.run([qemu,'compare',source,disk],check=True)
        desc=root/'Win7-DSH.ovf'
        n='http://schemas.dmtf.org/ovf/envelope/1'
        for event,(prefix,uri) in ET.iterparse(Path(__file__).with_name('desktop.ovf'),events=['start-ns']):
            ET.register_namespace(prefix,uri)
        tree=ET.parse(Path(__file__).with_name('desktop.ovf'))
        tree.find(f'.//{{{n}}}File').set(f'{{{n}}}size',str(disk.stat().st_size))
        size=json.loads(subprocess.check_output([qemu,'info','--output=json',disk]))['virtual-size']
        tree.find(f'.//{{{n}}}Disk').set(f'{{{n}}}capacity',str(size))
        tree.write(desc,encoding='utf-8',xml_declaration=True)
        manifest=root/'Win7-DSH.mf'
        manifest.write_text(''.join(f'SHA256({p.name})= {digest(p)}\n' for p in (desc,disk)),encoding='ascii')
        temp=root/'desktop.ova'
        with tarfile.open(temp,'w',format=tarfile.USTAR_FORMAT if disk.stat().st_size<8*1024**3 else tarfile.GNU_FORMAT) as ar:
            for p in [desc,manifest,disk]:ar.add(p,arcname=p.name)
        with tarfile.open(temp,'r') as ar:
            for p in [desc,manifest,disk]:
                with ar.extractfile(p.name) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==digest(p)
        os.replace(temp,output)
    output.with_suffix('.ova.sha256').write_text(f'{digest(output)}  {output.name}\n',encoding='ascii')

if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('source',type=Path);cli.add_argument('output',type=Path)
    cli.add_argument('--qemu-img',default='qemu-img')
    args=cli.parse_args();export(args.source.resolve(),args.output.resolve(),args.qemu_img)
