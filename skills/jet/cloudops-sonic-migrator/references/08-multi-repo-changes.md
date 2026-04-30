# Multi-Repository PR Specification

## Overview

A CloudOps-EKS to Sonic Runtime migration may require changes across up to 6 repositories. For each,
use the 3-tier PR creation strategy: try direct push → fork and PR from fork → output diffs for manual application.

## Repository Links

| Repository | URL |
|------------|-----|
| IFA/route53 | https://github.je-labs.com/IFA/route53 |
| cps/helm-core | https://github.je-labs.com/cps/helm-core |
| cps/projects | https://github.je-labs.com/cps/projects |
| IFA/domain-routing | https://github.je-labs.com/IFA/domain-routing |
| SmartGateway config | https://github.je-labs.com/external-api-services/smartgatewayconfiguration |
| api_specifications | https://github.je-labs.com/Architecture/api_specifications |

## PR Conventions

- **Branch name**: `{JIRA}-migrate-{service-name}-to-sonic-runtime` (or `migrate/{service}-to-sonic-runtime` if no Jira ticket)
- **PR title**: `{JIRA}: Migrate {service-name} to Sonic Runtime - {repo purpose}`
- **PR body**: Include summary, Jira ticket link, and migration details

---

## Repository 1: Source Application Repository

**What**: Full goldenpath restructure of the service repository.

**PR body template**:
```markdown
## Summary
- Restructure repository to Sonic Runtime goldenpath format
- Add helmfile.d/ with environment-specific configuration
- Configure {Sonic Pipeline / GitHub Actions} for CI/CD
- Replace all `*.eks.tkwy-*.io` domain references with `jet-internal.com`

## Jira
[{JIRA}](https://justeattakeaway.atlassian.net/browse/{JIRA})

## Migration Details
- Source platform: CloudOps-EKS
- Target: Sonic Runtime (EU1)
- Environments: {ENV_QA}, {ENV_STG}, {ENV_PRD} (from Phase 4 Q2 mapping)
- CI/CD: {Sonic Pipeline / GitHub Actions}
```

## Repository 2: IFA/route53 (DNS Traffic Split)

**When**: Service uses R-records or G-records, or needs gradual traffic split.

**Important**: Create records for **ALL environments** (QA, staging, AND production).

**PR body template**:
```markdown
## Summary
- Add weighted CNAME records for {service-name} traffic split (CloudOps-EKS → Sonic Runtime)
- Environments: {list of environments}
- Initial weights: CloudOps=100, Sonic Runtime=0 (no traffic shift yet)

## Jira
[{JIRA}](https://justeattakeaway.atlassian.net/browse/{JIRA})

## Next Steps
After merging, gradually adjust weights to shift traffic to Sonic Runtime.
```

## Repository 3: cps/helm-core (Istio Ingress customRules)

**When**: Service uses any DNS record beyond E-record and NG-record on the Istio ingress:
- R-records, G-records, brand domains

`jet-external.com` does NOT require customRules — SmartGateway proxies to internal NG-record.

**Critical**: Hostnames in `customRules` must exactly match DNS records and VirtualService `hosts`.
Run consistency validation before creating this PR.

**PR body template**:
```markdown
## Summary
- Add Istio ingress customRules for {APP_NAME} on igw-{project-id}
- Hostnames: {list of hostnames}

## Jira
[{JIRA}](https://justeattakeaway.atlassian.net/browse/{JIRA})

## Environments
{list of clusters updated}
```

## Repository 4: IFA/domain-routing (Brand Domains)

**When**: Service is accessible on a brand domain (e.g., `takeaway.com`) AND has external endpoints.

**PR body template**:
```markdown
## Summary
- Add weighted endpoint for {service-name} brand domain traffic split
- Brand domain: {brand-domain}
- Initial weights: CloudOps=100, Sonic Runtime=0

## Jira
[{JIRA}](https://justeattakeaway.atlassian.net/browse/{JIRA})
```

## Repository 5: cps/projects (Workload Roles / Vault)

**When**: Service needs AWS access (Workload Roles) or Vault `extra_policy_ro` for secret access.

**PR body template**:
```markdown
## Summary
- {Add Workload Role for AWS access / Add extra_policy_ro for Vault secret access}
- Project: {PROJECT_ID}

## Jira
[{JIRA}](https://justeattakeaway.atlassian.net/browse/{JIRA})
```

## Repository 6: SmartGateway Configuration (External Services)

**When**: DNS Path Discovery confirmed external internet-facing endpoints routed through SmartGateway.
NOT needed for brand domains used internally only.

**Important**: SmartGateway `host` must use the **NG-record** (not E-record), `port` must be `443`,
`protocol` must be `"https"`.

**PR body template**:
```markdown
## Summary
- Add SmartGateway route configuration for {service-name}
- Routes external traffic to internal NG-record: {ng-record}

## Jira
[{JIRA}](https://justeattakeaway.atlassian.net/browse/{JIRA})

## Testing
Deploy to QA first and test via SmartGateway regional endpoints.
```

---

## PR Creation Strategy (3-Tier Fallback)

### Tier 1: Direct Push (preferred)

```
1. Clone: gh repo clone github.je-labs.com/{org}/{repo} /tmp/{repo}
2. Branch: git checkout -b {branch-name}
3. Explore repo structure, follow existing conventions
4. Apply changes
5. Commit: git add . && git commit -m "{JIRA}: Migrate {service} to Sonic Runtime"
6. Push: git push -u origin {branch-name}
7. PR: gh pr create --title "..." --body "..."
```

### Tier 2: Fork (if push fails with permissions error)

```
1. Fork: gh repo fork github.je-labs.com/{org}/{repo} --clone --remote
2. Branch: git checkout -b {branch-name}
3. Apply same changes as Tier 1
4. Push to fork: git push -u origin {branch-name}
5. PR from fork: gh pr create --title "..." --body "..." --head {username}:{branch}
```

Tell user: "Created PR from a fork. Repo owners will need to approve."

### Tier 3: Manual Diffs (if forking also fails)

- Output the **full diff/patch** the user can apply manually
- Provide exact file paths and content
- Include PR title and body template
- Tell user which Slack channel to request review in

---

## PR Merge Order (Recommended)

1. **Source app repo** — deploy to QA first to verify
2. **cps/projects** — Vault policies / Workload Roles must be in place before app needs them
3. **cps/helm-core** — enables Istio ingress for external hosts
4. **SmartGateway** — external routing (if applicable)
5. **IFA/route53 / domain-routing** — traffic split last (only after service verified working)

## Review Channels

| Repository | Slack Channel |
|------------|--------------|
| `cps/helm-core` | `#help-core-platform-services` |
| `IFA/route53` | `#help-infra-foundations-aws` |
| `IFA/domain-routing` | `#help-infra-foundations-aws` |
| `IFA/cloudflareplatformproduction` | `#help-infra-foundations-aws` |
| SmartGateway config | `#help-http-integrations` |
| `api_specifications` | `#api-guild-design` |
| Source app repo | Team's own review process |
