---
name: jet-aws
description: JET (Just Eat Takeaway) AWS operational tasks including SSO authentication (orga and acas portals), profile selection, EKS/Kubernetes cluster access (legacy and Sonic Runtime/OneEKS), kubectl/kubeconfig setup, Helm/Helmfile deployments, AWS resource management (S3, RDS, ECR, Secrets Manager), IAM role assumption (SSO, IRSA, cross-account), Terraform/Terragrunt operations, and JET AWS account ID or naming convention lookups. This skill performs actual AWS CLI operations and troubleshooting — for Athena SQL queries use jet-aws-athena or jet-odl-athena, for migration readiness assessment use sonic-migration-analyzer, and for documentation lookup about AWS/EKS topics use jet-company-standards.
metadata:
  owner: ai-platform
---

# JET AWS

Operate within JET's AWS organisation: authenticate via SSO, select profiles, access EKS clusters, assume roles, and manage AWS resources.

## SSO Authentication

JET uses two AWS SSO portals. One login per portal covers all profiles on that portal.

| Portal | SSO Start URL | Used For |
|--------|--------------|----------|
| **Takeaway (orga)** | `https://orga.awsapps.com/start` | SRE, CloudOps, OneEKS/Sonic Runtime, DR, most accounts |
| **JetConnect (acas)** | `https://acas.awsapps.com/start` | Flyt, Gen4, Legacy JE, global-dns |

```bash
# Login (opens browser, authenticates via Okta)
aws sso login --profile <any-profile-on-that-portal>

# Verify credentials
aws sts get-caller-identity --profile <profile>
```

One login session is shared across all profiles on the same SSO portal. To access both portals, run `aws sso login` twice with a profile from each.

## Profile Selection

Profiles are configured in `~/.aws/config`. Select based on what you need to access.

**Decision tree:**

1. **What platform?**
   - Sonic Runtime / OneEKS clusters → use `euw1-pdv-*`, `apse2-pdv-*`, `usw2-pdv-*`, `euw1-plt-*`, `euw1-pmt-*` profiles
   - Legacy SRE EKS → use `sre-eks-*` profiles
   - Legacy CloudOps EKS → use `eks-cluster-*` or `takeaway-*` profiles
   - Flyt/JetConnect → use `flyt-*` or `gen4-*` profiles (acas portal)
   - DR → use `p-ew1-dr*` or `d-ew1-test-dr-*` profiles

2. **What environment?**
   - QA → profiles with `qa` or `dev`
   - Staging → profiles with `stg` or `staging`
   - Production → profiles with `prd` or `production`

3. **What region?**
   - `eu-west-1` → `euw1-*` (default for most)
   - `eu-central-1` → `p-ec1-*`
   - `ap-southeast-2` → `apse2-*`
   - `us-west-2` → `usw2-*`

For the full profile registry with account IDs, roles, and SSO portals, see [references/profiles.md](references/profiles.md).

For account naming conventions and architecture, see [references/architecture.md](references/architecture.md).

## EKS / Kubernetes Access

JET has two generations of EKS clusters. For cluster topology, bulkhead mapping, and Helm patterns, see [references/eks-clusters.md](references/eks-clusters.md).

### Kubeconfig Setup

```bash
# 1. Login to SSO
aws sso login --profile <profile>

# 2. Update kubeconfig (use --alias to keep context names clean)
aws eks update-kubeconfig --profile <profile> --name <cluster-name> --alias <cluster-name>

# 3. Verify
kubectl get nodes
```

### Legacy EKS Clusters

Use `cloudops-platform-user` role for kubectl access, `admin` for AWS console.

```bash
# Dev
aws eks update-kubeconfig --profile eks-cluster-dev-eks --name eks-cluster-dev --alias eks-cluster-dev

# Staging
aws eks update-kubeconfig --profile takeaway-staging-eks --name eks-cluster-staging-2 --alias eks-cluster-staging-2

# Production
aws eks update-kubeconfig --profile takeaway-production-eks --name eks-cluster-prod --alias eks-cluster-prod
```

### Sonic Runtime (OneEKS) Clusters

Cluster names match the profile names. Use the matching AWS profile directly.

```bash
# EU1 Production
aws eks update-kubeconfig --profile euw1-pdv-prd-5 --name euw1-pdv-prd-5 --alias euw1-pdv-prd-5

# EU2 Staging
aws eks update-kubeconfig --profile euw1-pdv-stg-6 --name euw1-pdv-stg-6 --alias euw1-pdv-stg-6
```

### Recommended Tools

| Tool | Version | Purpose |
|------|---------|---------|
| kubectl | 1.30 (legacy), 1.32 (OneEKS) | Cluster operations |
| k9s | latest | Terminal UI for clusters |
| kubectx/kubens | latest | Fast context/namespace switching |
| helm | 3.x | Chart management |
| helmfile | latest | Multi-environment Helm releases |

