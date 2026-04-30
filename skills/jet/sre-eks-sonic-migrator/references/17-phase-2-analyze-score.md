# Phase 2: Analyze & Score

**Goal**: Understand the current SRE-EKS deployment, assess complexity, and fetch current platform info.

**Dependency**: This phase delegates repository analysis, platform detection, scoring, blocker
identification, and CI/CD eligibility to the **`sonic-migration-analyzer`** skill. That skill
handles all generic analysis logic — do NOT duplicate it here.

**Load**: [04-cicd-eligibility.md](04-cicd-eligibility.md) (for Sonic Pipeline configuration details used later in Phase 5)

## 2.1 Fetch Current Platform Info

Before running the analyzer, fetch current information in parallel:

1. **Chart version**: `gh api --hostname github.je-labs.com /repos/helm-charts/basic-application/releases/latest | jq '.tag_name'`
2. **Clone goldenpath**: `gh repo clone github.je-labs.com/justeattakeaway-com/goldenpath /tmp/goldenpath` — for current environment names and patterns
3. **App tier from PlatformMetadata** (reuse `APP_NAME` validated in Phase 1):

   ```bash
   gh api --hostname github.je-labs.com /repos/metadata/PlatformMetadata/contents/Data/global_features/{APP_NAME}.json | jq -r '.content' | base64 -d | jq '.tier'
   ```

   Use the tier value (`bronze`, `silver`, `gold`) in the `app.tier` helm value.

Present the chart version to the user:

> "The current basic-application chart version is **{version}**."

If there are significant breaking changes (check `CHANGELOG.md` in the chart repo), inform the user of implications (e.g., Argo Rollouts replacing Deployments, KEDA replacing HPA).

## 2.2 Run the Sonic Migration Analyzer

Invoke the **`sonic-migration-analyzer`** skill against the cloned repository from Phase 1. The
analyzer will:

- Discover and read all relevant files in the repo (deployment configs, application files, dependencies)
- Detect the current platform (confirm SRE-EKS) with confidence level
- Calculate the complexity score (0-100)
- Identify blockers (JustSayingStack, monorepo, etc.) and warnings
- Determine CI/CD approach (Sonic Pipeline eligibility vs GitHub Actions)
- Detect runtime language, messaging patterns, `.service` dependencies, Vault paths
- Generate a full analysis report saved to `/tmp/`

If the analyzer reports **medium or low confidence** on platform detection, ask the user to
confirm that the service runs on SRE-EKS before proceeding.

## 2.3 Extract Service Configuration

From the analyzer's findings and the deployment config it discovered, extract the details needed
for code generation in Phase 5: port, health check path, replicas, resources, env vars, `.service`
dependencies, Vault paths, messaging config.

## 2.3a Legacy Domain Detection

Scan the cloned source repository for references to legacy domains that are **not supported** in Sonic Runtime:

- `*.tkwy.cloud` (e.g., `servicename.int.staging.tkwy.cloud`)
- `internal.takeaway.local`

Search config files, environment variables, helm values, and application code:

```bash
grep -rn "tkwy\.cloud\|internal\.takeaway\.local" /tmp/{repo} --include="*.yaml" --include="*.yml" --include="*.json" --include="*.properties" --include="*.env" --include="*.cs" --include="*.go" --include="*.java" --include="*.py" --include="*.js" --include="*.ts" --include="*.xml" --include="*.config" --include="*.tf"
```

If matches are found, add a **warning** to the migration summary:

> "**Warning — Legacy domains detected**: Your service references `{matched-domains}` which are not supported in Sonic Runtime. These must be migrated to GlobalDNS (`jet-internal.com` / `jet-external.com`) before or during the migration. See Phase 3 for resolution steps."

Store matched files and references as `LEGACY_DOMAIN_REFS` for use in Phase 3.

## 2.3b Vault Discovery

Detect current Vault usage from the source repo and infrastructure:

1. **In-repo detection**: Search for `vault.hashicorp.com` annotations in helm values and
   deployment manifests, Vault secret paths (`secret/`, `database/creds/`) in app config,
   and `hashicorp-vault-action` usage in GitHub Actions workflows
