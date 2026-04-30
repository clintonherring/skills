---
name: sre-eks-sonic-migrator
description: "Migrate services from SRE-EKS to Sonic Runtime (OneEKS). Interactive skill that analyzes a service repository on SRE-EKS and generates PRs across multiple repositories (source app, Route53, helm-core, Consul, domain-routing) to complete the migration. Only for SRE-EKS source platform — for other platforms (Marathon, L-JE EC2, RefArch EKS, Lambda) or read-only analysis, use sonic-migration-analyzer instead. Handles Sonic Pipeline configuration inline during Phase 5 (loads sonic-pipeline as a dependency for schema reference) — do not switch to sonic-pipeline separately during a migration."
metadata:
  owner: core-platform-services-eu
---

# SRE-EKS to Sonic Runtime Migrator

## Overview

Migrate services from SRE-EKS to Sonic Runtime (OneEKS) through an interactive, multi-phase workflow. Analyzes the source repo, identifies blockers, gathers user input for key decisions, generates all necessary changes, and creates PRs in relevant repositories.

SRE-EKS to Sonic Runtime is a big shift: single bulkhead to multiple bulkheads,
Consul to GlobalDNS, Legacy Takeaway Vaults to OneSecrets.

## When to Use / When NOT to Use

**Use this skill when**:

- Migrating a service currently deployed on **SRE-EKS** to Sonic Runtime (OneEKS)
- The user mentions "SRE-EKS migration", "move to Sonic Runtime", "OneEKS migration"
- The user has a repository with SRE-EKS deployment config and wants to generate goldenpath structure

**Do NOT use this skill when**:

- The service is on a **different source platform** (Marathon, L-JE EC2, RefArch EKS, Lambda, CloudOps) — use `sonic-migration-analyzer` directly for assessment, or a platform-specific migrator if available
- The service is **already on Sonic Runtime** — no migration needed
- The user only wants an **analysis/assessment** without generating changes — use `sonic-migration-analyzer`

## Prerequisites

### Required Tools

| Tool     | Purpose                                 | Installation                                     | Verification                   |
| -------- | --------------------------------------- | ------------------------------------------------ | ------------------------------ |
| `gh`     | GitHub Enterprise CLI (clone, fork, PR) | `brew install gh` or applicable to your platform | `gh --version`                 |
| `git`    | Version control                         | Pre-installed                                    | `git --version`                |
| `curl`   | Backstage API queries                   | Pre-installed on macOS/Linux                     | `curl --version`               |
| `jq`     | JSON processing                         | `brew install jq` or applicable to your platform | `jq --version`                 |
| `base64` | Decoding PlatformMetadata responses     | Pre-installed on macOS/Linux                     | `echo "dGVzdA==" \| base64 -d` |

### Required Authentication & Environment

| Requirement         | Purpose                          | Setup                                                   |
| ------------------- | -------------------------------- | ------------------------------------------------------- |
| GHE authentication  | All GitHub Enterprise operations | `gh auth login --hostname github.je-labs.com`           |
| `BACKSTAGE_API_KEY` | Backstage TechDocs search        | Export before running: `export BACKSTAGE_API_KEY="..."` |

Verify GHE auth: `gh auth status --hostname github.je-labs.com`

### Configuration Constants

The following URLs are used throughout the migration workflow. They are defined here once and
referenced as variables in all commands and reference files.

| Constant                | Default Value                                                    | Purpose                  |
| ----------------------- | ---------------------------------------------------------------- | ------------------------ |
| `BACKSTAGE_BACKEND_URL` | `https://backstagebackend.eu-west-1.production.jet-internal.com` | Backstage API backend    |
| `BACKSTAGE_UI_URL`      | `https://backstage.eu-west-1.production.jet-internal.com`        | Backstage UI (for links) |

Set these before starting:

```bash
export BACKSTAGE_BACKEND_URL="https://backstagebackend.eu-west-1.production.jet-internal.com"
export BACKSTAGE_UI_URL="https://backstage.eu-west-1.production.jet-internal.com"
```

### Precheck Script

Run the precheck script to validate all tools and auth before starting:

```bash
source scripts/precheck.sh && migrator_precheck
```

This checks all tools, GHE authentication, `BACKSTAGE_API_KEY` validity, and network connectivity.
Fix any failures before proceeding to Phase 0.

### Dependency Skills

This skill depends on other skills from the `ai-platform/skills` collection. Install them:

