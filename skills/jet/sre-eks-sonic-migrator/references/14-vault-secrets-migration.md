# Vault & OneSecrets Migration

## Architecture: Separate Vault Instances with Synced Data

Each OneEKS cluster runs its **own Vault instance**, separate from the SRE-EKS Vault. They are
independent HashiCorp Vault clusters with their own DynamoDB storage backends. However, they
share the same `env_type` (`prod`, `stage`, etc.) and the `cps/vault` CI/CD pipeline
synchronizes **static secrets** and **policies** across all instances of the same `env_type`.

The code comment in `cps/projects/modules/onesecrets/ro-role.tf` saying "OneSecrets runs in the
same Vault instances as SRE EKS Vault" refers to the fact that legacy KV v1 secret engines
(`secret/`) and OneSecrets KV v2 mounts (`<project>/`) coexist on each OneEKS Vault instance --
not that the OneEKS Vault and SRE-EKS Vault are the same server.

### Production Vault Instances (all `env_type: "prod"`)

| Instance               | Vault URL                                                | Type            |
| ---------------------- | -------------------------------------------------------- | --------------- |
| `sre-eks-production-1` | `vault.int.sre-eks-production-1.tkwy.cloud`              | Legacy SRE-EKS  |
| `euw1-pdv-prd-5`       | `vault.pdv-5.eu-west-1.production.jet-internal.com`      | OneEKS (EU1)    |
| `euw1-pdv-prd-6`       | `vault.pdv-6.eu-west-1.production.jet-internal.com`      | OneEKS (EU2)    |
| `usw2-pdv-prd-2`       | `vault.pdv-2.us-west-2.production.jet-internal.com`      | OneEKS (NA1)    |
| `apse2-pdv-prd-3`      | `vault.pdv-3.ap-southeast-2.production.jet-internal.com` | OneEKS (OC1)    |
| `marprod`              | (Marathon production)                                    | Legacy Marathon |

### What Is Shared vs What Differs

| Aspect                       | Shared across all `prod` instances?      | Details                                        |
| ---------------------------- | ---------------------------------------- | ---------------------------------------------- |
| Static secrets (`secret/`)   | **Yes** -- identical copies              | CI/CD pushes `secrets/prod/` to every instance |
| Policies (`vars/apps/prod/`) | **Yes** -- identical                     | Same `apps.tfvars` applied to all              |
| Instance-specific secrets    | **No** -- unique per instance            | From `secrets/instance-specific/<instance>/`   |
| Database dynamic backends    | **No** -- varies per instance            | See backend coverage table below               |
| RabbitMQ dynamic backends    | **No** -- varies per instance            | Different servers per instance                 |
| AWS secrets engine           | **No** -- only on `sre-eks-production-1` | Not mounted on any OneEKS instance             |

### Dynamic Backend Coverage (Production)

| Backend                                | `sre-eks-production-1`                   | `euw1-pdv-prd-5`                                      | `euw1-pdv-prd-6`            | `usw2-pdv-prd-2`            | `apse2-pdv-prd-3`           |
| -------------------------------------- | ---------------------------------------- | ----------------------------------------------------- | --------------------------- | --------------------------- | --------------------------- |
| `database-dynamic` connections         | 11 (via sre-commons ProxySQL)            | 11 (via direct connections)                           | 1 (`orderissues-glob` only) | 1 (`orderissues-glob` only) | 1 (`orderissues-glob` only) |
| `rabbitmq/`                            | Yes (`sre-commons-production-1`)         | Yes (`tk-rabbitmq.eu-west-1`) -- **different server** | No                          | No                          | No                          |
| `aws/`                                 | Yes (`sre-commons-production-1` account) | No                                                    | No                          | No                          | No                          |
| KV v1 `secret/`                        | Yes                                      | Yes (same data)                                       | Yes (same data)             | Yes (same data)             | Yes (same data)             |
| KV v1 `database/` (semi-dynamic creds) | Yes                                      | Yes                                                   | Yes                         | Yes                         | Yes                         |

**Key implication**: Even though the **policy** for `database/creds/myapp-ro` exists on all
instances, the actual credential generation will **fail** on instances where the corresponding
database connection is not configured in `secret-backends.tfvars`. Only `sre-eks-production-1`
and `euw1-pdv-prd-5` have most database connections configured.

