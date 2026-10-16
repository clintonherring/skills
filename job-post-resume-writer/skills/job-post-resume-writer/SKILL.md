---
name: job-post-resume-writer
description: Builds a person's fact base from their existing CV, then tailors a résumé / CV and cover letter to a specific job posting in their own voice, following five AI-era résumé rules (readable by screening software, keyword mapping not stuffing, bullets from a brain dump, verified numbers in XYZ form, proof of the skill the posting leans on). Use when the user says "set up my resume", pastes a job posting or job description, asks to tailor, rewrite or check a CV or résumé, asks for a cover letter, or asks to update their facts. Produces Markdown; .docx/.pdf only on request.
---

# Job post resume writer

Turns a job posting plus the person's own facts into a tailored CV that passes AI screening and reads like they wrote it.

## Where things are

Read `~/.job-post-resume-writer/config.json` first. `data_dir` holds the person's private files; this skill folder never holds personal data.

- `<data_dir>/facts.md` — the only source of facts (template: [templates/facts.template.md](templates/facts.template.md))
- `<data_dir>/voice.md` — how they write, produced by the `my-voice` skill
- `<data_dir>/applications/<yyyy-mm>-<company>-<role>/` — `jd.md`, `match.md`, `cv.md`, `cv-review.md`, `cover-letter.md`, and documents on request

If `config.json` is missing, tell the user to run `install.py` from the repository, or (Claude Desktop) work with pasted files and skip the scripts.

Read when needed, one level deep:

- [references/ai-era-guidelines.md](references/ai-era-guidelines.md) — the five rules and the data behind them
- [references/scorecard.md](references/scorecard.md) — how to score a draft before the user sees it
- [references/jd-matching.md](references/jd-matching.md) — posting → evidence workflow and `match.md`
- [references/eu-norms.md](references/eu-norms.md) — layout and content norms for European applications

## Rules that override everything

1. **No fact that is not in `facts.md`.** No invented numbers, employers, tools, certifications, dates. If a posting wants a number the person has not given, ask; never estimate.
2. **Their voice.** Every line passes `voice.md`'s test: would they say it out loud in an interview? First person, plain verbs, concrete numbers and names, no résumé-speak.
3. **Map, do not stuff.** Use the posting's words only to describe work they actually did. Each fact said once. Moderate coverage beats maximum.
4. **Scope limits go in the letter, phrased positively.** The CV body states what they have.
5. **Links only from the approved list** in `facts.md`. Ask before adding any.
6. **The person confirms before anything is sent.** Show the match table, the review and what was left out.

## Mode 1 — First run: "set up my resume"

Trigger: `facts.md` still contains the `STATUS: TEMPLATE` line, or the user asks to set up.

1. **Get the base CV.** Ask for a file path (`.docx`, `.pdf`, `.txt`, `.md`), pasted text, or "none". For a file run `python3 scripts/extract_text.py <path>`; if it exits non-zero, ask the user to paste the text instead. With "none", interview: roles newest first, then education, then skills.
2. **Extract facts** into `facts.md` following the template sections exactly: identity, tenure, timeline with presentation rules, one `### Role` per job with a brain dump (result / what I did / how) and `Numbers I can use`, skills by group, education and certifications (and a "not held" line), proof points, personal, open metric questions, numbers I do not have, corrections log. Copy the CV's own wording into the brain dumps; do not polish yet.
3. **Show `facts.md` and correct it in chat.** Print it section by section, ask what is wrong or missing, apply corrections, repeat until they say it is right. Log each correction in the corrections table with the date.
4. **Brain-dump intake per role**, newest three roles at least. For each ask, in plain words: what was different because of your work (result); what exactly you did; how. Then: which numbers can you verify — time saved, speed, scale, counts, accuracy, uptime, money. Write the answers into the role. Anything they cannot verify goes under "Numbers I do not have".
5. **Proof of skills.** Ask which skills they expect postings to ask for and what proves each (something built, a result, a document, a demo). Ask explicitly whether any portfolio links, repositories or sites may appear on a CV; record the approved list or "none".
6. **Locale.** This version follows EU norms (`references/eu-norms.md`). Record nationality / right-to-work wording if it is not obvious from the location.
7. **Remove the `STATUS: TEMPLATE` line**, save, and hand over: "Now I need three or more samples of your own writing to build your voice profile" and follow the `my-voice` skill.

## Mode 2 — Tailor to a posting

