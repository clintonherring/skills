# Traffic Split Patterns

## Approach 1: DNS-Based Weighted Routing (Most Common)

**Route53 traffic split domains**: `*.jet-internal.com`, `*.jet-external.com`

**Brand domains** (`*.takeaway.com`, `*.scoober.com`, etc.): traffic split is managed in
whichever repo manages the parent domain — either `IFA/route53` (weighted CNAME records)
or `IFA/domain-routing` (weighted endpoints via octodns). Search for the parent domain in
both repos during DNS discovery (Phase 2 Step 2d).

**Recommended approach**: Keep the old brand domain endpoint as-is for the runtime migration.
Defer domain migration (switching to GlobalDNS / SmartGateway) to a later phase. This keeps
the migration focused on the runtime. However, traffic split still happens on the brand
domain itself — add weighted records in whichever repo manages it. Only add NG-records
if the service actually needs a `jet-internal.com` address.

**NOT supported for traffic split**: `*.eks.tkwy-*.io` (CloudOps private domains — must be replaced entirely)

### Route53 Weighted Record Format

Clone `IFA/route53` and explore the repo structure to find the correct zone file and follow
existing patterns for field ordering, TTL values, and other conventions.

```yaml
# CloudOps entry (existing or new)
- name: "service.eu-west-1.production.jet-internal.com"
  type: "CNAME"
  records: "service.namespace.p.eks.tkwy-prod.io"
  weight: 100
  identifier: cloudops-service

# Sonic Runtime entry (new)
- name: "service.eu-west-1.production.jet-internal.com"
  type: "CNAME"
  records: "service.project.pdv-5.eu-west-1.production.jet-internal.com"
  weight: 0
  identifier: oneeks-service
```

### Per-Environment Weighted Records

**Important**: If the service uses R-records or G-records, weighted CNAME records must be
created for **ALL environments** (QA, staging, production), not just production. Each
environment may have a different DNS strategy:

| Environment | Example Strategy |
|-------------|----------------------------------------------------------|
| QA          | R-record via Route53 (weighted CNAME in qa zone)         |
| Staging     | R-record via Route53 (weighted CNAME in staging zone)    |
| Production  | Brand domain via `IFA/domain-routing` + R-record via Route53 |

When generating Route53 changes:

1. Identify which environments use R-records or G-records (from DNS Path Discovery in Phase 4)
2. Generate weighted CNAME records for **each** applicable environment
3. Follow existing input patterns in the `IFA/route53` repo for consistency
4. Each environment's zone file is typically in a separate directory — explore the repo to find the correct paths

### Gradual Increase Schedule

| Stage | Sonic Weight | CloudOps Weight | Duration |
|-------|-------------|-----------------|----------|
| Start | 0 | 100 | Deploy + verify |
| Canary | 1 | 99 | 1-2 days |
| 10% | 10 | 90 | 3-5 days |
| 50% | 50 | 50 | 1 week |
| Full | 100 | 0 | 30+ days before decommission |

## Approach 2: SmartGateway (External APIs)

For external-facing APIs:
- Host-based routing through SmartGateway (Kong)
- Preserves existing URLs
- Host = NG-record, port = 443, protocol = https
- **NOT needed if internal endpoints only** — even with a brand domain

## Approach 3: Path-Based Routing with Istio

For complex migrations where multiple microservices share the same domain and you cannot move
all of them at once. Routes different URL paths to different clusters during the transition
period using Istio VirtualServices.

> Source: [CloudOps to Sonic Runtime Traffic Split](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/oneeks/tasks/platform-transition/cloudops/cloudops-sonic-runtime-traffic-split/)

**When to use**: Multiple services behind the same domain, migrating one at a time.

**Important**: This approach still requires traffic split configuration — it does NOT mean
skipping traffic split entirely. If you identify this as the right approach, present it to
the user in Phase 4 Q6 and get explicit confirmation. Do NOT autonomously choose this
approach to avoid creating traffic split PRs.

**Required Components**:

| Component | Where | Purpose |
|-----------|-------|---------|
| VirtualService | CloudOps | Path matching rules to route specific paths to Sonic Runtime |
| ServiceEntry | CloudOps | Allow outbound routing to Sonic Runtime Ingress Gateway hostname |
| VirtualService | Sonic Runtime | Handle incoming traffic for the forwarded paths |
| Gateway | Sonic Runtime | Accept traffic for the shared domain |

**Example** — route `/couriers/*` to Sonic Runtime while keeping other paths on CloudOps:

```yaml
# CloudOps VirtualService
spec:
  gateways:
  - istio-system/igw-scoober-courier
  hosts:
  - courier.scoober.com
  http:
  - match:
    - uri:
        prefix: /couriers
    route:
    - destination:
        host: courier.lm-dlv-mcap.pdv-5.eu-west-1.production.jet-internal.com
        port:
          number: 80
```

**Reference Implementation**: PES-9523 (courier service migration)

## Route53 File Locations

| Environment | Scope | File |
|-------------|-------|------|
| QA | Internal | `non-production/records/qa.jet-internal.com-private.yml` |
| QA | External | `non-production/records/qa.jet-external.com.yml` |
| Staging | Internal | `non-production/records/eu-west-1.staging.jet-internal.com-private.yml` |
| Staging | External | `non-production/records/eu-west-1.staging.jet-external.com.yml` |
| Production | Internal | `production/records/eu-west-1.production.jet-internal.com-private.yml` |
| Production | External | `production/records/eu-west-1.production.jet-external.com.yml` |

## Brand Domain Migration Strategy

For brand domains discovered during DNS lookup, recommend deferring domain migration to
a later phase. Present the user with options:

**Internal brand domains:**

