#!/bin/bash
# ODL (Operational Data Lake) query helpers for JET.
# Sources jet-aws-athena's athena_query.sh for low-level Athena operations.
# Usage: source odl_queries.sh && odl_recent_deployments "my-app"
set -o pipefail

# --- Locate and source jet-aws-athena ---

_odl_find_athena_script() {
  local candidates=(
    "${JET_ATHENA_SCRIPT:-}"
    "${HOME}/.agents/skills/jet-aws-athena/scripts/athena_query.sh"
    "$(dirname "${BASH_SOURCE[0]}")/../../jet-aws-athena/scripts/athena_query.sh"
  )
  for c in "${candidates[@]}"; do
    [[ -n "$c" && -f "$c" ]] && { echo "$c"; return 0; }
  done
  echo "Error: Cannot find jet-aws-athena/scripts/athena_query.sh. Set JET_ATHENA_SCRIPT env var." >&2
  return 1
}

_ATHENA_SCRIPT=$(_odl_find_athena_script) || exit 1
# shellcheck source=/dev/null
source "$_ATHENA_SCRIPT"

# --- Configuration ---

ODL_DATABASE="${ODL_DATABASE:-transformed_data}"
ODL_WORKGROUP="${ODL_WORKGROUP:-primary}"
# Production environment type filter (accounts for inconsistent naming)
ODL_PROD_FILTER="environment.type IN ('production', 'prod', 'prd')"

# --- Deployment queries ---

# Recent deployments for an application
# Usage: odl_recent_deployments <app_name> [hours] [env_filter]
#   app_name:   application name (case-sensitive, supports LIKE patterns with %)
#   hours:      lookback window in hours (default: 24)
#   env_filter: "prod" (default), "all", or a specific environment.type value
odl_recent_deployments() {
  local app="$1" hours="${2:-24}" env="${3:-prod}"
  [[ -z "$app" ]] && { echo "Error: app name required" >&2; return 1; }

  local env_clause
  case "$env" in
    prod|production) env_clause="AND $ODL_PROD_FILTER" ;;
    all) env_clause="" ;;
    *) env_clause="AND environment.type = '${env}'" ;;
  esac

  local since
  since=$(date -u -v-${hours}H +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null \
    || date -u -d "${hours} hours ago" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null)

  athena_query "
    SELECT DISTINCT
      application.name AS app,
      application.owners AS team,
      environment.name AS env,
      environment.type AS env_type,
      deployment.start_time,
      deployment.end_time,
      deployment.status,
      deployment.app_version AS version,
      deployment.orchestrator,
      deployment.user AS deployer,
      deployment.host_technology AS infra,
      deployment.deployment_url
    FROM ${ODL_DATABASE}.all_dora_deployments
    WHERE application.name LIKE '${app}'
      AND deployment.start_time >= '${since}'
      ${env_clause}
    ORDER BY deployment.start_time DESC
    LIMIT 50
  " "$ODL_WORKGROUP"
}

# Failed deployments across all applications
# Usage: odl_failed_deployments [hours] [env_filter]
odl_failed_deployments() {
  local hours="${1:-24}" env="${2:-prod}"

  local env_clause
  case "$env" in
    prod|production) env_clause="AND $ODL_PROD_FILTER" ;;
    all) env_clause="" ;;
    *) env_clause="AND environment.type = '${env}'" ;;
  esac

  local since
  since=$(date -u -v-${hours}H +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null \
    || date -u -d "${hours} hours ago" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null)

  athena_query "
    SELECT DISTINCT
      application.name AS app,
      application.owners AS team,
      environment.name AS env,
      deployment.start_time,
      deployment.app_version AS version,
      deployment.orchestrator,
      deployment.user AS deployer,
      deployment.deployment_url
    FROM ${ODL_DATABASE}.all_dora_deployments
    WHERE deployment.status = 'fail'
      AND deployment.start_time >= '${since}'
      ${env_clause}
    ORDER BY deployment.start_time DESC
    LIMIT 100
  " "$ODL_WORKGROUP"
}

