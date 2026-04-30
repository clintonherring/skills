---
name: cloudops-sonic-migrator
description: "Migrate services from CloudOps-EKS to Sonic Runtime (OneEKS). Interactive skill that analyzes a service repository on CloudOps-EKS and generates PRs across multiple repositories (source app, Route53, helm-core, domain-routing, cps/projects) to complete the migration. Only for CloudOps-EKS source platform — for other platforms (Marathon, L-JE EC2, RefArch EKS, SRE-EKS, Lambda) or read-only analysis, use sonic-migration-analyzer instead. Handles Sonic Pipeline configuration inline during Phase 5 (loads sonic-pipeline as a dependency for schema reference) — do not switch to sonic-pipeline separately during a migration."
metadata:
  owner: core-platform-services-eu
---

# CloudOps-EKS to Sonic Runtime Migrator

## Overview

Migrate services from CloudOps-EKS to Sonic Runtime (OneEKS) through an interactive, multi-phase workflow. Analyzes the source repo, identifies blockers, gathers user input for key decisions, generates all necessary changes, and creates PRs in relevant repositories.

CloudOps EU clusters share the same AWS account as Sonic Runtime EU1 — no cross-account trust
needed for EU1. However, `*.eks.tkwy-*.io` private domains must all be replaced with
`*.jet-internal.com` Global DNS. Teams can deploy to any bulkhead (EU1 recommended).

## When to Use / When NOT to Use

**Use this skill when**:

- Migrating a service currently deployed on **CloudOps-EKS** to Sonic Runtime (OneEKS)
- The user mentions "CloudOps migration", "move to Sonic Runtime", "CloudOps to Sonic", "move service to OneEKS"
- The user has a repository with CloudOps-EKS deployment config and wants to generate goldenpath structure

**Do NOT use this skill when**:

- The service is on a **different source platform** (Marathon, L-JE EC2, RefArch EKS, SRE-EKS, Lambda) — use `sonic-migration-analyzer` directly for assessment, or a platform-specific migrator if available
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

| Constant               | Default Value                                                      | Purpose                    |
| ---------------------- | ------------------------------------------------------------------ | -------------------------- |
| `BACKSTAGE_BACKEND_URL` | `https://backstagebackend.eu-west-1.production.jet-internal.com`  | Backstage API backend      |
| `BACKSTAGE_UI_URL`      | `https://backstage.eu-west-1.production.jet-internal.com`         | Backstage UI (for links)   |

### Precheck Script

Run the precheck script to validate all tools and auth before starting:

```bash
bash scripts/precheck.sh
```

This checks all tools, GHE authentication, `BACKSTAGE_API_KEY` validity, and network connectivity.
Fix any failures before proceeding — see Phase 0 reference for remediation guidance per failure type.

### Dependency Skills

| Dependency Skill               | Purpose                                                                                                   | Required?                        |
| ------------------------------ | --------------------------------------------------------------------------------------------------------- | -------------------------------- |
| **`jet-company-standards`**    | GHE auth patterns, Backstage API, PlatformMetadata lookups, commit conventions, PR workflow. Used throughout. | Yes                              |
| **`sonic-migration-analyzer`** | Phase 3 — repository analysis, platform detection, complexity scoring (0-100), blocker identification.    | Yes                              |
| **`sonic-pipeline`**           | Phase 5 — `.sonic/sonic.yml` schema, field reference, runtime-specific config. Used if eligible.          | Yes (if Sonic Pipeline eligible) |
| **`jet-datadog`**              | Phase 7 — post-migration monitoring verification via `pup` CLI.                                           | No (optional)                    |

**Skill loading order**: Load `jet-company-standards` at Phase 0 for auth guidance. Load
`sonic-migration-analyzer` when entering Phase 3. Load `sonic-pipeline` when entering Phase 5
if the service is eligible. Load `jet-datadog` only if user wants monitoring verification in Phase 7.

---

## Dynamic Content Sources

**IMPORTANT**: Do NOT rely solely on hardcoded content in reference files for platform-specific
details. Always fetch current information from these authoritative sources at runtime.

> **Note**: Backstage search, GitHub Enterprise, and PlatformMetadata patterns are documented
> in full by **`jet-company-standards`**. Load that skill for troubleshooting if commands fail.

### Backstage Priority & Token Handling

**Backstage is the authoritative source** — always prioritize it over the knowledge base.
If a Backstage API call returns 401/403 (token expired) at ANY point during the migration:

