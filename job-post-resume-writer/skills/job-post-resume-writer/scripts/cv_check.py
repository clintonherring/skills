#!/usr/bin/env python3
"""Check a Markdown CV against the five AI-era résumé rules before the person sees it.

Usage:
    python3 cv_check.py path/to/cv.md --jd path/to/jd.md [--facts facts.md] [--voice voice.md] [--strict]

--facts and --voice default to <data_dir>/facts.md and <data_dir>/voice.md from
~/.job-post-resume-writer/config.json. Advisory by default (exit 0); with --strict, exit 1
on any FAIL.

Checks (see references/ai-era-guidelines.md and references/scorecard.md):
  Rule 1  structure: Summary → Skills → Experience → Education order, experience above
          education, no images/tables, length within two pages (~450–1050 words)
  Rule 2  repetition: key terms used more than 3 times outside the Skills list; with --jd,
          posting terms facts.md supports but the CV never uses, and posting terms in the CV
          that facts.md does not support (stuffing risk)
  Rule 3  voice: résumé-speak (generic list + the "avoid" section of voice.md); bullets not
          in first person; bullets over 30 words; more than 5 bullets per role
  Rule 4  numbers: roles whose bullets carry no number; every number in the CV must appear
          in facts.md (no invented metrics)
  Rule 5  proof: first bullet of the current role proves a skill the posting leans on (it
          names a posting term and carries a number or a named result); no "I have ideas"
          filler; every link in the CV is on the "Links allowed" line of facts.md
"""
import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from jd_match import PHRASES, candidate_terms, facts_for_matching, harvest_terms, has, norm  # noqa: E402
from jprw_config import default_facts, default_voice  # noqa: E402

BANNED = [
    "leveraged", "leverage", "spearheaded", "drove", "driving", "results-driven", "results driven",
    "proven track record", "track record of", "cross-functional", "operational excellence", "passionate",
    "dynamic", "synerg", "best-in-class", "world-class", "thought leader", "seasoned", "visionary",
    "go-getter", "detail-oriented", "team player", "self-starter", "responsible for", "stakeholder alignment",
    "utilised", "utilized", "facilitated", "orchestrated", "championed", "robust", "cutting-edge",
    "fast-paced", "hit the ground running", "go above and beyond", "wealth of experience",
]
FILLER = ["i have ideas", "ideas on how", "keen to explore", "interested in learning", "familiar with",
          "exposure to", "eager to", "willing to learn", "basic understanding"]
REPEAT_LIMIT = 3
MAX_BULLET_WORDS = 30
MAX_BULLETS_PER_ROLE = 5
WORDS_MIN, WORDS_MAX = 450, 1050
SKIP_REPEAT = set("""
i it the and at in my for on to with a of when most since alongside then present
january february march april may june july august september october november december
jan feb mar apr jun jul aug sep sept oct nov dec
""".split())


class Report:
    TITLES = {1: "the screening software can read it", 2: "fit is mapped, not stuffed",
              3: "their voice, not AI filler", 4: "numbers are real and present",
              5: "the skill the posting leans on is proven"}

    def __init__(self):
        self.items = []  # (rule, level, text)

    def add(self, rule, level, text):
        self.items.append((rule, level, text))

    def fails(self):
        return [i for i in self.items if i[1] == "FAIL"]

    def warns(self):
        return [i for i in self.items if i[1] == "WARN"]

    def dump(self):
        for rule in range(1, 6):
            rows = [i for i in self.items if i[0] == rule]
            print(f"\nRule {rule} — {self.TITLES[rule]}")
            if not rows:
                print("  PASS")
            for _, level, text in rows:
                print(f"  {level}  {text}")


def parse(md: str):
    md = re.sub(r"<!--.*?-->", "", md, flags=re.DOTALL)
    sections = []  # {"title", "level", "lines"}
    header = []
    cur = None
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


def bullets_of(sec):
    return [re.sub(r"^\-\s+", "", ln).strip() for ln in sec["lines"] if ln.strip().startswith("- ")]


def strip_md(text):
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text)
    text = re.sub(r"(?<!\w)\*(.*?)\*(?!\w)", r"\1", text)
    return text


