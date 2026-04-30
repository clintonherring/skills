# JET AWS Account Architecture

## SSO Portals

| Portal | Start URL | Okta App | Accounts |
|--------|----------|----------|----------|
| **orga** | `https://orga.awsapps.com/start` | AWS (Legacy Takeaway) | ~135 accounts: SRE, CloudOps, OneEKS, DR, infra |
| **acas** | `https://acas.awsapps.com/start` | AWS (Legacy Just Eat) | JetConnect, Flyt, Gen4, global-dns |

GBPI team (`#help-gbpi`) manages AWS SSO. SSO config repos: `git.takeaway.com/infrastructure-ops/terraform/aws-je-sso`.

## Account Naming Conventions

### Sonic Runtime / OneEKS (new standard)

Format: `<region>-<function>-<env>-<number>`

```
euw1-pdv-prd-5
│    │   │   └─ Partition number
│    │   └───── Environment: sbx, qa, stg, prd
│    └───────── Function: pdv (platform delivery), plt (platform), pmt (platform management)
└────────────── Region code
```

### Legacy Format

Format: `<descriptive-name>-<env>` or `<org>-<function>-<env>-<number>`

Examples: `sre-eks-production-1`, `takeaway-staging`, `cloudops-dev`

### Region Codes

| Code | AWS Region | Location |
|------|-----------|----------|
| `euw1` | eu-west-1 | Ireland (primary) |
| `ec1` | eu-central-1 | Frankfurt |
| `apse2` | ap-southeast-2 | Sydney |
| `usw2` | us-west-2 | Oregon |

### Environment Types

| Code | Full Name | Purpose |
|------|-----------|---------|
| `sbx` | Sandbox | Experimentation |
| `qa` | QA | Testing |
| `stg` | Staging | Pre-production |
| `prd` | Production | Live traffic |
| `dr` | Disaster Recovery | Failover |

### Bulkheads

Sonic Runtime uses bulkheads for blast radius isolation:

| Bulkhead | Region | QA | Staging | Production |
|----------|--------|----|---------|------------|
| **EU1** | eu-west-1 | euw1-pdv-qa-2 | euw1-pdv-stg-5 | euw1-pdv-prd-5 |
| **EU2** | eu-west-1 | euw1-pdv-qa-3 | euw1-pdv-stg-6 | euw1-pdv-prd-6 |
| **OC1** | ap-southeast-2 | apse2-pdv-qa-2 | apse2-pdv-stg-2 | apse2-pdv-prd-3 |
| **NA1** | us-west-2 | usw2-pdv-qa-1 | usw2-pdv-stg-1 | usw2-pdv-prd-2 |

EU1 is the primary bulkhead — start migrations here. EU1 has access to legacy Takeaway Vault secrets.

## Organisation Hierarchy

- **Master/root account**: `228773894774`
- **Organisation account (orga)**: `778305418618`
- **DNS hosted zones**: `<region>.<env_type>.jet-internal.com`
- **Account email format**: `team-pcit-aws-<account-id>@takeaway.com` or `aws+<account-name>@just-eat.com`

## IAM Role Patterns

### SSO Reserved Roles

Pattern: `arn:aws:iam::<account>:role/aws-reserved/sso.amazonaws.com/eu-west-1/AWSReservedSSO_<role-name>_<hash>`

When applications need to trust SSO-assumed roles, use wildcard matching on the hash portion.

### IRSA / Workload Roles (Sonic Runtime)

Pattern: `arn:aws:iam::<account>:role/jas/wl/terraform_managed/jas-wl-role-<project>-<app>`

Self-service via Terraform. Annotate the service account:
```yaml
eks.amazonaws.com/role-arn: "arn:aws:iam::<account>:role/jas/wl/terraform_managed/jas-wl-role-<project>-<app>"
```

### Cross-Account (Atlantis/Terraform)

Trust policy pattern: `arn:aws:iam::778305418618:role/sre/terraform_managed/atlantisOrgaAccess`

### Team Roles (OneEKS)

Pattern: `jas-[q|s|p]-<team-name>`
- `q` = QA
- `s` = Staging
- `p` = Production

Tag-based access control (ABAC) using `jet_acl` tags on resources.

## Terraform / IaC Conventions

- **Tool**: Terraform + Terragrunt
- **State**: S3 backend with DynamoDB locking
- **Modules**: Stored in GitHub Enterprise repositories
- **Account creation**: JET 2.0 Terraform modules (see `infrastructure-foundations-aws` group in Backstage)
- **EKS provisioning**: `cps/aws-core` repository
- **Namespace quotas**: `cps/projects` repository
