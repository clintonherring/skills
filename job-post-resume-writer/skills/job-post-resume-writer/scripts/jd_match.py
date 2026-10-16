#!/usr/bin/env python3
"""Scan a job posting against the person's facts.md.

Usage:
    python3 jd_match.py path/to/jd.md [--facts path/to/facts.md]

--facts defaults to <data_dir>/facts.md from ~/.job-post-resume-writer/config.json.

Prints three lists:
  MAPPED   posting terms that also appear in facts.md (safe to use, in the person's words)
  GAPS     posting terms that look like skills/tools/methods but are absent from facts.md
           (do not claim; decide: omit, address in the letter, or ask the person)
  UNUSED   facts.md terms the posting never mentions (do not pad the CV with them)

Terms come from three places: references/phrases.txt (cross-profession vocabulary),
the Skills table and role headings in facts.md (the person's own vocabulary), and
capitalised words / acronyms inside the posting (likely product or tool names).

This is a hint for the keyword-mapping step, not a scoring tool. Moderate coverage
of real experience beats maximum coverage (see references/ai-era-guidelines.md, rule 2).
"""
import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from jprw_config import default_facts  # noqa: E402

PHRASES_FILE = HERE.parent / "references" / "phrases.txt"

STOP = set("""
a an and are as at be been being by for from has have in into is it its of on or that the this to
was were will with you your we our their they them who what which when where how not can may
should must also than then there these those such more most other some any all each per via
able about above across after before between during within without under over up down out
role team teams work working experience experienced years year strong good great new high
level based including include includes ensure ensuring responsible responsibility
technology technologies solution solutions it we're you'll they're what's
monday tuesday wednesday thursday friday saturday sunday january february march april may june
july august september october november december
source location contact recruiter manager director salary hours apply benefits requirements
responsibilities qualifications about company department light basic advanced
""".split())


def _variants(t: str) -> set:
    """Singular/plural spellings so 'suppliers' matches 'supplier' and 'sla' matches 'slas'."""
    v = {t, t + "s", t + "es"}
    if t.endswith("ies"):
        v.add(t[:-3] + "y")
    if t.endswith("s"):
        v.add(t[:-1])
    if t.endswith("es"):
        v.add(t[:-2])
    return v


def has(text: str, term: str) -> bool:
    return any(_contains(text, v) for v in _variants(term))


def load_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower()).strip()


def load_phrases(path: Path = PHRASES_FILE) -> list:
    if not path.exists():
        return []
    out = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        ln = ln.strip().lower()
        if ln and not ln.startswith("#"):
            out.append(ln)
    return out


PHRASES = load_phrases()


def _clean_term(t: str) -> str:
    t = re.sub(r"\(.*?\)", "", t)  # drop "(light)" style qualifiers
    t = re.sub(r"\*\*|`", "", t)
    return norm(t).strip(" .;:-")


def harvest_terms(facts: str) -> set:
    """The person's own vocabulary: Skills table cells and certification names."""
    found = set()
    in_skills = False
    for ln in facts.splitlines():
        if ln.startswith("## "):
            in_skills = ln.lower().startswith("## skills")
            continue
        if in_skills and ln.startswith("|"):
            cells = [c.strip() for c in ln.strip("|").split("|")]
            if len(cells) >= 2 and not set(cells[1]) <= set("-: "):
                if cells[0].lower() in {"group", "category"}:
                    continue
                # "ServiceNow (incident, problem, change)" → item "servicenow"; the parenthesised
                # detail is split out as its own terms.
                detail = " , ".join(re.findall(r"\((.*?)\)", cells[1]))
                items = re.sub(r"\(.*?\)", "", cells[1])
                for item in re.split(r"[,;]", items + " , " + detail):
                    c = _clean_term(item)
                    if 2 <= len(c) <= 40 and c not in STOP and not c.isdigit():
                        found.add(c)
    # Certification names on the "held" line, e.g. "ITIL 4 Foundation (2019)"
    for m in re.finditer(r"^- Certifications? held[^:]*:\s*(.*)$", facts, flags=re.MULTILINE | re.IGNORECASE):
        for item in re.split(r"[;]", m.group(1)):
            c = _clean_term(re.sub(r",?\s*[A-Z]{1,3}-?\d{3}\b", "", item))
            if 2 <= len(c) <= 60:
                found.add(c)
    return found


