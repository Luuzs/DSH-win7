"""Create real, editable Office files and a PDF using the offline DSH runtime."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
from datetime import datetime
from docx import Document
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor
from pptx import Presentation
from pptx.util import Inches, Pt as SlidePt
from pptx.dml.color import RGBColor as SlideColor
from pptx.oxml.xmlchemy import OxmlElement
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment

FONT="Microsoft YaHei"
SAMPLE=["打开 Writer，修改文档中的工作记录，再保存为 DOCX。",
        "打开 Impress，编辑演示文稿的标题和正文，再保存为 PPTX。",
        "用 LibreOffice Draw 打开 PDF，检查中文、页边距和换行。"]
def generate(destination,title,lines):
    destination.mkdir(parents=True,exist_ok=True)
    out=Path(tempfile.mkdtemp(prefix=datetime.now().strftime("%Y%m%d-%H%M%S-"),dir=destination))
    d=Document()
    normal=d.styles["Normal"];normal.font.name=FONT;normal.font.size=Pt(11)
    normal.element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"),FONT)
    h=d.add_paragraph().add_run(title);h.bold=True;h.font.name=FONT;h.font.size=Pt(24)
    h.font.color.rgb=RGBColor.from_string("173949")
    h._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"),FONT)
    for line in lines:d.add_paragraph(line)
    d.save(out/"work-record.docx")
    p=Presentation();p.slide_width=Inches(13.333);p.slide_height=Inches(7.5)
    def textbox(slide,xywh,text,size,bold,color):
        shape=slide.shapes.add_textbox(*[Inches(x) for x in xywh])
        frame=shape.text_frame;frame.word_wrap=True
        run=frame.paragraphs[0].add_run();run.text=text
        run.font.name=FONT;run.font.size=SlidePt(size);run.font.bold=bold;run.font.color.rgb=SlideColor.from_string(color)
        ea=OxmlElement("a:ea");ea.set("typeface",FONT);run._r.get_or_add_rPr().append(ea)
    # Keep long content editable; use additional slides rather than shrinking all text.
    parts=[line[i:i+70] for line in lines for i in range(0,len(line),70)]
    for i in range(0,len(parts),3):
        s=p.slides.add_slide(p.slide_layouts[6]);s.background.fill.solid();s.background.fill.fore_color.rgb=SlideColor.from_string("F4F6F5")
        textbox(s,(.70,.65,11.9,1.25),title,34,True,"173949")
        for j,t in enumerate(parts[i:i+3]):textbox(s,(.80,2.05+j*1.48,11.60,1.34),t,21,False,"254C55")
    p.save(out/"work-brief.pptx")
    w=Workbook();sheet=w.active;sheet.title="工作记录";sheet.append(["序号","事项"])
    for i,t in enumerate(lines,1):sheet.append([i,t])
    sheet.column_dimensions["A"].width=9;sheet.column_dimensions["B"].width=82
    for row in sheet:
        for c in row:
            c.font=Font(name=FONT,bold=c.row==1,color="FFFFFF" if c.row==1 else "173949")
            c.alignment=Alignment(wrap_text=True,vertical="center")
            if c.row==1:c.fill=PatternFill("solid",fgColor="275761")
    w.save(out/"work-list.xlsx")
    # Use the native conversion engine already supplied inside DSH.
    resources=Path(os.environ["LOCALAPPDATA"])/"Programs/DSH-Win7/resources"
    node=resources/"runtime/primary-runtime/dependencies/node/bin/node.exe"
    cli=resources/"app.asar.unpacked/dsh/node_modules/@deepseek-ai/libreoffice-kit/lib/cli.js"
    pdf=out/"work-record.pdf"
    subprocess.run([str(node),str(cli),"convert","--input",str(out/"work-record.docx"),"--output",str(pdf)],check=True,timeout=180)
    if title not in [v.text for v in Document(out/"work-record.docx").paragraphs]:raise ValueError("DOCX read-back")
    if Presentation(out/"work-brief.pptx").slides[0].shapes[0].text!=title:raise ValueError("PPTX read-back")
    if load_workbook(out/"work-list.xlsx").active["B2"].value!=lines[0]:raise ValueError("XLSX read-back")
    data=pdf.read_bytes()
    if not data.startswith(b"%PDF-") or b"%%EOF" not in data[-1024:]:raise ValueError("PDF read-back")
    print("DSH_DOCUMENTS_OK",str(out))
    return out
if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--title",default="离线办公工作记录");parser.add_argument("--text",type=Path)
    args=parser.parse_args();lines=SAMPLE if args.text is None else [s for s in args.text.read_text(encoding="utf-8-sig").splitlines() if s.strip()]
    if not lines:parser.error("The input text is empty")
    generate(args.out,args.title,lines)
