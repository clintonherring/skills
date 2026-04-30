---
name: jet-pagerduty
description: >-
  Use this skill instead of going to PagerDuty directly when working in the JET environment. Covers all PagerDuty work at Just Eat Takeaway: querying the REST API v2 via curl + jq (list/ack/resolve/create incidents, check who is on-call, view escalation policies, list or toggle services, run analytics), and JET-specific configuration topics (Okta access, DevNull pattern, escalation policy structure, shadow rotas, support hours, re-alerting cron). Also use for managing PagerDuty configuration as code via pdconfig (Terraform) — adding a service, onboarding a new team, configuring support hours or retrigger workflows — always prefer pdconfig over manual PagerDuty UI changes. Use for routing Datadog/Prometheus alerts to PagerDuty via PlatformMetadata (PMD) integration keys. Triggers on mentions of PagerDuty, "who's on call", on-call rota, devnull, pdconfig, paging, escalation policy, PD schedule, or any request to ack/resolve/create PD incidents.
metadata:
  owner: ai-platform
---

# PagerDuty via REST API — JET Guide

This guide covers the PagerDuty REST API v2 for day-to-day operations at JET, plus JET-specific conventions.

## Getting Access

PagerDuty access is only granted to people who are on-call or need to be. If you are not going to be on the on-call rota, request the **Stakeholder** role instead (read-only, no license cost). If you are unsure, check with your team lead before requesting.

JET PagerDuty access is self-service via Okta:

1. Go to the [Okta Access Portal](https://takeaway.okta-emea.com/enduser/resource/catalog/entry/cen9wesqVsmTTBi7P0i5) to request access
2. Request the **Responder** role (standard for on-call engineers; requires manager approval)
3. Do NOT request Global Manager — that must go via EIT

Three roles exist:
| Role | Description |
|------|-------------|
| **Stakeholder** | Read-only, free (no license consumed) — for people who are not on-call |
| **Responder** | Standard on-call engineer license — only request if you will be on the rota |
| **Global Manager** | Request via EIT only |

After access is granted, install the PagerDuty mobile app and add your phone number. Configure notification rules to use **both** push notifications AND SMS/phone call — push immediately, SMS after 1–2 min, repeat up to 5 min.

## Authentication

Get your API key from **PagerDuty > My Profile > User Settings > API Access**. Use a **User API Token** (not account-level) for personal use.

```bash
export PD_API_KEY="your-token-here"
export PD_FROM_EMAIL="your@justeattakeaway.com"  # required for write operations

# Optionally persist to shell profile
echo 'export PD_API_KEY="..."' >> ~/.zshrc

# Verify
curl -s \
  -H "Authorization: Token token=$PD_API_KEY" \
  -H "Accept: application/vnd.pagerduty+json;version=2" \
  https://api.pagerduty.com/users/me | jq '.user.name'
```

All requests require:
- `Authorization: Token token=$PD_API_KEY`
- `Accept: application/vnd.pagerduty+json;version=2`
- Write operations additionally require `From: $PD_FROM_EMAIL` and `Content-Type: application/json`

## Pagination Helper

The API paginates using `offset`/`limit` (default limit 25, max 100). When `"more": true` in the response, there are additional pages. For large collections, source the bundled helper:

```bash
source scripts/pd_list.sh
# Usage: pd_list <endpoint> [query_params]
pd_list incidents "statuses[]=triggered&statuses[]=acknowledged" | jq -s '[.[].incidents[]]'
pd_list services "query=payments" | jq -s '[.[].services[]]'
```

See `scripts/pd_list.sh` for the full implementation and usage examples.

For most ad-hoc queries, `limit=100` on a single page is sufficient.

## Obtaining Resource IDs

PagerDuty endpoints take IDs (e.g. `P1234567`), not names. The standard pattern is to search or list first to get the ID, then use it in subsequent calls. Examples throughout this guide follow this pattern — look for the `_ID=$(curl ...)` assignment before the operation that uses it.

Quick lookup shortcuts:
```bash
# Incident ID from title search
curl -s -H "Authorization: Token token=$PD_API_KEY" \
  -H "Accept: application/vnd.pagerduty+json;version=2" \
  "https://api.pagerduty.com/incidents?statuses[]=triggered&limit=25" \
  | jq '.incidents[] | {id, title}'

# Service ID by name
curl -s -H "Authorization: Token token=$PD_API_KEY" \
  -H "Accept: application/vnd.pagerduty+json;version=2" \
  "https://api.pagerduty.com/services?query=my-service-name" \
  | jq '.services[] | {id, name}'

# Your own user ID
curl -s -H "Authorization: Token token=$PD_API_KEY" \
  -H "Accept: application/vnd.pagerduty+json;version=2" \
  "https://api.pagerduty.com/users/me" | jq '.user.id'
```

Where examples below use `$INCIDENT_ID`, `$SVC_ID`, `$EP_ID`, `$SCHED_ID` — resolve these with a lookup call first.

For complete curl + jq examples covering incidents, on-call/schedules, services, users & teams, and analytics, see `references/api-reference.md` → **Common Workflows** section.

## Key Principles

- **Priority vs urgency are different.** `urgency` (`high`/`low`) is distinct from priority labels (P1–P5). There is no server-side priority filter — always filter client-side with `jq 'select(.priority.name == "P1")'`.
- **Pagination matters for large datasets.** A single `limit=100` call may not return everything. Check `.more == true` and increment `offset` (use `pd_list` helper above).
- **Service IDs** — most endpoints take IDs, not names. Look up the ID first with a `?query=` search, then use the ID in subsequent calls. See the "Obtaining Resource IDs" note below.
- **Verify write operations.** All write examples pipe to `jq '.resource.status'` (or similar) so the returned state is visible immediately. Before running a bulk operation, confirm the affected IDs with a list/search call first. If a write produces an unexpected result, check the full response: re-run without the trailing `| jq` to inspect the raw JSON.

## Error Handling

| HTTP Status | Likely Cause | Fix |
|-------------|-------------|-----|
| `401 Unauthorized` | Token invalid or missing | Check `$PD_API_KEY` is set and valid |
| `403 Forbidden` | Token lacks permissions | Use a full-access User API Token |
| `404 Not Found` | Wrong resource ID | Verify ID with a list/search call first |
| `429 Too Many Requests` | Rate limited (960 req/min) | Back off and retry; avoid tight loops |
| `400 Bad Request` | Malformed request body | Check JSON structure matches API docs |

Missing `From:` header on write operations returns a `400` with message about requiring the header.

## JET PagerDuty Conventions

These are the standard patterns JET teams follow when setting up PagerDuty. **Prefer managing configuration via pdconfig (Terraform) rather than the PagerDuty UI** — see the Configuration as Code section below. The conventions here describe what the config should look like, whether set via Terraform or (as a last resort) manually.

### DevNull

`devnull@just-eat.com` is a placeholder user used to capture alerts during hours when no real engineer is on-call. Without it, PagerDuty would silently discard alerts fired into an empty schedule slot — no incident is created, and engineers coming on shift would have no record of what fired overnight.

**Why it is needed:** PagerDuty requires a schedule slot to be occupied. DevNull fills that slot, causing incidents to be created and held (DevNull never acknowledges them), while still preventing unwanted escalation.

**How it works together with support hours:**

1. **Schedule**: DevNull fills the uncovered hours layer on the on-call schedule
2. **Support hours on the service**: Configured to step urgency down to `low` outside business hours. Low-urgency incidents do not escalate beyond the current on-call (DevNull), so the team and team lead are not paged overnight
3. **Re-alerting cron** (in pdconfig): At business day start, open incidents still held by DevNull are re-triggered, paging the incoming on-call engineer

This means incidents are never lost — they are created, held by DevNull at low urgency overnight, and re-surfaced the next morning.

> **Note:** Some teams may have implemented this differently (e.g. using a maintenance window or a custom escalation policy layer). The support hours approach described above is the canonical JET pattern. When auditing a team's setup, check the service's support hours config and the escalation policy structure to understand which variant they are using.

### Escalation Policy Structure

Every team's escalation policy must have **at least 3 levels**:

| Level | Who | Escalate after |
|-------|-----|---------------|
| L1 | Primary on-call schedule (+ shadow schedule if exists) | 10 minutes |
| L2 | Everyone in the team | 5 minutes |
| L3 | Senior Tech Manager or Head of Engineering | 5 minutes, repeat 3 times |

### Shadow Rotas

For teams running on-call learning programmes, add a `team - shadow` schedule alongside the primary at L1 of the escalation policy. The shadow engineer is paged at the same time as the primary. Configure this via pdconfig.

### Non-24h Teams

For teams that are not on-call 24/7, the canonical setup (managed via pdconfig) is:
1. A `team-OutofHours` schedule with DevNull filling uncovered hours
2. A `team-OnCall` schedule for covered hours
3. Both at Layer 1 of the escalation policy
4. **Support hours** configured on the service (`use_support_hours = true` in pdconfig) so urgency steps down to `low` outside business hours — this prevents DevNull-held incidents from escalating further up the EP overnight

Overnight incidents that fire during off-hours are re-triggered at the start of the next business day — see the **Re-alerting** section below.

### Re-alerting Overnight Incidents

When a service is not covered 24/7, incidents that fire overnight won't wake anyone up (DevNull absorbs them). To ensure they get picked up the next morning, the pdconfig repo runs GitHub Actions cron workflows that re-trigger these incidents at business day start.

To add a service to this mechanism, see `references/pdconfig.md` — specifically the retrigger workflows section.

### Routing Alerts to PagerDuty via PMD

**Prefer PMD tags over any custom routing setup.** Alert routing to PagerDuty services at JET is driven by fields in your team's PlatformMetadata (PMD) entry (`Data/teams/<team-id>.json` in the PlatformMetadata repo). Do not wire up custom Alertmanager routes, Datadog routing rules, or direct integrations unless PMD cannot cover your use case.

The PMD fields for PagerDuty:

| Field | Purpose |
|-------|---------|
| `pagerduty_high_urgency_integration` | **Required for alerting.** Events API integration key for high-urgency Prometheus/Grafana alerts (Unified Alerting) |
| `pagerduty_low_urgency_integration` | Optional. Integration key for low-urgency alerts — used when a subscription name contains `low-urgency` |
| `pagerduty_integration_key_tarot_v2` | Integration key for Tarot/Datadog-based alerting (Skip/Delco) |
| `pagerduty_emergency_service_key` | PagerDuty Service ID — used by SOC Commander to reach the team during a P1 |
| `pagerduty_escalation_policy_key` | PagerDuty Escalation Policy ID — used by Backstage to link to the team's EP |
| `pagerduty_schedule_key` | PagerDuty Schedule ID — used by Backstage to link to the team's on-call schedule |

**To get the integration key:** In PagerDuty, go to your service > **Integrations** tab > **Add an integration** > select **Events API v2** > copy the key. Then add it to your PMD entry and open a PR.

Do not set deprecated fields (`pagerduty_integration_keys_for_seyren`, `pagerduty_integration_keys`, `pagerduty_infrastructure_integration`) — these are legacy and no longer used.

### Datadog Integration

For Tarot/Datadog-based alerting, add `pagerduty_integration_key_tarot_v2` to your PMD entry (see above for how to get the key). Automation then wires up Datadog → PagerDuty routing. You do **not** need to manually create Datadog monitor routing rules. If the wiring does not work or you need help setting it up, reach out in the **#help-observability** Slack channel.

## Configuration as Code (pdconfig)

JET manages PagerDuty configuration as Terraform code in the **pdconfig** repo:
`git@github.je-labs.com:PlatformObservability/pdconfig.git`

For detailed guidance on reading, modifying, and onboarding to pdconfig — including team directory structure, variable conventions, naming patterns, service defaults, and retrigger workflows — read `references/pdconfig.md`.

**Quick reference:**
- Each team has its own directory under `team/` with isolated S3 Terraform state
- To make changes: edit on a feature branch, get it reviewed, merge to main (apply runs from main only)
- To onboard a new team: copy `example-team/`, rename the state key in `initialize.tf`
- Never make changes directly in the PagerDuty UI for things managed by Terraform — they will be overwritten

## Reference Files

- `references/api-reference.md` — Key REST API endpoints with parameters, request bodies, and response shapes
- `references/pdconfig.md` — pdconfig Terraform repo: structure, conventions, retrigger workflows, onboarding
