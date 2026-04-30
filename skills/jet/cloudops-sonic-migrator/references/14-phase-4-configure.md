# Phase 4: Configure Migration

**Goal**: Gather user decisions on environment mapping, DNS exposure, vault/secrets strategy,
and traffic split approach. Present the full migration plan for confirmation.

**Load**: [02-environment-mapping.md](02-environment-mapping.md), [05-dns-and-networking.md](05-dns-and-networking.md) (discovery procedure),
[05b-dns-reference.md](05b-dns-reference.md) (record types, VirtualService hosts, customRules, decision tree),
[06-vault-secrets-migration.md](06-vault-secrets-migration.md), [07-traffic-split.md](07-traffic-split.md),
[21-smartgateway.md](21-smartgateway.md) (if `jet-external.com` endpoints detected)

## Q1: Bulkhead Selection

> "Sonic Runtime has multiple deployment regions called **bulkheads**. We recommend starting with **EU1 (Ireland)** — it's the closest equivalent to your current CloudOps-EKS setup. Which bulkhead(s) do you want to migrate to?"
>
> - EU1 (Recommended)
> - EU1 + EU2 (Multi-region HA)
> - Custom

**If non-EU1 bulkheads are selected** (EU2, OC1, NA1 — either alone or in addition to EU1):

