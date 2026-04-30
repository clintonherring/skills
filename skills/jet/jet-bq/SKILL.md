---
name: jet-bq
description: BigQuery data exploration, querying, and optimization. Use when working with BigQuery data, writing BQ SQL queries, exploring dataset schemas, profiling tables, sampling data (top 10s, head), generating reports, switching GCP projects, estimating query costs, or optimizing query performance. Triggers on tasks involving BigQuery, BQ, data analysis, SQL queries against BQ datasets, schema exploration, table profiling, cost estimation, or query optimization.
metadata:
  owner: ai-platform
---

# BigQuery Skill

## Prerequisites

Before using BigQuery, verify the environment:

```bash
# Check bq CLI is available
bq version

# Check current project
gcloud config get-value project

# Check authentication
gcloud auth list
```

If `bq` is not installed:

```bash
# macOS/Linux
brew install google-cloud-sdk
```

```powershell
# Windows
winget install Google.CloudSDK
```

```bash
# Then authenticate
gcloud auth login
gcloud auth application-default login

# Set default project
gcloud config set project PROJECT_ID
```

Required IAM: `roles/bigquery.user` (query), `roles/bigquery.dataViewer` (schema), `roles/bigquery.dataEditor` (create/modify).

## Discovery

### List datasets in current project

```bash
bq ls
```

### List datasets in another project

```bash
bq ls --project_id=OTHER_PROJECT
```

### List tables in a dataset

```bash
bq ls dataset_name
# or fully qualified
bq ls project_id:dataset_name
```

### Show table metadata

```bash
bq show dataset.table
bq show --format=prettyjson dataset.table
```

### Show table schema

```bash
bq show --schema --format=prettyjson dataset.table
```

### Show table row count and size

```bash
bq show --format=prettyjson dataset.table | grep -E '"numRows"|"numBytes"'
```

## Data Sampling

### Quick top-N sample

```bash
bq head -n 10 dataset.table
```

### Sample via query (preferred for filtered/formatted results)

```bash
bq query --nouse_legacy_sql \
  'SELECT * FROM `project.dataset.table` LIMIT 10'
```

### Sample with specific columns

```bash
bq query --nouse_legacy_sql \
  'SELECT col1, col2, col3 FROM `project.dataset.table` LIMIT 10'
```

## Running Queries

Always use Standard SQL (not legacy):

```bash
bq query --nouse_legacy_sql 'YOUR SQL HERE'
```

### Useful flags

| Flag                  | Purpose                                  |
| --------------------- | ---------------------------------------- |
| `--nouse_legacy_sql`  | Use Standard SQL (always include)        |
| `--format=prettyjson` | JSON output                              |
| `--format=csv`        | CSV output                               |
| `--format=sparse`     | Compact table output                     |
| `--max_rows=N`        | Limit output rows displayed              |
| `--dry_run`           | Estimate bytes scanned without executing |

### Multi-line queries

```bash
bq query --nouse_legacy_sql '
  SELECT
    DATE(created_at) AS day,
    COUNT(*) AS total
  FROM `project.dataset.table`
  WHERE created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
  GROUP BY day
  ORDER BY day DESC
'
```

## Cost Estimation

**Always dry-run before executing expensive queries:**

```bash
bq query --dry_run --nouse_legacy_sql '
  SELECT * FROM `project.dataset.large_table`
  WHERE partition_date = CURRENT_DATE()
'
```

Output shows bytes scanned. Rough cost: ~$5 per TB scanned (on-demand pricing).

| Bytes Scanned | Approximate Cost |
| ------------- | ---------------- |
| 1 GB          | $0.005           |
| 100 GB        | $0.50            |
| 1 TB          | $5.00            |
| 10 TB         | $50.00           |

If a query scans > 1 TB, warn the user and suggest optimizations before running.

## Project & Dataset Switching

### Switch default project

```bash
gcloud config set project NEW_PROJECT_ID
```

### Query a different project without switching

```bash
bq query --project_id=OTHER_PROJECT --nouse_legacy_sql \
  'SELECT * FROM `other_project.dataset.table` LIMIT 10'
```

### List available projects

```bash
gcloud projects list
```

## Query Writing Guidelines

1. **Always use Standard SQL** -- never use legacy SQL
2. **Always filter on partition columns** -- reduces cost and improves speed
3. **Select only needed columns** -- avoid `SELECT *` on wide tables
4. **Use `LIMIT` during exploration** -- add LIMIT when sampling data
5. **Prefer `APPROX_COUNT_DISTINCT`** over `COUNT(DISTINCT x)` for large tables
6. **Use `IF`/`COUNTIF`/`SUMIF`** instead of CASE+aggregate for conditional aggregation
7. **Qualify all table references** -- use `project.dataset.table` format
8. **Use backtick quoting** -- wrap table refs in backticks: `` `project.dataset.table` ``

For advanced SQL patterns (window functions, CTEs, unnesting, pivots, funnels, cohorts), see [references/query-patterns.md](references/query-patterns.md).

## Optimization

Key rules to follow when writing or reviewing queries:

1. **Dry-run first** -- always `--dry_run` queries that might scan large volumes
2. **Partition filtering** -- always include partition column in WHERE clause
3. **Cluster column filtering** -- use clustered columns in WHERE/JOIN for better pruning
4. **Avoid SELECT \*** -- select only required columns, especially on wide tables
5. **Use EXISTS over IN** -- `WHERE EXISTS (SELECT 1 ...)` is faster than `WHERE x IN (SELECT ...)`
6. **Reduce data before JOINs** -- filter/aggregate in CTEs before joining
7. **Avoid repeated reads** -- use CTEs or temp tables for data read multiple times
8. **Use approximate functions** -- `APPROX_COUNT_DISTINCT`, `APPROX_QUANTILES`, `APPROX_TOP_COUNT`

For comprehensive optimization guidance including query plan analysis, partitioning/clustering strategy, anti-patterns, and cost control, see [references/optimization-guide.md](references/optimization-guide.md).

## Output & Reporting

### Export results to CSV

```bash
bq query --nouse_legacy_sql --format=csv '...' > output.csv
```

### Save results to a destination table

```bash
bq query --nouse_legacy_sql \
  --destination_table=dataset.results_table \
  --replace \
  'SELECT ...'
```

### Export a table to GCS

```bash
bq extract --destination_format=CSV \
  dataset.table gs://bucket/path/file.csv
```

When generating reports, format results as markdown tables for readability.

## Reference Material

- **CLI commands**: [references/bq-cli-reference.md](references/bq-cli-reference.md) -- full bq CLI cheat sheet
- **SQL patterns**: [references/query-patterns.md](references/query-patterns.md) -- window functions, CTEs, unnesting, pivots, funnels, cohorts
- **Optimization**: [references/optimization-guide.md](references/optimization-guide.md) -- partitioning, clustering, query plans, anti-patterns, cost control
- **Future ideas**: [references/future-ideas.md](references/future-ideas.md) -- planned enhancements (profiling scripts, report generators)