### Helm Deployment (Golden Path)

Standard chart: `sre/basic-application` from `https://artifactory.takeaway.com/sre-helm-prod-virtual`

Helmfile directory structure:
```
helmfile.d/
├── bases/
│   ├── helmDefaults.yaml.gotmpl
│   └── repositories.yaml.gotmpl
├── helmfile.yaml.gotmpl          # Environment definitions + releases
├── state_values/
│   ├── defaults.yaml             # Shared defaults
│   ├── euw1-pdv-stg-5.yaml      # Per-environment overrides
│   └── euw1-pdv-prd-5.yaml
└── values/
    └── <RELEASE_NAME>.yaml.gotmpl
```

```bash
# Deploy to a specific environment
helmfile -e euw1-pdv-stg-5 apply

# Diff before applying
helmfile -e euw1-pdv-stg-5 diff
```

### DNS Patterns

```
# Namespaced global (preferred)
<app>.<namespace>.<env_type>.jet-internal.com

# Environment-scoped
<app>.<namespace>.<env_function>-<env_partition>.<region>.<env_type>.jet-internal.com
```

## Role Assumption Patterns

### SSO Roles (via `~/.aws/config`)

| Role | Access Level | Used By |
|------|-------------|---------|
| `admin` | Full account admin | SRE, CloudOps engineers |
| `cloudops-platform-user` | kubectl access to legacy EKS | EKS users |
| `je-read-write` | Read/write AWS resources | JetConnect teams |
| `core-platform-services` | CPS-level access | CPS teams |
| `je-eksclusteradmin` | EKS cluster admin (JetConnect) | Cluster admins |
| `jas-q-<team>` | QA namespace access (OneEKS) | Application teams |
| `jas-s-<team>` | Staging namespace access (OneEKS) | Application teams |
| `jas-p-<team>` | Production namespace access (OneEKS) | Application teams |
| `dips-admin` | DIPS team admin | DIPS engineers |
| `vault-sops` | SOPS encryption/decryption | Secret management |

### IRSA (IAM Roles for Service Accounts)

Workloads running in EKS assume IAM roles via service account annotations:

```yaml
# In Helm values or basic-application config
serviceAccount:
  annotations:
    eks.amazonaws.com/role-arn: "arn:aws:iam::<account-id>:role/jas/wl/terraform_managed/jas-wl-role-<project>-<app>"
```

Sonic Runtime workload roles are self-service via Terraform. Legacy EKS IRSA requires a ticket.

### Cross-Account Assumption

```bash
# Assume role in another account (e.g., Atlantis pattern)
aws sts assume-role \
  --role-arn "arn:aws:iam::<target-account>:role/<role-name>" \
  --role-session-name "my-session" \
  --profile <source-profile>
```

SSO-assumed roles follow pattern: `arn:aws:iam::<account>:role/aws-reserved/sso.amazonaws.com/eu-west-1/AWSReservedSSO_<role-name>_<hash>`

## Common AWS Operations

```bash
# ECR login (eu-west-1)
aws ecr get-login-password --profile <profile> | docker login --username AWS --password-stdin <account-id>.dkr.ecr.eu-west-1.amazonaws.com

# RDS auth token (expires in 15 min)
aws rds generate-db-auth-token --profile <profile> \
  --hostname <rds-endpoint> --port 3306 --username <db-user>

# S3 operations
aws s3 ls s3://<bucket> --profile <profile>
aws s3 cp <local-file> s3://<bucket>/<key> --profile <profile>

# Secrets Manager
aws secretsmanager get-secret-value --profile <profile> --secret-id <secret-name>

# Describe EKS clusters in an account
aws eks list-clusters --profile <profile>
```

## Terraform / IaC

JET uses Terraform with Terragrunt for AWS infrastructure.

- State backends are in S3 with DynamoDB locking
- Modules are in GitHub Enterprise repositories
- EKS cluster provisioning: `cps/aws-core` repository
- Namespace quotas: `cps/projects` repository

```bash
# Typical Terragrunt workflow
terragrunt plan --terragrunt-working-dir <path>
terragrunt apply --terragrunt-working-dir <path>

# With specific AWS profile
AWS_PROFILE=<profile> terragrunt plan
```

## Reference Files

- **[references/profiles.md](references/profiles.md)** — Full registry of all AWS profiles with account IDs, roles, regions, and SSO portals. Read when looking up a specific profile or account ID.
- **[references/architecture.md](references/architecture.md)** — Account naming conventions, region codes, environment types, bulkhead topology, IAM role patterns. Read when working with account structure.
- **[references/eks-clusters.md](references/eks-clusters.md)** — Complete EKS cluster topology, legacy vs Sonic Runtime mapping, profile-to-cluster mapping, Helmfile golden path, DNS patterns, secrets management, deployment methods. Read when working with EKS/Kubernetes.
