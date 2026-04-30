# CloudOps-EKS to Sonic Migrator Skill

Interactive, multi-phase skill that migrates services from CloudOps-EKS to Sonic Runtime (OneEKS). Analyzes a service repository, resolves blockers, and generates PRs across multiple repositories (source app, Route53, helm-core, domain-routing) to complete the migration end-to-end.

## Installation

```bash
npx skills add git@github.je-labs.com:ai-platform/skills.git
```

## Recommended Models

| Model                | Notes                                              |
| -------------------- | -------------------------------------------------- |
| **Claude Opus 4.6**  | Recommended — best for complex migration workflows |
| **Claude Sonnet 4.5** | Good alternative with strong reasoning             |

## Prerequisites

### Required Tools

| Tool     | Purpose                       | Installation                 |
| -------- | ----------------------------- | ---------------------------- |
| `gh`     | GitHub CLI for GHE operations | `brew install gh`            |
| `git`    | Version control               | `brew install git`           |
| `curl`   | HTTP requests                 | Pre-installed on macOS/Linux |
| `jq`     | JSON processing               | `brew install jq`            |
| `base64` | Encoding utilities            | Pre-installed on macOS/Linux |

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

1. **GitHub Enterprise**: `gh auth login --hostname github.je-labs.com`
2. **Backstage API**: `export BACKSTAGE_API_KEY="your-token-here"`

## Usage

This skill is for **end-to-end migrations from CloudOps-EKS to Sonic Runtime only**. It is triggered when you:

- Ask to migrate a service from CloudOps-EKS to Sonic Runtime / OneEKS
- Provide a CloudOps-EKS service repository to migrate
- Need multi-repo PRs generated for a CloudOps migration (Route53, helm-core, domain-routing)

> **Not this skill?**
>
> - For **read-only analysis and complexity scoring** (any source platform), use `sonic-migration-analyzer`.
> - For **configuring Sonic Pipeline** (sonic.yml, workloads, deployments) without migrating, use `sonic-pipeline`.
> - For **SRE-EKS migrations**, use `sre-eks-sonic-migrator`.

## Migration Phases

| Phase | Name                    |
| ----- | ----------------------- |
| 0     | Environment Precheck    |
| 1     | Gather Input            |
| 2     | Analyze & Score         |
| 3     | Assess & Resolve        |
| 3b    | Resolve Blockers        |
| 4     | Configure Migration     |
| 5     | Generate Changes        |
| 5.5   | Review & Confirm        |
| 6     | Create PRs              |
| 7     | Post-Migration Guidance |

## Skill Contents

- `SKILL.md` — Main skill instructions and phase workflows
- `scripts/precheck.sh` — Environment precheck validation script
- `references/` — 21 phase-specific and topic reference docs (DNS, Vault, traffic split, SmartGateway, etc.)
- `assets/templates/` — 14 code generation templates (helmfile, sonic.yml, Route53, Cloudflare, workflows, etc.)