```
OneEKS Cluster (e.g., euw1-pdv-prd-5)
  |
  +-- Vault Agent Sidecar (in each pod that needs secrets)
  |     |
  |     +-- Connects to LOCAL cluster Vault:
  |     |   https://vault.pdv-5.eu-west-1.production.jet-internal.com
  |     |
  |     +-- Authenticates via: Kubernetes auth backend (path "kubernetes")
  |     |
  |     +-- Gets token with policies:
  |           - default-onesecrets (basic token management)
  |           - <project-name>-ro  (read <project-name>/* KV v2)
  |           - plus extra_policy_ro paths (if configured)
  |
  +-- LOCAL Vault Instance (separate from sre-eks-production-1, but synced data)
        |
        +-- KV v2 mounts: <project-name>/  (one per project -- "OneSecrets")
        +-- KV v1 mount:  secret/          (synced copy of legacy secrets)
        +-- Dynamic secrets: database/, rabbitmq/ (coverage varies -- see table above)
        +-- Auth backends: kubernetes, oidc, github-jwt, plus JWT trust for other clusters
```

**Key implications**:

- The Vault agent sidecar always connects to the **local cluster Vault** -- no remote URLs needed
- Legacy static secret paths (`secret/...`) exist on all OneEKS Vault instances (synced from same source)
- Legacy dynamic secret paths (`database/creds/...`, `rabbitmq/creds/...`) exist only on instances where the backend is configured -- **primarily `euw1-pdv-prd-5`**
- Access to legacy paths requires an explicit read policy via `extra_policy_ro` in `cps/projects`
- The `vault.hashicorp.com/service` annotation is NOT needed -- the sidecar's default Vault address is correct

---

## Instance Capability by Cluster

> **WARNING — Legacy Resource Access**
>
> EU1 (`euw1-pdv-prd-5`) is the **only** bulkhead with broad access to legacy Takeaway
> resources — including legacy database connections (via `database-dynamic`), RabbitMQ
> backends, and most dynamic secret backends. Non-EU1 bulkheads (EU2, NA1, OC1) have
> **severely limited** legacy resource access. If your workload depends on legacy resources
> whose secrets are only available in the EU1 bulkhead, deploying to non-EU1 bulkheads will
> result in **runtime failures** (credential generation fails, connection errors).
>
> If you need legacy resource access from a non-EU1 bulkhead, reach out to
> `#help-core-platform-services` or `#help-sonic` on Slack for guidance before proceeding.

Not all OneEKS Vault instances have the same backend coverage. The distinction is **not simply
EU1 vs Non-EU1** -- it depends on which backends have been configured per instance in
`cps/vault/environments/prod/<instance>/secret-backends.tfvars`.

| Aspect                                   | `euw1-pdv-prd-5` (EU1)            | `euw1-pdv-prd-6` (EU2)      | `usw2-pdv-prd-2` (NA1)      | `apse2-pdv-prd-3` (OC1)     |
| ---------------------------------------- | --------------------------------- | --------------------------- | --------------------------- | --------------------------- |
| Legacy `secret/` KV v1                   | Yes (synced from `secrets/prod/`) | Yes (synced)                | Yes (synced)                | Yes (synced)                |
| `database-dynamic` connections           | 11 connections (full)             | 1 connection only           | 1 connection only           | 1 connection only           |
| `rabbitmq/` dynamic creds                | Yes                               | No                          | No                          | No                          |
| `aws/` dynamic creds                     | No                                | No                          | No                          | No                          |
| OneSecrets KV v2 (`<project>/`)          | Yes                               | Yes                         | Yes                         | Yes                         |
| `extra_policy_ro` for `secret/*`         | Works (data exists)               | Works (data exists)         | Works (data exists)         | Works (data exists)         |
| `extra_policy_ro` for `database/creds/*` | Works (most connections exist)    | Limited (1 connection only) | Limited (1 connection only) | Limited (1 connection only) |
| `extra_policy_ro` for `rabbitmq/creds/*` | Works (different RabbitMQ server) | Fails (no backend)          | Fails (no backend)          | Fails (no backend)          |

**Important**: All instances receive the same **policies** from `vars/apps/prod/`, so an
`extra_policy_ro` for `database/creds/myapp-ro` will be accepted on any instance. However,
the actual credential generation will **fail at runtime** if the database connection for that
role is not configured on that instance's `secret-backends.tfvars`.

