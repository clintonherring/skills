# Phase 2: Discover

**Goal**: Fetch current migration docs from Backstage, analyze the cloned repo for CloudOps-EKS
indicators, run goldenpath gap analysis, trace DNS paths, and discover secrets usage.

**Load**: [03-goldenpath-structure.md](03-goldenpath-structure.md), [05-dns-and-networking.md](05-dns-and-networking.md) (discovery procedure), [05b-dns-reference.md](05b-dns-reference.md) (record types, architecture)

## 2.1 Fetch Current Migration Docs from Backstage

Search Backstage TechDocs with these terms:
1. `cloudops+sonic+runtime+migration` → main migration guide
2. `cloudops+sonic+runtime+traffic+split` → traffic split procedures
3. `cloudops+environment+mapping+sonic+runtime` → environment mappings

```bash
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "$BACKSTAGE_BACKEND_URL/api/search/query?term={SEARCH_TERM}&types%5B0%5D=techdocs" \
  | jq '.results[:5][] | {title: .document.title, text: .document.text[:500]}'
```

Compare fetched docs against the knowledge base (`01-knowledge-base.md`). If anything changed
(environment mappings, domain patterns, process steps), update the KB before proceeding.

If `BACKSTAGE_API_KEY` is expired/missing, **stop and ask the user** to provide a valid token.
Walk them through the steps: open Backstage UI → DevTools → Network → copy Bearer token →
`export BACKSTAGE_API_KEY="eyJ..."`. Only fall back to the knowledge base if the user
explicitly says they cannot provide a token, and warn them that docs may be stale.

## 2.2 Detect CloudOps-EKS Indicators

Scan the cloned repo for CloudOps-specific patterns:

- Free-form K8s manifests (not goldenpath structure)
- DNS patterns: `*.eks.tkwy-*.io` (dev/staging/prod)
- IRSA roles: `irsa_{namespace}_{sa}` (where `{sa}` is the ServiceAccount name)
- AWS Secrets Manager usage
- Terragrunt/Terraform configs

```bash
grep -rn "eks\.tkwy-" /tmp/migration-{APP_NAME}/ \
  --include="*.yaml" --include="*.yml" --include="*.json" \
  --include="*.env" --include="*.properties" \
  --include="*.cs" --include="*.go" --include="*.java" --include="*.py"
```

Any `*.eks.tkwy-*.io` domains MUST be migrated — they are unreachable from Sonic Runtime.

## 2.2a Identify Deployment Structure

CloudOps repos use **many different deployment structures** — there is no single standard.
Before extracting config, identify how this repo organizes its deployment artifacts.

**Search the repo** for deployment-related files and directories:

```bash
# Look for common deployment indicators in the cloned repo
find /tmp/migration-{APP_NAME}/ -maxdepth 3 \
  \( -name "helmfile.yaml" -o -name "helmfile.yaml.gotmpl" \
     -o -name "k8s.yml" -o -name "Chart.yaml" \
     -o -name "values.yaml" -o -name "*.yaml.gotmpl" \) \
  -not -path "*/node_modules/*" -not -path "*/.git/*" | sort
```

Also check for deployment directories:

```bash
ls -d /tmp/migration-{APP_NAME}/{helmfile.d,.deploy,.deploy-eks,deploy,helmfile,ops,k8s}/ 2>/dev/null
```

**Record the result** as `DEPLOY_STRUCTURE`:
- The path(s) where deployment config lives
- The format (helm values, raw K8s YAML, helmfile, custom chart, etc.)
- Whether it uses a shared chart (e.g., `sre/basic-application`) or a custom in-repo chart