def _contains(text: str, term: str) -> bool:
    return re.search(r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])", text) is not None


def candidate_terms(jd: str, extra_phrases=()) -> set:
    """Terms in the posting worth checking: known phrases plus capitalised names and acronyms."""
    text = norm(jd)
    found = set()
    for ph in list(PHRASES) + list(extra_phrases):
        if _contains(text, ph):
            found.add(ph)
    # Capitalised words inside a sentence, and acronyms anywhere, are likely product/tool names.
    # Words at the start of a sentence are skipped: they are capitalised for grammar, not meaning.
    for m in re.finditer(r"\b([A-Z][A-Za-z0-9+#.-]{1,}|[A-Z]{2,})\b", jd):
        before = jd[: m.start()].rstrip()
        sentence_start = before == "" or before[-1] in ".:;!?\u2014-\u2022*#|" or before.endswith("\n")
        w = m.group(1).lower().strip(".")
        if w in STOP or len(w) < 2 or w.isdigit():
            continue
        if sentence_start and not m.group(1).isupper():
            continue
        found.add(w)
    # Drop single words already covered by a matched multi-word phrase ("power", "bi" vs "power bi").
    phrase_words = {w for ph in found if " " in ph for w in ph.split()}
    return {t for t in found if " " in t or t not in phrase_words}


def facts_for_matching(facts: str) -> str:
    """Remove the parts of facts.md that list what the person does NOT have."""
    facts = re.sub(r"^.*not held.*$", "", facts, flags=re.MULTILINE | re.IGNORECASE)
    facts = re.sub(r"^## numbers i do not have.*?(?=^## |\Z)", "", facts, flags=re.MULTILINE | re.DOTALL | re.IGNORECASE)
    facts = re.sub(r"^## open metric questions.*?(?=^## |\Z)", "", facts, flags=re.MULTILINE | re.DOTALL | re.IGNORECASE)
    facts = re.sub(r"^## corrections log.*?(?=^## |\Z)", "", facts, flags=re.MULTILINE | re.DOTALL | re.IGNORECASE)
    return facts


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("jd", type=Path)
    ap.add_argument("--facts", type=Path, default=default_facts())
    a = ap.parse_args()
    if not a.jd.exists():
        print(f"Posting file not found: {a.jd}", file=sys.stderr)
        return 2
    if a.facts is None:
        print("No --facts given and no data_dir in ~/.job-post-resume-writer/config.json. Run install.py first.", file=sys.stderr)
        return 2
    if not a.facts.exists():
        print(f"facts file not found: {a.facts}", file=sys.stderr)
        return 2

    jd = load_text(a.jd)
    facts_raw = load_text(a.facts)
    if facts_raw.lstrip().startswith("<!-- STATUS: TEMPLATE"):
        print("facts.md is still the blank template. Say 'set up my resume' to fill it first.", file=sys.stderr)
        return 2
    own = harvest_terms(facts_raw)
    facts = norm(facts_for_matching(facts_raw))
    terms = candidate_terms(jd, extra_phrases=own)

    mapped = sorted(t for t in terms if has(facts, t))
    gaps = sorted(t for t in terms if not has(facts, t))
    jd_n = norm(jd)
    unused = sorted(ph for ph in set(PHRASES) | own if has(facts, ph) and not has(jd_n, ph))

    def show(title, items, note):
        print(f"\n{title} ({len(items)}) — {note}")
        print("  " + (", ".join(items) if items else "—"))

    show("MAPPED", mapped, "in the posting and in facts.md; describe the real work with these words")
    show("GAPS", gaps, "in the posting, not in facts.md; omit, address in the letter, or ask the person")
    show("UNUSED", unused, "in facts.md, not in the posting; do not add just for coverage")
    print("\nReminder: moderate keyword coverage of real experience beats maximum coverage.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
