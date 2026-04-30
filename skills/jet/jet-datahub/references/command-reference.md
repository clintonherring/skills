# DataHub CLI & REST API Command Reference

Complete reference for DataHub operations used by this skill. Uses `datahub` CLI v1.0.0 for entity lookups and `curl` against the GMS REST API for search and lineage.

---

## Table of Contents

- [Auth Setup for curl](#auth-setup-for-curl)
- [Search (REST API)](#search-rest-api)
- [datahub get](#datahub-get)
- [datahub exists](#datahub-exists)
- [datahub timeline](#datahub-timeline)
- [datahub version](#datahub-version)
- [Lineage (REST API)](#lineage-rest-api)
- [Filter Patterns](#filter-patterns)
- [Aspect Reference](#aspect-reference)
- [URN Reference](#urn-reference)

---

## Auth Setup for curl

Load credentials from `~/.datahubenv` before running `curl` commands:

```bash
DATAHUB_GMS_URL=$(grep server ~/.datahubenv | awk '{print $2}')
DATAHUB_GMS_TOKEN=$(grep token ~/.datahubenv | awk '{print $2}')
```

Or set them directly:

```bash
export DATAHUB_GMS_URL="https://datahub.just-data.io/api/gms"
export DATAHUB_GMS_TOKEN="<your-token>"
```

All `curl` examples below assume these variables are set.

---

## Search (REST API)

The CLI v1.0.0 does not include a `search` subcommand. Use the GMS REST API instead.

### Endpoint

```
POST $DATAHUB_GMS_URL/entities?action=search
```

### Request Body

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `input` | Yes | string | Search query text |
| `entity` | Yes | string | Entity type: `dataset`, `dashboard`, `chart`, `glossaryTerm`, `dataProduct` |
| `start` | No | int | Pagination offset (default 0) |
| `count` | No | int | Number of results (default 10) |
| `filter` | No | object | Filter expression with `or`/`and` conditions |

### Basic Search

```bash
curl -s -X POST "$DATAHUB_GMS_URL/entities?action=search" \
  -H "Authorization: Bearer $DATAHUB_GMS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"input": "restaurant", "entity": "dataset", "start": 0, "count": 10}'
```

### Search with Platform Filter

```bash
curl -s -X POST "$DATAHUB_GMS_URL/entities?action=search" \
  -H "Authorization: Bearer $DATAHUB_GMS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "restaurant",
    "entity": "dataset",
    "start": 0,
    "count": 10,
    "filter": {
      "or": [{"and": [{"field": "platform", "condition": "EQUAL", "values": ["urn:li:dataPlatform:looker"]}]}]
    }
  }'
```

### Search with Tag Filter

```bash
curl -s -X POST "$DATAHUB_GMS_URL/entities?action=search" \
  -H "Authorization: Bearer $DATAHUB_GMS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "restaurant",
    "entity": "dataset",
    "start": 0,
    "count": 10,
    "filter": {
      "or": [{"and": [{"field": "tags", "condition": "EQUAL", "values": ["urn:li:tag:table_tier:gold"]}]}]
    }
  }'
```

### Response Structure

```json
{
  "value": {
    "numEntities": 530,
    "pageSize": 10,
    "from": 0,
    "entities": [
      {"entity": "urn:li:dataset:(urn:li:dataPlatform:bigquery,project.dataset.table,PROD)"}
    ],
    "metadata": {
      "aggregations": [
        {"name": "platform", "filterValues": [{"value": "urn:li:dataPlatform:bigquery", "facetCount": 500}]}
      ]
    }
  }
}
```

### Parsing with jq

```bash
# Extract URNs
... | jq -r '.value.entities[].entity'

# Get total count
... | jq '.value.numEntities'

# Get facet aggregations
... | jq '.value.metadata.aggregations[]'
```

---

## datahub get

Retrieve metadata for an entity by URN. Returns all aspects by default, or a specific aspect with `--aspect`.

> **Syntax note**: The command requires the `urn` subcommand: `datahub get urn --urn <URN>`.

### Flags

| Flag | Required | Description |
|------|----------|-------------|
| `--urn` | Yes | Entity URN |
| `-a`/`--aspect` | No | Specific aspect to fetch (e.g., `schemaMetadata`, `globalTags`, `datasetProperties`) |
| `--details`/`--no-details` | No | Toggle detailed output |

### Examples

```bash
# Full entity metadata (all aspects)
datahub get urn --urn "urn:li:dataset:(urn:li:dataPlatform:bigquery,project.dataset.table,PROD)"

# Schema only
datahub get urn --urn "urn:li:dataset:(...)" --aspect schemaMetadata

# Tags only (includes tier, domain, team tags)
datahub get urn --urn "urn:li:dataset:(...)" --aspect globalTags

# Dataset properties (name, description, custom properties)
datahub get urn --urn "urn:li:dataset:(...)" --aspect datasetProperties

# Deprecation status
datahub get urn --urn "urn:li:dataset:(...)" --aspect deprecation
```

> **Note**: The `ownership` aspect typically returns `{}` (empty). Use `globalTags` and look for `team:` prefixed tags as an ownership proxy.

---

## datahub exists

Check if an entity exists.

> **Syntax note**: The command requires the `urn` subcommand: `datahub exists urn --urn <URN>`.

```bash
datahub exists urn --urn "urn:li:dataset:(urn:li:dataPlatform:bigquery,project.dataset.table,PROD)"
```

Returns `true` or `false`.

---

## datahub timeline

Inspect metadata changes over time.

### Flags

| Flag | Required | Description |
|------|----------|-------------|
| `--urn` | Yes | Entity URN |
| `-c`/`--category` | Yes | One of: `tag`, `glossary_term`, `technical_schema`, `documentation`, `owner` |
| `--start` | No | Start time — milliseconds or shorthand like `7daysago`, `30daysago` |
| `--end` | No | End time — same format as `--start` |
| `-v`/`--verbose` | No | Show underlying HTTP response |
| `--raw` | No | Show raw diff |

### Examples

```bash
# Owner changes in last 30 days
datahub timeline \
  --urn "urn:li:dataset:(urn:li:dataPlatform:bigquery,project.dataset.table,PROD)" \
  -c owner --start 30daysago

# Schema changes in last 7 days with diff
datahub timeline \
  --urn "urn:li:dataset:(urn:li:dataPlatform:bigquery,project.dataset.table,PROD)" \
  -c technical_schema --start 7daysago --verbose --raw
```

---

## datahub version

Check client and server compatibility.

```bash
datahub version
datahub version --include-server
```

---

## Lineage (REST API)

The CLI v1.0.0 does not include a `lineage` subcommand. Use the GMS relationships endpoint.

### Endpoint

```
GET $DATAHUB_GMS_URL/relationships?direction=<DIR>&types=DownstreamOf&urn=<URL-ENCODED-URN>
```

### Parameters

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `direction` | Yes | `OUTGOING`, `INCOMING` | `OUTGOING` = upstream (what feeds this), `INCOMING` = downstream (what consumes this) |
| `types` | Yes | `DownstreamOf` | Relationship type |
| `urn` | Yes | URL-encoded URN | The entity to get lineage for |
| `count` | No | int | Max results (default varies) |
| `start` | No | int | Pagination offset |

### Examples

```bash
# Upstream lineage (what feeds into this table)
curl -s -X GET "$DATAHUB_GMS_URL/relationships?direction=OUTGOING&types=DownstreamOf&urn=urn%3Ali%3Adataset%3A%28urn%3Ali%3AdataPlatform%3Abigquery%2Cproject.dataset.table%2CPROD%29" \
  -H "Authorization: Bearer $DATAHUB_GMS_TOKEN"

# Downstream lineage (what consumes this table)
curl -s -X GET "$DATAHUB_GMS_URL/relationships?direction=INCOMING&types=DownstreamOf&urn=urn%3Ali%3Adataset%3A%28urn%3Ali%3AdataPlatform%3Abigquery%2Cproject.dataset.table%2CPROD%29" \
  -H "Authorization: Bearer $DATAHUB_GMS_TOKEN"
```

### Response Structure

```json
{
  "start": 0,
  "count": 7,
  "relationships": [
    {"type": "DownstreamOf", "entity": "urn:li:dataset:(urn:li:dataPlatform:bigquery,project.other_table,PROD)"}
  ]
}
```

### Parsing with jq

```bash
# Extract upstream/downstream URNs
... | jq -r '.relationships[].entity'

# Count relationships
... | jq '.count'
```

> **Note**: The URN must be URL-encoded in the query string. Encode `:` as `%3A`, `(` as `%28`, `)` as `%29`, `,` as `%2C`.

---

## Filter Patterns

Filters are used in the search REST API. They follow an `or`/`and` structure.

### Single filter

```json
{
  "filter": {
    "or": [{"and": [{"field": "platform", "condition": "EQUAL", "values": ["urn:li:dataPlatform:bigquery"]}]}]
  }
}
```

### Multiple AND conditions

```json
{
  "filter": {
    "or": [{
      "and": [
        {"field": "platform", "condition": "EQUAL", "values": ["urn:li:dataPlatform:bigquery"]},
        {"field": "tags", "condition": "EQUAL", "values": ["urn:li:tag:table_tier:gold"]}
      ]
    }]
  }
}
```

### Common filter fields

| Field | Description | Example values |
|-------|-------------|----------------|
| `platform` | Data platform | `urn:li:dataPlatform:bigquery`, `urn:li:dataPlatform:looker` |
| `tags` | Entity tags | `urn:li:tag:table_tier:gold`, `urn:li:tag:domain:finance`, `urn:li:tag:team:data-eng` |
| `domains` | Domain assignment | `urn:li:domain:<uuid>` |
| `glossaryTerms` | Glossary terms | `urn:li:glossaryTerm:<name>` |
| `container` | Container/project | `urn:li:container:<id>` |

---

## Aspect Reference

Common aspects available via `datahub get urn --aspect <name>`:

| Aspect | Description | Key fields |
|--------|-------------|------------|
| `datasetProperties` | Name, description, custom properties, external URL | `name`, `description`, `externalUrl`, `customProperties` |
| `schemaMetadata` | Column definitions with types and descriptions | `fields[].fieldPath`, `fields[].nativeDataType`, `fields[].description` |
| `globalTags` | Tags including tier, domain, team | `tags[].tag` (URN format) |
| `glossaryTerms` | Associated glossary terms | `terms[].urn` |
| `ownership` | Ownership info (often empty — use `globalTags` instead) | `owners[].owner`, `owners[].type` |
| `deprecation` | Deprecation status and note | `deprecated`, `note` |
| `status` | Removal status | `removed` |
| `datasetKey` | Platform, name, environment | `platform`, `name`, `origin` |

---

## URN Reference

| Entity | URN Pattern | Example |
|--------|-------------|---------|
| Dataset | `urn:li:dataset:(urn:li:dataPlatform:<platform>,<name>,<env>)` | `urn:li:dataset:(urn:li:dataPlatform:bigquery,project.dataset.table,PROD)` |
| Domain | `urn:li:domain:<uuid>` | `urn:li:domain:marketing` |
| Platform | `urn:li:dataPlatform:<name>` | `urn:li:dataPlatform:bigquery` |
| Container | `urn:li:container:<id>` | `urn:li:container:0e9e46bd...` |
| User | `urn:li:corpuser:<id>` | `urn:li:corpuser:jdoe` |
| Group | `urn:li:corpGroup:<id>` | `urn:li:corpGroup:data-eng` |
| Tag | `urn:li:tag:<name>` | `urn:li:tag:PII` |
| Glossary Term | `urn:li:glossaryTerm:<name>` | `urn:li:glossaryTerm:Revenue` |
| Dashboard | `urn:li:dashboard:(<platform>,<id>)` | `urn:li:dashboard:(looker,dashboards.19)` |
| Data Flow | `urn:li:dataFlow:(<platform>,<id>,<env>)` | `urn:li:dataFlow:(airflow,etl_daily,prod)` |
| Data Product | `urn:li:dataProduct:<id>` | `urn:li:dataProduct:order-revenue` |
| Schema Field | `urn:li:schemaField:(<dataset_urn>,<field>)` | `urn:li:schemaField:(urn:li:dataset:(...),user_id)` |