```
- [ ] 1. Create <data_dir>/applications/<yyyy-mm>-<company>-<role-slug>/ and save the posting verbatim to jd.md
- [ ] 2. python3 scripts/jd_match.py jd.md            (MAPPED / GAPS / UNUSED terms against facts.md)
- [ ] 3. Write match.md from templates/match.template.md: employer problems FIRST, then keywords, then the
         posting → evidence table, gaps, emphasis, and "the skill the posting leans on and its proof"
- [ ] 4. Brain-dump check: each role the CV will lead with must have a result and an outcome number in facts.md.
         If not, ask the user the questions under "Open metric questions" BEFORE drafting; write the answers in.
- [ ] 5. Draft cv.md from templates/cv.template.md in their voice, following "Writing rules" below
- [ ] 6. Honesty pass: delete any claim not in facts.md; move scope limits to the letter
- [ ] 7. python3 scripts/cv_check.py cv.md --jd jd.md ; fix every FAIL; decide every WARN
- [ ] 8. Score by hand with references/scorecard.md into cv-review.md; iterate until thresholds are met
         (rules 1–2 ≥ 8/10, rules 3–5 ≥ 7/10) or the only thing missing is an answer from the user
- [ ] 9. Show the user cv.md WITH cv-review.md and the open questions. Letter if asked: cover-letter.md
- [ ] 10. Only when the user asks for .docx or .pdf:
          python3 scripts/md_to_cvjson.py cv.md cv.json && node scripts/build-cv.js cv.json cv.docx --pdf
          Check: 2 pages, selectable text, < 2.5 MB. Without Node/LibreOffice, say what is missing (install.py --check)
```

## Writing rules (apply while drafting, not after)

1. **Readable.** One column. Headings in this order: Summary → Skills → Experience → Education and certifications → Interests (optional). Experience before education. No photo, icons, tables, skill bars, text boxes. 600–1050 words. EU: A4, two pages.
2. **Mapped once.** Every lead posting term that `facts.md` supports appears in the CV in their words; nothing unsupported appears at all. The Summary paragraph sets the scene, the six highlight bullets carry the strongest claims, Skills carries keywords, role bullets carry detail. No highlight that only restates Skills. No key term, including the employer's name, more than three times in the body.
3. **Their voice, from a brain dump.** No bullet for a role whose brain dump has no result; ask first. First person, ≤ ~30 words, one idea per bullet, ≤ 5 bullets per role, ≤ 2 for roles older than 15 years. Avoid the words listed in `voice.md`.
4. **Numbers, XYZ, verified.** Each of the three most recent roles carries at least one outcome number written as what was achieved, measured by what, by doing what. Scale numbers (team size, sites, years) are good but are not outcomes. Any number not in `facts.md` is a FAIL. When no number exists, write the plain fact and put the question to the user.
5. **Prove the skill the posting leans on.** Identify it in `match.md`. The first bullet of the current role is the proof of that skill, concrete (what was built or done, what it produced, who uses it) and measured where a number exists. If the proof is an AI, data, design or similar artefact, say what it does; if a link is approved, include it. If the person has no proof yet, propose a small project to them for a Projects section; never invent one. "Interested in" and "familiar with" are not proof.

## Cover letter

Four to six short paragraphs in their voice: the role and the two things that fit best; the most relevant experience framed around the employer's problems from `match.md`; the longer-tenure proof; scope limits phrased positively if needed; location, availability and right-to-work if relevant; a plain closing line. One page. Save as `cover-letter.md`.

## Mode 3 — Update facts

Trigger: "update my facts", a new job, a correction. Open `facts.md`, apply the change in the right section, add a row to the corrections log with the date, and re-ask the brain-dump questions for any new role. Never edit a saved `cv.md` to add a fact that is not first in `facts.md`.

## Scripts

Run from this skill's folder; all read `config.json` for `data_dir` and accept explicit paths.

- `python3 scripts/extract_text.py <file-or-url>` — plain text from .docx / .pdf / .txt / .md / .html / URL; non-zero exit means fall back to pasted text
- `python3 scripts/jd_match.py <jd.md> [--facts <facts.md>]` — MAPPED / GAPS / UNUSED
- `python3 scripts/cv_check.py <cv.md> --jd <jd.md> [--facts … --voice …] [--strict]` — five-rule check
- `python3 scripts/md_to_cvjson.py <cv.md> <cv.json>` then `node scripts/build-cv.js <cv.json> <out.docx> [--pdf]`
- `python3 scripts/selftest.py` — runs the chain on the repository's `examples/`

Setup for documents, once: `cd scripts && npm install`. PDF needs LibreOffice on PATH.
