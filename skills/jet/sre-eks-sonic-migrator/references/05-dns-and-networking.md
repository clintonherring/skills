# DNS & Networking

## Legacy Domains (Not Supported)

The following legacy domain patterns are **NOT supported** in Sonic Runtime and cannot be used for traffic splitting or DNS routing:

| Legacy Domain             | Description                                                           |
| ------------------------- | --------------------------------------------------------------------- |
| `*.tkwy.cloud`            | Legacy .tkwy.cloud hosts (e.g., `servicename.int.staging.tkwy.cloud`) |
| `internal.takeaway.local` | Legacy internal Takeaway domain                                       |

Services currently using these domains **must migrate to GlobalDNS** (`jet-internal.com` / `jet-external.com`) before or as part of the Sonic Runtime migration. Sonic Runtime's Istio-based networking does not integrate with the DNS infrastructure that manages these legacy domains.

If legacy domain references are detected during Phase 2 analysis, they will be flagged as a warning. See [18-phase-3-resolve-blockers.md](18-phase-3-resolve-blockers.md) for the resolution steps.

---

## DNS Record Types in Sonic Runtime

Sonic Runtime uses **GlobalDNS** with four record types. Two are auto-provisioned with project onboarding; two require additional configuration.

For current DNS formats and specifics, fetch from Backstage:

- Search: `expose service internally oneeks`
- Search: `dns service discovery specification`

### Record Format Reference (Spec 003 + Sonic Runtime)

In Sonic Runtime, each project has its own Istio IGW (`igw-<project-id>`) and the E-record wildcard is scoped to the project. The `project-id` is the same as the namespace and is used **as-is** — do NOT append or prepend any prefix or suffix.

`dns-prefix` = `APP_NAME` from PlatformMetadata (validated in Phase 1). May differ from the repo name.

| Type          | Format                                                                         | Example                                                                 |
| ------------- | ------------------------------------------------------------------------------ | ----------------------------------------------------------------------- |
| **E-record**  | `<APP_NAME>.<project-id>.<env-component>.<region>.<env-type>.jet-internal.com` | `orderapi.cu-order-reviews.pdv-5.eu-west-1.production.jet-internal.com` |
| **NG-record** | `<APP_NAME>.<project-id>.<env-type>.jet-internal.com`                          | `orderapi.cu-order-reviews.production.jet-internal.com`                 |
| **R-record**  | `<APP_NAME>.<region>.<env-type>.jet-internal.com`                              | `orderapi.eu-west-1.production.jet-internal.com`                        |
| **G-record**  | `<APP_NAME>.<env-type>.jet-internal.com`                                       | `orderapi.production.jet-internal.com`                                  |

For external records, replace `jet-internal.com` with `jet-external.com` in the **Route53 public zone** only. Note: `jet-external.com` records are only used for public DNS resolution — they do NOT appear in VirtualService hosts or Istio ingress `customRules`. External traffic is proxied through SmartGateway (Kong) which routes to the service's **internal** record (`jet-internal.com`), so the Istio ingress only ever sees `jet-internal.com` hostnames. Brand domains (e.g., `takeaway.com`) are an exception — they do appear on the Istio ingress as host headers.

**Components:**

| Component       | Description                                           | Example                       |
| --------------- | ----------------------------------------------------- | ----------------------------- |
| `APP_NAME`      | Application name from PlatformMetadata                | `orderapi`                    |
| `project-id`    | Sonic Runtime project (= namespace), as-is from user  | `cu-order-reviews`            |
| `env-component` | Summarized env-alias: `<env-function>-<partition-id>` | `pdv-5`                       |
| `region`        | AWS region name                                       | `eu-west-1`                   |
| `env-type`      | Environment type                                      | `qa`, `staging`, `production` |

**DNS resolution chain:** R → E → resource, G → E → resource, NG → E → resource (via CNAME).

### Auto-Provisioned (No helm-core PR Needed)

| Type                              | Description                                  | Scope                        |
| --------------------------------- | -------------------------------------------- | ---------------------------- |
| **Environment (E-record)**        | Environment-specific, NOT portable           | 1 per environment            |
| **Namespaced Global (NG-record)** | Portable, self-descriptive — **recommended** | Portable across environments |

