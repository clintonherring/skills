# Pup CLI Command Reference

Complete reference for all command groups in pup v0.35.0. Commands marked (DESTRUCTIVE) modify or delete data.

## Table of Contents

- [Core Observability](#core-observability): metrics, logs, apm, rum, events, traces, ddsql
- [Monitoring & Alerting](#monitoring--alerting): monitors, dashboards, slos, synthetics, downtime, notebooks, status-pages
- [Security & Compliance](#security--compliance): security, static-analysis, audit-logs, data-governance
- [Infrastructure & Cloud](#infrastructure--cloud): infrastructure, tags, network, cloud
- [Incident & Operations](#incident--operations): incidents, on-call, cases, error-tracking, service-catalog, scorecards, idp, investigations, fleet, workflows, change-requests
- [CI/CD & Development](#cicd--development): cicd, code-coverage
- [Organization & Access](#organization--access): users, organizations, api-keys, app-keys
- [Platform & Configuration](#platform--configuration): usage, cost, product-analytics, integrations, obs-pipelines, llm-obs, reference-tables, app-builder, misc, hamr
- [Auth & Agent](#auth--agent): acp, auth, agent, alias, skills, test, version

---

# Core Observability

## metrics

Query, list, and submit time-series metrics.

### metrics query

Query timeseries data (v2 API).

```bash
pup metrics query --query="avg:system.cpu.user{env:prod} by {host}" --from=1h
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--query` | string | | Metrics query (required) |
| `--from` | string | | Start time |
| `--to` | string | | End time |

### metrics search

Search metrics using classic query syntax (v1 API).

```bash
pup metrics search --query="avg:system.cpu.user{*}" --from=1h
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--query` | string | | Metrics query (required) |
| `--from` | string | | Start time |
| `--to` | string | | End time |

### metrics list

List available metric names.

```bash
pup metrics list --filter="system.cpu"
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--filter` | string | | Filter pattern |
| `--tag-filter` | string | | Filter by tag |

### metrics metadata get

Get metadata for a metric.

```bash
pup metrics metadata get "system.cpu.user"
```

### metrics metadata update

Update metric metadata. (DESTRUCTIVE)

```bash
pup metrics metadata update "custom.metric" --type=gauge --unit=percent
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--type` | string | | Metric type |
| `--unit` | string | | Metric unit |
| `--per-unit` | string | | Per unit |
| `--description` | string | | Description |
| `--short-name` | string | | Short name |

### metrics submit

Submit a custom metric data point. (DESTRUCTIVE)

```bash
pup metrics submit --name="custom.metric" --value=42 --tags="env:test"
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--name` | string | | Metric name (required) |
| `--value` | float | | Metric value (required) |
| `--tags` | string | | Comma-separated tags |
| `--host` | string | | Host name |
| `--type` | string | | Metric type |
| `--timestamp` | int | | Unix timestamp |
| `--interval` | int | | Interval in seconds |

### metrics tags list

List tag configurations for metrics.

```bash
pup metrics tags list --from=1h
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--from` | string | | Start time |
| `--to` | string | | End time |

## logs

Search, query, list, and aggregate log data.

**IMPORTANT**: Always pass `--storage=flex` on all log commands. JET stores the majority of logs in Flex Logs — omitting this flag queries only indexed logs and will miss most data.

### logs search

Search logs (v1 API, follows pagination).

```bash
pup logs search --query="status:error AND service:api" --from=1h --limit=100 --storage=flex
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--query` | string | | Search query (required) |
| `--from` | string | | Start time |
| `--to` | string | | End time |
| `--limit` | int | 50 | Max results (up to 1000) |
| `--sort` | string | | Sort order |
| `--index` | string | | Log index name |
| `--storage` | string | | Storage tier: indexes, online-archives, flex |

### logs query

Query logs (v2 API).

```bash
pup logs query --query="service:api AND status:error" --from=4h --storage=flex
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--query` | string | | Search query (required) |
| `--from` | string | | Start time |
| `--to` | string | | End time |
| `--limit` | int | 50 | Max results |
| `--sort` | string | | Sort order |
| `--storage` | string | | Storage tier |
| `--timezone` | string | | Timezone |

### logs list

List logs (v2 API, simple).

```bash
pup logs list --from=1h --limit=20 --storage=flex
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--from` | string | | Start time |
| `--to` | string | | End time |
| `--query` | string | | Search query |
| `--limit` | int | 50 | Max results |
| `--sort` | string | | Sort order |
| `--storage` | string | | Storage tier |

### logs aggregate

Aggregate logs (counts, distributions, statistics).

```bash
pup logs aggregate --query="*" --from=1h --compute="count" --group-by="service" --storage=flex
pup logs aggregate --query="service:api" --from=1h --compute="avg(@duration)" --group-by="@http.status_code" --storage=flex
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--query` | string | | Search query (required) |
| `--from` | string | | Start time |
| `--to` | string | | End time |
| `--compute` | string | count | Aggregation: count, avg, sum, min, max, cardinality, percentile |
| `--group-by` | string | | Group by field(s) |
| `--limit` | int | 10 | Max groups |
| `--storage` | string | | Storage tier |

### logs archives list / get / delete

Manage log archives.

```bash
pup logs archives list
pup logs archives get <archive-id>
pup logs archives delete <archive-id>   # (DESTRUCTIVE)
```

### logs custom-destinations list / get

Manage log custom destinations.

```bash
pup logs custom-destinations list
pup logs custom-destinations get <destination-id>
```

### logs metrics list / get / delete

Manage log-based metrics.

```bash
pup logs metrics list
pup logs metrics get <metric-id>
pup logs metrics delete <metric-id>     # (DESTRUCTIVE)
```

### logs restriction-queries list / get

Manage log restriction queries.

```bash
pup logs restriction-queries list
pup logs restriction-queries get <query-id>
```

## apm

APM services, entities, dependencies, and flow maps.

### apm services list

List APM services.

```bash
pup apm services list --env=production
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--env` | string | | Environment filter (required) |
| `--start` | int64 | | Start time (Unix timestamp) |
| `--end` | int64 | | End time (Unix timestamp) |

### apm services stats

List services with performance statistics.

```bash
pup apm services stats --env=prod
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--env` | string | | Environment filter |
| `--start` | int64 | | Start time (Unix timestamp) |
| `--end` | int64 | | End time (Unix timestamp) |
| `--primary-tag` | string | | Primary tag (group:value) |

### apm services operations

List operations for a service.

```bash
pup apm services operations <service-name> --env=prod
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--env` | string | | Environment filter |
| `--start` | int64 | | Start time (Unix timestamp) |
| `--end` | int64 | | End time (Unix timestamp) |
| `--primary-tag` | string | | Primary tag |
| `--primary-only` | bool | false | Only primary operations |

### apm services resources

List resources (endpoints) for a service operation.

```bash
pup apm services resources <service-name> --operation=rack.request --env=prod
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--operation` | string | | Operation name (required) |
| `--env` | string | | Environment filter |
| `--from` | int64 | | Start time (Unix timestamp) |
| `--to` | int64 | | End time (Unix timestamp) |
| `--primary-tag` | string | | Primary tag |
| `--peer-service` | string | | Peer service filter |

### apm entities list

Query APM entities.

```bash
pup apm entities list --env=prod --types=service --limit=50
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--env` | string | | Environment filter |
| `--types` | string | | Entity types (comma-separated) |
| `--include` | string | | Fields to include (comma-separated) |
| `--limit` | int | 50 | Max results |
| `--offset` | int | 0 | Page offset |
| `--start` | int64 | | Start time (Unix timestamp) |
| `--end` | int64 | | End time (Unix timestamp) |
| `--primary-tag` | string | | Primary tag |

### apm dependencies list

List service dependencies.

```bash
pup apm dependencies list --env=prod
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--env` | string | | Environment filter (required) |
| `--start` | int64 | | Start time (Unix timestamp) |
| `--end` | int64 | | End time (Unix timestamp) |
| `--primary-tag` | string | | Primary tag |

### apm flow-map

View service flow map.

```bash
pup apm flow-map --query="env:prod" --from=<unix-ts> --to=<unix-ts>
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--query` | string | | Query filter (required) |
| `--from` | int64 | | Start time (Unix timestamp) |
| `--to` | int64 | | End time (Unix timestamp) |
| `--limit` | int | 100 | Max nodes |

## rum

Real User Monitoring — apps, sessions, metrics, retention filters, playlists, heatmaps.

### rum apps list / get / create / update / delete

Manage RUM applications.

```bash
pup rum apps list
pup rum apps get --app-id=<id>
pup rum apps create --name="My App" --type=browser         # (DESTRUCTIVE)
pup rum apps update --app-id=<id> --name="New Name"        # (DESTRUCTIVE)
pup rum apps delete --app-id=<id>                          # (DESTRUCTIVE)
```

| Flag | Type | Description |
|------|------|-------------|
| `--app-id` | string | Application ID |
| `--name` | string | Application name |
| `--type` | string | Application type |

### rum sessions list / search

List or search RUM sessions.

```bash
pup rum sessions list --from=1h --limit=20
pup rum sessions search --query="@type:error" --from=1h
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--query` | string | | Search query |
| `--from` | string | | Start time |
| `--to` | string | | End time |
| `--limit` | int | | Max results |

### rum metrics list / get / create / update / delete

Manage RUM-based metrics.

```bash
pup rum metrics list
pup rum metrics get --metric-id=<id>
pup rum metrics create --name="my.metric" --event-type=view --compute="count"    # (DESTRUCTIVE)
pup rum metrics update --metric-id=<id> --compute="avg(@view.loading_time)"      # (DESTRUCTIVE)
pup rum metrics delete --metric-id=<id>                                          # (DESTRUCTIVE)
```

| Flag | Type | Description |
|------|------|-------------|
| `--metric-id` | string | Metric ID |
| `--name` | string | Metric name |
| `--event-type` | string | RUM event type |
| `--compute` | string | Aggregation function |
| `--filter` | string | Query filter |
| `--group-by` | string | Group by fields |

### rum retention-filters list / get / create / update / delete

Manage RUM retention filters.

```bash
pup rum retention-filters list
pup rum retention-filters get --filter-id=<id>
pup rum retention-filters create --name="Errors" --query="@type:error" --rate=100 --type=error   # (DESTRUCTIVE)
pup rum retention-filters update --filter-id=<id> --rate=50                                       # (DESTRUCTIVE)
pup rum retention-filters delete --filter-id=<id>                                                 # (DESTRUCTIVE)
```

| Flag | Type | Description |
|------|------|-------------|
| `--filter-id` | string | Filter ID |
| `--name` | string | Filter name |
| `--query` | string | Filter query |
| `--rate` | float | Sample rate |
| `--type` | string | Event type |
| `--enabled` | bool | Enable/disable |

### rum playlists list / get

```bash
pup rum playlists list
pup rum playlists get --playlist-id=<id>
```

### rum heatmaps query

```bash
pup rum heatmaps query --view="/checkout" --from=1h
```

| Flag | Type | Description |
|------|------|-------------|
| `--view` | string | View URL path |
| `--from` | string | Start time |
| `--to` | string | End time |

## events

Infrastructure events.

### events list

```bash
pup events list --tags="source:deploy" --start=<unix-ts> --end=<unix-ts>
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--start` | int64 | | Start timestamp |
| `--end` | int64 | | End timestamp |
| `--tags` | string | | Filter by tags |

### events search

```bash
pup events search --query="sources:pagerduty" --from=1d --limit=100
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--query` | string | | Search query |
| `--filter` | string | | Filter query |
| `--from` | string | | Start time |
| `--to` | string | | End time |
| `--limit` | int32 | 100 | Max results |

### events get

```bash
pup events get <event-id>
```

## traces

Trace commands (not yet fully implemented — use `apm` commands instead).

## ddsql

Execute DDSQL queries against Datadog data.

### ddsql table

Run a DDSQL query returning tabular results.

```bash
pup ddsql table --query="SELECT * FROM logs WHERE status='error' LIMIT 10" --from=1h
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--query` | string | | DDSQL query (required) |
| `--from` | string | | Start time |
| `--to` | string | | End time |

### ddsql time-series

Run a DDSQL query returning time-series results.

```bash
pup ddsql time-series --query="SELECT count(*) FROM logs GROUP BY service" --from=1h
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--query` | string | | DDSQL query (required) |
| `--from` | string | | Start time |
| `--to` | string | | End time |

---

# Monitoring & Alerting

## monitors

Manage monitors.

### monitors list

```bash
pup monitors list --tags="env:production" --name="CPU" --limit=500
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--tags` | string | | Filter by tags |
| `--name` | string | | Filter by name |
| `--limit` | int | 200 | Max results (max 1000) |

### monitors search

Full-text search across monitor names and queries.

```bash
pup monitors search --query="database" --per-page=50
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--query` | string | | Search query (required) |
| `--page` | int | | Page number |
| `--per-page` | int | | Results per page |
| `--sort` | string | | Sort order |

### monitors get

```bash
pup monitors get <monitor-id>
```

### monitors delete

(DESTRUCTIVE)

```bash
pup monitors delete <monitor-id> --yes
```

## dashboards

Manage dashboards.

### dashboards list

```bash
pup dashboards list
```

### dashboards get

```bash
pup dashboards get <dashboard-id>
```

### dashboards delete

(DESTRUCTIVE)

```bash
pup dashboards delete <dashboard-id> --yes
```

## slos

Service Level Objectives.

### slos list

```bash
pup slos list
```

### slos get

```bash
pup slos get <slo-id>
```

### slos status

Query SLO status (v2 API).

```bash
pup slos status <slo-id> --from=7d
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--from` | string | | Start time |
| `--to` | string | | End time |
| `--disable-corrections` | bool | | Disable SLO corrections |

### slos delete

(DESTRUCTIVE)

```bash
pup slos delete <slo-id> --yes
```

## synthetics

Synthetic monitoring tests, locations, and suites.

### synthetics tests list / get / search

```bash
pup synthetics tests list
pup synthetics tests get <test-public-id>
pup synthetics tests search --text="checkout" --count=25
```

| Flag (search) | Type | Default | Description |
|------|------|---------|-------------|
| `--text` | string | | Search text |
| `--count` | int | | Results count |
| `--start` | int | | Start offset |
| `--sort` | string | | Sort order |
| `--facets-only` | bool | | Return only facets |
| `--include-full-config` | bool | | Include full config |

### synthetics locations list

```bash
pup synthetics locations list
```

### synthetics suites list / get / create / update / delete

```bash
pup synthetics suites list --query="checkout"
pup synthetics suites get <suite-id>
pup synthetics suites create --file=suite.json    # (DESTRUCTIVE)
pup synthetics suites update --file=suite.json    # (DESTRUCTIVE)
pup synthetics suites delete --ids=<id1>,<id2>    # (DESTRUCTIVE)
```

## downtime

Monitor downtimes.

### downtime list / get / cancel

```bash
pup downtime list
pup downtime get <downtime-id>
pup downtime cancel <downtime-id>    # (DESTRUCTIVE)
```

## notebooks

Investigation notebooks.

### notebooks list / get / create / update / delete

```bash
pup notebooks list
pup notebooks get <notebook-id>
pup notebooks create --body='<json>'    # (DESTRUCTIVE)
pup notebooks update <id> --body='<json>'  # (DESTRUCTIVE)
pup notebooks delete <notebook-id>      # (DESTRUCTIVE)
```

## status-pages

Status pages, components, and degradations.

### status-pages pages list / get / create / update / delete

```bash
pup status-pages pages list
pup status-pages pages get <page-id>
pup status-pages pages create --file=page.json    # (DESTRUCTIVE)
pup status-pages pages update <id> --file=page.json  # (DESTRUCTIVE)
pup status-pages pages delete <page-id>            # (DESTRUCTIVE)
```

### status-pages components list / get / create / update / delete

```bash
pup status-pages components list
pup status-pages components get <component-id>
pup status-pages components create --file=component.json    # (DESTRUCTIVE)
pup status-pages components update <id> --file=comp.json    # (DESTRUCTIVE)
pup status-pages components delete <component-id>           # (DESTRUCTIVE)
```

### status-pages degradations list / get / create / update / delete

```bash
pup status-pages degradations list
pup status-pages degradations get <degradation-id>
pup status-pages degradations create --file=degradation.json    # (DESTRUCTIVE)
pup status-pages degradations update <id> --file=deg.json       # (DESTRUCTIVE)
pup status-pages degradations delete <degradation-id>           # (DESTRUCTIVE)
```

### status-pages third-party

```bash
pup status-pages third-party --search="aws" --active=true
```

| Flag | Type | Description |
|------|------|-------------|
| `--search` | string | Search term |
| `--active` | bool | Filter active only |

---

# Security & Compliance

## security

Security rules, signals, findings, content packs, and risk scores.

### security rules list / get / bulk-export

```bash
pup security rules list
pup security rules get <rule-id>
pup security rules bulk-export --rule-ids=<id1>,<id2>
```

### security signals list

```bash
pup security signals list
```

### security findings search

```bash
pup security findings search --query="status:critical" --limit=50
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--query` | string | | Search query |
| `--limit` | int | | Max results |
| `--sort` | string | | Sort order |

### security content-packs list / activate / deactivate

```bash
pup security content-packs list
pup security content-packs activate <pack-id>      # (DESTRUCTIVE)
pup security content-packs deactivate <pack-id>    # (DESTRUCTIVE)
```

### security risk-scores list

```bash
pup security risk-scores list --query="..."
```

## static-analysis

Code security analysis — AST, custom rulesets, SCA, coverage.

### static-analysis ast list / get

```bash
pup static-analysis ast list --repository=myorg/myrepo --branch=main --from=7d
pup static-analysis ast get <result-id>
```

| Flag | Type | Description |
|------|------|-------------|
| `--repository` | string | Repository name |
| `--branch` | string | Branch name |
| `--language` | string | Language filter |
| `--from` | string | Start time |
| `--to` | string | End time |

### static-analysis custom-rulesets list / get

```bash
pup static-analysis custom-rulesets list
pup static-analysis custom-rulesets get <ruleset-id>
```

### static-analysis sca list / get

```bash
pup static-analysis sca list --repository=myorg/myrepo --severity=critical
pup static-analysis sca get <finding-id>
```

| Flag | Type | Description |
|------|------|-------------|
| `--repository` | string | Repository name |
| `--severity` | string | Severity filter |
| `--status` | string | Status filter |

### static-analysis coverage list / get

```bash
pup static-analysis coverage list --repository=myorg/myrepo --from=7d
pup static-analysis coverage get <coverage-id>
```

## audit-logs

Audit trail.

### audit-logs list

```bash
pup audit-logs list --from=1h --limit=100
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--from` | string | 1h | Start time |
| `--to` | string | now | End time |
| `--limit` | int32 | 100 | Max results |

### audit-logs search

```bash
pup audit-logs search --query="@action:monitor.delete" --from=1d
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--query` | string | | Search query (required) |
| `--from` | string | 1h | Start time |
| `--to` | string | now | End time |
| `--limit` | int32 | 100 | Max results |

## data-governance

Sensitive data scanner.

### data-governance scanner rules list

```bash
pup data-governance scanner rules list
```

---

# Infrastructure & Cloud

## infrastructure

Host inventory.

### infrastructure hosts list

```bash
pup infrastructure hosts list --filter="env:production" --count=100 --sort="apps"
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--filter` | string | | Filter query |
| `--count` | int | | Max results |
| `--sort` | string | | Sort field |

### infrastructure hosts get

```bash
pup infrastructure hosts get <hostname>
```

## tags

Host tag management.

### tags list / get / add / update / delete

```bash
pup tags list
pup tags get <hostname>
pup tags add <hostname> <tag1>,<tag2>          # (DESTRUCTIVE)
pup tags update <hostname> <tag1>,<tag2>       # (DESTRUCTIVE)
pup tags delete <hostname>                      # (DESTRUCTIVE)
```

## network

Network monitoring.

### network flows list

```bash
pup network flows list
```

### network devices list / get / interfaces / tags

```bash
pup network devices list
pup network devices get <device-id>
pup network devices interfaces <device-id>
pup network devices tags <device-id>
```

### network interfaces list / update

```bash
pup network interfaces list
pup network interfaces update <interface-id> --file=interface.json  # (DESTRUCTIVE)
```

## cloud

Cloud provider integrations.

### cloud aws list

```bash
pup cloud aws list
```

### cloud gcp list

```bash
pup cloud gcp list
```

### cloud azure list

```bash
pup cloud azure list
```

### cloud oci tenancies list / get / create / update / delete

```bash
pup cloud oci tenancies list
pup cloud oci tenancies get <tenancy-id>
pup cloud oci tenancies create --file=tenancy.json    # (DESTRUCTIVE)
pup cloud oci tenancies update <id> --file=t.json     # (DESTRUCTIVE)
pup cloud oci tenancies delete <tenancy-id>           # (DESTRUCTIVE)
```

### cloud oci products list

```bash
pup cloud oci products list --product-keys=logs,metrics
```

---

# Incident & Operations

## incidents

Incident management.

### incidents list / get

```bash
pup incidents list
pup incidents get <incident-id>
```

### incidents attachments list / delete

```bash
pup incidents attachments list <incident-id>
pup incidents attachments delete <attachment-id>    # (DESTRUCTIVE)
```

### incidents handles list / create / update / delete

```bash
pup incidents handles list <incident-id>
pup incidents handles create <incident-id> --file=handle.json    # (DESTRUCTIVE)
pup incidents handles update <handle-id> --file=handle.json      # (DESTRUCTIVE)
pup incidents handles delete <handle-id>                          # (DESTRUCTIVE)
```

### incidents settings get / update

```bash
pup incidents settings get
pup incidents settings update --file=settings.json    # (DESTRUCTIVE)
```

### incidents postmortem-templates list / get / create / update / delete

```bash
pup incidents postmortem-templates list
pup incidents postmortem-templates get <template-id>
pup incidents postmortem-templates create --file=template.json    # (DESTRUCTIVE)
pup incidents postmortem-templates update <id> --file=t.json      # (DESTRUCTIVE)
pup incidents postmortem-templates delete <template-id>           # (DESTRUCTIVE)
```

## on-call

On-call team management.

### on-call teams list / get / create / update / delete

```bash
pup on-call teams list
pup on-call teams get <team-id>
pup on-call teams create --name="API Team" --handle="api-team"    # (DESTRUCTIVE)
pup on-call teams update <team-id> --name="New Name"              # (DESTRUCTIVE)
pup on-call teams delete <team-id>                                # (DESTRUCTIVE)
```

| Flag | Type | Description |
|------|------|-------------|
| `--name` | string | Team name |
| `--handle` | string | Team handle |
| `--description` | string | Team description |
| `--avatar` | string | Avatar URL |
| `--hidden` | bool | Hide team |

### on-call teams memberships list / add / update / remove

```bash
pup on-call teams memberships list <team-id>
pup on-call teams memberships add <team-id> --user-id=<uid> --role=member    # (DESTRUCTIVE)
pup on-call teams memberships update <membership-id> --role=admin            # (DESTRUCTIVE)
pup on-call teams memberships remove <membership-id>                          # (DESTRUCTIVE)
```

| Flag | Type | Description |
|------|------|-------------|
| `--user-id` | string | User UUID |
| `--role` | string | Role: admin, member |
| `--page-number` | int | Page number |
| `--page-size` | int | Results per page |
| `--sort` | string | Sort order |

## cases

Case management with Jira/ServiceNow integration.

### cases create / get / search

```bash
pup cases create --title="Investigate latency" --type-id=<uuid> --priority=P2    # (DESTRUCTIVE)
pup cases get <case-id>
pup cases search --query="latency" --page-size=20
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--title` | string | | Case title (required for create) |
| `--type-id` | string | | Case type UUID (required for create) |
| `--description` | string | | Case description |
| `--priority` | string | NOT_DEFINED | Priority: P1-P5, NOT_DEFINED |
| `--query` | string | | Search query |
| `--page-number` | int64 | 0 | Page number |
| `--page-size` | int64 | 10 | Results per page |

### cases assign / archive / unarchive / move / update-priority / update-title

```bash
pup cases assign <case-id> --user-id=<uuid>
pup cases archive <case-id>
pup cases unarchive <case-id>
pup cases move <case-id> --project-id=<uuid>
pup cases update-priority <case-id> --priority=P1
pup cases update-title <case-id> --title="New Title"
```

### cases projects list / get / create / update / delete

```bash
pup cases projects list
pup cases projects get <project-id>
pup cases projects create --name="My Project" --key="PROJ"    # (DESTRUCTIVE)
pup cases projects update <id> --file=project.json             # (DESTRUCTIVE)
pup cases projects delete <project-id>                         # (DESTRUCTIVE)
```

### cases projects notification-rules list / create / update / delete

```bash
pup cases projects notification-rules list <project-id>
pup cases projects notification-rules create <project-id> --file=rule.json    # (DESTRUCTIVE)
pup cases projects notification-rules update <rule-id> --file=rule.json       # (DESTRUCTIVE)
pup cases projects notification-rules delete <rule-id>                         # (DESTRUCTIVE)
```

### cases jira create-issue / link / unlink

```bash
pup cases jira create-issue <case-id> --file=jira.json
pup cases jira link <case-id> --file=link.json
pup cases jira unlink <case-id>
```

### cases servicenow create-ticket

```bash
pup cases servicenow create-ticket <case-id> --file=snow.json
```

## error-tracking

Error issue management.

### error-tracking issues search

```bash
pup error-tracking issues search --query="service:api" --from=1d --limit=10
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--query` | string | * | Search query |
| `--from` | string | 1d | Start time |
| `--to` | string | now | End time |
| `--limit` | int | 10 | Max results |
| `--order-by` | string | TOTAL_COUNT | Sort: TOTAL_COUNT, FIRST_SEEN, IMPACTED_SESSIONS, PRIORITY |

### error-tracking issues get

```bash
pup error-tracking issues get <issue-id>
```

## service-catalog

Service registry.

### service-catalog list / get

```bash
pup service-catalog list
pup service-catalog get <service-name>
```

## scorecards

Service quality scores.

### scorecards list / get

```bash
pup scorecards list
pup scorecards get <scorecard-id>
```

## idp

Internal Developer Portal — agent-native context layer for service ownership and dependency data.

### idp assist

Ask a natural-language question about services via the IDP.

```bash
pup idp assist "Who owns the checkout service?"
```

### idp find

Find a service by name.

```bash
pup idp find <service-name>
```

### idp owner

Get the owner of a service.

```bash
pup idp owner <service-name>
```

### idp deps

List dependencies of a service.

```bash
pup idp deps <service-name>
```

### idp register

Register or update a service definition. (DESTRUCTIVE)

```bash
pup idp register --file=service.json
```

| Flag | Type | Description |
|------|------|-------------|
| `--file` | string | Path to service definition JSON |

## investigations

AI-powered investigations.

### investigations list / get / trigger

```bash
pup investigations list --monitor-id=<id>
pup investigations get <investigation-id>
pup investigations trigger --monitor-id=<id> --type=monitor    # (DESTRUCTIVE)
```

| Flag | Type | Description |
|------|------|-------------|
| `--monitor-id` | string | Monitor ID |
| `--type` | string | Investigation type |
| `--event-id` | string | Event ID |
| `--event-ts` | string | Event timestamp |
| `--page-limit` | int | Page limit |
| `--page-offset` | int | Page offset |

## fleet

Fleet Automation — manage Datadog agents, deployments, and schedules.

### fleet agents list / get / versions

```bash
pup fleet agents list
pup fleet agents get <agent-id>
pup fleet agents versions
```

### fleet deployments list / get / configure / upgrade / cancel

```bash
pup fleet deployments list
pup fleet deployments get <deployment-id>
pup fleet deployments configure --file=config.json    # (DESTRUCTIVE)
pup fleet deployments upgrade --file=upgrade.json     # (DESTRUCTIVE)
pup fleet deployments cancel <deployment-id>          # (DESTRUCTIVE)
```

### fleet schedules list / get / create / update / delete / trigger

```bash
pup fleet schedules list
pup fleet schedules get <schedule-id>
pup fleet schedules create --file=schedule.json    # (DESTRUCTIVE)
pup fleet schedules update <schedule-id> --file=schedule.json  # (DESTRUCTIVE)
pup fleet schedules delete <schedule-id>           # (DESTRUCTIVE)
pup fleet schedules trigger <schedule-id>          # (DESTRUCTIVE)
```

## workflows

Workflow Automation — manage and run Datadog workflows.

### workflows get / create / update / delete

```bash
pup workflows get <workflow-id>
pup workflows create --file=workflow.json    # (DESTRUCTIVE)
pup workflows update <workflow-id> --file=workflow.json  # (DESTRUCTIVE)
pup workflows delete <workflow-id>           # (DESTRUCTIVE)
```

### workflows run

Trigger a workflow execution.

```bash
pup workflows run <workflow-id>    # (DESTRUCTIVE)
```

### workflows instances list / get / cancel

```bash
pup workflows instances list <workflow-id>
pup workflows instances get <instance-id>
pup workflows instances cancel <instance-id>    # (DESTRUCTIVE)
```

## change-requests

Change request management.

### change-requests create / get / update

```bash
pup change-requests create --file=change.json    # (DESTRUCTIVE)
pup change-requests get <change-id>
pup change-requests update <change-id> --file=change.json  # (DESTRUCTIVE)
```

### change-requests create-branch

```bash
pup change-requests create-branch <change-id> --file=branch.json    # (DESTRUCTIVE)
```

### change-requests decisions update / delete

```bash
pup change-requests decisions update <decision-id> --file=decision.json  # (DESTRUCTIVE)
pup change-requests decisions delete <decision-id>                        # (DESTRUCTIVE)
```

---

# CI/CD & Development

## cicd

CI/CD pipelines, events, tests, DORA metrics, flaky tests.

### cicd pipelines list / get

```bash
pup cicd pipelines list --from=1h --pipeline-name="deploy" --branch=main
pup cicd pipelines get --pipeline-id=<id>
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--from` | string | 1h | Start time |
| `--to` | string | now | End time |
| `--pipeline-name` | string | | Filter by pipeline name |
| `--branch` | string | | Filter by branch |
| `--pipeline-id` | string | | Pipeline ID (for get) |

### cicd events search / aggregate

```bash
pup cicd events search --query="@ci.pipeline.name:deploy" --from=1h --limit=50
pup cicd events aggregate --query="@ci.status:error" --from=1h --compute="count" --group-by="@ci.pipeline.name"
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--query` | string | | Search query (required) |
| `--from` | string | 1h | Start time |
| `--to` | string | now | End time |
| `--limit` | int32 | 50 | Max results |
| `--sort` | string | desc | Sort order |
| `--compute` | string | count | Aggregation function |
| `--group-by` | string | | Group by field(s) |

### cicd tests list / search / aggregate

```bash
pup cicd tests list --from=1h --query="@test.status:fail" --limit=50
pup cicd tests search --query="@test.name:checkout" --from=1h
pup cicd tests aggregate --query="@test.status:fail" --from=1h --compute="count" --group-by="@test.suite"
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--query` | string | | Search query |
| `--from` | string | 1h | Start time |
| `--to` | string | now | End time |
| `--limit` | int32 | 50 | Max results |
| `--sort` | string | desc | Sort order |
| `--cursor` | string | | Pagination cursor |
| `--compute` | string | count | Aggregation (aggregate only) |
| `--group-by` | string | | Group by (aggregate only) |

### cicd flaky-tests search / update

```bash
pup cicd flaky-tests search --query="@test.suite:checkout" --limit=100
pup cicd flaky-tests update --file=flaky.json    # (DESTRUCTIVE)
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--query` | string | | Search query |
| `--limit` | int64 | 100 | Max results |
| `--sort` | string | | Sort order (fqn, -fqn) |
| `--cursor` | string | | Pagination cursor |
| `--include-history` | bool | false | Include status history |

### cicd dora patch-deployment

```bash
pup cicd dora patch-deployment --file=deployment.json
```

## code-coverage

Code coverage summaries.

### code-coverage branch-summary

```bash
pup code-coverage branch-summary --repo=myorg/myrepo --branch=main
```

| Flag | Type | Description |
|------|------|-------------|
| `--repo` | string | Repository name (required) |
| `--branch` | string | Branch name (required) |

### code-coverage commit-summary

```bash
pup code-coverage commit-summary --repo=myorg/myrepo --commit=abc123
```

| Flag | Type | Description |
|------|------|-------------|
| `--repo` | string | Repository name (required) |
| `--commit` | string | Commit SHA (required) |

---

# Organization & Access

## users

User management.

### users list / get

```bash
pup users list
pup users get <user-id>
```

### users roles list

```bash
pup users roles list
```

### users seats

```bash
pup users seats
```

## organizations

Organization settings.

### organizations list / get

```bash
pup organizations list
pup organizations get <org-id>
```

## api-keys

API key management.

### api-keys list / get / create / delete

```bash
pup api-keys list
pup api-keys get <key-id>
pup api-keys create --name="My Key"    # (DESTRUCTIVE)
pup api-keys delete <key-id>           # (DESTRUCTIVE)
```

## app-keys

Application key management.

### app-keys list / get / create / update / delete

```bash
pup app-keys list --page-size=20
pup app-keys get <key-id>
pup app-keys create --name="My Key"           # (DESTRUCTIVE)
pup app-keys update <key-id> --name="New Name"  # (DESTRUCTIVE)
pup app-keys delete <key-id>                   # (DESTRUCTIVE)
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--page-number` | int64 | 0 | Page number (0-indexed) |
| `--page-size` | int64 | 10 | Results per page |

---

# Platform & Configuration

## usage

Usage and billing metrics.

### usage summary

```bash
pup usage summary --start=2024-01 --end=2024-06
```

| Flag | Type | Description |
|------|------|-------------|
| `--start` | string | Start month |
| `--end` | string | End month |

### usage hourly

```bash
pup usage hourly --start=2024-01-01 --end=2024-01-02
```

## cost

Cost management.

### cost projected

```bash
pup cost projected
```

### cost attribution

```bash
pup cost attribution --start-month=2024-01 --fields="team,service"
```

| Flag | Type | Description |
|------|------|-------------|
| `--start-month` | string | Start month YYYY-MM (required) |
| `--end-month` | string | End month YYYY-MM |
| `--fields` | string | Tag keys for breakdown (required) |

### cost by-org

```bash
pup cost by-org --start-month=2024-01 --view=actual
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--start-month` | string | | Start month YYYY-MM (required) |
| `--end-month` | string | | End month YYYY-MM |
| `--view` | string | actual | View type: actual, estimated, historical |

### cost aws-config / azure-config / gcp-config

Manage cloud cost integration configs.

```bash
pup cost aws-config list
pup cost aws-config get <config-id>
pup cost aws-config create --file=config.json    # (DESTRUCTIVE)
pup cost aws-config delete <config-id>           # (DESTRUCTIVE)

pup cost azure-config list
pup cost azure-config get <config-id>
pup cost azure-config create --file=config.json  # (DESTRUCTIVE)
pup cost azure-config delete <config-id>         # (DESTRUCTIVE)

pup cost gcp-config list
pup cost gcp-config get <config-id>
pup cost gcp-config create --file=config.json    # (DESTRUCTIVE)
pup cost gcp-config delete <config-id>           # (DESTRUCTIVE)
```

## product-analytics

Server-side product analytics.

### product-analytics events send

```bash
pup product-analytics events send --app-id=<id> --event="checkout" --user-id=<uid>
```

| Flag | Type | Description |
|------|------|-------------|
| `--app-id` | string | Application ID |
| `--event` | string | Event name |
| `--user-id` | string | User ID |
| `--properties` | string | Event properties (JSON) |

### product-analytics query

Query scalar or time-series product analytics data.

```bash
pup product-analytics query --app-id=<id> --query="..." --from=7d
```

| Flag | Type | Description |
|------|------|-------------|
| `--app-id` | string | Application ID |
| `--query` | string | Analytics query |
| `--from` | string | Start time |
| `--to` | string | End time |

## integrations

Third-party integrations.

### integrations slack list

```bash
pup integrations slack list
```

### integrations pagerduty list

```bash
pup integrations pagerduty list
```

### integrations webhooks list

```bash
pup integrations webhooks list
```

### integrations jira accounts list / delete

```bash
pup integrations jira accounts list
pup integrations jira accounts delete <account-id>    # (DESTRUCTIVE)
```

### integrations jira templates list / get / create / update / delete

```bash
pup integrations jira templates list
pup integrations jira templates get <template-id>
pup integrations jira templates create --file=template.json    # (DESTRUCTIVE)
pup integrations jira templates update <id> --file=t.json      # (DESTRUCTIVE)
pup integrations jira templates delete <template-id>           # (DESTRUCTIVE)
```

### integrations servicenow instances / templates / users / assignment-groups / business-services

```bash
pup integrations servicenow instances list
pup integrations servicenow templates list
pup integrations servicenow templates get <id>
pup integrations servicenow templates create --file=t.json    # (DESTRUCTIVE)
pup integrations servicenow templates update <id> --file=t.json  # (DESTRUCTIVE)
pup integrations servicenow templates delete <id>              # (DESTRUCTIVE)
pup integrations servicenow users list
pup integrations servicenow assignment-groups list
pup integrations servicenow business-services list
```

## obs-pipelines

Observability pipelines — full CRUD.

### obs-pipelines list / get / create / update / delete / validate

```bash
pup obs-pipelines list
pup obs-pipelines get <pipeline-id>
pup obs-pipelines create --file=pipeline.json    # (DESTRUCTIVE)
pup obs-pipelines update <pipeline-id> --file=pipeline.json  # (DESTRUCTIVE)
pup obs-pipelines delete <pipeline-id>           # (DESTRUCTIVE)
pup obs-pipelines validate --file=pipeline.json
```

## llm-obs

LLM Observability — manage projects, experiments, and datasets.

### llm-obs projects list / create

```bash
pup llm-obs projects list
pup llm-obs projects create --name="My Project"    # (DESTRUCTIVE)
```

### llm-obs experiments list / create / update / delete

```bash
pup llm-obs experiments list --project-id=<id>
pup llm-obs experiments create --project-id=<id> --file=experiment.json  # (DESTRUCTIVE)
pup llm-obs experiments update <experiment-id> --file=experiment.json    # (DESTRUCTIVE)
pup llm-obs experiments delete <experiment-id>                           # (DESTRUCTIVE)
```

### llm-obs datasets list / create

```bash
pup llm-obs datasets list --project-id=<id>
pup llm-obs datasets create --project-id=<id> --file=dataset.json    # (DESTRUCTIVE)
```

## reference-tables

Reference tables for log enrichment.

### reference-tables list / get / create / batch-query

```bash
pup reference-tables list
pup reference-tables get <table-id>
pup reference-tables create --file=table.json    # (DESTRUCTIVE)
pup reference-tables batch-query --file=query.json
```

## app-builder

Low-code app management.

### app-builder list / get / create / update / delete / publish / unpublish

```bash
pup app-builder list
pup app-builder get <app-id>
pup app-builder create --file=app.json            # (DESTRUCTIVE)
pup app-builder update <app-id> --file=app.json   # (DESTRUCTIVE)
pup app-builder delete <app-id>                   # (DESTRUCTIVE)
pup app-builder delete-batch --ids=<id1>,<id2>    # (DESTRUCTIVE)
pup app-builder publish <app-id>                  # (DESTRUCTIVE)
pup app-builder unpublish <app-id>                # (DESTRUCTIVE)
```

## misc

Miscellaneous utilities.

### misc ip-ranges

```bash
pup misc ip-ranges
```

### misc status

```bash
pup misc status
```

## hamr

High Availability Multi-Region connections.

### hamr connections get / create

```bash
pup hamr connections get <connection-id>
pup hamr connections create --file=connection.json    # (DESTRUCTIVE)
```

---

# Auth & Agent

## acp

Local ACP server and OpenAI-compatible proxy to Datadog Bits AI.

### acp serve

Start a local ACP + OpenAI-compatible server that proxies requests to Datadog Bits AI.

```bash
pup acp serve
pup acp serve --port=8080
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--port` | int | 3000 | Port to listen on |

## auth

OAuth2 authentication.

### auth login / logout / status / refresh

```bash
pup auth login       # Opens browser for OAuth2 login
pup auth logout      # Clear stored tokens
pup auth status      # Check authentication status
pup auth refresh     # Refresh access token
```

## agent

Agent tooling for AI coding assistants.

### agent guide

Output the comprehensive steering guide.

```bash
pup agent guide
```

### agent schema

Output command schema as JSON.

```bash
pup agent schema
pup agent schema --compact    # Minimal schema (names + flags only)
```

## alias

Command shortcuts.

### alias list / set / delete / import

```bash
pup alias list
pup alias set <name> <command>     # (DESTRUCTIVE)
pup alias delete <name>            # (DESTRUCTIVE)
pup alias import <yaml-file>       # (DESTRUCTIVE)
```

## skills

Manage and install pup agent skills.

### skills list

```bash
pup skills list
pup skills list --type=skill
pup skills list --type=agent
```

### skills install

Install skills into your AI coding assistant.

```bash
pup skills install
pup skills install --target-agent=claude-code
pup skills install --target-agent=cursor
pup skills install dd-monitors    # Install a specific skill
```

### skills path

```bash
pup skills path
```

## test

Test connection to Datadog API.

```bash
pup test
```

## version

Print pup version.

```bash
pup version
```

---

# Global Flags

Available on all commands:

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--output` / `-o` | string | json | Output format: json, table, yaml, csv |
| `--yes` / `-y` | bool | false | Skip confirmation prompts |
| `--agent` | bool | false | Enable agent mode (auto-detected for AI assistants) |
| `--org` | string | | Target a specific Datadog organisation (multi-org) |
| `--config` | string | ~/.config/pup/config.yaml | Config file path |
| `--site` | string | datadoghq.com | Datadog site |
| `--verbose` | bool | false | Enable verbose logging |
| `--read-only` | bool | false | Block all write operations (create, update, delete) |
