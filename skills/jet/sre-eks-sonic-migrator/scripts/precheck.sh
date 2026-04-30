#!/usr/bin/env bash
# SRE-EKS to Sonic Runtime Migrator — Environment Precheck
#
# Validates that all required tools, authentication, and environment variables
# are configured before starting the migration workflow.
#
# Usage:
#   source /path/to/scripts/precheck.sh
#   migrator_precheck          # Run all checks, print results table
#   migrator_check_tool gh     # Check a single tool

set -euo pipefail

# Colours (disabled when not a terminal)
if [[ -t 1 ]]; then
  _GREEN='\033[0;32m'; _RED='\033[0;31m'; _YELLOW='\033[0;33m'; _NC='\033[0m'
else
  _GREEN=''; _RED=''; _YELLOW=''; _NC=''
fi

_PASS="${_GREEN}PASS${_NC}"
_FAIL="${_RED}FAIL${_NC}"
_WARN="${_YELLOW}WARN${_NC}"

_results=()
_has_failure=0

_record() {
  local status="$1" check="$2" detail="$3"
  _results+=("${status}|${check}|${detail}")
  if [[ "$status" == "FAIL" ]]; then _has_failure=1; fi
}

# ── Individual checks ────────────────────────────────────────────────────

_check_gh() {
  if ! command -v gh &>/dev/null; then
    _record "FAIL" "gh CLI" "Not installed. Install GitHub CLI before running the migrator (e.g. brew install gh)"
    return
  fi
  local ver
  ver=$(gh --version | head -1)
  _record "PASS" "gh CLI" "$ver"
}

_check_gh_auth() {
  if ! command -v gh &>/dev/null; then
    _record "FAIL" "GHE authentication" "gh CLI not installed"
    return
  fi
  if gh auth status --hostname github.je-labs.com &>/dev/null 2>&1; then
    _record "PASS" "GHE authentication" "Authenticated to github.je-labs.com"
  else
    _record "FAIL" "GHE authentication" "Not authenticated. Run: gh auth login --hostname github.je-labs.com"
  fi
}

_check_git() {
  if ! command -v git &>/dev/null; then
    _record "FAIL" "git" "Not installed"
    return
  fi
  local ver
  ver=$(git --version)
  _record "PASS" "git" "$ver"
}

_check_curl() {
  if ! command -v curl &>/dev/null; then
    _record "FAIL" "curl" "Not installed"
    return
  fi
  _record "PASS" "curl" "$(curl --version | head -1)"
}

_check_jq() {
  if ! command -v jq &>/dev/null; then
    _record "FAIL" "jq" "Not installed. Install jq before running the migrator (e.g. brew install jq)"
    return
  fi
  _record "PASS" "jq" "$(jq --version)"
}

_check_base64() {
  if ! command -v base64 &>/dev/null; then
    _record "FAIL" "base64" "Not installed (should be pre-installed on macOS/Linux)"
    return
  fi
  # Quick functional test
  local result
  result=$(echo "dGVzdA==" | base64 -d 2>/dev/null || echo "dGVzdA==" | base64 --decode 2>/dev/null || echo "DECODE_FAILED")
  if [[ "$result" == "test" ]]; then
    _record "PASS" "base64" "Working"
  else
    _record "FAIL" "base64" "Decode test failed"
  fi
}

_check_backstage_key() {
  if [[ -z "${BACKSTAGE_API_KEY:-}" ]]; then
    _record "FAIL" "BACKSTAGE_API_KEY" "Not set. Export it before running the migrator. Check https://github.je-labs.com/ai-platform/skills/blob/master/skills/jet-company-standards/references/backstage.md#getting-a-token for instructions."
    return
  fi
  # Optionally validate with a lightweight search query
  local http_code
  local backstage_url="${BACKSTAGE_BACKEND_URL:-https://backstagebackend.eu-west-1.production.jet-internal.com}"
  http_code=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer ${BACKSTAGE_API_KEY}" \
    "${backstage_url}/api/search/query?term=test&types%5B0%5D=techdocs" \
    --connect-timeout 5 2>/dev/null || echo "000")
  if [[ "$http_code" == "200" ]]; then
    _record "PASS" "BACKSTAGE_API_KEY" "Set and validated (HTTP 200)"
  elif [[ "$http_code" == "401" || "$http_code" == "403" ]]; then
    _record "FAIL" "BACKSTAGE_API_KEY" "Set but invalid or expired (HTTP $http_code)"
  elif [[ "$http_code" == "000" ]]; then
    _record "WARN" "BACKSTAGE_API_KEY" "Set but could not reach Backstage API (network issue?)"
  else
    _record "WARN" "BACKSTAGE_API_KEY" "Set but got unexpected response (HTTP $http_code)"
  fi
}

_check_ghe_network() {
  local http_code
  http_code=$(curl -s -o /dev/null -w "%{http_code}" \
    "https://github.je-labs.com" \
    --connect-timeout 5 2>/dev/null || echo "000")
  if [[ "$http_code" == "000" ]]; then
    _record "FAIL" "GHE network" "Cannot reach github.je-labs.com (VPN connected?)"
  else
    _record "PASS" "GHE network" "github.je-labs.com reachable (HTTP $http_code)"
  fi
}

# ── Main precheck function ───────────────────────────────────────────────

migrator_precheck() {
  _results=()
  _has_failure=0

  echo ""
  echo "SRE-EKS → Sonic Runtime Migrator — Environment Precheck"
  echo "========================================================"
  echo ""

  _check_gh
  _check_git
  _check_curl
  _check_jq
  _check_base64
  _check_ghe_network
  _check_gh_auth
  _check_backstage_key

  # Print results table
  printf "\n%-6s  %-22s  %s\n" "Status" "Check" "Detail"
  printf "%-6s  %-22s  %s\n" "------" "----------------------" "------"
  for row in "${_results[@]}"; do
    IFS='|' read -r status check detail <<< "$row"
    case "$status" in
      PASS) printf "${_PASS}    %-22s  %s\n" "$check" "$detail" ;;
      FAIL) printf "${_FAIL}    %-22s  %s\n" "$check" "$detail" ;;
      WARN) printf "${_WARN}    %-22s  %s\n" "$check" "$detail" ;;
    esac
  done

  echo ""
  echo -e "${_YELLOW}Model recommendation:${_NC} This skill involves complex multi-phase reasoning and multi-repo"
  echo "code generation. For best results, use Claude Opus 4.6 (recommended) or Claude Sonnet 4.5."
  echo ""
  if [[ $_has_failure -eq 1 ]]; then
    echo -e "${_RED}Some checks failed. Please fix the issues above before proceeding.${_NC}"
    return 1
  else
    echo -e "${_GREEN}All checks passed. Ready to start the migration workflow.${_NC}"
    return 0
  fi
}

# Single-tool check (for use in SKILL.md inline checks)
migrator_check_tool() {
  local tool="${1:-}"
  case "$tool" in
    gh)        _check_gh ;;
    git)       _check_git ;;
    curl)      _check_curl ;;
    jq)        _check_jq ;;
    base64)    _check_base64 ;;
    gh-auth)   _check_gh_auth ;;
    backstage) _check_backstage_key ;;
    network)   _check_ghe_network ;;
    *) echo "Unknown tool: $tool. Available: gh, git, curl, jq, base64, gh-auth, backstage, network" ;;
  esac
}

# Run automatically if executed directly (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  migrator_precheck
fi
