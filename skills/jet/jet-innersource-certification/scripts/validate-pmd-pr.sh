#!/usr/bin/env bash
#
# JET InnerSource PlatformMetadata PR Validator
#
# Validates a PlatformMetadata pull request for InnerSource certification correctness.
# Checks the feature JSON, the owning team JSON, the PR checklist, and optionally
# cross-references the linked GitHub repository.
#
# Usage: bash validate-pmd-pr.sh <PR_URL_OR_NUMBER> [--repo-check] [--json]
#
# Arguments:
#   PR_URL_OR_NUMBER   The PR URL (https://github.je-labs.com/metadata/PlatformMetadata/pull/123)
#                      or just the PR number (123)
#   --repo-check       Also clone and validate the linked repository (slower)
#   --json             Output results as JSON
#
set -euo pipefail

# --- Parse arguments ---------------------------------------------------------

PR_INPUT="${1:-}"
REPO_CHECK=false
OUTPUT_JSON=false
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for arg in "$@"; do
  case "$arg" in
    --repo-check) REPO_CHECK=true ;;
    --json) OUTPUT_JSON=true ;;
  esac
done

if [[ -z "$PR_INPUT" ]]; then
  echo "Usage: bash validate-pmd-pr.sh <PR_URL_OR_NUMBER> [--repo-check] [--json]"
  echo ""
  echo "Examples:"
  echo "  bash validate-pmd-pr.sh 23149"
  echo "  bash validate-pmd-pr.sh https://github.je-labs.com/metadata/PlatformMetadata/pull/23149"
  echo "  bash validate-pmd-pr.sh 23149 --repo-check"
  exit 1
fi

# Extract PR number from URL or use directly
PR_NUMBER="$PR_INPUT"
if [[ "$PR_INPUT" == http* ]]; then
  PR_NUMBER=$(echo "$PR_INPUT" | grep -oE '[0-9]+$')
fi

GHE_HOST="github.je-labs.com"
PMD_REPO="metadata/PlatformMetadata"

# --- Counters ----------------------------------------------------------------

PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0
TOTAL_COUNT=0

declare -a RESULTS=()

# --- Helpers -----------------------------------------------------------------

color_reset="\033[0m"
color_green="\033[0;32m"
color_red="\033[0;31m"
color_yellow="\033[0;33m"
color_cyan="\033[0;36m"
color_bold="\033[1m"

escape_json() {
  local s="$1"
  s="${s//\\/\\\\}"
  s="${s//\"/\\\"}"
  s="${s//$'\n'/\\n}"
  s="${s//$'\t'/\\t}"
  printf '%s' "$s"
}

pass() {
  local name="$1" detail="${2:-}"
  ((PASS_COUNT++))
  ((TOTAL_COUNT++))
  RESULTS+=("{\"name\":\"$(escape_json "$name")\",\"status\":\"PASS\",\"detail\":\"$(escape_json "$detail")\"}")
  if [[ "$OUTPUT_JSON" == false ]]; then
    printf "  ${color_green}PASS${color_reset}  %-55s %s\n" "$name" "$detail"
  fi
}

fail() {
  local name="$1" detail="${2:-}"
  ((FAIL_COUNT++))
  ((TOTAL_COUNT++))
  RESULTS+=("{\"name\":\"$(escape_json "$name")\",\"status\":\"FAIL\",\"detail\":\"$(escape_json "$detail")\"}")
  if [[ "$OUTPUT_JSON" == false ]]; then
    printf "  ${color_red}FAIL${color_reset}  %-55s %s\n" "$name" "$detail"
  fi
}

warn() {
  local name="$1" detail="${2:-}"
  ((WARN_COUNT++))
  ((TOTAL_COUNT++))
  RESULTS+=("{\"name\":\"$(escape_json "$name")\",\"status\":\"WARN\",\"detail\":\"$(escape_json "$detail")\"}")
  if [[ "$OUTPUT_JSON" == false ]]; then
    printf "  ${color_yellow}WARN${color_reset}  %-55s %s\n" "$name" "$detail"
  fi
}

section() {
  if [[ "$OUTPUT_JSON" == false ]]; then
    echo ""
    printf "${color_bold}${color_cyan}── %s ──${color_reset}\n" "$1"
    echo ""
  fi
}

# --- Fetch PR data -----------------------------------------------------------

if [[ "$OUTPUT_JSON" == false ]]; then
  echo ""
  printf "${color_bold}JET InnerSource PlatformMetadata PR Validator${color_reset}\n"
  printf "PR: ${color_cyan}https://${GHE_HOST}/${PMD_REPO}/pull/${PR_NUMBER}${color_reset}\n"
