# Phase 5: Generate Changes

**Goal**: Generate all code changes using current patterns from authoritative sources.
The helmfile is replaced with a clean goldenpath structure for Sonic Runtime.

**Load**: [03-goldenpath-structure.md](03-goldenpath-structure.md), [08-multi-repo-changes.md](08-multi-repo-changes.md),
[07-traffic-split.md](07-traffic-split.md). Also load `sonic-pipeline` skill if eligible.
Also load [21-smartgateway.md](21-smartgateway.md) if `jet-external.com` endpoints detected.

## Templates

Parameterized templates are in `assets/templates/`. Use `{{PLACEHOLDER}}` syntax for substitution.

| Template | Purpose | When |
|----------|---------|------|
| `helmfile.yaml.gotmpl.tmpl` | Sonic Runtime helmfile (goldenpath) | Always |
| `helmDefaults.yaml.gotmpl.tmpl` | Helm defaults (wait, atomic) | Always |
| `repositories.yaml.gotmpl.tmpl` | Helm chart repository | Always |
| `state-values-defaults.yaml.tmpl` | Shared defaults (port, replicas) | Always |
| `state-values-env.yaml.tmpl` | Per-env config (domains, env_vars) | Always |
| `app-values.yaml.gotmpl.tmpl` | Helm values (deploy, vault, VS) | Always |
| `sonic.yml.tmpl` | Sonic Pipeline config | If Sonic Pipeline eligible |
| `build-deploy-main.yml.tmpl` | GHA CI/CD workflow | If NOT Sonic Pipeline |
| `build-pr.yml.tmpl` | GHA PR workflow | If NOT Sonic Pipeline |
| `route53-weighted-cname.yml.tmpl` | Route53 traffic split records | If R-record / G-record |
| `igw-custom-rules.yaml.tmpl` | Istio gateway customRules | If R-record / G-record / brand domain |
| `smartgateway-config.json.hbs.tmpl` | SmartGateway route | If `jet-external.com` endpoints |
| `cloudflare-dns-record.yaml.tmpl` | Cloudflare DNS for brand domains | If brand domain + external |
| `waf-rules.yaml.tmpl` | WAF rules guidance | If brand domain + Cloudflare |

## 5.0 Fetch Current Patterns

Before generating code:

1. **Read templates** from `assets/templates/` for the parameterized file structures.
2. **Read goldenpath repo** (if not already cloned):
   ```bash
   gh repo clone github.je-labs.com/justeattakeaway-com/goldenpath /tmp/goldenpath -- --depth 1
   ```
3. **Clone basic-application chart**:
   ```bash
   gh repo clone github.je-labs.com/helm-charts/basic-application /tmp/basic-application -- --depth 1
   ```
   - Read `values.yaml` for current config schema
   - Read `CHANGELOG.md` for breaking changes between the service's current chart version and latest
   - Note: The basic-application chart defaults to **Deployment** + **HorizontalPodAutoscaler** (HPA).
     KEDA ScaledObject is available as an opt-in from chart version 1.1.10+ but is NOT the default.
     Generate helm values using `Deployment` + `horizontalPodAutoscaler` unless the user explicitly
     requests KEDA scaling.
4. **If Sonic Pipeline**: Load the **`sonic-pipeline`** skill for sonic.yml schema reference.
   Also load [04-cicd-eligibility.md](04-cicd-eligibility.md) for test detection and mapping.
5. **If GitHub Actions**: Read workflow files from goldenpath repo for current patterns.

## 5.1 Source Repository

1. Create `helmfile.d/` structure following goldenpath layout
2. Populate `state_values/defaults.yaml` from extracted config
3. Create per-env `state_values/{env}.yaml` with correct domains
4. **Create the values file** `values/{APP_NAME}.yaml.gotmpl` using the current
   basic-application chart schema. This replaces the old values template — the helmfile
   is a clean goldenpath structure with only Sonic Runtime environments and a single release.
   The old CloudOps config (environments, values, state_values) is removed from the helmfile.
