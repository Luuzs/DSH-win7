"""Build the offline kit using an extracted, pinned upstream desktop and prerequisite media."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream,"sha256").hexdigest()

def assemble(kit, original, media, seven):
    policy=kit/"tools/network-policy.exe"
    if not policy.is_file():raise ValueError("Build network-policy.exe first")
    patch=kit/"tools/harden-app.py"
    spec=importlib.util.spec_from_file_location("intranet_build",patch)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    kit.mkdir(exist_ok=True,parents=True)
    payload=kit/"payload";payload.mkdir(exist_ok=True)
    official=json.loads((Path(__file__).resolve().parents[1]/"media.lock.json").read_text(encoding="utf-8"))
    for name, expected in official.items():
        src=media/name
        if sha(src)!=expected:raise ValueError(f"Media checksum mismatch: {name}")
        target=kit/name;target.parent.mkdir(exist_ok=True,parents=True)
        if src.resolve()!=target.resolve():shutil.copyfile(src,target)
    with tempfile.TemporaryDirectory(dir=kit.parent) as work:
        desktop=Path(work)/"desktop"
        shutil.copytree(original,desktop)
        module.harden(desktop)
        files={key:sha(desktop/key) for key in ["DeepSeek Harness.exe","resources/app.asar"]}
        (kit/"tools/patched-files.json").write_text(json.dumps(files,indent=2),encoding="ascii")
        packed=Path(work)/"DSH-Intranet-win7-x64.exe"
        subprocess.run([str(seven/"7z.exe"),"a","-t7z","-sfx"+str(seven/"7z.sfx"),"-mx=5","-mmt=4","-ms=64m",str(packed),"."],cwd=desktop,check=True)
        subprocess.run([str(seven/"7z.exe"),"t",str(packed)],check=True)
        os.replace(packed,payload/packed.name)
    items=sorted([*(p for p in payload.glob("*.msu")),payload/"vc_redist.x64.exe",payload/"DSH-Intranet-win7-x64.exe"])
    (payload/"SHA256SUMS").write_bytes("".join(f"{sha(p)}  {p.name}\r\n" for p in items).encode("ascii"))

if __name__=="__main__":
    root=Path(__file__).resolve().parents[1]
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kit",type=Path,default=root/"out/kit")
    parser.add_argument("--original",type=Path,required=True)
    parser.add_argument("--media",type=Path,required=True,help="Offline kit root containing original payload/ and office/ media")
    parser.add_argument("--seven",type=Path,default=Path(os.environ.get("ProgramFiles","."))/"7-Zip")
    args=parser.parse_args()
    assemble(*(p.resolve() for p in [args.kit,args.original,args.media,args.seven]))