Services deploying to clusters other than `euw1-pdv-prd-5` that need dynamic database or
RabbitMQ credentials should either:

- Use OneSecrets (KV v2) with static credentials managed by the team
- Request the necessary database connections be added to the target instance's `secret-backends.tfvars` in `cps/vault`
- Use only static secrets from `secret/` (which are synced everywhere)

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

You do NOT need to configure these URLs — the Vault agent sidecar discovers the Vault address
automatically from the cluster's internal configuration.

---

## Detection: Discovering Current Vault Usage (Phase 2.3b)

### In-Repo Detection

Search the source repository for existing Vault patterns:

1. **Vault agent annotations** — search for `vault.hashicorp.com` in helm values, deployment manifests:

   ```
   grep -r "vault.hashicorp.com" helmfile.d/ deploy/ k8s/ chart/ --include="*.yaml" --include="*.yml" --include="*.gotmpl"
   ```

   Extract: role name, secret paths, template format (KV v1 `.Data` vs KV v2 `.Data.data`)

2. **Vault paths in app config** — search for `secret/`, `database/creds/`, `rabbitmq/creds/`:

   ```
   grep -rn "secret/" --include="*.yaml" --include="*.yml" --include="*.json" --include="*.gotmpl"
   ```

3. **GHA Vault action** — search for `hashicorp-vault-action` in `.github/workflows/`:

   ```
   grep -r "hashicorp-vault-action\|vault-action" .github/workflows/
   ```

4. **Environment variables** — look for `VAULT_ADDR`, `VAULT_ROLE`, `VAULT_SECRET_PATH` in configs

### cps/vault Lookup

Clone and check the Vault infrastructure repo for app-specific configuration:

```bash
gh repo clone github.je-labs.com/cps/vault /tmp/cps-vault -- --depth 1
```

Check for app config in each environment (directories use short names matching `env_type`):

```bash
# Dev
cat /tmp/cps-vault/vars/apps/k8s-dev/{APP_NAME}.yml 2>/dev/null

# Staging
cat /tmp/cps-vault/vars/apps/stage/{APP_NAME}.yml 2>/dev/null

# Production
cat /tmp/cps-vault/vars/apps/prod/{APP_NAME}.yml 2>/dev/null
```

App config files contain: `kubernetes_roles`, `policy` (read/write capabilities), `approle` (if used),
`database_roles_dynamic` (if using dynamic DB credentials).

Note: The same policies are applied to **all** vault instances sharing an `env_type`. For
example, all `prod` instances (`sre-eks-production-1`, `euw1-pdv-prd-5`, `euw1-pdv-prd-6`,
`usw2-pdv-prd-2`, `apse2-pdv-prd-3`, `marprod`) get the same `apps.tfvars` generated from
`vars/apps/prod/`.

### cps/projects Lookup

Check if the project already has OneSecrets configured:

```bash
cat /tmp/cps-projects/projects/pdv/{PROJECT_ID}.yml
```

Look for existing `onesecrets` section: `enabled`, `extra_policy_ro`, `extra_policy`, `extra_policy_rw`,
`external_clusters`.

---

## Migration Scenarios & Decision Tree

### Scenario A: euw1-pdv-prd-5 + Legacy Secrets (Simplest)

**When**: Deploying to `euw1-pdv-prd-5` (EU1 primary), service currently uses legacy Vault (`secret/` paths,
`database/creds/`, `rabbitmq/creds/`).

**Actions**:

1. Add `extra_policy_ro` to project YAML in `cps/projects` granting read access to the legacy
   secret paths the service needs
2. Configure Vault agent annotations in helm values with KV v1 template format (`.Data`)
3. Set Vault role = PROJECT_ID in annotations and sonic.yml

**No changes needed to**:

- Vault URLs (local cluster Vault is correct)
- Static secret content (`secret/` paths contain the same data, synced from the same source)
- Application code (same secret format at the file level)

**Caveats for dynamic secrets**:

- `database/creds/` -- `euw1-pdv-prd-5` has most database connections configured (11 connections)
  but uses different connection URLs than `sre-eks-production-1` (direct connections vs ProxySQL).
  Verify the specific database role exists in `cps/vault/environments/prod/euw1-pdv-prd-5/secret-backends.tfvars`