1. **Stop and ask the user** for a fresh `BACKSTAGE_API_KEY` token.
2. Walk them through: open Backstage UI → DevTools → Network → filter `query` → copy
   `Authorization: Bearer eyJ...` → `export BACKSTAGE_API_KEY="eyJ..."`.
3. Re-run `bash scripts/precheck.sh backstage` to validate the new token.
4. Resume the migration from where it stopped.

**Never silently fall back to the knowledge base.** Only use reference files as a fallback
if the user explicitly says they cannot provide a token, and clearly warn them that results
may be inaccurate due to potentially stale information.

### Backstage TechDocs (search via API)

```bash
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "$BACKSTAGE_BACKEND_URL/api/search/query?term={SEARCH_TERM}&types%5B0%5D=techdocs" \
  | jq '.results[:5][] | {title: .document.title, text: .document.text[:500]}'
```

Search terms for CloudOps migration:
1. `cloudops+sonic+runtime+migration` → main migration guide
2. `cloudops+sonic+runtime+traffic+split` → traffic split procedures
3. `cloudops+environment+mapping+sonic+runtime` → environment mappings

### Key Rule

Reference files contain **procedural logic** (detection patterns, decision trees, interactive
prompts) and **structural hints** (directory layouts, patterns). For specific versions, formats,
schemas, or configuration patterns — **fetch from source**.

---

## Migration Workflow

Execute phases in order. Each phase has a dedicated reference file with full procedural details.
Load reference files **only when entering the phase** to conserve context.

```
Phase 0: Environment Precheck ...... (Automatic — validates tools, auth, dependencies)
Phase 1: Gather Input .............. (Interactive — service, repo, project, Jira)
Phase 2: Discover .................. (Automatic — Backstage fetch, repo analysis, DNS)
Phase 3: Assess .................... (Automatic — delegates to sonic-migration-analyzer)
Phase 3b: Resolve Blockers ......... (Interactive — skip if none found)
Phase 4: Configure Migration ....... (Interactive — exposure, vault, traffic split)
Phase 5: Generate Changes .......... (Automatic — includes consistency validation)
Phase 5.5: Review & Confirm ....... (Interactive — user approves before PRs)
Phase 6: Create PRs ................ (Automatic — with fork fallback)
Phase 7: Post-Migration ........... (Informational — summary, KB update, verification)
```

---

### Phase 0: Environment Precheck

Validate all required tools, authentication, and dependency skills before starting.
Load knowledge base for accumulated learnings and patterns.

**Reference**: [references/10-phase-0-precheck.md](references/10-phase-0-precheck.md)
**Load skill**: `jet-company-standards` (for GHE auth patterns and tool reference)
**Load also**: [references/01-knowledge-base.md](references/01-knowledge-base.md)

Run `bash scripts/precheck.sh` and present a pass/fail table. If any check fails, use the
remediation table in the reference to guide the user through fixing it. Gate: all required
checks must pass before proceeding.

---

### Phase 1: Gather Input

Identify the service, validate against PlatformMetadata, clone the repo, find the Sonic Runtime
project, and collect Jira context.

**Reference**: [references/11-phase-1-gather-input.md](references/11-phase-1-gather-input.md)
**Load skill**: `jet-company-standards` (for PlatformMetadata lookups and `gh` CLI patterns)

Key outputs: `APP_NAME` (canonical name from PlatformMetadata), `PROJECT_ID` (Sonic Runtime
project, validated in cps/projects), `PROJECT_BULKHEADS`, cloned repo at `/tmp/migration-{APP_NAME}`,
`JIRA_TICKET`.

---

### Phase 2: Discover

Fetch current migration docs from Backstage, analyze the cloned repo for CloudOps-EKS indicators,
run goldenpath gap analysis, trace DNS paths, and discover secrets usage.

**Reference**: [references/12-phase-2-discover.md](references/12-phase-2-discover.md)
**Load also**:
- [references/03-goldenpath-structure.md](references/03-goldenpath-structure.md) (for gap analysis)
- [references/05-dns-and-networking.md](references/05-dns-and-networking.md) (for DNS discovery procedure)
- [references/05b-dns-reference.md](references/05b-dns-reference.md) (for DNS record types, architecture, decision tree)

Key outputs: CloudOps indicators, `SERVICE_CONFIG` (port, health path, replicas, resources,
env vars, service account), goldenpath gap table, `EXPOSURE_TYPE` (internal/external/both),
`SECRETS_INVENTORY`, `VAULT_CURRENT_CONFIG`, domain reference list.

---

### Phase 3: Assess

