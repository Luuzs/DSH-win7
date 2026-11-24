"""Materialize the intranet edition from readable templates and a deployment endpoint."""
import argparse
import ipaddress
from pathlib import Path
import re

def render(template_dir,output,host,port,model):
    address=ipaddress.IPv4Address(host)
    if address.is_loopback or address.is_multicast or address.is_unspecified or not 1<=port<=65535:
        raise ValueError('A unicast IPv4 endpoint and TCP port are required.')
    if not re.fullmatch(r'[A-Za-z0-9_.:/-]{1,150}',model):raise ValueError('Invalid model identifier.')
    substitutions={'@@MODEL_IP@@':str(address),'@@MODEL_IP_HEX@@':f'0x{int(address):08x}','@@MODEL_PORT@@':str(port),'@@MODEL_ID@@':model}
    if output.resolve()==template_dir.resolve() or template_dir.resolve() in output.resolve().parents:
        raise ValueError('Select a separate output directory.')
    for source in sorted(template_dir.rglob('*')):
        if not source.is_file():continue
        relative=source.relative_to(template_dir)
        target=output/(str(relative)[:-3] if source.name.endswith('.in') else relative)
        data=source.read_bytes()
        for token,value in substitutions.items():data=data.replace(token.encode(),value.encode())
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)

if __name__=='__main__':
    root=Path(__file__).resolve().parents[1]
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--ip',required=True)
    p.add_argument('--port',required=True,type=int);p.add_argument('--model',required=True)
    p.add_argument('--output',type=Path,default=root/'out/kit')
    args=p.parse_args();render(root/'intranet/templates',args.output,args.ip,args.port,args.model)
