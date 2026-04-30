# SRE-EKS to Sonic Migrator Skill

Interactive, multi-phase skill that migrates services from SRE-EKS to Sonic Runtime (OneEKS). Analyzes a service repository, resolves blockers, and generates PRs across multiple repositories (source app, Route53, helm-core, Consul, domain-routing) to complete the migration end-to-end.

## Installation

```bash
npx skills add git@github.je-labs.com:ai-platform/skills.git
```

## Recommended Models

This skill involves complex multi-phase reasoning, multi-repo code generation, and cross-referencing across several reference documents. For best results, use a higher-end model:

| Model                 | Notes                                               |
| --------------------- | --------------------------------------------------- |
| **Claude Opus 4.6**   | Recommended — best for complex migration workflows  |
| **Claude Sonnet 4.5** | Good alternative with strong reasoning capabilities |

Lower-tier models may produce incomplete templates, miss cross-repo dependencies, or fail to follow the multi-phase workflow correctly.

## Prerequisites

### Required Tools

| Tool     | Purpose                       | Installation (MacOS/Linux)   | Installation (Windows PowerShell) |
| -------- | ----------------------------- | ---------------------------- | ---------------------- |
| `gh`     | GitHub CLI for GHE operations | `brew install gh`            | `winget install GitHub.cli` |
| `git`    | Version control               | `brew install git`           | `winget install Git.Git` |
| `curl`   | HTTP requests                 | Pre-installed on macOS/Linux | `winget install cURL.cURL` |
| `jq`     | JSON processing               | `brew install jq`            | `winget install jqlang.jq` |
| `base64` | Encoding utilities            | Pre-installed on macOS/Linux | Use PowerShell `[Convert]::ToBase64String(...)` |

### Required Skills

| Skill                      | Purpose                                   |
| -------------------------- | ----------------------------------------- |
| `sonic-migration-analyzer` | Complexity scoring and analysis (Phase 2) |
| `jet-company-standards`    | JET development standards and conventions |
| `sonic-pipeline`           | Sonic Pipeline schema reference (Phase 5) |

### Optional Skills

| Skill         | Purpose                             |
| ------------- | ----------------------------------- |
| `jet-datadog` | Post-migration observability checks |

### Authentication Setup

1. **GitHub Enterprise**:

   ```bash
   gh auth login --hostname github.je-labs.com
   ```

2. **Backstage API**:
   ```bash
   export BACKSTAGE_API_KEY="your-token-here"
   ```

## Usage

This skill is for **end-to-end migrations from SRE-EKS to Sonic Runtime only**. It is triggered when you:

- Ask to migrate a service from SRE-EKS to Sonic Runtime / OneEKS
- Provide an SRE-EKS service repository to migrate
- Need multi-repo PRs generated for an SRE-EKS migration (Route53, helm-core, Consul, domain-routing)

> **Not this skill?**
>
> - For **read-only analysis and complexity scoring** (any source platform), use `sonic-migration-analyzer`.
> - For **configuring Sonic Pipeline** (sonic.yml, workloads, deployments) without migrating, use `sonic-pipeline`.

## Migration Phases

| Phase | Name                    |
| ----- | ----------------------- |
| 0     | Environment Precheck    |
| 1     | Gather Input            |
| 2     | Analyze & Score         |
| 3     | Resolve Blockers        |
| 4     | Configure Migration     |
| 5     | Generate Changes        |
| 5.5   | Review & Confirm        |
| 6     | Create PRs              |
| 7     | Post-Migration Guidance |

## Skill Contents

- `SKILL.md` — Main skill instructions and phase workflows
- `scripts/precheck.sh` — Environment precheck validation script
- `references/` — 22 phase-specific and topic reference docs (DNS, Consul, bulkheads, SmartGateway, etc.)
- `assets/templates/` — 15 code generation templates (helmfile, sonic.yml, Route53, Consul, workflows, etc.)
