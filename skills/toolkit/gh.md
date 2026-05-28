# gh (GitHub CLI)

## Location
Should be on PATH. Authenticated against `github.je-labs.com`.

## Verification
```powershell
gh auth status --hostname github.je-labs.com
```

## Key Repos

| Repo | Host | Purpose |
|---|---|---|
| `ai-platform/skills` | `github.je-labs.com` | JET skills (canonical source for jet/ category) |
| `ai-platform/team-skills` | `github.je-labs.com` | AI Platform team-specific skills |
| `IFA/docs` | `github.je-labs.com` | IFA TechDocs (runbooks, how-to-guides, guidelines) |
| `anthropics/skills` | `github.com` | Anthropic community skills |
| `clintonherring/skills` | `github.com` | Personal skills repo (custom/, cursor/) |

## PowerShell Escaping Tips

PowerShell handles quotes differently from bash. Common gotchas with `gh api`:

```powershell
# GOOD - single quotes for simple paths
gh api --hostname github.je-labs.com /repos/IFA/docs/contents/docs/runbooks --jq ".[].name"

# GOOD - no query params in the URL
gh api --hostname github.je-labs.com /repos/IFA/docs/git/trees/main --jq ".tree[].path"

# BAD - query params with ? get split into multiple args
gh api --hostname github.je-labs.com "/repos/IFA/docs/git/trees/main?recursive=1"
# PowerShell splits on ? -- use the contents API or recursive tree SHA instead

# GOOD - reading file content from GHE
$content = gh api --hostname github.je-labs.com /repos/IFA/docs/contents/docs/runbooks/network-disruptions.md --jq .content
[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($content))

# GOOD - jq select with escaped quotes
gh api --hostname github.je-labs.com /repos/IFA/docs/git/trees/main --jq '.tree[] | select(.path==\"docs\") | .sha'
```

## Notes
- Always use `--hostname github.je-labs.com` for JET GitHub Enterprise
- Default org for infrastructure repos: `IFA`
- JET skills org: `ai-platform`
- Use `/repos/<org>/<repo>/contents/<path>` API to read files (returns base64)
- Use `/repos/<org>/<repo>/git/trees/<sha>` to list directory contents

## IFA/docs -- Live Documentation Access

`IFA/docs` (`github.je-labs.com`) is the TechDocs repo for IFA (runbooks, how-to-guides, guidelines). Content changes frequently -- always fetch live via `gh api` rather than caching locally.

### Browse the structure
```powershell
# List top-level docs categories
gh api --hostname github.je-labs.com /repos/IFA/docs/contents/docs --jq ".[].name"

# List runbooks
gh api --hostname github.je-labs.com /repos/IFA/docs/contents/docs/runbooks --jq ".[].name"

# List how-to-guides subdirectories
gh api --hostname github.je-labs.com /repos/IFA/docs/contents/docs/how-to-guides --jq ".[].name"

# List a specific subdirectory (e.g. databases)
gh api --hostname github.je-labs.com /repos/IFA/docs/contents/docs/how-to-guides/databases --jq ".[].name"
```

### Read a specific document
```powershell
# Fetch and decode a doc (base64 -> UTF8)
$content = gh api --hostname github.je-labs.com /repos/IFA/docs/contents/docs/runbooks/network-disruptions.md --jq .content
[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($content))
```

### Structure reference (L0)
```
docs/
├── runbooks/                          # Incident response
│   ├── network-disruptions.md
│   ├── database-issues-in-production.md
│   ├── environments-unreachableunavailable.md
│   ├── cloudflare-general.md          # Cloudflare ops, WAF, Workers, Datadog logs
│   ├── cloudflare-expose-endpoint.md
│   ├── internet-outage.md
│   ├── aws-organizations-scp.md
│   ├── backup-jobs-failingfailed.md
│   ├── puppetserver-was-unable-to-retrieve-a-valid-vault-token.md
│   ├── timestamp-issues-on-aws-cron1-6-machines.md
│   └── tms-issues.md
├── how-to-guides/
│   ├── databases/                     # MySQL replication, Galera, InnoDB, connections
│   ├── proxysql/                      # Enable/disable MySQL servers
│   ├── domain-routing/                # Cloudflare WAF, subfolder proxy, microservices
│   ├── network/                       # TGW, DNS zones, Route53, flowlogs, uplinks
│   ├── procedures/                    # CDN, merge requests, server phase-out
│   ├── puppet/                        # Puppet config management
│   ├── teleport/                      # Teleport access
│   ├── okta-privileged-access/        # Okta elevated access
│   ├── maxscale/                      # MaxScale load balancer
│   ├── backups/                       # Backup procedures
│   ├── server/                        # Server management
│   ├── storage/                       # Storage management
│   ├── invoicing/                     # Invoicing
│   ├── ddos-protection.md
│   ├── artifactory.md
│   └── zscaler.md
├── aws/
│   ├── auth/gcp.md                    # GCP cross-auth
│   └── NAT_Gateway/overview_nat_gateway.md
└── guidelines/                        # Monitoring, audit logging, SDLC, patch mgmt
    ├── monitoring-guidelines.md
    ├── database-audit-logging.md
    ├── database-loadbalancers.md
    ├── sdlc-software-development-life-cycle.md
    └── configuration-management-changes-policyworking-agreement.md
```
