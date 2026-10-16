# Scorecard — review a CV against the five rules before the person sees it

Run `python3 scripts/cv_check.py cv.md --jd jd.md` first; it catches the mechanical problems. Then score each rule by hand with the questions below, write the result to `cv-review.md` (template: `templates/review.template.md`), and iterate until every rule meets its threshold. Only then show the person the draft **with** the review.

Thresholds: rules 1 and 2 ≥ 8/10 (these decide whether the AI passes the CV); rules 3, 4 and 5 ≥ 7/10 (these decide whether the human does). Below threshold means rewrite, not "note and send". When a rule cannot reach threshold without information only the person has, list the exact question under *Questions for the person* and say what the score would be with the answer.

## Rule 1 — can the AI read it? (87% say simple text parses best)

- One column, headings Summary / Skills / Experience / Education…, experience above education.
- No images, icons, skill bars, tables, photos, text boxes.
- 600–1050 words (two A4 pages at 10pt). If a document was produced: PDF < 2.5 MB and text can be selected.
- Score 10 if all hold; −2 per structural miss; −1 if over length.

## Rule 2 — is the fit obvious without stuffing? (tailored +84%; max keywords −21%)

- Were the employer's problems written down before any bullet? (`match.md` → *Problems*.)
- Does every lead posting term with evidence in `facts.md` appear in the CV, in the person's words? (`cv_check` "never says" list.)
- Does any posting term appear in the CV without evidence in `facts.md`? That is a FAIL, not a deduction.
- Is each fact said once? No key term more than 3 times in the body; no highlight that merely restates the Skills block; employer name no more than 3 times.
- Score 10 if all hold; −1 per missing lead term; −1 per repeated fact cluster; 0 if anything unsupported is claimed.

## Rule 3 — does the AI stop where it should? (thoughtful +8%; generic −9%)

- Did the bullets start from a brain dump (result / what they did / how) in `facts.md`? Roles with no result in their brain dump cannot score above 6.
- Is every line something the person would say in an interview? First person, plain verbs, their phrases (`voice.md`). No word from their avoid list or the generic banned list.
- One idea per bullet, ≤ ~30 words, ≤ 5 bullets per role, ≤ 2 for roles older than 15 years.
- Score 10 if all hold; −1 per fragment or banned word; −2 per role written without a brain dump.

## Rule 4 — is impact proven with numbers? (quantified +75%)

- Does each of the three most recent roles carry at least one result with a number (not only a scale number such as "team of 6")? Scale is good; outcome is better: time, speed, uptime, coverage, count of things changed.
- Is every bullet with a verified number written XYZ: what was achieved, measured by what, by doing what?
- Is every number in the CV present in `facts.md`? (`cv_check` FAIL otherwise.)
- Were the missing metrics asked for? Each role without an outcome number must have a concrete question in *Questions for the person*.
- Score: 10 if all recent roles have an outcome number in XYZ form; 7 if they have scale numbers only; 5 if any recent role has no number; 0 if any number is invented.

## Rule 5 — is the skill the posting leans on proven? (60% want proof; +15 pp)

- Did `match.md` name the skill the employer cares most about and the evidence for it?
- Is the first bullet of the current role that proof, relevant to the posting?
- Does it say what was built or done, what it produced and who uses it, not that the person "has ideas" or "is interested"?
- Is there a number on it, or a question to the person to get one?
- Links only from the approved list in `facts.md`. If the person has no proof yet, propose a small Projects entry; do not invent one.
- Score 10 if all hold; 7 if the bullet is first and concrete but unmeasured; 5 if it is generic or filler; 0 if an unapproved link or invented proof appears.

## Review file format

See `templates/review.template.md`. The worked example in the repository is `examples/cv-review.md`.