> **Common patterns seen on CloudOps** (non-exhaustive):
>
> | Pattern | Indicators | Where to find config |
> |---------|-----------|----------------------|
> | `.deploy/k8s.yml` or `.deploy-eks/k8s.yml` | `deploy_mode: helm` at top of file | Deployment, HPA, service specs are inline in the YAML |
> | `helmfile.d/` + shared chart | `helmfile.yaml.gotmpl`, `values/`, `state_values/` dirs | Values in `values/{app}.yaml.gotmpl`, per-env in `state_values/` |
> | Flat `helmfile.yaml` + custom chart | `helmfile.yaml` at root, chart in `ops/` or `charts/` dir | Values in the helmfile releases section or custom chart values |
> | `helmfile/` dir | Directory with per-service YAML files | Per-service helmfile with values inline or in separate files |
> | `deploy/helm/` + custom chart | `Chart.yaml` + raw K8s templates in `templates/` | Values in `values.yaml`, deployment specs in templates |
>
> The agent should **read the actual files found** and adapt — do not assume a specific structure.

## 2.2b Extract Service Configuration

From the deployment files identified in step 2.2a, extract and store the service's runtime
configuration. The same set of variables is needed regardless of structure — only the location
and format differ. Read the discovered deployment files and extract these values:

**Core service config** (look for these in the deployment spec, helm values, or k8s.yml):

| Variable | What to look for | Example |
|----------|-----------------|---------|
| `CONTAINER_PORT` | Container port in deployment/pod spec | `8080` |
| `HEALTH_PATH` | Readiness or liveness probe path | `/actuator/health` |
| `HEALTH_PORT` | Probe port | `8080` |
| `SERVICE_ACCOUNT_NAME` | ServiceAccount name (if defined) | `user-api-sa` |
| `ENV_VARS[]` | Environment variables | Array of `{name, value/valueFrom}` |
| `VOLUME_MOUNTS[]` | Volume mounts | Mounted secrets, config files |
| `POD_ANNOTATIONS` | Pod annotations | Vault agent annotations, etc. |
| `PDB_MIN_AVAILABLE` | PodDisruptionBudget | `1` |

**Resource and scaling config** (may be in separate per-env files, state values, or inline):

| Variable | What to look for | Example |
|----------|-----------------|---------|
| `IMAGE_REPO` | Container image repository | `artifacts.takeaway.com/docker-prod-virtual/jetms-user-api` |
| `CPU_REQUEST` | CPU request | `300m` |
| `MEMORY_REQUEST` | Memory request | `2Gi` |
| `MEMORY_LIMIT` | Memory limit | `2Gi` |
| `MIN_REPLICAS` (per env) | HPA or autoscaler min replicas | `3` |
| `MAX_REPLICAS` (per env) | HPA or autoscaler max replicas | `4` |
| `CPU_TARGET` (per env) | HPA CPU target utilization | `100` |
| `IRSA_ROLE_ARN` (per env) | IAM role for service account | `arn:aws:iam::{AWS_ACCOUNT_ID}:role/irsa_{NAMESPACE}_{SA_NAME}` |
| `VAULT_ROLE` (per env) | Vault role | `cu-service-jetms_eks-cluster-prod_jetms_star` |
| `VAULT_PATH` (per env) | Vault auth path | `eks-cluster-prod` |

If per-environment overrides exist (e.g., separate files for staging vs. production, or
environment-specific sections), capture the per-env values. If the config is flat (single
file, no per-env split), note that and use the same values for all environments.

Store collectively as `SERVICE_CONFIG`. This avoids Phase 5 having to re-read/re-discover
these values — they're captured once here and referenced throughout.

## 2.3 Goldenpath Gap Analysis

Load `03-goldenpath-structure.md` and compare the current repo structure against it.
Using the `DEPLOY_STRUCTURE` identified in step 2.2a, produce a mapping table showing
what exists today and what needs to be created for the goldenpath target:

| Current (what exists) | Target (what it needs to become) | Action |
|---|---|---|
| _Source deployment config (wherever it lives)_ | `helmfile.d/values/{app}.yaml.gotmpl` | Convert |
| _Per-env config or env-specific sections_ | `helmfile.d/state_values/*.yaml` | Extract |
| _Current CI/CD workflow_ | `.sonic/sonic.yml` OR goldenpath GHA | Replace |
| _Ingress config (*.eks.tkwy-*.io)_ | virtualservices (*.jet-internal.com) | Migrate |
| (missing) | `helmfile.d/bases/` | Create |
| (missing) | `helmfile.d/helmfile.yaml.gotmpl` | Create |

