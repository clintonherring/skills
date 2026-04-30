# Phase 4: Configure Migration

**Goal**: Gather user decisions on deployment, networking, and exposure.

**Load**: [02-bulkheads-and-envs.md](02-bulkheads-and-envs.md), [05-dns-and-networking.md](05-dns-and-networking.md), [06-consul-bridge.md](06-consul-bridge.md)

## Q1: Bulkhead Selection

> "Sonic Runtime has multiple deployment regions called **bulkheads**. We recommend starting with **EU1 (Ireland)** — it's the closest equivalent to your current SRE-EKS setup and has access to your existing Vault secrets. Which bulkhead(s) do you want to migrate to?"
>
> - EU1 (Recommended)
> - EU1 + EU2 (Multi-region HA)
> - Custom

**If non-EU1 bulkheads are selected** (EU2, OC1, NA1 — either alone or in addition to EU1):

> "**Important — Legacy Resource Access**: Only **EU1** (`euw1-pdv-prd-5`) has broad access to legacy Takeaway resources. The other bulkheads you've selected (**{selected-non-eu1-bulkheads}**) have **severely limited** legacy resource access. This affects:"
>
> - **Vault secrets**: Legacy Vault paths (`secret/`, `database/creds/`, `rabbitmq/creds/`) are only fully available on EU1. Non-EU1 bulkheads require migrating to **OneSecrets** (KV v2).
> - **Legacy databases**: Dynamic database credential backends are mostly configured only on `euw1-pdv-prd-5`. Non-EU1 instances have at most 1 connection (`orderissues-glob`).
> - **RabbitMQ**: Dynamic RabbitMQ backends are only configured on `euw1-pdv-prd-5`. Non-EU1 instances have no RabbitMQ backend.
> - **Other legacy resources**: Any resource only reachable from the legacy environment where the access secrets are only available in the EU1 bulkhead will not be accessible from non-EU1 bulkheads.
>
> "If your workload depends on legacy resources, deploying to non-EU1 bulkheads may result in **runtime failures**. For guidance on legacy resource access from non-EU1 bulkheads, reach out to `#help-core-platform-services` or `#help-sonic` on Slack."
>
> "Would you like to proceed with the non-EU1 bulkheads now, or start with EU1 only and expand later?"

If the user chooses to proceed: note `NEEDS_ONESECRETS = true` for the non-EU1 environments and factor this into the helmfile values generation in Phase 5. Do NOT hard-block — the user may have already addressed legacy dependencies or may not have any.

## Q2: Environment Mapping Review

Use environment names fetched from the **goldenpath** repo (cloned in Phase 2) as the target.
Present the mapping populated with detected SRE-EKS env names:
QA Environment is needed in Sonic Runtime, if not detected, ensure Target (Sonic Runtime) has relevant `qa` environment in the bulkheads selected and inform the user that a QA environment will be created.

> "Here's how your environments will map. Please confirm or adjust:"
>
> | Current (SRE-EKS) | Target (Sonic Runtime) |
> | ----------------- | ---------------------- |
> | {detected-qa}     | {goldenpath-qa-env}    |
> | {detected-stg}    | {goldenpath-stg-env}   |
> | {detected-prd}    | {goldenpath-prd-env}   |

## Q3: Service Exposure Discovery (Automatic + Confirmation)

Instead of asking the user how the service is accessed, **discover it automatically** from the existing SRE-EKS configuration and DNS infrastructure, then confirm with the user.

**Load**: [10-dns-discovery.md](10-dns-discovery.md) — contains the full 4-step procedure (extract hostnames, trace DNS paths via Route53/domain-routing/Cloudflare, present findings table, confirm with user).

Follow the procedure in `10-dns-discovery.md` to:

1. Extract all hostnames from VirtualService/ingress/helmfile config
2. Trace DNS paths through `IFA/route53`, `IFA/domain-routing`, and Cloudflare repos (progressive discovery)
3. Present a DNS path analysis table to the user
4. Ask the user to confirm exposure type: **Internal only**, **External**, or **Both**

Store the result as `EXPOSURE_TYPE`. The subsequent questions branch based on this value.

**Key rule for SmartGateway**: SmartGateway is needed **only** when the service has external internet-facing endpoints (traffic routed through SmartGateway/Kong). Brand domains used for **internal** purposes (not proxied through Cloudflare/SmartGateway) do NOT need SmartGateway. Always trace the actual DNS path rather than assuming from the domain name alone. If unsure, ask the user to confirm the DNS path and whether it should be exposed to public internet.

