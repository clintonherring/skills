# Data Gathering for Person Reports

> **Purpose**: Detailed instructions for gathering data when generating a report about a specific person (engineer profile, executive summary, performance review). See SKILL.md for the condensed workflow.

## Overview

When generating a report about a specific person, you must actively gather data from available sources. **Do not rely on the user providing everything** — use the tools below to research the person.

## Employee Join Date / Tenure

**Always look up when the person joined JET.** This is a key data point for any person report — it provides context for their contributions and career progression.

**Primary source — GitHub Enterprise user profile:**
```bash
gh api users/<github-username> --jq '.created_at'
```
The `created_at` field shows when the GHE account was provisioned. This typically correlates with onboarding, but it is **not** a reliable proxy for the actual hire date — the person may have joined the company before getting a GHE account, or may have had a previous account. Extract the month and year for display (e.g., "September 2021") and use it only as a platform tenure indicator, not a join date.

**Corroborating source — earliest commit:**
```bash
gh api 'search/commits?q=author:<github-username>&sort=author-date&order=asc&per_page=1' \
  --jq '.items[0].commit.author.date'
```
The earliest commit is typically a few months after account creation (onboarding period). If it's much later, the person may have worked in private repos initially.

**Not available via:**
- Jira (`acli jira`) — has no user profile/lookup subcommand
- BigQuery — no HR/people datasets are accessible in `just-data-warehouse` or `just-data`

## GitHub Activity Data

Use the GitHub API (`gh api`) to gather contribution data. Key endpoints:

```bash
# User profile (name, email, company, created_at, public_repos)
gh api users/<username>

# Commit count in a date range (check total_count)
gh api 'search/commits?q=author:<username>+author-date:>2025-01-01' --jq '.total_count'

# Pull requests authored
gh api 'search/issues?q=author:<username>+type:pr+org:<org>' --jq '.total_count'

# Repositories contributed to (recent, sorted by push date)
gh api 'users/<username>/repos?sort=pushed&per_page=30' --jq '.[].full_name'

# Organisation memberships
gh api 'users/<username>/orgs' --jq '.[].login'
```

**Tips:**
- The search API has rate limits — use `per_page=1` with `--jq '.total_count'` when you only need counts
- For date-range queries, use `author-date:YYYY-MM-DD..YYYY-MM-DD` syntax
- Org-scoped searches (`+org:just-eat-takeaway`) may fail with 422 if the org name differs from what you expect — try without the org filter first

## Jira Data

Use `acli jira` to find the person's active work items. Available subcommands: `board`, `dashboard`, `field`, `filter`, `project`, `sprint`, `workitem`.

```bash
# Search for tickets assigned to the person
acli jira workitem list --query 'assignee = "<email-or-username>" AND status != Done ORDER BY updated DESC' --limit 20

# Get a specific ticket
acli jira workitem get --key EEAIP-123
```

**Note:** `acli jira` does NOT have a user lookup command — you cannot look up user profiles or creation dates via Jira.

## BigQuery Data

If the report needs data warehouse metrics (order counts, service health, etc.), use the `jet-bq` skill. Employee/HR data is NOT available in BigQuery.

## Data Points Checklist

At minimum, gather these before writing the report:

| Data Point | Source | Command |
|-----------|--------|---------|
| **GHE account creation date** | GHE user profile | `gh api users/<user> --jq '.created_at'` |
| **Platform tenure** | Calculated | `today - account_creation_date` (time on GHE, not company tenure) |
| **Total commits** (period) | GHE search | `gh api 'search/commits?q=author:<user>+author-date:>YYYY-MM-DD'` |
| **Total PRs** (period) | GHE search | `gh api 'search/issues?q=author:<user>+type:pr'` |
| **Org count** | GHE orgs | `gh api 'users/<user>/orgs' --jq 'length'` |
| **Active repos** | GHE repos | `gh api 'users/<user>/repos?sort=pushed&per_page=10'` |
| **Current Jira items** | Jira | `acli jira workitem list --query 'assignee = ...'` |
| **Blocked items** | Jira | `acli jira workitem list --query 'assignee = ... AND status = Blocked'` |

## People Data Guardrails

**Account creation date is NOT the same as company join date.** The GHE `created_at` field tells you when the account was created on that platform — not when the person joined JET. They may have joined the company years before getting a GHE account, or they may have had a previous account. **Never present account creation date as "joined JET".**

When presenting people data:
- **Say "active on GHE since [date]"** — not "joined JET in [date]"
- **Say "X years on the platform"** — not "X years at JET"
- **Never infer job title, role, or seniority** from API data — ask the user
- **Never infer reporting lines or team membership** unless confirmed by the user
- **Never infer career progression** from commit/PR history — correlation is not causation
- If the user explicitly tells you someone's join date or title, you may use that

## Presenting Tenure Data

- **Cover page**: Use GHE account age as a supporting stat (e.g., "4.5y on GHE") — never as company tenure
- **Stat cards**: Include a "Since [Month Year]" delta under the account age value
- **Timeline**: Only show milestones you have data for — do not invent career progression
- **Body text**: Open with "Active on GHE since [Month Year], [Name]..."
