#!/bin/bash
# Wiz GraphQL API helpers. Requires: wizcli (auth), jq, curl.
# Usage: source wiz_api.sh && wiz_get_issue <id-or-url>
set -o pipefail

WIZ_AUTH_FILE="${WIZ_AUTH_FILE:-$HOME/.wiz/auth.json}"

# --- Token management ---

_wiz_auth_field() { jq -r "$1" "$WIZ_AUTH_FILE" 2>/dev/null; }

# 0 = expired, 1 = still valid
_wiz_token_expired() {
  local ea
  ea=$(_wiz_auth_field '.expires_at')
  [[ -z "$ea" || "$ea" == "null" ]] && return 0
  # Strip fractional seconds for jq compat, 60s buffer
  jq -n --arg ea "$ea" \
    '($ea | split(".")[0] + "Z" | fromdateiso8601) - now < 60' | grep -q true
}

# Delegate refresh to wizcli (direct HTTP refresh is WAF-blocked)
# Supports service account auth (WIZ_CLIENT_ID + WIZ_CLIENT_SECRET) and
# interactive device-code auth as fallback.
_wiz_refresh_token() {
  command -v wizcli &>/dev/null || { echo "Error: wizcli not found. Install: brew install wizcli" >&2; return 1; }
  if [[ -n "${WIZ_CLIENT_ID:-}" && -n "${WIZ_CLIENT_SECRET:-}" ]]; then
    wizcli auth --id "$WIZ_CLIENT_ID" --secret "$WIZ_CLIENT_SECRET" &>/dev/null && ! _wiz_token_expired && {
      echo "Token refreshed via wizcli service account." >&2; return 0;
    }
    echo "Error: Service account auth failed. Check WIZ_CLIENT_ID / WIZ_CLIENT_SECRET." >&2
    return 1
  fi
  wizcli auth --use-device-code --no-browser &>/dev/null && ! _wiz_token_expired && {
    echo "Token refreshed via wizcli device code." >&2; return 0;
  }
  echo "Error: Token refresh failed. Run: wizcli auth --use-device-code" >&2
  return 1
}

get_wiz_token() {
  [[ -f "$WIZ_AUTH_FILE" ]] || { echo "Error: Not authenticated. Set WIZ_CLIENT_ID + WIZ_CLIENT_SECRET or run: wizcli auth --use-device-code" >&2; return 1; }
  local token
  token=$(_wiz_auth_field '.access_token')
  [[ -n "$token" && "$token" != "null" ]] || { echo "Error: No access token in $WIZ_AUTH_FILE" >&2; return 1; }
  if _wiz_token_expired; then
    echo "Token expired, refreshing..." >&2
    _wiz_refresh_token || return 1
    token=$(_wiz_auth_field '.access_token')
  fi
  echo "$token"
}

get_wiz_api_url() {
  local dc
  dc=$(_wiz_auth_field '.data_center')
  [[ -n "$dc" && "$dc" != "null" ]] || { echo "Error: No data_center in $WIZ_AUTH_FILE" >&2; return 1; }
  echo "https://api.${dc}.app.wiz.io/graphql"
}

# --- URL parsing ---

