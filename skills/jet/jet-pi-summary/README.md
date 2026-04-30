# jet-pi-summary

Copilot skill for investigating production incidents using the Observability Data Lake (ODL). Provides three modes:

- **Timeline** — Build a chronological incident timeline from Jira + Slack data
- **Catchup** — Summarise recent discussion and action items from a PI channel
- **Post-Mortem** — Generate a markdown post-mortem template file that can be imported into google docs
- **Prod Meet** — Generate a daily production meeting host briefing as a markdown file that can be imported into google docs

## Installation

```bash
npx skills add git@github.je-labs.com:ai-platform/skills.git
```

> **Note:** Do not install the `find-skills` skill.

## Prerequisites

### Required Tools

| Tool | Purpose | Installation (MacOS/Linux) | Installation (Windows PowerShell) |
|------|---------|----------------------------|------------------------|
| `aws` | AWS CLI v2 for Athena queries | `brew install awscli` | `winget install Amazon.AWSCLI` |
| `jq` | JSON processing | `brew install jq` | `winget install jqlang.jq` |
| `python3` | Timeline parser | Pre-installed on macOS | `winget install Python.Python.3.11` |

### Optional Tools

| Tool | Purpose | Installation (MacOS/Linux) | Installation (Windows PowerShell) |
|------|---------|----------------------------|------------------------|
| `python-dateutil` | Timezone-aware timestamp parsing | `pip install python-dateutil` | `pip install python-dateutil` |

### Required Skills

| Skill | Purpose |
|-------|---------|
| `jet-aws-athena` | Provides `athena_query` for Athena query execution |

### Authentication Setup

1. **AWS credentials**: You need access to the ODL account (`528757785644`) with the `odl-privileged-members` role for `euw1-plt-prd-3`.

```bash
# Option 1: Credentials already in ~/.aws/credentials (e.g. from vault or role assumption)
# use the odl-prd credentials profile if it exists
aws sts get-caller-identity  # verify they work

# Option 2: SSO profile
aws sso login --profile <your-profile>
export AWS_PROFILE=<your-profile>
```

## Usage

Once installed, use these explicit commands:

- `pi timeline <channel>` — Build a chronological incident timeline
- `pi catchup <channel>` — Summarise recent discussion and action items
- `pi post-mortem <channel>` — Generate a pre-filled post-mortem document
- `pi prodmeet` — Generate the daily production meeting host briefing (auto-adjusts by day of week)

### Examples

```
> pi timeline pi-12345
> pi catchup pi-67890
> pi post-mortem pi-12345
> pi prodmeet
> pi prodmeet 96h    # post-Bank-Holiday override
```

## Skill Contents

- `SKILL.md` — Main skill instructions with timeline and catchup workflows
- `references/athena-queries.md` — SQL queries and table schemas for Jira PI and Slack PI data
- `references/timeline-parser.py` — Python script for merging Jira + Slack events into a chronological timeline
- `references/post-mortem-template.md` — JET post-mortem meeting template
