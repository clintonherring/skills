# DNS & Networking Reference

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

### Auto-Provisioned on Istio Ingress (No helm-core PR Needed)

| Type                              | Description                                  | Scope                        | Route53 CNAME Needed? |
| --------------------------------- | -------------------------------------------- | ---------------------------- | --------------------- |
| **Environment (E-record)**        | Environment-specific, NOT portable           | 1 per environment            | No — fully automatic  |
| **Namespaced Global (NG-record)** | Portable, self-descriptive — **recommended** | Portable across environments | **Yes** — CNAME pointing to E-record |

Both are configured through the VirtualService `hosts` list in the helm values and the `igw-<project>` gateway that comes with project onboarding.

### Requires Additional Configuration

| Type                    | Description                                   | Requires                                             |
| ----------------------- | --------------------------------------------- | ---------------------------------------------------- |
| **Regional (R-record)** | Region-specific address                       | `customRules` in `cps/helm-core` on `igw-<project>`  |
| **Global (G-record)**   | Single global address                         | `customRules` in `cps/helm-core` on `igw-<project>`  |
| **Brand domain**        | Consumer-facing domain (e.g., `takeaway.com`) | `customRules` in `cps/helm-core` on `igw-<project>`  |

**Rule**: Only E-records and NG-records are auto-provisioned through `igw-<project>`. Any other hostname on the Istio ingress — R-records, G-records, brand domains — requires `customRules` in `cps/helm-core`. Note: `jet-external.com` does NOT appear on the Istio ingress; external API traffic is proxied through SmartGateway to the internal NG-record.

### User-Friendly Prompt for Regional Records

> "Your service will automatically get standard DNS records when deployed. Do you also need a **regional record**? This is typically only needed if other services outside your project reference your service by a region-specific address."

Most services do NOT need regional records. The NG-record is sufficient.

---

## CloudOps DNS Patterns (Source — to be replaced)

CloudOps-EKS uses private DNS domains that are **unreachable from Sonic Runtime**:

| Environment | Pattern                                       |
| ----------- | --------------------------------------------- |
| Dev         | `{service}.{namespace}.d.eks.tkwy-infra.io`   |
| Staging     | `{service}.{namespace}.x.eks.tkwy-staging.io` |
| Production  | `{service}.{namespace}.p.eks.tkwy-prod.io`    |

**CRITICAL**: ALL `*.eks.tkwy-*.io` domain references must be migrated to `*.jet-internal.com` equivalents. These are private CloudOps domains and will not resolve from Sonic Runtime.

---

## VirtualService Configuration

Fetch the current VirtualService schema from the **basic-application chart** (`values.yaml` → `virtualservices` section). The general pattern:

- `hosts`: List of DNS records the service responds to
- `gateways`: Reference to `istio-gateways/igw-{project-id}` (created during project onboarding)
- `http`: Route rules pointing to the service

Always include E-record in the hosts. Add NG-record (recommended). Add R-record only if user requested a regional record or if one was already in use. Use `project-id` as-is — no prefix or suffix.

### VirtualService Hosts by Exposure Type

Example for `APP_NAME`=`orderapi`, `project-id`=`cu-order-reviews`, env=`pdv-5.eu-west-1.production`:

| Exposure Type | Hosts to Include                                                                                                                                                                                          |
| ------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Internal only | E: `orderapi.cu-order-reviews.pdv-5.eu-west-1.production.jet-internal.com`, NG: `orderapi.cu-order-reviews.production.jet-internal.com`, (R: `orderapi.eu-west-1.production.jet-internal.com` if needed) |
| External API  | Same as Internal — SmartGateway proxies to NG-record, so Istio only sees `jet-internal.com` hosts                                                                                                         |
| Brand domain  | E-record, NG-record, PLUS `{APP_NAME}.takeaway.com` (brand domain hits ingress directly via Cloudflare)                                                                                                   |
| Both          | E-record, NG-record, brand domain hostname(s) if applicable                                                                                                                                               |

---

## helm-core customRules

A `cps/helm-core` PR is needed whenever the service uses any DNS record beyond E-record and NG-record on the Istio ingress. This includes:

- **Regional records (R-record)**
- **Global records (G-record)**
- **Brand domains** (e.g., `api.takeaway.com`) — consumer-facing hostnames that arrive at the Istio ingress with the brand domain as the host header

`jet-external.com` does NOT require `customRules` — external API traffic is proxied through SmartGateway to the service's internal NG-record, so the Istio ingress only sees `jet-internal.com` hostnames. Only E-records and NG-records are auto-provisioned via the `igw-<project>` gateway wildcard. All other hostnames that arrive at the Istio ingress require explicit `customRules`.

To find the correct file and format:

