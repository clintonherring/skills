# DNS ↔ helm-core ↔ VirtualService Consistency Validation

## Overview

After generating all changes, verify that the three layers of the routing chain are
consistent across every environment. A mismatch at any layer causes traffic to silently fail
(404 or connection refused).

## How It Works

When a client calls a DNS record (e.g., an R-record like
`app.eu-west-1.production.jet-internal.com`), the DNS resolves to the Istio ingress load balancer.
The HTTP request arrives with that hostname as the `Host` header. For the request to reach the
application:

1. **DNS** (Route53/domain-routing): The record must resolve (directly or via CNAME) to the Istio ingress
2. **helm-core**: The `igw-{project}` gateway must have a `customRules` entry matching that Host
   (except for E/NG records which are auto-provisioned via wildcard)
3. **VirtualService**: The app's VirtualService must list that Host in its `hosts` field (the
   `domains` list in state_values)

All three must be consistent.

## Records NOT Requiring customRules

E-records are auto-provisioned by the `igw-{project}` gateway wildcard.
NG-records resolve via Route53 CNAME to the E-record and are routed by the same IGW.
Neither requires explicit `customRules` in `cps/helm-core`:

- **E-record**: `{APP_NAME}.{project-id}.{env-component}.{region}.{env-type}.jet-internal.com` — auto-provisioned (IGW wildcard)
- **NG-record**: `{APP_NAME}.{project-id}.{env-type}.jet-internal.com` — needs Route53 CNAME pointing to E-record

Both only need to appear in the VirtualService `hosts` — no customRules entry required.

**Important**: NG-records are NOT auto-provisioned. You must create a CNAME in `IFA/route53`
pointing from the NG-record to the E-record before traffic will route correctly.

## Records Requiring customRules

Any other hostname on the Istio ingress requires explicit `customRules` in [`cps/helm-core`](https://github.je-labs.com/cps/helm-core):

- **R-record**: `{APP_NAME}.{region}.{env-type}.jet-internal.com`
- **G-record**: `{APP_NAME}.{env-type}.jet-internal.com`
- **Brand domains**: e.g., `api.takeaway.com`

**CRITICAL**: customRules MUST be added to the **same ingress gateway** (`igw-{project-id}`) that
serves the wildcard E-records. This is what allows NG-record and R-record CNAMEs to resolve
to the correct gateway — the DNS CNAME points to the E-record, which routes through the IGW,
and the customRules on that same IGW accept the R-record/brand hostname. If customRules are
placed on a different IGW, the CNAME chain breaks and traffic returns 404.

`jet-external.com` does NOT need customRules — external API traffic is proxied through SmartGateway
to the internal NG-record, so the Istio ingress only sees `jet-internal.com` host headers.

## Validation Procedure

**For each environment** (QA, staging, production), build a validation table:

> **DNS ↔ Routing Consistency Check**
>
> | Environment | Host | DNS (Route53/Domain-Routing) | helm-core customRules | VirtualService domains | Status |
> |-------------|------|------------------------------|----------------------|----------------------|--------|
> | Production | `app.project.pdv-5.eu-west-1.production.jet-internal.com` | E-record (auto) | Auto (igw wildcard) | Listed | OK |
> | Production | `app.project.production.jet-internal.com` | NG-record — Route53 CNAME → E-record | Auto (igw wildcard) | Listed | OK |
> | Production | `app.eu-west-1.production.jet-internal.com` | R-record CNAME → E-record | `customRules` on `igw-{project}` | Listed | OK |
> | Production | `app.takeaway.com` | Cloudflare origin CNAME | `customRules` on `igw-{project}` | Listed | OK |
> | Staging | `app.eu-west-1.staging.jet-internal.com` | R-record CNAME → E-record | `customRules` on `igw-{project}` | Listed | OK |
> | QA | `app.eu-west-1.qa.jet-internal.com` | R-record CNAME → E-record | `customRules` on `igw-{project}` | Listed | OK |

## Mismatch Detection

If any row shows a mismatch, flag it as an error and fix before creating PRs:

> "**MISMATCH**: `{host}` exists in {source} but is NOT listed in {missing-layer}. Traffic to this
> host will fail because {reason}. Fixing..."

Common mismatches and their effects:

| Missing From | Symptom | Fix |
|-------------|---------|-----|
| VirtualService `hosts` | 404 — Istio gateway accepts traffic but no VS routes it | Add host to `domains` in state_values |
| helm-core `customRules` | Connection refused — Istio gateway rejects the Host header | Add `customRules` entry for the host |
| DNS (Route53/domain-routing) | DNS resolution fails — clients can't resolve the hostname | Create the DNS record |

## SmartGateway Consistency Check (if `jet-external.com` endpoints detected)

When the service has `jet-external.com` endpoints (NOT brand domains), add a SmartGateway row to the validation table:

> | Environment | Host | SmartGateway `host` | SmartGateway `port` | SmartGateway `protocol` | Status |
> |-------------|------|---------------------|---------------------|------------------------|--------|
> | Production | `app.project.production.jet-external.com` | `app.project.production.jet-internal.com` (NG-record) | `443` | `https` | OK |

Verify for each SmartGateway environment config:
- **`host`** must be the service's **NG-record** (`jet-internal.com`) — NOT the `jet-external.com` address
- **`port`** must be `443` — SmartGateway connects via HTTPS to the Istio ingress
- **`protocol`** must be `"https"` — using `"http"` causes 301 redirects and breaks traffic

A mismatch here means external traffic enters SmartGateway but never reaches the service.

## Brand Domain Gate

**Every non-`jet-internal.com` / non-`jet-external.com` host in VirtualService `domains` must have a corresponding entry in `IFA/domain-routing` whose origin resolves to Sonic Runtime. If the origin still targets the source platform, generate a domain-routing PR to update it.** See the [official traffic split procedure](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/oneeks/tasks/platform-transition/cloudops/cloudops-sonic-runtime-traffic-split/).

## Cross-Environment Consistency

Ensure validation covers **all** environments where the service is deployed. The DNS strategy
may differ by environment (e.g., QA/staging use Route53 R-records, production uses brand domain
via domain-routing). Validate each environment independently.
