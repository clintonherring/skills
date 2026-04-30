# PagerDuty REST API v2 — Reference

Base URL: `https://api.pagerduty.com`

Required headers on every request:
```
Authorization: Token token=$PD_API_KEY
Accept: application/vnd.pagerduty+json;version=2
```
Write operations additionally require:
```
Content-Type: application/json
From: $PD_FROM_EMAIL
```

Pagination: responses include `"more": true/false`. Use `limit` (max 100) and `offset` to page through results.

---

## Table of Contents

- [Incidents](#incidents)
- [Escalation Policies](#escalation-policies)
- [On-Calls](#on-calls)
- [Schedules](#schedules)
- [Services](#services)
- [Users](#users)
- [Teams](#teams)
- [Analytics](#analytics)
- [Priorities](#priorities)
- [Log Entries](#log-entries)

---

## Incidents

### GET /incidents

List incidents.

| Parameter | Type | Description |
|-----------|------|-------------|
| `statuses[]` | string | `triggered`, `acknowledged`, `resolved` (repeatable) |
| `service_ids[]` | string | Filter by service ID (repeatable) |
| `user_ids[]` | string | Filter by assigned user ID (repeatable) |
| `team_ids[]` | string | Filter by team ID (repeatable) |
| `urgencies[]` | string | `high`, `low` (repeatable) |
| `since` | ISO 8601 | Start of date range (incident creation time) |
| `until` | ISO 8601 | End of date range |
| `sort_by` | string | e.g. `created_at:desc`, `resolved_at:asc` |
| `include[]` | string | Sideload related resources: `users`, `services`, `first_trigger_log_entries`, `escalation_policies`, `teams`, `assignees`, `priorities` |
| `limit` | int | Max results per page (max 100) |
| `offset` | int | Pagination offset |

Response key: `incidents`

**Example response shape:**
```json
{
  "incidents": [{
    "id": "PXXXXXXX",
    "title": "...",
    "status": "triggered",
    "urgency": "high",
    "priority": {"id": "...", "name": "P1"},
    "created_at": "2025-01-01T00:00:00Z",
    "service": {"id": "...", "summary": "checkout-api"},
    "assignments": [{"assignee": {"id": "...", "summary": "Alice Smith"}}]
  }],
  "more": false,
  "total": null
}
```

### GET /incidents/{id}

Get a single incident.

### PUT /incidents/{id}

Update an incident (ack, resolve, reassign, rename, set priority).

**Acknowledge:**
```json
{"incident": {"type": "incident_reference", "status": "acknowledged"}}
```

**Resolve:**
```json
{"incident": {"type": "incident_reference", "status": "resolved"}}
```

**Rename:**
```json
{"incident": {"type": "incident_reference", "title": "New title"}}
```

**Set priority** (get priority ID from `GET /priorities` first):
```json
{"incident": {"type": "incident_reference", "priority": {"id": "PRIORITY_ID", "type": "priority_reference"}}}
```

**Reassign to user:**
```json
{"incident": {"type": "incident_reference", "assignments": [{"assignee": {"id": "USER_ID", "type": "user_reference"}}]}}
```

### PUT /incidents

Bulk update multiple incidents in one request.

```json
{
  "incidents": [
    {"id": "P111", "type": "incident_reference", "status": "acknowledged"},
    {"id": "P222", "type": "incident_reference", "status": "resolved"}
  ]
}
```

Response key: `incidents`

### POST /incidents

Create an incident.

```json
{
  "incident": {
    "type": "incident",
    "title": "Elevated error rate on checkout",
    "service": {"id": "SVC_ID", "type": "service_reference"},
    "urgency": "high",
    "priority": {"id": "PRIORITY_ID", "type": "priority_reference"},
    "body": {"type": "incident_body", "details": "Description here"},
    "escalation_policy": {"id": "EP_ID", "type": "escalation_policy_reference"}
  }
}
```

Response key: `incident`

### GET /incidents/{id}/notes

List notes on an incident. Response key: `notes`

### POST /incidents/{id}/notes

Add a note to an incident.

```json
{"note": {"content": "Note text here"}}
```

Response key: `note`

### GET /incidents/{id}/log_entries

Get timeline log entries for an incident.

| Parameter | Type | Description |
|-----------|------|-------------|
| `is_overview` | bool | Return only high-level entries (recommended) |
| `include[]` | string | Sideload: `channels` |

Response key: `log_entries`

### GET /incidents/{id}/alerts

List alerts associated with an incident. Response key: `alerts`

---

## Escalation Policies

### GET /escalation_policies

List escalation policies.

| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | string | Filter by name (substring match) |
| `team_ids[]` | string | Filter by team ID (repeatable) |
| `include[]` | string | Sideload: `teams`, `services` |
| `limit` | int | Max 100 |
| `offset` | int | Pagination offset |

Response key: `escalation_policies`

**Example response shape:**
```json
{
  "escalation_policies": [{
    "id": "PXXXXXXX",
    "name": "Checkout - Escalation Policy",
    "escalation_rules": [
      {
        "escalation_delay_in_minutes": 10,
        "targets": [{"id": "...", "type": "schedule_reference", "summary": "Checkout - On Call"}]
      }
    ],
    "services": [{"id": "...", "summary": "checkout-api"}],
    "teams": [{"id": "...", "summary": "Checkout"}]
  }]
}
```

### GET /escalation_policies/{id}

Get a single escalation policy with full rule detail.

---

## On-Calls

### GET /oncalls

Show current on-call assignments. Use `escalation_policy_ids[]`, `schedule_ids[]`, or `user_ids[]` to scope.

| Parameter | Type | Description |
|-----------|------|-------------|
| `escalation_policy_ids[]` | string | Filter by EP ID (repeatable) |
| `schedule_ids[]` | string | Filter by schedule ID (repeatable) |
| `user_ids[]` | string | Filter by user ID (repeatable) |
| `since` | ISO 8601 | Start of window (default: now) |
| `until` | ISO 8601 | End of window |
| `include[]` | string | Sideload: `users`, `schedules`, `escalation_policies` |

Response key: `oncalls`

**Example response shape:**
```json
{
  "oncalls": [{
    "escalation_level": 1,
    "start": "2025-01-01T08:00:00Z",
    "end": "2025-01-08T08:00:00Z",
    "user": {"id": "...", "summary": "Alice Smith"},
    "schedule": {"id": "...", "summary": "Checkout - On Call"},
    "escalation_policy": {"id": "...", "summary": "Checkout - Escalation Policy"}
  }]
}
```

---

## Schedules

### GET /schedules

List schedules.

| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | string | Filter by name |
| `include[]` | string | Sideload: `schedule_layers` |
| `limit` | int | Max 100 |
| `offset` | int | Pagination offset |

Response key: `schedules`

### GET /schedules/{id}

Get a single schedule with full layer configuration.

| Parameter | Type | Description |
|-----------|------|-------------|
| `since` | ISO 8601 | Start of rendered window |
| `until` | ISO 8601 | End of rendered window |

### GET /schedules/{id}/overrides

List overrides (temporary on-call swaps) for a schedule.

| Parameter | Type | Description |
|-----------|------|-------------|
| `since` | ISO 8601 | **(required)** Start of window |
| `until` | ISO 8601 | **(required)** End of window |

Response key: `overrides`

### POST /schedules/{id}/overrides

Create an override (temporary swap).

```json
{
  "override": {
    "start": "2025-03-01T00:00:00Z",
    "end": "2025-03-02T00:00:00Z",
    "user": {"id": "USER_ID", "type": "user_reference"}
  }
}
```

---

## Services

### GET /services

List services.

| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | string | Filter by name (substring match) |
| `team_ids[]` | string | Filter by team ID (repeatable) |
| `include[]` | string | Sideload: `teams`, `escalation_policies`, `integrations` |
| `limit` | int | Max 100 |
| `offset` | int | Pagination offset |

Response key: `services`

**Example response shape:**
```json
{
  "services": [{
    "id": "PXXXXXXX",
    "name": "checkout-api",
    "status": "active",
    "escalation_policy": {"id": "...", "summary": "Checkout - Escalation Policy"},
    "teams": [{"id": "...", "summary": "Checkout"}],
    "integrations": [{"id": "...", "summary": "Events API v2", "integration_key": "..."}]
  }]
}
```

Status values: `active`, `warning`, `critical`, `maintenance`, `disabled`

### GET /services/{id}

Get a single service.

### PUT /services/{id}

Update a service (e.g. disable, change escalation policy).

**Disable:**
```json
{"service": {"type": "service_reference", "status": "disabled"}}
```

**Re-enable:**
```json
{"service": {"type": "service_reference", "status": "active"}}
```

### GET /services/{id}/integrations

List integrations for a service. Response key: `integrations`

### POST /services/{id}/integrations

Add an integration to a service (e.g. Events API v2).

```json
{
  "integration": {
    "type": "events_api_v2_inbound_integration"
  }
}
```

Response key: `integration` — contains `integration_key`

---

## Users

### GET /users

List users.

| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | string | Filter by name or email |
| `team_ids[]` | string | Filter by team membership (repeatable) |
| `include[]` | string | Sideload: `contact_methods`, `notification_rules`, `teams` |
| `limit` | int | Max 100 |
| `offset` | int | Pagination offset |

Response key: `users`

### GET /users/me

Get the currently authenticated user. Response key: `user`

### GET /users/{id}

Get a single user.

---

## Teams

### GET /teams

List teams.

| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | string | Filter by name |
| `limit` | int | Max 100 |
| `offset` | int | Pagination offset |

Response key: `teams`

### GET /teams/{id}/members

List members of a team.

| Parameter | Type | Description |
|-----------|------|-------------|
| `limit` | int | Max 100 |
| `offset` | int | Pagination offset |

Response key: `members` — each entry has `user` and `role`

---

## Analytics

### POST /analytics/raw/incidents

Get raw incident data for analysis. Requires `Content-Type: application/json`.

**Request body:**
```json
{
  "filters": {
    "created_at_start": "2025-01-01T00:00:00Z",
    "created_at_end": "2025-02-01T00:00:00Z",
    "service_ids": ["SVC_ID"],
    "team_ids": ["TEAM_ID"],
    "urgencies": ["high"],
    "priority_ids": ["PRIORITY_ID"]
  },
  "aggregate_unit": "day",
  "time_zone": "UTC",
  "limit": 1000,
  "cursor": null
}
```

All filter fields are optional. `aggregate_unit`: `hour`, `day`, `week`, `month`.

**Response shape:**
```json
{
  "data": [{
    "id": "PXXXXXXX",
    "created_at": "...",
    "resolved_at": "...",
    "service_id": "...",
    "service_name": "checkout-api",
    "team_id": "...",
    "team_name": "Checkout",
    "seconds_to_resolve": 1234,
    "seconds_to_first_ack": 456,
    "responder_count": 2,
    "escalation_count": 0,
    "priority_name": "P1"
  }],
  "response_metadata": {"cursor": null}
}
```

Pagination uses `cursor` instead of `offset`. Pass `cursor` value from `response_metadata` to fetch next page; `null` means no more pages.

### POST /analytics/metrics/incidents/services

Aggregate metrics per service (MTTA, MTTR, incident counts).

```json
{
  "filters": {
    "created_at_start": "2025-01-01T00:00:00Z",
    "created_at_end": "2025-02-01T00:00:00Z"
  },
  "aggregate_unit": "month",
  "time_zone": "UTC"
}
```

---

## Priorities

### GET /priorities

List priority levels configured in the account (P1–P5 or custom).

Response key: `priorities`

```json
{
  "priorities": [
    {"id": "PXXXXXXX", "name": "P1", "color": "...", "description": "..."},
    {"id": "PXXXXXXX", "name": "P2", "color": "...", "description": "..."}
  ]
}
```

Use priority IDs when setting priority on incidents or filtering analytics. Priority names cannot be used directly in API calls — look up the ID first.

---

## Log Entries

### GET /log_entries

Account-wide log entries (all events across the account).

| Parameter | Type | Description |
|-----------|------|-------------|
| `since` | ISO 8601 | Start of window |
| `until` | ISO 8601 | End of window |
| `is_overview` | bool | High-level entries only |
| `include[]` | string | Sideload: `incidents`, `services`, `teams`, `channels` |
| `limit` | int | Max 100 |
| `offset` | int | Pagination offset |

Response key: `log_entries`

---

## Common Workflows

Worked curl + jq examples for the most common day-to-day operations. All examples assume `$PD_API_KEY` and `$PD_FROM_EMAIL` are exported.

### Incidents

```bash
# List open incidents (triggered + acknowledged)
curl -s \
  -H "Authorization: Token token=$PD_API_KEY" \
  -H "Accept: application/vnd.pagerduty+json;version=2" \
  "https://api.pagerduty.com/incidents?statuses[]=triggered&statuses[]=acknowledged&limit=100" \
  | jq '.incidents[] | {id, title, status, urgency, created_at}'

# List open incidents for a specific service
SVC_ID=$(curl -s \
  -H "Authorization: Token token=$PD_API_KEY" \
  -H "Accept: application/vnd.pagerduty+json;version=2" \
  "https://api.pagerduty.com/services?query=my-service-name" \
  | jq -r '.services[0].id')
curl -s \
  -H "Authorization: Token token=$PD_API_KEY" \
  -H "Accept: application/vnd.pagerduty+json;version=2" \
  "https://api.pagerduty.com/incidents?statuses[]=triggered&statuses[]=acknowledged&service_ids[]=$SVC_ID&limit=100" \
  | jq '.incidents[] | {id, title, status}'

# List open P1/P2 incidents — filter client-side on priority.name
curl -s \
  -H "Authorization: Token token=$PD_API_KEY" \
  -H "Accept: application/vnd.pagerduty+json;version=2" \
  "https://api.pagerduty.com/incidents?statuses[]=triggered&statuses[]=acknowledged&limit=100" \
  | jq '[.incidents[] | select(.priority.name == "P1" or .priority.name == "P2")]'

# List incidents assigned to me
MY_ID=$(curl -s \
  -H "Authorization: Token token=$PD_API_KEY" \
  -H "Accept: application/vnd.pagerduty+json;version=2" \
  https://api.pagerduty.com/users/me | jq -r '.user.id')
curl -s \
  -H "Authorization: Token token=$PD_API_KEY" \
  -H "Accept: application/vnd.pagerduty+json;version=2" \
  "https://api.pagerduty.com/incidents?statuses[]=triggered&statuses[]=acknowledged&user_ids[]=$MY_ID&limit=100" \
  | jq '.incidents[] | {id, title, status}'

# Acknowledge an incident
curl -s -X PUT \
  -H "Authorization: Token token=$PD_API_KEY" \
  -H "Accept: application/vnd.pagerduty+json;version=2" \
  -H "Content-Type: application/json" \
  -H "From: $PD_FROM_EMAIL" \
  -d '{"incident":{"type":"incident_reference","status":"acknowledged"}}' \
  "https://api.pagerduty.com/incidents/$INCIDENT_ID" | jq '.incident.status'

# Resolve an incident
curl -s -X PUT \
  -H "Authorization: Token token=$PD_API_KEY" \
  -H "Accept: application/vnd.pagerduty+json;version=2" \
  -H "Content-Type: application/json" \
  -H "From: $PD_FROM_EMAIL" \
  -d '{"incident":{"type":"incident_reference","status":"resolved"}}' \
  "https://api.pagerduty.com/incidents/$INCIDENT_ID" | jq '.incident.status'

# Bulk acknowledge (multiple IDs at once)
curl -s -X PUT \
  -H "Authorization: Token token=$PD_API_KEY" \
  -H "Accept: application/vnd.pagerduty+json;version=2" \
  -H "Content-Type: application/json" \
  -H "From: $PD_FROM_EMAIL" \
  -d '{"incidents":[{"id":"P111","type":"incident_reference","status":"acknowledged"},{"id":"P222","type":"incident_reference","status":"acknowledged"}]}' \
  "https://api.pagerduty.com/incidents" | jq '[.incidents[] | {id, status}]'

# Create an incident
curl -s -X POST \
  -H "Authorization: Token token=$PD_API_KEY" \
  -H "Accept: application/vnd.pagerduty+json;version=2" \
  -H "Content-Type: application/json" \
  -H "From: $PD_FROM_EMAIL" \
  -d "{\"incident\":{\"type\":\"incident\",\"title\":\"Elevated error rate on checkout\",\"service\":{\"id\":\"$SVC_ID\",\"type\":\"service_reference\"},\"urgency\":\"high\"}}" \
  "https://api.pagerduty.com/incidents" | jq '{id: .incident.id, title: .incident.title}'

# Add a note to an incident
curl -s -X POST \
  -H "Authorization: Token token=$PD_API_KEY" \
  -H "Accept: application/vnd.pagerduty+json;version=2" \
  -H "Content-Type: application/json" \
  -H "From: $PD_FROM_EMAIL" \
  -d '{"note":{"content":"Investigating DB connection pool exhaustion"}}' \
  "https://api.pagerduty.com/incidents/$INCIDENT_ID/notes" | jq '.note.content'

# List notes for an incident
curl -s \
  -H "Authorization: Token token=$PD_API_KEY" \
  -H "Accept: application/vnd.pagerduty+json;version=2" \
  "https://api.pagerduty.com/incidents/$INCIDENT_ID/notes" \
  | jq '.notes[] | {created_at, content, user: .user.summary}'

# Get incident log entries (timeline)
curl -s \
  -H "Authorization: Token token=$PD_API_KEY" \
  -H "Accept: application/vnd.pagerduty+json;version=2" \
  "https://api.pagerduty.com/incidents/$INCIDENT_ID/log_entries?is_overview=true" \
  | jq '.log_entries[] | {created_at, type, summary}'

# Incidents in a date range
curl -s \
  -H "Authorization: Token token=$PD_API_KEY" \
  -H "Accept: application/vnd.pagerduty+json;version=2" \
  "https://api.pagerduty.com/incidents?since=2024-12-25T00:00:00Z&until=2025-01-01T00:00:00Z&limit=100" \
  | jq '.incidents[] | {id, title, status, created_at}'
```

### On-Call / Schedules

```bash
# Who is on-call for a service right now? (e.g. from a service URL like /service-directory/P4TR0E6)
#
# IMPORTANT: Do NOT use /oncalls?service_ids[]=<SVC_ID> — that returns the full EP member list,
# not the currently active on-call person. Always go via the escalation policy ID instead.
#
# Step 1: get the escalation policy ID for the service
EP_ID=$(curl -s \
  -H "Authorization: Token token=$PD_API_KEY" \
  -H "Accept: application/vnd.pagerduty+json;version=2" \
  "https://api.pagerduty.com/services/$SVC_ID" \
  | jq -r '.service.escalation_policy.id')

# Step 2: query /oncalls scoped to that EP — returns schedule-resolved, time-bounded results
curl -s \
  -H "Authorization: Token token=$PD_API_KEY" \
  -H "Accept: application/vnd.pagerduty+json;version=2" \
  "https://api.pagerduty.com/oncalls?escalation_policy_ids[]=$EP_ID&include[]=users&include[]=schedules" \
  | jq '[.oncalls[] | select(.escalation_level == 1) | {user: .user.name, schedule: .schedule.name, start, end}]'

# Who is on-call for an escalation policy right now?
EP_ID=$(curl -s \
  -H "Authorization: Token token=$PD_API_KEY" \
  -H "Accept: application/vnd.pagerduty+json;version=2" \
  "https://api.pagerduty.com/escalation_policies?query=Checkout" \
  | jq -r '.escalation_policies[0].id')

curl -s \
  -H "Authorization: Token token=$PD_API_KEY" \
  -H "Accept: application/vnd.pagerduty+json;version=2" \
  "https://api.pagerduty.com/oncalls?escalation_policy_ids[]=$EP_ID" \
  | jq '.oncalls[] | {level: .escalation_level, user: .user.summary, schedule: .schedule.summary}'

# Who is on-call for a specific schedule?
SCHED_ID=$(curl -s \
  -H "Authorization: Token token=$PD_API_KEY" \
  -H "Accept: application/vnd.pagerduty+json;version=2" \
  "https://api.pagerduty.com/schedules?query=My+Schedule" \
  | jq -r '.schedules[0].id')

curl -s \
  -H "Authorization: Token token=$PD_API_KEY" \
  -H "Accept: application/vnd.pagerduty+json;version=2" \
  "https://api.pagerduty.com/oncalls?schedule_ids[]=$SCHED_ID" \
  | jq '.oncalls[] | {user: .user.summary, start, end}'

# List all escalation policies
curl -s \
  -H "Authorization: Token token=$PD_API_KEY" \
  -H "Accept: application/vnd.pagerduty+json;version=2" \
  "https://api.pagerduty.com/escalation_policies?limit=100" \
  | jq '.escalation_policies[] | {id, name}'

# List all schedules
curl -s \
  -H "Authorization: Token token=$PD_API_KEY" \
  -H "Accept: application/vnd.pagerduty+json;version=2" \
  "https://api.pagerduty.com/schedules?limit=100" \
  | jq '.schedules[] | {id, name}'

# Render upcoming shifts for a schedule (next 7 days)
SINCE=$(date -u +%Y-%m-%dT%H:%M:%SZ)
UNTIL=$(date -u -v+7d +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -d '+7 days' +%Y-%m-%dT%H:%M:%SZ)
curl -s \
  -H "Authorization: Token token=$PD_API_KEY" \
  -H "Accept: application/vnd.pagerduty+json;version=2" \
  "https://api.pagerduty.com/oncalls?schedule_ids[]=$SCHED_ID&since=$SINCE&until=$UNTIL" \
  | jq '.oncalls[] | {user: .user.summary, start, end}'
```

### Services

```bash
# List all services
curl -s \
  -H "Authorization: Token token=$PD_API_KEY" \
  -H "Accept: application/vnd.pagerduty+json;version=2" \
  "https://api.pagerduty.com/services?limit=100" \
  | jq '.services[] | {id, name, status}'

# Find a service by name
curl -s \
  -H "Authorization: Token token=$PD_API_KEY" \
  -H "Accept: application/vnd.pagerduty+json;version=2" \
  "https://api.pagerduty.com/services?query=payments&limit=100" \
  | jq '.services[] | {id, name, status}'

# Disable a service (put in maintenance)
curl -s -X PUT \
  -H "Authorization: Token token=$PD_API_KEY" \
  -H "Accept: application/vnd.pagerduty+json;version=2" \
  -H "Content-Type: application/json" \
  -H "From: $PD_FROM_EMAIL" \
  -d '{"service":{"type":"service_reference","status":"disabled"}}' \
  "https://api.pagerduty.com/services/$SVC_ID" | jq '.service.status'

# Re-enable a service
curl -s -X PUT \
  -H "Authorization: Token token=$PD_API_KEY" \
  -H "Accept: application/vnd.pagerduty+json;version=2" \
  -H "Content-Type: application/json" \
  -H "From: $PD_FROM_EMAIL" \
  -d '{"service":{"type":"service_reference","status":"active"}}' \
  "https://api.pagerduty.com/services/$SVC_ID" | jq '.service.status'
```

### Users & Teams

```bash
# List all users
curl -s \
  -H "Authorization: Token token=$PD_API_KEY" \
  -H "Accept: application/vnd.pagerduty+json;version=2" \
  "https://api.pagerduty.com/users?limit=100" \
  | jq '.users[] | {id, name, email, role}'

# Find a user by email
curl -s \
  -H "Authorization: Token token=$PD_API_KEY" \
  -H "Accept: application/vnd.pagerduty+json;version=2" \
  "https://api.pagerduty.com/users?query=user@justeat.com" \
  | jq '.users[0] | {id, name, email}'

# Who is this user on-call for?
USER_ID=$(curl -s \
  -H "Authorization: Token token=$PD_API_KEY" \
  -H "Accept: application/vnd.pagerduty+json;version=2" \
  "https://api.pagerduty.com/users?query=user@justeat.com" \
  | jq -r '.users[0].id')
curl -s \
  -H "Authorization: Token token=$PD_API_KEY" \
  -H "Accept: application/vnd.pagerduty+json;version=2" \
  "https://api.pagerduty.com/oncalls?user_ids[]=$USER_ID" \
  | jq '.oncalls[] | {level: .escalation_level, schedule: .schedule.summary, start, end}'

# List all teams
curl -s \
  -H "Authorization: Token token=$PD_API_KEY" \
  -H "Accept: application/vnd.pagerduty+json;version=2" \
  "https://api.pagerduty.com/teams?limit=100" \
  | jq '.teams[] | {id, name}'
```

### Analytics

```bash
# Get raw incident analytics for a date range
curl -s -X POST \
  -H "Authorization: Token token=$PD_API_KEY" \
  -H "Accept: application/vnd.pagerduty+json;version=2" \
  -H "Content-Type: application/json" \
  -d '{"filters":{"created_at_start":"2025-01-01T00:00:00Z","created_at_end":"2025-02-01T00:00:00Z"},"aggregate_unit":"day","time_zone":"UTC"}' \
  "https://api.pagerduty.com/analytics/raw/incidents" \
  | jq '.data[] | {id, created_at, resolved_at, service_name, seconds_to_resolve}'

# Filter analytics by service
curl -s -X POST \
  -H "Authorization: Token token=$PD_API_KEY" \
  -H "Accept: application/vnd.pagerduty+json;version=2" \
  -H "Content-Type: application/json" \
  -d "{\"filters\":{\"created_at_start\":\"2025-01-01T00:00:00Z\",\"created_at_end\":\"2025-02-01T00:00:00Z\",\"service_ids\":[\"$SVC_ID\"]}}" \
  "https://api.pagerduty.com/analytics/raw/incidents" \
  | jq '[.data[] | {id, seconds_to_resolve, responder_count}]'
```
