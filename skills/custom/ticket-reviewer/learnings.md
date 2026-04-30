# Learnings

Accumulated patterns and insights from real-world ticket reviews.

## KIR Tickets
- Evidence comes from Slack, not Jira or GitHub
- Always ask user to paste the Slack messages for the relevant date
- Reviewer's job: confirm monitoring during the change, note any alerts
- False-positive PD alerts should be documented explicitly

## GitHub Group/Permission Changes
- "Groups" at JET are typically teams within an org (e.g., `IFA/gbpi`), not standalone orgs
- Check team membership first: `gh api orgs/<ORG>/teams/<TEAM>/members`
- Only fall back to org-level check if no team is found

## DNS Changes
- Always independently verify with `nslookup` -- don't trust pasted dig output alone
- Check if the record should be publicly accessible (not VPN-only)

## General
- Read ALL comments chronologically -- the full history tells the story
- Never close without user approval
- Multiple independent checks are better than one
