# Review — Rituals Retail Technology IT Architect — 16 October 2026

Review of `2026-10-rituals-retail-technology-it-architect.md` as written, before the fixes below are applied. This is the worked example for `references/scorecard.md`.

cv_check: 0 FAIL, 15 WARN — over length (1110 words); CGI ×7, Rituals ×6, POS/ServiceNow/AWS ×4; JD term "lifecycle" supported in facts but absent from the CV; one Suitsupply bullet not first person; JET role has no number; "I have ideas" filler in the AI highlight.

| Rule | Score | Threshold | Verdict |
|------|-------|-----------|---------|
| 1 | 9 | 8 | One column, right headings, experience first, 2 pages / 0.06 MB when rendered. Slightly over the word guide. |
| 2 | 7 | 8 | Well mapped (22 JD terms, only Teams Rooms and Jamf 200 unmatched) but the same facts are said three times (Summary → highlights → Skills → bullets); "Tools" highlight restates Skills; "lifecycle" never said although the CGI work supports it. |
| 3 | 7 | 7 | Voice is Clinton's; no banned words. Suitsupply and JET bullets have activity but no result because their brain dumps were built from the old CV, not from him. |
| 4 | 5 | 7 | Scale numbers everywhere (1000+ stores, ~150 stores, 1500 staff, 15 years) but only one outcome in XYZ form (VPN, 100% uptime since March 2020). JET has no number at all. |
| 5 | 5 | 7 | AI bullet is first under JET (correct) but generic; the AI highlight ends on "I have ideas". No link allowed, so the words must carry the proof and currently do not. |

## Fixable without Clinton (pending his go)
- Make the JET AI bullet concrete from facts.md: skills that pull the Jira timeline, Datadog logs, GitHub PR history and CloudTrail together and propose a root cause; a second that checks DNS, IAM and access changes against evidence before a ticket is closed. Rewrite the AI highlight the same way; drop "I have ideas".
- Add lifecycle to the CGI intro: "The work ran across the full lifecycle of the store network, from requirements and design through implementation and handover to the support teams."
- Cut the "Tools" highlight (Skills carries it). Reduce "Rituals" to two or three mentions and "CGI" to the role header plus two.
- Make the second Suitsupply bullet first person.

## Questions for Clinton (needed to reach threshold)
- CGI: ~150 stores over how many months and countries; on schedule; stores per week at peak? → rule 4 from 5 to 7+
- Cowhills → NewBlack: stores migrated in your time, period, any downtime figure? → rule 4
- JET AI skills: investigation time before vs with the skill; incidents it has been used on; engineers using it? → rules 4 and 5 to 8+
- JET Entra: roughly how many internal users? → rule 4
- Suitsupply: stores/countries; what you delivered (standard, design, rollout) and what changed → rules 3 and 4
- Allan Gray vendors: number of vendors/contracts, any SLA or renegotiation result? → rule 4
- VPN: how many days to build; how many users carried? (LinkedIn post, April 2020) → rule 4
- Cloud moves: how many workloads or what share of the estate moved to Azure/AWS? → rule 4

## Left as is, and why
- Two-sentence bullets for Prudential and Abvest exceed 30 words but are the only bullet in each role; acceptable for roles 15+ years old.
- "Beyond work" heading kept; harmless to parsers and Clinton's preference.