Fetch current platform info, delegate repository analysis to `sonic-migration-analyzer`, and
determine Sonic Pipeline eligibility. Present the analyzer's full output (score, breakdown,
findings, suggestions). Classify warnings as either handled by this skill (Phases 4-6) or
real blockers requiring Phase 3b.

**Reference**: [references/13-phase-3-assess.md](references/13-phase-3-assess.md)
**Load skill**: `sonic-migration-analyzer` (for repo analysis, platform detection, scoring, blockers)
**Load also**: [references/04-cicd-eligibility.md](references/04-cicd-eligibility.md)

Key outputs: complexity score, blockers/warnings, runtime language, CI/CD eligibility,
service configuration (port, replicas, resources, env vars, Vault paths), `VAULT_CURRENT_CONFIG`.

Present assessment and **wait for explicit user confirmation** before proceeding.

---

### Phase 3b: Resolve Blockers

Address real blockers identified in Phase 3. Skip if none found. For each blocker, **attempt
auto-resolution first** (e.g., check Global DNS for upstream dependencies, verify library
versions) before presenting options to the user.

**Reference**: [references/19-phase-3b-resolve-blockers.md](references/19-phase-3b-resolve-blockers.md)
**Load also**: [references/20-mex-and-messaging.md](references/20-mex-and-messaging.md) (if messaging detected)

For each blocker that can't be auto-resolved, present in plain language with options
(fix first, defer, proceed with workaround). Blockers can be deferred — they'll be tracked
as `DEFERRED_BLOCKERS[]` and highlighted in Phase 5.5 review and Phase 7 summary.

Gate: all blockers must be resolved or explicitly deferred before proceeding.

---

### Phase 4: Configure Migration

Gather user decisions on bulkhead selection, environment mapping, DNS exposure, vault/secrets strategy, and
traffic split approach.

**Reference**: [references/14-phase-4-configure.md](references/14-phase-4-configure.md)
**Load also**:
- [references/02-environment-mapping.md](references/02-environment-mapping.md)
- [references/05-dns-and-networking.md](references/05-dns-and-networking.md) (for DNS discovery procedure)
- [references/05b-dns-reference.md](references/05b-dns-reference.md) (for DNS record types, VirtualService hosts, customRules, decision tree)
- [references/06-vault-secrets-migration.md](references/06-vault-secrets-migration.md)
- [references/07-traffic-split.md](references/07-traffic-split.md)
- [references/21-smartgateway.md](references/21-smartgateway.md) (if `jet-external.com` endpoints detected)

Key outputs: bulkhead selection, environment mapping confirmed, `VAULT_STRATEGY`, `NEEDS_WORKLOAD_ROLE`,
traffic split strategy, full plan (repos to modify, changes per repo).

Present plan and **get explicit confirmation**: "Ready to generate changes?"

---

### Phase 5: Generate Changes

Generate all code changes across up to 6 repositories using current patterns from authoritative
sources. The helmfile is replaced with a clean goldenpath structure for Sonic Runtime.

**Reference**: [references/15-phase-5-generate.md](references/15-phase-5-generate.md)
**Load skill**: `sonic-pipeline` (if eligible — for sonic.yml schema and runtime config)
**Load also**:
- [references/03-goldenpath-structure.md](references/03-goldenpath-structure.md)
- [references/08-multi-repo-changes.md](references/08-multi-repo-changes.md)
- [references/07-traffic-split.md](references/07-traffic-split.md)
- [references/05b-dns-reference.md](references/05b-dns-reference.md) (for DNS record formats, VirtualService hosts, customRules generation)
- [references/06-vault-secrets-migration.md](references/06-vault-secrets-migration.md) (if Vault configured)
- [references/09-consistency-validation.md](references/09-consistency-validation.md) (for DNS consistency check)

Generates: source repo changes (helmfile.d/, sonic.yml or workflows, Vault annotations),
Route53 records, helm-core customRules, domain-routing config, SmartGateway config,
API specifications, workload roles — as applicable.

---

### Phase 5.5: Review & Confirm

Present all generated changes for user review. This is the gate before PR creation.

**Reference**: [references/16-phase-55-review.md](references/16-phase-55-review.md)

User can: approve all, review specific files, request changes, ask questions (with dynamic
Backstage TechDocs search), or cancel. **Only explicit approval triggers Phase 6.**

---

### Phase 6: Create PRs

Create PRs in all relevant repos (up to 6) with proper branch naming, commit format, and
fork fallback.

