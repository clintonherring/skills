#!/usr/bin/env bash
# CloudOps-EKS to Sonic Runtime Migrator — Environment Precheck
#
# Validates that all required tools, authentication, and environment variables
# are configured before starting the migration workflow.
#
# Usage:
#   source /path/to/scripts/precheck.sh
#   migrator_precheck          # Run all checks, print results table
#   migrator_check_tool gh     # Check a single tool

set -eo pipefail

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
  local _sts="$1" check="$2" detail="$3"
  _results+=("${_sts}|${check}|${detail}")
  if [[ "$_sts" == "FAIL" ]]; then _has_failure=1; fi
}

# ── Individual checks ────────────────────────────────────────────────────

_check_gh() {
  if ! command -v gh &>/dev/null; then
    _record "FAIL" "gh CLI" "Not installed. Install: brew install gh"
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
    _record "FAIL" "jq" "Not installed. Install: brew install jq"
    return
  fi
  _record "PASS" "jq" "$(jq --version)"
}

_check_kubectl() {
  if ! command -v kubectl &>/dev/null; then
    _record "WARN" "kubectl" "Not installed. Install: brew install kubectl"
    return
  fi
  local ver
  ver=$(kubectl version --client -o json 2>/dev/null | jq -r '.clientVersion.gitVersion' 2>/dev/null || echo "unknown")
  _record "PASS" "kubectl" "$ver"
}

_check_helmfile() {
  if ! command -v helmfile &>/dev/null; then
    _record "WARN" "helmfile" "Not installed. Install: brew install helmfile"
    return
  fi
  local ver
  ver=$(helmfile --version 2>/dev/null | head -1)
  _record "PASS" "helmfile" "$ver"
}

_check_terraform() {
  if ! command -v terraform &>/dev/null && ! command -v terragrunt &>/dev/null; then
    _record "WARN" "terraform/terragrunt" "Neither installed. Install: brew install terraform (or terragrunt)"
    return
  fi
  if command -v terraform &>/dev/null; then
    _record "PASS" "terraform" "$(terraform --version -json 2>/dev/null | jq -r '.terraform_version' 2>/dev/null || terraform --version | head -1)"
  fi
  if command -v terragrunt &>/dev/null; then
    _record "PASS" "terragrunt" "$(terragrunt --version 2>/dev/null | head -1)"
  fi
}

_check_base64() {
  if ! command -v base64 &>/dev/null; then
    _record "FAIL" "base64" "Not installed (should be pre-installed on macOS/Linux)"
    return
  fi
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
    _record "FAIL" "BACKSTAGE_API_KEY" "Not set. Open Backstage → DevTools → Network → copy Bearer token"
    return
  fi
  local http_code
  http_code=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer ${BACKSTAGE_API_KEY}" \
    "${BACKSTAGE_BACKEND_URL:-https://backstagebackend.eu-west-1.production.jet-internal.com}/api/search/query?term=test&types%5B0%5D=techdocs" \
    --connect-timeout 5 2>/dev/null || echo "000")
  if [[ "$http_code" == "200" ]]; then
    _record "PASS" "BACKSTAGE_API_KEY" "Set and validated (HTTP 200)"
  elif [[ "$http_code" == "401" || "$http_code" == "403" ]]; then
    _record "FAIL" "BACKSTAGE_API_KEY" "Set but invalid or expired (HTTP $http_code). Get a fresh token."
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
  echo "CloudOps-EKS → Sonic Runtime Migrator — Environment Precheck"
  echo "============================================================="
  echo ""

  _check_gh
  _check_git
  _check_curl
  _check_jq
  _check_base64
  _check_kubectl
  _check_helmfile
  _check_terraform
  _check_ghe_network
  _check_gh_auth
  _check_backstage_key

  # Print results table
  printf "\n%-6s  %-22s  %s\n" "Status" "Check" "Detail"
  printf "%-6s  %-22s  %s\n" "------" "----------------------" "------"
  for row in "${_results[@]}"; do
    IFS='|' read -r _sts check detail <<< "$row"
    case "$_sts" in
      PASS) printf "${_PASS}    %-22s  %s\n" "$check" "$detail" ;;
      FAIL) printf "${_FAIL}    %-22s  %s\n" "$check" "$detail" ;;
      WARN) printf "${_WARN}    %-22s  %s\n" "$check" "$detail" ;;
    esac
  done

  echo ""
  if [[ $_has_failure -eq 1 ]]; then
    echo -e "${_RED}Some checks failed. Please fix the issues above before proceeding.${_NC}"
    return 1
  else
    echo -e "${_GREEN}All checks passed. Ready to start the migration workflow.${_NC}"
    return 0
  fi
}

# Single-tool check
migrator_check_tool() {
  local tool="${1:-}"
  case "$tool" in
    gh)        _check_gh ;;
    git)       _check_git ;;
    curl)      _check_curl ;;
    jq)        _check_jq ;;
    base64)    _check_base64 ;;
    kubectl)   _check_kubectl ;;
    helmfile)  _check_helmfile ;;
    terraform) _check_terraform ;;
    gh-auth)   _check_gh_auth ;;
    backstage) _check_backstage_key ;;
    network)   _check_ghe_network ;;
    *) echo "Unknown tool: $tool. Available: gh, git, curl, jq, base64, kubectl, helmfile, terraform, gh-auth, backstage, network" ;;
  esac
}

# Run automatically if executed directly (not sourced)
# Compatible with both bash and zsh
if [[ "${BASH_SOURCE[0]:-$0}" == "${0}" ]]; then
  migrator_precheck
fi