fi

# Get PR metadata
PR_JSON=$(gh api --hostname "$GHE_HOST" "/repos/$PMD_REPO/pulls/$PR_NUMBER" 2>&1)
if echo "$PR_JSON" | grep -q '"message"'; then
  echo "ERROR: Failed to fetch PR #${PR_NUMBER}: $(echo "$PR_JSON" | jq -r '.message')"
  exit 1
fi

PR_TITLE=$(echo "$PR_JSON" | jq -r '.title')
PR_BODY=$(echo "$PR_JSON" | jq -r '.body // ""')
PR_STATE=$(echo "$PR_JSON" | jq -r '.state')

if [[ "$OUTPUT_JSON" == false ]]; then
  printf "Title: ${color_cyan}%s${color_reset}\n" "$PR_TITLE"
  printf "State: %s\n" "$PR_STATE"
fi

# Get changed files
PR_FILES_JSON=$(gh api --hostname "$GHE_HOST" "/repos/$PMD_REPO/pulls/$PR_NUMBER/files" 2>&1)
FEATURE_FILES=$(echo "$PR_FILES_JSON" | jq -r '.[].filename | select(startswith("Data/global_features/"))')
TEAM_FILES=$(echo "$PR_FILES_JSON" | jq -r '.[].filename | select(startswith("Data/teams/"))')

if [[ -z "$FEATURE_FILES" && -z "$TEAM_FILES" ]]; then
  if [[ "$OUTPUT_JSON" == false ]]; then
    echo ""
    printf "  ${color_yellow}This PR does not modify any feature or team files. Nothing to validate for InnerSource.${color_reset}\n"
    echo ""
  fi
  exit 0
fi

# --- Validate each feature file ----------------------------------------------