5. **Vault sidecar annotations** (if `VAULT_STRATEGY != none`):
   - Annotations with KV v2 templates (`.Data.data`), role = `PROJECT_ID`
   - Secret paths: `{PROJECT_ID}/data/{SECRET_NAME}`
   - See [06-vault-secrets-migration.md](06-vault-secrets-migration.md) for annotation templates
   - **Secrets classification**: Plaintext secrets (OKTA tokens, API keys, client IDs) that were
     previously stored as env var values in state_values YAML files should be moved to Vault
     (OneSecrets KV v2). Only non-sensitive configuration (URLs, feature flags, log levels,
     profile names) should remain as env vars. See the "Rule of thumb" in
     [06-vault-secrets-migration.md](06-vault-secrets-migration.md).
6. **cps/projects update** (if `NEEDS_EXTRA_POLICY_RO`):
   Update `projects/pdv/{PROJECT_ID}.yml` with `onesecrets.extra_policy_ro`
7. If Sonic Pipeline: create `.sonic/sonic.yml` using `sonic-pipeline` skill.
   Key fields from our discovery:
   - `metadata.vaultRole` = `PROJECT_ID`
   - `metadata.vaultSecretPath` based on `VAULT_STRATEGY`
   - environments from Phase 4 mapping
   - runtime detected in Phase 3
   Also load [04-cicd-eligibility.md](04-cicd-eligibility.md) for test detection and mapping.
   After generating sonic.yml, **disable event triggers** in existing GHA deploy workflows
   (comment out `push` triggers) but keep the workflow files as an emergency fallback during
   the transition. Retain `workflow_dispatch` so the old pipeline can be triggered manually
   if needed. Remove the old workflow files only after the migration is fully verified and
   traffic has been shifted to Sonic Runtime.
8. If NOT Sonic Pipeline: add goldenpath GHA workflows from `03-goldenpath-structure.md`
9. Replace all `*.eks.tkwy-*.io` domain references with `*.jet-internal.com` equivalents

**Helmfile structure — clean goldenpath replacement**:

CloudOps continues deploying from the current main branch until the Sonic PR merges.
Traffic cutover is managed at the **DNS level** (Route53 weighted routing).

1. **Replace the helmfile with goldenpath structure**: Use `assets/templates/helmfile.yaml.gotmpl.tmpl`
   as the base. Create a single-release helmfile with only Sonic Runtime environments.
   Remove the old CloudOps environments, releases, and state_values from the helmfile.
2. **Remove old CloudOps files**: Delete the old values template, old state_values files,
   and any CloudOps-specific configuration that is no longer needed.
3. **CloudOps keeps running** from the current main branch until the PR merges. This PR
   should only be merged **after** the Sonic deployment has been validated and traffic split
   is ready to begin.

> **Merge timing**: The source repo PR is the last PR to merge. First merge the supporting
> PRs (route53, helm-core, cps/projects) to set up DNS, gateway rules, and namespace access.
> Then deploy to Sonic (QA → staging). Only merge the source repo PR when you are ready
> to cut over CloudOps deploys.

Apply environment mapping from Phase 4 Q2 (confirmed by user, bulkhead-dependent).
**Use the actual values confirmed in Phase 4** — do not hardcode. The mapping was fetched
from Backstage and confirmed by the user during Phase 4 Q2.

**VirtualService domains**:
- Always include **E-record**: `{APP_NAME}.{PROJECT_ID}.pdv-{n}.{region}.{stage}.jet-internal.com`
- Add **NG-record** only if confirmed in Phase 4 Q3b (not needed when R-record is used)
- Add **R-record** only if confirmed in Phase 4 Q3b
- If brand domain detected, also add the brand domain hostname (e.g., `myservice.takeaway.com`)
- Use `APP_NAME` from PlatformMetadata as dns-prefix

## 5.2 Route53 (IFA/route53)

Clone or fork `IFA/route53`. Generate **two categories** of DNS records:

