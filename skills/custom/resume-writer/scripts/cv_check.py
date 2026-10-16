#!/usr/bin/env python3
"""Check a Markdown CV against the five AI-era résumé rules before Clinton sees it.

Usage:
    python3 cv_check.py assets/<cv>.md [--jd path/to/jd.md] [--facts path/to/facts.md] [--strict]

Advisory by default (exit 0). With --strict, exit 1 if any FAIL is reported.

Checks (see references/ai-era-guidelines.md and references/scorecard.md):
  Rule 1  structure: Summary → Skills → Experience → Education order, experience above
          education, no images/tables, length within two pages (~600–1050 words)
  Rule 2  repetition: proper nouns / key terms used more than 3 times; with --jd, JD terms
          that facts.md supports but the CV never uses, and JD terms in the CV that facts.md
          does not support (stuffing risk)
  Rule 3  voice: résumé-speak and generic phrases; bullets not written in first person;
          bullets over 30 words; more than 5 bullets per role
  Rule 4  numbers: roles whose bullets carry no number at all; every number in the CV must
          appear in facts.md (no invented metrics)
  Rule 5  AI proof: first bullet of the current role mentions AI; no "I have ideas" filler;
          no link to the skills repository (Clinton's instruction)
"""
import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_FACTS = HERE.parent / "references" / "facts.md"
sys.path.insert(0, str(HERE))
try:
    from jd_match import PHRASES, candidate_terms, facts_for_matching, norm  # noqa: E402
except Exception:  # pragma: no cover
    PHRASES, candidate_terms, facts_for_matching, norm = [], None, None, None

BANNED = [
    "owned", "leveraged", "codified", "spearheaded", "drove", "structural fix", "supplier governance",
    "results-driven", "results driven", "proven track record", "cross-functional", "operational excellence",
    "muscle", "passionate", "dynamic", "synerg", "best-in-class", "world-class", "thought leader",
    "seasoned", "visionary", "go-getter", "detail-oriented", "team player", "self-starter",
]
FILLER_AI = ["i have ideas", "ideas on how", "keen to explore", "interested in ai", "familiar with ai"]
REPEAT_LIMIT = 3
MAX_BULLET_WORDS = 30
MAX_BULLETS_PER_ROLE = 5
WORDS_MIN, WORDS_MAX = 600, 1050
SKIP_REPEAT = {
    "clinton", "herring", "i", "it", "the", "and", "at", "in", "my", "for", "on", "to", "with", "a", "of",
    "when", "most", "since", "alongside", "store", "then", "network", "networking", "systems", "principal",
    "platform", "infrastructure", "engineer", "architect", "associate", "specialist", "manager", "south",
    "africa", "south africa", "university", "cape town", "nl", "entra id", "id", "pbx", "acls",
}


class Report:
    def __init__(self):
        self.items = []  # (rule, level, text)

    def add(self, rule, level, text):
        self.items.append((rule, level, text))

    def fails(self):
        return [i for i in self.items if i[1] == "FAIL"]

    def dump(self):
        for rule in range(1, 6):
            rows = [i for i in self.items if i[0] == rule]
            title = {1: "AI can read it", 2: "fit is mapped, not stuffed", 3: "his voice, not AI filler",
                     4: "numbers are real and present", 5: "AI skills are proven"}[rule]
            print(f"\nRule {rule} — {title}")
            if not rows:
                print("  PASS")
            for _, level, text in rows:
                print(f"  {level}  {text}")


def parse(md: str):
    md = re.sub(r"<!--.*?-->", "", md, flags=re.DOTALL)
    lines = md.splitlines()
    sections = []  # {"title", "level", "lines"}
    header = []
    cur = None
    for ln in lines:
        m = re.match(r"^(#{2,3})\s+(.*)", ln)
        if m:
            cur = {"title": m.group(2).strip(), "level": len(m.group(1)), "lines": []}
            sections.append(cur)
        elif cur is None:
            header.append(ln)
        else:
            cur["lines"].append(ln)
    return header, sections


def bullets_of(sec):
    return [re.sub(r"^\-\s+", "", ln).strip() for ln in sec["lines"] if ln.strip().startswith("- ")]


