# BigQuery Optimization Guide

## Table of Contents
- [Pre-Query Checklist](#pre-query-checklist)
- [Partitioning](#partitioning)
- [Clustering](#clustering)
- [Query Plan Analysis](#query-plan-analysis)
- [Common Anti-Patterns](#common-anti-patterns)
- [Join Optimization](#join-optimization)
- [Cost Control](#cost-control)
- [Materialized Views](#materialized-views)
- [Slot Usage and Performance](#slot-usage-and-performance)

## Pre-Query Checklist

Before running any non-trivial query:

1. **Dry run** to check bytes scanned:
   ```bash
   bq query --dry_run --nouse_legacy_sql 'YOUR QUERY'
   ```
2. **Check table size** to understand scale:
   ```bash
   bq show --format=prettyjson dataset.table | grep -E '"numRows"|"numBytes"'
   ```
3. **Check partitioning/clustering** to know which filters help:
   ```bash
   bq show --format=prettyjson dataset.table | grep -E '"timePartitioning"|"clustering"'
   ```
4. **Add partition filter** if table is partitioned
5. **Add LIMIT** during exploration

## Partitioning

Partitioned tables divide data into segments for efficient querying. Always filter on the partition column.

### Types

| Type | Use When |
|------|----------|
| Time-based (DAY/HOUR/MONTH/YEAR) | Table has a date/timestamp column queried with date ranges |
| Integer range | Table has an integer key queried with range filters |
| Ingestion time (`_PARTITIONTIME`) | No natural partition column; use load time |

### Best practices

- **Always include partition filter in WHERE clause** -- without it, BQ scans all partitions
- Partition on the column most frequently used in WHERE/JOIN
- Use DAY partitioning for most cases; HOUR if table receives > 1 GB/hour
- Tables with < 1 GB generally don't benefit from partitioning

### Check if a query uses partition pruning

```bash
# Run dry_run, then check the actual query
bq query --dry_run --nouse_legacy_sql '
  SELECT * FROM `project.dataset.partitioned_table`
  WHERE partition_date = CURRENT_DATE()
'
# Compare bytes scanned with vs without the partition filter
```

## Clustering

Clustered tables sort data within partitions by specified columns (up to 4). Filters and joins on clustered columns reduce bytes scanned.

### When to cluster

- Columns frequently in WHERE clauses
- Columns frequently in JOIN conditions
- Columns frequently in GROUP BY / ORDER BY
- High-cardinality columns (user_id, session_id) benefit most

### Column order matters

Put columns in order of filter frequency:
```sql
-- If you most often filter by country, then city, then store_id:
CLUSTER BY country, city, store_id
```

### Check clustering effectiveness

Compare dry-run bytes with and without the cluster column filter:
```bash
# Without cluster filter
bq query --dry_run --nouse_legacy_sql '
  SELECT COUNT(*) FROM `dataset.table`
  WHERE partition_date = "2024-01-01"
'

# With cluster filter
bq query --dry_run --nouse_legacy_sql '
  SELECT COUNT(*) FROM `dataset.table`
  WHERE partition_date = "2024-01-01"
    AND country = "GB"
'
```

## Query Plan Analysis

After running a query, inspect the job to understand performance:

```bash
# Get job ID from query output, then:
bq show -j --format=prettyjson JOB_ID
```

Key fields to examine in the query plan:

| Field | What to Look For |
|-------|-----------------|
| `totalBytesProcessed` | How much data was scanned |
| `totalBytesBilled` | Actual billed amount (min 10 MB) |
| `totalSlotMs` | Slot-milliseconds consumed |
| `queryPlan[].recordsRead` | Rows read per stage |
| `queryPlan[].recordsWritten` | Rows output per stage |
| `queryPlan[].shuffleOutputBytes` | Data shuffled between stages |
| `queryPlan[].waitRatioAvg` | Time waiting for slots (> 0.5 = slot contention) |

### Signs of a problem

- **Large `shuffleOutputBytes`** -- too much data moving between stages; filter earlier
- **High `waitRatioAvg`** -- slot contention; query is competing for resources
- **`recordsRead` >> `recordsWritten`** in early stages -- good, means filters are working
- **`recordsRead` ≈ `recordsWritten`** in early stages -- bad, no pruning happening

## Common Anti-Patterns

### 1. SELECT * on wide tables

```sql
-- BAD: reads all columns
SELECT * FROM `dataset.wide_table` LIMIT 100

-- GOOD: select only what you need
SELECT user_id, event_name, event_timestamp
FROM `dataset.wide_table` LIMIT 100
```

### 2. Missing partition filter

```sql
-- BAD: full table scan
SELECT COUNT(*) FROM `dataset.events`
WHERE event_name = 'purchase'

-- GOOD: partition-aware
SELECT COUNT(*) FROM `dataset.events`
WHERE event_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
  AND event_name = 'purchase'
```

### 3. Using IN with large subquery

```sql
-- BAD: materializes full subquery
SELECT * FROM orders
WHERE customer_id IN (SELECT customer_id FROM vip_customers)

-- GOOD: use EXISTS or JOIN
SELECT o.* FROM orders o
WHERE EXISTS (
  SELECT 1 FROM vip_customers v WHERE v.customer_id = o.customer_id
)

-- ALSO GOOD: use JOIN
SELECT o.* FROM orders o
INNER JOIN vip_customers v ON o.customer_id = v.customer_id
```

### 4. Repeated table scans in CTEs

```sql
-- BAD: base_data is re-scanned for each CTE that references it
-- (BQ may optimize this, but don't rely on it for large tables)

-- GOOD: materialize intermediate results to a temp table for very large datasets
-- or restructure to scan once
```

### 5. Cross joins / cartesian products

```sql
-- BAD: accidental cross join
SELECT * FROM table_a, table_b  -- produces rows_a * rows_b rows

-- GOOD: always use explicit JOIN with ON clause
SELECT * FROM table_a JOIN table_b ON table_a.id = table_b.a_id
```

### 6. Ordering without LIMIT

```sql
-- BAD: sorts entire result set
SELECT * FROM large_table ORDER BY created_at DESC

-- GOOD: always LIMIT when using ORDER BY
SELECT * FROM large_table ORDER BY created_at DESC LIMIT 100
```

### 7. Using DISTINCT as a fix for bad joins

```sql
-- BAD: hiding a many-to-many join with DISTINCT
SELECT DISTINCT a.*, b.name
FROM table_a a JOIN table_b b ON a.category = b.category

-- GOOD: fix the join to produce correct cardinality
-- Investigate why the join produces duplicates
```

## Join Optimization

### Filter before joining

```sql
-- BAD: join then filter
SELECT o.*, c.name
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_date >= '2024-01-01'
  AND c.country = 'GB'

-- BETTER: filter in CTEs before joining
WITH filtered_orders AS (
  SELECT * FROM orders WHERE order_date >= '2024-01-01'
),
gb_customers AS (
  SELECT * FROM customers WHERE country = 'GB'
)
SELECT o.*, c.name
FROM filtered_orders o
JOIN gb_customers c ON o.customer_id = c.customer_id
```

### Join order

BQ optimizes join order automatically in most cases, but as a guideline:
- Put the larger table on the left side of the JOIN
- Put the smaller table on the right (it becomes the broadcast side)

### Avoid skewed joins

If one join key has disproportionately many rows (e.g., `NULL` or a default value), it causes slot imbalance:

```sql
-- Filter out skewed keys before joining
WHERE join_key IS NOT NULL AND join_key != 'UNKNOWN'
```

## Cost Control

### On-demand pricing

- $5 per TB scanned (first 1 TB/month free)
- Minimum 10 MB billed per query
- Cancelled queries still bill for bytes scanned before cancellation

### Reduce scan size

1. **Use partition filters** -- most impactful optimization
2. **Select specific columns** -- BQ is columnar; fewer columns = less data read
3. **Use clustering filters** -- additional pruning within partitions
4. **Use `LIMIT` in exploration** -- does NOT reduce bytes scanned for the query, but reduces output processing
5. **Use approximate functions** -- `APPROX_COUNT_DISTINCT` can be faster/cheaper than `COUNT(DISTINCT)`

### Set up safeguards

```bash
# Set maximum bytes billed (query fails if it would exceed)
bq query --nouse_legacy_sql --maximum_bytes_billed=1000000000 'SELECT ...'
# 1000000000 = 1 GB
```

### Cost estimation formula

```
Cost = (bytes_scanned / 1,099,511,627,776) * $5.00
```

Quick reference:
- 10 GB query ≈ $0.05
- 100 GB query ≈ $0.50
- 1 TB query ≈ $5.00

## Materialized Views

Use materialized views for frequently-run aggregation queries:

```sql
CREATE MATERIALIZED VIEW dataset.mv_daily_sales AS
SELECT
  DATE(order_timestamp) AS order_date,
  product_category,
  COUNT(*) AS order_count,
  SUM(revenue) AS total_revenue
FROM `dataset.orders`
GROUP BY 1, 2
```

### When to use

- Query runs frequently (multiple times per day)
- Base table is large but aggregation is small
- Data freshness requirements allow for some lag
- The aggregation pattern is stable

### Limitations

- Only supports aggregate queries (GROUP BY)
- No JOINs in materialized view definition
- Base table must be partitioned or clustered for incremental refresh
- Max 20 materialized views per table

## Slot Usage and Performance

### Check slot consumption

```bash
# After running a query, check the job:
bq show -j --format=prettyjson JOB_ID | grep totalSlotMs
```

### Estimate slots used

```
Average slots = totalSlotMs / (elapsed_time_ms)
```

### Reduce slot usage

1. **Reduce data volume** -- all optimizations above help
2. **Avoid complex regex** on large string columns
3. **Reduce number of GROUP BY columns** where possible
4. **Use APPROX functions** -- they use fewer slots
5. **Break up very large queries** into stages with temp tables
