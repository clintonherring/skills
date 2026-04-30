---
name: jet-datahub
description: >-
  Search, discover, and govern data assets in the DataHub catalog across BigQuery,
  dbt, Airflow, and Looker. Use this skill for metadata discovery — finding datasets,
  tracing lineage, checking data freshness/quality, identifying owners, viewing
  glossary terms, and inspecting PII/governance tags. Use jet-bq (not this skill)
  to query or explore BigQuery schemas for SQL writing; use jet-odl-athena (not this
  skill) for application/service ownership. Triggers: "where does this come from?",
  "who owns this table?", "is this data fresh?", "show me the dbt model", "impact
  of changing a column", lineage, or governance requests. Always load this skill
  before using any DataHub functions — it contains a mandatory discovery strategy.
metadata:
  owner: ai-platform
---

# DataHub Navigator

> **CRITICAL**: This skill contains a mandatory **Prioritized Discovery Strategy** that MUST be followed for all data discovery queries. Do NOT use DataHub commands for discovery without first reading and following the strategy defined below.

Use this skill to explore and query metadata in DataHub. This skill covers **read-only** operations: searching, browsing, getting details, and discovering schema. It does not cover writes, deletes, or ingestion.

> **Not covered**: This skill does not support querying or managing AWS resources (e.g., S3, Glue, Athena, Redshift). AWS integration is not yet available.

> **Safety constraint**: This skill is strictly read-only. NEVER execute commands or API calls that create, update, delete, or modify any data in DataHub or any other system. This includes mutations, `datahub delete`, `datahub put`, ingestion commands, or any operation that changes state. Only perform queries and reads.

## Prerequisites

| Tool | Tested Version | Installation |
|------|----------------|--------------|
| `datahub` CLI | `acryl-datahub==1.0.0` | `uv tool install --python 3.11 "acryl-datahub==1.0.0"` |
| `curl` | any | Pre-installed on macOS/Linux |
| `jq` (optional) | any | For JSON slicing — `brew install jq` |

Authenticate after installation:

```bash
datahub init --host https://datahub.just-data.io/api/gms --token <your-token>
```

## Quick Start

Verify CLI installation and server connectivity:

```bash
datahub version --include-server
```

If this returns client version, server config, and no errors, auth and connectivity are confirmed.

## Key Principles

- **Read-only**: All workflows in this skill are read-only. No mutations.
- **Auth model**: Authenticate with `datahub init` or `DATAHUB_GMS_URL` + `DATAHUB_GMS_TOKEN`. See [references/setup-guide.md](references/setup-guide.md).
- **CLI for entity lookups**: Use `datahub get urn`, `datahub exists urn`, and `datahub timeline` for entity-level operations.
- **REST API for search and lineage**: Use `curl` against the GMS REST API for search and relationship traversal. The CLI v1.0.0 does not include `search` or `graphql` subcommands.
- **Ownership fallback**: The `ownership` aspect is often empty. Always check `globalTags` for `team:` prefixed entries (e.g. `team:sales-restaurant-analytics`) as a proxy for ownership information.

## Auth for curl Commands

Before running `curl` commands, load credentials from `~/.datahubenv`:

```bash
DATAHUB_GMS_URL=$(grep server ~/.datahubenv | awk '{print $2}')
DATAHUB_GMS_TOKEN=$(grep token ~/.datahubenv | awk '{print $2}')
```

Or set environment variables directly:

```bash
export DATAHUB_GMS_URL="https://datahub.just-data.io/api/gms"
export DATAHUB_GMS_TOKEN="<your-token>"
```

All `curl` examples below assume these variables are set.

## Commands

| Command | Purpose | Method |
|---------|---------|--------|
| Search for entities | Catalog discovery with filters | `curl POST $DATAHUB_GMS_URL/entities?action=search` |
| Get entity metadata | Full or aspect-specific metadata by URN | `datahub get urn --urn <urn>` |
| Get specific aspect | Schema, tags, properties | `datahub get urn --urn <urn> --aspect <aspect>` |
| Check existence | Verify entity exists | `datahub exists urn --urn <urn>` |
| Get lineage | Upstream/downstream relationships | `curl GET $DATAHUB_GMS_URL/relationships?...` |
| Metadata history | Changes over time | `datahub timeline --urn <urn> -c <category>` |

For full flag details, output formats, and examples, see [references/command-reference.md](references/command-reference.md).

## Search

