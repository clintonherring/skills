# Traffic Split: SRE-EKS to Sonic Runtime

## Strategy Overview

Traffic split enables gradual migration with minimal risk:

1. **Deploy** the service to Sonic Runtime (0% traffic)
2. **Configure** DNS-based traffic splitting
3. **Shift** traffic gradually: 0% → 10% → 25% → 50% → 100%
4. **Monitor** at each step, rollback if issues detected
5. **Decommission** SRE-EKS deployment after 100% confirmed

## Prerequisites Before Starting Traffic Split

- [ ] Service deployed and healthy in Sonic Runtime
- [ ] All connections verified (databases, caches, dependencies)
- [ ] No Consul `.service` dependencies remaining (all migrated to GlobalDNS)
- [ ] Observability confirmed (Datadog dashboards, alerts configured)
- [ ] Health check endpoint responding
- [ ] If Consul bridge needed: `oneeks_migrated_services` configured

## Authoritative Source

Fetch the full traffic split guide from Backstage:

```bash
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "$BACKSTAGE_BACKEND_URL/api/search/query?term=sre-eks+sonic+runtime+traffic+split&types%5B0%5D=techdocs" \
  | jq '.results[:3][] | {title: .document.title, text: .document.text[:500]}'
```

## Approach 1: GlobalDNS (Route53 Weighted CNAME)

Used for `*.jet-internal.com` records (internal service-to-service traffic).

Create **weighted CNAME records** in the `IFA/route53` repository. Route53 distributes traffic based on weights.

| Phase   | SRE-EKS Weight | Sonic Weight | Action                          |
| ------- | -------------- | ------------ | ------------------------------- |
| Initial | 100            | 0            | Deploy and verify               |
| 10%     | 90             | 10           | Smoke test with live traffic    |
| 25%     | 75             | 25           | Monitor error rates and latency |
| 50%     | 50             | 50           | Extended observation (1-2 days) |
| 100%    | 0              | 100          | Full migration, monitor 1 week  |

### Route53 Configuration

Clone `IFA/route53` and explore the repo structure to find:

- The correct zone file for the service's DNS record
- Existing weighted record examples to follow the current terraform patterns

```bash
gh repo clone github.je-labs.com/IFA/route53 /tmp/route53
```

Generate two weighted CNAME records: one for SRE-EKS (weight: 100) and one for Sonic Runtime (weight: 0).

### Per-Environment Route53 Records

**Important**: If the service uses R-records (regional) or G-records (global), weighted CNAME records must be created for **ALL environments** (QA, staging, production), not just production. Each environment may have a different DNS strategy:

| Environment | Example Strategy                                             |
| ----------- | ------------------------------------------------------------ |
| QA          | R-record via Route53 (weighted CNAME in qa zone)             |
| Staging     | R-record via Route53 (weighted CNAME in staging zone)        |
| Production  | Brand domain via `IFA/domain-routing` + R-record via Route53 |

When generating Route53 changes:

1. Identify which environments use R-records or G-records (from DNS Path Discovery in Phase 4)
2. Generate weighted CNAME records for **each** applicable environment
3. Check repo readme files for guidance.
4. Follow existing input patterns in the `IFA/route53` repo for consistency
5. Each environment's zone file is typically in a separate directory — explore the repo to find the correct paths

### VirtualService Domain Update

Ensure the VirtualService in the Sonic Runtime deployment includes the traffic split domain in its `hosts` list.

## Approach 2: Brand Domain (domain-routing Repository)

Used for brand domains like `takeaway.com`, `lieferando.de`, etc.

> "Is your service accessible on a brand domain (e.g., `api.takeaway.com`, `api.lieferando.de`)?"

If yes, clone the `IFA/domain-routing` repository and explore its structure. Traffic splitting for brand domains involves **three layers**:

### 2a. Weighted Endpoint Entries

Generate weighted endpoint entries with SRE-EKS weight=100 and Sonic Runtime weight=0. Explore the repo for the current schema. Pattern:

