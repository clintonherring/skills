# BigQuery Discovery Queries for Event-Driven Architecture

Queries against the `just-data-bq-users` GCP project to discover event-driven metadata, throughput, and service dependencies.

## Case-Insensitive Querying

BigQuery string comparisons are case-sensitive by default. Always use one of these approaches to ensure case-insensitive matching:

```sql
-- Option 1: LOWER() for LIKE comparisons (preferred for simple patterns)
WHERE LOWER(column_name) LIKE '%myevent%'

-- Option 2: REGEXP_CONTAINS with (?i) flag (preferred for complex patterns)
WHERE REGEXP_CONTAINS(column_name, r'(?i)my.?event')

-- Option 3: LOWER() for exact comparisons
WHERE LOWER(topic_name) = LOWER('MyEvent')
```

Apply this to all `WHERE` clauses that filter on event names, topic names, service names, or any user-provided search terms.

## Table of Contents
- [Data Model: Event Name = Table Name](#data-model-event-name--table-name)
- [Dataset Discovery](#dataset-discovery)
- [Schema Exploration](#schema-exploration)
- [Event Table Discovery](#event-table-discovery)
- [Producer Discovery via RaisingComponent](#producer-discovery-via-raisingcomponent)
- [Topic & Queue Metadata](#topic--queue-metadata)
- [Message Throughput](#message-throughput)
- [Service Dependencies](#service-dependencies)
- [Cost-Safe Query Patterns](#cost-safe-query-patterns)

---

## Data Model: Event Name = Table Name

In JET's BigQuery datasets, **the event name is always part of the table name**. For example, an event called `MyEvent` would have its data in a table whose name contains `myevent` (or a variant like `my_event`). This means:

1. **To find data for a specific event**, search for tables whose names match the event name -- do NOT rely on a generic "events" table with a "topic" column.
2. **To find who raised the event**, look for columns like `RaisingComponent`, `SourceService`, `Publisher`, `ProducerService`, or similar in the event table. These columns identify the component/service that published the event.
3. **Table naming is not standardized** across all datasets. The event name may appear as PascalCase, snake_case, or lowercase. Always use case-insensitive matching when searching.

## Dataset Discovery

Before running any queries, explore what's available. The datasets in `just-data-bq-users` may change over time.

```bash
# List all datasets in the project
bq ls --project_id just-data-bq-users --format=prettyjson 2>/dev/null | jq '.[].datasetReference.datasetId'

# List tables in a specific dataset
bq ls --project_id just-data-bq-users DATASET_NAME --format=prettyjson 2>/dev/null | jq '.[].tableReference.tableId'

# Get schema of a specific table
bq show --schema --format=prettyjson just-data-bq-users:DATASET_NAME.TABLE_NAME
```

## Schema Exploration

Once you find a potentially relevant table, explore its schema before querying:

```bash
# Full table info (schema, row count, size, partitioning)
bq show --format=prettyjson just-data-bq-users:DATASET_NAME.TABLE_NAME

# Quick sample (zero cost if table is small)
bq head -n 5 just-data-bq-users:DATASET_NAME.TABLE_NAME

# Dry-run to estimate query cost BEFORE executing
bq query --project_id=just-data-bq-users --use_legacy_sql=false --dry_run \
  'SELECT * FROM `just-data-bq-users.DATASET_NAME.TABLE_NAME` LIMIT 10'
```

## Event Table Discovery

Since event names are embedded in table names, the first step is to find the right table for your event.

### Find tables matching an event name

```bash
# List all tables in a dataset and filter by event name (case-insensitive)
bq ls --project_id just-data-bq-users DATASET_NAME --format=prettyjson 2>/dev/null \
  | jq -r '.[].tableReference.tableId' \
  | grep -i "EVENT_NAME"

# Search across multiple datasets -- list datasets first, then search each
for ds in $(bq ls --project_id just-data-bq-users --format=prettyjson 2>/dev/null | jq -r '.[].datasetReference.datasetId'); do
  MATCHES=$(bq ls --project_id just-data-bq-users "$ds" --format=prettyjson 2>/dev/null | jq -r '.[].tableReference.tableId' | grep -i "EVENT_NAME")
  if [ -n "$MATCHES" ]; then
    echo "=== Dataset: $ds ==="
    echo "$MATCHES"
  fi
done
```

### Search INFORMATION_SCHEMA for tables by name

```sql
-- Find tables whose name contains the event name (case-insensitive)
-- Run this per dataset (replace DATASET_NAME)
SELECT table_name, table_type, creation_time, row_count, size_bytes
FROM `just-data-bq-users.DATASET_NAME.INFORMATION_SCHEMA.TABLES`
WHERE LOWER(table_name) LIKE '%myevent%'
   OR LOWER(table_name) LIKE '%my_event%'
ORDER BY creation_time DESC
```

## Producer Discovery via RaisingComponent

Once you find the event table, look for columns that identify the producer/source component. Common column names include `RaisingComponent`, `SourceService`, `Publisher`, `Source`, `ProducerService`, `Component`, or `ServiceName`.

### Find producer-identifying columns in an event table

```bash
# Check the table schema for producer-related columns
bq show --schema --format=prettyjson just-data-bq-users:DATASET_NAME.TABLE_NAME \
  | jq '.[] | select(.name | test("(?i)(raising|source|publisher|producer|component|service)"))'
```

### Query distinct producers from an event table

```sql
-- Replace COLUMN_NAME with the actual column (e.g., RaisingComponent, SourceService)
SELECT DISTINCT
  COLUMN_NAME AS producer,
  COUNT(*) AS event_count,
  MIN(event_timestamp) AS first_seen,
  MAX(event_timestamp) AS last_seen
FROM `just-data-bq-users.DATASET_NAME.EVENT_TABLE_NAME`
WHERE event_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
GROUP BY producer
ORDER BY event_count DESC
LIMIT 50
```

### Sample event data to understand structure

```sql
-- Always sample first to understand the table shape and find producer columns
SELECT *
FROM `just-data-bq-users.DATASET_NAME.EVENT_TABLE_NAME`
LIMIT 5
```

## Topic & Queue Metadata

These are template queries. Replace `DATASET_NAME` and `TABLE_NAME` with actual values once you've discovered the right tables.

### Find tables that might contain topic/queue information

Look for tables with columns named like `topic`, `queue`, `event`, `message`, `producer`, `consumer`, `RaisingComponent`, `SourceService`:

```bash
# Search for tables with event-related column names
# (Run this after discovering datasets)
bq query --project_id=just-data-bq-users --use_legacy_sql=false --format=prettyjson \
  "SELECT table_name, column_name, data_type
   FROM \`just-data-bq-users.DATASET_NAME.INFORMATION_SCHEMA.COLUMNS\`
   WHERE LOWER(column_name) LIKE '%topic%'
      OR LOWER(column_name) LIKE '%queue%'
      OR LOWER(column_name) LIKE '%event%'
      OR LOWER(column_name) LIKE '%producer%'
      OR LOWER(column_name) LIKE '%consumer%'
      OR LOWER(column_name) LIKE '%message%'
      OR LOWER(column_name) LIKE '%raising%'
      OR LOWER(column_name) LIKE '%source%service%'
      OR LOWER(column_name) LIKE '%component%'
   ORDER BY table_name, column_name"
```

### List distinct topics/queues

```sql
-- Template: adjust table and column names based on what you discover
SELECT DISTINCT
  topic_name,
  COUNT(*) AS message_count
FROM `just-data-bq-users.DATASET_NAME.TABLE_NAME`
WHERE topic_name IS NOT NULL
GROUP BY topic_name
ORDER BY message_count DESC
LIMIT 100
```

### Find producers and consumers for a topic

```sql
-- Template: adjust based on actual schema
-- Uses LOWER() for case-insensitive topic matching
SELECT DISTINCT
  service_name,
  role,  -- 'producer' or 'consumer'
  topic_name
FROM `just-data-bq-users.DATASET_NAME.TABLE_NAME`
WHERE LOWER(topic_name) = LOWER('your-topic-name')
ORDER BY role, service_name
LIMIT 100
```

## Message Throughput

### Messages per topic over time

```sql
-- Template: adjust based on actual schema
SELECT
  topic_name,
  DATE(event_timestamp) AS event_date,
  COUNT(*) AS message_count,
  APPROX_COUNT_DISTINCT(producer_id) AS distinct_producers,
  APPROX_COUNT_DISTINCT(consumer_id) AS distinct_consumers
FROM `just-data-bq-users.DATASET_NAME.TABLE_NAME`
WHERE event_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
GROUP BY topic_name, event_date
ORDER BY topic_name, event_date
LIMIT 500
```

### Top topics by volume

```sql
-- Template: adjust based on actual schema
SELECT
  topic_name,
  COUNT(*) AS total_messages,
  MIN(event_timestamp) AS first_message,
  MAX(event_timestamp) AS last_message
FROM `just-data-bq-users.DATASET_NAME.TABLE_NAME`
WHERE event_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
GROUP BY topic_name
ORDER BY total_messages DESC
LIMIT 50
```

## Service Dependencies

### Build a service dependency graph from message data

```sql
-- Template: shows which services talk to each other via messaging
SELECT
  producer_service,
  consumer_service,
  topic_name,
  COUNT(*) AS message_count
FROM `just-data-bq-users.DATASET_NAME.TABLE_NAME`
WHERE event_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
GROUP BY producer_service, consumer_service, topic_name
ORDER BY message_count DESC
LIMIT 200
```

## Cost-Safe Query Patterns

BigQuery charges by data scanned. Follow these rules to avoid surprise costs:

1. **Always dry-run first**:
   ```bash
   bq query --project_id=just-data-bq-users --use_legacy_sql=false --dry_run \
     'YOUR_QUERY_HERE'
   ```
   The output shows bytes that would be scanned. At ~$5/TB, multiply accordingly.

2. **Use LIMIT**: Always add `LIMIT` to exploratory queries.

3. **Filter by time**: If the table is partitioned by timestamp, always include a time filter to reduce scan size:
   ```sql
   WHERE event_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
   ```

4. **Select specific columns**: Avoid `SELECT *` on wide tables. Name only the columns you need.

5. **Use approximate functions**: `APPROX_COUNT_DISTINCT` is cheaper and faster than `COUNT(DISTINCT ...)` on large tables.

6. **Cost thresholds**:
   | Scan Size | Estimated Cost | Action |
   |-----------|---------------|--------|
   | < 1 GB | < $0.01 | Safe to run |
   | 1-10 GB | $0.01-$0.05 | OK for targeted queries |
   | 10-100 GB | $0.05-$0.50 | Add filters to reduce scan |
   | > 100 GB | > $0.50 | Warn user before running |
   | > 1 TB | > $5.00 | Do NOT run without explicit user approval |
