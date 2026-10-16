#!/usr/bin/env python3
"""Scan a job description against references/facts.md.

Usage:
    python3 jd_match.py path/to/jd.md [--facts path/to/facts.md]

Prints three lists:
  MAPPED   JD terms that also appear in facts.md (safe to use, in Clinton's words)
  GAPS     JD terms that look like skills/tools/methods but are absent from facts.md
           (do not claim; decide: omit, address in letter, or ask Clinton)
  UNUSED   facts.md keywords the JD never mentions (do not pad the CV with them)

This is a hint for the keyword-mapping step, not a scoring tool. Moderate coverage
of real experience beats maximum coverage (see ai-era-guidelines.md, rule 2).
"""
import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_FACTS = HERE.parent / "references" / "facts.md"

# Multi-word and special-cased terms worth matching as a unit.
PHRASES = [
    "problem management", "incident management", "change management", "root cause",
    "root-cause", "lifecycle management", "life cycle", "payment terminals", "payment terminal",
    "point of sale", "pos", "ipad", "ipads", "mac", "macs", "jamf", "meraki", "cisco", "entra id",
    "entra", "azure", "aws", "kubernetes", "datadog", "cloudtrail", "servicenow", "jira",
    "confluence", "itil", "itsm", "okta", "intune", "teams rooms", "mdm", "sd-wan", "wan", "lan",
    "wifi", "wi-fi", "vpn", "firewall", "ngfw", "waf", "load balancer", "proxy", "radware",
    "vmware", "newblack", "new black", "cowhills", "veducon", "rsg", "cgi", "suitsupply",
    "rituals", "retail", "store", "stores", "omnichannel", "e-commerce", "supplier", "suppliers",
    "vendor", "vendors", "contractor", "contractors", "stakeholder", "stakeholders",
    "business case", "business cases", "architecture", "architect", "standards", "standardisation",
    "standardization", "governance", "security", "c2m2", "monitoring", "observability", "ai",
    "machine learning", "automation", "python", "terraform", "linux", "windows", "docker",
    "rollout", "rollouts", "deployment", "deployments", "handover", "support", "3rd line",
    "third line", "helpdesk", "service desk", "call centre", "call center", "project management",
    "agile", "scrum", "togaf", "ccna", "ccnp", "cissp", "dutch", "english", "amsterdam",
]

STOP = set("""
a an and are as at be been being by for from has have in into is it its of on or that the this to
was were will with you your we our their they them who what which when where how not can may
should must also than then there these those such more most other some any all each per via
able about above across after before between during within without under over up down out
role team teams work working experience experienced years year strong good great new high
level based including include includes ensure ensuring responsible responsibility
technology technologies solution solutions it
""".split())


def load_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower()).strip()


def candidate_terms(jd: str) -> set:
    text = norm(jd)
    found = set()
    for ph in PHRASES:
        if re.search(r"(?<![a-z0-9])" + re.escape(ph) + r"(?![a-z0-9])", text):
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
    # Drop single words already covered by a matched multi-word phrase ("teams", "rooms" vs "teams rooms").
    phrase_words = {w for ph in found if " " in ph for w in ph.split()}
    return {t for t in found if " " in t or t not in phrase_words}


def facts_for_matching(facts: str) -> str:
    """Remove the parts of facts.md that list what Clinton does NOT have."""
    facts = re.sub(r"^not held.*$", "", facts, flags=re.MULTILINE | re.IGNORECASE)
    facts = re.sub(r"^## numbers i do not have.*?(?=^## |\Z)", "", facts, flags=re.MULTILINE | re.DOTALL | re.IGNORECASE)
    return facts


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("jd", type=Path)
    ap.add_argument("--facts", type=Path, default=DEFAULT_FACTS)
    a = ap.parse_args()
    if not a.jd.exists():
        print(f"JD file not found: {a.jd}", file=sys.stderr)
        return 2
    if not a.facts.exists():
        print(f"facts file not found: {a.facts}", file=sys.stderr)
        return 2

    jd = load_text(a.jd)
    facts = norm(facts_for_matching(load_text(a.facts)))
    terms = candidate_terms(jd)

    def in_facts(t: str) -> bool:
        return re.search(r"(?<![a-z0-9])" + re.escape(t) + r"(?![a-z0-9])", facts) is not None

    mapped = sorted(t for t in terms if in_facts(t))
    gaps = sorted(t for t in terms if not in_facts(t))
    unused = sorted(ph for ph in PHRASES if in_facts(ph) and ph not in terms)

    def show(title, items, note):
        print(f"\n{title} ({len(items)}) — {note}")
        print("  " + (", ".join(items) if items else "—"))

    show("MAPPED", mapped, "in the JD and in facts.md; describe the real work with these words")
    show("GAPS", gaps, "in the JD, not in facts.md; omit, address in the letter, or ask Clinton")
    show("UNUSED", unused, "in facts.md, not in the JD; do not add just for coverage")
    print("\nReminder: moderate keyword coverage of real experience beats maximum coverage.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
