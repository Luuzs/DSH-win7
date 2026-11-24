"""Check whether HEAD includes the exact archived Win7 port and expanded application trees."""
import json
from pathlib import Path
import subprocess

root=Path(__file__).resolve().parents[1]
def git(*args, data=None):
    return subprocess.check_output(["git","-C",str(root),*args],input=data)
lock=json.loads((root/"sources.lock.json").read_text())
port,harness=lock[:2]
tree=git("rev-parse","HEAD:"+harness["directory"].rstrip("/")).decode().strip()
if tree!=harness["git_tree"]:raise SystemExit("DSH application source tree differs from its pinned snapshot.")
records=git("ls-tree","-z","HEAD:"+port["directory"].rstrip("/")).split(b"\0")
for i,row in enumerate(records):
    if row.endswith(b"\tdeepseek-harness"):
        records[i]=b"160000 commit "+harness["commit"].encode()+b"\tdeepseek-harness"
restored=git("mktree","--missing","-z",data=b"\0".join(records)).decode().strip()
if restored!=port["git_tree"]:raise SystemExit("Win7 port differs from its pinned snapshot.")
print("Verified the Git trees of the full DSH application and Win7 port.")