for feature_file in $FEATURE_FILES; do
  feature_name=$(basename "$feature_file" .json)

  section "Feature: $feature_name ($feature_file)"

  # Get the file content from the PR's head branch
  HEAD_SHA=$(echo "$PR_JSON" | jq -r '.head.sha')
  FEATURE_CONTENT=$(gh api --hostname "$GHE_HOST" "/repos/$PMD_REPO/contents/$feature_file?ref=$HEAD_SHA" 2>&1 | jq -r '.content // ""' | base64 -d 2>/dev/null || echo "")

  if [[ -z "$FEATURE_CONTENT" ]]; then
    # File might be deleted
    STATUS=$(echo "$PR_FILES_JSON" | jq -r ".[] | select(.filename == \"$feature_file\") | .status")
    if [[ "$STATUS" == "removed" ]]; then
      warn "File status" "Feature file removed in this PR -- skipping checks"
      continue
    fi
    fail "Feature file readable" "Could not read feature file content"
    continue
  fi

  # Parse key fields
  CONTRIBUTION_TYPE=$(echo "$FEATURE_CONTENT" | jq -r '.contribution_type // "not set"')
  TRUSTED_COMMITTERS=$(echo "$FEATURE_CONTENT" | jq -r '.trusted_committers // [] | .[]' 2>/dev/null)
  TC_COUNT=$(echo "$FEATURE_CONTENT" | jq '.trusted_committers // [] | length')
  OWNERS=$(echo "$FEATURE_CONTENT" | jq -r '.owners // "not set"')
  DESCRIPTION=$(echo "$FEATURE_CONTENT" | jq -r '.description // ""')
  FEATURE_ID=$(echo "$FEATURE_CONTENT" | jq -r '.id // ""')
  RUN_BOOK_PATH=$(echo "$FEATURE_CONTENT" | jq -r '.run_book_path // "not set"')
  GH_OWNER=$(echo "$FEATURE_CONTENT" | jq -r '.github_repository.owner // "not set"')
  GH_NAME=$(echo "$FEATURE_CONTENT" | jq -r '.github_repository.name // "not set"')
  TIER=$(echo "$FEATURE_CONTENT" | jq -r '.tier // "not set"')
  LIFECYCLE_STATUS=$(echo "$FEATURE_CONTENT" | jq -r '.lifecycle.status // "not set"')

  # --- Check: contribution_type ---
  if [[ "$CONTRIBUTION_TYPE" == "innerSourceBasic" || "$CONTRIBUTION_TYPE" == "innerSourceAdvanced" ]]; then
    pass "contribution_type" "$CONTRIBUTION_TYPE"
  elif [[ "$CONTRIBUTION_TYPE" == "not set" ]]; then
    fail "contribution_type" "Not set. Must be 'innerSourceBasic' or 'innerSourceAdvanced' for InnerSource"
  else
    warn "contribution_type" "Set to '$CONTRIBUTION_TYPE' -- not an InnerSource type"
  fi

  IS_INNERSOURCE=false
  if [[ "$CONTRIBUTION_TYPE" == "innerSourceBasic" || "$CONTRIBUTION_TYPE" == "innerSourceAdvanced" ]]; then
    IS_INNERSOURCE=true
  fi

  # --- Check: feature id matches filename ---
  if [[ "$FEATURE_ID" == "$feature_name" ]]; then
    pass "id matches filename" "id='$FEATURE_ID' matches '$feature_name.json'"
  else
    fail "id matches filename" "id='$FEATURE_ID' does not match filename '$feature_name.json'"
  fi

  # --- Check: description ---
  if [[ ${#DESCRIPTION} -ge 10 ]]; then
    pass "description" "\"${DESCRIPTION:0:60}...\""
  elif [[ ${#DESCRIPTION} -ge 3 ]]; then
    warn "description" "Very short: \"$DESCRIPTION\". Consider a more descriptive text"
  else
    fail "description" "Missing or too short (min 3 chars required by schema)"
  fi

  # --- Check: owners ---
  if [[ "$OWNERS" != "not set" && -n "$OWNERS" ]]; then
    pass "owners" "$OWNERS"
  else
    fail "owners" "Not set"
  fi

  # --- Check: tier ---
  if [[ "$TIER" =~ ^[1-3]$ ]]; then
    pass "tier" "Tier $TIER"
  else
    fail "tier" "Must be 1, 2, or 3. Got: $TIER"
  fi

  # --- Check: lifecycle ---
  if [[ "$LIFECYCLE_STATUS" != "not set" ]]; then
    pass "lifecycle.status" "$LIFECYCLE_STATUS"
  else
    fail "lifecycle.status" "Not set"
  fi

  # --- Check: github_repository ---
  if [[ "$GH_OWNER" != "not set" && "$GH_NAME" != "not set" ]]; then
    pass "github_repository" "$GH_OWNER/$GH_NAME"
  else
    fail "github_repository" "Not set. Required for InnerSource (need a repo to contribute to)"
  fi

  # --- Check: run_book_path ---
  if [[ "$RUN_BOOK_PATH" != "not set" && -n "$RUN_BOOK_PATH" ]]; then
    pass "run_book_path" "$RUN_BOOK_PATH"
  else
    if [[ "$IS_INNERSOURCE" == true ]]; then
      fail "run_book_path" "Not set. Required for InnerSource certification"
    else
      warn "run_book_path" "Not set"
    fi
  fi

  # --- InnerSource-specific checks ---
  if [[ "$IS_INNERSOURCE" == true ]]; then

    section "InnerSource Requirements for: $feature_name"

    # --- Check: trusted_committers ---
    if [[ "$TC_COUNT" -ge 1 ]]; then
      tc_list=$(echo "$FEATURE_CONTENT" | jq -r '.trusted_committers | join(", ")')
      pass "trusted_committers" "$TC_COUNT defined: $tc_list"
    else
      fail "trusted_committers" "No trusted committers defined. At least 1 is required"
    fi

    # --- Cross-check: team exists ---
    TEAM_CONTENT=""
    if [[ "$OWNERS" != "not set" ]]; then
      TEAM_CONTENT=$(gh api --hostname "$GHE_HOST" "/repos/$PMD_REPO/contents/Data/teams/$OWNERS.json" 2>&1 | jq -r '.content // ""' | base64 -d 2>/dev/null || echo "")
      if [[ -n "$TEAM_CONTENT" ]]; then
        pass "Team exists in PlatformMetadata" "Data/teams/$OWNERS.json found"
      else
        fail "Team exists in PlatformMetadata" "Data/teams/$OWNERS.json not found"
      fi
    fi

    # --- Cross-check: team has slack_channel_name ---
    if [[ -n "$TEAM_CONTENT" ]]; then
      TEAM_SLACK=$(echo "$TEAM_CONTENT" | jq -r '.slack_channel_name // ""')
      if [[ -n "$TEAM_SLACK" ]]; then
        pass "Team slack_channel_name" "#$TEAM_SLACK"
      else
        fail "Team slack_channel_name" "Not set in team definition. Required for InnerSource"
      fi
    fi

    # --- Cross-check: trusted_committers are team engineers ---
    if [[ -n "$TEAM_CONTENT" && "$TC_COUNT" -ge 1 ]]; then
      TEAM_ENGINEERS=$(echo "$TEAM_CONTENT" | jq -r '.engineers // [] | .[]')
      TC_NOT_IN_TEAM=""
      while IFS= read -r tc; do
        [[ -z "$tc" ]] && continue
        if ! echo "$TEAM_ENGINEERS" | grep -qx "$tc"; then
          TC_NOT_IN_TEAM="${TC_NOT_IN_TEAM}${tc}, "
        fi
      done <<< "$TRUSTED_COMMITTERS"

      if [[ -z "$TC_NOT_IN_TEAM" ]]; then
        pass "Trusted committers in team" "All trusted committers are listed in team engineers"
      else
        TC_NOT_IN_TEAM="${TC_NOT_IN_TEAM%, }"
        warn "Trusted committers in team" "Not in team engineers list: $TC_NOT_IN_TEAM"
      fi
    fi

    # --- Check: PR checklist ---
    section "PR Checklist Validation"

    check_pr_item() {
      local label="$1" pattern="$2"
      if echo "$PR_BODY" | grep -qE "\[x\].*${pattern}"; then
        pass "$label" "Checked in PR"
      elif echo "$PR_BODY" | grep -qE "\[ \].*${pattern}"; then
        fail "$label" "Unchecked in PR body"
      else
        warn "$label" "Checklist item not found in PR body"
      fi
    }

    check_pr_item "Checklist: Team slack channel"         "[Tt]eam [Ss]lack [Cc]hannel"
    check_pr_item "Checklist: Trusted Committer(s)"       "[Tt]rusted [Cc]ommitter"
    check_pr_item "Checklist: Product Manager"            "[Pp]roduct [Mm]anager"
    check_pr_item "Checklist: README"                     "README"
    check_pr_item "Checklist: Runbook"                    "[Rr]unbook"
    check_pr_item "Checklist: Contribution document"      "[Cc]ontribution"
    check_pr_item "Checklist: Communication"              "[Cc]ommunicat"
    check_pr_item "Checklist: Test Automation"            "[Tt]est [Aa]utomation"
    check_pr_item "Checklist: SonarQube"                  "[Ss]onarqube\|[Ss]onarQube\|[Ss]onar[Qq]ube"

    # --- Optional: repo cross-check ---
    if [[ "$REPO_CHECK" == true && "$GH_OWNER" != "not set" && "$GH_NAME" != "not set" ]]; then
      section "Repository Cross-Check: $GH_OWNER/$GH_NAME"

      TMPDIR_REPO=$(mktemp -d)
      trap "rm -rf '$TMPDIR_REPO'" EXIT

      if gh repo clone "$GHE_HOST/$GH_OWNER/$GH_NAME" "$TMPDIR_REPO/repo" -- --depth 1 2>/dev/null; then
        pass "Repository cloneable" "$GH_OWNER/$GH_NAME"

        REPO_RESULT=$(bash "$SCRIPT_DIR/validate.sh" --json 2>/dev/null < /dev/null)
        REPO_ROOT="$TMPDIR_REPO/repo"
        export REPO_ROOT

        # Run validate.sh and capture results
        pushd "$TMPDIR_REPO/repo" > /dev/null
        REPO_RESULT=$(bash "$SCRIPT_DIR/validate.sh" --json 2>/dev/null || true)
        popd > /dev/null

        REPO_MUST_FAIL=$(echo "$REPO_RESULT" | jq '.summary.must.fail')
        REPO_MUST_PASS=$(echo "$REPO_RESULT" | jq '.summary.must.pass')
        REPO_SHOULD_FAIL=$(echo "$REPO_RESULT" | jq '.summary.should.fail')
        REPO_SHOULD_PASS=$(echo "$REPO_RESULT" | jq '.summary.should.pass')

        if [[ "$REPO_MUST_FAIL" -eq 0 ]]; then
          pass "Repo MUST checks" "All $REPO_MUST_PASS MUST checks pass"
        else
          fail "Repo MUST checks" "$REPO_MUST_FAIL MUST check(s) failed, $REPO_MUST_PASS passed"
        fi

        if [[ "$REPO_SHOULD_FAIL" -eq 0 ]]; then
          pass "Repo SHOULD checks" "All $REPO_SHOULD_PASS SHOULD checks pass"
        else
          warn "Repo SHOULD checks" "$REPO_SHOULD_FAIL SHOULD check(s) need attention, $REPO_SHOULD_PASS passed"
        fi

        # List individual repo failures
        REPO_FAILURES=$(echo "$REPO_RESULT" | jq -r '.checks[] | select(.status == "FAIL") | "  - [\(.priority)] \(.name): \(.detail)"')
        if [[ -n "$REPO_FAILURES" && "$OUTPUT_JSON" == false ]]; then
          echo ""
          printf "  ${color_red}Repo failures:${color_reset}\n"
          echo "$REPO_FAILURES"
        fi

        rm -rf "$TMPDIR_REPO"
        trap - EXIT
      else
        fail "Repository cloneable" "Could not clone $GH_OWNER/$GH_NAME"
        rm -rf "$TMPDIR_REPO"
        trap - EXIT
      fi
    fi
  fi
done

# --- Also validate any team files in the PR ----------------------------------

for team_file in $TEAM_FILES; do
  team_name=$(basename "$team_file" .json)

  section "Team: $team_name ($team_file)"

  HEAD_SHA=$(echo "$PR_JSON" | jq -r '.head.sha')
  TEAM_FILE_CONTENT=$(gh api --hostname "$GHE_HOST" "/repos/$PMD_REPO/contents/$team_file?ref=$HEAD_SHA" 2>&1 | jq -r '.content // ""' | base64 -d 2>/dev/null || echo "")

  if [[ -z "$TEAM_FILE_CONTENT" ]]; then
    STATUS=$(echo "$PR_FILES_JSON" | jq -r ".[] | select(.filename == \"$team_file\") | .status")
    if [[ "$STATUS" == "removed" ]]; then
      warn "File status" "Team file removed in this PR -- skipping checks"
      continue
    fi
    fail "Team file readable" "Could not read team file content"
    continue
  fi

  TEAM_SLACK=$(echo "$TEAM_FILE_CONTENT" | jq -r '.slack_channel_name // ""')
  TEAM_ENGINEERS=$(echo "$TEAM_FILE_CONTENT" | jq '.engineers // [] | length')
  TEAM_DESC=$(echo "$TEAM_FILE_CONTENT" | jq -r '.description // ""')

  if [[ -n "$TEAM_SLACK" ]]; then
    pass "slack_channel_name" "#$TEAM_SLACK"
  else
    fail "slack_channel_name" "Not set. Required for InnerSource teams"
  fi

  if [[ "$TEAM_ENGINEERS" -ge 1 ]]; then
    pass "engineers" "$TEAM_ENGINEERS engineer(s) listed"
  else
    fail "engineers" "No engineers listed"
  fi

  if [[ ${#TEAM_DESC} -ge 10 ]]; then
    pass "description" "\"${TEAM_DESC:0:60}...\""
  else
    warn "description" "Missing or very short team description"
  fi
done

# --- Summary -----------------------------------------------------------------

if [[ "$OUTPUT_JSON" == false ]]; then
  echo ""
  printf "${color_bold}${color_cyan}── Summary ──${color_reset}\n"
  echo ""
  printf "  ${color_green}%d passed${color_reset}, ${color_red}%d failed${color_reset}, ${color_yellow}%d warnings${color_reset} (out of %d checks)\n" \
    "$PASS_COUNT" "$FAIL_COUNT" "$WARN_COUNT" "$TOTAL_COUNT"
  echo ""

  if [[ "$FAIL_COUNT" -eq 0 ]]; then
    printf "  ${color_green}${color_bold}All checks passed. PR looks good for InnerSource certification.${color_reset}\n"
  else
    printf "  ${color_red}${color_bold}%d check(s) failed. PR needs corrections before InnerSource certification.${color_reset}\n" "$FAIL_COUNT"
  fi

  if [[ "$WARN_COUNT" -gt 0 ]]; then
    printf "  ${color_yellow}%d warning(s) should be reviewed.${color_reset}\n" "$WARN_COUNT"
  fi

  if [[ "$REPO_CHECK" == false ]]; then
    echo ""
    printf "  ${color_yellow}Tip:${color_reset} Run with --repo-check to also validate the linked repository.\n"
  fi
  echo ""
else
  printf '{\n'
  printf '  "pr": %d,\n' "$PR_NUMBER"
  printf '  "title": "%s",\n' "$(escape_json "$PR_TITLE")"
  printf '  "summary": {"pass": %d, "fail": %d, "warn": %d, "total": %d},\n' \
    "$PASS_COUNT" "$FAIL_COUNT" "$WARN_COUNT" "$TOTAL_COUNT"
  printf '  "checks": [\n'
  for i in "${!RESULTS[@]}"; do
    if [[ $i -lt $((${#RESULTS[@]} - 1)) ]]; then
      printf '    %s,\n' "${RESULTS[$i]}"
    else
      printf '    %s\n' "${RESULTS[$i]}"
    fi
  done
  printf '  ]\n'
  printf '}\n'
fi

if [[ "$FAIL_COUNT" -gt 0 ]]; then
  exit 1
fi
exit 0
