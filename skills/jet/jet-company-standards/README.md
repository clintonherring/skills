# JET Company Standards Skill

This skill provides JET (Just Eat Takeaway) development standards, conventions, and workflows for working with company tools and resources.

## Installation

```bash
npx skills add git@github.je-labs.com:ai-platform/skills.git
```

> **Note:** Do not install the `find-skills` skill.

## Prerequisites

### Required Tools

| Tool | Purpose | Installation (MacOS/Linux) | Installation (Windows PowerShell) |
|------|---------|----------------------------|------------------------|
| `gh` | GitHub CLI for GHE operations | `brew install gh` | `winget install GitHub.cli` |
| `acli` | Atlassian CLI for Jira | `brew tap atlassian/acli && brew install acli` | See internal Atlassian install docs |
| `confluence-cli` | Confluence CLI for documentation | `npm install -g confluence-cli` | `npm install -g confluence-cli` |
| `jq` | JSON processing | `brew install jq` | `winget install jqlang.jq` |
| `git` | Version control | `brew install git` | `winget install Git.Git` |

### Optional Tools

| Tool | Purpose | Installation (MacOS/Linux) | Installation (Windows PowerShell) |
|------|---------|----------------------------|------------------------|
| `helmfile` | Helm chart deployments | `brew install helmfile` | `scoop install helmfile` |
| `helm` | Kubernetes package manager | `brew install helm` | `winget install Helm.Helm` |
| `aws` | AWS CLI | `brew install awscli` | `winget install Amazon.AWSCLI` |

### Authentication Setup

1. **GitHub Enterprise**:
   ```bash
   gh auth login --hostname github.je-labs.com
   ```

2. **Atlassian CLI**: Follow internal documentation for `acli` authentication setup.

3. **Backstage API**:
   ```bash
   # Login (one-time, opens browser for Okta SSO)
   npx @backstage/cli auth login --backend-url https://backstagebackend.eu-west-1.production.jet-internal.com

   # Add to your shell profile (~/.zshrc, ~/.bashrc):
   export BACKSTAGE_API_KEY="$(npx @backstage/cli auth print-token)"
   ```

4. **AWS** (if needed): Configure via `aws configure` or SSO.

## Usage

Once installed, the skill is automatically triggered when you:

- Work on Jira tickets (e.g., "do PROJ-123")
- Ask about JET conventions or standards
- Need to find component repositories
- Create commits or pull requests for JET projects

## Skill Contents

- `SKILL.md` - Main skill instructions and workflows
- `references/acli.md` - Atlassian CLI (Jira) command reference
- `references/confluence-cli.md` - Confluence CLI command reference
- `references/gh.md` - GitHub CLI command reference
- `references/backstage.md` - Backstage API reference for searching docs, components, teams, and people
- `references/pmd.md` - PlatformMetadata reference for finding component repositories
