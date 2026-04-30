# bq CLI Reference

## Table of Contents
- [Authentication & Config](#authentication--config)
- [Listing Resources](#listing-resources)
- [Showing Metadata](#showing-metadata)
- [Querying](#querying)
- [Table Operations](#table-operations)
- [Data Loading](#data-loading)
- [Data Export](#data-export)
- [Job Management](#job-management)

## Authentication & Config

```bash
# Login interactively
gcloud auth login

# Set application default credentials (needed for some bq operations)
gcloud auth application-default login

# Set default project
gcloud config set project PROJECT_ID

# View current config
gcloud config list

# List available projects
gcloud projects list
```

## Listing Resources

```bash
# List datasets in current project
bq ls

# List datasets in a specific project
bq ls --project_id=PROJECT_ID

# List tables in a dataset
bq ls DATASET
bq ls PROJECT:DATASET

# List tables with details (type, labels, time partitioning)
bq ls --format=prettyjson DATASET

# List jobs (recent queries)
bq ls -j
bq ls -j -a                    # All users' jobs (requires admin)
bq ls -j --max_results=20      # Limit results

# List transfers
bq ls --transfer_config --transfer_location=eu
```

## Showing Metadata

```bash
# Show table metadata (rows, size, schema summary)
bq show DATASET.TABLE

# Show full table metadata as JSON
bq show --format=prettyjson DATASET.TABLE

# Show schema only
bq show --schema --format=prettyjson DATASET.TABLE

# Show dataset metadata
bq show DATASET

# Show view definition
bq show --view DATASET.VIEW

# Show job details (query plan, stats)
bq show -j JOB_ID
bq show -j --format=prettyjson JOB_ID
```

## Querying

```bash
# Basic query (always use --nouse_legacy_sql)
bq query --nouse_legacy_sql 'SELECT 1 AS test'

# Multi-line query
bq query --nouse_legacy_sql '
  SELECT col1, col2
  FROM `project.dataset.table`
  WHERE date_col >= "2024-01-01"
  LIMIT 100
'

# Dry run (estimate bytes scanned, no execution)
bq query --dry_run --nouse_legacy_sql 'SELECT * FROM `project.dataset.table`'

# Output formats
bq query --nouse_legacy_sql --format=csv 'SELECT ...'
bq query --nouse_legacy_sql --format=prettyjson 'SELECT ...'
bq query --nouse_legacy_sql --format=sparse 'SELECT ...'

# Limit displayed rows
bq query --nouse_legacy_sql --max_rows=50 'SELECT ...'

# Save results to destination table
bq query --nouse_legacy_sql \
  --destination_table=DATASET.DEST_TABLE \
  --replace \
  'SELECT ...'

# Append results to existing table
bq query --nouse_legacy_sql \
  --destination_table=DATASET.DEST_TABLE \
  --append_table \
  'SELECT ...'

# Query with a specific project (billing project)
bq query --project_id=BILLING_PROJECT --nouse_legacy_sql 'SELECT ...'

# Use parameterized queries
bq query --nouse_legacy_sql \
  --parameter='start_date:DATE:2024-01-01' \
  --parameter='limit_val:INT64:100' \
  'SELECT * FROM `dataset.table` WHERE dt >= @start_date LIMIT @limit_val'

# Query from a file
bq query --nouse_legacy_sql < query.sql
```

## Table Operations

```bash
# Quick peek at table data (no query cost)
bq head -n 10 DATASET.TABLE

# Head with specific columns
bq head -n 10 --selected_fields=col1,col2 DATASET.TABLE

# Create an empty table with schema
bq mk --table DATASET.TABLE col1:STRING,col2:INTEGER,col3:TIMESTAMP

# Create table from schema file
bq mk --table DATASET.TABLE schema.json

# Create a partitioned table
bq mk --table \
  --time_partitioning_field=created_at \
  --time_partitioning_type=DAY \
  --clustering_fields=country,city \
  DATASET.TABLE schema.json

# Copy a table
bq cp SOURCE_DATASET.SOURCE_TABLE DEST_DATASET.DEST_TABLE

# Delete a table
bq rm -t DATASET.TABLE

# Delete a table without confirmation
bq rm -f -t DATASET.TABLE

# Create a dataset
bq mk --dataset PROJECT:DATASET

# Create a dataset with location
bq mk --dataset --location=EU PROJECT:DATASET

# Delete a dataset (must be empty)
bq rm -d DATASET

# Delete a dataset and all its tables
bq rm -r -d DATASET

# Create a view
bq mk --view 'SELECT col1, col2 FROM `dataset.table`' DATASET.VIEW_NAME

# Update table description
bq update --description="Table description" DATASET.TABLE

# Update table expiration (seconds from now)
bq update --expiration=86400 DATASET.TABLE
```

## Data Loading

```bash
# Load CSV from local file
bq load --source_format=CSV \
  --autodetect \
  DATASET.TABLE ./data.csv

# Load CSV with schema
bq load --source_format=CSV \
  --skip_leading_rows=1 \
  DATASET.TABLE ./data.csv col1:STRING,col2:INTEGER

# Load JSON (newline-delimited)
bq load --source_format=NEWLINE_DELIMITED_JSON \
  --autodetect \
  DATASET.TABLE ./data.jsonl

# Load Parquet from GCS
bq load --source_format=PARQUET \
  DATASET.TABLE gs://bucket/path/*.parquet

# Load with partitioning
bq load --source_format=PARQUET \
  --time_partitioning_field=event_date \
  DATASET.TABLE gs://bucket/data.parquet

# Load with replace (overwrite table)
bq load --replace --source_format=CSV \
  --autodetect \
  DATASET.TABLE ./data.csv
```

## Data Export

```bash
# Export to CSV on GCS
bq extract --destination_format=CSV \
  DATASET.TABLE gs://bucket/output/data.csv

# Export to JSON on GCS
bq extract --destination_format=NEWLINE_DELIMITED_JSON \
  DATASET.TABLE gs://bucket/output/data.json

# Export to Parquet on GCS
bq extract --destination_format=PARQUET \
  DATASET.TABLE gs://bucket/output/data.parquet

# Export with compression
bq extract --destination_format=CSV --compression=GZIP \
  DATASET.TABLE gs://bucket/output/data.csv.gz

# Export with wildcard (for large tables, produces multiple files)
bq extract --destination_format=CSV \
  DATASET.TABLE gs://bucket/output/data_*.csv
```

## Job Management

```bash
# List recent jobs
bq ls -j --max_results=10

# Show job details (query plan, bytes processed, slot usage)
bq show -j JOB_ID
bq show -j --format=prettyjson JOB_ID

# Cancel a running job
bq cancel JOB_ID

# Wait for a job to complete
bq wait JOB_ID
```

## Global Flags

These flags work with most bq commands:

| Flag | Description |
|------|-------------|
| `--project_id=PROJECT` | Override default project |
| `--dataset_id=DATASET` | Override default dataset |
| `--location=REGION` | Specify processing location (US, EU, etc.) |
| `--format=FORMAT` | Output format: pretty, prettyjson, json, csv, sparse |
| `--quiet` or `-q` | Suppress status messages |
| `--headless` | Run without user interaction |
| `--synchronous_mode=false` | Run query asynchronously |
