#!/usr/bin/env bash
#
# JET InnerSource Certification Validator
#
# Validates a repository against JET InnerSource certification requirements.
# Run from the root of the repository you want to validate.
#
# Usage: bash validate.sh [--json]
#
# Options:
#   --json    Output results as JSON instead of formatted text
#
set -euo pipefail

# --- Configuration -----------------------------------------------------------

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
OUTPUT_JSON=false

if [[ "${1:-}" == "--json" ]]; then
  OUTPUT_JSON=true
fi

# --- Counters ----------------------------------------------------------------

MUST_PASS=0
MUST_FAIL=0
MUST_TOTAL=0
SHOULD_PASS=0
SHOULD_FAIL=0
SHOULD_TOTAL=0

# --- Result storage for JSON output ------------------------------------------

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
  local priority="$1" name="$2" detail="${3:-}"
  if [[ "$priority" == "MUST" ]]; then
    ((MUST_PASS++))
    ((MUST_TOTAL++))
  else
    ((SHOULD_PASS++))
    ((SHOULD_TOTAL++))
  fi
  RESULTS+=("{\"priority\":\"$(escape_json "$priority")\",\"name\":\"$(escape_json "$name")\",\"status\":\"PASS\",\"detail\":\"$(escape_json "$detail")\"}")
  if [[ "$OUTPUT_JSON" == false ]]; then
    printf "  ${color_green}PASS${color_reset}  %-50s %s\n" "$name" "$detail"
  fi
}

fail() {
  local priority="$1" name="$2" detail="${3:-}"
  if [[ "$priority" == "MUST" ]]; then
    ((MUST_FAIL++))
    ((MUST_TOTAL++))
  else
    ((SHOULD_FAIL++))
    ((SHOULD_TOTAL++))
  fi
  RESULTS+=("{\"priority\":\"$(escape_json "$priority")\",\"name\":\"$(escape_json "$name")\",\"status\":\"FAIL\",\"detail\":\"$(escape_json "$detail")\"}")
  if [[ "$OUTPUT_JSON" == false ]]; then
    printf "  ${color_red}FAIL${color_reset}  %-50s %s\n" "$name" "$detail"
  fi
}

warn() {
  local priority="$1" name="$2" detail="${3:-}"
  # Warnings count toward the priority but don't increment pass/fail
  if [[ "$priority" == "MUST" ]]; then
    ((MUST_TOTAL++))
  else
    ((SHOULD_TOTAL++))
  fi
  RESULTS+=("{\"priority\":\"$(escape_json "$priority")\",\"name\":\"$(escape_json "$name")\",\"status\":\"WARN\",\"detail\":\"$(escape_json "$detail")\"}")
  if [[ "$OUTPUT_JSON" == false ]]; then
    printf "  ${color_yellow}WARN${color_reset}  %-50s %s\n" "$name" "$detail"
  fi
}

section() {
  if [[ "$OUTPUT_JSON" == false ]]; then
    echo ""
    printf "${color_bold}${color_cyan}── %s ──${color_reset}\n" "$1"
    echo ""
  fi
}

# --- Utility functions -------------------------------------------------------

# Case-insensitive file finder. Returns 0 if at least one match is found.
find_file_ci() {
  local pattern="$1"
  find "$REPO_ROOT" -maxdepth 3 -iname "$pattern" -not -path '*/.git/*' -not -path '*/node_modules/*' -not -path '*/vendor/*' 2>/dev/null | head -1
}

# Check if a file has more than N non-empty lines
file_has_content() {
  local file="$1" min_lines="${2:-3}"
  if [[ -f "$file" ]]; then
    local count
    count=$(grep -c -v '^\s*$' "$file" 2>/dev/null || echo "0")
    [[ "$count" -ge "$min_lines" ]]
  else
    return 1
  fi
}

# Search for a pattern in any file under a directory
grep_recursive() {
  local pattern="$1" dir="${2:-$REPO_ROOT}"
  grep -rl "$pattern" "$dir" --include='*.yml' --include='*.yaml' --include='*.json' --include='*.md' --include='*.toml' --include='*.xml' --include='*.gradle' --include='*.csproj' --include='*.props' 2>/dev/null | head -1
}

