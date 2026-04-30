# Bulkheads & Environment Mapping

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

2. **Detect source SRE-EKS environments** from the source repo's deployment config (kubeContext names, helmfile environments, CI/CD deploy targets)

3. **Map by env-type**: Match QA→QA, Staging→Staging, Production→Production

4. **Present to user for confirmation** — show the proposed mapping and allow adjustments if needed (e.g., if QA environment is missing in SRE-EKS, inform the user that it will be created in Sonic Runtime).

## Why Start with EU1?

1. **Functional equivalent**: EU1 is the closest to the SRE-EKS single-bulkhead architecture
2. **Legacy Vault access**: EU1 is the **only** bulkhead with mirrored access to legacy Takeaway Vault secrets. Other bulkheads require full OneSecrets migration.
3. **Familiarity**: Same AWS region (eu-west-1) as SRE-EKS
4. **Incremental**: Validate on EU1 first, then expand to other bulkheads

Important to note here that certain datastores like thuis/generaldb/etc do not have qa equivalents. Be sure to inform the user about this.

## Bulkhead Clarification

> **Warning**: Non-EU1 bulkheads (EU2, NA1, OC1) do **not** have access to legacy resources that are only available in the SRE-EKS / legacy Takeaway environment. This includes legacy Vault secrets, legacy database connections (e.g., thuis, ProxySQL-backed backends), legacy RabbitMQ servers, and other infrastructure that only exists in the EU1 / SRE-EKS ecosystem.

If your service depends on **any legacy resource** whose secrets or connectivity is only available through the EU1 Vault instance, deploying to a non-EU1 bulkhead will fail at runtime — the workload will not be able to access the required resources.

**Before selecting a non-EU1 bulkhead**, verify:

1. **Secrets**: All secrets the service needs are available in OneSecrets (KV v2) or can be recreated there — legacy Vault paths (`secret/`, `database/creds/`, `rabbitmq/creds/`) are not accessible on non-EU1 Vault instances for most backends
2. **Database connections**: Dynamic database backends are limited on non-EU1 instances (see [14-vault-secrets-migration.md](14-vault-secrets-migration.md) for the instance capability matrix)
3. **Network reachability**: Legacy resources (databases, message brokers) in the SRE-EKS VPC may not be network-reachable from non-EU1 clusters

If you need to deploy to a non-EU1 bulkhead but depend on legacy resources, reach out to **`#help-core-platform-services`** or **`#help-sonic`** on Slack for guidance on how to make those resources available in your target bulkhead.

## Project & Namespace Rules

- **One project** for ALL environments (QA, Staging, Production across all bulkheads)
- Project ID format: `{process-group-prefix}-{suffix}` (e.g., `cu-order-reviews`)
- Namespace = Project ID (e.g., project `cu-order-reviews` → namespace `cu-order-reviews`). There is no prefix — the project ID is used directly as the Kubernetes namespace name.
- The project and namespace are created during Sonic Runtime onboarding — verify with the user that onboarding is complete
