# Résumé guidelines for the AI era

Condensed from the "Résumé Guide for the AI Era" video Clinton supplied (analysis of hiring reports and studies covering 4,000+ hiring managers and ~2 million applications). A CV has to pass two readers: first the AI screening software, then a human. Rules 1–2 pass the AI; rules 3–5 pass the human.

## Findings behind the rules

| Finding | Number |
|---------|--------|
| AI screening reads simple text CVs more accurately than visual ones | 87% of hiring managers |
| Tailored CVs get more interviews | 5.71% vs 3.09% interview rate (+84%) |
| Highest keyword coverage gets fewer interviews than moderate coverage | −21% |
| Hiring managers see thoughtful AI use as positive | 59% |
| Hiring managers reject AI-heavy CVs with little effort | 28% |
| Quantified impact vs responsibilities only | +75% interviews |
| Hiring managers want AI skills proven, not listed | 60% (26% interview/task, 19% work examples, 15% courses) |
| Adding role-relevant AI skills (Oxford experiment) | up to +15 percentage points |
| AI only decides pass/reject | 6% of hiring managers |
| Relevant experience valued over education | 86% |

## Rule 1 — Make sure the AI can read it

- One column. Conventional headings: **Summary, Experience, Skills, Education** (plus Projects, Certifications if needed). No icons, skill bars, graphics, photos (follow local norms; NL does not need a photo).
- Export a **selectable-text PDF under 2.5 MB**. Check by opening the PDF and copying text.
- Experience above education for anyone who is not a fresh graduate.

## Rule 2 — Make the fit obvious (keyword mapping, not stuffing)

- Give the model the JD and `facts.md`. First ask: *what problems does this employer need solved?* Then: *which skills and keywords matter most?* Only then write bullets.
- **Mapping**: use the JD's words to describe work Clinton actually did. **Stuffing**: cramming every JD phrase in regardless of evidence. Moderate coverage beats maximum coverage.
- Review every suggestion; if a keyword cannot be tied to a real experience in `facts.md`, remove it.

Stuffed: "Delivered customer support, customer service and customer-focused communication to improve the customer experience."
Mapped: "Reduced customer complaints by 31% using AI to create an onboarding email sequence from help-centre documents."

## Rule 3 — Know where the AI should stop

- Thoughtful AI use (spelling, grammar, wording) helped: +8% hire probability in an MIT experiment with ~500k job seekers. Generic AI output made applications more similar and harder to rank (up to −9% screening accuracy).
- Process: (1) brain dump the raw facts per role — **result, what Clinton contributed, how** — without polishing; (2) give the JD plus the notes and ask for stronger wording **without changing any fact**; (3) keep only language Clinton could explain naturally in an interview.
- The brain dumps live in `facts.md`. Add to them before writing; do not write from thin air.

Brain dump: "Sales and support gave conflicting refund answers, so I wrote one refund guide they both use; duplicate tickets dropped by 50%."
Bullet: "Decreased duplicate tickets by 50% by creating a shared refund guide for sales and support so customers received consistent answers."

## Rule 4 — Prove impact with numbers

- Two people can have the same responsibilities and very different results. Numbers separate them.
- Metrics are not only revenue: time saved, speed, scale (stores, offices, users), accuracy, uptime, coverage.
- Ask: "Which metrics matter for each experience? Ask me clarifying questions." Then rewrite with **XYZ**: accomplished X, as measured by Y, by doing Z. **Do not add or change facts or numbers.**
- For Clinton the verified numbers are listed per role in `facts.md`; the "Numbers I do not have" section is a hard stop.

## Rule 5 — Prove AI skills

- Where possible, make the **first bullet** under a role an AI achievement relevant to the JD.
- If there is no workplace example yet, do a small project for the target role and list it under **Projects**.
- Make the proof inspectable where possible: a portfolio link or a short document per project (situation, how and why AI was used, what changed). **Clinton's instruction: do not link the skills repository.** His proof is described in words on the CV and demonstrated in the interview.
- Writing "ChatGPT" in a skills list is not proof.

## Checklist before sending

Run `python3 scripts/cv_check.py <cv>.md --jd <jd>.md` and score with `scorecard.md` first; this list is the manual backstop.

```
- [ ] One column, conventional headings, no graphics or skill bars
- [ ] Selectable-text PDF < 2.5 MB (copy a line to check)
- [ ] Employer problems and top keywords written down before bullets
- [ ] Every keyword maps to a real experience in facts.md
- [ ] Every bullet written from a brain dump (result / contribution / how)
- [ ] Numbers present where facts.md has them; none invented
- [ ] First bullet of the current role is an AI achievement (if relevant)
- [ ] No link to the skills repository; AI work described in words, offered as an interview demo
- [ ] Experience above education
- [ ] Reads in Clinton's voice (see voice.md); he could say every line in an interview
```