- `rabbitmq/creds/` -- `euw1-pdv-prd-5` connects to a **different RabbitMQ server**
  (`tk-rabbitmq.eu-west-1.production.jet-internal.com`) than `sre-eks-production-1`
  (`awsproduction-rabbitmq.sre-commons-production-1.tkwy.cloud`). Verify the credentials work
  with the correct RabbitMQ endpoint your app connects to
- `aws/creds/` -- NOT available on `euw1-pdv-prd-5`. The AWS secrets engine is only mounted on
  `sre-eks-production-1`. Services needing AWS dynamic credentials must find an alternative

### Scenario B: euw1-pdv-prd-5 + Migrate to OneSecrets (KV v2)

**When**: Deploying to EU1, team wants to use the modern OneSecrets KV v2 mount instead of legacy paths.

**Actions**:

1. Ensure `onesecrets.enabled: true` in project YAML (may already be set during onboarding)
2. Copy/recreate secrets in the project's KV v2 mount (`<project-name>/`) using the Vault UI
   (Okta login) or Vault CLI
3. Configure Vault agent annotations with KV v2 template format (`.Data.data`)
4. Update secret paths in annotations from `secret/{app}` to `<project-name>/data/{secret-name}`
5. Set Vault role = PROJECT_ID

### Scenario C: Other Clusters (euw1-pdv-prd-6, usw2-pdv-prd-2, apse2-pdv-prd-3)

**When**: Deploying to clusters other than `euw1-pdv-prd-5`.

**What works**:

- Legacy `secret/` KV v1 paths -- the same static secrets are synced to all `prod` instances,
  so `extra_policy_ro` for `secret/myapp/*` will work on any cluster
- OneSecrets KV v2 mounts -- always available

**What does NOT work (or is limited)**:

- `database/creds/*` -- these clusters have only 1 database connection (`orderissues-glob`).
  Most dynamic DB credential roles will fail at runtime even though the policy is granted
- `rabbitmq/creds/*` -- not configured on these instances; credential generation will fail
- `aws/creds/*` -- not configured on any OneEKS instance

**Actions**:

1. All dynamic secrets (database, rabbitmq) must be migrated to OneSecrets KV v2 with static
   credentials managed by the team, or the necessary backend connections must be added to the
   target cluster's `secret-backends.tfvars` in `cps/vault`
2. Use KV v2 template format (`.Data.data`) in annotations for OneSecrets paths
3. Legacy `secret/` KV v1 paths CAN still be read via `extra_policy_ro` (static data is synced)
4. If ALSO deploying to `euw1-pdv-prd-5`, dynamic secrets may work there but not on other clusters --
   consider using `project_overrides` per cluster if needed

### Scenario D: GHA Vault Access

**When**: GitHub Actions workflows need to read secrets from Vault.

**Actions**:

1. Use `github-actions/hashicorp-vault-action@v2` action
2. Auth path: `auth/github-jwt` (JWT auth backend for GitHub)
3. The `extra_policy_ro` policy is also applied to the GitHub JWT role via the `-ro` policy

---

## `extra_policy_ro` Configuration

The `extra_policy_ro` field in `cps/projects/projects/pdv/{PROJECT_ID}.yml` is a raw HCL Vault
policy string appended to the project's read-only policy. It grants the Vault token (used by
both Kubernetes auth and GitHub JWT auth) permission to read additional paths on the local Vault
instance. Since static secrets (`secret/`) are synced to all instances of the same `env_type`,
this works for KV v1 paths on any cluster. For dynamic backends (`database/creds/`,
`rabbitmq/creds/`), verify the backend is configured on the target cluster.

### Format

```yaml
# In cps/projects/projects/pdv/{PROJECT_ID}.yml
onesecrets:
  enabled: true
  extra_policy_ro: |
    path "secret/{app-name}/*" { capabilities=["read"] }
    path "secret/shared-config/{app-name}" { capabilities=["read"] }
    path "database/creds/{app-name}-ro" { capabilities=["read"] }
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

### Real Example (from PR #3576: `cu-payment-par.yml`)

```yaml
onesecrets:
  enabled: true
  extra_policy_ro: |
    path "secret/confluent_cloud/fee-config-service" { capabilities=["read"] }
```

### Another Example (`cu-payment-payinc.yml`)

```yaml
onesecrets:
  extra_policy_ro: |
    path "secret/voucher-redemption-service/*" { policy="read" }
    path "secret/payments-gateway/auth-users/voucher-redemption-service" { capabilities=["read"] }
    path "database/creds/voucher-redemption-service-ro" { policy="read" }
    path "database/creds/voucher-redemption-service-rw" { policy="read" }