1. Clone `cps/helm-core`: `gh repo clone github.je-labs.com/cps/helm-core /tmp/helm-core -- --depth 1`
2. Explore `clusters/` directory to find the istio-gateways config files
3. Look at existing `customRules` entries for the pattern to follow
4. Add the G/R-record/brand-domain host under the `igw-<project>` gateway

This must be done for each cluster/environment where the record should be active.

```yaml
# Regional record customRules (internal)
customRules:
  - hosts:
    - "{APP_NAME}.eu-west-1.production.jet-internal.com"
    defaultGateway: igw-{project-id}

# Brand domain customRules (brand domain traffic hits ingress directly)
customRules:
  - hosts:
    - "{APP_NAME}.takeaway.com"
    defaultGateway: igw-{project-id}
```

Must be added per cluster/environment in the helm-core `istio-gateways.yaml.gotmpl` files.

---

## Host Header Routing Chain (Critical Consistency Rule)

When a client calls a DNS record, the DNS resolves to the Istio ingress load balancer. The HTTP request arrives with that hostname as the `Host` header. For the request to reach the application, **all three layers must match**:

1. **DNS** (Route53 or domain-routing): The record must resolve to the Istio ingress
2. **helm-core**: The `igw-{project}` gateway must have a `customRules` entry for that Host (except E/NG records — auto-provisioned via wildcard)
3. **VirtualService**: The app's VirtualService must list that Host in its `hosts` field

A mismatch at any layer causes traffic to fail silently (404 or connection refused). See the consistency validation reference (`09-consistency-validation.md`) for the validation procedure.

---

## External Service DNS

External (public-facing) services use a layered architecture with additional components beyond internal DNS. The key difference: **external services are always exposed internally first**, then proxied through SmartGateway and optionally Cloudflare.

**SmartGateway is needed ONLY when the service has `*.jet-external.com` endpoints** — i.e., traffic from the public internet routed through SmartGateway (Kong) to the service. Brand domains (`*.takeaway.com`, `*.lieferando.de`, etc.) that route through Cloudflare CDN directly to the Istio ingress do NOT need SmartGateway — they are a completely separate traffic path. Always trace the actual DNS path during DNS discovery (Phase 2 / Phase 4 Q3) rather than assuming from the domain name or exposure type alone.

### Architecture Overview

```
Internal Only:
  Other JET Service → GlobalDNS (jet-internal.com) → Istio IGW → VirtualService → Pods

External API (via SmartGateway):
  Internet Client → jet-external.com (public DNS) → SmartGateway (Kong) → Internal NG-record (jet-internal.com:443) → Istio IGW → VirtualService → Pods

Brand Domain (via Cloudflare → Istio directly):
  Internet User → Route53 → Cloudflare CDN (proxied, WAF, DDoS) → Istio IGW (host: takeaway.com) → VirtualService → Pods

Brand Domain (internal use, no Cloudflare/SmartGateway):
  Other JET Service → Route53 (brand domain CNAME → Istio endpoint) → Istio IGW (host: brand.com) → VirtualService → Pods
```

**Key insight**: For external APIs, SmartGateway proxies to the service's internal NG-record. The Istio ingress only sees `jet-internal.com` host headers — `jet-external.com` never reaches the ingress. For brand domains, Cloudflare routes directly to the Istio ingress with the brand domain as the host header, so `customRules` are needed for brand domains but NOT for `jet-external.com`.

### Domain Types

| Domain                                                | Purpose                     | DNS Zone                    | Managed In           |
| ----------------------------------------------------- | --------------------------- | --------------------------- | -------------------- |
| `*.jet-internal.com`                                  | Internal service-to-service | Private Route53             | `IFA/route53`        |
| `*.jet-external.com`                                  | External/public APIs        | Public Route53              | `IFA/route53`        |
| Brand domains (`takeaway.com`, `lieferando.de`, etc.) | Consumer-facing sites       | Public Route53 and/or Cloudflare | `IFA/route53` and/or `IFA/domain-routing` |

**Important**: Brand domain DNS can be in `IFA/route53` (public zone records files),
`IFA/domain-routing` (Cloudflare-proxied records), or both. Always search for the
**parent domain** (e.g., `scoober.com`) in both repos — not just the subdomain.

### SmartGateway (Kong Gateway)

SmartGateway is a customized extension of Kong Gateway that routes `jet-external.com` API traffic from the public internet. SmartGateway is needed **only** when `*.jet-external.com` endpoints are detected in DNS path discovery. Brand domains (Cloudflare → Istio directly) do NOT go through SmartGateway and do NOT need SmartGateway configuration.

For SmartGateway **configuration details** (JSON schema, paths, plugins, environment mapping, testing workflow), see `21-smartgateway.md`.

**Key configuration rules**:

- **`host`**: Must use the service's **NG-record** (internal address)
- **`port`**: Must be `443` — SmartGateway connects via HTTPS
- **`protocol`**: Must be `"https"` — prevents 301 redirects

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

### Cloudflare Integration (Brand Domains)

Brand domains use Cloudflare as a CDN and WAF layer. Cloudflare configuration is managed in the `IFA/domain-routing` repo.

**Three components** (always fetch current format from the repo):

1. **Route53 DNS record** — Points the brand domain to Cloudflare:
   - Location: `vars/records/route53/{domain}.yaml`
   - Record: CNAME to `{subdomain}.{domain}.cdn.cloudflare.net.`

2. **Cloudflare DNS record** — Proxied CNAME to the origin:
   - Location: `vars/records/cloudflare/{domain}.yaml`
   - Origin must point to SmartGateway or Istio public ingress endpoint
   - `proxied: true` enables Cloudflare CDN/WAF

3. **WAF rules** — Allow/block rules for the brand domain:
   - Location: `vars/domains/waf.yml`
   - Define which paths, methods, and hosts are allowed through
   - Can also set page rules for cache behavior in `vars/domains/page_rules.yml`

**During migration**: The Cloudflare origin endpoint needs to change from the CloudOps-EKS origin to the Sonic Runtime endpoint. This is done by updating the CNAME value in the Cloudflare DNS record.

### API Governance (BOATS)

All externally-exposed APIs require an **OpenAPI v3 specification** registered in the `api_specifications` repo using the BOATS format. This is reviewed and approved by the **API Design Guild** (`#api-guild-design` on Slack).

- Spec location: `src/paths/` in the `api_specifications` repo
- Format: YAML or Nunjucks (`.yml.njks`) with OpenAPI v3 schema
- Required fields: `x-component-name`, `description`, `operationId`, `responses`

---

## Decision Tree: DNS Configuration by Exposure Type

Exposure type is determined by DNS path discovery (Phase 2 / Phase 4 Q3), not by asking the user directly.

```
Discovered = Internal only?
├── E-record + NG-record (auto-provisioned, jet-internal.com)
├── R-record or G-record? → Only if user confirmed regional record needed → helm-core customRules + Route53 (all envs)
└── Done

Discovered = External (internet-facing via SmartGateway)?
├── All of Internal above (VirtualService uses jet-internal.com only), PLUS:
├── SmartGateway config → proxies external traffic to NG-record (port 443, HTTPS)
├── BOATS API spec (if not existing)
└── No helm-core customRules needed for jet-external.com (SmartGateway handles it)

Discovered = Brand domain (Cloudflare proxied, external)?
├── All of Internal above, PLUS:
├── SmartGateway config → proxies to NG-record
├── Cloudflare proxied CNAME in domain-routing repo
├── WAF rules in domain-routing repo
├── helm-core customRules for brand domain hostname (brand domain hits ingress directly)
├── VirtualService must include brand domain in hosts
└── BOATS API spec (if not existing)

Discovered = Brand domain (internal use, no Cloudflare/SmartGateway)?
├── All of Internal above, PLUS:
├── helm-core customRules for brand domain hostname
├── VirtualService must include brand domain in hosts
├── Route53 record for brand domain (direct CNAME to Istio endpoint)
└── No SmartGateway, no Cloudflare, no BOATS needed

Discovered = Brand domain?
├── All of Internal above, PLUS:
├── helm-core customRules for brand domain hostname
├── VirtualService must include brand domain in hosts
├── Recommend: keep old endpoint for now, defer domain migration to a later phase
├── Internal brand domain: expose options — keep old endpoint OR change to GlobalDNS (clients must update)
├── External brand domain: can migrate to SMG, or keep without SMG for now (2.0 phase)
└── If parent domain not found in either repo → escalate to user / ask in #help-infra-foundations-aws

Discovered = Both (internal + external)?
├── Internal DNS: E-record + NG-record + optional R-record
├── External: SmartGateway + BOATS (always)
├── If brand domain: + Cloudflare + helm-core customRules for brand hostname
└── VirtualService: jet-internal.com hosts + brand domain (if applicable)
```

---

## Per-Environment DNS Strategy

The DNS strategy may differ by environment. For example:

- QA/Staging: GlobalDNS R-record via `IFA/route53`
- Production: Brand domain via `IFA/domain-routing`

When R-records or G-records are used, the DNS records must exist in **all environments** (QA, staging, production) — not just production. Users need to test the DNS path in QA/staging before production.

---

## Internal vs External Summary

| Domain               | Purpose                                           |
| -------------------- | ------------------------------------------------- |
| `*.jet-internal.com` | Internal service-to-service communication (HTTPS) |
| `*.jet-external.com` | External-facing endpoints (public internet)       |

### Best Practice

E-records should NOT be directly referenced outside the service's project. Use NG-records or R-records for cross-project communication.