# --- Checks ------------------------------------------------------------------

check_readme() {
  local readme
  readme=$(find_file_ci "README.md")
  if [[ -z "$readme" ]]; then
    fail "MUST" "README.md" "File not found"
    return
  fi
  if file_has_content "$readme" 5; then
    pass "MUST" "README.md" "Found at ${readme#$REPO_ROOT/}"
  else
    fail "MUST" "README.md" "File exists but appears to be a stub (fewer than 5 non-empty lines)"
  fi
}

check_contributing() {
  local file
  file=$(find_file_ci "CONTRIBUTING.md")
  if [[ -z "$file" ]]; then
    # Also check for contributing.md inside docs/
    file=$(find_file_ci "contributing.md")
  fi
  if [[ -n "$file" ]]; then
    pass "MUST" "CONTRIBUTING.md" "Found at ${file#$REPO_ROOT/}"
  else
    fail "MUST" "CONTRIBUTING.md" "File not found. Use the template in templates/CONTRIBUTING.md"
  fi
}

check_communication() {
  local file
  file=$(find_file_ci "COMMUNICATION.md")
  if [[ -z "$file" ]]; then
    file=$(find_file_ci "team-communication.md")
  fi
  if [[ -n "$file" ]]; then
    pass "MUST" "COMMUNICATION.md" "Found at ${file#$REPO_ROOT/}"
  else
    fail "MUST" "COMMUNICATION.md" "File not found. Use the template in templates/COMMUNICATION.md"
  fi
}

check_runbook() {
  local file
  file=$(find_file_ci "runbook*")
  if [[ -z "$file" ]]; then
    file=$(find_file_ci "RUNBOOK*")
  fi
  if [[ -z "$file" ]]; then
    # Check inside docs/
    file=$(find "$REPO_ROOT" -maxdepth 4 -iname "*runbook*" -not -path '*/.git/*' 2>/dev/null | head -1)
  fi
  if [[ -n "$file" ]]; then
    if file_has_content "$file" 3; then
      pass "MUST" "Runbook" "Found at ${file#$REPO_ROOT/}"
    else
      warn "MUST" "Runbook" "Found at ${file#$REPO_ROOT/} but it appears empty or trivial (fewer than 3 non-empty lines)"
    fi
  else
    fail "MUST" "Runbook" "No runbook found (looked for runbook.md, RUNBOOK.md, docs/*runbook*)"
  fi
}

check_test_automation() {
  local found=false detail=""

  # Look for common test directory patterns
  for dir in "test" "tests" "Test" "Tests" "__tests__" "spec" "specs" "test_*" "*Tests" "*Test" "*.Tests" "*.Test"; do
    if find "$REPO_ROOT" -maxdepth 3 -type d -iname "$dir" -not -path '*/.git/*' -not -path '*/node_modules/*' 2>/dev/null | grep -q .; then
      found=true
      detail="Test directory found"
      break
    fi
  done

  # Look for test config files
  if [[ "$found" == false ]]; then
    for cfg in "jest.config*" "vitest.config*" "pytest.ini" "pyproject.toml" "*.test.*" "*.spec.*" "xunit*" "nunit*" ".nunit" "karma.conf*" "mocha*" "phpunit*"; do
      if find "$REPO_ROOT" -maxdepth 3 -iname "$cfg" -not -path '*/.git/*' -not -path '*/node_modules/*' 2>/dev/null | grep -q .; then
        found=true
        detail="Test configuration found"
        break
      fi
    done
  fi

  # Look for test references in build files
  if [[ "$found" == false ]]; then
    if grep_recursive "test" "$REPO_ROOT" | grep -qiE '(jest|xunit|nunit|pytest|mocha|vitest|cypress|playwright)' 2>/dev/null; then
      found=true
      detail="Test framework reference found in config"
    fi
  fi

  if [[ "$found" == true ]]; then
    pass "MUST" "Test automation" "$detail"
  else
    fail "MUST" "Test automation" "No test directories or test configurations found"
  fi
}

