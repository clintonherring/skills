#!/usr/bin/env bash
# pd_list — paginate through any PagerDuty REST API v2 collection endpoint.
#
# Usage:
#   source scripts/pd_list.sh
#   pd_list <endpoint> [query_params]
#
# Examples:
#   pd_list incidents "statuses[]=triggered&statuses[]=acknowledged"
#   pd_list services "query=payments"
#   pd_list escalation_policies
#
# Requires: PD_API_KEY to be set in the environment.
# Each page of raw JSON is printed to stdout; pipe through jq as needed:
#   pd_list incidents | jq -s '[.[].incidents[]]'
#
# Exits non-zero and prints a diagnostic to stderr on HTTP errors (401, 429, 5xx, etc.).

pd_list() {
  local endpoint="$1"; shift
  local params="${1:-}"
  local offset=0; local limit=100; local more="true"
  while [ "$more" = "true" ]; do
    local resp http_code
    resp=$(curl -s -w "\n%{http_code}" \
      -H "Authorization: Token token=$PD_API_KEY" \
      -H "Accept: application/vnd.pagerduty+json;version=2" \
      "https://api.pagerduty.com/${endpoint}?limit=${limit}&offset=${offset}${params:+&${params}}")
    http_code=$(printf '%s' "$resp" | tail -1)
    resp=$(printf '%s' "$resp" | sed '$d')
    if ! [[ "$http_code" =~ ^[0-9]+$ ]]; then
      echo "pd_list: curl failed (no HTTP response) for /${endpoint}" >&2
      return 1
    fi
    if [ "$http_code" -lt 200 ] || [ "$http_code" -ge 300 ]; then
      echo "pd_list: HTTP $http_code from /${endpoint}" >&2
      echo "$resp" | jq -r '.error.message // .message // "unknown error"' >&2 2>/dev/null || true
      return 1
    fi
    echo "$resp"
    more=$(echo "$resp" | jq -r '.more // false')
    offset=$((offset + limit))
  done
}