Both are configured through the VirtualService `hosts` list in the helm values and the `igw-<project>` gateway that comes with project onboarding.

### Requires Additional Configuration

| Type                    | Description                                   | Requires                                                 |
| ----------------------- | --------------------------------------------- | -------------------------------------------------------- |
| **Regional (R-record)** | Region-specific address                       | `customRules` in `cps/helm-core` on `igw-<project>`      |
| **Global (G-record)**   | Single global address                         | `customRules` in `cps/helm-core` on `igw-<project>`setup |
| **Brand domain**        | Consumer-facing domain (e.g., `takeaway.com`) | `customRules` in `cps/helm-core` on `igw-<project>`      |

**Rule**: Only E-records and NG-records are auto-provisioned through `igw-<project>`. Any other hostname on the Istio ingress — R-records, G-records, brand domains — requires `customRules` in `cps/helm-core`. Note: `jet-external.com` does NOT appear on the Istio ingress; external API traffic is proxied through SmartGateway to the internal NG-record.

### User-Friendly Prompt for Regional Records

> "Your service will automatically get standard DNS records when deployed. Do you also need a **regional record**? This is typically only needed if other services outside your project reference your service by a region-specific address."

Most services do NOT need regional records. The NG-record is sufficient.

## VirtualService Configuration

Fetch the current VirtualService schema from the **basic-application chart** (`values.yaml` → `virtualservices` section). The general pattern:

- `hosts`: List of DNS records the service responds to
- `gateways`: Reference to `istio-gateways/igw-{project-id}` (created during project onboarding)
- `http`: Route rules pointing to the service

Always include E-record in the hosts. Add NG-record (recommended). Add R-record only if user requested a regional record or if it was used already. Use `project-id` as-is — no prefix or suffix.

## helm-core customRules

A `cps/helm-core` PR is needed whenever the service uses any DNS record beyond E-record and NG-record on the Istio ingress. This includes:

- **Regional records (R-record)**
- **Global records (G-record)**
- **Brand domains** (e.g., `api.takeaway.com`) — consumer-facing hostnames that arrive at the Istio ingress with the brand domain as the host header

`jet-external.com` does NOT require `customRules` when external API traffic is proxied through SmartGateway to the service's internal NG-record, so the Istio ingress only sees `jet-internal.com` hostnames.

`jet-external.com` hosts will be needed, and should be added to the istio-ext ingress in `helm-core` if service is not proxied through Smartgateway but is exposed externally.

Only E-records and NG-records are auto-provisioned via the `igw-<project>` gateway wildcard. All other hostnames that arrive at the Istio ingress require explicit `customRules`.

### Critical: Same Ingress Requirement

`customRules` **must be added to the same ingress resource** (e.g., `istio-int`, `istio-int-2`) that contains the project's wildcard rule (`*.{project-id}.{domain}`). Each ingress in `istio-gateways.yaml.gotmpl` creates a **separate AWS ALB**. The DNS resolution chain for R-records and G-records works via CNAME to the E-record, which resolves to the ALB hosting the wildcard. If `customRules` are placed on a different ingress (different ALB), the CNAME chain delivers traffic to one ALB while the host-matching rule lives on another — causing the request to fail silently (404 or connection refused).

```
R-record → CNAME → E-record (wildcard) → ALB-A
customRules for R-record must be on ALB-A (same ingress as the wildcard)
```

### Finding the Correct File and Ingress

1. Clone `cps/helm-core`: `gh repo clone github.je-labs.com/cps/helm-core /tmp/helm-core`
2. Explore `clusters/{cluster}/releases/istio-gateways.yaml.gotmpl` for each target cluster
3. Find the ingress that contains your project's wildcard rule (`*.{project-id}.{domain}`)
4. Add the `customRules` entry **under that same ingress**
5. If the ingress is at its ALB rule limit, a new ingress must be defined — contact `#help-core-platform-services` for guidance

This must be done for each cluster/environment where the R-record should be active.

## Migrating from Consul .service Addresses