Search uses the GMS REST API. The `entity` parameter accepts: `dataset`, `dashboard`, `chart`, `glossaryTerm`, `dataProduct`.

### Basic search

```bash
curl -s -X POST "$DATAHUB_GMS_URL/entities?action=search" \
  -H "Authorization: Bearer $DATAHUB_GMS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"input": "restaurant", "entity": "dataset", "start": 0, "count": 10}'
```

### Search with filters

```bash
# Filter by platform (e.g., Looker)
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

### Common filter fields

| Field | Example values |
|-------|---------------|
| `platform` | `urn:li:dataPlatform:bigquery`, `urn:li:dataPlatform:looker` |
| `tags` | `urn:li:tag:table_tier:gold`, `urn:li:tag:domain:finance` |
| `domains` | `urn:li:domain:<uuid>` |
| `glossaryTerms` | `urn:li:glossaryTerm:<name>` |

### Parsing search results

Search returns entities in `value.entities[].entity` (URNs) and facets in `value.metadata.aggregations`. Use `jq` for extraction:

```bash
# Extract URNs
... | jq -r '.value.entities[].entity'

# Get total count
... | jq '.value.numEntities'
```

## Collaborative Logic: DataHub + BigQuery

DataHub is the **starting point for discovery**. Always check DataHub first to identify the correct, gold-standard dataset and its lineage before writing queries.

**If `jet-bq` is installed** — use it to explore schemas and write/run SQL queries against the datasets DataHub identifies.

**Example workflow** — User asks: "Write a query to get total revenue from our main sales table."

1. **DataHub**: Search for `sales` datasets using the REST API.
2. **DataHub**: `datahub get urn --urn <urn> --aspect globalTags` to check governance tags and tier.
3. **jet-bq**: Explore the schema of that specific table.
4. **jet-bq**: Write and optimize the SQL query.

**If `jet-bq` is NOT installed** — DataHub can still provide schema fields, lineage, and governance context via `datahub get urn --aspect schemaMetadata`. Present these results to the user and suggest a query they can run manually.

**Scope boundaries**:
- **DataHub vs. jet-bq**: DataHub discovers and validates *which* data to use (search, lineage, governance, ownership). Schema exploration for SQL writing belongs to `jet-bq`; schema exploration for governance, field-level lineage, or tag inspection belongs here.
- **DataHub vs. jet-odl-athena**: DataHub covers **data asset** ownership. Application or service team ownership belongs to `jet-odl-athena`.

## Classify Before Acting

> **CRITICAL**: Before making ANY search or tool call, you MUST classify the user's request and output a **Pre-Flight Block**. This is mandatory — do NOT proceed to any DataHub command without first outputting this block.

Output a **Pre-Flight Block** verbatim before your first tool call (see [references/discovery-templates.md](references/discovery-templates.md) for the template).

| Request Type | Examples | Action |
|-------------|----------|--------|
| **Discovery query** | "What data do we have about X?", "Find tables for Y", "Where is Z data?" | Classify as `DISCOVERY`. You MUST follow the **Prioritized Discovery Strategy** below. Do NOT skip layers. Create TodoWrite items for each layer. |
| **Specific operation** | "Show me lineage for urn:li:...", "Get schema for X", "What queries use this table?" | Classify as `SPECIFIC_OPERATION`. Use the relevant **Core Workflow** directly. |
| **Targeted metadata query** | "Who owns fact_order?", "Is fact_order deprecated?", "What team owns this table?" | Classify as `TARGETED_METADATA`. Skip the 6-layer strategy. Instead: (1) search for the table by name to find the URN, (2) use `datahub get urn` to fetch the answer directly. |

> **CRITICAL**: NEVER start a discovery query by jumping straight to a broad catalog search. Always work through the prioritized layers first. If you find yourself about to run a broad dataset search as your first tool call, STOP — you are violating the strategy.

## Prioritized Discovery Strategy

> **CRITICAL**: You MUST work through these layers **in order**. NEVER skip to Layer 6 (Full Catalog) without first checking Layers 1-5. Each layer takes one tool call — this is not expensive. Stop searching when a layer produces relevant results, but **always check Layer 2 (Business Glossary)** regardless, to enrich the response with business context.

> **When does this apply?** This strategy governs all **discovery queries** — when the user is looking for data assets, asking "what data do we have about X?", or exploring the catalog. It does **NOT** apply when the user explicitly requests lineage, schema details, dataset queries, or other specific operations — those should use the relevant Core Workflow directly.

> **NEVER do this**: Jumping straight to a broad dataset search without first checking Looker, Glossary, Data Products, and Tier Labels. This is the most common mistake and produces uncurated, low-quality results.

### Mandatory TodoWrite Task Tracking

> **CRITICAL**: When executing the Prioritized Discovery Strategy, you MUST create a TodoWrite task list with one item per layer BEFORE making your first search call. See [references/discovery-templates.md](references/discovery-templates.md) for the exact items to create.

### Mandatory Layer Gate — Audit Trail

> **CRITICAL**: After completing each layer, you MUST output a **Layer Gate Block** before proceeding to the next layer. See [references/discovery-templates.md](references/discovery-templates.md) for the template and gate rules.

| Priority | Layer | What to search | When to stop |
|----------|-------|---------------|--------------|
| 1 | **Semantic Layer** | Looker platform assets (explores, views, dashboards) | If relevant results found |
| 2 | **Business Glossary** | Glossary terms + linked datasets | **Always check** for context enrichment |
| 3 | **Data Products** | Curated data product bundles | If relevant results found |
| 4 | **Tagged Tables** | Datasets filtered by domain/team tags | If relevant results found |
| 5 | **Tier Labels** | Datasets by tier (gold > silver > bronze) | If relevant results found at any tier |
| 6 | **Full Catalog** | All datasets (broad search) | Final fallback — always returns results |

For common mistakes to avoid and result ranking criteria, see [references/discovery-strategy.md](references/discovery-strategy.md).

### Layer 1: Semantic Layer (Looker)

Search Looker for datasets, dashboards, and charts. **Complete fully before starting Layer 2.**

> **CRITICAL**: You MUST search all three entity types separately (`dataset`, `dashboard`, `chart`) with the Looker platform filter.

```bash
# Search Looker datasets
curl -s -X POST "$DATAHUB_GMS_URL/entities?action=search" \
  -H "Authorization: Bearer $DATAHUB_GMS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "...",
    "entity": "dataset",
    "start": 0,
    "count": 15,
    "filter": {"or": [{"and": [{"field": "platform", "condition": "EQUAL", "values": ["urn:li:dataPlatform:looker"]}]}]}
  }'

