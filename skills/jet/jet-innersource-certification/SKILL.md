---
name: jet-innersource-certification
description: Validate whether a JET repository meets the InnerSource certification requirements, or validate a PlatformMetadata PR for InnerSource correctness. Use this skill when checking InnerSource readiness, auditing a repository for InnerSource compliance, preparing a component for InnerSource certification, reviewing PlatformMetadata PRs, or when the user asks about InnerSource setup, certification checks, or readiness assessments. Triggers include "check innersource", "innersource certification", "innersource readiness", "is this repo innersource ready", "validate innersource", "innersource audit", "PlatformMetadata PR", or any github.je-labs.com/metadata/PlatformMetadata/pull/ URL.
metadata:
  owner: ai-platform
---

# JET InnerSource Certification Checks

Validate whether a GitHub repository meets JET's InnerSource certification requirements, or validate a PlatformMetadata pull request for InnerSource certification correctness.

The full certification criteria are inlined in [references/certification-criteria.md](references/certification-criteria.md) -- read that file directly rather than fetching external URLs.

## When to use

- Checking if a repository is ready for InnerSource certification
- Auditing a component against InnerSource requirements
- Preparing a repository for InnerSource onboarding
- Generating a readiness report for a team
- **Validating a PlatformMetadata PR** for InnerSource certification correctness
- Reviewing whether a feature JSON in PlatformMetadata has all required InnerSource fields

## Prerequisites

