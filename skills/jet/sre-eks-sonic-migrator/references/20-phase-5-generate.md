# Phase 5: Generate Changes

**Goal**: Generate all code changes using current patterns from authoritative sources. Existing configuration should not be removed or changed so that the service can continue running on SRE-EKS until the new configs are deployed and verified in Sonic Runtime.

**Load**: [03-goldenpath-structure.md](03-goldenpath-structure.md), [09-multi-repo-changes.md](09-multi-repo-changes.md), [08-traffic-split.md](08-traffic-split.md). **Also load the `sonic-pipeline` skill** if the service is eligible for Sonic Pipeline.

## 5.0 Fetch Current Patterns

Before generating code:

1. **Read goldenpath repo** (cloned in Phase 2) for current helmfile structure, workflow patterns, and helm values template
2. **Clone basic-application chart**: `gh repo clone github.je-labs.com/helm-charts/basic-application /tmp/basic-application`
   - Read `values.yaml` to understand the current config schema (deployment vs rollout, HPA vs KEDA ScaledObject, etc.)
   - Read `CHANGELOG.md` for breaking changes between known version and current
   - Inform user of implications: "The chart uses **Argo Rollouts** (not Deployments) and **KEDA ScaledObject** (not HPA). Your helm values will be generated accordingly."
3. **If Sonic Pipeline**: Load the **`sonic-pipeline`** skill. This provides the authoritative
   sonic.yml schema (apiVersion, metadata, environments, workloads), workload configuration
   reference (resources, artifacts, deployments), test types and runtime-specific configuration,
   and onboarding steps. Also read `references/04-cicd-eligibility.md` for migration-specific
   test detection and mapping guidance (how to discover existing tests in SRE-EKS repos and
   map them to Sonic Pipeline config).
4. **If GitHub Actions**: Read workflow files from goldenpath repo for current patterns and versions

Use templates from `assets/templates/` as starting points — replace `{{PLACEHOLDER}}` values
with actuals from Phases 1-4 and **update any schema patterns** based on the fetched chart `values.yaml`.

## 5.1 Source Repository

1. Create `helmfile.d/` structure following the goldenpath repo layout
2. Populate `state_values/defaults.yaml` from extracted config
3. Create per-env `state_values/{env}.yaml` with correct domains based on DNS decisions
4. Create `values/{service}.yaml.gotmpl` using the **basic-application chart's current `values.yaml` schema** as reference
5. **Vault sidecar annotations** (if `VAULT_STRATEGY != none`):
   Generate `podAnnotations` block in the helm values file based on `VAULT_STRATEGY`.
   - If `legacy`: Vault agent annotations with KV v1 templates (`.Data`), role = `PROJECT_ID`
   - If `onesecrets`: Annotations with KV v2 templates (`.Data.data`), role = `PROJECT_ID`
   - If `both`: Both sets for different secret paths (each with its own `agent-inject-template-*` name)
   - No `vault.hashicorp.com/service` annotation — sidecar uses local cluster Vault
     See [14-vault-secrets-migration.md](14-vault-secrets-migration.md) for annotation templates.
6. **`cps/projects` update** (if `NEEDS_EXTRA_POLICY_RO`):
   Update `projects/pdv/{PROJECT_ID}.yml` in the cloned `cps/projects` repo:
   - Add `onesecrets.extra_policy_ro` with read policies for each detected legacy secret path
   - If `onesecrets.enabled` is not already `true`, set it
   - This change will be a separate PR to `cps/projects` (Phase 6)