Adapt the "Current" column to reflect the actual files found — the examples above are
generic placeholders. The target column is always the goldenpath structure.

This table drives Phase 4 (Configure) and Phase 5 (Generate). Use the Gap Analysis Checklist
from the goldenpath reference to ensure nothing is missed.

## 2.4 DNS Path Discovery

Load `05-dns-and-networking.md` (discovery procedure) and `05b-dns-reference.md` (record types, decision tree) and trace how traffic currently reaches the service:

1. Extract all hostnames from existing K8s manifests/ingress config
2. Trace each through Route53, domain-routing, and Cloudflare (if applicable)
3. Present findings as a table showing hostname → DNS path → exposure type
4. Ask user to confirm: **internal-only**, **external**, or **both**?

Store result as `EXPOSURE_TYPE` — this drives SmartGateway and domain-routing decisions.

## 2.5 Vault / Secrets Discovery

Discover all secrets usage — both application-level (AWS Secrets Manager, Spring Cloud config)
and deployment-level (Vault agent annotations, K8s secrets). This produces two outputs:
`SECRETS_INVENTORY` (what secrets exist) and `VAULT_CURRENT_CONFIG` (how Vault is currently wired).

### 2.5a Grep for secrets patterns

```bash
grep -rn "secretsmanager\|aws.*secret\|vault\.hashicorp\|/secret/" /tmp/migration-{APP_NAME}/ \
  --include="*.yaml" --include="*.yml" --include="*.json" \
  --include="*.properties" --include="*.java" --include="*.py" \
  --include="*.go" --include="*.cs" --include="*.gradle"
```

Record each finding as a `SECRETS_INVENTORY` entry:

| Field | Description |
|-------|-------------|
| `name` | Human-readable name (e.g., "RDS credentials", "Okta private key") |
| `source` | Current source: `aws-sm`, `vault-kv`, `k8s-secret`, `hardcoded`, `env-var` |
| `path` | Secret path or reference (e.g., `/secret/rds/jetms-prod-cluster/...`) |
| `env` | Which environments (staging, production, all) |
| `target` | Migration target: `onesecrets` or `already-vault` |
| `day1_status` | Sonic readiness — see classification rules below |

**`day1_status` classification rules**:

| Source | Condition | `day1_status` | Rationale |
|--------|-----------|---------------|----------|
| `vault-kv` | KV v2 path (`{project}/data/...`) | `ready` | Already in OneSecrets — just update annotations (role=PROJECT_ID, drop auth-path) |
| `vault-kv` | KV v1 path (`secret/...`) | `ready` | Synced to all OneEKS instances — use `extra_policy_ro` |
| `k8s-secret` | Any | `blocked` | Migrate to OneSecrets: agent replaces `secretRef`/volume mounts with Vault sidecar injection, team creates values in Vault UI before first deploy |
| `aws-sm` | App reads via SDK at runtime | `blocked` | Migrate secrets to OneSecrets before first deploy. See [Migrating Secrets](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/oneeks/tasks/manage-secrets/migrating-secrets/) |
| `aws-sm` | App reads via Vault sidecar only | `blocked` | Secret values must exist in OneSecrets before first deploy |
| `hardcoded` / `env-var` | Any | `ready` | Move to OneConfig (ConfigMaps via `state_values/*.yaml`) or OneSecrets in generated helm values |

### 2.5b Extract Vault agent configuration

From the deployment files identified in step 2.2a (`DEPLOY_STRUCTURE`), look for Vault
annotations and configuration. These may appear as pod annotations, helm values, or
dedicated config sections depending on the repo's deployment structure.

**Vault annotations** (search for these in deployment specs, values files, or k8s.yml):

