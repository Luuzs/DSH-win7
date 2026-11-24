# 在本工作目录生成办公文件

DSH 对话中优先使用本机的 `mcp__office__create_documents` 工具。将用户需要的标题传入 `title`，正文按段落传入 `paragraphs`。工具将返回四个真实文件的路径。该工具在本机运行。

根据用户的材料写标题和正文。将正文按段落保存为 UTF-8 文本，例如 `brief.txt`。每个非空行生成一个正文段落，可编辑的演示文稿会按篇幅分页。

在 Windows PowerShell 中从当前工作目录调用本机已安装的离线工具。下面的标题和文件名可按用户要求更换。

```powershell
& "$env:USERPROFILE\.dsh-intranet-win7\make-documents.cmd" --out . --title "本周工作记录" --text ".\brief.txt"
```

程序输出实际保存目录，在其中生成 `work-record.docx`、`work-brief.pptx`、`work-list.xlsx` 和 `work-record.pdf`。按需要调整可编辑文件，并把最终文件名告诉用户。可以使用本机 LibreOffice Writer、Impress、Calc 和 Draw 查看和修改文件。