# Accept a UUID or a Wiz issue URL, return the UUID
extract_issue_id() {
  local input="$1"
  # Already a bare UUID?
  echo "$input" | grep -oE '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' && return 0
  # URL-decode the fragment and extract UUID
  local decoded uuid
  decoded=$(printf '%b' "$(echo "${input#*#}" | sed 's/%/\\x/g')")
  uuid=$(echo "$decoded" | grep -oE '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}' | head -1)
  [[ -n "$uuid" ]] && { echo "$uuid"; return 0; }
  echo "Error: Could not extract issue ID from: $input" >&2
  return 1
}

# --- GraphQL ---

wiz_query() {
  local query="$1" variables="$2"
  [[ -z "$query" ]] && { echo "Error: query required" >&2; return 1; }
  : "${variables:="{}"}"
  local token api_url
  token=$(get_wiz_token) || return 1
  api_url=$(get_wiz_api_url) || return 1
  curl -s -X POST "$api_url" \
    -H "Authorization: Bearer ${token}" \
    -H "Content-Type: application/json" \
    -d "$(jq -n -c --arg q "$query" --argjson v "$variables" '{query:$q,variables:$v}')"
}

# --- Project operations ---

wiz_search_projects() {
  local search="$1"
  [[ -z "$search" ]] && { echo "Error: search term required" >&2; return 1; }
  wiz_query 'query ($f: ProjectFilters) {
  projects(filterBy: $f, first: 20) {
    nodes { id name slug }
  }
}' "$(jq -n -c --arg s "$search" '{f:{search:$s}}')"
}

# Resolve a project name to its UUID (first match)
_wiz_resolve_project_id() {
  local name="$1" result
  result=$(wiz_search_projects "$name") || return 1
  local id
  id=$(echo "$result" | jq -r '.data.projects.nodes[0].id // empty')
  [[ -n "$id" ]] || { echo "Error: No project found matching '$name'" >&2; return 1; }
  echo "$id"
}

# --- Issue operations ---

wiz_get_issue() {
  local issue_id
  [[ -z "$1" ]] && { echo "Error: Issue ID or URL required" >&2; return 1; }
  issue_id=$(extract_issue_id "$1") || return 1

  wiz_query 'query IssueDetails($id: ID!) {
  issue(id: $id) {
    id
    status
    severity
    createdAt
    updatedAt
    dueAt
    resolvedAt
    statusChangedAt
    note
    resolutionReason
    control {
      id
      name
      description
      severity
      type
      resolutionRecommendation
      sourceCloudConfigurationRule {
        id
        name
        shortId
        remediationInstructions
      }
      securitySubCategories {
        title
        category {
          name
          framework {
            name
          }
        }
      }
    }
    project {
      id
      name
      slug
      businessUnit
      riskProfile {
        businessImpact
      }
    }
    entitySnapshot {
      id
      type
      nativeType
      name
      status
      cloudPlatform
      cloudProviderURL
      providerId
      region
      resourceGroupExternalId
      subscriptionExternalId
      subscriptionName
      subscriptionTags
      tags
    }
    serviceTickets {
      externalId
      name
      url
    }
  }
}' "$(jq -n -c --arg id "$issue_id" '{id:$id}')"
}

# --- Vulnerability report helpers ---

# Shared: fetch vulnerability findings for a project, return JSON to stdout
_wiz_fetch_vuln_findings() {
  local project_id="$1" filter="$2" limit="${3:-2000}"
  local variables
  variables=$(jq -n -c --argjson f "$filter" --argjson l "$limit" '{filterBy: $f, first: $l}')
  wiz_query 'query ($filterBy: VulnerabilityFindingFilters, $first: Int) {
  vulnerabilityFindings(filterBy: $filterBy, first: $first) {
    nodes {
      name
      vendorSeverity
      score
      hasExploit
      hasCisaKevExploit
      hasFix
    }
    totalCount
  }
}' "$variables"
}