```

### `extra_policy` vs `extra_policy_ro` vs `extra_policy_rw`

| Field             | Applied To                               | Use Case                                        |
| ----------------- | ---------------------------------------- | ----------------------------------------------- |
| `extra_policy_ro` | Kubernetes auth + GitHub JWT (read-only) | Application reading legacy secrets at runtime   |
| `extra_policy_rw` | Vault UI Okta login (read-write)         | Team managing legacy secrets via Vault UI       |
| `extra_policy`    | All of the above                         | Legacy compat (adds to both RO and RW policies) |

For migration, `extra_policy_ro` is the correct choice — it grants read access for the application
without granting write access.

---

## Vault Sidecar Annotations

### Standard OneEKS Annotations (KV v1 — Legacy Secrets)

```yaml
podAnnotations:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/agent-run-as-user: "1337"
  vault.hashicorp.com/role: "{{PROJECT_ID}}"
  vault.hashicorp.com/agent-inject-template-secrets.json: |
    {{`{{- with secret "secret/{{APP_NAME}}" }}`}}
    {{`{{ .Data | toUnescapedJSON }}`}}
    {{`{{- end }}`}}
```

Notes:

- `role` = project name (= Kubernetes auth role created by `cps/projects`)
- `secret/{{APP_NAME}}` = legacy KV v1 path
- `.Data` = KV v1 format (no nested `data` key)
- The `agent-run-as-user: "1337"` is standard for OneEKS pods

### Standard OneEKS Annotations (KV v2 — OneSecrets)

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

### Multiple Secret Files

Each secret file needs its own `agent-inject-template-*` annotation:

```yaml
podAnnotations:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/agent-run-as-user: "1337"
  vault.hashicorp.com/role: "{{PROJECT_ID}}"
  # Legacy secret (KV v1)
  vault.hashicorp.com/agent-inject-template-legacy.json: |
    {{`{{- with secret "secret/{{APP_NAME}}" }}`}}
    {{`{{ .Data | toUnescapedJSON }}`}}
    {{`{{- end }}`}}
  # OneSecrets (KV v2)
  vault.hashicorp.com/agent-inject-template-onesecrets.json: |
    {{`{{- with secret "{{PROJECT_ID}}/data/app-config" }}`}}
    {{`{{ .Data.data | toUnescapedJSON }}`}}
    {{`{{- end }}`}}
```

Secrets are injected to `/vault/secrets/{template-name}` — e.g., `/vault/secrets/legacy.json`
and `/vault/secrets/onesecrets.json`.

---

## sonic.yml Metadata

The `metadata` section of `.sonic/sonic.yml` includes Vault configuration:

```yaml
metadata:
  metadataId: { { APP_NAME } }
  project: { { PROJECT_ID } }
  team: { { TEAM_NAME } }
  vaultRole: { { PROJECT_ID } } # Vault role = project name
  vaultSecretPath: { { SECRET_PATH } } # See below for path format
```

### vaultSecretPath Values

| Strategy           | vaultSecretPath                    | Notes                |
| ------------------ | ---------------------------------- | -------------------- |
| Legacy (KV v1)     | `secret/{{APP_NAME}}`              | Legacy secret path   |
| OneSecrets (KV v2) | `{{PROJECT_ID}}/data/{{APP_NAME}}` | Project KV v2 mount  |
| None               | (omit or leave empty)              | No Vault integration |

The `vaultRole` should always be the `PROJECT_ID` — this is the Kubernetes auth role name
created by `cps/projects`.

---

## GHA Vault Access

GitHub Actions can read Vault secrets using JWT auth:

```yaml
- uses: github-actions/hashicorp-vault-action@v2
  with:
    url: https://vault.pdv-5.eu-west-1.production.jet-internal.com
    method: jwt
    path: auth/github-jwt
    role: { { PROJECT_ID } }
    secrets: |
      secret/{{APP_NAME}} key1 | SECRET_VALUE ;
