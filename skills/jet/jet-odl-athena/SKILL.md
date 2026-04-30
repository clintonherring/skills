---
name: jet-odl-athena
description: Query JET's Operational Data Lake (ODL) via AWS Athena to investigate production incidents, track deployments, look up team ownership, review security posture, analyze GitHub activity, and examine reliability and cost metrics. Use this skill when the user asks about recent deployments, production changes, who deployed what, failed deployments, deployment history for an application, team ownership of services, Wiz security issues or vulnerabilities, GitHub PR activity, infrastructure costs, reliability metrics, or any question that can be answered from the ODL. Also triggers on mentions of ODL, operational data lake, DORA metrics, deployment history, or platform metadata lookups.
metadata:
  owner: ai-platform
---

# JET Operational Data Lake (ODL)

Query JET's ODL via Athena to investigate production incidents, track deployments, look up ownership, and more.

## Prerequisites

- **jet-aws-athena skill** must be installed (provides `athena_query.sh`)
- Valid AWS credentials for the ODL account (`528757785644`)

## Quick Start

```bash
source scripts/odl_queries.sh

# What deployed to production in the last 24 hours for a specific app?
odl_recent_deployments "my-app"

# Any failed production deployments in the last 6 hours?
odl_failed_deployments 6

# What did a team deploy today?
odl_deployments_by_team "my-team" 24

# Who owns this application?
odl_app_owner "my-app"

# Open critical Wiz issues for a team
odl_wiz_issues "my-team" "CRITICAL"
```

## Database Overview

| Item | Value |
|------|-------|
| Primary database | `transformed_data` |
| Workgroup | `primary` (or `odl_athena_workgroup`) |
| AWS account | `528757785644` |
| Total tables | 75+ |

Full table schemas: see [references/schema.md](references/schema.md).

## Data Conventions

These conventions are critical for writing correct queries:

1. **Production environment filter** -- `environment.type` is inconsistent. Always use:
   ```sql
   environment.type IN ('production', 'prod', 'prd')
   ```
2. **Struct field access** -- Many tables use nested structs. Access with dot notation:
   ```sql
   SELECT application.name, deployment.start_time FROM transformed_data.all_dora_deployments
   ```
3. **Timestamps** -- `all_dora_deployments` stores times as ISO 8601 strings (compare with `>=`). GitHub tables store timestamps as Unix epoch in milliseconds (convert with `FROM_UNIXTIME(timestamp / 1000)`).
4. **Deployment statuses** -- Only two values: `success` and `fail`.
5. **Orchestrators** -- `concourse`, `sonic`, `github`, `jenkins`, `marathon`.
6. **Host technologies** -- `eks`, `ec2`, `ecs`, `s3`, `serverless`, `gke`, `cloudrun`, `helm`, etc.
7. **Wiz SCD tables** -- `wiz_issues` and `wiz_vulnerabilities` use slowly changing dimensions. Filter with `is_latest = true` for current state.
8. **No partitions on most tables** -- Always use `LIMIT` and time-range filters to control scan costs.
9. **Duplicate rows** -- `all_dora_deployments` contains duplicate rows. Always use `SELECT DISTINCT` in deployment queries.

## Helper Script Functions

Source `scripts/odl_queries.sh` to get these pre-built functions. Each sources `jet-aws-athena` automatically.

### Deployments

| Function | Description |
|----------|-------------|
| `odl_recent_deployments <app> [hours] [env]` | Recent deployments for an app (default: 24h, prod) |
| `odl_failed_deployments [hours] [env]` | All failed deployments (default: 24h, prod) |
| `odl_deployments_by_team <team> [hours] [env]` | Deployments by owning team |
| `odl_deployment_timeline <app> [days] [env]` | Deployment history for an app (default: 7d, prod) |

The `env` parameter accepts: `prod` (default, matches production/prod/prd), `all`, or a specific type like `staging`.

### Platform Metadata

| Function | Description |
|----------|-------------|
| `odl_team_info <team>` | Team details: engineers, slack, PagerDuty, Jira |
| `odl_app_owner <app>` | Application ownership, tier, repo, lifecycle |
| `odl_env_info <env>` | Environment details: AWS account, region, tags |

### Security

| Function | Description |
|----------|-------------|
| `odl_wiz_issues [team_or_resource] [severity]` | Open Wiz security issues |
| `odl_wiz_vulns [team_or_resource] [severity]` | Open Wiz vulnerabilities |

### GitHub, Reliability, Cost

| Function | Description |
|----------|-------------|
| `odl_recent_prs <repo> [days]` | Recent PRs for a repo (default: 7d) |
| `odl_reliability_summary [year]` | Monthly availability and MTTD |
| `odl_cost_by_app <app> [weeks]` | Weekly cost data (default: 4w) |

## Incident Investigation Workflow

When investigating a production incident:

1. **Identify recent deployments** near the incident time:
   ```bash
   odl_recent_deployments "suspect-app" 4
   ```

2. **Check for failed deployments** across all apps:
   ```bash
   odl_failed_deployments 4
   ```

3. **Find the owning team** and their contact info:
   ```bash
   odl_app_owner "suspect-app"
   odl_team_info "owning-team"
   ```

4. **Review deployment timeline** for patterns:
   ```bash
   odl_deployment_timeline "suspect-app" 14
   ```

5. **Check related security issues**:
   ```bash
   odl_wiz_issues "owning-team" "CRITICAL"
   ```

## Ad-hoc Queries

For questions not covered by the helper functions, write SQL against `transformed_data` directly. Source the athena helpers and use `athena_query`:

```bash
source scripts/odl_queries.sh

# Deployments by a specific user
athena_query "
  SELECT application.name, deployment.start_time, deployment.status
  FROM transformed_data.all_dora_deployments
  WHERE deployment.user LIKE '%john.doe%'
    AND deployment.start_time >= '2026-02-01'
  ORDER BY deployment.start_time DESC
  LIMIT 50
"

# Top deploying teams this week
athena_query "
  SELECT application.owners AS team, COUNT(*) AS deploy_count
  FROM transformed_data.all_dora_deployments
  WHERE deployment.start_time >= '2026-02-10'
    AND environment.type IN ('production', 'prod', 'prd')
  GROUP BY application.owners
  ORDER BY deploy_count DESC
  LIMIT 20
"

# Apps with most failed deployments
athena_query "
  SELECT application.name, COUNT(*) AS failures
  FROM transformed_data.all_dora_deployments
  WHERE deployment.status = 'fail'
    AND deployment.start_time >= '2026-01-01'
    AND environment.type IN ('production', 'prod', 'prd')
  GROUP BY application.name
  ORDER BY failures DESC
  LIMIT 20
"
```

Consult [references/schema.md](references/schema.md) for full column details on all tables.