```bash
npx skills add git@github.je-labs.com:ai-platform/skills.git
```

| Dependency Skill               | Purpose in This Migrator                                                                                                                                                                                                                                                                                     | Required?                        |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------- |
| **`sonic-migration-analyzer`** | Phase 2 — repository analysis, platform detection, complexity scoring (0-100), blocker identification, CI/CD eligibility assessment. The migrator delegates the entire analysis phase to this skill.                                                                                                         | Yes                              |
| **`jet-company-standards`**    | Authoritative source for GitHub Enterprise (`gh` CLI with `--hostname github.je-labs.com`), Backstage TechDocs search API, PlatformMetadata lookups, Jira (`acli`) operations, commit message conventions, and PR workflow. Used throughout Phases 0-6.                                                      | Yes                              |
| **`sonic-pipeline`**           | Authoritative source for the `.sonic/sonic.yml` schema, field reference, workload configuration (resources, artifacts, deployments), and runtime-specific details (dotnet, Go, Java Maven/Gradle, Python, Redpanda Connect). Used in Phase 5 when generating sonic.yml for Sonic Pipeline eligible services. | Yes (if Sonic Pipeline eligible) |
| **`jet-datadog`**              | Datadog observability via `pup` CLI. Can be used in Phase 7 for post-migration monitoring verification (log queries, APM service checks, monitor status).                                                                                                                                                    | No (optional)                    |

**Skill loading order**: Load `jet-company-standards` at the start (Phase 0) for authentication
guidance and tool reference. Load `sonic-migration-analyzer` when entering Phase 2. Load
`sonic-pipeline` when entering Phase 5 if the service is Sonic Pipeline eligible. Load `jet-datadog`
only if the user wants Datadog verification in Phase 7.

---

## Dynamic Content Sources

**IMPORTANT**: Do NOT rely solely on hardcoded content in reference files for platform-specific
details. Always fetch current information from these authoritative sources at runtime.

> **Note**: The Backstage search, GitHub Enterprise, and PlatformMetadata patterns below are
> documented in full by the **`jet-company-standards`** skill (including authentication setup,
> error handling, and alternative approaches). Load that skill for troubleshooting if any of
> these commands fail or require auth configuration.

### Backstage TechDocs (search via API)

```bash
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "$BACKSTAGE_BACKEND_URL/api/search/query?term={SEARCH_TERM}&types%5B0%5D=techdocs" \
  | jq '.results[:5][] | {title: .document.title, text: .document.text[:500]}'
```

For the full list of search terms by topic and the GitHub Enterprise repository reference table, see [references/13-backstage-queries.md](references/13-backstage-queries.md).

### GitHub Enterprise Repositories

See [references/13-backstage-queries.md](references/13-backstage-queries.md) for the complete table of repos, clone commands, and what to fetch from each.

### Key Rule

Reference files contain **procedural logic** (detection patterns, scoring, decision trees,
interactive prompts) and **structural hints** (directory layouts, conceptual explanations).
For any specific versions, formats, schemas, or configuration patterns — **fetch from source**.

---

## Migration Workflow

Execute phases in order. Each phase has a dedicated reference file with full procedural details.
Load reference files **only when entering the phase** to conserve context. Run compaction after each phase to reset context for the next phase. The workflow is designed to be linear, but some phases may loop back (e.g., if blockers are found in Phase 2, resolve in Phase 3 and then re-analyze in Phase 2).

```
Phase 0: Environment Precheck ...... (Automatic — validates tools, auth, dependencies)
Phase 1: Gather Input .............. (Interactive)
Phase 2: Analyze & Score ........... (Automatic — delegates to sonic-migration-analyzer)
Phase 3: Resolve Blockers .......... (Interactive, conditional)
Phase 4: Configure Migration ....... (Interactive — includes DNS discovery)
Phase 5: Generate Changes .......... (Automatic — includes consistency validation)
Phase 5.5: Review & Confirm ....... (Interactive — user approves before PRs)
Phase 6: Create PRs ................ (Automatic — with fork fallback)
Phase 7: Post-Migration Guidance ... (Informational)
```

---

### Phase 0: Environment Precheck

Validate all required tools, authentication, and dependency skills before starting.

**Reference**: [references/15-phase-0-precheck.md](references/15-phase-0-precheck.md)
**Load skill**: `jet-company-standards` (for GHE auth patterns and tool reference)

