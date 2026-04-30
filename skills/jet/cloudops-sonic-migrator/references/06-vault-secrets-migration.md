# Vault & Secrets Migration

## Architecture: OneSecrets (Vault KV v2)

Sonic Runtime uses **OneSecrets** (HashiCorp Vault KV v2) for all secret management.
Each project gets its own KV v2 mount on the cluster's Vault instance.

**Key implications**:
- The Vault agent sidecar always connects to the **local cluster Vault** — no remote URLs needed
- Secret paths follow the pattern `{project}/data/{secret-name}` (KV v2)
- Cross-project access is granted via `extra_policy_ro` in `cps/projects`
- The `vault.hashicorp.com/service` annotation is NOT needed — the sidecar's default Vault address is correct

### How Vault Works on Sonic Runtime

Each OneEKS cluster has its own Vault instance. Every pod that needs secrets gets a **Vault Agent sidecar** injected automatically based on pod annotations. The sidecar uses the pod's **Kubernetes ServiceAccount** (the workload identity) to authenticate to the local Vault, receives a token scoped to the project's read policy, reads the requested secrets, and injects them as **files** (at `/vault/secrets/`) or as **environment variables** (via `environmentSecrets` chart feature or init container sourcing).

```
OneEKS Cluster (e.g., euw1-pdv-prd-5)
  |
  +-- Pod (your application)
  |     |
  |     +-- Vault Agent Sidecar (auto-injected via annotations)
  |     |     |
  |     |     +-- Authenticates to LOCAL cluster Vault using:
  |     |     |     - Kubernetes auth backend (path "kubernetes")
  |     |     |     - ServiceAccount JWT token (workload identity)
  |     |     |     - Role = PROJECT_ID (e.g., "cu-service-jetms")
  |     |     |
  |     |     +-- Receives Vault token with policies:
  |     |     |     - default-onesecrets (basic token management)
  |     |     |     - <project-name>-ro  (read <project-name>/* KV v2)
  |     |     |     - plus extra_policy_ro paths (if configured)
  |     |     |
  |     |     +-- Reads secrets and injects them as:
  |     |           - Files at /vault/secrets/{template-name}
  |     |           - Environment variables (via environmentSecrets)
  |     |
  |     +-- App Container (starts after secrets are available)
  |
  +-- LOCAL Vault Instance
        |
        +-- KV v2 mounts: <project-name>/  (one per project — "OneSecrets")
        +-- KV v1 mount:  secret/          (synced copy of legacy secrets)
        +-- Auth backends: kubernetes, oidc, github-jwt
```

**Key points**:
- No remote Vault URLs needed — sidecar auto-discovers the local Vault
- No `auth-path` annotation needed — Sonic Runtime uses the standard `kubernetes` auth path
- The Vault role = project ID (not the old `{project}_{cluster}_{namespace}_star` format)
- Secrets are available before the app container starts (init container pattern)
- **Mounting as files is the recommended approach** — env var injection is supported but discouraged by the platform (secrets exposed via `kubectl describe pod`)
- **Environment isolation**: Each environment (qa, staging, production) has its own Vault instance — secrets don't leak across environments
- **Secret rotation**: Plan for rotation during migration to avoid service disruption

## Learning Resources