### 5.2a NG-record CNAMEs (Connectivity — Not Traffic Split)

Only generate if `NEEDS_NG_RECORD` was confirmed in Phase 4 Q3b (skip if R-record is used instead).

NG-records are NOT auto-provisioned. They require a Route53 CNAME pointing to the E-record.
Generate one NG-record CNAME per environment confirmed in `DNS_ENVS[]`:

```yaml
# Pattern per environment:
- name: "{APP_NAME}.{PROJECT_ID}.{ENV}.jet-internal.com"
  type: "CNAME"
  records: "{APP_NAME}.{PROJECT_ID}.{ENV_COMPONENT}.{REGION}.{ENV}.jet-internal.com"

# {ENV_COMPONENT} is the bulkhead component name (e.g., pdv-2, pdv-5)
# Look it up from the project's bulkhead definition for each environment.
# Generate one entry per environment (QA, staging, production).
# Follow existing patterns in the route53 repo for TTL and other fields.
```

File locations:
- QA: `non-production/records/qa.jet-internal.com-private.yml`
- Staging: `non-production/records/staging.jet-internal.com-private.yml` (or `eu-west-1.staging.jet-internal.com-private.yml`)
- Production: `production/records/production.jet-internal.com-private.yml` (or `eu-west-1.production.jet-internal.com-private.yml`)

These are **simple CNAMEs** (not weighted). They make the service reachable on Sonic Runtime
via the short, portable NG-record hostname. They are independent of traffic split.

**Per-environment DNS strategy**: The DNS strategy may differ by environment. For example,
a service might use a brand domain in production but only Route53 R-records in staging.
Handle each environment independently based on Phase 4 decisions.

### 5.2b Traffic Split Weighted Records (Gradual Migration)

If the user chose gradual traffic split in Q6, add weighted CNAME records for the
**R-record or G-record** that currently resolves to the CloudOps domain.

**Important**: Generate weighted records only for environments confirmed in Phase 4 Q3b (`DNS_ENVS[]`).
QA and staging may not need traffic split records if those environments don't have consumers
using the R-record/G-record address. Confirm with the user which environments need them.

See `07-traffic-split.md` for file locations, record format, and per-environment guidance.
Follow existing patterns in the `IFA/route53` repo for TTL values and field conventions.

Initial config: weight 0 for Sonic Runtime, weight 100 for CloudOps.
Identifiers: `oneeks-{APP_NAME}` and `cloudops-{APP_NAME}`.

> **Key difference**: NG-record CNAMEs (5.2a) make the service *reachable* on Sonic Runtime.
> Traffic split records (5.2b) gradually *redirect clients* from CloudOps to Sonic Runtime.
> Both are needed, but they serve different purposes and go in different Route53 zone files.

Tag `@support-ifa` in PR description.

## 5.3 Helm-Core ([cps/helm-core](https://github.je-labs.com/cps/helm-core))

Clone or fork `cps/helm-core`. Add `customRules` to
`clusters/{cluster}/releases/istio-gateways.yaml.gotmpl` for the service domain
on the project's ingress gateway (`igw-{PROJECT_ID}`).

**CRITICAL**: customRules MUST be on the **same IGW** (`igw-{PROJECT_ID}`) that serves the
wildcard E-records. This is what allows CNAME chains (NG-record → E-record, R-record → E-record)
to work — all hostnames resolve through the same gateway.

Hosts must match Route53 entries. Tag `@help-core-platform-services` in PR description.

**Not needed for**: E-records, NG-records (handled by IGW wildcard).
**Needed for**: R-records, G-records, brand domains.

## 5.4 Domain-Routing (if brand domain)

Only if the service uses a brand domain (e.g., `takeaway.com`, `lieferando.de`, `scoober.com`, etc.).
Brand domain traffic split is managed in `IFA/domain-routing` — NOT in Route53.
Both are DNS-level weighted routing, just different DNS providers (Cloudflare vs Route53).

