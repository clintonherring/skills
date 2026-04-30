---
name: jet-aws-athena
description: AWS Athena query execution and data exploration via the AWS CLI. Use this skill when running SQL queries against Athena, exploring Athena databases, tables, and schemas, checking query execution status, fetching query results, listing workgroups, or when the user asks about querying data in S3 via Athena or references AWS Athena in any context.
metadata:
  owner: ai-platform
---

# AWS Athena CLI

Run SQL queries against AWS Athena, explore databases and tables, and retrieve results using the AWS CLI and helper scripts.

## Prerequisites

| Tool | Purpose | Installation (MacOS/Linux) | Installation (Windows PowerShell) |
|------|---------|----------------------------|------------------------|
| `aws` | AWS CLI v2 | `brew install awscli` | `winget install Amazon.AWSCLI` |
| `jq` | JSON processing | `brew install jq` | `winget install jqlang.jq` |

## Authentication

You must have valid AWS credentials configured before using Athena. Typically:

```bash
# SSO login (most common at JET)
aws sso login --profile <profile-name>

# Or set the profile for the session
export AWS_PROFILE=<profile-name>
```

Ensure the IAM identity has permissions for `athena:*` and `s3:GetObject`/`s3:PutObject` on the query results bucket.

## Configuration

| Variable | Default | Description |
|---|---|---|
| `ATHENA_REGION` | `eu-west-1` | AWS region for all Athena API calls |
| `ATHENA_CATALOG` | `AwsDataCatalog` | Glue Data Catalog name |
| `ATHENA_WORKGROUP` | `primary` | Default Athena workgroup |
| `ATHENA_POLL_INTERVAL` | `2` | Seconds between status polls |
| `ATHENA_MAX_POLL` | `300` | Max seconds to wait for a query |

Override any variable before sourcing the script or at runtime:

```bash
export ATHENA_REGION=us-east-1
source /path/to/scripts/athena_query.sh
```

## Quick Usage

```bash
source /path/to/scripts/athena_query.sh

# List databases in the default (AwsDataCatalog) catalog
athena_list_databases

# List tables in a database
athena_list_tables "my_database"

# Describe a table's schema (columns, types, partitions)
athena_describe_table "my_database" "my_table"

# Run a query and wait for results (blocks until complete)
athena_query "SELECT * FROM my_database.my_table LIMIT 10"

# Run a query against a specific workgroup
athena_query "SELECT count(*) FROM my_database.my_table" "my-workgroup"

# Run a query asynchronously (returns query execution ID)
athena_start_query "SELECT * FROM my_database.my_table LIMIT 100"

# Check query status
athena_get_status "<query-execution-id>"

# Fetch results of a completed query
athena_get_results "<query-execution-id>"

# List available workgroups
athena_list_workgroups

# Preview sample rows from a table
athena_preview "my_database" "my_table" 5
```

## Core Concepts

### Workgroups

Athena workgroups control query settings, cost limits, and output locations. Each workgroup has a configured S3 output location for query results. The default workgroup is `primary`, but teams often have dedicated workgroups.

When running queries, always check if a specific workgroup should be used:

```bash
# List available workgroups
athena_list_workgroups

# Use a specific workgroup
athena_query "SELECT 1" "my-workgroup"
```

### Catalogs and Databases

Athena uses catalogs (default: `AwsDataCatalog`) that contain databases. Databases contain tables backed by data in S3. Explore the hierarchy before querying:

```bash
# List databases
athena_list_databases

# List tables in a database
athena_list_tables "my_database"

# Understand the schema
athena_describe_table "my_database" "my_table"
```

### Query Lifecycle

Athena queries are asynchronous. The lifecycle is:

1. **Start** -- submit the SQL query, receive a query execution ID
2. **Poll** -- check status until the query reaches a terminal state (`SUCCEEDED`, `FAILED`, `CANCELLED`)
3. **Fetch** -- retrieve results once succeeded

The `athena_query` helper function handles all three steps automatically. Use `athena_start_query` / `athena_get_status` / `athena_get_results` for manual control.

### Query States

| State | Description |
|-------|-------------|
| `QUEUED` | Query is waiting to be executed |
| `RUNNING` | Query is currently executing |
| `SUCCEEDED` | Query completed successfully |
| `FAILED` | Query failed (check error message) |
| `CANCELLED` | Query was cancelled |

## Best Practices

1. **Always use LIMIT** -- Athena scans data in S3 and costs scale with data scanned. Add `LIMIT` clauses when exploring data.
2. **Use partitions** -- Filter on partition columns (often `year`, `month`, `day`, `dt`, or `date`) to reduce data scanned.
3. **Preview before querying** -- Use `athena_preview` or `athena_describe_table` to understand the table structure before writing complex queries.
4. **Use the right workgroup** -- Different workgroups may have different permissions and output locations. Ask the user which workgroup to use if unclear.
5. **Check for errors** -- If a query fails, use `athena_get_status` to see the error message and reason.
6. **Use parameterized patterns** -- For repeated queries, use variables to avoid SQL injection risks.

## Exploring Data

### Recommended exploration workflow

1. **List databases** to find the relevant database:
   ```bash
   athena_list_databases
   ```

2. **List tables** in the database:
   ```bash
   athena_list_tables "my_database"
   ```

3. **Describe the table** to understand columns and partitions:
   ```bash
   athena_describe_table "my_database" "my_table"
   ```

4. **Preview a few rows** to understand the data:
   ```bash
   athena_preview "my_database" "my_table" 5
   ```

5. **Write and run** your analytical query:
   ```bash
   athena_query "SELECT col1, count(*) FROM my_database.my_table WHERE dt = '2025-01-01' GROUP BY col1 LIMIT 100"
   ```

## Direct AWS CLI Usage

If you need to go beyond the helper functions, use the AWS CLI directly:

```bash
# Start a query
aws athena start-query-execution \
  --query-string "SELECT 1" \
  --work-group "primary" \
  --query-execution-context Database=my_database

# Get query status
aws athena get-query-execution \
  --query-execution-id "<id>"

# Get query results
aws athena get-query-results \
  --query-execution-id "<id>" \
  --max-items 100

# List databases
aws athena list-databases \
  --catalog-name AwsDataCatalog

# List tables
aws athena list-table-metadata \
  --catalog-name AwsDataCatalog \
  --database-name my_database

# Get table metadata
aws athena get-table-metadata \
  --catalog-name AwsDataCatalog \
  --database-name my_database \
  --table-name my_table

# List workgroups
aws athena list-work-groups

# List named queries (saved queries)
aws athena list-named-queries --work-group "primary"
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `AccessDeniedException` | Check AWS profile/credentials and IAM permissions |
| `FAILED` query status | Run `athena_get_status <id>` and check `StateChangeReason` |
| No results returned | Verify the table has data and partition filters are correct |
| Timeout waiting for results | Use `athena_start_query` for long-running queries and poll manually |
| `INVALID_INPUT` error | Check SQL syntax; Athena uses Trino/Presto SQL dialect |

## Related Skills

- **jet-odl-athena** -- Pre-built queries and schema references for JET's Operational Data Lake (ODL). Use it to investigate deployments, team ownership, Wiz security issues, GitHub activity, reliability metrics, and more. It depends on this skill for low-level Athena operations.