check_sonarqube() {
  local found=false detail=""

  # Check GHA workflows for sonar references
  if [[ -d "$REPO_ROOT/.github/workflows" ]]; then
    if grep -rli "sonar" "$REPO_ROOT/.github/workflows/" 2>/dev/null | grep -q .; then
      found=true
      detail="SonarQube found in GitHub Actions workflows"
    fi
  fi

  # Check for sonar config files
  if [[ "$found" == false ]]; then
    for cfg in "sonar-project.properties" ".sonarcloud.properties" "sonar*.properties"; do
      if find "$REPO_ROOT" -maxdepth 2 -iname "$cfg" -not -path '*/.git/*' 2>/dev/null | grep -q .; then
        found=true
        detail="SonarQube configuration file found"
        break
      fi
    done
  fi

  # Check for sonar references in build files
  if [[ "$found" == false ]]; then
    if grep -rli "sonar" "$REPO_ROOT" --include='*.csproj' --include='*.props' --include='*.gradle' --include='*.xml' --include='Makefile' --include='*.yml' --include='*.yaml' 2>/dev/null | grep -q .; then
      found=true
      detail="SonarQube reference found in build files"
    fi
  fi

  if [[ "$found" == true ]]; then
    pass "MUST" "SonarQube integration" "$detail"
  else
    fail "MUST" "SonarQube integration" "No SonarQube configuration or references found"
  fi
}

check_github_actions() {
  if [[ -d "$REPO_ROOT/.github/workflows" ]]; then
    local count
    count=$(find "$REPO_ROOT/.github/workflows" -name '*.yml' -o -name '*.yaml' 2>/dev/null | wc -l | tr -d ' ')
    if [[ "$count" -gt 0 ]]; then
      pass "MUST" "GitHub Actions CI/CD" "$count workflow(s) found"
    else
      fail "MUST" "GitHub Actions CI/CD" ".github/workflows/ exists but contains no workflow files"
    fi
  else
    fail "MUST" "GitHub Actions CI/CD" ".github/workflows/ directory not found"
  fi
}

check_codeowners() {
  if [[ -f "$REPO_ROOT/.github/CODEOWNERS" ]] || [[ -f "$REPO_ROOT/CODEOWNERS" ]] || [[ -f "$REPO_ROOT/docs/CODEOWNERS" ]]; then
    pass "SHOULD" "CODEOWNERS" "File found"
  else
    fail "SHOULD" "CODEOWNERS" ".github/CODEOWNERS not found. Required for branch protection via code owners"
  fi
}

check_trusted_committers() {
  local found=false detail=""

  # Check for trusted committer references in repo docs
  if grep -rli "trusted.committer" "$REPO_ROOT" --include='*.md' --include='*.yml' --include='*.yaml' --include='*.json' 2>/dev/null | grep -q .; then
    found=true
    detail="Trusted Committer references found in repo docs"
  fi

  if [[ "$found" == true ]]; then
    pass "MUST" "Trusted Committer(s) defined" "$detail"
  else
    warn "MUST" "Trusted Committer(s) defined" "No references found in repo. Verify in PlatformMetadata"
  fi
}

check_product_owner() {
  local found=false detail=""

  # Check for product owner / product manager references
  if grep -rliE "product.*(owner|manager)" "$REPO_ROOT" --include='*.md' --include='*.yml' --include='*.yaml' 2>/dev/null | grep -q .; then
    found=true
    detail="Product Owner/Manager references found in repo docs"
  fi

  if [[ "$found" == true ]]; then
    pass "MUST" "Product Owner defined" "$detail"
  else
    warn "MUST" "Product Owner defined" "No references found in repo. Verify in Backstage entities"
  fi
}

