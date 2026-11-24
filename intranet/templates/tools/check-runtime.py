"""Offline installation acceptance. Uses only the installed DSH runtimes."""
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile

import docx
import lxml.etree
import numpy
import openpyxl
import pandas
import pptx
from PIL import Image

def main():
    os.environ.update(POWERSHELL_TELEMETRY_OPTOUT="1",POWERSHELL_UPDATECHECK="Off",DOTNET_CLI_TELEMETRY_OPTOUT="1",PIP_DISABLE_PIP_VERSION_CHECK="1",NPM_CONFIG_UPDATE_NOTIFIER="false")
    root = Path(os.environ["LOCALAPPDATA"]) / "Programs" / "DSH-Win7" / "resources"
    deps = root / "runtime/primary-runtime/dependencies"
    node = deps / "node/bin/node.exe"
    out = Path(tempfile.mkdtemp(prefix="DSH-Win7-check-"))
    print("Results:", out, flush=True)
    def run(*args):
        p = subprocess.run(args, cwd=out, capture_output=True, timeout=180)
        print(p.stdout.decode("utf-8","replace").strip(), flush=True)
        if p.returncode:
            raise RuntimeError(f"{args[0]} returned {p.returncode}: {p.stderr.decode('utf-8','replace')}")
    run(node, "--version")
    run(node, deps/"pnpm/bin/pnpm.mjs", "--version")
    run(root/"runtime/pwsh/pwsh.exe", "-NoProfile", "-NonInteractive", "-Command", "$PSVersionTable.PSVersion.ToString()")
    Image.new("RGB", (16,16), "green").save(out/"sample.png")
    assert numpy.arange(4).sum() == 6
    assert pandas.Series([10, 20]).sum() == 30
    assert lxml.etree.fromstring(b"<ok/>").tag == "ok"
    d = docx.Document()
    d.add_paragraph("DSH Windows 7 offline acceptance")
    d.save(out/"sample.docx")
    w = openpyxl.Workbook()
    w.active["A1"] = 42
    w.save(out/"sample.xlsx")
    p = pptx.Presentation()
    p.slides.add_slide(p.slide_layouts[0]).shapes.title.text = "DSH Windows 7"
    p.save(out/"sample.pptx")
    cli = root/"app.asar.unpacked/dsh/node_modules/@deepseek-ai/libreoffice-kit/lib/cli.js"
    for ext in ["docx", "xlsx", "pptx"]:
        pdf = out/(ext+".pdf")
        run(node, cli, "convert", "--input", out/("sample."+ext), "--output", pdf)
        if not pdf.read_bytes().startswith(b"%PDF-"):
            raise ValueError(f"Invalid PDF for {ext}")
    print(json.dumps({"result":"PASS", "python":sys.version.split()[0],
                      "office_to_pdf":["docx","xlsx","pptx"]}),flush=True)

if __name__ == "__main__":
    main()
