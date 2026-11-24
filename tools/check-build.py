"""Verify that the two built entry points contain the configured guard and valid JavaScript."""
import argparse
import ipaddress
from pathlib import Path
import subprocess

root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--ip',type=ipaddress.IPv4Address,required=True)
p.add_argument('--port',type=int,required=True)
p.add_argument('--node',default='node')
p.add_argument('--harness',type=Path,default=root/'dsh-win7/deepseek-harness')
args=p.parse_args()
h=args.harness
for file in [h/'apps/desktop/lib/main.js',h/'apps/desktop-host/lib/cli.js']:
    subprocess.run([args.node,'--check',str(file)],check=True)
    code=file.read_text(encoding='utf-8')
    for expected in ['DSH intranet destination denied','DSH Intranet Policy',str(args.ip),str(args.port)]:
        if expected not in code:raise SystemExit(f'{file.name} lacks the expected network control: {expected}')
if not (h/'apps/web/dist/index.html').is_file():raise SystemExit('Missing Web application build')
print('Verified desktop, host CLI and Web build outputs.')