check_api_docs() {
  local found=false detail=""

  # OpenAPI / Swagger
  for pattern in "openapi*" "swagger*" "*.openapi.*" "*.swagger.*"; do
    if find "$REPO_ROOT" -maxdepth 4 -iname "$pattern" -not -path '*/.git/*' -not -path '*/node_modules/*' 2>/dev/null | grep -q .; then
      found=true
      detail="OpenAPI/Swagger spec found"
      break
    fi
  done

  # AsyncAPI
  if [[ "$found" == false ]]; then
    if find "$REPO_ROOT" -maxdepth 4 -iname "asyncapi*" -not -path '*/.git/*' 2>/dev/null | grep -q .; then
      found=true
      detail="AsyncAPI spec found"
    fi
  fi

  # API docs directory
  if [[ "$found" == false ]]; then
    if find "$REPO_ROOT" -maxdepth 3 -type d -iname "api" -not -path '*/.git/*' 2>/dev/null | grep -q .; then
      found=true
      detail="API documentation directory found"
    fi
  fi

  # API references in docs
  if [[ "$found" == false ]]; then
    if grep -rliE "(api|endpoint|contract)" "$REPO_ROOT/docs" --include='*.md' 2>/dev/null | grep -q .; then
      found=true
      detail="API references found in docs/"
    fi
  fi

  if [[ "$found" == true ]]; then
    pass "SHOULD" "API documentation" "$detail"
  else
    fail "SHOULD" "API documentation" "No API specs (OpenAPI/Swagger/AsyncAPI) or api docs found"
  fi
}

check_design_docs() {
  local found=false detail=""

  for pattern in "design*" "architecture*" "DESIGN*" "ARCHITECTURE*"; do
    if find "$REPO_ROOT" -maxdepth 4 -iname "$pattern" -not -path '*/.git/*' -not -path '*/node_modules/*' 2>/dev/null | grep -q .; then
      found=true
      detail="Design/architecture documentation found"
      break
    fi
  done

  if [[ "$found" == false ]]; then
    if find "$REPO_ROOT/docs" -maxdepth 3 -iname "*.md" 2>/dev/null | xargs grep -liE "(design|architecture|how.*(it|the|this).*(works|functions))" 2>/dev/null | grep -q .; then
      found=true
      detail="Design content found in docs/"
    fi
  fi

  if [[ "$found" == true ]]; then
    pass "SHOULD" "Design documentation" "$detail"
  else
    fail "SHOULD" "Design documentation" "No design or architecture documentation found"
  fi
}

check_c4_diagrams() {
  local found=false detail=""

  # Look for PlantUML files
  if find "$REPO_ROOT" -maxdepth 4 -iname "*.puml" -not -path '*/.git/*' 2>/dev/null | grep -q .; then
    found=true
    detail="PlantUML (.puml) files found"
  fi

  # Look for C4 references
  if [[ "$found" == false ]]; then
    if grep -rli "C4" "$REPO_ROOT" --include='*.puml' --include='*.plantuml' --include='*.md' 2>/dev/null | grep -q .; then
      found=true
      detail="C4 diagram references found"
    fi
  fi

  # Look for Structurizr or other C4 tooling
  if [[ "$found" == false ]]; then
    if find "$REPO_ROOT" -maxdepth 4 \( -iname "*.dsl" -o -iname "structurizr*" \) -not -path '*/.git/*' 2>/dev/null | grep -q .; then
      found=true
      detail="Structurizr DSL files found"
    fi
  fi

  if [[ "$found" == true ]]; then
    pass "SHOULD" "C4 diagrams" "$detail"
  else
    fail "SHOULD" "C4 diagrams" "No C4/PlantUML diagrams found. Use PlantUML with C4 extensions"
  fi
}

check_adrs() {
  local found=false detail=""

  # Look for ADR directory
  for pattern in "adr" "adrs" "ADR" "ADRs" "decisions" "architecture-decisions"; do
    if find "$REPO_ROOT" -maxdepth 4 -type d -iname "$pattern" -not -path '*/.git/*' 2>/dev/null | grep -q .; then
      found=true
      detail="ADR directory found"
      break
    fi
  done

  # Look for ADR files
  if [[ "$found" == false ]]; then
    if find "$REPO_ROOT" -maxdepth 4 -iname "*adr*" -name "*.md" -not -path '*/.git/*' 2>/dev/null | grep -q .; then
      found=true
      detail="ADR files found"
    fi
  fi

  if [[ "$found" == true ]]; then
    pass "SHOULD" "ADRs (Architecture Decision Records)" "$detail"
  else
    fail "SHOULD" "ADRs (Architecture Decision Records)" "No ADR directory or files found"
  fi
}

