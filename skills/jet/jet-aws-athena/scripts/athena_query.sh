#!/bin/bash
# AWS Athena CLI helpers. Requires: aws (v2), jq.
# Usage: source athena_query.sh && athena_query "SELECT 1"
set -o pipefail

ATHENA_REGION="${ATHENA_REGION:-eu-west-1}"
ATHENA_CATALOG="${ATHENA_CATALOG:-AwsDataCatalog}"
ATHENA_WORKGROUP="${ATHENA_WORKGROUP:-primary}"
ATHENA_POLL_INTERVAL="${ATHENA_POLL_INTERVAL:-2}"
ATHENA_MAX_POLL="${ATHENA_MAX_POLL:-300}"

# --- Database & Table exploration ---

athena_list_databases() {
  local catalog="${1:-$ATHENA_CATALOG}"
  aws athena list-databases \
    --region "$ATHENA_REGION" \
    --catalog-name "$catalog" \
    --query 'DatabaseList[].Name' \
    --output json | jq -r '.[]' | sort
}

athena_list_tables() {
  local database="$1" catalog="${2:-$ATHENA_CATALOG}"
  [[ -z "$database" ]] && { echo "Error: database name required" >&2; return 1; }
  aws athena list-table-metadata \
    --region "$ATHENA_REGION" \
    --catalog-name "$catalog" \
    --database-name "$database" \
    --query 'TableMetadataList[].Name' \
    --output json | jq -r '.[]' | sort
}

athena_describe_table() {
  local database="$1" table="$2" catalog="${3:-$ATHENA_CATALOG}"
  [[ -z "$database" || -z "$table" ]] && { echo "Error: database and table name required" >&2; return 1; }
  local metadata
  metadata=$(aws athena get-table-metadata \
    --region "$ATHENA_REGION" \
    --catalog-name "$catalog" \
    --database-name "$database" \
    --table-name "$table" \
    --output json) || return 1

  echo "=== Table: ${database}.${table} ==="
  echo ""
  echo "--- Columns ---"
  echo "$metadata" | jq -r '.TableMetadata.Columns[] | "  \(.Name)  \(.Type)  \(.Comment // "")"'
  echo ""

  local partitions
  partitions=$(echo "$metadata" | jq -r '.TableMetadata.PartitionKeys // []')
  if [[ "$partitions" != "[]" ]]; then
    echo "--- Partition Keys ---"
    echo "$partitions" | jq -r '.[] | "  \(.Name)  \(.Type)"'
    echo ""
  fi

  local table_type
  table_type=$(echo "$metadata" | jq -r '.TableMetadata.TableType // "unknown"')
  echo "Table Type: $table_type"

  local create_time
  create_time=$(echo "$metadata" | jq -r '.TableMetadata.CreateTime // "unknown"')
  echo "Created: $create_time"

  local parameters
  parameters=$(echo "$metadata" | jq -r '.TableMetadata.Parameters // {}')
  local location
  location=$(echo "$parameters" | jq -r '.location // empty')
  [[ -n "$location" ]] && echo "S3 Location: $location"

  local serde
  serde=$(echo "$parameters" | jq -r '.["serde.serialization.lib"] // .inputformat // empty')
  [[ -n "$serde" ]] && echo "Format: $serde"
}

# --- Query execution ---

athena_start_query() {
  local query="$1" workgroup="${2:-$ATHENA_WORKGROUP}" database="$3"
  [[ -z "$query" ]] && { echo "Error: SQL query required" >&2; return 1; }

  local cmd=(aws athena start-query-execution
    --region "$ATHENA_REGION"
    --query-string "$query"
    --work-group "$workgroup")

  [[ -n "$database" ]] && cmd+=(--query-execution-context "Database=$database")

  local result
  result=$("${cmd[@]}" --output json) || return 1
  echo "$result" | jq -r '.QueryExecutionId'
}

