# Matching a job description to Clinton's CV

Working files (`jd.md`, `match.md`) go in `tasks/applications/<company>-<role-slug>/`. The CV itself is saved as Markdown in the skill's `assets/` folder as `<yyyy-mm>-<company>-<role-slug>.md` (and `…-cover-letter.md` if a letter is asked for). A `.docx`/`.pdf` is produced only when Clinton asks.

## Steps

1. **Save the JD.** Paste it verbatim into `jd.md` with the company, role title, recruiter name, location/office expectation and the URL or date.
2. **Keyword scan.** Run `python3 scripts/jd_match.py jd.md` (from the skill directory). It prints JD terms that appear in `facts.md` (mapped), JD terms that look technical but do not (gaps), and the facts keywords the JD never mentions (do not pad with these). This is a hint, not the decision.
3. **Write `match.md`** using the template below. Fill the *Problems* section first, from reading the JD, before touching keywords or bullets.
4. **Choose emphasis.** Pick the two or three themes that lead; everything else supports. Record the choice and why.
5. **Draft bullets** from the brain dumps in `facts.md` in Clinton's voice (`voice.md`), XYZ where a verified number exists. One idea per bullet, ≤ ~30 words.
6. **Honesty pass.** Delete any claim that is not in `facts.md`. Move scope limits (Jamf, ServiceNow, etc.) to the letter, phrased positively.
7. **Save.** Write the CV as Markdown to `assets/<yyyy-mm>-<company>-<role-slug>.md` in the structure given in `SKILL.md`.
8. **Show Clinton** the match table and anything you left out or were unsure of. He confirms before sending.
9. **Only if asked for a document:** transcribe the Markdown into `cv.json` (schema in `scripts/build-cv.js` header; copy `examples/rituals-2026.json`), run `node scripts/build-cv.js cv.json out.docx --pdf`, validate the `.docx` with `skills/anthropic/docx/scripts/office/validate.py`, and check the PDF: 2 pages, selectable text, < 2.5 MB.

## match.md template

```markdown
# <Company> — <Role>

Recruiter: <name> · Office: <x% / days> · Source: <url/date>

## Problems this employer needs solved
1. …
2. …
3. …

## Keywords that matter (from the JD)
Lead: …, …, …
Support: …, …
Nice to have: …

## JD → evidence
| JD ask | Evidence in facts.md | Bullet / where it goes |
|--------|----------------------|------------------------|
| … | … | … |

## Honest gaps (do not fake)
- …  → how to handle (omit / letter / interview)

## Emphasis decision
Lead with: … Support with: … Leave out: …

## Open questions for Clinton
- …
```

## Worked example

`skills/custom/clinton-cv/references/rituals-retail-tech-architect.md` is the match document for the Rituals Retail Technology IT Architect role (October 2026); `assets/2026-10-rituals-retail-technology-it-architect.md` is the resulting CV and `examples/rituals-2026.json` the same content in build form. Reuse its JD → evidence table style.

## Reusable evidence by theme

| Theme | Strongest evidence |
|-------|--------------------|
| Retail store technology | CGI: 1000+ Rituals stores, Meraki, iPad POS on NewBlack, payment terminals, ~150-store rollouts; Suitsupply as second retailer |
| Vendor / supplier management | 15 years managing 3rd party vendors and contractors at Allan Gray; Rituals partner map (Veducon, CGI/NewBlack, RSG) |
| Problem management / RCA | JET incident root cause across AWS, Kubernetes, DNS, IAM with Datadog, CloudTrail, PR history |
| Standards and lifecycle | CGI design → implementation → handover; Allan Gray infrastructure direction and business cases |
| Cloud | Azure and AWS since 2016; Azure Network Engineer Associate; AWS Certified Solutions Architect – Associate; own Azure/Digital Ocean platforms |
| Identity | Entra ID for internal users, about a year at JET |
| ITSM | Jira/Confluence daily; ServiceNow store rollout training; AJBM 2014 ITSM paper |
| Security | Operational security; risk/compliance-driven controls at Allan Gray; C2M2 advice |
| Resilience / remote work | Lockdown VPN, 100% uptime since March 2020 |
| AI | AI agent skills at JET; public skills repo; SAR vision project |
| Leadership of change | Cowhills → NewBlack POS replacement team; DC-to-DC and DC-to-cloud moves |
| NL fit | Almere near Amsterdam; Arbeid vrij toegestaan, TWV niet vereist; ZZP or payroll possible |