- [jet-company-standards](https://github.je-labs.com/ai-platform/skills/tree/master/skills/jet-company-standards) skill installed (for GHE and Backstage access)
- `gh` CLI authenticated with GitHub Enterprise (`gh auth login --hostname github.je-labs.com`)
- The repository to validate must be cloned locally, and the current working directory must be inside it

## Instructions

### Running the validation

To validate a repository, run the bundled script from within the target repository's root:

```bash
bash <path-to-skill>/scripts/validate.sh
```

The script will output a categorized report with PASS/FAIL/WARN for each check, grouped by priority (MUST / SHOULD).

### Interpreting results

The checks are split into two priority levels derived from the official setup guide:

**MUST checks** -- these are mandatory for InnerSource certification:
- README.md exists and is non-trivial (more than just a title)
- CONTRIBUTING.md exists (contribution guidelines)
- COMMUNICATION.md exists (team contact info)
- Runbook exists (operational documentation)
- Test automation is present (test directories or config files)
- SonarQube integration is configured (in GHA workflows or config)
- GitHub Actions CI/CD workflows exist
- `.github/CODEOWNERS` file exists
- Trusted Committer(s) defined (checked in repo docs or PlatformMetadata)
- Product Owner defined

**SHOULD checks** -- recommended for certification:
- API documentation exists (OpenAPI/Swagger specs, AsyncAPI, or docs/api)
- Design documentation exists
- C4 diagrams exist (PlantUML `.puml` files with C4 extensions)
- ADRs (Architecture Decision Records) directory exists
- Standards documentation exists (coding style / guidelines)
- Road map is documented
- FAQs document exists
- Documents surfaced in Backstage (mkdocs.yml + techdocs workflow)
- Branch protection / restrictions configured
- Slack channel documented in COMMUNICATION.md
- Observability configured (OTel / DataDog references)

### After running the checks

Once the report is generated, you MUST:

1. Present the full report to the user, organized by MUST and SHOULD sections.
2. For each FAIL result, explain what is missing and provide actionable remediation guidance.
3. Offer to help fix any failing checks. For file-based checks (CONTRIBUTING.md, COMMUNICATION.md, etc.), offer to generate the file using the bundled templates in the `templates/` directory.
4. If the user wants to fix issues, work through them one at a time, marking progress as you go.

### Generating missing files from templates

The `templates/` directory contains starter templates for common missing files:

| Template | Target file | Description |
|----------|-------------|-------------|
| `templates/CONTRIBUTING.md` | `CONTRIBUTING.md` | Contribution guidelines template |
| `templates/COMMUNICATION.md` | `COMMUNICATION.md` | Team communication template |

When generating files from templates, replace all `TODO` placeholders with information specific to the repository. Ask the user for any details you cannot infer (team name, Slack channel, Jira prefix, etc.).

### Manual / external checks

Some checks cannot be fully automated from the repository alone. After running the script, remind the user to verify these manually:

- **Trusted Committers in PlatformMetadata**: Verify at `https://github.je-labs.com/metadata/PlatformMetadata/tree/master/Data/global_features`
- **Product Manager in Backstage**: Verify at `https://github.je-labs.com/backstage/backstage-entities/tree/main/group`
- **Slack channel in PlatformMetadata**: Verify the team definition includes `slack_channel_name`
- **SonarQube quality gate**: Verify the project is not flagged on Scorecard
- **Launch Control Checklist**: Verify compliance at the organizational level
- **Architecture Hub participation**: Verify ADRs are presented to Advice Forums
- **SLIs defined and monitored**: Verify in DataDog or equivalent

---

## PlatformMetadata PR Validation

### When to use

Use the PMD PR validator when:
- A user shares a PlatformMetadata PR URL (e.g. `https://github.je-labs.com/metadata/PlatformMetadata/pull/23149`)
- A user asks you to review or validate a PlatformMetadata PR for InnerSource correctness
- A user is preparing to submit a PlatformMetadata PR to register a component for InnerSource

### Running the PMD PR validation

```bash
bash <path-to-skill>/scripts/validate-pmd-pr.sh <PR_URL_OR_NUMBER> [--repo-check] [--json]
```

Arguments:
- `PR_URL_OR_NUMBER` -- A full PR URL (`https://github.je-labs.com/metadata/PlatformMetadata/pull/23149`) or just the PR number (`23149`)
- `--repo-check` -- Also clone and validate the linked repository using `validate.sh` (slower, requires network access)
- `--json` -- Output results as JSON instead of formatted text

### What the PMD PR validator checks

**Feature file checks:**
- `contribution_type` is set to `innerSourceBasic` or `innerSourceAdvanced`
- `id` matches the JSON filename
- `description` is present and non-trivial (10+ chars)
- `owners` (team name) is set
- `tier` is set to 1, 2, or 3
- `lifecycle.status` is set
- `github_repository` owner and name are set
- `run_book_path` is set (required for InnerSource types)

**InnerSource-specific checks** (when `contribution_type` is an InnerSource type):
- `trusted_committers` array has at least 1 entry
- Owning team file exists in `Data/teams/`
- Team has `slack_channel_name` set
- Trusted committers are listed in team's `engineers` array

**PR checklist checks** (parsed from the PR body):
- Team Slack channel configured
- Trusted Committer(s) nominated
- Product Manager registered
- README exists
- Runbook exists
- Contribution document exists
- Communication document exists
- Test automation in place
- SonarQube integrated

**Team file checks** (if the PR also modifies team files):
- `slack_channel_name` is set
- `engineers` array has at least 1 entry
- `description` is present and non-trivial

**Optional repo cross-check** (with `--repo-check`):
- Clones the linked repository and runs the full `validate.sh` against it
- Reports MUST and SHOULD check pass/fail counts
- Lists individual repo failures

### Interpreting PMD PR results

Each check produces one of:
- **PASS** -- Requirement met
- **FAIL** -- Requirement not met; must be fixed before certification
- **WARN** -- Potential issue; should be reviewed but may be acceptable

The script exits with code `1` if any checks FAIL, `0` otherwise.

### After running the PMD PR checks

Once the report is generated, you MUST:

1. Present the full report to the user, organized by section (Feature, InnerSource Requirements, PR Checklist, Team, Repository).
2. For each FAIL, explain what is wrong and suggest the fix (e.g., "add `run_book_path` to the feature JSON").
3. For each WARN, explain the risk and whether the user needs to act.
4. If the user wants to fix the PR, help them draft the corrected JSON or PR body.

---

## Choosing which validator to use

| Scenario | Script to use |
|----------|---------------|
| You have a repo cloned locally and want to check InnerSource readiness | `validate.sh` |
| You have a PlatformMetadata PR URL and want to validate the PR | `validate-pmd-pr.sh` |
| You want to validate both the PR and the linked repo | `validate-pmd-pr.sh --repo-check` |
| You want machine-readable output (for piping or further processing) | Either script with `--json` |

### Full certification criteria reference

See [references/certification-criteria.md](references/certification-criteria.md) for the complete list of requirements derived from the official documentation.