athena_get_status() {
  local execution_id="$1"
  [[ -z "$execution_id" ]] && { echo "Error: query execution ID required" >&2; return 1; }
  aws athena get-query-execution \
    --region "$ATHENA_REGION" \
    --query-execution-id "$execution_id" \
    --output json | jq '{
      QueryExecutionId: .QueryExecution.QueryExecutionId,
      State: .QueryExecution.Status.State,
      StateChangeReason: .QueryExecution.Status.StateChangeReason,
      SubmissionDateTime: .QueryExecution.Status.SubmissionDateTime,
      CompletionDateTime: .QueryExecution.Status.CompletionDateTime,
      DataScannedBytes: .QueryExecution.Statistics.DataScannedInBytes,
      EngineExecutionTimeMs: .QueryExecution.Statistics.EngineExecutionTimeInMillis,
      OutputLocation: .QueryExecution.ResultConfiguration.OutputLocation
    }'
}

_athena_get_state() {
  local execution_id="$1"
  aws athena get-query-execution \
    --region "$ATHENA_REGION" \
    --query-execution-id "$execution_id" \
    --query 'QueryExecution.Status.State' \
    --output text
}

athena_wait_for_query() {
  local execution_id="$1"
  [[ -z "$execution_id" ]] && { echo "Error: query execution ID required" >&2; return 1; }

  local elapsed=0 state
  while [[ $elapsed -lt $ATHENA_MAX_POLL ]]; do
    state=$(_athena_get_state "$execution_id") || return 1
    case "$state" in
      SUCCEEDED) return 0 ;;
      FAILED|CANCELLED)
        echo "Error: Query $state" >&2
        athena_get_status "$execution_id" >&2
        return 1
        ;;
    esac
    sleep "$ATHENA_POLL_INTERVAL"
    elapsed=$((elapsed + ATHENA_POLL_INTERVAL))
    echo "Waiting for query $execution_id... ($state, ${elapsed}s elapsed)" >&2
  done
  echo "Error: Timed out after ${ATHENA_MAX_POLL}s waiting for query $execution_id" >&2
  return 1
}

athena_get_results() {
  local execution_id="$1" max_items="${2:-1000}"
  [[ -z "$execution_id" ]] && { echo "Error: query execution ID required" >&2; return 1; }
  aws athena get-query-results \
    --region "$ATHENA_REGION" \
    --query-execution-id "$execution_id" \
    --max-items "$max_items" \
    --output json | jq '{
      columns: [.ResultSet.ResultSetMetadata.ColumnInfo[] | {Name, Type}],
      rows: [.ResultSet.Rows[1:][] | [.Data[].VarCharValue]],
      next_token: .NextToken
    }'
}

# --- High-level helpers ---

# Run a query synchronously: submit, wait, return results
athena_query() {
  local query="$1" workgroup="${2:-$ATHENA_WORKGROUP}" database="$3"
  [[ -z "$query" ]] && { echo "Error: SQL query required" >&2; return 1; }

  local execution_id
  execution_id=$(athena_start_query "$query" "$workgroup" "$database") || return 1
  echo "Query started: $execution_id" >&2

  athena_wait_for_query "$execution_id" || return 1
  echo "Query succeeded, fetching results..." >&2
  athena_get_results "$execution_id"
}

# Preview N rows from a table
athena_preview() {
  local database="$1" table="$2" limit="${3:-10}" workgroup="${4:-$ATHENA_WORKGROUP}"
  [[ -z "$database" || -z "$table" ]] && { echo "Error: database and table name required" >&2; return 1; }
  athena_query "SELECT * FROM \"${database}\".\"${table}\" LIMIT ${limit}" "$workgroup" "$database"
}

# --- Workgroup operations ---

athena_list_workgroups() {
  aws athena list-work-groups \
    --region "$ATHENA_REGION" \
    --output json | jq -r '.WorkGroups[] | "\(.Name)\t\(.State)\t\(.Description // "")"' | sort | column -t -s $'\t'
}