- **Video**: [JETflix 2025.06: Becoming a OneSecrets Expert](https://jetflix.jet-internal.com) — comprehensive walkthrough of OneSecrets setup, secret management, and migration patterns.
- **OneConfig**: Non-sensitive configuration (feature flags, URLs, timeouts) should use **OneConfig** (ConfigMaps + Helmfile templating), NOT OneSecrets. See [OneConfig Tutorial](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/oneeks/tutorials/manage-config-with-helmfile/) for patterns.

> **Rule of thumb**: Passwords, API keys, tokens, certificates → **OneSecrets**. Everything else → **OneConfig** (ConfigMaps via `state_values/*.yaml` and `envFromConfigMap`).

## Migration Ordering: Secrets as a Separate Workstream

Secrets migration is a **separate workstream** from the runtime migration, not a prerequisite
that blocks it. This aligns with the official Backstage guide
([Migrating Secrets](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/oneeks/tasks/manage-secrets/migrating-secrets/))
which presents secrets migration as one of several parallel steps in the overall platform
transition.

The agent should:

1. **Generate all Vault configuration** in the migration PRs: annotations in the Sonic values
   file, `onesecrets` policies in `cps/projects`, `extra_policy_ro` entries. This is code that
   can be reviewed and merged independently.
2. **Generate a secrets migration checklist** in the Phase 7 summary — listing every secret
   that must be created in Vault UI, the exact KV v2 path, which Vault instances (per bulkhead
   and environment), and the source of the current values.
3. **Do NOT block PR creation** on secrets being created. The PRs contain configuration that
   references secret paths — the actual secret values are created separately.
4. **Inform the user** that secrets migration is a separate activity, referencing the Backstage
   guide. The team handles it as part of their migration workstream.

### Why This Is Safe

- **CloudOps keeps running** on its existing secrets (AWS SM, K8s Secrets, cross-cluster Vault)
  throughout the migration. Nothing changes for the running service.
- **Sonic deployment is manually triggered** — either via `workflow_dispatch` in GHA or by the
  team's first Sonic Pipeline run. Pods will not start on Sonic until the team explicitly
  triggers deployment.
- **If secrets are missing** when the Sonic deployment runs, pods will fail with
  `Init:CrashLoopBackOff` (Vault sidecar can't read secrets). This is recoverable — create
  the secrets and the pods will start on the next restart.
- **No data loss risk** — secrets are read-only from the app's perspective.

### Day-1 Secret Continuity by Source Type

Not all secrets require migration before the first Sonic deployment. The agent classifies
each secret from `SECRETS_INVENTORY` by its `day1_status` to determine what to generate,
what to warn about, and what the user must handle.

| Source | Day-1 on Sonic | Agent Generates | User Action Before First Deploy | Blocks Deploy? |
|--------|---------------|-----------------|--------------------------------|----------------|
| **Vault KV v2** (cross-cluster JWT) | Already exists on local OneEKS Vault — same data | Updated annotations: `role={PROJECT_ID}`, drop `auth-path`, `auth-type`, `auth-config-*` | None | **No** |
| **Vault KV v1** (`secret/` paths) | Synced identically to all OneEKS instances | `extra_policy_ro` in `cps/projects` + KV v1 annotations (`.Data` format) | None | **No** |
| **K8s Secrets** (`secretRef`, volume mounts) | Don't exist in the new `{PROJECT_ID}` namespace — must be migrated to OneSecrets | Replaces `secretRef`/volume mounts with Vault sidecar: file secrets → `agent-inject-template-*` file injection, env secrets → `environmentSecrets` | Create the secret values in Vault UI at `{PROJECT_ID}/data/{secret-name}` before first deploy | **Yes** — pods will fail if OneSecrets values don't exist |
| **AWS Secrets Manager** (via SDK/starter) | App reads from AWS SM at runtime — must migrate to OneSecrets | OneSecrets annotations targeting `{PROJECT_ID}/data/{secret-name}` | Migrate secrets to OneSecrets before first deploy. See [Migrating Secrets](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/oneeks/tasks/manage-secrets/migrating-secrets/) | **Yes** — app will fail to read secrets unless migrated |
| **AWS SM** (via Vault sidecar only) | Secret values must exist in OneSecrets KV v2 | OneSecrets annotations targeting `{PROJECT_ID}/data/{secret-name}` | Create secret values in Vault UI before first deploy | **Yes** — sidecar will fail to read |
| **Hardcoded env vars** | Values moved to ConfigMaps | `state_values/*.yaml` entries (OneConfig pattern) | None | **No** |

> **AWS Secrets Manager note**: Services using AWS Secrets Manager (e.g., via SDK or
> Spring starters) must migrate those secrets to **OneSecrets** (Vault KV v2) before the
> first Sonic deploy. See [Migrating Secrets](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/oneeks/tasks/manage-secrets/migrating-secrets/).

**What the agent always generates** (regardless of `day1_status`):
- Vault sidecar annotations in the Sonic helm values (targeting OneSecrets KV v2 paths)
- `extra_policy_ro` in `cps/projects` (only if the service needs to read secrets outside its own project KV v2 mount or from KV v1 `secret/` paths). Note: `onesecrets:` is just a YAML parent key for `extra_policy_ro` — it is NOT a feature toggle. OneSecrets is enabled by default on all PDV clusters.
- Workload Role if AWS resources detected
- `vaultRole` and `vaultSecretPath` in `sonic.yml`

**What the agent never blocks on**:
- Actual secret values existing in Vault UI
- AWS SM → OneSecrets code changes (that's the team's workstream)
- K8s Secret recreation (documented as a pre-deploy step, not a PR gate)

**What the agent explicitly warns about**:
- Any secret with `day1_status = recreate` or `blocked` — these will cause pod failures
  if not addressed before the first Sonic deployment. The agent lists them in the Phase 7
  summary under "Before First Deploy" with exact commands.

### Secrets Migration Checklist Format (for Phase 7)

Generate this table in the migration summary, **grouped by `day1_status`**:

```markdown
## Secrets Status

### ✅ Works Immediately (no action needed)
| Secret | Source | What Was Generated |
|--------|--------|--------------------|  
| {name} | Vault KV v2 / KV v1 / AWS SM (via SDK) | Updated annotations + extra_policy_ro / Workload Role |

### ⚠️ Before First Deploy
| Secret | Source | Action Required |
|--------|--------|----------------|
| {name} | K8s Secret | `kubectl get secret -n {OLD_NS} {name} -o yaml \| kubectl apply -n {PROJECT_ID} -f -` |
| {name} | AWS SM (sidecar only) | Create `{PROJECT_ID}/data/{secret-name}` in Vault UI |

### 🔄 Migrate Later (separate workstream)
| Secret | Current Source | OneSecrets Path | Vault Instances |
|--------|---------------|-----------------|----------------|
| {name} | AWS SM | {PROJECT_ID}/data/{secret-name} | {Vault UI URLs per env} |

Follow the [Backstage Migrating Secrets guide](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/oneeks/tasks/manage-secrets/migrating-secrets/).

### How to Create OneSecrets
1. Log into Vault UI via Okta: `https://vault.{env}.{region}.{stage}.jet-internal.com`
2. Navigate to `{PROJECT_ID}/` → Create secret
3. Add key-value pairs matching the template annotations
4. Repeat for each environment and bulkhead
```

## CloudOps Context

CloudOps-EKS used **AWS Secrets Manager** (now deprecated). Sonic Runtime standardizes on
**OneSecrets** (Vault KV v2). All CloudOps secrets must be migrated to OneSecrets.
Non-sensitive configuration values (environment URLs, feature flags, log levels) should use
**OneConfig** — ConfigMaps managed through Helmfile state values.

Migration paths for CloudOps:
- **AWS Secrets Manager → OneSecrets KV v2** (`{project}/data/` path) — the standard path
- **Some CloudOps services already read from OneSecrets** (Vault KV v2) via cross-cluster auth.
  These use the `auth/{legacy_env}` auth path (e.g., `auth/eks-cluster-prod`) and a role
  following the naming convention `{project}_{cluster}_{namespace}_star`. These secrets
  continue working on Sonic Runtime — only the auth path changes.

### Reading OneSecrets from CloudOps (Pre-Migration Validation)

You can validate OneSecrets access while still on CloudOps by adding these podAnnotations:

```yaml
podAnnotations:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/agent-run-as-user: "1337"
  vault.hashicorp.com/tls-skip-verify: "true"
  vault.hashicorp.com/auth-type: "jwt"
  vault.hashicorp.com/auth-path: "auth/{legacy_env}"  # e.g. "auth/eks-cluster-prod"
  vault.hashicorp.com/auth-config-path: "/var/run/secrets/kubernetes.io/serviceaccount/token"
  vault.hashicorp.com/auth-config-role: "{project}_{cluster}_{namespace}_star"
  vault.hashicorp.com/auth-config-remove_jwt_after_reading: "false"
  vault.hashicorp.com/agent-inject-secret-mysecret: "{project}/data/{secret-name}"
```

Cluster environment mapping: **Use the mapping confirmed in Phase 4 Q2** (fetched from
Backstage). Do not hardcode environment names here. The mapping for the user's selected
bulkheads will have been confirmed before reaching this step.

The OneSecrets role must be explicitly requested in `cps/projects` with `extra_policy_ro_legacy`
or by enabling the legacy auth path in the project YAML.

### `external_clusters` — Enabling Cross-Cluster Access

OneSecrets (KV v2) is enabled by default on all PDV clusters — the environment-level flag `onesecrets_enabled` is `true` in every environment's `values.yml`. There is no need to set `onesecrets.enabled: true` per project.

To read from OneEKS Vault while still running on CloudOps-EKS, the project must configure
`external_clusters` in `cps/projects`. This creates JWT auth roles on the OneEKS Vault so
CloudOps pods can authenticate using their service account token:

```yaml
# In cps/projects/projects/pdv/{PROJECT_ID}.yml
# NOTE: external_clusters is a TOP-LEVEL field
external_clusters:
  - cluster_name: eks-cluster-staging-2   # CloudOps staging cluster
    namespace: {NAMESPACE}                 # Namespace where pods run on CloudOps
  - cluster_name: eks-cluster-prod         # CloudOps production cluster
    namespace: {NAMESPACE}
```

This is useful for **pre-migration validation** — you can verify secrets are readable from
OneEKS Vault before cutting over. After full migration to Sonic Runtime, the `external_clusters`
entries can be removed.

---

## Production Vault Instances

Each OneEKS cluster runs its own Vault instance. These are independent HashiCorp Vault clusters.
The `cps/vault` CI/CD pipeline synchronizes **static secrets** and **policies** across all
instances of the same `env_type` (prod, stage, etc.).

| Instance | Vault URL | Bulkhead |
|---|---|---|
| `euw1-pdv-prd-5` | `vault.pdv-5.eu-west-1.production.jet-internal.com` | EU1 |
| `euw1-pdv-prd-6` | `vault.pdv-6.eu-west-1.production.jet-internal.com` | EU2 |
| `usw2-pdv-prd-2` | `vault.pdv-2.us-west-2.production.jet-internal.com` | NA1 |
| `apse2-pdv-prd-3` | `vault.pdv-3.ap-southeast-2.production.jet-internal.com` | OC1 |

### What Is Shared vs What Differs Across Instances

| Aspect | Shared across all `prod` instances? | Details |
|---|---|---|
| OneSecrets KV v2 (`<project>/`) | **Yes** — each instance has the mount | Team manages secrets per instance independently |
| Static secrets (`secret/` KV v1) | **Yes** — identical copies | CI/CD pushes `secrets/prod/` to every instance |
| Policies (`vars/apps/prod/`) | **Yes** — identical | Same `apps.tfvars` applied to all |

> **Note**: Legacy dynamic backends (`database/creds/`, `rabbitmq/creds/`) also exist on some
> instances but vary per cluster. CloudOps services migrate from AWS SM to OneSecrets KV v2
> (static secrets) and would not typically interact with dynamic Vault backends.

---

## Multi-Bulkhead Vault Topology

Each bulkhead (EU1, EU2, OC1, NA1) has its own **separate Vault instance** in its AWS region.
OneSecrets KV v2 secrets do NOT sync between bulkheads — you must create secrets in each
bulkhead's Vault independently via the Vault UI (Okta login). The annotation format is
identical across bulkheads; only the secret data must be replicated manually.

> **Important**: OneSecrets KV v2 is available in **all** bulkheads. Since CloudOps services
> migrate from AWS SM to OneSecrets KV v2 (static secrets), multi-bulkhead deployment works
> seamlessly — just create the same secrets in each bulkhead's Vault UI independently.
> If a CloudOps service also reads from legacy `secret/` KV v1 paths (e.g., shared config
> from other teams), those are synced identically across all instances, so they also work
> everywhere.

| Capability | All Bulkheads (EU1, EU2, NA1, OC1) |
|---|---|
| OneSecrets KV v2 (`<project>/data/`) | ✅ Available on all |
| Legacy `secret/` KV v1 (via `extra_policy_ro`) | ✅ Synced identically across all |

---

## Migration Scenarios & Decision Tree

### Scenario A: CloudOps → OneSecrets (Standard Path)

**When**: CloudOps service uses AWS Secrets Manager (most common).

**Actions**:
1. Identify all secrets in AWS Secrets Manager
2. If cross-project or KV v1 `secret/` access is needed, add `onesecrets.extra_policy_ro` in project YAML (`cps/projects`). OneSecrets KV v2 access to the project's own mount is available by default — no `onesecrets:` block needed unless extra policies are required.
3. Create secrets in project's KV v2 mount via Vault UI (Okta login) or Vault CLI
4. Configure Vault agent annotations with KV v2 template format (`.Data.data`)
5. Secret paths: `{project-name}/data/{secret-name}` (note: `data/` is required for KV v2 API)
6. Remove AWS Secrets Manager dependencies from application code (e.g., `spring-boot-aws-secretsmanager-starter`)
7. Set Vault role = PROJECT_ID

### Scenario B: CloudOps Already Using OneSecrets (Partial Migration)

**When**: CloudOps service already reads some secrets from OneSecrets via cross-cluster auth
(paths like `{project}/data/...`, role like `{project}_{cluster}_{namespace}_star`).

**Actions**:
1. These secrets already exist in OneSecrets — no migration needed for them
2. After migration to Sonic Runtime, the auth path changes from `auth/{legacy_env}` to standard
   Kubernetes auth, but secret paths remain the same
3. Update annotations: remove `auth-path`, `auth-type: jwt`, `auth-config-*` (not needed on Sonic Runtime)
4. Set Vault role = PROJECT_ID (instead of the `{project}_{cluster}_{namespace}_star` format)
5. Any remaining AWS SM secrets still need Scenario A treatment

### Scenario C: Non-EU1 Bulkheads (Per-Bulkhead Setup)

**When**: Deploying to EU2, OC1, or NA1 (alone or in addition to EU1).

**Actions**:
1. Each bulkhead has its own Vault instance — secrets don't sync between them
2. Create secrets in each bulkhead's OneSecrets independently
3. Use KV v2 template format (`.Data.data`) — same annotations work across all bulkheads
4. The Vault agent sidecar always connects to the local cluster Vault automatically

### Scenario D: Shared/Cross-Project Vault Secrets

**When**: Service needs to read secrets owned by another project on Sonic Runtime.

**Actions**:
1. Use `extra_policy_ro` to grant read access to the other project's secret path
2. The owning project must approve the policy addition in `cps/projects`

---

## `extra_policy_ro` Configuration

The `extra_policy_ro` field in `cps/projects/projects/pdv/{PROJECT_ID}.yml` is a raw HCL Vault
policy string appended to the project's read-only policy.

### Format

```yaml
# In cps/projects/projects/pdv/{PROJECT_ID}.yml
onesecrets:
  enabled: true
  extra_policy_ro: |
    path "secret/{app-name}/*" { capabilities=["read"] }
    path "secret/shared-config/{app-name}" { capabilities=["read"] }
```

### How It Works (from `cps/projects/modules/onesecrets/ro-role.tf`)

The `extra_policy_ro` content is concatenated with the default project read policy:

```hcl
resource "vault_policy" "role-ro" {
  name   = "${each.key}-ro"
  policy = join("\n", [
    # Default: read from project's own KV v2 mount
    "path \"${each.key}/*\" { capabilities = [\"read\", \"list\"] }",
    # Plus extra_policy (if any)
    try(each.value.config.onesecrets.extra_policy, ""),
    # Plus extra_policy_ro (if any)
    try(each.value.config.onesecrets.extra_policy_ro, "")
  ])
}
```

This policy is attached to the Kubernetes auth role:

```hcl
resource "vault_kubernetes_auth_backend_role" "kubernetes" {
  backend                          = data.vault_auth_backend.kubernetes.path  # "kubernetes"
  role_name                        = each.key  # project name
  bound_service_account_namespaces = [each.key]
  bound_service_account_names      = ["*"]
  token_policies                   = ["default-onesecrets", "${each.key}-ro"]
}
```

This policy applies to both Kubernetes auth (sidecar) and GitHub JWT auth (GHA workflows).

### Real Examples

```yaml
# Single secret path
onesecrets:
  enabled: true
  extra_policy_ro: |
    path "secret/confluent_cloud/fee-config-service" { capabilities=["read"] }
```

```yaml
# Multiple paths (Vault + dynamic DB creds)
onesecrets:
  extra_policy_ro: |
    path "secret/voucher-redemption-service/*" { policy="read" }
    path "secret/payments-gateway/auth-users/voucher-redemption-service" { capabilities=["read"] }
    path "database/creds/voucher-redemption-service-ro" { policy="read" }
    path "database/creds/voucher-redemption-service-rw" { policy="read" }
```

### `extra_policy` vs `extra_policy_ro` vs `extra_policy_rw`

| Field | Applied To | Use Case |
|-------|-----------|----------|
| `extra_policy_ro` | Kubernetes auth + GitHub JWT (read-only) | Application reading secrets at runtime |
| `extra_policy_rw` | Vault UI Okta login (read-write) | Team managing secrets via Vault UI |
| `extra_policy` | All of the above | Legacy compat (adds to both RO and RW) |

For migration, `extra_policy_ro` is the correct choice.

---

## Vault URL Construction

Vault URLs for OneEKS clusters follow this pattern:

```
https://vault.{env_function}-{partition_id}.{aws_region}.{environment}.jet-internal.com
```

Examples:

| Cluster        | Vault URL                                                   |
| -------------- | ----------------------------------------------------------- |
| euw1-pdv-qa-2  | `https://vault.pdv-2.eu-west-1.qa.jet-internal.com`         |
| euw1-pdv-stg-5 | `https://vault.pdv-5.eu-west-1.staging.jet-internal.com`    |
| euw1-pdv-prd-5 | `https://vault.pdv-5.eu-west-1.production.jet-internal.com` |

You do NOT need to configure these URLs in annotations — the Vault agent sidecar discovers
the Vault address automatically. These are useful for:
- GHA Vault action `url` parameter
- Debugging with Vault CLI
- Vault UI access (Okta login)

---

## Detection: Discovering Current Vault Usage (Phase 2)

Search the source repository for existing Vault/secrets patterns:

| What | Command |
|------|---------|
| Vault agent annotations | `grep -r "vault.hashicorp.com" helmfile.d/ deploy/ k8s/ chart/ --include="*.yaml" --include="*.yml" --include="*.gotmpl"` |
| Vault paths in app config | `grep -rn "secret/" --include="*.yaml" --include="*.yml" --include="*.json" --include="*.gotmpl"` |
| GHA Vault action | `grep -r "hashicorp-vault-action\|vault-action" .github/workflows/` |
| AWS Secrets Manager usage | `grep -rn "aws-secretsmanager\|secretsmanager\|aws.secretsmanager" --include="*.java" --include="*.kt" --include="*.gradle*" --include="*.xml" --include="*.yaml" --include="*.yml"` |
| Spring Boot AWS SM starter | `grep -rn "spring-boot-aws-secretsmanager" --include="*.gradle*" --include="*.xml"` |
| Env vars referencing secrets | `grep -rn "VAULT_ADDR\|VAULT_ROLE\|VAULT_SECRET_PATH\|AWS_SECRET" --include="*.yaml" --include="*.yml"` |

Also check `cps/projects` for existing OneSecrets config:

```bash
cat /tmp/cps-projects/projects/pdv/{PROJECT_ID}.yml
```

Look for: `onesecrets` section (`enabled`, `extra_policy_ro`, `extra_policy`, `extra_policy_rw`, `external_clusters`).

### cps/vault Lookup (Optional — If Service Already Uses Vault)

Some CloudOps services already have Vault configuration (e.g., if they partially read from
OneSecrets via cross-cluster auth). If so, check the Vault infra repo:

```bash
gh repo clone github.je-labs.com/cps/vault /tmp/cps-vault -- --depth 1

# App Vault config (staging)
cat /tmp/cps-vault/vars/apps/stage/{APP_NAME}.yml 2>/dev/null

# App Vault config (production)
cat /tmp/cps-vault/vars/apps/prod/{APP_NAME}.yml 2>/dev/null
```

Most CloudOps services will NOT have entries here since they used AWS SM, not Vault.
Only check this if Phase 2 discovery found existing `vault.hashicorp.com` annotations
or OneSecrets paths in the service's helm values.

---

## Vault Sidecar Annotations

### KV v1 — Legacy Secrets (via `extra_policy_ro`)

Used when the service needs to read from legacy `secret/*` paths shared by other teams.
This is NOT the standard CloudOps migration path — use KV v2 for your own secrets.

```yaml
podAnnotations:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/agent-run-as-user: "1337"
  vault.hashicorp.com/role: "{{PROJECT_ID}}"
  vault.hashicorp.com/agent-inject-template-legacy.json: |
    {{`{{- with secret "secret/{{APP_NAME}}" }}`}}
    {{`{{ .Data | toUnescapedJSON }}`}}
    {{`{{- end }}`}}
```

Notes:
- `secret/{{APP_NAME}}` = legacy KV v1 path
- `.Data` = KV v1 format (no nested `data` key — different from KV v2)
- Requires `extra_policy_ro` in `cps/projects` granting read access to the legacy path

### KV v2 — OneSecrets (Recommended)

> **Recommended approach**: Mount secrets as files. This provides dynamic secret updates
> (no pod restart needed), consistency across languages, and better security (secrets not
> visible via `kubectl describe pod`). Only use environment variable injection as a last
> resort for third-party applications where code cannot be modified.

```yaml
podAnnotations:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/agent-run-as-user: "1337"
  vault.hashicorp.com/role: "{{PROJECT_ID}}"
  vault.hashicorp.com/agent-inject-template-secrets.json: |
    {{`{{- with secret "{{PROJECT_ID}}/data/{{SECRET_NAME}}" }}`}}
    {{`{{ .Data.data | toUnescapedJSON }}`}}
    {{`{{- end }}`}}
```

Notes:
- `{{PROJECT_ID}}/data/{{SECRET_NAME}}` = KV v2 path (project's own mount)
- `.Data.data` = KV v2 format (nested `data` key)
- `data/` in the path is required for KV v2 API reads
- Secrets are mounted at `/vault/secrets/{template-name}` (e.g., `/vault/secrets/secrets.json`)

### Multiple Secret Files

Each secret file needs its own `agent-inject-template-*` annotation:

```yaml
podAnnotations:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/agent-run-as-user: "1337"
  vault.hashicorp.com/role: "{{PROJECT_ID}}"
  vault.hashicorp.com/agent-inject-template-db-creds.json: |
    {{`{{- with secret "{{PROJECT_ID}}/data/db-credentials" }}`}}
    {{`{{ .Data.data | toUnescapedJSON }}`}}
    {{`{{- end }}`}}
  vault.hashicorp.com/agent-inject-template-api-keys.json: |
    {{`{{- with secret "{{PROJECT_ID}}/data/api-keys" }}`}}
    {{`{{ .Data.data | toUnescapedJSON }}`}}
    {{`{{- end }}`}}
```

Secrets injected to `/vault/secrets/{template-name}` — e.g., `/vault/secrets/db-creds.json`.

---

## sonic.yml Vault Metadata

```yaml
metadata:
  metadataId: {{APP_NAME}}
  project: {{PROJECT_ID}}
  team: {{TEAM_NAME}}
  vaultRole: {{PROJECT_ID}}          # Vault role = project name
  vaultSecretPath: {{SECRET_PATH}}   # See table below
```

| Strategy | vaultSecretPath | Notes |
|----------|----------------|-------|
| OneSecrets (KV v2) | `{{PROJECT_ID}}/data/{{APP_NAME}}` | Project KV v2 mount |
| None | (omit or leave empty) | No Vault integration |

---

## GHA Vault Access

```yaml
- uses: github-actions/hashicorp-vault-action@v2
  with:
    url: https://vault.{BULKHEAD_ENV}.{REGION}.{STAGE}.jet-internal.com  # Derive from Phase 4 env mapping
    method: jwt
    path: auth/github-jwt
    role: {{PROJECT_ID}}
    secrets: |
      {{PROJECT_ID}}/data/{{APP_NAME}} key1 | SECRET_VALUE ;
```

The `github-jwt` auth backend is configured in OneEKS Vault clusters. The `-ro` policy
(including `extra_policy_ro`) is applied to the GitHub JWT role.

---

## Step-by-Step Checklist: CloudOps → OneSecrets (KV v2, Standard Path)

1. [ ] Identify all secrets in AWS Secrets Manager used by the service
2. [ ] If cross-project or KV v1 `secret/` access needed, add `onesecrets.extra_policy_ro` in project YAML. OneSecrets is enabled by default — a bare `onesecrets:` block is not needed.
3. [ ] Create secrets in project's KV v2 mount via Vault UI (Okta login)
4. [ ] If app uses `spring-boot-aws-secretsmanager-starter` or similar: remove the dependency
5. [ ] Generate Vault agent annotations in helm values (KV v2 format)
6. [ ] Set `vaultRole` and `vaultSecretPath` in sonic.yml metadata
7. [ ] Optional: validate secrets from CloudOps using `auth/{legacy_env}` path before migration
8. [ ] After deployment: check sidecar logs (`kubectl logs -n {PROJECT_ID} {pod} -c vault-agent`)

## Step-by-Step Checklist: CloudOps Already Using OneSecrets (Partial Migration)

1. [ ] Identify which secrets are already in OneSecrets (look for `{project}/data/` Vault paths)
2. [ ] Identify remaining secrets still in AWS Secrets Manager
3. [ ] Create AWS SM secrets in OneSecrets KV v2 mount (same as standard path)
4. [ ] Update Vault annotations: remove cross-cluster auth fields (`auth-path`, `auth-type`, `auth-config-*`)
5. [ ] Update Vault role from `{project}_{cluster}_{namespace}_star` to just `{PROJECT_ID}`
6. [ ] Set `vaultRole` and `vaultSecretPath` in sonic.yml metadata
7. [ ] After deployment: verify all secrets load correctly from local cluster Vault

## Vault Configuration Validation Checklist

1. [ ] `vaultRole` in sonic.yml = PROJECT_ID
2. [ ] New secrets use KV v2 format (`.Data.data`) — KV v1 (`secret/`) is only for existing cross-project reads via `extra_policy_ro`
3. [ ] Secret paths follow `{project}/data/{secret-name}` format
4. [ ] Cross-cluster auth annotations removed (no `auth-path`, `auth-type`, `auth-config-*`)
5. [ ] No references to AWS Secrets Manager remain in code/config
6. [ ] For multi-bulkhead: secrets exist in each bulkhead's Vault independently
