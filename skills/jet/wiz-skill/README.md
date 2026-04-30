# Wiz Security Issues Skill

This skill enables retrieval and analysis of Wiz security issues and vulnerability findings via the Wiz GraphQL API. It uses `wizcli` device code authentication (browser SSO) so no service account is required.

## Installation

```bash
npx skills add git@github.je-labs.com:ai-platform/skills.git
```

## Prerequisites

### Required Tools

| Tool | Purpose | Installation (MacOS/Linux) | Installation (Windows PowerShell) |
|------|---------|----------------------------|------------------------|
| `wizcli` | Authentication (device code flow) | `brew install wizcli` or download from Wiz portal | Download from the Wiz portal |
| `jq` | JSON processing | `brew install jq` | `winget install jqlang.jq` |
| `curl` | HTTP requests | Pre-installed on macOS/Linux | `winget install cURL.cURL` |

### Authentication Setup

```bash
# Authenticate via browser SSO (no service account needed)
wizcli auth --use-device-code
```

This stores credentials in `~/.wiz/auth.json`. The skill automatically refreshes expired tokens using the stored refresh token.

## Usage

Once installed, the skill is automatically triggered when you:

- Paste a Wiz issue URL (e.g., `https://app.wiz.io/issues#...`)
- Ask about Wiz vulnerabilities or security findings
- Reference Wiz issues by ID
- Need to investigate or remediate cloud security issues

## Skill Contents

- `SKILL.md` - Main skill instructions, field reference, and workflows
- `scripts/wiz_api.sh` - Wiz GraphQL API helper functions (auth, issue lookup, issue listing)