7. If Sonic Pipeline: create `.sonic/sonic.yml` using `assets/templates/sonic.yml.tmpl` as base.
   Use the **`sonic-pipeline`** skill as the authoritative reference for the sonic.yml schema,
   field values, and runtime-specific configuration:
   - Set `apiVersion` and `workloads.apiVersion` per the versions documented in `sonic-pipeline`
   - Populate `metadata` fields per `sonic-pipeline` guidance (metadataId=APP_NAME, project=PROJECT_ID, team, vaultRole, vaultSecretPath). Use `sonic-pipeline`'s metadata discovery commands (PlatformMetadata, Vault, project lookup) to find values.
     - `metadata.vaultRole`: Set to `PROJECT_ID` (Vault role in Sonic Runtime = project name)
     - `metadata.vaultSecretPath`: Based on `VAULT_STRATEGY` from Q4e:
       - legacy: `secret/{APP_NAME}` (or the specific detected legacy path)
       - onesecrets: `{PROJECT_ID}/data/{APP_NAME}`
       - none: omit or leave empty
   - Map environments from Phase 2 bulkhead/env decisions to cluster identifiers (format documented in `sonic-pipeline`)
   - Set `resources.{APP_NAME}` with detected deployment method (helmfile or argocd)
   - Set `artifacts.{APP_NAME}` with detected runtime, runtimeVersion, appType — refer to `sonic-pipeline` for supported runtimes and their runtime-specific reference files
   - Detect existing tests in source repo and map to `artifacts.tests` (build-time) and `deployment.tests` (deploy-time) — see `references/04-cicd-eligibility.md` for SRE-EKS test pattern detection and mapping logic, and `sonic-pipeline` runtime references for the target test configuration format

     If NOT Sonic Pipeline: create `.github/workflows/` from goldenpath patterns

8. **Replace `.service` references using `SERVICE_ADDR_MAP`** (from Phase 4 Q4a-2):

   For every entry in `SERVICE_ADDR_MAP`, replace the `.service` address with the confirmed GlobalDNS address. Replacements are **environment-aware** — place them in per-environment `state_values/{env}.yaml` files, not hardcoded in application code.

   Example: If the app reads `MYSQL_HOST` env var set to `general.mysql.service` and the confirmed
   schema name is `bc-thuis`, set it to `bc-thuis.tk-mysql.eu-west-1.staging.jet-internal.com`
   in staging and `bc-thuis.tk-mysql.eu-west-1.production.jet-internal.com` in production.
   If hardcoded in app config, replace with a templated value from state_values.

   For read-heavy services, if a read-only endpoint was confirmed (e.g., `MYSQL_HOST_RO`), set it
   to the `-ro` variant: `bc-thuis.tk-mysql-ro.eu-west-1.staging.jet-internal.com` in staging and
   `bc-thuis.tk-mysql-ro.eu-west-1.production.jet-internal.com` in production.

   > **Note**: The GlobalDNS address uses the **schema name** confirmed in Phase 4 Q4a-2 (stored in
   > `SERVICE_ADDR_MAP[].schemaname`), which may differ from the original `.service` prefix. Always
   > use the confirmed mapping — do not re-derive from the `.service` address.

   This applies to **both** infrastructure and application dependencies — `.service` is not resolvable in Sonic Runtime.

   **For `PENDING` entries** (user deferred resolution): keep the `.service` reference with a warning comment and flag as a **blocker** in Phase 5.5 review. The service cannot deploy with unresolved `.service` addresses.

9. If Consul bridge: add `igw-marathon` VirtualService entry (fetch format from Backstage)
10. Remove old SRE-EKS deploy configs

**VirtualService domains** (see `05-dns-and-networking.md` for exact formats):

- Always include **E-record**: `{APP_NAME}.{project-id}.{env-component}.{region}.{env-type}.jet-internal.com`
- Add **NG-record** (recommended): `{APP_NAME}.{project-id}.{env-type}.jet-internal.com`
- Add **R-record** only if Q4b=Yes: `{APP_NAME}.{region}.{env-type}.jet-internal.com`
- Add **G-record** only if Q4b=Yes and global record needed: `{APP_NAME}.{env-type}.jet-internal.com`
- If Consul bridge, add `igw-marathon` VirtualService entry with `.service` host
- If external/brand-domain, also add the brand domain hostname to VirtualService (brand domains hit the ingress directly via Cloudflare). External APIs via SmartGateway do NOT need additional hosts — SmartGateway proxies to the NG-record.
- Use `project-id` as-is — no prefix or suffix. Use `APP_NAME` from PlatformMetadata as the dns-prefix.

## 5.2 Route53 (per-environment DNS records)

