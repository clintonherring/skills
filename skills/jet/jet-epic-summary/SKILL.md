---
name: jet-epic-summary
description: Use this skill when the user asks for an epic summary, epic overview, or wants to know what tickets are in a Jira epic. Triggered by phrases like "epic summary <EPIC-KEY>", "summarize epic <EPIC-KEY>", or "what's in epic <EPIC-KEY>". Produces a Markdown summary containing an epic overview, ticket status breakdown, key tickets table, and progress assessment. Requires `acli` (Atlassian CLI) to be installed and authenticated against the Just Eat Takeaway Jira instance. See jet-company-standards for acli setup.
metadata:
  owner: ai-platform
---

# Epic Summary Skill

You help users get a concise summary of a Jira epic and its child tickets.

## Instructions

When the user provides a Jira epic key (e.g. `COE-894`), do the following:

### Step 1: Verify Prerequisites

Before making any Jira calls, verify that `acli` is installed and authenticated:

```
command -v acli >/dev/null 2>&1 && echo "acli is installed" || echo "acli is NOT installed"
acli jira auth 2>&1 | head -5
```

If `acli` is not installed, tell the user to install it:
- **macOS/Linux:** `brew tap atlassian/acli && brew install acli`
- **Windows:** See [Atlassian CLI Windows install guide](https://developer.atlassian.com/cloud/acli/guides/install-windows/)

If not authenticated, tell them to run `acli jira auth`.

### Step 2: Fetch Epic Tickets

Run this command in the terminal, replacing `<EPIC_KEY>` with the actual epic key provided by the user:

```
acli jira workitem search --jql "\"Epic Link\"=<EPIC_KEY>" --json --fields "key,summary,status,description" --limit 100 | python3 references/parse_jira.py
```

> **Note:**
> - The `parse_jira.py` script path is relative to the skill. Make sure you run the command from the skill directory.
> - `--limit 100` is sufficient for most epics.
> - `--json` ensures structured JSON output for the parser.
> - The `acli` tool must be authenticated against the Just Eat Takeaway Jira instance (`justeattakeaway.atlassian.net`). See the **jet-company-standards** skill for setup details.

### Step 3: Summarize the Results

After getting the output, produce a well-structured summary with the following sections:

1. **Epic Overview** – A 3–5 sentence high-level summary of what the epic is about, synthesized from all the ticket summaries and descriptions.

2. **Ticket Status Breakdown** – A quick count of tickets by status (e.g., Done: 5, In Progress: 3, To Do: 2).

3. **Key Tickets** – A table of the most important/notable tickets with columns:
   | Ticket | Summary | Status | Short Description
   Pick tickets that are most meaningful to understanding the epic's scope and progress.

4. **Overall Progress Assessment** – A brief 2–3 sentence assessment of how the epic is progressing based on the status distribution of tickets.

### Formatting Rules

- Use Markdown formatting throughout.
- Ticket keys should be plain text (e.g., `COE-123`).
- Keep the summary concise but informative.
- If the epic has no tickets, state that clearly.
- If there's an error from the API, relay the error message to the user.