```yaml
- name: { service-name }
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

### 2b. Cloudflare Origin Update

If the brand domain uses Cloudflare (most do), the Cloudflare DNS record's origin must eventually be updated to point to the Sonic Runtime endpoint. During the traffic split phase, the weighted endpoints handle routing, so the Cloudflare origin doesn't need to change immediately. After 100% traffic shift:

- Update `vars/records/cloudflare/{domain}.yaml`: change the CNAME `value` from the SRE-EKS origin to the Sonic Runtime SmartGateway/ingress endpoint
- The `proxied: true` setting should remain

### 2c. WAF Rule Verification

Check `vars/domains/waf.yml` for existing WAF rules referencing the service. If rules reference SRE-EKS-specific paths or origins, they may need updating:

- Path-based rules typically don't change (paths are the same on Sonic Runtime)
- Origin-based rules may need updating if they reference SRE-EKS hostnames
- Add new allow rules if the service has new paths on Sonic Runtime

### 2d. VirtualService and helm-core

The brand domain hostname must be included in:

1. The VirtualService `hosts` list in the Sonic Runtime deployment
2. The `customRules` in `cps/helm-core` for the `igw-{project}` gateway

See `05-dns-and-networking.md` for details.

## Approach 3: External API (via SmartGateway)

Used for services exposed externally via SmartGateway — i.e., services with **external internet-facing endpoints** routed through SmartGateway (Kong). This is determined by DNS Path Discovery in Phase 4, NOT simply by whether the service has a brand domain (brand domains used internally don't need SmartGateway).

**Key insight**: External API traffic flows through SmartGateway, which proxies to the service's internal NG-record (`jet-internal.com`). The Istio ingress only ever sees `jet-internal.com` host headers — `jet-external.com` does not appear on the ingress. Therefore:

- No `jet-external.com` customRules in helm-core are needed
- VirtualService hosts only contain `jet-internal.com` records
- Traffic split is handled by updating the SmartGateway config to point to the new NG-record

### Prerequisites

- SmartGateway configuration deployed and tested (see Phase 5.6)
- API specification registered in `api_specifications` repo
- Service deployed and healthy on Sonic Runtime (VirtualService with E-record + NG-record)

### Traffic Split Mechanism

For external APIs, the traffic split happens at the **SmartGateway level**, not at Route53:

1. SmartGateway config `host` currently points to SRE-EKS endpoint
2. Update `host` to Sonic Runtime NG-record (e.g., `{APP_NAME}.{project-id}.{env-type}.jet-internal.com`)
3. SmartGateway immediately routes all external traffic to Sonic Runtime

For a more gradual approach, you can also use Route53 weighted records on the `jet-external.com` public zone to split traffic between the SRE-EKS SmartGateway endpoint and a new Sonic Runtime SmartGateway endpoint. But this is less common — most teams simply update the SmartGateway config.

### SmartGateway Cutover

1. Update `host` in SmartGateway config from SRE-EKS endpoint to Sonic Runtime NG-record
2. Deploy to QA, test via SmartGateway regional endpoints
3. Deploy to staging, then production
4. All external traffic now flows through Sonic Runtime

### Rollback

Revert the SmartGateway config `host` back to the SRE-EKS endpoint and redeploy.

## Approach Selection Guide

| Current DNS                                            | Approach                                       | Traffic Split Mechanism                                           |
| ------------------------------------------------------ | ---------------------------------------------- | ----------------------------------------------------------------- |
| `*.jet-internal.com` (internal)                        | Approach 1 (GlobalDNS)                         | Route53 weighted records in private zone (`IFA/route53`)          |
| External API via SmartGateway                          | Approach 3 (SmartGateway)                      | Update SmartGateway config `host` to new NG-record                |
| Brand domain (external, via Cloudflare + SmartGateway) | Approach 2 + 3                                 | Weighted endpoints in `IFA/domain-routing` + SmartGateway         |
| Brand domain (internal, via Cloudflare direct)         | Approach 2 (Brand Domain)                      | Weighted endpoints in `IFA/domain-routing`, helm-core customRules |
| `*.tkwy.cloud` (legacy)                                | **NOT SUPPORTED** — migrate to GlobalDNS first | N/A                                                               |
| Multiple types                                         | Use appropriate approach for each domain       | Multiple repos/mechanisms                                         |

> **Note**: The approach depends on DNS Path Discovery results from Phase 4. A brand domain used only internally (no SmartGateway in the path) does not need Approach 3.

## Per-Environment DNS Strategy

Different environments may use different DNS strategies. For example:

| Environment | DNS Strategy                                   | Traffic Split Mechanism                     |
| ----------- | ---------------------------------------------- | ------------------------------------------- |
| QA          | R-record (Route53)                             | Route53 weighted CNAME                      |
| Staging     | R-record (Route53)                             | Route53 weighted CNAME                      |
| Production  | Brand domain (`IFA/domain-routing`) + R-record | Weighted endpoints + Route53 weighted CNAME |

When planning traffic split, handle each environment's DNS independently. The DNS Path Discovery in Phase 4 captures per-environment DNS details. See `05-dns-and-networking.md` for the full Per-Environment DNS Strategy reference.

## Rollback Procedure

At any point during the traffic split:

1. Set SRE-EKS weight back to **100** and Sonic Runtime weight to **0**
2. Verify traffic returns to SRE-EKS (check Datadog / monitoring)
3. Investigate and resolve the issue in Sonic Runtime
4. Resume traffic split when ready

## DNS Cutover (After 100% Traffic Shift)

Once 100% traffic runs through Sonic Runtime for at least **1 week**:

1. Update the DNS record to a **direct CNAME** (remove weighted routing)
2. Point directly to the Sonic Runtime NG-record or E-record
3. Remove the SRE-EKS weighted record

**Per-environment**: Perform DNS cutover for each environment independently. A common pattern is to cutover QA first, then staging, then production — allowing validation at each stage before proceeding.

## Decommission Checklist

After successful DNS cutover:

- [ ] No traffic flowing to SRE-EKS deployment (verify in monitoring)
- [ ] Consul bridge removed (if configured) — remove `oneeks_migrated_services` entry
- [ ] SRE-EKS deployment scaled down / deleted
- [ ] SRE-EKS namespace cleaned up
- [ ] Weighted Route53 records cleaned up (remove SRE-EKS entry)
- [ ] domain-routing entries updated (if brand domain)
- [ ] Monitoring dashboards updated to only reference Sonic Runtime
- [ ] Team documentation updated