# Deployments by owning team
# Usage: odl_deployments_by_team <team_name> [hours] [env_filter]
odl_deployments_by_team() {
  local team="$1" hours="${2:-24}" env="${3:-prod}"
  [[ -z "$team" ]] && { echo "Error: team name required" >&2; return 1; }

  local env_clause
  case "$env" in
    prod|production) env_clause="AND $ODL_PROD_FILTER" ;;
    all) env_clause="" ;;
    *) env_clause="AND environment.type = '${env}'" ;;
  esac

  local since
  since=$(date -u -v-${hours}H +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null \
    || date -u -d "${hours} hours ago" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null)

  athena_query "
    SELECT DISTINCT
      application.name AS app,
      environment.name AS env,
      deployment.start_time,
      deployment.status,
      deployment.app_version AS version,
      deployment.orchestrator,
      deployment.user AS deployer,
      deployment.deployment_url
    FROM ${ODL_DATABASE}.all_dora_deployments
    WHERE application.owners LIKE '${team}'
      AND deployment.start_time >= '${since}'
      ${env_clause}
    ORDER BY deployment.start_time DESC
    LIMIT 100
  " "$ODL_WORKGROUP"
}

# Deployment history/timeline for an application
# Usage: odl_deployment_timeline <app_name> [days] [env_filter]
odl_deployment_timeline() {
  local app="$1" days="${2:-7}" env="${3:-prod}"
  [[ -z "$app" ]] && { echo "Error: app name required" >&2; return 1; }

  local env_clause
  case "$env" in
    prod|production) env_clause="AND $ODL_PROD_FILTER" ;;
    all) env_clause="" ;;
    *) env_clause="AND environment.type = '${env}'" ;;
  esac

  local since
  since=$(date -u -v-${days}d +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null \
    || date -u -d "${days} days ago" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null)

  athena_query "
    SELECT DISTINCT
      deployment.start_time,
      deployment.status,
      deployment.app_version AS version,
      environment.name AS env,
      deployment.orchestrator,
      deployment.user AS deployer,
      deployment.deployment_url
    FROM ${ODL_DATABASE}.all_dora_deployments
    WHERE application.name = '${app}'
      AND deployment.start_time >= '${since}'
      ${env_clause}
    ORDER BY deployment.start_time DESC
    LIMIT 200
  " "$ODL_WORKGROUP"
}

# --- Platform metadata queries ---

# Look up team information
# Usage: odl_team_info <team_name>
odl_team_info() {
  local team="$1"
  [[ -z "$team" ]] && { echo "Error: team name required" >&2; return 1; }

  athena_query "
    SELECT
      id,
      description,
      department,
      sub_department,
      tech_manager,
      senior_tech_manager,
      slack_channel_name,
      jira_project_id,
      pagerduty_escalation_policy_key,
      pagerduty_emergency_service_key,
      engineers
    FROM ${ODL_DATABASE}.platformmetadata_teams
    WHERE id LIKE '${team}'
    LIMIT 10
  " "$ODL_WORKGROUP"
}

# Find the owner of an application
# Usage: odl_app_owner <app_name>
odl_app_owner() {
  local app="$1"
  [[ -z "$app" ]] && { echo "Error: app name required" >&2; return 1; }

  athena_query "
    SELECT
      id,
      owners,
      description,
      tier,
      type,
      contribution_type,
      sonic_ring,
      github_repository.owner AS github_org,
      github_repository.name AS github_repo,
      lifecycle.status AS lifecycle_status,
      app_group
    FROM ${ODL_DATABASE}.platformmetadata_features
    WHERE id LIKE '${app}'
    LIMIT 10
  " "$ODL_WORKGROUP"
}

# Look up environment details
# Usage: odl_env_info <env_name_or_pattern>
odl_env_info() {
  local env="$1"
  [[ -z "$env" ]] && { echo "Error: environment name or pattern required" >&2; return 1; }

  athena_query "
    SELECT
      id,
      alias,
      env_type,
      owner,
      team,
      platform,
      aws_account_alias,
      aws_region,
      tags
    FROM ${ODL_DATABASE}.platformmetadata_environments
    WHERE id LIKE '${env}' OR alias LIKE '${env}'
    LIMIT 20
  " "$ODL_WORKGROUP"
}

# --- Security queries ---

