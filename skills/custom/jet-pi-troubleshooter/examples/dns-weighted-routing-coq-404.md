# DNS Weighted Routing Migration Causes Downstream 404s

## PI Ticket
[PI-33757](https://justeattakeaway.atlassian.net/browse/PI-33757) -- "UK, ES - Compensation tool not working in OM"

## Date
2026-05-05

## Symptom Type
DNS / Weighted Routing, Downstream Service Failures

## Affected Markets
UK, ES (INT Marketplace)

## Severity / Category
Infra -- Maintenance (Correct)

## Triggers
- CS UK reported compensation tool not working in Order Management (OM)
- CS ES confirmed same issue
- `consumerhelpapi` throwing unhandled `Refit.ApiException: 404 (Not Found)` errors in production
- Errors on calls to `consumerorderqueriesapi.je-apis.com` and `consumerorderqueriesapi-i18n-production.justeat-int.com`
- Multiple consumers/tenants affected simultaneously (UK, ES)
- SOC notified of route53 changes in progress

## Timeline

| Time (BST) | Event |
|------------|-------|
| 07:53 | PR #1145 opened in `IFA/route53` -- change `consumerorderqueriesapi` from 100% ELB / 0% Istio to 50/50 (ticket BCOB-3283) |
| 08:25 | Atlantis plan run by `ori-gilgun` (PR author `roman-kormysh` lacked route53 write permissions) |
| 08:37 | Atlantis apply -- DNS weights changed to 50/50 for both `je-apis.com` and `justeat-int.com` zones |
| ~08:38 | PR #1145 merged |
| 09:48 | SOC (Mauro Montisci) received report from CS UK that compensation tool not working |
| 10:05 | SOC received report from CS ES -- same issue |
| 10:19 | SOC raised PI-33757 and paged `payments-processing` |
| 10:23 | Tim Jongsma identified possible link to COQ migration |
| 10:24 | Teymur confirmed errors on `consumerhelpapi` side, preparing revert |
| 10:25 | Roman Kormysh opened revert PR #1148 |
| 10:28 | Atlantis plan for revert (run by `devdas-bhagat` -- `roman-kormysh` blocked by permissions) |
| 10:31 | Revert applied -- weights restored to 100% ELB / 0% Istio |
| 10:35 | Matthew McCouaig identified root cause: `consumerorderqueriesapi.je-apis.com` host not in Istio configs or helmfile state values |
| 10:39 | Mark Dominy provided list of all host-headers the service needs to support before re-attempting DNS split |
| 10:47 | Keah Peters scaled up/down `consumerhelpapi` to force new boxes (flush DNS cache) |
| 10:49 | Teymur confirmed no new errors since 10:49 |
| 10:50 | CS ES confirmed resolved; CS UK intermittent issues persist |
| 11:28 | CS UK still had 20+ agents with intermittent issues after clearing caches

## What Changed

**PR #1145** (`BCOB-3283: change prod coq to 50/50 between elb and istio`):

Two zones affected:
- `justeat-int.com` zone (`Z1OAKJ4TBFDJC5`):
  - `consumerorderqueriesapi-i18n-production.justeat-int.com` CNAME `l-je`: 100 -> 50
  - `consumerorderqueriesapi-i18n-production.justeat-int.com` CNAME `oneeks`: 0 -> 50
- `je-apis.com` zone (`Z2C0KXD7FKZDJF`):
  - `consumerorderqueriesapi-production.je-apis.com` CNAME `l-je`: 100 -> 50
  - `consumerorderqueriesapi-production.je-apis.com` CNAME `oneeks`: 0 -> 50

**PR #1148** (Revert):
- Reversed all weights back to 100% `l-je` / 0% `oneeks`

## Error Signature

From Datadog (`consumerhelpapi` service, production):

```
HTTP request to "GET" https://consumerorderqueriesapi.je-apis.com/uk/orders/{orderId}/baditemsqueries/{queryId}
failed with status code NotFound. Content: ""
```

Stack trace:
```
Refit.ApiException: Response status code does not indicate success: 404 (Not Found).
  at ...IConsumerOrderQueriesClient.GetBadItemsQuery(...)
  at JustEat.ConsumerHelpApi.Services.BadItemsService.GetQuery(...)
  at JustEat.ConsumerHelpApi.Controllers.BadItemsFlowController.OfflineCompensationRequestSummary(...)
```

Key attributes:
- `service: consumerhelpapi` (the **downstream** consumer, not the service that was changed)
- `Uri` field points to `consumerorderqueriesapi.je-apis.com` (the service whose DNS was changed)
- `StatusCode: NotFound` (404)
- Multiple distinct order IDs affected -- not a data issue, a routing issue

## Investigation Steps (What the Troubleshooter Should Do)

### Step 1: Identify the failing upstream service from error logs

The error logs in `consumerhelpapi` contain the `Uri` field showing the failing call:
```
https://consumerorderqueriesapi.je-apis.com/uk/orders/{orderId}/baditemsqueries/{queryId}
```

The failing service is `consumerorderqueriesapi`, not `consumerhelpapi`. This is a **downstream symptom**.

### Step 2: Check for DNS/route53 changes to the failing service domain

```bash
gh search prs --repo github.je-labs.com/IFA/route53 "consumerorderqueriesapi" --merged --sort updated --limit 5
```

Or search for recent PRs in the route53 repo:
```bash
gh pr list -R github.je-labs.com/IFA/route53 --state merged --limit 10 --json title,mergedAt,number
```

### Step 3: Examine the route53 PR and Atlantis plan output

```bash
gh pr view <PR_NUMBER> -R github.je-labs.com/IFA/route53 --json title,body,comments,mergedAt,files
```

Look for:
- `weighted_routing_policy` changes in the Atlantis plan output
- Weight shifts between `l-je` (ELB/legacy) and `oneeks` (Istio/OneEKS) set identifiers
- The Atlantis apply timestamp vs. when errors started

### Step 4: Check if the OneEKS endpoint serves the same API surface

```bash
# Check for errors on the consumerorderqueriesapi service itself
pup logs search --query='jet_env:"production" AND service:"consumerorderqueriesapi" AND status:error' \
  --from=4h --limit=20 --storage=flex
```

If the OneEKS deployment doesn't have the same routes configured (e.g., missing VirtualService routes, different API version), requests routed to it will 404.

### Step 5: Verify the revert restores service

After the revert PR is applied, monitor error rates:
```bash
pup logs aggregate --query='jet_env:"production" AND service:"consumerhelpapi" AND @Level:"Error"' \
  --from=2h --compute="count" --group-by="@Level" --storage=flex
```

## Root Cause

The host `consumerorderqueriesapi.je-apis.com` was **not configured in the Istio gateway** ([istio-gateways.yaml.gotmpl](https://github.je-labs.com/cps/helm-core/blob/8f8ec6f55ad3d3e25c0debfbbf7c81dfb86a27d1/clusters/euw1-pdv-prd-6/releases/istio-gateways.yaml.gotmpl#L695-L697)) or in the [helmfile state values](https://github.je-labs.com/operations-order-management-ta/ConsumerOrderQueries/blob/44b765ff73e25bae370db48598f1368a9bfd9b2c/helmfile.d/state_values/euw1-pdv-prd-6.yaml#L4-L6). The OneEKS deployment only recognized the `-production` variant (`consumerorderqueriesapi-production.je-apis.com`) but not the bare hostname (`consumerorderqueriesapi.je-apis.com`).

When DNS weighted routing shifted 50% of traffic to OneEKS, requests arriving with the `consumerorderqueriesapi.je-apis.com` Host header got 404s from Istio because no VirtualService matched that host. The `-production` variant returned 200s.

Additionally, `ordermanagementapi` was sending requests with incorrect host headers (its own name instead of `consumerorderqueriesapi`), which also needed fixing.

**Post-revert residual impact**: Even after the DNS revert, `consumerhelpapi` instances cached the old DNS resolution. Scale-up/scale-down (forcing new instances) was needed to flush the cached resolution. CS UK agents still experienced intermittent issues for ~40 minutes after due to local DNS/browser caching.

## Key Insights

1. **Errors appear in the downstream consumer, not the service being changed** -- `consumerhelpapi` logged the errors, but the root cause was a DNS change to `consumerorderqueriesapi`. Always trace the `Uri` field in HTTP error logs to identify the actual affected service.

2. **Host header mismatch is the real issue, not missing routes** -- The OneEKS deployment served `consumerorderqueriesapi-production.je-apis.com` correctly, but the bare `consumerorderqueriesapi.je-apis.com` was not in the Istio gateway config. Check `cps/helm-core` istio-gateways and the app's helmfile state values for host lists.

3. **Weighted routing changes are immediate but DNS caching delays recovery** -- The weight change took effect immediately, but even after reverting, application instances and client browsers cached the old DNS. Scale up/down was needed to flush server-side caching, and CS agents needed to clear browser caches.

4. **Permission model slows reverts** -- The PR author (`roman-kormysh`) could not run Atlantis plan/apply in `IFA/route53` (permission check failed). The revert required someone with write access (`devdas-bhagat`) to trigger Atlantis. This added ~10 minutes to the revert timeline.

5. **SOC notification is a signal** -- When SOC is notified about route53 changes ("Hello Soc, we're making some changes to route53"), this is a strong indicator that infrastructure changes are happening that could correlate with errors appearing shortly after.

6. **Check all host-headers before re-attempting traffic split** -- Use Datadog to find all host headers currently hitting a service (IIS logs grouped by `@cs-host`). All must be configured in the Istio gateway before shifting traffic. Other services may send incorrect headers (e.g., `ordermanagementapi` sending its own host header instead of `consumerorderqueriesapi`).

7. **~70 minute gap between change and PI raise** -- The DNS change was applied at 08:37, but SOC didn't receive the CS report until 09:48. The troubleshooter must look back further than the PI start time to find the causal change.

## Resolution Pattern
1. Identify the failing upstream URI from downstream error logs
2. Search `IFA/route53` for recent merges affecting that domain
3. Confirm the weight shift timeline correlates with error onset
4. Revert the route53 PR to restore 100% traffic to the working endpoint
5. Investigate why the OneEKS endpoint isn't serving the expected routes before re-attempting the migration

## Datadog Queries Used

```bash
# Downstream errors in the consumer
pup logs search --query='jet_env:"production" AND service:"consumerhelpapi" AND (@Level:"Error")' \
  --from=72h --limit=20 --storage=flex

# Error rate aggregation
pup logs aggregate --query='jet_env:"production" AND service:"consumerhelpapi" AND @Level:"Error"' \
  --from=4h --compute="count" --group-by="service" --storage=flex

# Upstream service errors
pup logs search --query='jet_env:"production" AND service:"consumerorderqueriesapi" AND status:error' \
  --from=4h --limit=20 --storage=flex
```

## GitHub Commands Used

```bash
# View the original change PR
gh pr view 1145 -R github.je-labs.com/IFA/route53 --json title,body,comments,mergedAt,files,reviews

# View the revert PR
gh pr view 1148 -R github.je-labs.com/IFA/route53 --json title,body,comments,mergedAt,files,state
```