def strip_md(text):
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text)
    return text


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cv", type=Path)
    ap.add_argument("--jd", type=Path)
    ap.add_argument("--facts", type=Path, default=DEFAULT_FACTS)
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()

    md = a.cv.read_text(encoding="utf-8")
    facts_raw = a.facts.read_text(encoding="utf-8") if a.facts.exists() else ""
    header, sections = parse(md)
    body_text = strip_md("\n".join(ln for s in sections for ln in s["lines"]))
    full_text = strip_md(re.sub(r"<!--.*?-->", "", md, flags=re.DOTALL))
    rep = Report()

    # ---------------- Rule 1: structure ----------------
    h2 = [s["title"].lower() for s in sections if s["level"] == 2]
    want = ["summary", "skills", "experience"]
    idx = {w: next((i for i, t in enumerate(h2) if t.startswith(w)), None) for w in want}
    edu_idx = next((i for i, t in enumerate(h2) if t.startswith("education")), None)
    for w in want:
        if idx[w] is None:
            rep.add(1, "FAIL", f"missing '## {w.title()}' heading")
    if edu_idx is None:
        rep.add(1, "FAIL", "missing '## Education…' heading")
    elif idx["experience"] is not None and edu_idx < idx["experience"]:
        rep.add(1, "FAIL", "Education appears before Experience (86% of hiring managers value experience more)")
    if all(idx[w] is not None for w in want) and not (idx["summary"] < idx["skills"] < idx["experience"]):
        rep.add(1, "WARN", "heading order is not Summary → Skills → Experience")
    if "![" in md:
        rep.add(1, "FAIL", "image found; images do not parse and inflate file size")
    if re.search(r"^\|.*\|\s*$", md, flags=re.MULTILINE):
        rep.add(1, "WARN", "Markdown table found; tables parse badly in ATS tools")
    words = len(full_text.split())
    if words > WORDS_MAX:
        rep.add(1, "WARN", f"{words} words; over ~{WORDS_MAX} usually spills past two A4 pages at 10pt")
    elif words < WORDS_MIN:
        rep.add(1, "WARN", f"{words} words; under ~{WORDS_MIN} looks thin for 20+ years")
    else:
        rep.add(1, "PASS", f"{words} words (two-page range)")

    # ---------------- Rule 2: mapping vs stuffing ----------------
    counts = {}
    rep_text = strip_md("\n".join(ln for s in sections for ln in s["lines"]))  # headers and role titles excluded
    for tok in re.findall(r"\b[A-Z][A-Za-z0-9+#.-]{1,}(?: [A-Z][A-Za-z0-9+#.-]{1,})*\b", rep_text):
        t = tok.lower().strip(".")
        if t in SKIP_REPEAT or len(t) < 3 or t.split()[0] in SKIP_REPEAT:
            continue
        counts[t] = counts.get(t, 0) + 1
    lowered = full_text.lower()
    for ph in PHRASES:
        if " " in ph:
            n = len(re.findall(r"(?<![a-z0-9])" + re.escape(ph) + r"(?![a-z0-9])", lowered))
            if n:
                counts[ph] = n
    for t, n in sorted(counts.items(), key=lambda x: -x[1]):
        if n > REPEAT_LIMIT:
            rep.add(2, "WARN", f"'{t}' appears {n} times; say each fact once (limit {REPEAT_LIMIT})")
    if a.jd and a.jd.exists() and candidate_terms:
        jd_terms = candidate_terms(a.jd.read_text(encoding="utf-8"))
        facts_n = norm(facts_for_matching(facts_raw))
        cv_n = norm(full_text)

        def has(text, t):
            variants = {t, t + "s", t[:-1] if t.endswith("s") else t, t + "es"}
            return any(re.search(r"(?<![a-z0-9])" + re.escape(v) + r"(?![a-z0-9])", text) for v in variants)

        supported_unused = sorted(t for t in jd_terms if has(facts_n, t) and not has(cv_n, t))
        unsupported_used = sorted(t for t in jd_terms if not has(facts_n, t) and has(cv_n, t))
        if supported_unused:
            rep.add(2, "WARN", "JD terms facts.md supports but the CV never says: " + ", ".join(supported_unused))
        if unsupported_used:
            rep.add(2, "FAIL", "JD terms in the CV with no backing in facts.md (stuffing risk): " + ", ".join(unsupported_used))
        if not supported_unused and not unsupported_used:
            rep.add(2, "PASS", "every supported JD term is used; no unsupported JD term is claimed")
    elif a.jd:
        rep.add(2, "WARN", f"JD file not found: {a.jd}")
    else:
        rep.add(2, "WARN", "no --jd given; mapping coverage not checked")

    # ---------------- Rule 3: voice ----------------
    for b in BANNED:
        if re.search(r"(?<![a-z])" + re.escape(b) + r"(?![a-z])", lowered):
            rep.add(3, "FAIL", f"résumé-speak: '{b}'")
    exp_secs = []
    in_exp = False
    for s in sections:
        if s["level"] == 2:
            in_exp = s["title"].lower().startswith("experience")
        elif s["level"] == 3 and in_exp:
            exp_secs.append(s)
    for s in exp_secs:
        bl = bullets_of(s)
        if len(bl) > MAX_BULLETS_PER_ROLE:
            rep.add(3, "WARN", f"{s['title']}: {len(bl)} bullets (limit {MAX_BULLETS_PER_ROLE})")
        for b in bl:
            plain = strip_md(b)
            if len(plain.split()) > MAX_BULLET_WORDS:
                rep.add(3, "WARN", f"{s['title']}: bullet over {MAX_BULLET_WORDS} words: \"{plain[:60]}…\"")
            if not re.search(r"\b(I|my|me|we|our|with my)\b", plain):
                rep.add(3, "WARN", f"{s['title']}: not in first person: \"{plain[:70]}…\"")

    # ---------------- Rule 4: numbers ----------------
    facts_digits = set(re.findall(r"\d[\d,.]*", facts_raw))
    for s in exp_secs:
        bl = bullets_of(s)
        intro = " ".join(ln for ln in s["lines"] if ln.strip() and not ln.strip().startswith("- "))
        if bl and not any(re.search(r"\d", b) for b in bl) and not re.search(r"\d", intro):
            rep.add(4, "WARN", f"{s['title']}: no number in any bullet or intro (responsibilities only)")
    numbered = sum(1 for s in exp_secs for b in bullets_of(s) if re.search(r"\d", b))
    total = sum(len(bullets_of(s)) for s in exp_secs)
    if total:
        rep.add(4, "PASS" if numbered / total >= 0.5 else "WARN", f"{numbered}/{total} experience bullets carry a number")
    for num in sorted(set(re.findall(r"\d[\d,.]*", body_text))):
        if num.rstrip(".,") not in {d.rstrip(".,") for d in facts_digits}:
            rep.add(4, "FAIL", f"number '{num}' is not in facts.md — remove it or add the fact first")

    # ---------------- Rule 5: AI proof ----------------
    if exp_secs:
        first = bullets_of(exp_secs[0])
        if first and re.search(r"\bAI\b", strip_md(first[0])):
            rep.add(5, "PASS", f"first bullet of '{exp_secs[0]['title']}' is the AI achievement")
        else:
            rep.add(5, "WARN", f"first bullet of '{exp_secs[0]['title']}' is not an AI achievement")
    for f in FILLER_AI:
        if f in lowered:
            rep.add(5, "WARN", f"filler instead of proof: '{f}' — say what the tooling does")
    if "clintonherring/skills" in lowered or "github.com/clintonherring" in lowered:
        rep.add(5, "FAIL", "skills repository is linked; Clinton's instruction is not to use it as a portfolio")
    if not re.search(r"\bAI\b", body_text):
        rep.add(5, "WARN", "no AI achievement anywhere in the CV")

    rep.dump()
    fails = rep.fails()
    print(f"\n{len(fails)} FAIL, {sum(1 for i in rep.items if i[1] == 'WARN')} WARN")
    print("Next: fill references/scorecard.md for this CV; fix FAILs; decide each WARN; only then show Clinton.")
    return 1 if (a.strict and fails) else 0


if __name__ == "__main__":
    sys.exit(main())