check_standards_docs() {
  local found=false detail=""

  for pattern in "standards*" "STANDARDS*" "coding-style*" "style-guide*" ".editorconfig" ".eslintrc*" ".prettierrc*" "stylecop*" ".rubocop*"; do
    if find "$REPO_ROOT" -maxdepth 3 -iname "$pattern" -not -path '*/.git/*' -not -path '*/node_modules/*' 2>/dev/null | grep -q .; then
      found=true
      detail="Standards/style configuration found"
      break
    fi
  done

  if [[ "$found" == true ]]; then
    pass "SHOULD" "Standards documentation" "$detail"
  else
    fail "SHOULD" "Standards documentation" "No standards, style guides, or linter configs found"
  fi
}

check_roadmap() {
  local found=false detail=""

  for pattern in "ROADMAP*" "roadmap*" "ROAD_MAP*"; do
    if find "$REPO_ROOT" -maxdepth 3 -iname "$pattern" -not -path '*/.git/*' 2>/dev/null | grep -q .; then
      found=true
      detail="Roadmap document found"
      break
    fi
  done

  # Check README for roadmap section
  if [[ "$found" == false ]]; then
    local readme
    readme=$(find_file_ci "README.md")
    if [[ -n "$readme" ]] && grep -qi "road.map\|roadmap" "$readme" 2>/dev/null; then
      found=true
      detail="Roadmap section found in README.md"
    fi
  fi

  if [[ "$found" == true ]]; then
    pass "SHOULD" "Road map" "$detail"
  else
    fail "SHOULD" "Road map" "No roadmap document or section found"
  fi
}

check_faq() {
  local found=false detail=""

  for pattern in "FAQ*" "faq*"; do
    if find "$REPO_ROOT" -maxdepth 3 -iname "$pattern" -not -path '*/.git/*' 2>/dev/null | grep -q .; then
      found=true
      detail="FAQ document found"
      break
    fi
  done

  # Check README for FAQ section
  if [[ "$found" == false ]]; then
    local readme
    readme=$(find_file_ci "README.md")
    if [[ -n "$readme" ]] && grep -qi "FAQ\|frequently.asked" "$readme" 2>/dev/null; then
      found=true
      detail="FAQ section found in README.md"
    fi
  fi

  if [[ "$found" == true ]]; then
    pass "SHOULD" "FAQs" "$detail"
  else
    fail "SHOULD" "FAQs" "No FAQ document or section found"
  fi
}

check_backstage_integration() {
  local found=false detail=""

  if [[ -f "$REPO_ROOT/mkdocs.yml" ]]; then
    found=true
    detail="mkdocs.yml found"

    # Also check for techdocs workflow
    if find "$REPO_ROOT/.github/workflows" -iname "*techdocs*" 2>/dev/null | grep -q .; then
      detail="mkdocs.yml and TechDocs workflow found"
    else
      detail="mkdocs.yml found but no TechDocs GHA workflow detected"
    fi
  fi

  if [[ "$found" == true ]]; then
    pass "SHOULD" "Backstage TechDocs integration" "$detail"
  else
    fail "SHOULD" "Backstage TechDocs integration" "No mkdocs.yml found. Docs won't appear in Backstage"
  fi
}

check_observability() {
  local found=false detail=""

  # Check for OTel / DataDog direct references
  if grep -rli --exclude-dir='.git' --exclude-dir='node_modules' --exclude-dir='vendor' \
    "opentelemetry\|otel\|datadog\|dd-trace\|ddtrace" "$REPO_ROOT" \
    --include='*.yml' --include='*.yaml' --include='*.json' --include='*.toml' \
    --include='*.csproj' --include='*.props' --include='*.gradle' \
    --include='*.cs' --include='*.js' --include='*.ts' --include='*.py' \
    --include='*.go' --include='*.java' --include='Dockerfile' 2>/dev/null | grep -q .; then
    found=true
    detail="Observability instrumentation found (OTel/DataDog)"
  fi

  # Check for JET internal monitoring wrappers (@rmp/services, GlobalMonitoringService, MonitorProvider)
  if [[ "$found" == false ]]; then
    if grep -rliE --exclude-dir='.git' --exclude-dir='node_modules' --exclude-dir='vendor' \
      "GlobalMonitoringService|MonitorProvider|@rmp/services.*monitor|monitoring" "$REPO_ROOT" \
      --include='*.cs' --include='*.js' --include='*.ts' --include='*.py' \
      --include='*.go' --include='*.java' --include='*.vue' 2>/dev/null | grep -q .; then
      found=true
      detail="Observability found via JET internal monitoring wrapper"
    fi
  fi

  if [[ "$found" == true ]]; then
    pass "SHOULD" "Observability (OTel/DataDog)" "$detail"
  else
    fail "SHOULD" "Observability (OTel/DataDog)" "No OpenTelemetry, DataDog, or monitoring instrumentation found"
  fi
}