Run `source scripts/precheck.sh && migrator_precheck` and present a pass/fail table. Gate: all
required checks must pass before proceeding.

---

### Phase 1: Gather Input

Identify the service, validate against PlatformMetadata, clone the repo, and collect project info.

**Reference**: [references/16-phase-1-gather-input.md](references/16-phase-1-gather-input.md)
**Load skill**: `jet-company-standards` (for PlatformMetadata lookups and `gh` CLI patterns)

Key outputs: `APP_NAME` (canonical name from PlatformMetadata), `PROJECT_ID` (Sonic Runtime
project), cloned repo at `/tmp/{repo}`, Jira ticket number.

---

### Phase 2: Analyze & Score

Fetch current platform info and delegate repository analysis to the `sonic-migration-analyzer` skill.

**Reference**: [references/17-phase-2-analyze-score.md](references/17-phase-2-analyze-score.md)
**Load skill**: `sonic-migration-analyzer` (for repo analysis, platform detection, scoring, blockers)
**Load also**: [references/04-cicd-eligibility.md](references/04-cicd-eligibility.md) (for Sonic Pipeline config details, used in Phase 5)

Key outputs: complexity score, blockers/warnings, runtime language, CI/CD eligibility,
service configuration (port, replicas, resources, env vars, Vault paths), `VAULT_CURRENT_CONFIG`.

---

### Phase 3: Resolve Blockers

Address blocking issues (JustSayingStack, monorepo) before proceeding. Skip if none found.

**Reference**: [references/18-phase-3-resolve-blockers.md](references/18-phase-3-resolve-blockers.md)
**Load also**: [references/07-mex-and-messaging.md](references/07-mex-and-messaging.md) (if messaging detected)

---

### Phase 4: Configure Migration

Gather user decisions on bulkheads, environments, DNS exposure, Consul backward compatibility,
SmartGateway, Vault/secrets strategy, traffic split, and cross-account AWS access.

**Reference**: [references/19-phase-4-configure.md](references/19-phase-4-configure.md)
**Load also**:

- [references/02-bulkheads-and-envs.md](references/02-bulkheads-and-envs.md)
- [references/05-dns-and-networking.md](references/05-dns-and-networking.md)
- [references/06-consul-bridge.md](references/06-consul-bridge.md)
- [references/10-dns-discovery.md](references/10-dns-discovery.md) (for Q3 — automatic DNS discovery)
- [references/11-smartgateway.md](references/11-smartgateway.md) (for Q4c, if external)
- [references/14-vault-secrets-migration.md](references/14-vault-secrets-migration.md) (for Q4e)

Key outputs: `EXPOSURE_TYPE`, bulkhead selection, environment mapping, `VAULT_STRATEGY`,
`NEEDS_WORKLOAD_ROLE`, traffic split strategy.

---

### Phase 5: Generate Changes

Generate all code changes across up to 8 repositories using current patterns from authoritative
sources. Existing SRE-EKS config is preserved until Sonic Runtime is verified.

**Reference**: [references/20-phase-5-generate.md](references/20-phase-5-generate.md)
**Load skill**: `sonic-pipeline` (if Sonic Pipeline eligible — for sonic.yml schema and runtime config)
**Load also**:

- [references/03-goldenpath-structure.md](references/03-goldenpath-structure.md)
- [references/09-multi-repo-changes.md](references/09-multi-repo-changes.md)
- [references/08-traffic-split.md](references/08-traffic-split.md)
- [references/04-cicd-eligibility.md](references/04-cicd-eligibility.md) (for test mapping)
- [references/14-vault-secrets-migration.md](references/14-vault-secrets-migration.md) (if Vault configured)
- [references/11-smartgateway.md](references/11-smartgateway.md) (if external, for config generation)
- [references/12-consistency-validation.md](references/12-consistency-validation.md) (for DNS consistency check)

Generates: source repo changes (helmfile.d/, sonic.yml or workflows, Vault annotations),
Route53 records, helm-core customRules, Consul bridge entries, domain-routing config,
SmartGateway config, API specs, workload roles — as applicable.

---

### Phase 5.5: Review & Confirm

Present all generated changes for user review. This is the gate before PR creation.

**Reference**: [references/21-phase-55-review.md](references/21-phase-55-review.md)
**Load also**: [references/13-backstage-queries.md](references/13-backstage-queries.md) (for interactive Q&A search terms)