Clone `IFA/domain-routing` and **read the existing config file** for the brand domain to
understand its current structure before making changes. Different brand domains use different
formats — some use weighted `microservices:` endpoints, others use simple CNAME records.

```bash
gh repo clone github.je-labs.com/IFA/domain-routing /tmp/domain-routing -- --depth 1
# Find the config for the brand domain
find /tmp/domain-routing/vars/records/ -name "*.yaml" -o -name "*.yml" \
  | xargs grep -l "{APP_NAME}\|{BRAND_DOMAIN}" 2>/dev/null
```

Based on what you find, generate the appropriate changes:

1. **Update the origin/endpoint** to include the Sonic Runtime target alongside the existing
   CloudOps target. Follow the existing structure in the file — do not invent a new format.
   Initial weight: 0 for Sonic Runtime, 100 for CloudOps (if the format supports weights).
   If the format is a simple CNAME (no weights), the cutover will be a single record swap
   rather than gradual — note this in the PR description.
2. **Cloudflare DNS** (if Cloudflare-fronted): The origin endpoint update in step 1 handles
   this — Cloudflare proxies to whatever the domain-routing config specifies.
3. **WAF rules** (if applicable): Check `vars/domains/waf.yml` for existing rules referencing
   the service. Update or add allow rules as needed.

## 5.5 cps/projects (if AWS access or Vault needed)

If `NEEDS_WORKLOAD_ROLE` was set in Phase 4, generate the Workload Role definition.

**This PR is always needed when the service accesses AWS resources**, even for EU1-only
deployments (EU1 shares the same account but still requires a Workload Role instead of IRSA).

**Exclude SecretsManager**: Do NOT include `secretsmanager:GetSecretValue` permissions in
the Workload Role. Secrets are being migrated to OneSecrets (Vault KV v2) — the app will
read them from the Vault sidecar, not from AWS SM. Only include permissions for AWS resources
the app continues accessing directly on Sonic (DynamoDB, S3, SQS, SNS, RDS, Kinesis, etc.).
If SecretsManager was the **only** AWS access, do not generate a Workload Role at all.

### 5.5a Workload Role Definition

1. Clone `cps/projects` if not already cloned (should be at `/tmp/cps-projects` from Phase 1).

2. Explore existing workload definitions to follow conventions:
   ```bash
   ls /tmp/cps-projects/workloads/pdv/ | head -20
   cat /tmp/cps-projects/workloads/pdv/{similar-project}.yaml  # pick one for reference
   ```

3. Create or update `workloads/pdv/{PROJECT_ID}.yaml` with the detected AWS permissions:
   - Apply **least-privilege**: use specific resource ARNs, not wildcards
   - Extract IAM actions from the service's existing IRSA role/policy (check CloudOps
     Terraform, IAM policy documents, or `aws iam get-role-policy` output)
   - Extract resource ARNs (DynamoDB tables, S3 buckets, SQS queues, RDS) from application
     config, environment variables, and helmfile state values
   - For each target environment, populate `accounts.{env}` with the correct `variables`
     (table names, account IDs, regions)
   - Use the template pattern from `sonic-migration-analyzer/references/05-aws-access.md`
     (contains the full Workload Role specification, YAML structure, cross-account setup
     patterns, ARN formats, and SDK compatibility requirements)

### 5.5b Helmfile Integration

4. Add `serviceAccount` annotations to the helmfile values (if not already present from 5.1):
   ```yaml
   serviceAccount:
     create: true
     {{- if .StateValues.workloadRoleARN }}
     annotations:
       eks.amazonaws.com/role-arn: {{ .StateValues.workloadRoleARN | quote }}
     {{- end }}
   ```

5. Add `workloadRoleARN` to each environment's `state_values/{env}.yaml`:
   ```yaml
   workloadRoleARN: "arn:aws:iam::{AWS_ACCOUNT_ID}:role/jas/wl/terraform_managed/jas-wl-role-{PROJECT_ID}-{APP_NAME}"
   ```
   For environments where the Workload Role doesn't exist yet (e.g., non-EU1 bulkheads
   pending cross-account setup), use a commented-out placeholder:
   ```yaml
   # workloadRoleARN: "" # TODO: Create Workload Role for this environment
   ```