# Search Looker dashboards
# Same but with "entity": "dashboard"

# Search Looker charts
# Same but with "entity": "chart"
```

**Layer 1 requires three sub-steps:**

1. **Search broadly**: Use multiple query variations (e.g., `order+cancel`, `cancellation+reason`).
2. **Check if the answer already exists**: If dashboards/charts returned, get details with `datahub get urn --urn <urn>` and check upstream lineage.
3. **Check governance on source tables**: For each candidate, run upstream lineage to inspect the upstream table's tier, domain, and tags.

### Layer 2: Business Glossary (Always Check)

**Always consult the glossary**, even if Layer 1 returned results.

```bash
curl -s -X POST "$DATAHUB_GMS_URL/entities?action=search" \
  -H "Authorization: Bearer $DATAHUB_GMS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"input": "restaurant", "entity": "glossaryTerm", "start": 0, "count": 5}'
```

### Layer 3: Data Products

```bash
curl -s -X POST "$DATAHUB_GMS_URL/entities?action=search" \
  -H "Authorization: Bearer $DATAHUB_GMS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"input": "restaurant", "entity": "dataProduct", "start": 0, "count": 10}'
```

### Layer 4: Tagged Tables

```bash
curl -s -X POST "$DATAHUB_GMS_URL/entities?action=search" \
  -H "Authorization: Bearer $DATAHUB_GMS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "restaurant",
    "entity": "dataset",
    "start": 0,
    "count": 10,
    "filter": {"or": [{"and": [{"field": "tags", "condition": "EQUAL", "values": ["urn:li:tag:domain:partner-and-sales-analytics"]}]}]}
  }'
```

### Layer 5: Tier Labels (Gold > Silver > Bronze)

```bash
curl -s -X POST "$DATAHUB_GMS_URL/entities?action=search" \
  -H "Authorization: Bearer $DATAHUB_GMS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "restaurant",
    "entity": "dataset",
    "start": 0,
    "count": 10,
    "filter": {"or": [{"and": [{"field": "tags", "condition": "EQUAL", "values": ["urn:li:tag:table_tier:gold"]}]}]}
  }'