Route53 records are needed in **two scenarios**:

1. **R-record or G-record creation**: If the service uses R-records or G-records, these DNS records must exist in **all environments** (QA, staging, production) — not just production. Users need to test the DNS path in QA/staging before going live.

2. **Gradual traffic split**: If the user chose gradual traffic split, weighted CNAME records are needed. These should also be created for staging (for validation) in addition to production.

**Per-environment DNS strategy**: The DNS strategy may differ by environment. For example:

- QA/Staging: GlobalDNS R-record via Route53
- Production: Brand domain via domain-routing repo

Handle each environment independently based on Phase 4 decisions.

For each environment that needs Route53 records:

- Fetch current terraform patterns from `IFA/route53` repo
- For `jet-internal.com` records: look in the private zone files (e.g., `*-private.yml`)
- If gradual traffic split for this environment: generate weighted CNAME records (SRE-EKS=100, Sonic Runtime=0)
- If R-record/G-record without traffic split: generate direct CNAME records pointing to the E-record

## 5.3 helm-core (if any DNS record beyond E-record and NG-record)

Only E-records and NG-records are auto-provisioned via the `igw-<project>` gateway wildcard. Any other hostname on the Istio ingress — R-records, brand domains — requires explicit `customRules` in `cps/helm-core`. Note: `jet-external.com` does NOT need customRules because external API traffic is proxied through SmartGateway to the internal NG-record.

Clone `cps/helm-core`, find the correct `istio-gateways.yaml.gotmpl` files, and generate `customRules` following the existing patterns in the repo.

**Regional record** (Q4b=Yes): Add `customRules` mapping the R-record host to `igw-{project}`.
**Global record** (Q4b=Yes): Add `customRules` mapping the G-record host to `igw-{project}`.

**Brand domain** (if brand domain discovered in Q3 and traffic hits ingress directly): Add `customRules` mapping the brand domain hostname (e.g., `api.takeaway.com`) to `igw-{project}`. Brand domain traffic arrives at the Istio ingress directly via Cloudflare with the brand domain as the host header. Example pattern from migration guide:

```yaml
customRules:
  - hosts:
      - "{APP_NAME}.takeaway.com"
    defaultGateway: igw-{project-id}
```

Must be done for each cluster/environment. Fetch the current file structure from the repo.

**Critical**: Every hostname in `customRules` must also appear in the VirtualService `hosts` list (the `domains` in state_values), and every DNS record pointing to this service must have a matching entry. See Section 5.8 (Consistency Validation) for the cross-check.

## 5.4 Consul (if backward compat)

Fetch current `oneeks_migrated_services` format from Backstage. Generate entries for staging + production.

## 5.5 Domain-Routing (if brand domain)

Clone `IFA/domain-routing` and explore its structure. Generate:

1. **Weighted endpoint entries** for traffic splitting (SRE-EKS=100, Sonic Runtime=0):

   ```yaml
   endpoints:
     sre-eks:
       type: CNAME
       value: { SRE_EKS_ENDPOINT }
       weight: 100
     oneeks:
       type: CNAME
       value: { SONIC_E_RECORD }
       weight: 0
   ```

2. **Cloudflare DNS record** (if Cloudflare is used — see Q4d): Update the origin endpoint in `vars/records/cloudflare/{domain}.yaml` to point to the Sonic Runtime endpoint. Use `cloudflare-dns-record.yaml.tmpl` as a starting point.

3. **WAF rules** (if applicable): Check `vars/domains/waf.yml` for existing rules referencing the service. Update or add allow rules using `waf-rules.yaml.tmpl` as a starting point.

## 5.6 SmartGateway Configuration (if EXPOSURE_TYPE is external or both)

**Load**: [11-smartgateway.md](11-smartgateway.md) — contains full config generation procedure, environment mapping, JSON schema patterns, and plugin requirements.

Follow the procedure in `11-smartgateway.md` to clone `external-api-services/smartgatewayconfiguration`, generate the config JSON using `smartgateway-config.json.hbs.tmpl`, and place it under `Data/Global/{service-name}.json.hbs`. Key requirements: service host must be the NG-record, port=443, protocol=https, include `rate-limiting` plugin at minimum.

