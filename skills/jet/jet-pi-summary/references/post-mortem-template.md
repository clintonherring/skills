# Post-Mortem Template

*Facilitator starts with a summary of the structure of the meeting, clarifies the goals, reminds people this isn't about blame, it's about learning, encourages everyone to participate (both in helping with the notes and in talking).*

*"The unexpected happens, and we all know it, so perfection is not the focus. Instead, the focus is on learning, future prevention, and minimising impact".*

*(Part 1/2)*
What happened?

**Summary of root cause:**
\<A brief description of the problem and the root cause as understood\>

**Impact:**
\<A brief description of the impact of the issue, eg. All sites down for X hrs, Increased user errors for X mins, Slow responses for 50% of users during peak, Restaurants were unable to receive orders for X mins, etc.\>

What happened pre incident?

*Tell the story of the pre-incident.*

*Topics ideas to cover:*

* *Relevant info leading up to the incident that is relevant to affecting the incident (ie rushed change, not testing failovers)*
* *Testing and monitoring through the stages and environments (including synthetic test coverage)*
* *What stopped us spotting this prior to live?*
* *Ideas covering how to fail prior to live?*
* *In order to make sure we are capturing and aligning tickets with the correct Assignee consider using the following example format:*
  *#ACTION - Update Documentation in GBO*
  * *Assignee: Tom Jones*
  * *Link Type: [blocker / mitigates / relates to]*
* *Was this a new feature release? - If so, was it behind a feature flag?*

**Q. A related question?**
**A.** Yes. No. Maybe. Explanation.
**#ACTION:**

- Description: \<summary\>
- Assignee: \<individual / team\>
- Link Type: \<Blocker / Relates to\>

What happened during the incident itself?

*Tell the story of the incident covering off the questions below, write as if posting on a blog, have some high level timeline interspersed with relevant questions and answers*

*Example questions and topics you may want to ask/talk about:*

* *When was the first alert? Could have we spotted this earlier? If so, how?*
* *When was the first engineer response, when did the SOC become aware?*
* *What things did we try?  Were they the right thing at the right time?  What else should have we tried?*
* *How quickly did we identify the cause, how quickly did we implement the resolution?*
* *How would we resolve quicker next time?*
* *Were there steps we could have taken to restore service or reduce the impact before trying to identify the cause?*
* *Was the functionality we lost actually 'needed' could we have simply backed off/turned off/gone without?*
* *Could the incident have been avoided? If so, how?*
* *SOC's role in the incident (communications, running of tools, escalation etc)*
* *In order to make sure we are capturing and aligning tickets with the correct Assignee consider using the following example format:*
  *#ACTION - Update Documentation in GBO*
  * *Assignee: Tom Jones*
  * *Link Type: [blocker / mitigates / relates to]*

### Incident-timeline

- 00:00 Something happened
- 00:01 Something else happened
- 00:05 Another event occurred

**Q. Focussing on MTTD- How quickly did we detected the issue?**
*(Is there anything we missed or should have spotted earlier?)*
**A.** Yes. No. Maybe. Explanation.
**#ACTION:**

- Description: \<summary\>
- Assignee: \<individual / team\>
- Link Type: \<Blocker / Relates to\>

**Q. A related question?**
**A.** Yes. No. Maybe. Explanation.
**#ACTION:**

- Description: \<summary\>
- Assignee: \<individual / team\>
- Link Type: \<Blocker / Relates to\>

What happened post incident?

*Anything during the following day/evening that needs to be talked about.*
*Anything else required to close the incident down.*
*This section may not be needed and can be deleted.*

**Q. A related question?**
**A.** Yes. No. Maybe. Explanation.
**#ACTION:**

- Description: \<summary\>
- Assignee: \<individual / team\>
- Link Type: \<Blocker / Relates to\>

Who will present at Op-Exc
*Are there lessons learned here which are a good candidate for wider communication via OpExc All Hands or other comms platform?  If so, who should do it?*
**Name :**

---

What went well?

*Call out wins!*

* Post-mortem went amazingly well!

---

*(Part 2/2)*

## Capturing actions during Post-Mortem

*Based on above discussion, we need to confirm agreed actions with all teams to take forward as a priority. This should include:-*

1) *SRM lead to review and confirm the actions with the teams.*
2) *Teams are required to create a ticket (Jira) in their own project to cover the agreed actions above and link it in the PI ticket.*
3) *The created actions should clearly define if they are dependent/blocked by others, as well as having an initial assignee*
4) *The actions which need to be completed before the PI is "Mitigated" or "Risk Accepted" should be linked from the PI to the action ticket using the "blocker" or "mitigated by" link type, ie: PI-12345, with link of type "mitigated by" to AB-54321*
5) *The PI should include the team owners of any linked and outstanding action*

| *Actions Captured during Post Mortem* |  |  |
| :---- | :---- | :---- |
| ***Action*** | ***Owner(s) & Team(s)*** | ***Jira Ref*** |
|  |  |  |

*Last Actions/Notes/Reminders (SM, or mini-Retro Leader):*

* *Tidy up the post mortem and remove the prompts and anything surplus*
* *Copy and Paste the actions table into the JIRA @'ing the task owner, and including the team in the "Team Owners" PI field*
* *Save the post mortem, link to the JIRA (by actual Jira "www" Link) and copy across the Actions table*
* *Remove Jira Ref / entire Actions table from this document, and replace with link to specific Jira comment containing Actions table*
* *Ask the tech manager to mark the actions that are required to be completed for them to consider risk accepting this issue*
* *Put the post mortem on the tech blog. - Non-SM run post mortems might also be useful to share with the wider tech community, you should consider sharing this more widely.*