```

### Layer 6: Full Catalog Search (Fallback)

```bash
curl -s -X POST "$DATAHUB_GMS_URL/entities?action=search" \
  -H "Authorization: Bearer $DATAHUB_GMS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"input": "restaurant", "entity": "dataset", "start": 0, "count": 20}'
```

### Discovery Output Format

Present results as **ranked actionable options** (best first):

1. **Existing dashboard/chart** — Recommend with link if it already answers the question.
2. **Use a Looker explore directly** — If explore has right fields, recommend it.
3. **Query the source table** — Recommend governed BigQuery table with suggested query.

> **Verification**: Before presenting your top-ranked result, confirm it is accessible by running `datahub exists urn --urn <urn>`. This catches stale or deleted entities.

## Quick Workflows

For targeted metadata questions about **known tables**, skip the full discovery strategy and use these streamlined workflows.

### Who owns this table?

```bash
# Step 1: Find the table URN via search
curl -s -X POST "$DATAHUB_GMS_URL/entities?action=search" \
  -H "Authorization: Bearer $DATAHUB_GMS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"input": "<table_name>", "entity": "dataset", "start": 0, "count": 5}'

# Step 2: Get tags (ownership is usually in team: tags)
datahub get urn --urn "<urn_from_step_1>" --aspect globalTags
```

> **Note**: The `ownership` aspect is often empty. Check `globalTags` for `team:` prefixed tags (e.g. `team:sales-restaurant-analytics`) as a proxy for ownership.

### What is this table? (full details)

```bash
datahub get urn --urn "<urn>"
```

### What are the upstream/downstream dependencies?

```bash
# Upstream lineage (what feeds into this table)
curl -s -X GET "$DATAHUB_GMS_URL/relationships?direction=OUTGOING&types=DownstreamOf&urn=<url-encoded-urn>" \
  -H "Authorization: Bearer $DATAHUB_GMS_TOKEN"

# Downstream lineage (what consumes this table)
curl -s -X GET "$DATAHUB_GMS_URL/relationships?direction=INCOMING&types=DownstreamOf&urn=<url-encoded-urn>" \
  -H "Authorization: Bearer $DATAHUB_GMS_TOKEN"
```

> **Note**: The URN must be URL-encoded in the query string. Use `jq -r '.relationships[].entity'` to extract downstream/upstream URNs.

### Does this table exist?

```bash
datahub exists urn --urn "<urn>"
```

## Core Workflows

| # | Workflow | Method | Example |
|---|----------|--------|---------|
| 1 | Search for data assets | `curl` REST | `POST $DATAHUB_GMS_URL/entities?action=search` with `{"input": "customers", "entity": "dataset", ...}` |
| 2 | Browse by platform | `curl` REST | Same as #1 with `filter.or[].and[].field=platform` |
| 3 | Browse by tag/tier | `curl` REST | Same as #1 with `filter.or[].and[].field=tags` |
| 4 | Get entity details | `datahub` CLI | `datahub get urn --urn "urn:li:dataset:(...)"` |
| 5 | Get schema fields | `datahub` CLI | `datahub get urn --urn "urn:li:dataset:(...)" --aspect schemaMetadata` |
| 6 | Get tags | `datahub` CLI | `datahub get urn --urn "urn:li:dataset:(...)" --aspect globalTags` |
| 7 | Get lineage | `curl` REST | `GET $DATAHUB_GMS_URL/relationships?direction=OUTGOING&types=DownstreamOf&urn=<urn>` |
| 8 | Check existence | `datahub` CLI | `datahub exists urn --urn "urn:li:dataset:(...)"` |
| 9 | Metadata timeline | `datahub` CLI | `datahub timeline --urn "urn:li:dataset:(...)" -c owner --start 30daysago` |

## Setup

For installation methods, authentication details, connectivity checks, and troubleshooting, see [references/setup-guide.md](references/setup-guide.md).

## Reference Material

| File | When to Read |
|------|-------------|
| [references/command-reference.md](references/command-reference.md) | Full command flags, output formats, and examples for all CLI and REST operations |
| [references/discovery-strategy.md](references/discovery-strategy.md) | Detailed examples for each discovery layer, common mistakes, and ranking criteria |
| [references/discovery-templates.md](references/discovery-templates.md) | Verbatim output templates (Pre-Flight Block, TodoWrite items, Layer Gate Block) |
| [references/setup-guide.md](references/setup-guide.md) | Installation, auth setup, and troubleshooting |
