# Phase 6: Create PRs

**Goal**: Create PRs in all relevant repos (up to 8). Only execute after user approval in Phase 5.5.

**Load**: [09-multi-repo-changes.md](09-multi-repo-changes.md)

> **Tooling**: All `gh` CLI operations (clone, fork, push, PR create) and commit message formatting
> in this phase follow **`jet-company-standards`** conventions. That skill defines the commit
> format (`{TICKET}: Description` or `{TICKET} Description` — detect from repo history), PR
> workflow, and fork fallback patterns. Load it for auth troubleshooting or if `gh` commands fail.

## Repos that may need PRs (depending on Phase 4 decisions)

| #   | Repo                                              | Condition                                                                       |
| --- | ------------------------------------------------- | ------------------------------------------------------------------------------- |
| 1   | Source app repo                                   | Always                                                                          |
| 2   | `IFA/route53`                                     | R-record or G-record in any environment, OR gradual traffic split via GlobalDNS |
| 3   | `cps/helm-core`                                   | R-record or brand domain (anything beyond E/NG on the Istio ingress)            |
| 4   | Consul repo                                       | Consul backward compat (Q4a=Yes)                                                |
| 5   | `IFA/domain-routing`                              | Brand domain with Cloudflare (DNS, WAF, weighted endpoints)                     |
| 6   | `external-api-services/smartgatewayconfiguration` | External internet-facing endpoints (routed through SmartGateway)                |
| 7   | `api_specifications`                              | External internet-facing endpoints (if no existing BOATS spec)                  |
| 8   | `cps/projects`                                    | Vault `extra_policy_ro` update (`NEEDS_EXTRA_POLICY_RO`=true)                   |

## PR Creation Process

For each repo with changes:

1. Clone (if not cloned)
2. Branch: `{JIRA}-migrate-{service}-to-sonic`
3. Apply changes
4. Commit: `{JIRA}: Migrate {service} to Sonic Runtime`
5. Push
6. Create PR (see body templates and fork fallback strategy in `09-multi-repo-changes.md`)

**If push fails** (permissions), follow the 3-tier fallback strategy (direct push → fork → manual diff) documented in [09-multi-repo-changes.md](09-multi-repo-changes.md).

**Review channels**: See the review channels table in [09-multi-repo-changes.md](09-multi-repo-changes.md) for which Slack channel to direct users to for each repository.

**External service PRs note**: SmartGateway and api_specifications PRs typically require review from teams outside the service owner's team. Alert the user about these review requirements.

## Suggested Merge Order

Present summary of all PRs with URLs. Suggest merge order:

1. Source app repo (deploy to QA first)
2. `cps/projects` (if Vault `extra_policy_ro` — must be merged before app deploys so Vault policies are in place)
3. helm-core (if needed — enables Istio ingress for external hosts)
4. SmartGateway / api_specifications (if needed — enables external routing)
5. Route53 / domain-routing (traffic split — only after service is verified in QA/staging)
6. Consul (backward compat — can be merged in parallel with source app)
