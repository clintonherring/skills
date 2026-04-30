# Phase 0: Environment Precheck

**Goal**: Validate that all required tools, authentication, and dependency skills are available
before starting the migration workflow.

**Load**: **`jet-company-standards`** skill (for GHE auth patterns and tool reference)

## 0.1 Run Precheck Script

```bash
bash scripts/precheck.sh
```

Present results as a pass/fail table:

> | Check                   | Status      |
> | ----------------------- | ----------- |
> | `gh` CLI installed      | PASS / FAIL |
> | `git` installed         | PASS / FAIL |
> | `curl` installed        | PASS / FAIL |
> | `jq` installed          | PASS / FAIL |
> | `base64` working        | PASS / FAIL |
> | `kubectl` installed     | PASS / WARN |
> | `helmfile` installed    | PASS / WARN |
> | `terraform/terragrunt`  | PASS / WARN |
> | GHE network reachable   | PASS / FAIL |
> | GHE authentication      | PASS / FAIL |
> | `BACKSTAGE_API_KEY` set | PASS / FAIL |
>
> `kubectl`, `helmfile`, and `terraform/terragrunt` are WARN (not FAIL) because the agent can
> generate configs without them, but the user needs them to deploy and verify.

## 0.2 Remediation Guide

If any check fails, guide the user through fixing it using this table:

| Failed Check | How to Fix |
|---|---|
| `gh CLI` | `brew install gh` (macOS) or `sudo apt install gh` (Linux), then `gh auth login --hostname github.je-labs.com` |
| `git` | `brew install git` or `sudo apt install git` |
| `curl` / `jq` / `base64` | `brew install <tool>` or `sudo apt install <tool>` |
| GHE network | "Are you connected to the VPN? github.je-labs.com must be reachable." |
| GHE authentication | `gh auth login --hostname github.je-labs.com --web` — walk them through the browser flow |
| `BACKSTAGE_API_KEY` not set | Open <https://backstage.eu-west-1.production.jet-internal.com/>, DevTools → Network → filter `query` → copy `Authorization: Bearer eyJ...` from request headers → `export BACKSTAGE_API_KEY="eyJ..."` |
| `BACKSTAGE_API_KEY` expired (401/403) | Token is short-lived (~1 hour). Same steps as above to get a fresh one. |
| `BACKSTAGE_API_KEY` network error | VPN may be disconnected, or Backstage is down. Ask user to check VPN and retry. Do NOT fall back to knowledge base without asking. |
| `kubectl` | `brew install kubectl` or download from kubernetes.io. Needed to verify deployments and inspect running config. |
| `helmfile` | `brew install helmfile`. Needed for `helmfile diff` and `helmfile apply` to deploy to Sonic Runtime. |
| `terraform/terragrunt` | `brew install terraform` (or `brew install terragrunt`). Needed for Workload Role Terraform definitions in `cps/projects`. |

**Gate**: Do NOT proceed until all critical checks (gh, GHE auth, GHE network) pass.
`BACKSTAGE_API_KEY` is also critical — if it fails, **ask the user** to provide a valid token
before proceeding. Walk them through the steps: open Backstage UI → DevTools → Network → copy
Bearer token. Do NOT silently fall back to the knowledge base. Only use the knowledge base
as a last resort if the user explicitly says they cannot provide a token, and warn them that
migration docs may be stale and results may be inaccurate.

## 0.3 Verify Dependency Skills

```bash
for skill in jet-company-standards sonic-migration-analyzer sonic-pipeline; do
  [[ -d "$HOME/.agents/skills/$skill" ]] && echo "✅ $skill" || echo "❌ $skill — install required"
done
```

If any skill is missing, the user needs to install it before proceeding.

## 0.4 Load Knowledge Base

Read `references/01-knowledge-base.md` for accumulated learnings, environment mappings, domain
patterns, edge cases, and past migration results.

**Always cross-check against Backstage** — do NOT rely solely on hardcoded KB content. Phase 2
will fetch the latest migration docs and compare key facts. If anything has changed, update
the KB before proceeding. This ensures the agent never works from stale information.