> "Your service uses the brand domain **{domain}** for internal traffic. You have two
> options:"
>
> 1. **Keep old endpoint** (recommended) — keep using the brand domain as-is. Migrate
>    to GlobalDNS (`jet-internal.com`) in a follow-up phase.
> 2. **Change to GlobalDNS now** — switch to `jet-internal.com`/`jet-external.com`.
>    All clients currently using `{domain}` must update to the new address.
>
> When you're ready for the domain migration later, see:
> - [Expose Service Internally](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/oneeks/tasks/networking/expose-service-internally/) — GlobalDNS setup
> - [DNS Service Discovery Spec](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/oneeks/concepts/dns/) — record types (E/NG/R/G)

**External brand domains:**

> "Your service uses the brand domain **{domain}** for external traffic. You have two
> options:"
>
> 1. **Keep without SmartGateway for now** (recommended) — keep the brand domain routing
>    as-is. Migrate to SmartGateway in a 2.0 migration phase.
> 2. **Migrate to SmartGateway now** — set up SmartGateway routing for external traffic.
>
> When you're ready for the SmartGateway migration later, see:
> - [Expose Service Externally](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/oneeks/tasks/networking/expose-service-externally/) — SmartGateway setup
> - [CloudOps Traffic Split](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/oneeks/tasks/platform-transition/cloudops/cloudops-sonic-runtime-traffic-split/) — traffic split guide

If the parent domain's records file was found in `IFA/route53` or `IFA/domain-routing`,
the subdomain can be added there when the team is ready for the domain migration phase.

If the parent domain was NOT found in either repo, ask the user to check with the
IFA team (`#help-infra-foundations-aws`).

## Upstream Dependency Domains & Global DNS Resolution

All dependencies (services, databases, message brokers) must be resolved through **Global DNS**
(`*.jet-internal.com`) in Sonic Runtime. Platform-specific domains (e.g., `*.eks.tkwy-*.io`)
are unreachable.

> Source: [CloudOps Traffic Split: Application Readiness](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/oneeks/tasks/platform-transition/cloudops/cloudops-sonic-runtime-traffic-split/#application-readiness-in-sonic-runtime):
> *"Platform Domain Migration: Services must not use platform-specific domains (e.g.,
> `*.eks.tkwy-*.io`) to reach dependencies"*

All dependencies (databases, RabbitMQ, other services) must be accessible from Sonic Runtime
via **Global DNS** (`*.jet-internal.com`). Infrastructure services typically use the `tk-<service>`
prefix (e.g., `tk-rabbitmq.eu-west-1.production.jet-internal.com`). If a dependency is missing
from Global DNS, work with the CPS team to resolve it before migration.

### Dependency Classification

**During Phase 2 discovery**, when `*.eks.tkwy-*.io` references are found, classify each as:

| Type | Example | Action |
|------|---------|--------|
| **Own domain** (service being migrated) | `partner-management-api.ns.p.eks.tkwy-prod.io` | Replace with `*.jet-internal.com` in Phase 5 |
| **Infrastructure service** (DB, RabbitMQ, cache) | `rabbitmq.ns.p.eks.tkwy-prod.io` | Replace with `tk-<service>.{region}.{stage}.jet-internal.com` |
| **Upstream service** (another app) | `jetms-user-api.jetms.p.eks.tkwy-prod.io` | Resolve via Global DNS lookup (see below) |

### Active Resolution Procedure (Phase 4)

For each upstream dependency on a CloudOps-only domain (`*.eks.tkwy-*.io`), **actively resolve** it:

**Step 1 — Search Global DNS (Route53)**:
```bash
# Check if a *.jet-internal.com record already exists for the dependency
gh repo clone github.je-labs.com/IFA/route53 /tmp/route53 -- --depth 1
grep -r "<dependency-service-name>" /tmp/route53/ --include="*.yml"
```

**Step 2 — Search Backstage**:
```bash
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "$BACKSTAGE_BACKEND_URL/api/search/query?term=<dependency-service-name>&types%5B0%5D=techdocs" \
  | jq '.results[:3]'
```

**Step 3 — Check VirtualService in CloudOps** (if accessible):
```bash
kubectl get virtualservice <dependency-name> -n <namespace> -o yaml | grep -A5 "hosts:"
# Look for *.jet-internal.com entries alongside *.eks.tkwy-*.io entries
```

**Step 4 — Classify result**:

| Result | Action |
|--------|--------|
| `*.jet-internal.com` record found | Auto-replace in generated config |
| `tk-<service>` infrastructure entry found | Auto-replace with `tk-<service>.{region}.{stage}.jet-internal.com` |
| No Global DNS record found | Flag as `# TODO: BLOCKER` — dependency team must expose via Global DNS before cutover |

### Infrastructure Service DNS Patterns

Infrastructure services (DB, RabbitMQ, etc.) already have Global DNS entries with `tk-` prefix:

| Service | Global DNS Pattern | Example |
|---------|-------------------|---------|
| RabbitMQ | `tk-rabbitmq.{region}.{stage}.jet-internal.com` | `tk-rabbitmq.eu-west-1.staging.jet-internal.com` |
| Database | `tk-{db-name}.{region}.{stage}.jet-internal.com` | `tk-postgres.eu-west-1.production.jet-internal.com` |
| Other | `tk-{service}.{region}.{stage}.jet-internal.com` | Verify in Backstage |

If an infrastructure dependency is missing from Global DNS, contact the **CPS team** to add it
before proceeding with migration.

## Critical Rules

- DNS entries MUST match customRules/hosts in helm-core
- Records needed for ALL environments (QA, staging, AND production) — not just production
- Initial config: weight 0 for Sonic Runtime, weight 100 for CloudOps
- Identifiers: `oneeks-{service}` and `cloudops-{service}`
- `jet-external.com` does NOT need customRules (SmartGateway proxies to NG-record)
