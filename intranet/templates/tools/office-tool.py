"""Offline DSH document tool. The caller can supply text, never commands or paths."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(sys.argv[1]).resolve()
SCHEMA = {"type":"object","properties":{
    "title":{"type":"string","minLength":1,"maxLength":100},
    "paragraphs":{"type":"array","minItems":1,"maxItems":100,"items":{"type":"string","minLength":1,"maxLength":1500}}
},"required":["title","paragraphs"],"additionalProperties":False}
TOOL = {"name":"create_documents","description":"Create editable DOCX, PPTX and XLSX files plus a PDF with the supplied Chinese or English title and paragraphs. Runs offline on this Windows computer, saves a new folder under Documents/DSH-Office and returns the actual file paths.","inputSchema":SCHEMA,
        "annotations":{"readOnlyHint":False,"destructiveHint":False,"openWorldHint":False}}

def documents(args):
    title=args.get("title");lines=args.get("paragraphs")
    if not isinstance(title,str) or not title.strip() or len(title)>100:raise ValueError("Supply a title of 1-100 characters.")
    if not isinstance(lines,list) or not 1<=len(lines)<=100 or any(not isinstance(s,str) or not s.strip() or len(s)>1500 for s in lines) or sum(map(len,lines))>25000:raise ValueError("Supply 1-100 text paragraphs, up to 25000 characters in total.")
    ROOT.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="DSH-office-input-") as temp:
        content=Path(temp)/"input.txt";content.write_text("\n".join(lines),encoding="utf-8")
        p=subprocess.run([sys.executable,str(Path(__file__).with_name("make-documents.py")),"--out",str(ROOT),"--title",title,"--text",str(content)],
                         capture_output=True,timeout=240,env={**os.environ,"PYTHONIOENCODING":"utf-8"})
    if p.returncode:raise RuntimeError(p.stderr.decode("utf-8","replace")[-800:] or "Document generation failed.")
    folder=next(Path(s.split(" ",1)[1]).resolve() for s in p.stdout.decode("utf-8").splitlines() if s.startswith("DSH_DOCUMENTS_OK "))
    if folder.parent!=ROOT:raise ValueError("Unexpected output directory.")
    files=[folder/n for n in ("work-record.docx","work-brief.pptx","work-list.xlsx","work-record.pdf")]
    if not all(p.is_file() and p.stat().st_size for p in files):raise ValueError("Incomplete outputs.")
    return "\n".join(str(p) for p in files)

def dispatch(method,params):
    if method=="initialize":
        return {"protocolVersion":"2025-06-18","capabilities":{"tools":{}},"serverInfo":{"name":"win7-offline-office","version":"1.0.0"},"instructions":"For requests to generate local Office files, use create_documents with the user's title and paragraphs. Report the returned file paths."}
    if method=="ping":return {}
    if method=="tools/list":return {"tools":[TOOL]}
    if method=="tools/call" and params.get("name")==TOOL["name"]:
        try:return {"content":[{"type":"text","text":documents(params.get("arguments",{}))}],"isError":False}
        except Exception as exc:return {"content":[{"type":"text","text":str(exc)}],"isError":True}
    raise KeyError(method)

for raw in sys.stdin.buffer:
    try:
        message=json.loads(raw)
        if "id" not in message:continue
        reply={"jsonrpc":"2.0","id":message["id"]}
        try:reply["result"]=dispatch(message.get("method"),message.get("params",{}))
        except KeyError:reply["error"]={"code":-32601,"message":"Method not supported"}
        sys.stdout.buffer.write((json.dumps(reply,ensure_ascii=True)+"\n").encode("ascii"));sys.stdout.buffer.flush()
    except (ValueError,TypeError):continue