- `vault.hashicorp.com/agent-inject` → confirms Vault is active
- `vault.hashicorp.com/auth-type` → `jwt` if using cross-cluster OneEKS Vault access, otherwise `kubernetes` (default)
- `vault.hashicorp.com/auth-path` → current auth path (e.g., `auth/eks-cluster-prod`)

**Vault role and secrets config** (may be in separate env-specific files or inline):

- `vault.role` or `environmentSecrets.role` → current Vault role name
- `vault.path` → Vault auth path per environment
- `environmentSecrets.secrets[]` → secret paths and env var mappings

Search broadly if the structure is unfamiliar:

```bash
grep -rn "vault\.\|vault:" /tmp/migration-{APP_NAME}/ \
  --include="*.yaml" --include="*.yml" --include="*.gotmpl" \
  | grep -v ".git/"
```

### 2.5c Check cps/projects for existing OneSecrets config

```bash
gh api --hostname github.je-labs.com \
  /repos/cps/projects/contents/projects/pdv/{PROJECT_ID}.yml \
  --jq '.content' | base64 -d
```

Look for:
- `onesecrets:` block → already configured for OneSecrets?
- `extra_policy_ro:` → existing cross-project Vault access
- `external_clusters:` → CloudOps cluster mappings already present

### 2.5d Check K8s secrets referenced

From the helm values, identify any K8s `Secret` references:
- `envFrom[].secretRef.name` → e.g., `github-api-credentials`
- `volumes[].secret.secretName` → e.g., `okta-key`

These K8s secrets do NOT auto-migrate — they must be recreated as OneSecrets entries.

### 2.5e Store VAULT_CURRENT_CONFIG

Combine all findings into `VAULT_CURRENT_CONFIG`:

| Field | Value |
|-------|-------|
| `vault_active` | true/false — are Vault annotations present? |
| `vault_auth_type` | `kubernetes` (default) or `jwt` (if cross-cluster OneEKS access) |
| `vault_roles` | Map of env → role name |
| `vault_paths` | Map of env → auth path |
| `vault_secrets` | List of `{secretPath, envVars[]}` from environmentSecrets |
| `k8s_secrets` | List of K8s secret names referenced |
| `aws_sm_paths` | List of AWS SM secret paths (from application config) |
| `onesecrets_configured` | true/false — does cps/projects already have onesecrets? |
| `extra_policy_ro` | Existing cross-project policies (if any) |

This is consumed by Phase 4 (vault strategy decision) and Phase 5 (OneSecrets generation).

## 2.7 Dependency Discovery (Global DNS)

For each `*.eks.tkwy-*.io` reference found in step 2.2, classify it:

| Type | Pattern | Action |
|------|---------|--------|
| **Own domain** | `{APP_NAME}.{namespace}.*.eks.tkwy-*.io` | Phase 5 auto-replaces |
| **Infrastructure** (DB, RabbitMQ) | Known infra patterns | Map to `tk-<service>.{region}.{stage}.jet-internal.com` |
| **Upstream service** | Another app's `*.eks.tkwy-*.io` domain | Must be resolved via Global DNS (see 07-traffic-split.md) |

Store upstream dependencies as `DEPENDENCY_DOMAINS[]` — each entry with:
- `name`: service name extracted from domain
- `cloudops_domain`: the `*.eks.tkwy-*.io` URL found
- `env`: which environment (staging/production)
- `resolved`: whether a `*.jet-internal.com` record was found (populated in Phase 4)

## 2.8 Present Discovery Summary

Present all findings to the user before proceeding:

> **Discovery Summary: {APP_NAME}**
>
> | Finding | Details |
> |---------|---------|
> | Deployment structure | {what was found in 2.2a — e.g., `.deploy/k8s.yml`, `helmfile.d/`, etc.} |
> | CloudOps indicators | {list of indicators found} |
> | `*.eks.tkwy-*.io` refs | {count} references found |
> | Goldenpath gap | {N} files to create, {N} to convert, {N} to migrate |
> | Exposure type | {internal/external/both} |
> | Secrets | {count} AWS SM refs, {count} Vault refs |
