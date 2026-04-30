# Environment Mapping: CloudOps-EKS → Sonic Runtime

## Sonic Runtime Bulkheads (Conceptual)

Sonic Runtime uses isolated deployment pools called **bulkheads** for fault tolerance and regional proximity. There are currently 4 bulkheads across different AWS regions.

For current bulkhead details and environment names, fetch from:

- **Goldenpath repo**: Clone `justeattakeaway-com/goldenpath` and read `helmfile.d/helmfile.yaml.gotmpl` for current environment names
- **Backstage**: Search `sre-eks sonic runtime migration` for the latest environment mapping

## Environment Naming Convention

Format: `{region}-{env-function}-{env-type}-{partition}`

| Component            | Example Values                  |
| -------------------- | ------------------------------- |
| Region               | `euw1`, `euw2`, `apse2`, `usw2` |
| Environment Function | `pdv` (product development)     |
| Environment Type     | `qa`, `stg`, `prd`              |
| Partition            | environment partition           |

## How to Build the Environment Mapping

1. **Fetch current target environments** from the cloned goldenpath repo:
   - Read `helmfile.d/helmfile.yaml.gotmpl` — the `environments:` block lists the current Sonic Runtime environment names
   - Read `helmfile.d/state_values/` directory — each file corresponds to one environment

2. **Detect source CloudOps environments** from the source repo's deployment config (kubeContext names, helmfile environments, CI/CD deploy targets)

3. **Map by env-type**: Match Dev→QA, Staging→Staging, Production→Production

4. **Present to user for confirmation** — show the proposed mapping and allow adjustments if needed (e.g., if QA environment is missing in CloudOps, inform the user that it will be created in Sonic Runtime).

## Why Start with EU1?

1. **Same AWS account**: CloudOps EU clusters and Sonic Runtime EU1 share the same AWS account (`takeaway-production` / `takeaway-staging`) — no cross-account IAM trust needed
2. **Functional equivalent**: EU1 is the closest to the CloudOps single-cluster architecture
3. **Incremental**: Validate on EU1 first, then expand to other bulkheads

Important: Certain datastores like thuis/generaldb/etc do not have QA equivalents. Inform the user about this when mapping QA environments.

## Bulkhead Clarification

> **Warning**: Non-EU1 bulkheads (EU2, NA1, OC1) are in **different AWS accounts** than CloudOps. Resources in the CloudOps account (`takeaway-production`, `takeaway-staging`, `cloudops-dev`) are not directly accessible from non-EU1 clusters.

**Before selecting a non-EU1 bulkhead**, verify:

1. **Secrets**: AWS Secrets Manager secrets from CloudOps must be recreated in OneSecrets (Vault KV v2) for **each** target bulkhead independently — OneSecrets does not sync across bulkheads
2. **AWS resources**: DynamoDB, S3, SQS, RDS, etc. in the CloudOps account need **cross-account IAM policies** for non-EU1 access (EU1 shares the same account, so no issue)
3. **Network reachability**: Databases and other resources in the CloudOps VPC may not be reachable from non-EU1 clusters without VPC peering or Transit Gateway

If you need to deploy to a non-EU1 bulkhead but depend on CloudOps-account resources, reach out to **`#help-core-platform-services`** or **`#help-sonic`** on Slack for guidance.

## CloudOps-Specific Facts

- CloudOps uses **IRSA** for AWS access: role pattern `irsa_{namespace}_{sa}` where `{sa}` is the Kubernetes ServiceAccount name (namespace + SA name ≤ 58 chars)
- Sonic Runtime uses **Workload Roles** for AWS access (self-service Terraform in `cps/projects`)
- Non-EU1 bulkheads are in different AWS accounts — cross-account access may be needed

## Project & Namespace Rules

- **One project** for ALL environments (QA, Staging, Production across all bulkheads)
- Project ID format: `{process-group-prefix}-{suffix}` (e.g., `cu-service-jetms`)
- Namespace = Project ID (e.g., project `cu-service-jetms` → namespace `cu-service-jetms`). There is no prefix — the project ID is used directly as the Kubernetes namespace name.
- The project and namespace are created during Sonic Runtime onboarding — verify with the user that onboarding is complete

## QA Environment

QA environment is **mandatory** in Sonic Runtime even if the CloudOps service doesn't have a
dev/QA deployment. Always include it in the environment mapping — show "(none — new)" in the
Current column if no CloudOps QA equivalent exists. Do NOT ask the user whether to skip QA.
Use the EU1 QA environment (fetched from goldenpath) as the target.

Use environment names fetched from the **goldenpath** repo as the target.
Present the mapping populated with detected Sonic Runtime environment names.

## All Sonic Runtime Environments (from Backstage)

Reference table — always verify at runtime by querying Backstage (`kind=environment,metadata.tags=oneeks`):

| Bulkhead | QA | Staging | Production |
| -------- | -- | ------- | ---------- |
| EU1 | `euw1-pdv-qa-2` | `euw1-pdv-stg-5` | `euw1-pdv-prd-5` |
| EU2 | `euw1-pdv-qa-3` | `euw1-pdv-stg-6` | `euw1-pdv-prd-6` |
| OC1 | `apse2-pdv-qa-2` | `apse2-pdv-stg-2` | `apse2-pdv-prd-3` |
| NA1 | `usw2-pdv-qa-1` | `usw2-pdv-stg-1` | `usw2-pdv-prd-2` |

> **Note**: EU1 and EU2 are **both** in `euw1` (eu-west-1, Ireland). They are different isolation partitions within the same AWS region, not different regions. There are no `euw2-pdv-*` environments.