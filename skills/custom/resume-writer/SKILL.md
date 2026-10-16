---
name: resume-writer
description: Writes and tailors Clinton Herring's résumé / CV and cover letters to a specific job description, in his own voice, following AI-era résumé rules (ATS-readable one-column layout, keyword mapping not stuffing, brain-dump-first bullets, XYZ metrics only from verified facts, proven AI skills). Use when the user pastes a job description, asks to tailor or rewrite a CV or résumé, write a cover letter, check a CV against a JD, or asks what to emphasise for a role. Not for session resuming (see resume-session).
---

# Resume Writer

Turns a job description plus Clinton's fact base into a tailored CV (and letter) that passes AI screening and reads like he wrote it.

Read first, every time:

- [references/facts.md](references/facts.md) — the only source of facts, with a brain dump and verified numbers per role
- [references/voice.md](references/voice.md) — how he writes; the "would he say it in an interview" test
- [references/ai-era-guidelines.md](references/ai-era-guidelines.md) — the five rules and the pre-send checklist
- [references/jd-matching.md](references/jd-matching.md) — the JD → evidence workflow and `match.md` template

## Rules that override everything

1. **No fact that is not in `facts.md`.** No invented metrics, vendors, certifications, team names or dates. If a JD needs a number Clinton has not given, ask him; do not estimate.
2. **His voice.** First person, full sentences, plain verbs, concrete numbers and product names. No résumé-speak. Rewrite anything he could not say naturally in an interview.
3. **Map, do not stuff.** Use JD words only to describe work he actually did. Moderate keyword coverage beats maximum.
4. **Scope limits go in the letter, phrased positively.** The CV body states what he has. Never claim Jamf administration, ServiceNow implementation, or Rituals employment.
5. **Clinton confirms before anything is sent.** Show him the match table and what you left out.

## Workflow

```
- [ ] 1. Save the JD to tasks/applications/<company>-<role>/jd.md
- [ ] 2. python3 scripts/jd_match.py jd.md   (mapped / gaps / unused terms)
- [ ] 3. Write match.md: employer problems → keywords that matter → JD→evidence table → gaps → emphasis
- [ ] 4. Draft bullets from the brain dumps in facts.md, in his voice, XYZ where a verified number exists
- [ ] 5. Honesty pass against facts.md; move scope limits to the letter
- [ ] 6. Write cv.json (copy examples/rituals-2026.json) → node scripts/build-cv.js cv.json <name>.docx --pdf
- [ ] 7. Validate: docx validate.py passes; PDF is 2 pages, selectable text, < 2.5 MB
- [ ] 8. Show Clinton the match table, the draft, and open questions
```

Setup once: `cd scripts && npm install` (needs the `docx` package). PDF export needs LibreOffice (`soffice`) on PATH; without it, deliver the `.docx` and tell Clinton to export the PDF himself. Validate `.docx` with `skills/anthropic/docx/scripts/office/validate.py` (`pip install defusedxml lxml`).

## Layout (rule 1 — the AI must be able to read it)

One column, A4, Calibri 10pt, these headings in this order: **Summary** (short paragraph plus up to six one-line bullets with a bold lead word) → **Skills** (four labelled keyword lines) → **Experience** (role header with right-aligned dates, a one- or two-sentence intro in his words, short bullets with one idea each) → **Projects** (only if needed for AI proof) → **Education, certifications and publication** → one line **Beyond work**. No photos, icons, graphics, tables of skill bars or multi-column layouts. Experience before education. Two pages.

`scripts/build-cv.js` produces exactly this layout from `cv.json`; do not hand-build documents.

## Bullets (rules 3 and 4)

For each role, start from the brain dump in `facts.md` (result / what Clinton did / how). Write the bullet in first person. Where `facts.md` lists a number, use XYZ: what was achieved, measured by what, by doing what. Where it does not, write the plain fact without a number. Keep bullets ≤ ~30 words, one idea each, no more than five per role, two for roles older than 15 years.

## AI proof (rule 5)

Where it fits the JD, the first bullet of the current role is the AI achievement (reusable AI agent skills for incident investigation and change review). Do not link the skills repository or any portfolio; describe the AI work in words and offer to demonstrate it in an interview. If a JD needs AI evidence the facts do not cover, propose a small project to Clinton rather than inventing one.

## Cover letter

Four to six short paragraphs in the same voice: the role and why he fits (two sentences); the most relevant experience with the JD's own problems in mind; the long-tenure proof (Allan Gray, vendors, lifecycle); current role and AI; honest scope line if needed; location and work status; "I would welcome the chance to talk about the role." Keep it to one page. Mirror the text into `tasks/applications/<company>-<role>/cover-letter.md`.

## Keeping the fact base current

When Clinton gives a new fact or correction in chat, add it to `facts.md` first (role brain dump or the relevant table), then regenerate. Record the correction so it does not come back (see the Azure/VPS note under AI proof points as the pattern). `skills/custom/clinton-cv` holds the Rituals-specific application notes and the original CV extract; this skill's `facts.md` is the canonical fact base going forward.
