#!/usr/bin/env python3
"""Convert a Markdown CV written to templates/cv.template.md into the JSON that build-cv.js reads.

Usage:
    python3 md_to_cvjson.py cv.md cv.json
    node build-cv.js cv.json cv.docx --pdf

Expected Markdown shape (see templates/cv.template.md):
    <!-- comment -->                      ignored
    # Full name
    **Headline**
    City · phone · email · [text](url)   contact line; [text](url) parts become links
    *status line*                         optional, italic
    ## Summary        paragraph, then "- **Label**  text" highlight bullets
    ## Skills         "- **Group:** text" lines
    ## Experience     "### Title | Org — dates", optional intro paragraph, "- bullet" lines
    ## Projects       same shape as Experience; a "See: [text](url)" line becomes the entry link
    ## Education…     "- line" bullets
    ## <anything else> one short paragraph → the closing "extra" block (e.g. Interests)
"""
import argparse
import json
import re
import sys
from pathlib import Path

LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def strip_md(text: str) -> str:
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = LINK_RE.sub(r"\1", text)
    text = re.sub(r"(?<!\w)\*(.*?)\*(?!\w)", r"\1", text)
    text = re.sub(r"`(.*?)`", r"\1", text)
    return text.strip()


def split_sections(md: str):
    md = re.sub(r"<!--.*?-->", "", md, flags=re.DOTALL)
    header, sections, cur = [], [], None
    for ln in md.splitlines():
        m = re.match(r"^(#{2,3})\s+(.*)", ln)
        if m:
            cur = {"title": m.group(2).strip(), "level": len(m.group(1)), "lines": []}
            sections.append(cur)
        elif cur is None:
            header.append(ln)
        else:
            cur["lines"].append(ln)
    return header, sections


def parse_header(header):
    out = {"name": "", "headline": "", "contact": [], "links": [], "status": ""}
    for ln in header:
        s = ln.strip()
        if not s:
            continue
        if s.startswith("# ") and not out["name"]:
            out["name"] = s[2:].strip()
        elif s.startswith("**") and s.endswith("**") and not out["headline"]:
            out["headline"] = strip_md(s)
        elif s.startswith("*") and s.endswith("*") and not s.startswith("**"):
            out["status"] = strip_md(s)
        elif "·" in s or "@" in s or "+" in s:
            for part in re.split(r"\s*·\s*|\s*\|\s*", s):
                part = part.strip()
                if not part:
                    continue
                m = LINK_RE.fullmatch(part)
                if m:
                    out["links"].append({"text": m.group(1), "url": m.group(2)})
                else:
                    out["contact"].append(strip_md(part))
    return out


def entries_of(lines):
    """Group '### Title | Org — dates' blocks into entry dicts."""
    entries, cur = [], None
    for ln in lines:
        m = re.match(r"^###\s+(.*)", ln)
        if m:
            head = m.group(1).strip()
            title, org, dates = head, "", ""
            if "|" in head:
                title, rest = [x.strip() for x in head.split("|", 1)]
            else:
                rest = ""
            if rest:
                if " — " in rest:
                    org, dates = [x.strip() for x in rest.rsplit(" — ", 1)]
                elif " - " in rest:
                    org, dates = [x.strip() for x in rest.rsplit(" - ", 1)]
                else:
                    org = rest
            elif " — " in head:
                title, dates = [x.strip() for x in head.rsplit(" — ", 1)]
            cur = {"title": strip_md(title), "org": strip_md(org), "dates": strip_md(dates), "intro": "", "bullets": []}
            entries.append(cur)
            continue
        if cur is None:
            continue
        s = ln.strip()
        if not s:
            continue
        if s.startswith("- "):
            cur["bullets"].append(strip_md(s[2:]))
        elif s.lower().startswith("see:"):
            m2 = LINK_RE.search(s)
            if m2:
                cur["link"] = {"text": m2.group(1), "url": m2.group(2)}
        else:
            cur["intro"] = (cur["intro"] + " " + strip_md(s)).strip()
    return entries


def convert(md: str) -> dict:
    header, sections = split_sections(md)
    doc = parse_header(header)
    doc.update({"summary": "", "highlights": [], "skills": [], "experience": [], "projects": [], "education": [], "headings": {}})

    # Re-attach ### blocks to their parent ## section.
    groups, cur = [], None
    for s in sections:
        if s["level"] == 2:
            cur = {"title": s["title"], "lines": list(s["lines"])}
            groups.append(cur)
        elif cur is not None:
            cur["lines"].append("### " + s["title"])
            cur["lines"].extend(s["lines"])

    for g in groups:
        t = g["title"]
        tl = t.lower()
        if tl.startswith("summary") or tl.startswith("profile"):
            doc["headings"]["summary"] = t
            para = []
            for ln in g["lines"]:
                s = ln.strip()
                if not s:
                    continue
                if s.startswith("- "):
                    m = re.match(r"^-\s+\*\*(.+?)\*\*\s*(.*)$", s)
                    if m:
                        doc["highlights"].append({"label": m.group(1).strip().rstrip(":"), "text": strip_md(m.group(2))})
                    else:
                        doc["highlights"].append({"label": "", "text": strip_md(s[2:])})
                else:
                    para.append(strip_md(s))
            doc["summary"] = " ".join(para)
        elif tl.startswith("skills") or tl.startswith("core"):
            doc["headings"]["skills"] = t
            for ln in g["lines"]:
                s = ln.strip()
                m = re.match(r"^-\s+\*\*(.+?)\*\*:?\s*(.*)$", s)
                if m:
                    doc["skills"].append({"label": m.group(1).strip().rstrip(":"), "text": strip_md(m.group(2))})
                elif s.startswith("- "):
                    doc["skills"].append({"label": "", "text": strip_md(s[2:])})
        elif tl.startswith("experience") or tl.startswith("work"):
            doc["headings"]["experience"] = t
            doc["experience"] = entries_of(g["lines"])
        elif tl.startswith("project"):
            doc["headings"]["projects"] = t
            doc["projects"] = entries_of(g["lines"])
        elif tl.startswith("education") or tl.startswith("certif"):
            doc["headings"]["education"] = t
            for ln in g["lines"]:
                s = ln.strip()
                if s.startswith("- "):
                    doc["education"].append(strip_md(s[2:]))
                elif s:
                    doc["education"].append(strip_md(s))
        else:
            text = " ".join(strip_md(ln.strip().lstrip("- ")) for ln in g["lines"] if ln.strip())
            if text:
                doc["extra"] = {"heading": t, "text": text}

    for k in ("projects",):
        if not doc[k]:
            doc.pop(k)
    return doc


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cv", type=Path)
    ap.add_argument("out", type=Path)
    a = ap.parse_args()
    if not a.cv.exists():
        print(f"CV file not found: {a.cv}", file=sys.stderr)
        return 2
    doc = convert(a.cv.read_text(encoding="utf-8"))
    problems = []
    if not doc["name"]:
        problems.append("no '# Name' line")
    if not doc["experience"]:
        problems.append("no entries under '## Experience'")
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {a.out}: {len(doc['highlights'])} highlights, {len(doc['skills'])} skill lines, "
          f"{len(doc['experience'])} roles, {len(doc['education'])} education lines")
    for p in problems:
        print(f"WARN  {p}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
