# aws (AWS CLI)

## Location
Should be on PATH via standard installation.

## Verification
```powershell
aws --version
aws sts get-caller-identity
```

## SSO Login

The primary SSO profile for cross-account access is `clinton-idm-node`. This uses the JET IDM portal and gives access to select an account/role interactively:

```powershell
aws sso login --profile clinton-idm-node
```

After login, use `--profile clinton-idm-node` for commands, or set specific account profiles:

```powershell
# Interactive account selection (IDM portal)
aws sso login --profile clinton-idm-node

# Use a specific account profile (auto-populated by aws-sso-util)
aws sts get-caller-identity --profile PRODUCTION.admin-view-only
```

## Available Profiles

| Profile | Purpose |
|---------|---------|
| `clinton-idm-node` | Primary SSO login (IDM portal, account selector) |
| `clinton-itservice-node` | IT Services SSO login |
| `clinton-flyt-staging` | Flyt staging |
| `clinton-flyt-prod` | Flyt production |
| `clinton-eks-dev` | EKS dev (eu-central-1) |
| `PRODUCTION.admin-view-only` | JE Production read-only (228773894774) |
| `PRODUCTION.je-read-write` | JE Production read-write (228773894774) |
| `I18N-Production.admin-view-only` | I18N Production read-only (612833568613) |
| `Just-Eat-Networks-Production.admin-view-only` | Networking read-only (277154940863) |

Many more account-specific profiles exist (auto-populated by `aws-sso-util`). Check `~/.aws/config` for the full list.

## Notes
- JET uses AWS SSO via Okta (start URL: `https://d-93676bf05c.awsapps.com/start/#`)
- SSO region: `eu-west-1`
- Default region: `eu-west-1` (except `clinton-eks-dev` which is `eu-central-1`)
- Account-specific profiles use `credential_process = aws-sso-util credential-process` for automatic token refresh
- For CloudTrail queries, ensure you're in the right account profile