2. **cps/vault lookup**: Clone `cps/vault` and check `vars/apps/{env}/{APP_NAME}.yml` for
   each SRE-EKS environment (dev, staging, production) — extracts `kubernetes_roles`, policy
   paths, `database_roles_dynamic`, `approle` config
3. **cps/projects lookup**: Check if project already has `onesecrets` config in
   `projects/pdv/{PROJECT_ID}.yml` (may already have `extra_policy_ro`, `external_clusters`)

Store all findings as `VAULT_CURRENT_CONFIG` for use in Phase 4 Q4e. Include: detected secret
paths, KV version (v1/v2), current Vault role name, existing `extra_policy_ro` entries.

## 2.3c `.service` Dependency Classification

Classify all `.service` references detected by the analyzer into **infrastructure** and **application** dependencies. This drives mapping in Phase 4 Q4a-2 and replacement in Phase 5 Step 8.

### Detection

Scan the cloned source repository for all `.service` address references. Also check environment variables in helm values and deployment manifests.

### Classification

**Infrastructure** — `<schemaname>.<resource>.service` or `<resource>.service` where `<resource>` is a known type: `mysql`, `mysql-ro`, `postgres`, `cassandra`, `rabbitmq`, `redis`, `memcached`, `maxscale`, `proxysql`, `elasticsearch`, `smtp`. Also `tk-<resource>.service` or `<schemaname>-<resource>.service` variants. The `<schemaname>` prefix is typically a database schema name or logical resource identifier (e.g., `general`, `thuis`).

**Application** — everything else (e.g., `orderapi.service`, `paymentgateway.service`).

### Derive Proposed Mappings

For infrastructure deps, derive GlobalDNS equivalents using the mapping rules in [05-dns-and-networking.md](05-dns-and-networking.md#infrastructure-mapping-rules).

> **Important**: The prefix in the `.service` address (e.g., `general`, `thuis`) may
> be a server-level name rather than the actual database schema name. When deriving proposed
> GlobalDNS, note that schema-specific DNS is recommended for portability. Flag for confirmation
> with the user in Phase 4 Q4a-2 — the user should verify whether the prefix is a schema name
> or a server name, and provide the correct schema name if they differ.

### Store Results

- `SERVICE_DEPS_INFRA[]` — Infrastructure refs with proposed GlobalDNS per environment:
  ```
  { original: "general.mysql.service", schemaname: "general", proposed_production: "general.tk-mysql.eu-west-1.production.jet-internal.com", proposed_staging: "general.tk-mysql.eu-west-1.staging.jet-internal.com", type: "mysql", needs_schema_confirmation: true }
  ```
  Set `needs_schema_confirmation: true` when the prefix might be a server-level name rather than
  a schema name (e.g., `general`, `thuis` are common server-level names).
- `SERVICE_DEPS_APP[]` — Application refs:
  ```
  { original: "orderapi.service", type: "application" }
  ```

## 2.4 Present Migration-Specific Summary

Combine the analyzer's output with the platform info fetched in 2.1 to present the
migration-specific summary:

> **Migration Analysis: {service-name}**
> | Field | Value |
> |-------|-------|
> | Platform | SRE-EKS (from analyzer) |
> | Runtime | {language} (from analyzer) |
> | Complexity | {score}/100 ({band}) (from analyzer) |
> | Sonic Pipeline | {Eligible / Not eligible} (from analyzer) |
> | Chart Version | {fetched version} (from 2.1) |
> | App Tier | {tier} (from PlatformMetadata) |
>
> **Blockers**: {list from analyzer, or "None"}
> **Warnings**: {list from analyzer, or "None"}
> **Dependencies**: {N} .service refs ({N} infrastructure, {N} application), {N} messaging resources (from analyzer)
>
> **Infrastructure .service Dependencies** (proposed GlobalDNS mappings):
>
> | Current (.service) | Proposed GlobalDNS (production) | Type       |
> | ------------------ | ------------------------------- | ---------- |
> | {infra-dep-1}      | {proposed-mapping-1}            | {resource} |
> | {infra-dep-2}      | {proposed-mapping-2}            | {resource} |
>
> **Application .service Dependencies**: {list or "None"}
>
> Proposed mappings will be validated against IFA/route53 in Phase 4 Q4a-2.