```

The `github-jwt` auth backend is configured in OneEKS Vault clusters. The `-ro` policy
(including `extra_policy_ro`) is applied to the GitHub JWT role.

---

## `external_clusters` — Cross-Cluster Access

The `external_clusters` feature in `cps/projects` enables workloads running on **legacy SRE-EKS
clusters** to authenticate to the **OneEKS Vault** and read OneSecrets. This is the reverse
direction — useful during migration when the service still runs on SRE-EKS but needs to read
from the OneSecrets KV v2 mount.

```yaml
# In cps/projects/projects/pdv/{PROJECT_ID}.yml
onesecrets:
  enabled: true
  external_clusters:
    - cluster_name: sre-eks-staging-1
      namespace: { { SRE_EKS_NAMESPACE } }
    - cluster_name: sre-eks-production-1
      namespace: { { SRE_EKS_NAMESPACE } }
```

This creates JWT auth roles on the OneEKS Vault so SRE-EKS pods can authenticate using their
service account token and read from the project's OneSecrets mount.

---

## Discovery Commands Summary

| What                                      | Command                                                                         |
| ----------------------------------------- | ------------------------------------------------------------------------------- |
| Clone Vault infra                         | `gh repo clone github.je-labs.com/cps/vault /tmp/cps-vault -- --depth 1`        |
| App Vault config (staging)                | `cat /tmp/cps-vault/vars/apps/stage/{APP_NAME}.yml`                             |
| App Vault config (production)             | `cat /tmp/cps-vault/vars/apps/prod/{APP_NAME}.yml`                              |
| Project OneSecrets config                 | `cat /tmp/cps-projects/projects/pdv/{PROJECT_ID}.yml`                           |
| Vault auth backends (per instance)        | `cat /tmp/cps-vault/environments/prod/{INSTANCE}/auth-backends.tfvars`          |
| Vault secret backends (per instance)      | `cat /tmp/cps-vault/environments/prod/{INSTANCE}/secret-backends.tfvars`        |
| Check backend coverage for target cluster | `cat /tmp/cps-vault/environments/prod/{TARGET_INSTANCE}/secret-backends.tfvars` |
| In-repo Vault annotations                 | `grep -r "vault.hashicorp.com" helmfile.d/ deploy/ --include="*.yaml"`          |
| In-repo Vault paths                       | `grep -rn "secret/" --include="*.yaml" --include="*.gotmpl"`                    |
| GHA Vault action                          | `grep -r "hashicorp-vault-action" .github/workflows/`                           |

---

## Step-by-Step Checklist: Migration with Legacy Secrets

1. [ ] **Detect** current Vault usage (Phase 2.3b detection commands above)
2. [ ] **List** all secret paths the service reads (from annotations, app config, `cps/vault`)
3. [ ] **Classify** each path: static KV v1 (`secret/`), dynamic DB (`database/creds/`), dynamic RabbitMQ (`rabbitmq/creds/`), or dynamic AWS (`aws/creds/`)
4. [ ] **Check target cluster backend coverage**: Review `cps/vault/environments/prod/{TARGET_INSTANCE}/secret-backends.tfvars` to confirm dynamic backends exist
5. [ ] **Verify** project exists in `cps/projects/projects/pdv/{PROJECT_ID}.yml`
6. [ ] **Add** `extra_policy_ro` to project YAML with read policies for each legacy path
7. [ ] **If using per-cluster overrides**: Add `extra_policy_ro` in `cps/projects/environments/pdv/eu1/{INSTANCE}/project_overrides/{PROJECT_ID}.yml`
8. [ ] **Generate** Vault agent annotations in helm values (KV v1 format)
9. [ ] **Set** `vaultRole` and `vaultSecretPath` in sonic.yml metadata
10. [ ] **Create PR** to `cps/projects` for `extra_policy_ro` changes
11. [ ] **Verify** after deployment: check sidecar logs, secret file existence, dynamic cred generation

## Step-by-Step Checklist: Migration to OneSecrets (KV v2)

1. [ ] **Ensure** `onesecrets.enabled: true` in project YAML
2. [ ] **Create** secrets in project's KV v2 mount via Vault UI (Okta login) or CI/CD
3. [ ] **Generate** Vault agent annotations in helm values (KV v2 format)
4. [ ] **Update** secret paths from `secret/{app}` to `{project}/data/{secret-name}`
5. [ ] **Set** `vaultRole` and `vaultSecretPath` in sonic.yml metadata
6. [ ] **If also using legacy paths**: Add `extra_policy_ro` for those paths
7. [ ] **Verify** after deployment: check sidecar logs, secret file existence
