# Prioritized Discovery Strategy — Layer Examples

All examples use a scenario where the user asks about **order revenue** data.

All search examples use `curl` against the GMS REST API (`POST $DATAHUB_GMS_URL/entities?action=search`). Entity details use the `datahub` CLI. See [command-reference.md](command-reference.md) for full syntax.

## Auth Prerequisite

Before running any `curl` commands, load credentials:

```bash
DATAHUB_GMS_URL=$(grep server ~/.datahubenv | awk '{print $2}')
DATAHUB_GMS_TOKEN=$(grep token ~/.datahubenv | awk '{print $2}')
```

## Layer 1: Semantic Layer (Looker)

Search the Looker platform for datasets, dashboards, and charts — the curated, business-facing semantic layer.

> **CRITICAL**: You MUST search all three entity types separately — `dataset`, `dashboard`, and `chart` — with the Looker platform filter.

**Step 1a: Search with multiple query variations** to cover naming differences:

```bash
# Looker datasets
curl -s -X POST "$DATAHUB_GMS_URL/entities?action=search" \
  -H "Authorization: Bearer $DATAHUB_GMS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "order revenue",
    "entity": "dataset",
    "start": 0,
    "count": 15,
    "filter": {"or": [{"and": [{"field": "platform", "condition": "EQUAL", "values": ["urn:li:dataPlatform:looker"]}]}]}
  }'

# Looker dashboards
curl -s -X POST "$DATAHUB_GMS_URL/entities?action=search" \
  -H "Authorization: Bearer $DATAHUB_GMS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"input": "order revenue", "entity": "dashboard", "start": 0, "count": 15}'

# Looker charts
curl -s -X POST "$DATAHUB_GMS_URL/entities?action=search" \
  -H "Authorization: Bearer $DATAHUB_GMS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"input": "order revenue", "entity": "chart", "start": 0, "count": 15}'
```

**Step 1b: Drill into results** — If dashboards or charts are returned, get their details and check upstream lineage:

```bash
# Get entity details
datahub get urn --urn "urn:li:dashboard:(looker,dashboards.21)"

# Check upstream lineage
curl -s -X GET "$DATAHUB_GMS_URL/relationships?direction=OUTGOING&types=DownstreamOf&urn=<url-encoded-urn>" \
  -H "Authorization: Bearer $DATAHUB_GMS_TOKEN"
```

If an existing dashboard directly answers the user's question, recommend it first — the user may not need to write any SQL.

**Step 1c: Check governance on upstream source tables** — For each candidate, inspect the underlying table's tags:

```bash
# Get tags (tier, domain, team) for the upstream table
datahub get urn --urn "<upstream_dataset_urn>" --aspect globalTags
```

**Complete all three sub-steps before proceeding to Layer 2.**

## Layer 2: Business Glossary (Always Check)

**Always consult the glossary**, even if Layer 1 returned results. Glossary terms provide standardized business definitions and context.

```bash
curl -s -X POST "$DATAHUB_GMS_URL/entities?action=search" \
  -H "Authorization: Bearer $DATAHUB_GMS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"input": "order revenue", "entity": "glossaryTerm", "start": 0, "count": 5}'
```

If relevant terms are found, discover linked datasets by filtering on glossary terms:

```bash
curl -s -X POST "$DATAHUB_GMS_URL/entities?action=search" \
  -H "Authorization: Bearer $DATAHUB_GMS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "*",
    "entity": "dataset",
    "start": 0,
    "count": 10,
    "filter": {"or": [{"and": [{"field": "glossaryTerms", "condition": "EQUAL", "values": ["urn:li:glossaryTerm:revenue"]}]}]}
  }'
```

## Layer 3: Data Products

Search for curated, domain-owned data product bundles.

```bash
curl -s -X POST "$DATAHUB_GMS_URL/entities?action=search" \
  -H "Authorization: Bearer $DATAHUB_GMS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"input": "order revenue", "entity": "dataProduct", "start": 0, "count": 10}'
```

## Layer 4: Tagged Tables

Filter datasets by domain or team tags:

```bash
curl -s -X POST "$DATAHUB_GMS_URL/entities?action=search" \
  -H "Authorization: Bearer $DATAHUB_GMS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "order revenue",
    "entity": "dataset",
    "start": 0,
    "count": 10,
    "filter": {"or": [{"and": [{"field": "tags", "condition": "EQUAL", "values": ["urn:li:tag:domain:finance"]}]}]}
  }'
```

## Layer 5: Tier Labels (Gold > Silver > Bronze)

Search by quality tier in order: **gold > silver > bronze**. Stop at the first tier with results.

```bash
# Gold tier
curl -s -X POST "$DATAHUB_GMS_URL/entities?action=search" \
  -H "Authorization: Bearer $DATAHUB_GMS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "order revenue",
    "entity": "dataset",
    "start": 0,
    "count": 10,
    "filter": {"or": [{"and": [{"field": "tags", "condition": "EQUAL", "values": ["urn:li:tag:table_tier:gold"]}]}]}
  }'
```

> **Note**: Tier tag URNs may vary. Common patterns: `urn:li:tag:table_tier:gold`, `urn:li:tag:tier:gold`. Use whichever returns results. Check search facets (`value.metadata.aggregations`) to discover available tag values.

## Layer 6: Full Catalog Search (Fallback)

Broad search across the entire catalog. Flag results as uncurated and suggest checking with data owners.

```bash
curl -s -X POST "$DATAHUB_GMS_URL/entities?action=search" \
  -H "Authorization: Bearer $DATAHUB_GMS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"input": "order revenue", "entity": "dataset", "start": 0, "count": 20}'
```

## Common Mistakes

> **Mistake 1 — Skipping straight to Full Catalog**: Running a broad dataset search as the first and only search. This bypasses the semantic layer, glossary, data products, and tier labels.
>
> **Fix**: Always start at Layer 1 (Looker). Search with the Looker platform filter. Output the Pre-Flight Block, create TodoWrite items, and work through layers sequentially.

> **Mistake 2 — Recommending a later-layer result over a governed Layer 1 result**: Finding Looker views in Layer 1, skipping the governance check, then recommending a different table from Layer 5.
>
> **Fix**: Layer 1 results with a governance-validated gold-tier upstream source should be ranked **at least equal** to gold-tier tables found in later layers.

> **Mistake 3 — Skipping Layer 2 (Business Glossary)**: Finding good results in Layer 1 and immediately presenting them without checking the glossary.
>
> **Fix**: Layer 2 is marked "Always Check" — it MUST be executed regardless of Layer 1 results.

> **Mistake 4 — Searching Looker with only one entity type**: Only searching for `dataset` and missing dashboards and charts that already answer the question.
>
> **Fix**: Always search all three entity types (`dataset`, `dashboard`, `chart`) separately for Layer 1.

## Result Ranking — When Multiple Candidates Are Found

**Ranking criteria (in priority order):**
1. **Tier**: Gold > Silver > Bronze > untagged
2. **Governance completeness**: Prefer datasets with description, domain assignment, and team tags
3. **Asset type**: Physical tables > non-materialized views
4. **Partitioning**: Partitioned tables preferred for time-filtered queries
5. **Field relevance**: Only use as tiebreaker after governance criteria are equal

**How to check**: Use `datahub get urn --urn <urn> --aspect globalTags` to inspect tier, domain, and team tags for each candidate.
