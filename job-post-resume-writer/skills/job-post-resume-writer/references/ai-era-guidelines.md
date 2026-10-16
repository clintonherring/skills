# Résumé guidelines for the AI era

Condensed from a review of hiring reports and academic studies (including MIT and Oxford experiments) covering more than 4,000 hiring managers and nearly 2 million applications. A CV has to pass two readers: first the AI screening software, then a human. Rules 1–2 pass the AI; rules 3–5 pass the human.

## Findings behind the rules

| Finding | Number |
|---------|--------|
| AI screening reads simple text CVs more accurately than visual ones | 87% of hiring managers |
| Tailored CVs get more interviews | 5.71% vs 3.09% interview rate (+84%) |
| Highest keyword coverage gets fewer interviews than moderate coverage | −21% |
| Hiring managers see thoughtful AI use as positive | 59% |
| Hiring managers reject AI-heavy CVs with little effort | 28% |
| Quantified impact vs responsibilities only | +75% interviews |
| Hiring managers want skills proven, not listed (asked about AI skills) | 60% (26% interview/task, 19% work examples, 15% courses) |
| Adding role-relevant AI skills (Oxford experiment) | up to +15 percentage points |
| AI is the final pass/reject decision maker | 6% of hiring managers |
| Relevant experience valued over education | 86% |

## Rule 1 — Make sure the AI can read it

- One column. Conventional headings: **Summary, Skills, Experience, Education** (plus Projects, Certifications if needed). No icons, skill bars, graphics, photos, text boxes or tables.
- Follow local norms (see `eu-norms.md`). Some markets expect a photo; the EU generally does not.
- Export a **selectable-text PDF under 2.5 MB** when a document is needed. Check by opening the PDF and copying a line.
- Experience above education for anyone who is not a fresh graduate.

## Rule 2 — Make the fit obvious (keyword mapping, not stuffing)

- Give the model the posting and `facts.md`. First ask: *what problems does this employer need solved?* Then: *which skills and keywords matter most?* Only then write bullets.
- **Mapping**: use the posting's words to describe work the person actually did. **Stuffing**: cramming every posting phrase in regardless of evidence. Moderate coverage beats maximum coverage.
- Review every suggestion; if a keyword cannot be tied to a real experience in `facts.md`, remove it.

Stuffed: "Delivered customer support, customer service and customer-focused communication to improve the customer experience."
Mapped: "Reduced customer complaints by 31% using AI to create an onboarding email sequence from help-centre documents."

## Rule 3 — Know where the AI should stop

- Thoughtful AI use (spelling, grammar, wording) helped: +8% hire probability in an MIT experiment with about 500k job seekers. Generic AI output made applications more similar and harder to rank (up to −9% screening accuracy).
- Process: (1) brain dump the raw facts per role — **result, what the person contributed, how** — without polishing; (2) give the posting plus the notes and ask for stronger wording **without changing any fact**; (3) keep only language the person could explain naturally in an interview.
- The brain dumps live in `facts.md`. Add to them before writing; never write from thin air.

Brain dump: "Sales and support gave conflicting refund answers, so I wrote one refund guide they both use; duplicate tickets dropped by 50%."
Bullet: "Decreased duplicate tickets by 50% by creating a shared refund guide for sales and support so customers received consistent answers."

## Rule 4 — Prove impact with numbers

- Two people can have the same responsibilities and very different results. Numbers separate them.
- Metrics are not only revenue: time saved, speed, scale (sites, users, team), accuracy, uptime, coverage, counts of things changed.
- Ask the person: "Which metrics matter for each role? I will ask clarifying questions." Then rewrite with **XYZ**: accomplished X, as measured by Y, by doing Z. **Do not add or change facts or numbers.**
- Verified numbers are listed per role in `facts.md`; the "Numbers I do not have" section is a hard stop.

## Rule 5 — Prove the skills the posting leans on

- The research asked specifically about AI skills, and the principle generalises: a skill that is only listed is not believed. Identify in `match.md` which skill the employer cares most about, and prove it.
- Where possible, make the **first bullet** under the current role the proof of that skill, relevant to the posting: what was built or done, what it produced, who uses it, with a number if one exists.
- If there is no workplace example yet, do a small project for the target role and list it under **Projects**. Never invent one.
- Make the proof inspectable where the person allows it: an approved portfolio link, or a short document per project (situation, how and why, what changed). Otherwise describe it in words and offer to demonstrate in the interview.
- Writing a tool name in a skills list is not proof.

## Checklist before sending

Run `python3 scripts/cv_check.py <cv>.md --jd <jd>.md` and score with `scorecard.md` first; this list is the manual backstop.

```
- [ ] One column, conventional headings, no graphics or skill bars
- [ ] If a PDF: selectable text, < 2.5 MB
- [ ] Employer problems and top keywords written down before bullets
- [ ] Every keyword maps to a real experience in facts.md
- [ ] Every bullet written from a brain dump (result / contribution / how)
- [ ] Numbers present where facts.md has them; none invented
- [ ] First bullet of the current role proves the skill the posting leans on
- [ ] Only approved links; otherwise proof in words, offered as an interview demo
- [ ] Experience above education
- [ ] Reads in the person's voice (voice.md); they could say every line in an interview
```