def avoid_terms_from_voice(voice: str) -> list:
    """Words listed under '## Words and shapes to avoid' in voice.md (the part after a colon, comma-separated)."""
    out = []
    m = re.search(r"^## [^\n]*avoid[^\n]*\n(.*?)(?=^## |\Z)", voice, flags=re.MULTILINE | re.DOTALL | re.IGNORECASE)
    if not m:
        return out
    for ln in m.group(1).splitlines():
        ln = ln.strip().lstrip("-* ").strip()
        if ":" not in ln:
            continue
        tail = ln.split(":", 1)[1]
        for item in re.split(r"[,;]", tail):
            item = item.strip().strip(".").strip().lower()
            if 0 < len(item.split()) <= 3 and '"' not in item and "“" not in item:
                out.append(item)
    return out


def allowed_links(facts: str) -> list:
    m = re.search(r"^\|\s*Links allowed[^|]*\|\s*(.*?)\s*\|\s*$", facts, flags=re.MULTILINE | re.IGNORECASE)
    if not m:
        return []
    return re.findall(r"https?://\S+|www\.\S+|[a-z0-9.-]+\.[a-z]{2,}/\S*", m.group(1).lower())


def person_name_tokens(facts: str) -> set:
    m = re.search(r"^\|\s*Name\s*\|\s*(.*?)\s*\|\s*$", facts, flags=re.MULTILINE)
    return {w.lower() for w in m.group(1).split()} if m else set()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cv", type=Path)
    ap.add_argument("--jd", type=Path)
    ap.add_argument("--facts", type=Path, default=default_facts())
    ap.add_argument("--voice", type=Path, default=default_voice())
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()

    if not a.cv.exists():
        print(f"CV file not found: {a.cv}", file=sys.stderr)
        return 2
    md = a.cv.read_text(encoding="utf-8")
    facts_raw = a.facts.read_text(encoding="utf-8") if a.facts and a.facts.exists() else ""
    voice_raw = a.voice.read_text(encoding="utf-8") if a.voice and a.voice.exists() else ""
    header, sections = parse(md)
    body_text = strip_md("\n".join(ln for s in sections for ln in s["lines"]))
    full_text = strip_md(re.sub(r"<!--.*?-->", "", md, flags=re.DOTALL))
    lowered = full_text.lower()
    rep = Report()
    if not facts_raw:
        rep.add(4, "WARN", "no facts.md found; number and link checks are weak (pass --facts)")

    # ---------------- Rule 1: structure ----------------
    h2 = [s["title"].lower() for s in sections if s["level"] == 2]
    want = ["summary", "skills", "experience"]
    idx = {w: next((i for i, t in enumerate(h2) if t.startswith(w)), None) for w in want}
    edu_idx = next((i for i, t in enumerate(h2) if t.startswith("education")), None)
    for w in want:
        if idx[w] is None:
            rep.add(1, "FAIL", f"missing '## {w.title()}' heading (conventional headings parse best)")
    if edu_idx is None:
        rep.add(1, "FAIL", "missing '## Education…' heading")
    elif idx["experience"] is not None and edu_idx < idx["experience"]:
        rep.add(1, "FAIL", "Education appears before Experience (hiring managers weigh experience more)")
    if all(idx[w] is not None for w in want) and not (idx["summary"] < idx["skills"] < idx["experience"]):
        rep.add(1, "WARN", "heading order is not Summary → Skills → Experience")
    if "![" in md:
        rep.add(1, "FAIL", "image found; images do not parse and inflate file size")
    if re.search(r"^\|.*\|\s*$", md, flags=re.MULTILINE):
        rep.add(1, "WARN", "Markdown table found; tables parse badly in screening tools")
    if not header or not any(ln.startswith("# ") for ln in header):
        rep.add(1, "FAIL", "no '# Name' line at the top")
    words = len(full_text.split())
    if words > WORDS_MAX:
        rep.add(1, "WARN", f"{words} words; over ~{WORDS_MAX} usually spills past two A4 pages at 10pt")
    elif words < WORDS_MIN:
        rep.add(1, "WARN", f"{words} words; under ~{WORDS_MIN} looks thin unless the career is short")
    else:
        rep.add(1, "PASS", f"{words} words (two-page range)")

    # ---------------- Rule 2: mapping vs stuffing ----------------
    own_terms = harvest_terms(facts_raw) if facts_raw else set()
    skip = SKIP_REPEAT | person_name_tokens(facts_raw)
    # Count outside the Skills list: that list is a keyword block by design.
    count_text = strip_md("\n".join(ln for s in sections if not s["title"].lower().startswith("skills") for ln in s["lines"]))
    counts = {}
    for m in re.finditer(r"\b[A-Z][A-Za-z0-9+#.-]{1,}(?: [A-Z][A-Za-z0-9+#.-]{1,})*\b", count_text):
        before = count_text[: m.start()].rstrip()
        if before == "" or before[-1] in ".:;!?\u2014-\u2022*#|" or before.endswith("\n"):
            continue  # sentence start: capitalised for grammar
        t = m.group(0).lower().strip(".")
        if t in skip or len(t) < 3 or t.split()[0] in skip or re.fullmatch(r"[\d,.%+]+", t):
            continue
        counts[t] = counts.get(t, 0) + 1
    count_lower = count_text.lower()
    for ph in set(PHRASES) | own_terms:
        if " " in ph:
            n = len(re.findall(r"(?<![a-z0-9])" + re.escape(ph) + r"(?![a-z0-9])", count_lower))
            if n:
                counts[ph] = n
    for t, n in sorted(counts.items(), key=lambda x: -x[1]):
        if n > REPEAT_LIMIT:
            rep.add(2, "WARN", f"'{t}' appears {n} times outside Skills; say each fact once (limit {REPEAT_LIMIT})")
    jd_terms = set()
    if a.jd and a.jd.exists():
        jd_terms = candidate_terms(a.jd.read_text(encoding="utf-8"), extra_phrases=own_terms)
        facts_n = norm(facts_for_matching(facts_raw))
        cv_n = norm(full_text)
        body_n = norm(body_text)  # the headline may carry the target job title; the body may not claim unsupported terms
        supported_unused = sorted(t for t in jd_terms if has(facts_n, t) and not has(cv_n, t))
        unsupported_used = sorted(t for t in jd_terms if not has(facts_n, t) and has(body_n, t))
        if supported_unused:
            rep.add(2, "WARN", "posting terms facts.md supports but the CV never says: " + ", ".join(supported_unused))
        if unsupported_used:
            rep.add(2, "FAIL", "posting terms in the CV with no backing in facts.md (stuffing risk): " + ", ".join(unsupported_used))
        if not supported_unused and not unsupported_used:
            rep.add(2, "PASS", "every supported posting term is used; no unsupported posting term is claimed")
    elif a.jd:
        rep.add(2, "WARN", f"posting file not found: {a.jd}")
    else:
        rep.add(2, "WARN", "no --jd given; mapping coverage not checked")

    # ---------------- Rule 3: voice ----------------
    avoid = list(dict.fromkeys(BANNED + avoid_terms_from_voice(voice_raw)))
    if not voice_raw:
        rep.add(3, "WARN", "no voice.md found; only the generic résumé-speak list is checked (pass --voice)")
    for b in avoid:
        if re.search(r"(?<![a-z])" + re.escape(b) + r"(?![a-z])", lowered):
            rep.add(3, "FAIL", f"résumé-speak: '{b}'")
    exp_secs = []
    in_exp = False
    for s in sections:
        if s["level"] == 2:
            in_exp = s["title"].lower().startswith("experience")
        elif s["level"] == 3 and in_exp:
            exp_secs.append(s)
    if not exp_secs:
        rep.add(3, "FAIL", "no '### Title | Organisation — dates' entries under Experience")
    for s in exp_secs:
        bl = bullets_of(s)
        if len(bl) > MAX_BULLETS_PER_ROLE:
            rep.add(3, "WARN", f"{s['title']}: {len(bl)} bullets (limit {MAX_BULLETS_PER_ROLE})")
        for b in bl:
            plain = strip_md(b)
            if len(plain.split()) > MAX_BULLET_WORDS:
                rep.add(3, "WARN", f"{s['title']}: bullet over {MAX_BULLET_WORDS} words: \"{plain[:60]}…\"")
            if not re.search(r"\b(I|my|me|we|our)\b", plain):
                rep.add(3, "WARN", f"{s['title']}: not in first person: \"{plain[:70]}…\"")
            if re.search(r"\b(was|were|been)\s+\w+ed\b", plain):
                rep.add(3, "WARN", f"{s['title']}: passive voice: \"{plain[:70]}…\"")

    # ---------------- Rule 4: numbers ----------------
    facts_digits = {d.rstrip(".,") for d in re.findall(r"\d[\d,.]*", facts_raw)}
    for s in exp_secs:
        bl = bullets_of(s)
        intro = " ".join(ln for ln in s["lines"] if ln.strip() and not ln.strip().startswith("- "))
        if bl and not any(re.search(r"\d", b) for b in bl) and not re.search(r"\d", intro):
            rep.add(4, "WARN", f"{s['title']}: no number in any bullet or intro (responsibilities only) — ask for one or accept")
    numbered = sum(1 for s in exp_secs for b in bullets_of(s) if re.search(r"\d", b))
    total = sum(len(bullets_of(s)) for s in exp_secs)
    if total:
        rep.add(4, "PASS" if numbered / total >= 0.5 else "WARN", f"{numbered}/{total} experience bullets carry a number")
    if facts_raw:
        for num in sorted(set(re.findall(r"\d[\d,.]*", body_text))):
            if num.rstrip(".,") not in facts_digits:
                rep.add(4, "FAIL", f"number '{num}' is not in facts.md — remove it or add the fact first")

    # ---------------- Rule 5: proof ----------------
    if exp_secs:
        first = bullets_of(exp_secs[0])
        role = exp_secs[0]["title"]
        if not first:
            rep.add(5, "WARN", f"'{role}' has no bullets; the first bullet should prove the skill the posting leans on")
        else:
            plain = strip_md(first[0])
            pl = plain.lower()
            names_term = any(has(pl, t) for t in jd_terms) if jd_terms else True
            has_number = re.search(r"\d", plain) is not None
            if names_term and has_number:
                rep.add(5, "PASS", f"first bullet of '{role}' names a posting term and carries a number")
            elif names_term:
                rep.add(5, "WARN", f"first bullet of '{role}' names a posting term but has no number or measured result")
            else:
                rep.add(5, "WARN", f"first bullet of '{role}' does not name any posting term; is it the proof the posting needs?")
    for f in FILLER:
        if f in lowered:
            rep.add(5, "WARN", f"filler instead of proof: '{f}' — say what you did with it, or drop it")
    links = re.findall(r"\((https?://[^)\s]+)\)|(?<![\w/])(www\.[^\s)]+)", re.sub(r"<!--.*?-->", "", md, flags=re.DOTALL))
    links = [x or y for x, y in links]
    if links:
        allowed = allowed_links(facts_raw)
        for url in links:
            u = url.lower().rstrip("/").replace("https://", "").replace("http://", "").replace("www.", "")
            ok = any(u in al.rstrip("/").replace("https://", "").replace("http://", "").replace("www.", "")
                     or al.rstrip("/").replace("https://", "").replace("http://", "").replace("www.", "") in u
                     for al in allowed)
            if not ok:
                rep.add(5, "FAIL", f"link {url} is not on the 'Links allowed on a CV' line of facts.md")
        if all(i[0] != 5 or i[1] != "FAIL" for i in rep.items):
            rep.add(5, "PASS", f"{len(links)} link(s), all on the allowed list")

    rep.dump()
    fails = rep.fails()
    print(f"\n{len(fails)} FAIL, {len(rep.warns())} WARN")
    print("Next: score with references/scorecard.md into cv-review.md; fix FAILs; decide each WARN; only then show the person.")
    return 1 if (a.strict and fails) else 0


if __name__ == "__main__":
    sys.exit(main())