User can: approve all, review specific files, request changes, ask questions (with dynamic
Backstage TechDocs search), or cancel. **Only explicit approval triggers Phase 6.**

---

### Phase 6: Create PRs

Create PRs in all relevant repos (up to 8) with proper branch naming, commit format, and
fork fallback.

**Reference**: [references/22-phase-6-create-prs.md](references/22-phase-6-create-prs.md)
**Load skill**: `jet-company-standards` (for commit format, PR workflow, fork fallback)
**Load also**: [references/09-multi-repo-changes.md](references/09-multi-repo-changes.md) (PR templates, review channels)

Present PR URLs and recommended merge order (source app first, then infrastructure repos,
DNS/traffic split last).

---

### Phase 7: Post-Migration Guidance

Present post-merge verification steps, traffic split progression, and decommissioning guidance.

**Reference**: [references/23-phase-7-post-migration.md](references/23-phase-7-post-migration.md)
**Load skill**: `jet-datadog` (optional — for post-migration monitoring via `pup` CLI)

Includes: QA deployment verification, Vault secret injection checks, smoke testing,
environment promotion, gradual traffic shift schedule, SRE-EKS decommissioning, and
external service steps (SmartGateway testing, API spec approval, Cloudflare verification).

---

## Reference Loading Guide

| Phase              | Phase Reference                                                             | Additional References                                                                                                                                                      | Skills                         |
| ------------------ | --------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------ |
| Phase 0            | [15-phase-0-precheck.md](references/15-phase-0-precheck.md)                 | Run `scripts/precheck.sh`                                                                                                                                                  | `jet-company-standards`        |
| Phase 1            | [16-phase-1-gather-input.md](references/16-phase-1-gather-input.md)         | —                                                                                                                                                                          | `jet-company-standards`        |
| Phase 2            | [17-phase-2-analyze-score.md](references/17-phase-2-analyze-score.md)       | `04-cicd-eligibility.md`                                                                                                                                                   | `sonic-migration-analyzer`     |
| Phase 3            | [18-phase-3-resolve-blockers.md](references/18-phase-3-resolve-blockers.md) | `07-mex-and-messaging.md` (if messaging)                                                                                                                                   | —                              |
| Phase 4            | [19-phase-4-configure.md](references/19-phase-4-configure.md)               | `02-bulkheads-and-envs.md`, `05-dns-and-networking.md`, `06-consul-bridge.md`, `10-dns-discovery.md`, `11-smartgateway.md`, `14-vault-secrets-migration.md`                | —                              |
| Phase 5            | [20-phase-5-generate.md](references/20-phase-5-generate.md)                 | `03-goldenpath-structure.md`, `09-multi-repo-changes.md`, `08-traffic-split.md`, `04-cicd-eligibility.md`, `14-vault-secrets-migration.md`, `12-consistency-validation.md` | `sonic-pipeline` (if eligible) |
| Phase 5 (external) | —                                                                           | Also `11-smartgateway.md`, `05-dns-and-networking.md` (External DNS section)                                                                                               | —                              |
| Phase 5.5          | [21-phase-55-review.md](references/21-phase-55-review.md)                   | `13-backstage-queries.md` (for Q&A search terms)                                                                                                                           | —                              |
| Phase 6            | [22-phase-6-create-prs.md](references/22-phase-6-create-prs.md)             | `09-multi-repo-changes.md` (PR templates, fork fallback, review channels)                                                                                                  | `jet-company-standards`        |
| Phase 7            | [23-phase-7-post-migration.md](references/23-phase-7-post-migration.md)     | —                                                                                                                                                                          | `jet-datadog` (optional)       |

Load phase references and additional references **only when entering the phase** to conserve context.

---

## Key Tools

All required CLI tools and authentication are listed in the [Prerequisites](#prerequisites) section.
Tool documentation, auth setup, and troubleshooting are provided by the **`jet-company-standards`** skill.

Quick reference for the most-used commands:

- **PlatformMetadata lookup**: `gh api --hostname github.je-labs.com /repos/metadata/PlatformMetadata/contents/Data/global_features/{COMPONENT}.json | jq -r '.content' | base64 -d`
- **Backstage search**: `curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" "$BACKSTAGE_BACKEND_URL/api/search/query?term={TERM}&types%5B0%5D=techdocs"`
- **Datadog / pup**: Post-migration monitoring via **`jet-datadog`** skill (optional, Phase 7)
