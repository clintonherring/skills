# Phase 3: Assess

**Goal**: Fetch current platform info, run sonic-migration-analyzer for scoring, and determine
CI/CD eligibility.

**Load**: `sonic-migration-analyzer` skill, [04-cicd-eligibility.md](04-cicd-eligibility.md)

## 3.1 Fetch Current Platform Info

Before running the analyzer, fetch current information:

1. **Chart version**:
   ```bash
   gh api --hostname github.je-labs.com /repos/helm-charts/basic-application/releases/latest | jq '.tag_name'
   ```
2. **App tier from PlatformMetadata** (reuse `APP_NAME` from Phase 1):
   ```bash
   gh api --hostname github.je-labs.com /repos/metadata/PlatformMetadata/contents/Data/global_features/{APP_NAME}.json \
     | jq -r '.content' | base64 -d | jq '.tier'
   ```

Present the chart version to the user:
> "The current basic-application chart version is **{version}**."

## 3.2 Run sonic-migration-analyzer

Invoke the **`sonic-migration-analyzer`** skill against the cloned repository from Phase 1.
The analyzer will:

- Discover and read all relevant files
- Detect the current platform (confirm CloudOps-EKS) with confidence level
- Calculate the complexity score (0-100)
- Identify blockers and warnings
- Determine CI/CD approach (Sonic Pipeline eligibility vs GitHub Actions)
- Detect runtime language, messaging patterns, dependencies
- Generate a full analysis report saved to `/tmp/`

If the analyzer reports **medium or low confidence** on platform detection, ask the user to
confirm that the service runs on CloudOps-EKS before proceeding.

## 3.3 Classify Warnings

The analyzer reports all migration concerns as warnings. After receiving the report,
classify each warning as either **handled by this skill** or a **real blocker**:

| Handled by this skill (Phases 4-6) | Real blocker (needs Phase 3b) |
|------------------------------------|-------------------------------|
| Helm chart conversion | Platform-specific domain dependencies (`*.eks.tkwy-*.io`, `*.service`, etc.) |
| Secrets / Vault migration (parallel workstream, not a blocker) | JustSayingStack (needs v7 upgrade) |
| IRSA / workload identity | Monorepo without Sonic Pipeline support |
| Istio / JWT / authz config | Missing Sonic Runtime onboarding |
| Multi-region / bulkhead setup | Any dependency requiring external team action |
| DNS migration / traffic split | |
| CI/CD pipeline conversion | |
| Namespace mapping | |

This table is not exhaustive — use judgement. If a warning describes work that a later phase
of this skill generates or configures, it's handled. If it requires action outside the
skill's control, it's a real blocker for Phase 3b.

**Important**: Secrets / Vault migration is NOT a blocker. It is a parallel workstream.
The skill generates all Vault configuration (annotations, policies, paths) in the migration
PRs. Actual secret values are created separately by the team before their first Sonic deploy.
If the analyzer listed secrets as a "Critical Blocker", reclassify it as handled and note
it as a pre-deploy requirement in the assessment summary.

## 3.4 Present Assessment

Present the analyzer's full output (score, breakdown, findings) to the user. Then add a
summary that distinguishes handled warnings from real blockers:

> **Migration Assessment: {APP_NAME}**
>
> | Field | Value |
> |-------|-------|
> | Platform | CloudOps-EKS (confirmed) |
> | Runtime | {language} |
> | Complexity | {score}/100 ({band}) |
> | Sonic Pipeline | {Eligible / Not eligible} |
> | Chart Version | {version} |
> | App Tier | {tier} |
>
> **Blockers requiring action**: {list, or "None"}
> **Warnings handled by this workflow**: {count} items — will be resolved in Phases 4-6.
> **Pre-deploy requirements**: {e.g., "Secrets migration — create secret values in OneSecrets before first Sonic deploy", or "None"}

If there are real blockers, proceed to **Phase 3b** to resolve them.
If no real blockers, skip Phase 3b.

**Gate**: Ask "Do you want to proceed?" and wait for explicit confirmation.