> "**Important**: Each bulkhead has its own **separate Vault instance**. The bulkheads you've selected (**{selected-non-eu1-bulkheads}**) require creating your secrets in **OneSecrets** independently in each bulkhead's Vault. This means:"
>
> - Secrets must be created in OneSecrets for **each bulkhead** independently (they don't sync)
> - Your helmfile values per environment will reference the local Vault — the annotations are the same, but the secret data must exist in each Vault
> - See the [OneSecrets documentation](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/oneeks/tasks/use-onesecrets/) for the setup process
>
> "Would you like to proceed with the non-EU1 bulkheads now (requires creating secrets in each Vault), or start with EU1 only and expand later?"

If the user chooses to proceed: note `NEEDS_ONESECRETS_MULTI_BULKHEAD = true` and factor this into the helmfile values generation in Phase 5

## Q2: Environment Mapping Review

**Fetch environment names from Backstage**, not from hardcoded values. Query the Backstage
search API for `"Sonic Runtime Environments"` to get the current environment list with AWS
account IDs. See `02-environment-mapping.md` → "All Sonic Runtime Environments" for the
full reference table.

For each selected bulkhead, look up the QA/STG/PRD environment name from the Backstage data
and present the mapping:

> "Here's how your environments will map. Please confirm or adjust:"
>
> | Current (CloudOps) | Target (Sonic Runtime) | Bulkhead | AWS Account |
> | ------------------- | ---------------------- | -------- | ----------- |
> | eks-cluster-dev | {fetched from Backstage} | EU1 | {fetched} |
> | eks-cluster-staging-2 | {fetched from Backstage} | EU1 | {fetched} |
> | eks-cluster-prod | {fetched from Backstage} | EU1 | {fetched} |

If APAC (`eks-cluster-prod-ap`) detected and OC1 selected, add the OC1 row.

If additional bulkheads selected (EU2, NA1), add corresponding rows from the Backstage
environment data. **Do NOT guess or hardcode** — always fetch and verify.

**QA is mandatory**: Always include the QA environment row in the mapping, even if the
CloudOps service has no dev/QA deployment today. Show "(none — new)" in the Current column
when no CloudOps QA equivalent exists. Do NOT ask the user whether to skip QA — it is
required for Sonic Runtime.

Based on DNS discovery from Phase 2, identify the CloudOps ingress endpoint the service
currently uses — this is the `*.eks.tkwy-*.io` hostname extracted from the K8s ingress or
helmfile config (e.g., `default-internal.ing.p.eks.tkwy-prod.io`,
`foodtools-public.ing.p.eks.tkwy-prod.io`). Present it to the user so they can confirm
the desired exposure for Sonic Runtime.

> "Based on my analysis, your CloudOps ingress points to **{detected_ingress_endpoint}**
> and your service appears to be **{EXPOSURE_TYPE}**. How should it be exposed in Sonic Runtime?"
>
> - **Internal only** — only accessed by other services within the cluster
> - **External** — internet-facing API
> - **Both** — internal + external endpoints

Store as confirmed `EXPOSURE_TYPE`.

## Q3b: Regional/Global DNS Record (if EXPOSURE_TYPE is internal or both)

Check if any existing `*.jet-internal.com` records were discovered in Phase 2 DNS discovery
(e.g., `{APP_NAME}.production.jet-internal.com`, `{APP_NAME}.eu-west-1.production.jet-internal.com`).

**If existing R-record (regional) or G-record (global) found:**

> "Your service has an existing DNS record: **{discovered_record}**. In Sonic Runtime,
> E-records are created automatically. You have these options:"
>
> - **Keep R-record** — preserves existing integrations (requires Route53 + helm-core customRules)
> - **Use NG-record instead** — shorter, portable address (`{APP_NAME}.{PROJECT_ID}.{stage}.jet-internal.com`). Requires Route53 CNAME but no customRules
> - **E-record only** — no additional DNS records
>
> "Which environments need this record?"
>
> - **All** (QA, staging, production)
> - **Production only**
> - **Staging + production**

If R-record → store `NEEDS_CUSTOM_RULES = true`, `CUSTOM_DNS_RECORDS[]`, and `DNS_ENVS[]`.
If NG-record → store `NEEDS_NG_RECORD = true` and `DNS_ENVS[]`.
Note: R-record and NG-record are typically not both needed — if using R-record, skip NG-record.

**If no existing regional/global records found:**

> "Your service will automatically get an E-record when deployed:"
> - E-record: `{APP_NAME}.{PROJECT_ID}.{env-component}.{region}.{stage}.jet-internal.com`
>
> "Do you also need an **NG-record** (`{APP_NAME}.{PROJECT_ID}.{stage}.jet-internal.com`)
> or a **regional record** (`{APP_NAME}.{region}.{stage}.jet-internal.com`)?
> This is only needed if services outside your project reference you by address."
>
> - **No** (Most services don't need this)
> - **Yes** — ask for desired record format and which environments

Yes → generate Route53 CNAMEs (and `customRules` if R-record) per `05b-dns-reference.md`.

## Q4: SmartGateway & API Governance (if `jet-external.com` endpoints detected in DNS discovery)

**Load**: [21-smartgateway.md](21-smartgateway.md) — contains SmartGateway config repo, JSON
schema, environment mapping, plugin requirements, and API governance details.

SmartGateway is needed **only** when DNS path discovery (Q3) confirmed `*.jet-external.com`
endpoints — i.e., traffic from the public internet routed through SmartGateway (Kong) to the
service.

**SmartGateway is NOT needed for brand domains** (`*.takeaway.com`, `*.lieferando.de`, etc.)
that route through Cloudflare directly to the Istio ingress gateway. Brand domains are handled
separately in Q4b below.

> "Your service has `jet-external.com` endpoints that route through **SmartGateway** (Kong
> Gateway). SmartGateway proxies internet traffic to your service's internal NG-record
> address."
>
> "All externally-exposed APIs also require an **OpenAPI specification** registered with
> the API Design Guild (using the BOATS format). Do you already have one?"
>
> - **Yes** — I already have a BOATS spec in the `api_specifications` repository
> - **No** — I need to create one
> - **Not sure**

If **No** or **Not sure**: inform the user this is a prerequisite and that a placeholder
spec will be generated. Add `api_specifications` to the PR repo list.

Store SmartGateway environment mapping from `21-smartgateway.md` based on bulkhead selection.

**If no `jet-external.com` endpoints detected**: Skip Q4 entirely. Brand domains are handled
in Q4b.

## Q4b: Brand Domain Details (if brand domains discovered in Phase 2 DNS discovery)

Brand domains are non-`jet-internal.com` external domains like `*.takeaway.com`,
`*.lieferando.de`, `*.thuisbezorgd.nl`, etc.

**If brand domains were discovered:**

> "I discovered the following brand domain(s) in your current configuration:
> **{discovered-domains}**. Are these correct? Are there any additional brand domains?"
> — (Free text, comma-separated for additions)

> "Based on the DNS path analysis, your brand domain traffic currently routes through:
> **{discovered-path}** (e.g., 'Cloudflare CDN → origin CNAME → CloudOps-EKS ingress').
> I'll configure the migration to update this path to point to Sonic Runtime."

If Cloudflare proxy was detected in the DNS discovery: note that the migration will update
the Cloudflare origin endpoint in the `IFA/domain-routing` repo and may need WAF rule
adjustments.

Also ask about the routing path:

> "What URL path(s) does your service handle on this brand domain? For example:
> `/api/orders`, `/auth/*`, or `/*` (all paths)"
> — (Free text)

Store `BRAND_DOMAINS[]` with `{ domain, paths, cloudflare_proxied }` for Phase 5.

**If no brand domains discovered:** Skip silently.

## Q5: Vault / Secrets Strategy

Based on secrets discovery from Phase 2.5 and bulkhead selection from Q1.

**Present the `SECRETS_INVENTORY` classification** with `day1_status` (see
`06-vault-secrets-migration.md` → "Day-1 Secret Continuity by Source Type").

**If no secrets detected:**

> "I didn't detect any secrets usage. Do you need secrets management in Sonic Runtime?"
> - **No** (Skip)
> - **Yes** — Set up OneSecrets (KV v2)

**If secrets detected, present the classified inventory:**

> "Here's how your secrets will work on Sonic from day 1:"
>
> | Secret | Source | Day-1 Status | What I'll Generate | What You Do |
> |--------|--------|-------------|-------------------|-------------|
> | {name} | {source} | ✅ `ready` / 🔄 `migrate-later` / ❌ `blocked` | {annotation/policy/workload-role} | {action or "Nothing"} |

**If any secrets have `day1_status = blocked` (K8s Secrets or Vault-sidecar-only AWS SM):**

> "❌ These secrets must exist in **OneSecrets** before your first Sonic deploy. I'll generate
> the Vault sidecar annotations (replacing `secretRef`/volume mounts with Vault injection),
> but you need to create the actual values in Vault UI at `{PROJECT_ID}/data/{secret-name}`."
>
> "For K8s Secrets: copy the current values from `kubectl get secret -n {OLD_NS} {name} -o jsonpath='{.data}'`
> and create them in the Vault UI."

**If any secrets come from AWS Secrets Manager (via SDK):**

> "⚠️ Your app reads secrets from **AWS Secrets Manager** — these must be migrated to
> **OneSecrets** (Vault KV v2) before your first Sonic deploy. I'll generate the
> OneSecrets annotations, but you need to create the actual values in Vault UI."
>
> See: [Migrating Secrets guide](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/oneeks/tasks/manage-secrets/migrating-secrets/)

**If any secrets have `day1_status = blocked`:**

> "❌ These secrets are read via Vault sidecar annotations but don't exist in OneSecrets yet.
> **Pods will fail to start** (`Init:CrashLoopBackOff`) until you create the secret values
> in Vault UI. I'll generate the annotations and policies — you need to create the actual
> values before your first Sonic deploy."

**Pre-migration tip** (show if any Vault secrets detected):

> You can validate OneSecrets access while still on CloudOps by using the `auth/{legacy_env}`
> Vault auth path (e.g., `auth/eks-cluster-prod`). See:
> [Reading OneSecrets from CloudOps](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/oneeks/tasks/manage-secrets/read-secrets-from-oneeks-vault-in-cloudops/)

**If existing OneSecrets/Vault annotations detected (KV v2 paths like `{project}/data/...`):**

> "Your service already reads from **OneSecrets** (Vault KV v2): **{detected_paths}**."
>
> "These secrets are already in OneSecrets and will continue working on Sonic Runtime — no
> migration needed for these. After migration, the Vault auth path will change from
> `auth/{legacy_env}` to the standard Kubernetes auth, but the secret paths stay the same."

**If BOTH AWS Secrets Manager AND existing Vault detected (mixed):**

> "Your service uses a **mix** of secrets backends:"
> - **OneSecrets/Vault** (already migrated): **{vault_paths}** — these continue working as-is
> - **AWS Secrets Manager** (must migrate): **{sm_paths}** — these must be recreated in OneSecrets
>
> "I'll generate the Vault sidecar annotations for all secrets, combining the existing
> OneSecrets paths with new entries for the AWS SM secrets you'll create."

**If multiple bulkheads selected:**

> "Since you're deploying to multiple bulkheads (**{bulkheads}**), remember that each bulkhead
> has its own Vault instance. Secrets must be created in each bulkhead's OneSecrets independently."

Store: `VAULT_STRATEGY` (none | onesecrets | mixed), `VAULT_PATHS[]`, `SM_PATHS_TO_MIGRATE[]`

## Q6: Traffic Split Strategy

> "How would you like to handle the DNS cutover from CloudOps to Sonic Runtime?"
>
> - **Gradual traffic split** (Recommended — shift 0% → 1% → 10% → 50% → 100% using weighted DNS)
> - **Direct cutover** (Switch immediately. Only for non-critical services.)

If gradual, per-environment DNS weighted records will be generated.
See `07-traffic-split.md` for Route53 record format and file locations.

> **Traffic split is always DNS-level, but the repo depends on the domain type:**
>
> | Domain type | Repo | Mechanism |
> |-------------|------|-----------|
> | `*.jet-internal.com` / `*.jet-external.com` | `IFA/route53` | Route53 weighted CNAME records |
> | Brand domains | `IFA/route53` or `IFA/domain-routing` | Weighted records in whichever repo manages the parent domain |

**If brand domains were discovered**, recommend keeping the brand domain hostname and doing
traffic split directly on it. Confirm with the user:

> "Your brand domain **{domain}** — I recommend keeping this hostname and setting up traffic
> split directly on it. This means clients don't need to change anything. I'll include it
> in VirtualService hosts, create helm-core customRules, and add weighted records in
> `{repo}` for gradual traffic split. Migrating to GlobalDNS or SmartGateway can be done
> as a follow-up phase. Does this work for you?"
>
> Later references:
> - [Expose Service Internally](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/oneeks/tasks/networking/expose-service-internally/)
> - [Expose Service Externally](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/oneeks/tasks/networking/expose-service-externally/)

Only add NG-records if the service actually needs a `jet-internal.com` address.

**Do NOT autonomously decide to skip traffic split** or choose an alternative approach
(e.g., Istio path-based routing). Always present the situation to the user and wait for
their input before proceeding. Traffic split is a critical part of the migration — a missing
DNS record doesn't mean traffic split isn't needed, it means you need more information.

**Confirm the traffic split plan** before proceeding. Present a summary of what will be
generated and in which repos:

> "Here's the traffic split plan for **{APP_NAME}**:"
>
> | Domain | DNS Provider | Repo | Action |
> |--------|-------------|------|--------|
> | `{R-record or G-record}` | Route53 | `IFA/route53` | Add weighted CNAME (CloudOps=100, Sonic=0) |
> | `{brand-domain}` | Cloudflare or Route53 | `IFA/domain-routing` or `IFA/route53` | Add weighted record (CloudOps=100, Sonic=0) |
>
> "Does this look correct?"

Store confirmed plan as `TRAFFIC_SPLIT_PLAN[]` for Phase 5.

## Q7: AWS Resource Access

Check if the service uses AWS resources (DynamoDB, S3, SQS, SNS, RDS, etc.) detected in Phase 2.
Also check the cloned source repo for AWS SDK usage, environment variables referencing AWS
resources (table names, bucket names, queue URLs), or IAM role configurations (IRSA annotations).

**If AWS resource dependencies detected:**

A Workload Role in `cps/projects` is **always** needed — even for EU1 (same AWS account),
because Sonic Runtime uses Workload Roles instead of IRSA for pod-level IAM identity.

**Exclude SecretsManager from the Workload Role**: If the service's only AWS access is
`secretsmanager:GetSecretValue` (reading secrets from AWS Secrets Manager), do NOT create
a Workload Role for it. Those secrets are being migrated to OneSecrets (Vault KV v2) as
part of this migration — the app will read them from the Vault sidecar instead. Only create
a Workload Role for AWS resources the app will **continue accessing directly** on Sonic
(e.g., DynamoDB, S3, SQS, SNS, RDS, Kinesis, etc.).

> "Your service accesses AWS resources: **{detected_resources}**."
>
> "On Sonic Runtime, AWS access uses **Workload Roles** (defined in `cps/projects`) instead
> of IRSA. I'll generate the Workload Role definition as part of the migration PRs."
>
> "Do you already have a Workload Role set up in `cps/projects` for this service?"
> - **Yes** — already configured
> - **No** — I need to set one up
> - **Not sure**

If **No** or **Not sure**:

> "I'll generate a `cps/projects` workload definition as part of the migration PRs. You'll
> need your team's AWS account IDs for each environment — you can find them in
> [Backstage OneEKS Environments](https://backstage.eu-west-1.production.jet-internal.com/catalog/default/environment?filters%5Bkind%5D=environment&filters%5Btags%5D=oneeks&filters%5Buser%5D=all).
> The PR will need approval from the IFA team (`@support-ifa` in `#help-infra-foundations-aws`)."

Store `NEEDS_WORKLOAD_ROLE = true`.

**If non-EU1 bulkheads selected AND AWS resources detected:**

Additionally inform about cross-account requirements:

> "Your non-EU1 bulkheads (**{bulkheads}**) use **different AWS accounts** than CloudOps.
> Accessing your existing AWS resources from those bulkheads requires **cross-account trust**.
> This is a **bidirectional setup**:"
>
> 1. **Side 1 (Sonic Runtime)**: Workload Role in `cps/projects` with IAM permissions (generated)
> 2. **Side 2 (Legacy account)**: Update resource-based policies to trust the new role (manual)
>
> "For the legacy-side resource policies (Side 2), I'll provide the policy statements you
> need to apply, but you'll need to update them through your existing infrastructure-as-code
> (Terraform, CloudFormation, etc.)."

Store `NEEDS_CROSS_ACCOUNT = true`.

> **Note**: EU1 shares the same AWS account as CloudOps — no cross-account trust needed for
> EU1 resources. But the Workload Role definition in `cps/projects` is still required for EU1.

**If no AWS resources detected:** Skip silently.

## Q8: Upstream Dependency Resolution (Global DNS)

**If `DEPENDENCY_DOMAINS[]` is not empty** (upstream `*.eks.tkwy-*.io` refs found in Phase 2.6):

For each upstream dependency, **actively resolve** it following the procedure in
`07-traffic-split.md` → "Active Resolution Procedure":

1. Clone `IFA/route53` and search for the dependency's `*.jet-internal.com` record
2. Search Backstage for the dependency service
3. If accessible, check the dependency's VirtualService for `*.jet-internal.com` hosts

Present resolution results:

> "I found **{N}** upstream dependencies on CloudOps-only domains. Here are the results:"
>
> | Dependency | CloudOps Domain | Global DNS Record | Status |
> |------------|----------------|-------------------|--------|
> | {service} | `{cloudops_url}` | `{jet-internal_url}` | ✅ Resolved |
> | {service} | `{cloudops_url}` | — | ❌ Not found |
>
> For resolved dependencies: "I'll use the Global DNS address in the generated config."
> For unresolved: "This dependency is not yet available via Global DNS. The dependency team
> must expose it before full cutover. I'll add a `# TODO: BLOCKER` comment."

Store each resolution result for Phase 5 config generation.

**If no upstream dependencies detected:** Skip silently.

## Q9: Questions Before Generating

> "Before I generate the migration changes, do you have any questions about the decisions
> made so far? I can look up documentation for any topic."

Search Backstage TechDocs for relevant topics if the user asks. Continue until the user
says "proceed" or similar.

## Present Migration Plan

Show the full plan for confirmation:

> **Migration Plan: {APP_NAME}**
>
> | # | Repository | Changes | Required? |
> |---|------------|---------|-----------|
> | 1 | `{org}/{repo}` | Goldenpath restructure (helmfile.d/, sonic.yml or GHA) | Yes |
> | 2 | `IFA/route53` | DNS weighted records (all envs) | Yes |
> | 3 | `cps/helm-core` | customRules for R-records/G-records | If needed |
> | 4 | `IFA/domain-routing` or `IFA/route53` | Brand domain traffic split | If brand domain (add subdomain to parent domain's repo) |
> | 5 | `cps/projects` | Workload Role / extra_policy_ro | If AWS/Vault |
> | 6 | SmartGateway config | External API routing | If `jet-external.com` endpoints |
> | 7 | `api_specifications` | OpenAPI spec (BOATS format) | If `jet-external.com` + no existing spec |
>
> **Not automated** (manual steps):
> - Create secrets in OneSecrets Vault for each environment
> - Update legacy AWS resource policies (if cross-account needed)
> - For non-EU1 bulkheads: create secrets in each bulkhead's Vault independently

**Gate**: Get explicit confirmation: "Ready to generate changes?"
