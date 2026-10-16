# Matching a job description to Clinton's CV

Output of this workflow is a folder `tasks/applications/<company>-<role-slug>/` containing `jd.md`, `match.md`, `cv.json`, the generated `.docx`/`.pdf`, and (if asked) `cover-letter.md`.

## Steps

1. **Save the JD.** Paste it verbatim into `jd.md` with the company, role title, recruiter name, location/office expectation and the URL or date.
2. **Keyword scan.** Run `python3 scripts/jd_match.py jd.md` (from the skill directory). It prints JD terms that appear in `facts.md` (mapped), JD terms that look technical but do not (gaps), and the facts keywords the JD never mentions (do not pad with these). This is a hint, not the decision.
3. **Write `match.md`** using the template below. Fill the *Problems* section first, from reading the JD, before touching keywords or bullets.
4. **Choose emphasis.** Pick the two or three themes that lead; everything else supports. Record the choice and why.
5. **Draft bullets** from the brain dumps in `facts.md` in Clinton's voice (`voice.md`), XYZ where a verified number exists. One idea per bullet, ≤ ~30 words.
6. **Honesty pass.** Delete any claim that is not in `facts.md`. Move scope limits (Jamf, ServiceNow, etc.) to the letter, phrased positively.
7. **Build.** Write `cv.json` (schema in `scripts/build-cv.js` header; copy `examples/rituals-2026.json`), then `node scripts/build-cv.js cv.json out.docx --pdf`. Validate the `.docx` with `skills/anthropic/docx/scripts/office/validate.py`. Check the PDF: 2 pages, selectable text, < 2.5 MB.
8. **Show Clinton** the match table and anything you left out or were unsure of. He confirms before sending.

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

`skills/custom/clinton-cv/references/rituals-retail-tech-architect.md` is the match document for the Rituals Retail Technology IT Architect role (October 2026), and `examples/rituals-2026.json` is the resulting CV content. Reuse its JD → evidence table style.

## Reusable evidence by theme

| Theme | Strongest evidence |
|-------|--------------------|
| Retail store technology | CGI: 1000+ Rituals stores, Meraki, iPad POS on NewBlack, payment terminals, ~150-store rollouts; Suitsupply as second retailer |
| Vendor / supplier management | 15 years managing 3rd party vendors and contractors at Allan Gray; Rituals partner map (Veducon, CGI/NewBlack, RSG) |
| Problem management / RCA | JET incident root cause across AWS, Kubernetes, DNS, IAM with Datadog, CloudTrail, PR history |
| Standards and lifecycle | CGI design → implementation → handover; Allan Gray infrastructure direction and business cases |
| Cloud | Azure and AWS since 2016; Azure Network Engineer Associate; own Azure/Digital Ocean platforms |
| Identity | Entra ID for internal users, about a year at JET |
| ITSM | Jira/Confluence daily; ServiceNow store rollout training; AJBM 2014 ITSM paper |
| Security | Operational security; risk/compliance-driven controls at Allan Gray; C2M2 advice |
| Resilience / remote work | Lockdown VPN, 100% uptime since March 2020 |
| AI | AI agent skills at JET; public skills repo; SAR vision project |
| Leadership of change | Cowhills → NewBlack POS replacement team; DC-to-DC and DC-to-cloud moves |
| NL fit | Almere near Amsterdam; Arbeid vrij toegestaan, TWV niet vereist; ZZP or payroll possible |