### 5.5c Cross-Account (if NEEDS_CROSS_ACCOUNT)

6. If `NEEDS_CROSS_ACCOUNT` was set (non-EU1 bulkheads with AWS resources), generate a summary
   of **Side 2 (legacy account) changes** the user needs to apply manually:
   > "You'll also need to update resource-based policies in your legacy AWS account to trust
   > the new Sonic Runtime workload role. Here are the policy statements needed:"
   >
   > (Generate specific policy JSON for each detected resource — RDS security group,
   > DynamoDB table policy, S3 bucket policy, etc.)
   >
   > "Apply these through your existing infrastructure-as-code. The IFA team
   > (`@support-ifa` in `#help-infra-foundations-aws`) can help if needed."

   > **Note**: EU1 shares the same AWS account as CloudOps — no cross-account trust needed
   > for EU1 resources. Cross-account is only needed for non-EU1 bulkheads.

### 5.5d Vault extra_policy_ro (if needed)

7. If Vault secret access requires cross-project read policies, update
   `projects/pdv/{PROJECT_ID}.yml` with `extra_policy_ro`. See
   [06-vault-secrets-migration.md](06-vault-secrets-migration.md) → "extra_policy_ro Configuration"
   for the exact format.

Tag `@support-ifa` in the PR description for review.

## 5.6 SmartGateway (if `jet-external.com` endpoints detected)

**Load**: [21-smartgateway.md](21-smartgateway.md) — contains full config procedure, JSON
schema, environment mapping, plugin requirements.

Follow the procedure in `21-smartgateway.md` to:
1. Clone `external-api-services/smartgatewayconfiguration`
2. Explore existing configs for current conventions
3. Generate config JSON using `assets/templates/smartgateway-config.json.hbs.tmpl`
4. Place under `Data/Global/{service-name}.json.hbs`

Key requirements: host = NG-record, port = 443, protocol = https, include `rate-limiting`
plugin at minimum.

> Inform user: "After SmartGateway PR is merged, test via SmartGateway regional endpoints
> before going fully live. Request review in `#help-http-integrations`."

## 5.7 API Specifications (if `jet-external.com` endpoints detected AND no existing BOATS spec)

If the user indicated in Phase 4 Q4 that they don't have a BOATS spec:

1. Clone `api_specifications` repo. Explore `src/paths/` for existing examples.
2. Generate a **placeholder OpenAPI v3 spec** based on detected routes and endpoints.
3. Inform the user they must refine it and get approval from `#api-guild-design` before
   going live externally.

If already has a BOATS spec: skip, but note spec may need updating if URLs/paths change.

## 5.8 Vault Configuration Validation

If `VAULT_STRATEGY != none`, validate consistency:

1. `vaultRole` in sonic.yml = `PROJECT_ID` = Kubernetes auth role in `cps/projects`
2. Secret paths in helm annotations match actual paths in OneSecrets (`{PROJECT_ID}/data/...`)
3. All secrets use KV v2 format (`.Data.data`)
4. If `extra_policy_ro` used: every cross-project path has a corresponding policy entry
5. No references to AWS Secrets Manager remain in code/config
6. For multi-bulkhead: confirm secrets exist in each bulkhead's Vault independently

See [06-vault-secrets-migration.md](06-vault-secrets-migration.md) for annotation templates
and policy format.

## 5.9 Consistency Validation

Before creating PRs, load [09-consistency-validation.md](09-consistency-validation.md) and
validate the three routing layers:

| Layer | What to check |
|-------|---------------|
| DNS (Route53/domain-routing) | Record exists and resolves |
| helm-core customRules | Host listed on `igw-{PROJECT_ID}` |
| VirtualService domains | Host in state_values domains list |

Build a per-environment validation table. Fix any mismatches before proceeding.
