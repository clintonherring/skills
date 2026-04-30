# epic-summary

Copilot skill for summarising Jira epics. Fetches all child tickets of an epic via `acli` (Atlassian CLI) and produces a concise, structured overview.

## Installation

```bash
npx skills add git@github.je-labs.com:ai-platform/skills.git
```

## Prerequisites

### Required Tools

| Tool | Purpose | Installation (MacOS/Linux) | Installation (Windows PowerShell) |
|------|---------|----------------------------|----------------------------------|
| `acli` | Atlassian CLI for Jira queries | `brew tap atlassian/acli && brew install acli` | See [Atlassian CLI Windows install guide](https://developer.atlassian.com/cloud/acli/guides/install-windows/) |
| `python3` | Jira response parser | Pre-installed on macOS | `winget install Python.Python.3.11` |

### Authentication Setup

The skill uses `acli` to authenticate against the Just Eat Takeaway Jira instance. Run the following to authenticate:

```bash
acli jira auth
```

See the **jet-company-standards** skill for full `acli` setup details.

## Usage

Use any of these natural-language triggers:

- `epic summary <EPIC-KEY>` — Summarise the epic and its child tickets
- `summarize epic <EPIC-KEY>` — Same as above
- `what's in epic <EPIC-KEY>` — Same as above

### Examples

```
> epic summary COE-894
> summarize epic COE-123
> what's in epic COE-456
```

### Output

The skill produces a Markdown summary with:

1. **Epic Overview** — High-level description of the epic's scope
2. **Ticket Status Breakdown** — Count of tickets by status (e.g. Done: 5, In Progress: 3)
3. **Key Tickets** — Table of the most notable tickets with summary, status, and description
4. **Overall Progress Assessment** — Brief assessment of how the epic is progressing

## Skill Contents

- `SKILL.md` — Main skill instructions with the fetch-and-summarise workflow
- `references/parse_jira.py` — Python script for parsing `acli` JSON output into readable text

