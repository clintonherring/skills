#!/usr/bin/env bash
#
# jira-comment.sh — Post a formatted ADF comment to a Jira Cloud issue.
#
# Usage:
#   jira-comment.sh ISSUE-KEY ADF_JSON_FILE
#   jira-comment.sh ISSUE-KEY --body '{"type":"doc",...}'
#
# Examples:
#   jira-comment.sh AND-1234 /tmp/comment.json
#   jira-comment.sh AND-1234 --body '{"type":"doc","version":1,"content":[...]}'
#
# Why this exists:
#   acli's `comment create --body/--body-file` silently strips ADF text marks
#   (bold, italic, code, links) and rejects heading nodes entirely.
#   This script bypasses acli and uses the Jira REST API v3 directly,
#   reusing acli's OAuth token from the macOS keychain.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
CLOUD_ID_CACHE="$SKILL_DIR/.cloud_id"
ACLI_CONFIG="$HOME/.config/acli/global_auth_config.yaml"

# --- Argument parsing ---

if [[ $# -lt 2 ]]; then
  echo "Usage: jira-comment.sh ISSUE-KEY ADF_JSON_FILE" >&2
  echo "       jira-comment.sh ISSUE-KEY --body '{...}'" >&2
  exit 1
fi

ISSUE_KEY="$1"
shift

if [[ ! "$ISSUE_KEY" =~ ^[A-Z][A-Z0-9]+-[0-9]+$ ]]; then
  echo "Error: Invalid issue key: $ISSUE_KEY (expected format: PROJ-123)" >&2
  exit 1
fi

if [[ "$1" == "--body" ]]; then
  shift
  ADF_BODY="$1"
else
  ADF_FILE="$1"
  if [[ ! -f "$ADF_FILE" ]]; then
    echo "Error: File not found: $ADF_FILE" >&2
    exit 1
  fi
  ADF_BODY=$(cat "$ADF_FILE")
fi

# --- Cloud ID (cached) ---

get_cloud_id() {
  if [[ -f "$CLOUD_ID_CACHE" ]]; then
    cat "$CLOUD_ID_CACHE"
    return
  fi

  if [[ ! -f "$ACLI_CONFIG" ]]; then
    echo "Error: acli config not found at $ACLI_CONFIG" >&2
    echo "Run 'acli auth login' first." >&2
    exit 1
  fi

  local cloud_id
  cloud_id=$(ACLI_CONFIG_PATH="$ACLI_CONFIG" python3 -c "
import yaml, sys, os
config_path = os.environ['ACLI_CONFIG_PATH']
with open(config_path) as f:
    config = yaml.safe_load(f)
profiles = config.get('profiles', [])
if not profiles:
    sys.exit('No profiles found in acli config')
print(profiles[0]['cloud_id'])
" 2>/dev/null)

  if [[ -z "$cloud_id" ]]; then
    # Fallback: parse with grep if PyYAML is not available
    cloud_id=$(grep -m1 '^\s*cloud_id:' "$ACLI_CONFIG" | awk '{print $2}')
  fi

  if [[ -z "$cloud_id" ]]; then
    echo "Error: Could not extract cloud_id from $ACLI_CONFIG" >&2
    exit 1
  fi

  echo "$cloud_id" > "$CLOUD_ID_CACHE"
  echo "$cloud_id"
}

# --- OAuth token (fresh each time — tokens expire hourly) ---

get_access_token() {
  local raw_token
  raw_token=$(security find-generic-password -s "acli" -w 2>/dev/null) || {
    echo "Error: No acli token found in macOS keychain." >&2
    echo "Run 'acli auth login' first." >&2
    exit 1
  }

  echo "$raw_token" \
    | sed 's/^go-keyring-base64://' \
    | base64 -d \
    | gunzip \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])"
}

# --- Post comment ---

CLOUD_ID=$(get_cloud_id)
ACCESS_TOKEN=$(get_access_token)

PAYLOAD=$(echo "$ADF_BODY" | python3 -c "
import json, sys
body = json.load(sys.stdin)
print(json.dumps({'body': body}))
")

RESPONSE=$(echo "$PAYLOAD" | curl -s -w "\n%{http_code}" -X POST \
  "https://api.atlassian.com/ex/jira/$CLOUD_ID/rest/api/3/issue/$ISSUE_KEY/comment" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  --data-binary @-)

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [[ "$HTTP_CODE" == "201" ]]; then
  COMMENT_ID=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "unknown")
  echo "Comment added to $ISSUE_KEY (comment id: $COMMENT_ID)"
  echo "https://justeattakeaway.atlassian.net/browse/$ISSUE_KEY"
else
  echo "Error: Failed to add comment (HTTP $HTTP_CODE)" >&2
  echo "$BODY" >&2
  exit 1
fi
