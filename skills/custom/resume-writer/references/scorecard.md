# Scorecard — review a CV against the five rules before Clinton sees it

Run `python3 scripts/cv_check.py assets/<cv>.md --jd <jd.md>` first; it catches the mechanical problems. Then score each rule by hand with the questions below, write the result to `assets/<cv>-review.md`, and iterate until every rule meets its threshold. Only then show Clinton the draft **with** the review.

Thresholds: rules 1 and 2 ≥ 8/10 (these decide whether the AI passes the CV); rules 3, 4 and 5 ≥ 7/10 (these decide whether the human does). Below threshold means rewrite, not "note and send". When a rule cannot reach threshold without information only Clinton has (a number, a Suitsupply brain dump), list the exact question under *Questions for Clinton* and say what the score would be with the answer.

## Rule 1 — can the AI read it? (87% say simple text parses best)

- One column, headings Summary / Skills / Experience / Education…, experience above education.
- No images, icons, skill bars, tables, photos, text boxes.
- 600–1050 words (two A4 pages at 10pt). If a document was produced: PDF < 2.5 MB and text can be selected.
- Score 10 if all hold; −2 per structural miss; −1 if over length.

## Rule 2 — is the fit obvious without stuffing? (tailored +84%; max keywords −21%)

- Were the employer's problems written down before any bullet? (`match.md` → *Problems*.)
- Does every lead JD term with evidence in `facts.md` appear in the CV, in Clinton's words? (`cv_check` "never says" list.)
- Does any JD term appear in the CV without evidence in `facts.md`? That is a FAIL, not a deduction.
- Is each fact said once? No key term more than 3 times in the body; no highlight that merely restates the Skills block; employer name no more than 3 times.
- Score 10 if all hold; −1 per missing lead term; −1 per repeated fact cluster; 0 if anything unsupported is claimed.

## Rule 3 — does the AI stop where it should? (thoughtful +8%; generic −9%)

- Did the bullets start from a brain dump (result / what Clinton did / how) in `facts.md`? Roles with no result in their brain dump cannot score above 6.
- Is every line something Clinton would say in an interview? First person, plain verbs, his phrases (`clinton-voice` / `voice.md`). No word from the banned list.
- One idea per bullet, ≤ ~30 words, ≤ 5 bullets per role, ≤ 2 for roles older than 15 years.
- Score 10 if all hold; −1 per fragment or banned word; −2 per role written without a brain dump.

## Rule 4 — is impact proven with numbers? (quantified +75%)

- Does each of the three most recent roles carry at least one result with a number (not only a scale number such as "1000+ stores")? Scale is good; outcome is better: time, speed, uptime, coverage, count of things changed.
- Is every bullet with a verified number written XYZ: what was achieved, measured by what, by doing what?
- Is every number in the CV present in `facts.md`? (`cv_check` FAIL otherwise.)
- Were the missing metrics asked for? Each role without an outcome number must have a concrete question in *Questions for Clinton*.
- Score: 10 if all recent roles have an outcome number in XYZ form; 7 if they have scale numbers only; 5 if any recent role has no number; 0 if any number is invented.

## Rule 5 — are AI skills proven, not listed? (60% want proof; +15 pp)

- Is the first bullet of the current role an AI achievement relevant to the JD?
- Does it say what the tooling does (inputs, what it produces, who uses it), not that Clinton "has ideas" or "is interested"?
- Is there a number on it, or a question to Clinton to get one?
- No link to the skills repository (Clinton's instruction). Proof is in the words and offered as an interview demo. If the JD leans on AI and the facts are thin, propose a small Projects entry to Clinton; do not invent one.
- Score 10 if all hold; 7 if the bullet is first and concrete but unmeasured; 5 if it is generic or filler; 0 if the repo is linked.

## Review file format

```markdown
# Review — <company> <role> — <date>

cv_check: <n> FAIL, <n> WARN (summary of what they were and what was done)

| Rule | Score | Threshold | Verdict |
|------|-------|-----------|---------|
| 1 | /10 | 8 | … |
| 2 | /10 | 8 | … |
| 3 | /10 | 7 | … |
| 4 | /10 | 7 | … |
| 5 | /10 | 7 | … |

## Fixed in this pass
- …

## Questions for Clinton (needed to reach threshold)
- <role>: <exact question> → would lift rule <n> from <x> to <y>

## Left as is, and why
- …
```

Worked example: `assets/2026-10-rituals-retail-technology-it-architect-review.md`.