**Reference**: [references/17-phase-6-create-prs.md](references/17-phase-6-create-prs.md)
**Load skill**: `jet-company-standards` (for commit format, PR workflow, fork fallback)
**Load also**: [references/08-multi-repo-changes.md](references/08-multi-repo-changes.md) (PR templates, review channels)

Present PR URLs and recommended merge order:
source app → cps/projects → helm-core → SmartGateway → route53/domain-routing

---

### Phase 7: Post-Migration

Present post-merge verification steps, traffic split progression, decommissioning guidance,
and update the knowledge base.

**Reference**: [references/18-phase-7-summarize.md](references/18-phase-7-summarize.md)
**Load skill**: `jet-datadog` (optional — for post-migration monitoring via `pup` CLI)

---

## Reference Loading Guide

| Phase              | Phase Reference                                                          | Additional References                                                                              | Skills                              |
| ------------------ | ------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------- | ----------------------------------- |
| Phase 0            | [10-phase-0-precheck.md](references/10-phase-0-precheck.md)             | `01-knowledge-base.md`, run `scripts/precheck.sh`                                                  | `jet-company-standards`             |
| Phase 1            | [11-phase-1-gather-input.md](references/11-phase-1-gather-input.md)     | —                                                                                                  | `jet-company-standards`             |
| Phase 2            | [12-phase-2-discover.md](references/12-phase-2-discover.md)             | `03-goldenpath-structure.md`, `05-dns-and-networking.md`, `05b-dns-reference.md`                   | —                                   |
| Phase 3            | [13-phase-3-assess.md](references/13-phase-3-assess.md)                 | `04-cicd-eligibility.md`                                                                           | `sonic-migration-analyzer`          |
| Phase 3b           | [19-phase-3b-resolve-blockers.md](references/19-phase-3b-resolve-blockers.md) | `20-mex-and-messaging.md` (if messaging detected)                                            | —                                   |
| Phase 4            | [14-phase-4-configure.md](references/14-phase-4-configure.md)           | `02-environment-mapping.md`, `05-dns-and-networking.md`, `05b-dns-reference.md`, `06-vault-secrets-migration.md`, `07-traffic-split.md`, `21-smartgateway.md` (if `jet-external.com` endpoints) | —                      |
| Phase 5            | [15-phase-5-generate.md](references/15-phase-5-generate.md)             | `03-goldenpath-structure.md`, `05b-dns-reference.md`, `08-multi-repo-changes.md`, `07-traffic-split.md`, `06-vault-secrets-migration.md`, `09-consistency-validation.md`, `21-smartgateway.md` (if `jet-external.com` endpoints) | `sonic-pipeline` (if eligible) |
| Phase 5.5          | [16-phase-55-review.md](references/16-phase-55-review.md)               | —                                                                                                  | —                                   |
| Phase 6            | [17-phase-6-create-prs.md](references/17-phase-6-create-prs.md)         | `08-multi-repo-changes.md`                                                                         | `jet-company-standards`             |
| Phase 7            | [18-phase-7-summarize.md](references/18-phase-7-summarize.md)           | `01-knowledge-base.md`                                                                             | `jet-datadog` (optional)            |

Load phase references and additional references **only when entering the phase** to conserve context.

---

## Key Rules

### CloudOps-Specific Facts

- `*.eks.tkwy-*.io` domains are **unreachable** from Sonic Runtime — all must be migrated
- CloudOps EU clusters and Sonic Runtime EU1 share the **same AWS account** — no cross-account IAM trust needed for EU1
- Non-EU1 bulkheads are in different AWS accounts — cross-account access may be needed
- Teams can deploy to **any bulkhead** (EU1 recommended, OC1 for APAC, EU2/NA1 for multi-region)
- TKWY Kafka accessible from Sonic Runtime — no migration needed
- CloudOps uses **AWS Secrets Manager** (not Vault) — migrate to OneSecrets (Vault KV v2)
- SmartGateway only for `jet-external.com` APIs (NOT brand domains via Cloudflare); Route53 needed for ALL environments
- DNS entries must **match** customRules in helm-core
- Sonic Pipeline eliminates GHA workflows (optionally keep as backup)

### Quick Tool Reference

- **PlatformMetadata lookup**: `gh api --hostname github.je-labs.com /repos/metadata/PlatformMetadata/contents/Data/global_features/{COMPONENT}.json | jq -r '.content' | base64 -d`
- **Backstage search**: `curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" "$BACKSTAGE_BACKEND_URL/api/search/query?term={TERM}&types%5B0%5D=techdocs"`
- **Datadog / pup**: Post-migration monitoring via **`jet-datadog`** skill (optional, Phase 7)
