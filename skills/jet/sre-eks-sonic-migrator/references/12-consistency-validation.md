# DNS ↔ helm-core ↔ VirtualService Consistency Validation

## Overview

After generating all changes in Phase 5, verify that the three layers of the routing chain are
consistent across every environment. A mismatch at any layer causes traffic to silently fail
(404 or connection refused).

## How It Works

When a client calls a DNS record (e.g., an R-record like
`app.eu-west-1.production.jet-internal.com`), the DNS resolves to the Istio ingress load balancer.
The HTTP request arrives with that hostname as the `Host` header. For the request to reach the
application:

1. **DNS** (Route53/domain-routing): The record must resolve (directly or via CNAME) to the Istio
   ingress
2. **helm-core**: The `igw-{project}` gateway must have a `customRules` entry matching that Host
   (except for E/NG records which are auto-provisioned via wildcard)
3. **VirtualService**: The app's VirtualService must list that Host in its `hosts` field (the
   `domains` list in state_values)

All three must be consistent.

## Auto-Provisioned Records (No customRules Needed)

E-records and NG-records are auto-provisioned by the `igw-{project}` gateway wildcard:

- **E-record**: `{APP_NAME}.{project-id}.{env-component}.{region}.{env-type}.jet-internal.com`
- **NG-record**: `{APP_NAME}.{project-id}.{env-type}.jet-internal.com`

These only need to appear in the VirtualService `hosts` — no customRules entry required.

## Records Requiring customRules

Any other hostname on the Istio ingress requires explicit `customRules` in `cps/helm-core`:

- **R-record**: `{APP_NAME}.{region}.{env-type}.jet-internal.com`
- **G-record**: `{APP_NAME}.{env-type}.jet-internal.com`
- **Brand domains**: e.g., `api.takeaway.com`

`jet-external.com` does NOT need customRules — external API traffic is proxied through SmartGateway
to the internal NG-record, so the Istio ingress only sees `jet-internal.com` host headers.

## Validation Procedure

**For each environment** (QA, staging, production), build a validation table:

> **DNS ↔ Routing Consistency Check**
>
> | Environment | Host                                                               | DNS (Route53/Domain-Routing) | helm-core customRules            | VirtualService domains | Status |
> | ----------- | ------------------------------------------------------------------ | ---------------------------- | -------------------------------- | ---------------------- | ------ |
> | Production  | `app.cu-order-reviews.pdv-5.eu-west-1.production.jet-internal.com` | E-record (auto)              | Auto (igw wildcard)              | Listed                 | OK     |
> | Production  | `app.cu-order-reviews.production.jet-internal.com`                 | NG-record (auto)             | Auto (igw wildcard)              | Listed                 | OK     |
> | Production  | `app.eu-west-1.production.jet-internal.com`                        | R-record CNAME → E-record    | `customRules` on `igw-{project}` | Listed                 | OK     |
> | Production  | `app.takeaway.com`                                                 | Cloudflare origin CNAME      | `customRules` on `igw-{project}` | Listed                 | OK     |
> | Staging     | `app.eu-west-1.staging.jet-internal.com`                           | R-record CNAME → E-record    | `customRules` on `igw-{project}` | Listed                 | OK     |
> | QA          | `app.eu-west-1.qa.jet-internal.com`                                | R-record CNAME → E-record    | `customRules` on `igw-{project}` | Listed                 | OK     |

## Mismatch Detection

If any row shows a mismatch (e.g., host in Route53 but missing from customRules or VirtualService),
flag it as an error and fix before proceeding to Phase 5.5:

> "**MISMATCH**: `{host}` exists in {source} but is NOT listed in {missing-layer}. Traffic to this
> host will fail because {reason}. Fixing..."

Common mismatches and their effects:

| Missing From                 | Symptom                                                    | Fix                                   |
| ---------------------------- | ---------------------------------------------------------- | ------------------------------------- |
| VirtualService `hosts`       | 404 — Istio gateway accepts traffic but no VS routes it    | Add host to `domains` in state_values |
| helm-core `customRules`      | Connection refused — Istio gateway rejects the Host header | Add `customRules` entry for the host  |
| DNS (Route53/domain-routing) | DNS resolution fails — clients can't resolve the hostname  | Create the DNS record                 |

## Cross-Environment Consistency

Ensure the validation covers **all** environments where the service is deployed. The DNS strategy
may differ by environment (e.g., QA/staging use Route53 R-records, production uses brand domain
via domain-routing). Validate each environment independently.

## Same Ingress Validation

In addition to the three-layer consistency check above, verify that **customRules are on the same
ingress** as the project's `igw-{project}` wildcard rules in `istio-gateways.yaml.gotmpl`.

Each ingress entry in the file creates a separate AWS ALB. R-records and G-records CNAME to the
E-record, which resolves to the ALB of the igw wildcard's ingress. If customRules are placed on
a different ingress, the CNAME chain delivers traffic to the wrong ALB.

**Validation step**: For each cluster's `istio-gateways.yaml.gotmpl`, confirm:

1. Find the ingress entry containing the `igw-{project}` gateway wildcard (matches `*.{project}.*.jet-internal.com`)
2. Verify that ALL `customRules` for this project are under that **same** ingress entry
3. If customRules appear under a different ingress entry, flag as an error:

> "**MISMATCH**: customRules for `{host}` are on a different ingress than the `igw-{project}`
> wildcard. This creates a separate ALB — R-record/G-record CNAME chains will resolve to the
> wrong ALB and traffic will not reach the service. Move the customRules to the same ingress
> as `igw-{project}`."