## Q4a: Consul Backward Compatibility (if EXPOSURE_TYPE is internal, external-api, or both)

> "Do you want other services still running on SRE-EKS to be able to reach your service at its current `.service` address (e.g., `{service}.service`)? This keeps backward compatibility so dependent services don't need to update their config immediately."
>
> - **Yes** (Recommended if others depend on you)
> - **No**

Yes → generate Consul bridge config per `06-consul-bridge.md`

## Q4a-2: Resolve .service Dependencies

If `SERVICE_DEPS_INFRA` or `SERVICE_DEPS_APP` are non-empty (from Phase 2.3c), validate and confirm all mappings. See [05-dns-and-networking.md](05-dns-and-networking.md#migrating-from-consul-service-addresses) for mapping rules and validation procedure.

**Prerequisite**: `IFA/route53` should already be cloned from Q3 (`/tmp/route53`). If not, clone it now.

### Step 1: Validate Infrastructure Mappings

For each entry in `SERVICE_DEPS_INFRA`, validate the proposed GlobalDNS address exists in `IFA/route53` per the Route53 validation procedure in `05-dns-and-networking.md`. Mark each as **Validated** or **Not validated**.

### Step 1b: Confirm Schema Names

For entries where `needs_schema_confirmation` is true (see Phase 2.3c), ask the user to confirm the schema name before validating:

> "We detected `{original}` — the prefix `{schemaname}` may be a server-level name (e.g., `general` is the shared MySQL server). **Schema-specific DNS is recommended** for portability — if a schema needs to move to a different server, only the DNS record needs repointing.
>
> Is `{schemaname}` your actual database schema name, or should we use a different schema name?
> For example, if your schema is `bc-thuis`, the GlobalDNS would be `bc-thuis.tk-mysql.eu-west-1.production.jet-internal.com`."

If the user provides a different schema name, update the proposed mapping and re-validate against `IFA/route53`. If the schema-specific DNS record does not exist yet, advise the team to request it via `#help-core-platform-services`.

### Step 2: Present Findings

> "Your service uses `.service` addresses. Sonic Runtime does **NOT** support `.service` resolution — **all** must be replaced with GlobalDNS addresses."
>
> **Infrastructure Dependencies:**
>
> | Current (`.service`)    | Schema Name | Proposed GlobalDNS (production)                           | Validated? |
> | ----------------------- | ----------- | --------------------------------------------------------- | ---------- |
> | `general.mysql.service` | `bc-thuis`  | `bc-thuis.tk-mysql.eu-west-1.production.jet-internal.com` | Yes        |
>
> (Populated from `SERVICE_DEPS_INFRA` with confirmed schema names and real validation results)

For **not validated** mappings, ask the user to: provide the correct address, contact `#help-core-platform-services`, or defer (flagged as blocker — service cannot deploy with unresolved addresses).

### Step 3: Resolve Application Dependencies

Application `.service` addresses **must also be replaced** — they are not resolvable in Sonic Runtime.

> **Application Dependencies:**
>
> | Current (`.service`) | Action Needed                                                  |
> | -------------------- | -------------------------------------------------------------- |
> | `orderapi.service`   | Provide the GlobalDNS or brand domain address for this service |
>
> "For each application dependency, provide a reachable address:"
>
> - **Has GlobalDNS / brand domain** → Provide the address (e.g., `orderapi.eu-west-1.production.jet-internal.com`) — validate it in `IFA/route53`
> - **No known address** → This is a **blocker**. The target service must get a GlobalDNS record or be migrated first. Contact the owning team or `#help-core-platform-services`.

### Step 4: Store Confirmed Mappings

Store as `SERVICE_ADDR_MAP` — per-environment dictionary for Phase 5 Step 8:

```
SERVICE_ADDR_MAP = {
  "general.mysql.service": {
    "schemaname": "bc-thuis",
    "staging": "bc-thuis.tk-mysql.eu-west-1.staging.jet-internal.com",
    "production": "bc-thuis.tk-mysql.eu-west-1.production.jet-internal.com"
  },
  "general.mysql-ro.service": {
    "schemaname": "bc-thuis",
    "staging": "bc-thuis.tk-mysql-ro.eu-west-1.staging.jet-internal.com",
    "production": "bc-thuis.tk-mysql-ro.eu-west-1.production.jet-internal.com"
  },
  "orderapi.service": {
    "staging": "orderapi.eu-west-1.staging.jet-internal.com",
    "production": "orderapi.eu-west-1.production.jet-internal.com"
  }
}
```

The `schemaname` field records the confirmed schema name used in the GlobalDNS address (which may
differ from the original `.service` prefix if the user provided a schema-specific name). For
read-heavy services, consider also mapping a read-only variant
(`<schemaname>.tk-<resource>-ro.<region>.<env-type>.jet-internal.com`) to reduce load on the
primary writer.

````

Entries where the user deferred resolution: store as `"PENDING"` and flag as a **blocker** in Phase 5.5 review. There is no `KEEP_SERVICE` option — all `.service` references must be resolved.

## Q4b: Regional DNS Record (if EXPOSURE_TYPE is internal or both)

> "Your service will automatically get standard DNS records when deployed. For example, the E-record will be `{APP_NAME}.{project-id}.{env-component}.{region}.production.jet-internal.com` and the NG-record will be `{APP_NAME}.{project-id}.production.jet-internal.com`. Do you also need a **regional record** like `{APP_NAME}.eu-west-1.production.jet-internal.com` or a **global record** like `{APP_NAME}.production.jet-internal.com`? This is only needed if services outside your project reference you by a region-specific address or global address."
>
> - **No** (Most services don't need this)
> - **Yes** — ask for desired record format

Yes → generate `customRules` in `cps/helm-core` per `05-dns-and-networking.md`

## Q4c: SmartGateway & API Governance (if EXPOSURE_TYPE is external or both)

**Load**: [11-smartgateway.md](11-smartgateway.md) — contains SmartGateway environment mapping, API governance details, and config generation guidance.

SmartGateway is needed **only** when the service is external exposed => internet-facing endpoints (determined by DNS discovery in Q3).

> "Your service has external internet-facing endpoints that require **SmartGateway** (Kong Gateway) to route internet traffic. SmartGateway proxies requests to your service's **internal** E-record address."
>
> "All externally-exposed APIs also require an **OpenAPI specification** registered with the API Design Guild (using the BOATS format). Do you already have one?"
>
> - **Yes** — I already have a BOATS spec in the `api_specifications` repository
> - **No** — I need to create one
> - **Not sure**

If **No** or **Not sure**: inform the user this is a prerequisite and that a placeholder spec will be generated.

Store SmartGateway environment mapping from `11-smartgateway.md` based on bulkhead selection.

## Q4d: Brand Domain Details (if brand domains discovered in Q3)

Based on the DNS discovery, present the brand domains found:

> "I discovered the following brand domain(s) in your current configuration: **{discovered-domains}**. Are these correct? Are there any additional brand domains?"
> — (Free text, comma-separated for additions)

> "Based on the DNS path analysis, your brand domain traffic currently routes through: **{discovered-path}** (e.g., 'Cloudflare CDN → origin CNAME → SRE-EKS ingress'). I'll configure the migration to update this path to point to Sonic Runtime."

If Cloudflare proxy was detected in the DNS discovery: note that the migration will update the Cloudflare origin endpoint in the `IFA/domain-routing` repo and may need WAF rule adjustments.

Also ask about the routing path:

> "What URL path(s) does your service handle on this brand domain? For example: `/api/orders`, `/auth/*`"
> — (Free text)

## Q4e: Vault / Secrets Strategy

**Load**: [14-vault-secrets-migration.md](14-vault-secrets-migration.md)

Based on Vault discovery (Phase 2.3b) and bulkhead selection (Q1), present findings and
determine the migration path. Only ask for decisions that can't be automated.

**If no Vault usage detected:**

> "I didn't detect any Vault usage in your current SRE-EKS deployment. Do you need
> secrets management for this service in Sonic Runtime?"
>
> - **No** (Skip Vault setup)
> - **Yes** — Set up OneSecrets (KV v2)

**If EU1 only and legacy Vault secrets detected:**

> "Your service reads secrets from these Vault paths: **{detected_paths}**."
>
> "Since you're deploying to EU1, your existing secrets are already available on the
> OneSecret EU1 Vault instance — no secret migration needed. I'll add `extra_policy_ro` to your
> project config in `cps/projects` to grant read access to these legacy paths."
>
> "Optionally, you can migrate to **OneSecrets** (KV v2) for better tooling and
> multi-bulkhead readiness. Would you like to:"
>
> - **Keep legacy Vault** (Recommended — simplest path, add `extra_policy_ro` only)
> - **Migrate to OneSecrets** (Requires manually recreating secrets in your project KV v2 path like cu-order-reviews/\*)

**If non-EU1 bulkheads selected and legacy secrets detected:**

> "Your non-EU1 bulkheads (**{bulkheads}**) do NOT have legacy Vault secrets —
> those only exist on EU1 Vault instances (same Vault servers as SRE-EKS). For non-EU1
> environments, you must use OneSecrets (KV v2). Please manually (via vault-cli or vault UI) migrate your secrets to OneSecrets and reference them in your helmfile values for the non-EU1 environments."
>
> "For your EU1 environments, I'll add `extra_policy_ro` for legacy path access.
> For non-EU1, you'll need to create secrets in your project's OneSecrets KV v2 mount."

Store: `VAULT_STRATEGY` (legacy | onesecrets | both | none), `VAULT_PATHS[]`,
`NEEDS_EXTRA_POLICY_RO` (bool), `VAULT_ROLE` (= PROJECT_ID)

## Q5: Traffic Split Strategy

> "How would you like to handle the DNS cutover from SRE-EKS to Sonic Runtime?"
>
> - **Gradual traffic split** (Recommended — shift 0% → 10% → 50% → 100% using weighted DNS. Safest.)
> - **Direct cutover** (Switch immediately. Only for non-critical services.)

If EXPOSURE_TYPE is external and brand domain with Cloudflare detected in Q3 DNS discovery and gradual split chosen: note that traffic weights are managed in the `IFA/domain-routing` repo (not Route53) for brand domains.

## Q5b: Cross-Account AWS Access

Check if the analyzer detected AWS resource dependencies (DynamoDB, S3, SQS, SNS, etc.) during Phase 2. Also check the cloned source repo for AWS SDK usage, environment variables referencing AWS resources (table names, bucket names, queue URLs), or IAM role configurations.

If AWS resource dependencies are detected:

> "Your service accesses AWS resources (e.g., **{detected-resources}**). Since SRE-EKS and Sonic Runtime use **different AWS accounts**, you'll need a **Workload Role** (IRSA) to access these resources from Sonic Runtime. This requires a **bidirectional setup**:"
>
> 1. **Side 1 (Sonic Runtime)**: Define a workload role in `cps/projects/workloads/pdv/{PROJECT_ID}.yaml` with the required IAM permissions
> 2. **Side 2 (Legacy account)**: Update resource-based policies on the target resources (DynamoDB table policy, S3 bucket policy, SQS queue policy) to trust the new Sonic Runtime workload role
>
> "Do you already have a Workload Role set up in `cps/projects` for this service?"
>
> - **Yes** — I already have a workload role configured
> - **No** — I need to set one up
> - **Not sure**

If **No** or **Not sure**:

> "I'll generate a `cps/projects` workload definition as part of the migration PRs. You'll need your team's AWS account IDs for each environment — you can find them in [Backstage OneEKS Environments](https://backstage.eu-west-1.production.jet-internal.com/catalog/default/environment?filters%5Bkind%5D=environment&filters%5Btags%5D=oneeks&filters%5Buser%5D=all). The PR will need approval from the IFA team (`@support-ifa` in `#help-infra-foundations-aws`)."
>
> "For the legacy-side resource policies (Side 2), I'll provide the policy statements you need to apply, but you'll need to update them through your existing infrastructure-as-code (Terraform, CloudFormation, etc.)."

Store `NEEDS_WORKLOAD_ROLE = true` and add `cps/projects` as an additional PR repository in Phase 5.

> **Reference**: The `sonic-migration-analyzer` skill's `references/05-aws-access.md` contains the full Workload Role specification, cross-account setup patterns, ARN formats, and SDK compatibility requirements. Load it if the user needs detailed guidance.

If NO AWS resource dependencies detected: skip this question silently.

## Q6: Questions Before Generating Changes

> "Before I generate the migration changes, do you have any questions about the decisions made so far? I can look up documentation for any topic."

If the user asks a question, dynamically search Backstage TechDocs for the relevant topic:

```bash
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "$BACKSTAGE_BACKEND_URL/api/search/query?term={RELEVANT_SEARCH_TERM}&types%5B0%5D=techdocs" \
  | jq '.results[:3][] | {title: .document.title, url: "'"$BACKSTAGE_UI_URL"'\(.document.location)", text: .document.text[:500]}'
````

Present a summary of the relevant documentation and include the Backstage URL for further reading. Continue answering questions until the user says "proceed" or similar.
