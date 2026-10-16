#!/usr/bin/env python3
"""Quick statistical read of a person's writing samples, to seed voice.md.

Usage:
    python3 voice_profile.py sample1.txt [sample2.md …] [--top 15]

Reads plain text / Markdown files (run extract_text.py first for .docx, .pdf, URLs). Reports:
  - sentence count, average and median sentence length, share of short (≤ 12 words) and long (> 25) sentences
  - first-person ratio (sentences containing I / my / me / we / our)
  - most common verbs they reach for (heuristic: words following I / we / and, plus common past-tense forms)
  - recurring two- and three-word phrases (appear in 2+ places)
  - hedging words (maybe, perhaps, I think, sort of …) and intensifiers (very, really, extremely …)
  - résumé-speak that appears in their own writing (so you know not to put it on the avoid list)
  - numbers: how often a sentence with a claim also carries a number
Stdlib only. Advisory output for the agent; nothing is written.
"""
import argparse
import re
import sys
from collections import Counter
from pathlib import Path

FIRST_PERSON = re.compile(r"\b(I|I'm|I've|I'd|my|me|we|we're|our|us)\b")
HEDGES = ["maybe", "perhaps", "i think", "i guess", "sort of", "kind of", "a bit", "somewhat", "probably",
          "possibly", "i believe", "i feel", "to be honest", "arguably"]
INTENSIFIERS = ["very", "really", "extremely", "incredibly", "highly", "truly", "hugely", "massively", "super"]
RESUME_SPEAK = ["leveraged", "leverage", "spearheaded", "drove", "synergy", "passionate", "results-driven",
                "proven track record", "cross-functional", "stakeholder alignment", "best-in-class", "dynamic",
                "seasoned", "visionary", "robust", "utilised", "utilized", "facilitated", "orchestrated", "championed"]
COMMON_VERBS = set("""
am is are was were be been being have has had do does did make made build built run ran lead led manage managed
own owned write wrote fix fixed set up ran took take taken moved move cut keep kept chase chased train trained
work worked help helped put ask asked tell told talk talked start started stop stopped use used try tried
plan planned decide decided learn learned learnt report reported design designed test tested deliver delivered
deploy deployed replace replaced change changed create created implement implemented introduce introduced
support supported review reviewed check checked track tracked measure measured solve solved
want wanted need needed think thought know knew see saw get got go went come came find found show showed
""".split())
STOP = set("""
the a an and or but if so to of in on at for with from by as is are was were be been it its this that these those
i my me we our you your they them their he she his her not no yes do does did have has had will would can could
should may might must also just very really then than there here when where what which who how all any some
""".split())


def sentences(text: str):
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    text = re.sub(r"^#+\s.*$", "", text, flags=re.MULTILINE)  # headings are not sentences
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[*_`]+", "", text)
    text = re.sub(r"^\s*[-•]\s+", "", text, flags=re.MULTILINE)
    parts = re.split(r"(?<=[.!?])\s+|\n{2,}|\n(?=[A-Z])", text)
    return [p.strip() for p in parts if len(p.split()) >= 3]


def words(s: str):
    return re.findall(r"[A-Za-z][A-Za-z'’-]*", s.lower())


def verbs(sents):
    c = Counter()
    for s in sents:
        w = words(s)
        for i, tok in enumerate(w):
            if tok in {"i", "we"} and i + 1 < len(w):
                nxt = w[i + 1]
                if nxt in {"have", "had", "am", "was", "were", "also", "then"} and i + 2 < len(w):
                    nxt = w[i + 2]
                if nxt not in STOP:
                    c[nxt] += 1
            elif tok in COMMON_VERBS and tok not in {"am", "is", "are", "was", "were", "be", "been", "being"}:
                c[tok] += 1
    return c


def ngrams(sents, n):
    c = Counter()
    for s in sents:
        w = [t for t in words(s)]
        for i in range(len(w) - n + 1):
            g = w[i:i + n]
            if g[0] in STOP and g[-1] in STOP:
                continue
            if all(t in STOP for t in g):
                continue
            c[" ".join(g)] += 1
    return c


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("samples", nargs="+", type=Path)
    ap.add_argument("--top", type=int, default=15)
    a = ap.parse_args()

    texts = []
    for p in a.samples:
        if not p.exists():
            print(f"not found: {p}", file=sys.stderr)
            return 2
        texts.append(p.read_text(encoding="utf-8", errors="replace"))
    sents = [s for t in texts for s in sentences(t)]
    if not sents:
        print("No sentences found. Are these plain-text files? Run extract_text.py on documents first.", file=sys.stderr)
        return 2

    lens = sorted(len(words(s)) for s in sents)
    avg = sum(lens) / len(lens)
    median = lens[len(lens) // 2]
    short = sum(1 for n in lens if n <= 12) / len(lens)
    long_ = sum(1 for n in lens if n > 25) / len(lens)
    fp = sum(1 for s in sents if FIRST_PERSON.search(s)) / len(sents)
    numbered = sum(1 for s in sents if re.search(r"\d", s)) / len(sents)
    lower_all = " ".join(sents).lower()

    print(f"Samples: {len(texts)} file(s), {len(sents)} sentences, {sum(lens)} words")
    print(f"\nSentence length: average {avg:.1f} words, median {median}; {short:.0%} short (≤12), {long_:.0%} long (>25)")
    print(f"First person: {fp:.0%} of sentences use I / my / we / our"
          + ("  → write CV bullets in first person" if fp >= 0.4 else "  → they write more impersonally; check whether that is them or the sample type"))
    print(f"Numbers: {numbered:.0%} of sentences carry a number")

    v = verbs(sents)
    print(f"\nVerbs they reach for ({a.top}): " + ", ".join(f"{w} ({n})" for w, n in v.most_common(a.top)))

    for n, label in ((3, "three-word"), (2, "two-word")):
        rec = [(g, c) for g, c in ngrams(sents, n).most_common(60) if c >= 2][: a.top]
        print(f"\nRecurring {label} phrases: " + (", ".join(f"\"{g}\" ({c})" for g, c in rec) if rec else "none repeated"))

    hedges = [(h, lower_all.count(h)) for h in HEDGES if lower_all.count(h)]
    intens = [(h, len(re.findall(r"\b" + h + r"\b", lower_all))) for h in INTENSIFIERS]
    intens = [(h, n) for h, n in intens if n]
    print("\nHedging: " + (", ".join(f"{h} ({n})" for h, n in hedges) if hedges else "none") )
    print("Intensifiers: " + (", ".join(f"{h} ({n})" for h, n in intens) if intens else "none"))

    rs = [(w, len(re.findall(r"(?<![a-z])" + re.escape(w) + r"(?![a-z])", lower_all))) for w in RESUME_SPEAK]
    rs = [(w, n) for w, n in rs if n]
    print("Résumé-speak they actually use: " + (", ".join(f"{w} ({n})" for w, n in rs) if rs else "none — keep the full avoid list"))

    excl = lower_all.count("!")
    print(f"Exclamation marks: {excl}" + ("  → avoid them" if excl == 0 else ""))

    longest = max(sents, key=lambda s: len(words(s)))
    shortest = min(sents, key=lambda s: len(words(s)))
    print(f"\nShortest sentence: \"{shortest}\"")
    print(f"Longest sentence:  \"{longest[:160]}{'…' if len(longest) > 160 else ''}\"")
    print("\nUse this to confirm what you read in the samples; write voice.md from the samples themselves.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