# Prioritized vulnerability report (compact)
# Usage: wiz_vuln_report <team-name> [--has-fix] [--has-exploit]
wiz_vuln_report() {
  local team_name="" has_fix="false" has_exploit="false"
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --has-fix)     has_fix="true"; shift ;;
      --has-exploit) has_exploit="true"; shift ;;
      *)             [[ -z "$team_name" ]] && team_name="$1"; shift ;;
    esac
  done
  [[ -z "$team_name" ]] && { echo "Usage: wiz_vuln_report <team-name> [--has-fix] [--has-exploit]" >&2; return 1; }

  local project_id
  project_id=$(_wiz_resolve_project_id "$team_name") || return 1

  local filter
  filter=$(jq -n -c --arg pid "$project_id" \
    --argjson fix "$has_fix" --argjson exploit "$has_exploit" \
    '{projectIdV2: {equals: [$pid]}}
     | if $fix     then . + {hasFix: true}     else . end
     | if $exploit then . + {hasExploit: true}  else . end')

  local tmpfile
  tmpfile=$(mktemp)
  _wiz_fetch_vuln_findings "$project_id" "$filter" 2000 > "$tmpfile" || { rm -f "$tmpfile"; return 1; }

  local nodes='[.data.vulnerabilityFindings.nodes] | flatten'

  echo "=== PRIORITIZED VULNERABILITY REPORT: $team_name ==="
  [[ "$has_fix" == "true" ]] && echo "(Filtered: has fix available)"
  [[ "$has_exploit" == "true" ]] && echo "(Filtered: has known exploit)"
  echo ""

  echo "=== PRIORITY 1: CISA KEV (Actively Exploited) ==="
  jq -r "$nodes | map(select(.hasCisaKevExploit == true)) |
    group_by(.name) | map({cve: .[0].name, severity: .[0].vendorSeverity, score: (.[0].score // 0), hasFix: (.[0].hasFix // false), count: length}) |
    .[] | \"[\(.severity)] \(.cve) | CVSS: \(.score) | Fix: \(.hasFix) | Count: \(.count)\"" "$tmpfile" 2>/dev/null || echo "None"

  echo ""
  echo "=== PRIORITY 2: CRITICAL + Known Exploit ==="
  jq -r "$nodes | map(select(.vendorSeverity == \"CRITICAL\" and .hasExploit == true and .hasCisaKevExploit != true)) |
    group_by(.name) | map({cve: .[0].name, severity: .[0].vendorSeverity, score: (.[0].score // 0), hasFix: (.[0].hasFix // false), count: length}) |
    .[] | \"[\(.severity)] \(.cve) | CVSS: \(.score) | Fix: \(.hasFix) | Count: \(.count)\"" "$tmpfile" 2>/dev/null || echo "None"

  echo ""
  echo "=== PRIORITY 3: HIGH + Known Exploit (Top 10 by count) ==="
  jq -r "$nodes | map(select(.vendorSeverity == \"HIGH\" and .hasExploit == true)) |
    group_by(.name) | map({cve: .[0].name, severity: .[0].vendorSeverity, score: (.[0].score // 0), hasFix: (.[0].hasFix // false), count: length}) |
    sort_by(.count) | reverse | .[0:10] |
    .[] | \"[\(.severity)] \(.cve) | CVSS: \(.score) | Fix: \(.hasFix) | Count: \(.count)\"" "$tmpfile" 2>/dev/null || echo "None"

  echo ""
  echo "=== PRIORITY 4: HIGH Severity - No Fix ==="
  jq -r "$nodes | map(select(.vendorSeverity == \"HIGH\" and .hasFix != true)) |
    group_by(.name) | map({cve: .[0].name, severity: .[0].vendorSeverity, score: (.[0].score // 0), hasFix: .hasFix, count: length}) |
    .[] | \"[\(.severity)] \(.cve) | CVSS: \(.score) | Fix: \(.hasFix) | Count: \(.count)\"" "$tmpfile" 2>/dev/null || echo "None"

  echo ""
  echo "=== SUMMARY ==="
  jq -r "$nodes | group_by(.vendorSeverity) |
    map({severity: .[0].vendorSeverity, count: length}) |
    .[] | \"\(.severity): \(.count)\"" "$tmpfile"

  rm -f "$tmpfile"
}

# Full vulnerability analysis report (detailed, formatted tables)
# Usage: wiz_vuln_report_full <team-name>
wiz_vuln_report_full() {
  local team_name="$1"
  [[ -z "$team_name" ]] && { echo "Usage: wiz_vuln_report_full <team-name>" >&2; return 1; }

  local project_id
  project_id=$(_wiz_resolve_project_id "$team_name") || return 1

  local filter
  filter=$(jq -n -c --arg pid "$project_id" '{projectIdV2: {equals: [$pid]}}')

  local tmpfile
  tmpfile=$(mktemp)
  _wiz_fetch_vuln_findings "$project_id" "$filter" 5000 > "$tmpfile" || { rm -f "$tmpfile"; return 1; }

  local nodes='[.data.vulnerabilityFindings.nodes] | flatten'
  local total
  total=$(jq -r '.data.vulnerabilityFindings.totalCount' "$tmpfile")

  echo ""
  echo "================================================================================"
  echo "                    VULNERABILITY PRIORITY ANALYSIS"
  echo "                              $team_name"
  echo "================================================================================"
  echo ""
  echo "Total Findings: $total"
  echo ""

  echo "--------------------------------------------------------------------------------"
  echo "SEVERITY SUMMARY"
  echo "--------------------------------------------------------------------------------"
  jq -r "$nodes | group_by(.vendorSeverity) |
    map({severity: .[0].vendorSeverity, count: length}) | .[] |
    if .severity == \"CRITICAL\" then \"CRITICAL:  \(.count)\"
    elif .severity == \"HIGH\" then \"HIGH:      \(.count)\"
    elif .severity == \"MEDIUM\" then \"MEDIUM:    \(.count)\"
    elif .severity == \"LOW\" then \"LOW:       \(.count)\"
    else \"OTHER:     \(.count)\" end" "$tmpfile"

  local tbl_header tbl_sep
  tbl_header=$(printf "%-15s | %-25s | %-8s | %-6s | %-10s" "SEVERITY" "CVE" "CVSS" "FIX" "INSTANCES")
  tbl_sep="--------------------------------------------------------------------------------"

  _wiz_print_table() {
    local title="$1" jq_expr="$2"
    echo ""
    echo "================================================================================"
    echo "$title"
    echo "================================================================================"
    echo "$tbl_header"
    echo "$tbl_sep"
    jq -r "$jq_expr" "$tmpfile" 2>/dev/null | while IFS='|' read -r sev cve score fix count; do
      printf "%-15s | %-25s | %-8s | %-6s | %-10s\n" "$sev" "$cve" "$score" "$fix" "$count"
    done || echo "None found"
  }

  _wiz_print_table "PRIORITY 1: CISA KEV (Actively Exploited in Real Attacks)" \
    "$nodes | map(select(.hasCisaKevExploit == true)) |
     group_by(.name) | map({cve: .[0].name, severity: .[0].vendorSeverity, score: (.[0].score // 0), hasFix: (.[0].hasFix // false), count: length}) |
     .[] | \"\(.severity) | \(.cve) | \(.score) | \(.hasFix) | \(.count)\""

  _wiz_print_table "PRIORITY 2: CRITICAL Severity + Known Exploit" \
    "$nodes | map(select(.vendorSeverity == \"CRITICAL\" and .hasExploit == true)) |
     group_by(.name) | map({cve: .[0].name, severity: .[0].vendorSeverity, score: (.[0].score // 0), hasFix: (.[0].hasFix // false), count: length}) |
     .[] | \"\(.severity) | \(.cve) | \(.score) | \(.hasFix) | \(.count)\""

  _wiz_print_table "PRIORITY 3: HIGH Severity + Known Exploit (Top 20)" \
    "$nodes | map(select(.vendorSeverity == \"HIGH\" and .hasExploit == true)) |
     group_by(.name) | map({cve: .[0].name, severity: .[0].vendorSeverity, score: (.[0].score // 0), hasFix: (.[0].hasFix // false), count: length}) |
     sort_by(.score) | reverse | .[0:20] |
     .[] | \"\(.severity) | \(.cve) | \(.score) | \(.hasFix) | \(.count)\""

  _wiz_print_table "PRIORITY 4: MEDIUM Severity + Known Exploit (Top 15)" \
    "$nodes | map(select(.vendorSeverity == \"MEDIUM\" and .hasExploit == true)) |
     group_by(.name) | map({cve: .[0].name, severity: .[0].vendorSeverity, score: (.[0].score // 0), hasFix: (.[0].hasFix // false), count: length}) |
     sort_by(.score) | reverse | .[0:15] |
     .[] | \"\(.severity) | \(.cve) | \(.score) | \(.hasFix) | \(.count)\""

  echo ""
  echo "================================================================================"
  echo "PRIORITY 5: NO FIX AVAILABLE (Top 15)"
  echo "================================================================================"
  printf "%-15s | %-25s | %-8s | %-8s | %-10s\n" "SEVERITY" "CVE" "CVSS" "EXPLOIT" "INSTANCES"
  echo "$tbl_sep"
  jq -r "$nodes | map(select(.hasFix != true)) |
    group_by(.name) | map({cve: .[0].name, severity: .[0].vendorSeverity, score: (.[0].score // 0), hasExploit: (.[0].hasExploit // false), count: length}) |
    sort_by(.score) | reverse | .[0:15] |
    .[] | \"\(.severity) | \(.cve) | \(.score) | \(.hasExploit) | \(.count)\"" "$tmpfile" 2>/dev/null | while IFS='|' read -r sev cve score exploit count; do
    printf "%-15s | %-25s | %-8s | %-8s | %-10s\n" "$sev" "$cve" "$score" "$exploit" "$count"
  done || echo "None found"

  echo ""
  echo "================================================================================"
  echo "TOP 10 MOST COMMON VULNERABILITIES"
  echo "================================================================================"
  printf "%-30s | %-10s | %-8s | %-10s\n" "CVE" "SEVERITY" "CVSS" "INSTANCES"
  echo "$tbl_sep"
  jq -r "$nodes | group_by(.name) |
    map({cve: .[0].name, severity: .[0].vendorSeverity, score: (.[0].score // 0), count: length}) |
    sort_by(.count) | reverse | .[0:10] |
    .[] | \"\(.cve) | \(.severity) | \(.score) | \(.count)\"" "$tmpfile" 2>/dev/null | while IFS='|' read -r cve severity score count; do
    printf "%-30s | %-10s | %-8s | %-10s\n" "$cve" "$severity" "$score" "$count"
  done

  rm -f "$tmpfile"
}

# --- Issue operations ---

wiz_list_issues() {
  local statuses="" severities="" projects="" project_name="" limit=20
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --status)       statuses="$2";     shift 2 ;;
      --severity)     severities="$2";   shift 2 ;;
      --project)      projects="$2";     shift 2 ;;
      --project-name) project_name="$2"; shift 2 ;;
      --limit)        limit="$2";        shift 2 ;;
      *) echo "Error: Unknown option: $1" >&2; return 1 ;;
    esac
  done

  # Resolve project name to UUID if --project-name was used
  if [[ -n "$project_name" && -z "$projects" ]]; then
    projects=$(_wiz_resolve_project_id "$project_name") || return 1
  fi

  local variables
  variables=$(jq -n -c \
    --arg s "$statuses" --arg sv "$severities" --arg p "$projects" --argjson l "$limit" \
    '{first: $l, orderBy: {field: "SEVERITY", direction: "DESC"},
      filterBy: ({}
        | if $s  != "" then .status   = ($s  | split(",") | map(ltrimstr(" "))) else . end
        | if $sv != "" then .severity = ($sv | split(",") | map(ltrimstr(" "))) else . end
        | if $p  != "" then .project  = ($p  | split(",") | map(ltrimstr(" "))) else . end)}')

  wiz_query 'query ListIssues($filterBy: IssueFilters, $first: Int, $after: String, $orderBy: IssueOrder) {
  issues(filterBy: $filterBy, first: $first, after: $after, orderBy: $orderBy) {
    nodes {
      id
      status
      severity
      createdAt
      updatedAt
      control {
        id
        name
        description
        severity
        type
        resolutionRecommendation
        sourceCloudConfigurationRule {
          id
          name
          shortId
          remediationInstructions
        }
      }
      project {
        id
        name
        slug
      }
      entitySnapshot {
        id
        type
        nativeType
        name
        status
        cloudPlatform
        cloudProviderURL
        providerId
        region
        subscriptionExternalId
        subscriptionName
        tags
      }
      serviceTickets {
        externalId
        name
        url
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
    totalCount
  }
}' "$variables"
}
