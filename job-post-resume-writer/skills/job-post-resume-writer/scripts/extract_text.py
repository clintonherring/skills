#!/usr/bin/env python3
"""Print the plain text of a CV or writing sample so the agent does not hand-parse it.

Usage:
    python3 extract_text.py <file-or-url> [--out text.txt]

Supported: .docx (stdlib), .pdf (pdftotext, then pypdf), .txt / .md, .html / http(s) URL (stdlib).
Exit codes: 0 text printed; 2 unsupported or unreadable (ask the user to paste the text); 3 PDF with no
extractor available or no text layer (scanned PDF).
"""
import argparse
import html
import re
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def from_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("word/document.xml"))
    out = []
    for p in root.iter(W + "p"):
        parts = []
        for node in p.iter():
            if node.tag == W + "t" and node.text:
                parts.append(node.text)
            elif node.tag == W + "tab":
                parts.append("\t")
            elif node.tag == W + "br":
                parts.append("\n")
        line = "".join(parts).strip()
        if p.find(".//" + W + "numPr") is not None and line:
            line = "- " + line
        out.append(line)
    text = "\n".join(out)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def from_pdf(path: Path) -> str:
    if shutil.which("pdftotext"):
        try:
            res = subprocess.run(["pdftotext", "-layout", str(path), "-"], capture_output=True, text=True, check=True)
            if res.stdout.strip():
                return res.stdout.strip()
        except Exception:
            pass
    try:
        import pypdf  # type: ignore

        reader = pypdf.PdfReader(str(path))
        text = "\n".join((pg.extract_text() or "") for pg in reader.pages).strip()
        if text:
            return text
        print("PDF has no text layer (scanned?). Ask the user to paste the text.", file=sys.stderr)
        sys.exit(3)
    except ImportError:
        print("No PDF extractor: install poppler (pdftotext) or `pip install pypdf`, or ask the user to paste the text.", file=sys.stderr)
        sys.exit(3)


class _Stripper(HTMLParser):
    SKIP = {"script", "style", "nav", "footer", "header", "noscript", "svg"}
    BLOCK = {"p", "div", "br", "li", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "section", "article", "blockquote"}

    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip += 1
        elif tag in self.BLOCK:
            self.parts.append("\n")
            if tag == "li":
                self.parts.append("- ")

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skip:
            self.skip -= 1
        elif tag in self.BLOCK:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)

    def text(self):
        t = html.unescape("".join(self.parts))
        t = re.sub(r"[ \t]+", " ", t)
        t = re.sub(r"\n\s*\n+", "\n\n", t)
        return t.strip()


def from_html(raw: str) -> str:
    s = _Stripper()
    s.feed(raw)
    return s.text()


def from_url(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (resume-writer extract_text)"})
    with urllib.request.urlopen(req, timeout=20) as r:
        ctype = r.headers.get("Content-Type", "")
        raw = r.read()
    if "pdf" in ctype:
        tmp = Path("/tmp/_extract.pdf") if Path("/tmp").exists() else Path.home() / "_extract.pdf"
        tmp.write_bytes(raw)
        return from_pdf(tmp)
    return from_html(raw.decode("utf-8", errors="replace"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source")
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    src = a.source
    try:
        if re.match(r"^https?://", src):
            text = from_url(src)
        else:
            p = Path(src).expanduser()
            if not p.exists():
                print(f"Not found: {p}", file=sys.stderr)
                return 2
            ext = p.suffix.lower()
            if ext == ".docx":
                text = from_docx(p)
            elif ext == ".pdf":
                text = from_pdf(p)
            elif ext in {".txt", ".md", ".markdown"}:
                text = p.read_text(encoding="utf-8", errors="replace")
            elif ext in {".html", ".htm"}:
                text = from_html(p.read_text(encoding="utf-8", errors="replace"))
            elif ext == ".doc":
                print("Legacy .doc is not supported: save as .docx or paste the text.", file=sys.stderr)
                return 2
            else:
                print(f"Unsupported type {ext}: paste the text instead.", file=sys.stderr)
                return 2
    except SystemExit:
        raise
    except Exception as e:  # unreadable file, bad zip, network error
        print(f"Could not extract: {e}. Ask the user to paste the text.", file=sys.stderr)
        return 2
    if not text.strip():
        print("No text found. Ask the user to paste the text.", file=sys.stderr)
        return 2
    if a.out:
        a.out.write_text(text, encoding="utf-8")
        print(f"Wrote {a.out} ({len(text.split())} words)")
    else:
        sys.stdout.write(text + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
