# Phase 0: Environment Precheck

**Goal**: Validate that all required tools, authentication, and dependency skills are available before starting the migration workflow.

**Load**: **`jet-company-standards`** skill (for GHE auth patterns and tool reference)

Run the precheck script:

```bash
source scripts/precheck.sh && migrator_precheck
```

Present results as a pass/fail table:

> | Check                   | Status      |
> | ----------------------- | ----------- |
> | `gh` CLI installed      | PASS / FAIL |
> | `git` installed         | PASS / FAIL |
> | `curl` installed        | PASS / FAIL |
> | `jq` installed          | PASS / FAIL |
> | GHE authentication      | PASS / FAIL |
> | `BACKSTAGE_API_KEY` set | PASS / FAIL |
> | GHE network reachable   | PASS / FAIL |

**Gate**: If any **required** check fails, stop and tell the user how to fix it (installation command or auth setup). Do not proceed to Phase 1 until all required checks pass.

If the precheck script is not available (e.g., running outside the skill directory), perform the checks manually:

```bash
gh --version && git --version && curl --version && jq --version
gh auth status --hostname github.je-labs.com
[ -n "$BACKSTAGE_API_KEY" ] && echo "BACKSTAGE_API_KEY is set" || echo "BACKSTAGE_API_KEY is NOT set"
```