# --- Main execution ----------------------------------------------------------

if [[ "$OUTPUT_JSON" == false ]]; then
  echo ""
  printf "${color_bold}JET InnerSource Certification Validator${color_reset}\n"
  printf "Repository: ${color_cyan}%s${color_reset}\n" "$REPO_ROOT"
  echo ""
fi

# MUST checks
section "MUST Requirements (mandatory for certification)"

check_readme
check_contributing
check_communication
check_runbook
check_test_automation
check_sonarqube
check_github_actions
check_trusted_committers
check_product_owner

# SHOULD checks
section "SHOULD Requirements (recommended for certification)"

check_codeowners
check_api_docs
check_design_docs
check_c4_diagrams
check_adrs
check_standards_docs
check_roadmap
check_faq
check_backstage_integration
check_observability

# --- Summary -----------------------------------------------------------------

if [[ "$OUTPUT_JSON" == false ]]; then
  echo ""
  printf "${color_bold}${color_cyan}── Summary ──${color_reset}\n"
  echo ""

  local_must_warn=$((MUST_TOTAL - MUST_PASS - MUST_FAIL))
  local_should_warn=$((SHOULD_TOTAL - SHOULD_PASS - SHOULD_FAIL))

  printf "  MUST   checks: ${color_green}%d passed${color_reset}, ${color_red}%d failed${color_reset}" "$MUST_PASS" "$MUST_FAIL"
  if [[ "$local_must_warn" -gt 0 ]]; then
    printf ", ${color_yellow}%d warn${color_reset}" "$local_must_warn"
  fi
  printf " (out of %d)\n" "$MUST_TOTAL"

  printf "  SHOULD checks: ${color_green}%d passed${color_reset}, ${color_red}%d failed${color_reset}" "$SHOULD_PASS" "$SHOULD_FAIL"
  if [[ "$local_should_warn" -gt 0 ]]; then
    printf ", ${color_yellow}%d warn${color_reset}" "$local_should_warn"
  fi
  printf " (out of %d)\n" "$SHOULD_TOTAL"

  echo ""
  if [[ "$MUST_FAIL" -eq 0 ]]; then
    printf "  ${color_green}${color_bold}All MUST requirements are met.${color_reset}\n"
  else
    printf "  ${color_red}${color_bold}%d MUST requirement(s) not met. Certification blocked.${color_reset}\n" "$MUST_FAIL"
  fi
  echo ""
  printf "  ${color_yellow}Note:${color_reset} Some checks (Trusted Committers in PlatformMetadata, Product Owner\n"
  printf "  in Backstage, SonarQube Scorecard status, Launch Control Checklist) require\n"
  printf "  manual verification outside the repository.\n"
  echo ""
else
  # JSON output
  printf '{\n'
  printf '  "repository": "%s",\n' "$REPO_ROOT"
  printf '  "summary": {\n'
  printf '    "must": {"pass": %d, "fail": %d, "total": %d},\n' "$MUST_PASS" "$MUST_FAIL" "$MUST_TOTAL"
  printf '    "should": {"pass": %d, "fail": %d, "total": %d}\n' "$SHOULD_PASS" "$SHOULD_FAIL" "$SHOULD_TOTAL"
  printf '  },\n'
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

# Exit code: 0 if all MUST checks pass, 1 otherwise
if [[ "$MUST_FAIL" -gt 0 ]]; then
  exit 1
fi
exit 0
