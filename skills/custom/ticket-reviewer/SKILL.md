---
name: ticket-reviewer
description: Review Jira tickets that are in Review status assigned to the current user. Use this skill whenever the user asks to review tickets, check their review queue, verify ticket work, or mentions Jira reviews. Also use when the user says "review my tickets", "what tickets need review", "check my review queue", or anything related to verifying completed work on Jira tickets before closing them.
---

# Ticket Reviewer

A skill for reviewing Jira tickets that are in Review status, verifying the work was done correctly, and closing or providing feedback.

## Prerequisites

- `acli` (Atlassian CLI) must be installed and authenticated
- `gh` (GitHub CLI) must be authenticated against `github.je-labs.com`
- `nslookup` or DNS tools available for DNS verification

If `acli` is not on PATH, see `toolkit/acli.md` for the Windows-specific location.

## Step 1: Fetch tickets in review

Use acli to search for tickets where the current user is the reviewer and the ticket is not done:

```
acli jira workitem search --jql "reviewer = currentUser() AND status != Done" --fields "key,summary,status,assignee" --json
```

Present a summary table to the user with: ticket key, summary, assignee, and status.

## Step 2: Review each ticket

For each ticket the user wants to review, follow this process:

### 2a. Get ticket details and comments

```
acli jira workitem view <KEY> --json
acli jira workitem comment list --key <KEY> --json
```

Read the description to understand what work was requested, and read the comments to understand what was done.

### 2b. Check for associated PRs

Search GitHub Enterprise for PRs whose title starts with the ticket key. This is a common convention at JET -- PRs are titled like "INF-8129 Add Ori to GBPI group".

```
gh api "search/issues?q=<TICKET-KEY>+type:pr&per_page=10" --hostname github.je-labs.com --jq ".items[] | {number, state, title, repository_url, pull_request}"
```

For each PR found:
- Check if it's **merged** (state "closed" + `pull_request.merged_at` is not null)
- Note the repository it belongs to
- Report the PR status to the user

If a ticket has associated PRs and they are all merged, that's strong evidence the work is done. If PRs are still open or unmerged, flag this -- the work may be incomplete.

Also check comments for GitHub commit/PR links (e.g. `github.je-labs.com/<org>/<repo>/commit/<sha>` or `/pull/<number>`) and verify those too.

### 2c. Verify the work based on evidence in comments

> **Note**: These verification patterns are enhanced over time. When a review reveals a novel pattern or gotcha, add it to `examples/` and update this section. Check `examples/` for detailed real-world review examples beyond what's summarised here.

The assignee should have left evidence in the comments that the work is complete. Look for verification patterns like:

#### DNS changes (dig output)
When the ticket involves DNS record changes (CNAME, A records, etc.), the assignee typically pastes a `dig` command output as proof. For example:

```
dig -t CNAME go-tracker.just-eat.es

;; ANSWER SECTION:
go-tracker.just-eat.es. 300 IN CNAME go-tracker.just-eat.es.cdn.cloudflare.net.
```

When you see a `dig` output in the comments, independently verify it:
- Run `nslookup <domain>` to confirm the record resolves correctly
- If the ticket mentions Cloudflare, search the relevant Cloudflare repo on GitHub Enterprise for the record or related PRs/commits
- If the ticket mentions the record should be publicly accessible (not VPN-only), try an HTTP request to confirm

#### GitHub group/permission changes
When the ticket involves adding users to GitHub groups or changing permissions:
- IMPORTANT: "groups" at JET are typically **teams within an org**, not standalone orgs. For example, "Add Ori to the GBPI group" means the `gbpi` team inside the `IFA` org, NOT a separate `GBPI` org.
- Check the team membership first: `gh api orgs/<ORG>/teams/<TEAM>/members --hostname github.je-labs.com -q ".[].login"`
- Example: `gh api orgs/IFA/teams/gbpi/members --hostname github.je-labs.com -q ".[].login"`
- Only fall back to org-level membership check if no team is found
- If unsure which org owns the team, check the ticket description or comments for clues (repo links, org names)

#### AWS/infrastructure changes
When the ticket involves AWS account migrations, Cloud WAN changes, or similar:
- Look for evidence that the work is complete (struck-through items, status updates)
- Check if all listed items have been addressed or if some remain

#### KIR (Key Infrastructure Review) tickets
KIR tickets are recurring review tickets (e.g. "KIR - 2026/04/09") that track infrastructure changes made on a specific date. The evidence for these tickets comes from Slack messages, not from Jira comments or GitHub.

> **See**: `examples/inf-8118-kir.md` for a real KIR review example.

When reviewing a KIR ticket:
1. Note the date in the ticket summary (e.g. "KIR - 2026/04/09")
2. Ask the user to paste the Slack message(s) from that date's KIR discussion
3. Review the pasted Slack content to confirm the changes were discussed and acknowledged
4. The reviewer adds a comment summarising what they observed during the change window -- e.g. any PagerDuty alerts received, whether they were real or false positives, and general outcome
5. Close the ticket

Example prompt to the user:
> "This is a KIR ticket for [date]. Can you paste the Slack message from that day's KIR discussion?"

#### General pattern
Always look at the comments chronologically. The assignee should have:
1. Described what they plan to do
2. Done the work
3. Posted evidence/proof it's complete
4. Moved the ticket to Review

If there's no evidence the work was completed, flag this to the user.

## Step 3: Take action

Based on the review:

### If the work is verified:
Add a comment confirming the review and close the ticket:

```
acli jira workitem comment create --key <KEY> --body "<review comment>"
acli jira workitem transition --key <KEY> --status "Closed" --yes
```

If "Closed" doesn't work as a status, try "Done".

### If the work is incomplete or unverified:
Add a comment explaining what's missing and inform the user. Do NOT close the ticket.

### If you can't verify:
Tell the user what you checked and what you couldn't confirm, and let them decide.

## Self-Improving Context

Before starting any review:
1. **Check `examples/`** for past reviews of similar ticket types or services
2. **Apply `learnings.md`** patterns -- known review criteria, common gotchas

After completing a review session:
- The user may say **"new review example"** to capture notable reviews as references

## Important notes

- Always present findings to the user before taking action (closing/commenting)
- Never close a ticket without the user's approval
- When verifying, use multiple independent checks where possible
- Read ALL comments, not just the latest one -- the full history tells the story
