---
name: resume-writer
description: Writes and tailors Clinton Herring's résumé / CV and cover letters to a specific job description, in his own voice, following AI-era résumé rules (ATS-readable one-column layout, keyword mapping not stuffing, brain-dump-first bullets, XYZ metrics only from verified facts, proven AI skills). Use when the user pastes a job description, asks to tailor or rewrite a CV or résumé, write a cover letter, check a CV against a JD, or asks what to emphasise for a role. Not for session resuming (see resume-session).
---

# Resume Writer

Turns a job description plus Clinton's fact base into a tailored CV (and letter) that passes AI screening and reads like he wrote it.

Read first, every time:

- [references/facts.md](references/facts.md) — the only source of facts, with a brain dump and verified numbers per role
- [`clinton-voice`](../clinton-voice/SKILL.md) — how he writes (habits, slogan table, guide excerpts); load before drafting
- [references/voice.md](references/voice.md) — CV-specific quick reference (patterns, banned words, rewrite examples)
- [references/ai-era-guidelines.md](references/ai-era-guidelines.md) — the five rules and the pre-send checklist
- [references/jd-matching.md](references/jd-matching.md) — the JD → evidence workflow and `match.md` template
- [references/scorecard.md](references/scorecard.md) — how to score the draft against the five rules before Clinton sees it

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
- [ ] 3. Write match.md: employer problems FIRST → keywords that matter → JD→evidence table → gaps → emphasis
- [ ] 4. Brain-dump intake: for every role the CV will lead with, check facts.md has result / what Clinton did / how
         AND an outcome number. Where it does not, ask Clinton the questions under "Open metric questions" in
         facts.md BEFORE drafting. Write his answers into facts.md.
- [ ] 5. Draft bullets from the brain dumps, in his voice, following "Writing rules" below
- [ ] 6. Honesty pass against facts.md; move scope limits to the letter
- [ ] 7. Save the CV as Markdown: assets/<yyyy-mm>-<company>-<role-slug>.md (format below)
- [ ] 8. Self-review: python3 scripts/cv_check.py assets/<cv>.md --jd jd.md; fix every FAIL; decide every WARN;
         then score by hand with references/scorecard.md into assets/<cv>-review.md. Iterate until thresholds
         are met (rules 1–2 ≥ 8, rules 3–5 ≥ 7) or the only thing missing is an answer from Clinton.
- [ ] 9. Show Clinton the draft WITH the review and the open questions. Letter, if asked: assets/<same>-cover-letter.md
- [ ] 10. Only when Clinton asks for a .docx or .pdf: transcribe the .md into cv.json (copy examples/rituals-2026.json)
          → node scripts/build-cv.js cv.json <name>.docx --pdf → validate (docx validate.py; PDF 2 pages, selectable
          text, < 2.5 MB)
```

## Writing rules (apply while drafting, not after)

These are the five rules turned into constraints on the text. `cv_check.py` tests most of them; the scorecard covers the rest.

1. **Readable.** Headings Summary → Skills → Experience → Education; experience first; no images, tables or bars; 600–1050 words.
2. **Mapped once.** Every lead JD term that `facts.md` supports appears in the CV in his words. Nothing the facts do not support appears at all. Each fact is said **once**: the Summary paragraph sets the scene, the highlights carry the six strongest claims, Skills carries keywords, bullets carry the detail. No highlight that merely restates Skills (no "Tools" line). No key term, including the employer's name, more than three times in the body.
3. **His voice from a brain dump.** No bullet is written for a role whose brain dump lacks a result; ask first. First person, plain verbs, ≤ ~30 words, one idea, ≤ 5 bullets per role, ≤ 2 for roles older than 15 years. Banned words in `voice.md`.
4. **Numbers, XYZ, verified.** Each of the three most recent roles carries at least one outcome number, written XYZ (what, measured by, how). Scale numbers (stores, staff, years) are good but do not count as outcomes. Any number not in `facts.md` is a FAIL. When the outcome number does not exist yet, write the plain fact and put the question to Clinton; never estimate.
5. **AI proven in words.** First bullet of the current role is the AI achievement when the JD can use it, and it says what the tooling takes in, what it produces and who uses it. No "I have ideas" or "I am interested in". No link to the skills repository.

## Output: Markdown first

Every CV is saved under `assets/` as a Markdown file so the text is versioned and easy to review and diff. Do not produce `.docx` or `.pdf` unless Clinton asks. One file per application, named `<yyyy-mm>-<company>-<role-slug>.md`, starting with an HTML comment: company, role, recruiter, date written, JD source. Structure (matches `build-cv.js` so it can be transcribed later):

```markdown
# Clinton Herring
**<headline>**
<contact line · links>
*<work status line>*
## Summary
<paragraph>
- **<Lead word>**  <one line>   (up to six)
## Skills
- **<Group>:** <keywords>   (four lines)
## Experience
### <Title> | <Org> — <dates>
<one- or two-sentence intro, optional>
- <bullet>
## Education, certifications and publication
- …
## Beyond work
<one line>
```

First saved CV: `assets/2026-10-rituals-retail-technology-it-architect.md`.

Setup for docx/pdf (only when asked): `cd scripts && npm install` (needs the `docx` package). PDF export needs LibreOffice (`soffice`) on PATH; without it, deliver the `.docx` and tell Clinton to export the PDF himself. Validate `.docx` with `skills/anthropic/docx/scripts/office/validate.py` (`pip install defusedxml lxml`).

## Layout (rule 1 — the AI must be able to read it)

One column, A4, Calibri 10pt, these headings in this order: **Summary** (short paragraph plus up to six one-line bullets with a bold lead word) → **Skills** (four labelled keyword lines) → **Experience** (role header with right-aligned dates, a one- or two-sentence intro in his words, short bullets with one idea each) → **Projects** (only if needed for AI proof) → **Education, certifications and publication** → one line **Beyond work**. No photos, icons, graphics, tables of skill bars or multi-column layouts. Experience before education. Two pages.

`scripts/build-cv.js` produces exactly this layout from `cv.json` when a document is requested; do not hand-build documents. The Markdown in `assets/` follows the same section order so the transcription is mechanical.

## Bullets (rules 3 and 4)

For each role, start from the brain dump in `facts.md` (result / what Clinton did / how). Write the bullet in first person. Where `facts.md` lists a number, use XYZ: what was achieved, measured by what, by doing what. Where it does not, write the plain fact without a number. Keep bullets ≤ ~30 words, one idea each, no more than five per role, two for roles older than 15 years.

## AI proof (rule 5)

Where it fits the JD, the first bullet of the current role is the AI achievement (reusable AI agent skills for incident investigation and change review). Do not link the skills repository or any portfolio; describe the AI work in words and offer to demonstrate it in an interview. If a JD needs AI evidence the facts do not cover, propose a small project to Clinton rather than inventing one.

## Cover letter

Four to six short paragraphs in the same voice: the role and why he fits (two sentences); the most relevant experience with the JD's own problems in mind; the long-tenure proof (Allan Gray, vendors, lifecycle); current role and AI; honest scope line if needed; location and work status; "I would welcome the chance to talk about the role." Keep it to one page. Save it as `assets/<yyyy-mm>-<company>-<role-slug>-cover-letter.md`.

## Keeping the fact base current

When Clinton gives a new fact or correction in chat, add it to `facts.md` first (role brain dump or the relevant table), then regenerate. Record the correction so it does not come back (see the Azure/VPS note under AI proof points as the pattern). `skills/custom/clinton-cv` holds the Rituals-specific application notes and the original CV extract; this skill's `facts.md` is the canonical fact base going forward.