Sonic Runtime does **NOT** support `.service` resolution. **All** `.service` references in the migrating service must be replaced with GlobalDNS (`jet-internal.com`) equivalents — both infrastructure and application dependencies. The service will not function in Sonic Runtime with unresolved `.service` addresses.

**Reference**: [Backstage — Marathon Platform Transition: Important Points](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/oneeks/tasks/platform-transition/marathon/#important-points)

### Categories

| Category           | Pattern                                                   | Example                                     |
| ------------------ | --------------------------------------------------------- | ------------------------------------------- |
| **Infrastructure** | `<schemaname>.<resource>.service` or `<resource>.service` | `general.mysql.service`, `rabbitmq.service` |
| **Application**    | `<servicename>.service`                                   | `orderapi.service`                          |

> **Note**: The `<schemaname>` prefix in infrastructure `.service` addresses typically corresponds
> to a database schema name, instance name, or logical resource identifier.
> For example, in `general.mysql.service`, `general` is the schema name on the shared MySQL server.
> See the best practice note below the mapping rules for details on why schema-specific DNS is preferred.

### Infrastructure Mapping Rules

Infrastructure services use GlobalDNS with a `tk-` prefix:

| Rule | Source pattern                                            | GlobalDNS equivalent                                                               |
| ---- | --------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| 1    | `<schemaname>.<resource>.service`                         | `<schemaname>.tk-<resource>.<region>.<env-type>.jet-internal.com`                  |
| 2    | `<resource>.service` (no schemaname)                      | `tk-<resource>.<region>.<env-type>.jet-internal.com`                               |
| 3    | `<schemaname>-<resource>.service`                         | Check for `tk-<schemaname>-<resource>` first; if not found, split and apply rule 1 |
| 4    | Read-only variant (e.g., `<schemaname>.mysql-ro.service`) | `<schemaname>.tk-<resource>-ro.<region>.<env-type>.jet-internal.com`               |

> **Best practice — use schema-specific DNS**: When mapping infrastructure `.service` addresses,
> use the **database schema name** (or logical instance name) as the `<schemaname>` prefix, not a
> generic server or brand name. This makes DNS portable — if a schema becomes problematic or needs
> to be moved to a different server, only the DNS record needs repointing, with no application
> config changes required.
>
> For **read-heavy services**, also consider configuring a read-only endpoint
> (`<schemaname>.tk-<resource>-ro.<region>.<env-type>.jet-internal.com`) to keep load off the
> primary writer.
>
> **When detecting `.service` references**: ask the service team to confirm their actual schema
> names. The prefix in the `.service` address (e.g., `general`, `thuis`) may be a
> server-level name rather than the schema name. Validate the correct schema-specific DNS record
> exists in `IFA/route53`; if it doesn't, the team may need to request it via
> `#help-core-platform-services`.

### Application Mapping Rules

Application `.service` addresses point to other JET microservices. Since `.service` is not resolvable in Sonic Runtime, **every** application dependency must also be replaced:

- **Has GlobalDNS address** (migrated or has R-record/NG-record): replace with that address
- **Still on SRE-EKS with no GlobalDNS**: the user must provide a reachable address (brand domain, GlobalDNS, or the target service must be migrated first). **Do not leave `.service` references** — they will fail at runtime.
- **Unknown status**: search `IFA/route53` for `<service>.<region>.<env-type>.jet-internal.com`; ask the user if not found

### Route53 Validation (Mandatory)

Every proposed GlobalDNS mapping must be validated against `IFA/route53` (already cloned in Phase 4 Q3):

```bash
grep -r "<proposed-hostname>" /tmp/route53 --include="*.yaml" --include="*.yml"
```

- **Found** → validated, use it
- **Not found** → ask the user: provide correct address, contact `#help-core-platform-services`, or defer (flagged as blocker)

### Environment-Aware Replacements

Addresses differ per environment. Place them in per-environment `state_values/{env}.yaml` — not hardcoded in application code.

### Workflow

1. **Phase 2.3c**: Detect and classify `.service` references, derive proposed mappings
2. **Phase 4 Q4a-2**: Validate against Route53, confirm with user, store as `SERVICE_ADDR_MAP`
3. **Phase 5 Step 8**: Apply `SERVICE_ADDR_MAP` per environment

### Best Practice

E-records should NOT be directly referenced outside the service's Project. Use NG-records or R-records for cross-project communication.

## External Service DNS

External (public-facing) services use a layered architecture with additional components beyond internal DNS. The key difference: **external services are always exposed internally first**, then proxied through SmartGateway and optionally Cloudflare.

**SmartGateway is needed ONLY when the service has external internet-facing endpoints** — i.e., traffic from the public internet routed through SmartGateway (Kong) to the service. Brand domains used for internal purposes (not proxied through Cloudflare/SmartGateway) do NOT need SmartGateway. Always trace the actual DNS path during the DNS discovery step (Phase 4 Q3) rather than assuming from the domain name alone.

### Architecture Overview

```
Internal Only:
  Other JET Service → GlobalDNS (jet-internal.com) → Istio IGW → VirtualService → Pods

External API (via SmartGateway):
  Internet Client → jet-external.com (public DNS) → Cloudflare (proxied) -> SmartGateway (Kong) → Internal E/NG-record (jet-internal.com:443) → Istio IGW (istio-int-*) → VirtualService → Pods

Brand Domain (via Cloudflare → Istio directly):
  Internet Client → Route53 → Cloudflare (proxied, WAF, DDoS) → Istio IGW (istio-ext) (host: takeaway.com) → VirtualService → Pods

Brand Domain (internal use, no Cloudflare/SmartGateway):
  Other JET Service → Route53 (brand domain CNAME → Istio endpoint) → Istio IGW (host: brand.com) → VirtualService → Pods
```

**Key insight**: For external APIs, SmartGateway proxies to the service's internal NG-record. The Istio ingress only sees `jet-internal.com` host headers — `jet-external.com` never reaches the ingress. For brand domains, Cloudflare routes directly to the Istio ingress with the brand domain as the host header, so `customRules` are needed for brand domains but NOT for `jet-external.com`.

### Domain Types

| Domain                                                | Purpose                     | DNS Zone                    | Managed In           |
| ----------------------------------------------------- | --------------------------- | --------------------------- | -------------------- |
| `*.jet-internal.com`                                  | Internal service-to-service | Private Route53             | `IFA/route53`        |
| `*.jet-external.com`                                  | External/public APIs        | Public Route53              | `IFA/route53`        |
| Brand domains (`takeaway.com`, `lieferando.de`, etc.) | Consumer-facing sites       | Public Route53 + Cloudflare | `IFA/domain-routing` |

### SmartGateway (Kong Gateway)

SmartGateway is a customized extension of Kong Gateway that routes internet-facing JET API traffic. SmartGateway is needed **only** when the service has external internet-facing endpoints — determined by the DNS path discovery in Phase 4 Q3. Brand domains used internally (not proxied through Cloudflare → SmartGateway) do NOT need SmartGateway. Some services are only proxied through Cloudflare without SmartGateway, in those cases, they can be directly exposed via the External Istio Ingress (istio-ext) with the brand domain as the host header. This should be user's choice.

**Key configuration rules** (always fetch current schema from the `external-api-services/smartgatewayconfiguration` repo):

- **`host`**: Must use the service's **NG-record** (internal address)
- **`port`**: Must be `443` — SmartGateway connects via HTTPS
- **`protocol`**: Must be `"https"` — prevents 301 redirects
- **`routes`**: Define URL paths, methods, and protocols the service handles externally
- **`plugins`**: Rate limiting, authentication, etc.
- **`environments`**: SmartGateway has its own environment names (different from Sonic Runtime envs)

**SmartGateway Environment Mapping** (approximate — always verify from repo):

| SmartGateway Env               | Bulkhead | Stage      |
| ------------------------------ | -------- | ---------- |
| `eu-central-1-ing-qa-1`        | EU1      | QA         |
| `eu-central-1-ing-staging-1`   | EU1      | Staging    |
| `eu-central-1-ing-prod-1`      | EU1      | Production |
| `eu-west-1-ing-qa-1`           | EU2      | QA         |
| `eu-west-1-ing-staging-1`      | EU2      | Staging    |
| `eu-west-1-ing-prod-1`         | EU2      | Production |
| `ap-southeast-2-ing-qa-1`      | OC1      | QA         |
| `ap-southeast-2-ing-staging-1` | OC1      | Staging    |
| `ap-southeast-2-ing-prod-1`    | OC1      | Production |
| `us-east-1-ing-qa-1`           | NA1      | QA         |
| `us-east-1-ing-staging-1`      | NA1      | Staging    |
| `us-west-2-ing-prod-1`         | NA1      | Production |

Config files are placed under `Data/Global/{service-name}.json.hbs` in the SmartGateway repo.

**Testing workflow**: Deploy SmartGateway config to QA first (ad-hoc deploy). Test via SmartGateway regional endpoints. Request review in `#help-http-integrations`. Merge and deploy to staging/production.

### Cloudflare Integration (Brand Domains)

Brand domains use Cloudflare as a CDN layer in front of SmartGateway. Cloudflare configuration is managed in the `IFA/domain-routing` repo.

**Three components** (always fetch current format from the repo):

1. **Route53 DNS record** — Points the brand domain to Cloudflare:
   - Location: `vars/records/route53/{domain}.yaml`
   - Record: CNAME to `{subdomain}.{domain}.cdn.cloudflare.net.`

2. **Cloudflare DNS record** — Proxied CNAME to the origin:
   - Location: `vars/records/cloudflare/{domain}.yaml`
   - Origin must point to SmartGateway or Istio public ingress endpoint
   - `proxied: true` enables Cloudflare CDN

**During migration**: The Cloudflare origin endpoint needs to change from the SRE-EKS origin to the Sonic Runtime endpoint. This is done by updating the CNAME value in the Cloudflare DNS record.

### API Governance (BOATS)

All externally-exposed APIs require an **OpenAPI v3 specification** registered in the `api_specifications` repo using the BOATS format. This is reviewed and approved by the **API Design Guild** (`#api-guild-design` on Slack).

- Spec location: `src/paths/` in the `api_specifications` repo
- Format: YAML or Nunjucks (`.yml.njks`) with OpenAPI v3 schema
- Required fields: `x-component-name`, `description`, `operationId`, `responses`

### Istio Gateway customRules for Non-Standard Hosts

When a service receives traffic on a hostname beyond E-record and NG-record — such as an R-record or brand domain — the Istio ingress gateway must be configured to accept that hostname via `customRules` in `cps/helm-core`.

**Note**: `jet-external.com` does NOT need `customRules`. External API traffic goes through SmartGateway, which proxies to the internal NG-record. The Istio ingress only sees `jet-internal.com` host headers. Brand domains are different — Cloudflare routes directly to the Istio ingress with the brand domain as the host header.

```
# Regional record customRules (internal)
customRules:
  - hosts:
    - "{APP_NAME}.eu-west-1.production.jet-internal.com"
    defaultGateway: igw-{project-id}

# Brand domain customRules (brand domain internal traffic hits ingress directly)
customRules:
  - hosts:
    - "{APP_NAME}.takeaway.com"
    defaultGateway: igw-{project-id}

# Brand domain customRules (brand domain external traffic proxied from Cloudflare)
istio-ext:
  rules:
    - hosts:
      - "{APP_NAME}.takeaway.com"
      defaultGateway: igw-{project-id}
```

Must be added per cluster/environment in the helm-core `istio-gateways.yaml.gotmpl` files.

### Decision Tree: DNS Configuration by Exposure Type

Exposure type is determined by DNS path discovery (Phase 4 Q3), not by asking the user directly.

```
Discovered = Internal only?
├── E-record + NG-record (auto-provisioned, jet-internal.com)
├── R-record or G-record? → Only if user confirmed regional record needed → helm-core customRules + Route53 (all envs)
└── Consul bridge? → Only if Q4a=Yes → igw-marathon VirtualService entry

Discovered = External (internet-facing via SmartGateway)?
├── All of Internal above (VirtualService uses jet-internal.com only), PLUS:
├── SmartGateway config → proxies external traffic to NG-record (port 443, HTTPS)
├── BOATS API spec (if not existing)
└── No helm-core customRules needed for jet-external.com (SmartGateway handles it)

Discovered = Brand domain (Cloudflare proxied, external)?
├── All of Internal above, PLUS:
├── (if user chooses) SmartGateway config → proxies to NG-record
├── Cloudflare proxied CNAME in domain-routing repo
├── helm-core customRules for brand domain hostname (brand domain hits ingress directly)
├── VirtualService must include brand domain in hosts
└── BOATS API spec (if not existing)

Discovered = Brand domain (internal use, no Cloudflare/SmartGateway)?
├── All of Internal above, PLUS:
├── helm-core customRules for brand domain hostname
├── VirtualService must include brand domain in hosts
├── Route53 record for brand domain (direct CNAME to Istio endpoint)
└── No SmartGateway, no Cloudflare, no BOATS needed

Discovered = Both (internal + external)?
├── Internal DNS: E-record + NG-record + optional R-record
├── External: SmartGateway + BOATS (always)
├── If brand domain: + Cloudflare + helm-core customRules for brand hostname
└── VirtualService: jet-internal.com hosts + brand domain (if applicable)
```

### DNS Path Discovery (Phase 4 Q3)

To accurately determine how a service is exposed, discover the DNS path from existing infrastructure rather than asking the user:

1. **Extract hostnames** from existing VirtualService / ingress config (Phase 2)
2. **Check `IFA/route53`** — search for each hostname in terraform files; note record type, target, zone
3. **Check `IFA/domain-routing`** — search for hostname in `vars/records/`; check for Cloudflare proxy
4. **If Cloudflare detected**: Check `IFA/cloudflareplatformproduction` and `IFA/cloudflareplatformstaging` for Cloudflare DNS records, WAF rules, page rules, origin overrides
5. **Present findings** to user as a table and ask for confirmation

This discovery-first approach ensures accuracy — brand domains can be used internally without Cloudflare/SmartGateway, and the DNS path trace reveals the actual routing.

### Host Header Routing Chain (Critical Consistency Rule)

When a client calls a DNS record, the DNS resolves to the Istio ingress load balancer. The HTTP request arrives with that hostname as the `Host` header. For the request to reach the application, **all three layers must match**:

1. **DNS** (Route53 or domain-routing): The record must resolve to the Istio ingress
2. **helm-core**: The `igw-{project}` gateway must have a `customRules` entry for that Host (except E/NG records — auto-provisioned via wildcard)
3. **VirtualService**: The app's VirtualService must list that Host in its `hosts` field

A mismatch at any layer causes traffic to fail silently (404 or connection refused). See Phase 5.8 in the main workflow for the validation step.

### Per-Environment DNS Strategy

The DNS strategy may differ by environment. For example:

- QA/Staging: GlobalDNS R-record via `IFA/route53`
- Production: Brand domain via `IFA/domain-routing`

When R-records or G-records are used, the DNS records must exist in **all environments** (QA, staging, production) — not just production. Users need to test the DNS path in QA/staging before production.

### VirtualService Hosts by Exposure Type

Example for `APP_NAME`=`orderapi`, `project-id`=`cu-order-reviews`, env=`pdv-5.eu-west-1.production`:

| Exposure Type | Hosts to Include                                                                                                                                                                                          |
| ------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Internal only | E: `orderapi.cu-order-reviews.pdv-5.eu-west-1.production.jet-internal.com`, NG: `orderapi.cu-order-reviews.production.jet-internal.com`, (R: `orderapi.eu-west-1.production.jet-internal.com` if Q4b=Yes) |
| External API  | Same as Internal — SmartGateway proxies to NG-record, so Istio only sees `jet-internal.com` hosts                                                                                                         |
| Brand domain  | E-record, NG-record, PLUS `{APP_NAME}.takeaway.com` (brand domain hits ingress directly via Cloudflare)                                                                                                   |
| Both          | E-record, NG-record, brand domain hostname(s) if applicable                                                                                                                                               |

If Consul bridge is enabled, also add the `.service` host on `igw-marathon` gateway.