> Inform user: "After the SmartGateway PR is merged, you can test via SmartGateway regional endpoints before going fully live. Request review in `#help-edge` on Slack."

## 5.7 API Specifications (if EXPOSURE_TYPE is external or both AND no BOATS spec)

If the user indicated in Q4c that they don't have a BOATS spec:

1. Clone `api_specifications` repo. Explore `src/paths/` for existing examples.
2. Generate a **placeholder OpenAPI v3 spec** based on the service's detected routes and endpoints.
3. Inform the user they must refine it and get approval from the API Design Guild (`#api-guild-design` on Slack) before going live externally.

If the user already has a BOATS spec: skip this step, but note that the existing spec may need updating if URLs or paths change during migration.

## 5.7b Workload Role (if NEEDS_WORKLOAD_ROLE)

If `NEEDS_WORKLOAD_ROLE` was set in Phase 4 Q5b, generate the workload role definition in `cps/projects`:

1. Clone `cps/projects` if not already cloned (it was cloned in Phase 1 for onboarding validation):

   ```bash
   # Already cloned to /tmp/cps-projects in Phase 1 step 6
   ```

2. Create or update `workloads/pdv/{PROJECT_ID}.yaml` with the detected AWS permissions:
   - Extract IAM actions from the service's existing IAM role/policy (if discoverable from SRE-EKS config)
   - Extract resource ARNs (DynamoDB tables, S3 buckets, SQS queues) from application config and environment variables
   - For each target environment, populate `accounts.{env}` with the correct `variables` (table names, account IDs, regions)
   - Use the template pattern from `sonic-migration-analyzer/references/05-aws-access.md`

3. Add `serviceAccount` annotations to the helmfile values (`helmfile.d/values/{APP_NAME}.yaml.gotmpl`):

   ```yaml
   serviceAccount:
     annotations:
       eks.amazonaws.com/role-arn: "{{ .Values.workloadRoleARN }}"
   ```

4. Add `workloadRoleARN` to each environment's state_values file with the ARN pattern:

   ```
   arn:aws:iam::{AWS_ACCOUNT_ID}:role/jas/wl/terraform_managed/jas-wl-role-{PROJECT_ID}-{APP_NAME}
   ```

5. Generate a summary of **Side 2 (legacy account) changes** the user needs to apply manually:
   > "You'll also need to update resource-based policies in your legacy AWS account to trust the new Sonic Runtime workload role. Here are the policy statements needed:"
   >
   > (Generate specific policy JSON for each detected resource — DynamoDB table policy, S3 bucket policy, etc.)
   >
   > "Apply these through your existing infrastructure-as-code. The IFA team (`@support-ifa` in `#help-infra-foundations-aws`) can help if needed."

## 5.7c Vault Configuration Validation

If `VAULT_STRATEGY != none`, validate Vault configuration consistency:

1. `vaultRole` in sonic.yml = `PROJECT_ID` = Kubernetes auth role name in `cps/projects`
2. Secret paths in helm value annotations match paths in `extra_policy_ro` (if used)
3. KV version is consistent: `.Data` for KV v1 (`secret/`) vs `.Data.data` for KV v2 (`<project>/data/`)
4. If `extra_policy_ro` is used, every legacy path the app reads has a corresponding policy entry
5. For non-EU1 environments: confirm NO legacy `secret/` paths are referenced — must be OneSecrets only

See [14-vault-secrets-migration.md](14-vault-secrets-migration.md) for the full annotation templates and policy format.

## 5.8 DNS ↔ helm-core ↔ VirtualService Consistency Validation

**Load**: [12-consistency-validation.md](12-consistency-validation.md) — contains the full validation procedure, the 3-layer routing chain explanation, per-environment validation table format, and mismatch resolution guidance.

Follow the procedure in `12-consistency-validation.md` to build a per-environment validation table verifying that every hostname is consistent across DNS (Route53/domain-routing), helm-core (customRules), and VirtualService (domains). Fix any mismatches before proceeding to Phase 5.5.