# Open Wiz security issues
# Usage: odl_wiz_issues [team_or_resource] [severity] [limit]
#   team_or_resource: team name or resource name pattern (optional, shows all if omitted)
#   severity:         CRITICAL, HIGH, MEDIUM, LOW (optional)
#   limit:            max results (default: 50)
odl_wiz_issues() {
  local filter="$1" severity="$2" limit="${3:-50}"

  local where_clauses="is_latest = true AND status != 'RESOLVED'"
  [[ -n "$filter" ]] && where_clauses="${where_clauses} AND (CONTAINS(team, '${filter}') OR resource_name LIKE '%${filter}%')"
  [[ -n "$severity" ]] && where_clauses="${where_clauses} AND severity = '${severity}'"

  athena_query "
    SELECT
      id,
      title,
      severity,
      status,
      resource_type,
      resource_name,
      cloud_account,
      cloud_region,
      team,
      created_time,
      finding_url
    FROM ${ODL_DATABASE}.wiz_issues
    WHERE ${where_clauses}
    ORDER BY
      CASE severity
        WHEN 'CRITICAL' THEN 1
        WHEN 'HIGH' THEN 2
        WHEN 'MEDIUM' THEN 3
        WHEN 'LOW' THEN 4
        ELSE 5
      END,
      created_time DESC
    LIMIT ${limit}
  " "$ODL_WORKGROUP"
}

# Open Wiz vulnerabilities
# Usage: odl_wiz_vulns [team_or_resource] [severity] [limit]
odl_wiz_vulns() {
  local filter="$1" severity="$2" limit="${3:-50}"

  local where_clauses="is_latest = true AND status != 'RESOLVED'"
  [[ -n "$filter" ]] && where_clauses="${where_clauses} AND (CONTAINS(team, '${filter}') OR resource_name LIKE '%${filter}%')"
  [[ -n "$severity" ]] && where_clauses="${where_clauses} AND severity = '${severity}'"

  athena_query "
    SELECT
      id,
      name,
      severity,
      status,
      score,
      resource_type,
      resource_name,
      resource_technology,
      cloud_account,
      team,
      has_exploit,
      fixed_version,
      first_seen_time,
      finding_url
    FROM ${ODL_DATABASE}.wiz_vulnerabilities
    WHERE ${where_clauses}
    ORDER BY score DESC NULLS LAST, first_seen_time ASC
    LIMIT ${limit}
  " "$ODL_WORKGROUP"
}

# --- GitHub queries ---

# Recent PRs for a repository
# Usage: odl_recent_prs <repo_name> [days]
#   repo_name: full repo path (e.g., "org/repo") or pattern with %
#   days:      lookback window (default: 7)
odl_recent_prs() {
  local repo="$1" days="${2:-7}"
  [[ -z "$repo" ]] && { echo "Error: repo name required" >&2; return 1; }

  local since_ms
  since_ms=$(( $(date +%s) - (days * 86400) ))
  since_ms=$((since_ms * 1000))

  athena_query "
    SELECT
      repo,
      actor,
      action,
      pull_request_title,
      pull_request_url,
      FROM_UNIXTIME(timestamp / 1000) AS event_time
    FROM ${ODL_DATABASE}.github_pr_logs_clean
    WHERE repo LIKE '${repo}'
      AND timestamp >= ${since_ms}
      AND action IN ('merge', 'create', 'close')
    ORDER BY timestamp DESC
    LIMIT 100
  " "$ODL_WORKGROUP"
}

# --- Reliability queries ---

# Reliability metrics summary
# Usage: odl_reliability_summary [year]
odl_reliability_summary() {
  local year="${1:-$(date +%Y)}"

  athena_query "
    SELECT
      a.year,
      a.month,
      a.monthly_peak_avail_pct,
      a.peak_avail_running_ytd_pct,
      m.running_ytd AS mttd_running_ytd
    FROM ${ODL_DATABASE}.reliability_peak_availability_mom a
    LEFT JOIN ${ODL_DATABASE}.reliability_mttd_mom m
      ON a.year = m.year AND a.month = m.month
    WHERE a.year = ${year}
    ORDER BY a.month
  " "$ODL_WORKGROUP"
}

# --- Cost queries ---

# Cost data for an application
# Usage: odl_cost_by_app <app_name> [weeks]
odl_cost_by_app() {
  local app="$1" weeks="${2:-4}"
  [[ -z "$app" ]] && { echo "Error: app name required" >&2; return 1; }

  local since
  since=$(date -u -v-${weeks}w +"%Y-%m-%d" 2>/dev/null \
    || date -u -d "${weeks} weeks ago" +"%Y-%m-%d" 2>/dev/null)

  athena_query "
    SELECT
      app,
      environment,
      team,
      department,
      sub_department,
      date,
      cost
    FROM ${ODL_DATABASE}.finout_wow_by_component
    WHERE app LIKE '${app}'
      AND date >= DATE '${since}'
    ORDER BY date DESC
    LIMIT 100
  " "$ODL_WORKGROUP"
}
