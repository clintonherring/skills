# jet-innersource-certification-checks

An OpenCode agent skill that validates whether a JET (Just Eat Takeaway) GitHub repository meets the InnerSource certification requirements, and can also validate PlatformMetadata PRs for InnerSource certification correctness.

## What it checks

The skill provides two validators:

### 1. Repository Validator (`validate.sh`)

Runs automated checks against a cloned repository, grouped by priority:

### MUST (mandatory for certification)

| # | Check | How it's verified |
|---|-------|-------------------|
| 1 | README.md exists and is non-trivial | File exists with 5+ non-empty lines |
| 2 | CONTRIBUTING.md exists | File search (case-insensitive) |
| 3 | COMMUNICATION.md exists | File search (case-insensitive) |
| 4 | Runbook exists | File search for `*runbook*` |
| 5 | Test automation present | Test dirs or config files detected |
| 6 | SonarQube integrated | References in GHA workflows or config |
| 7 | GitHub Actions CI/CD | `.github/workflows/` with workflow files |
| 8 | Trusted Committer(s) defined | References in docs (manual PlatformMetadata check) |
| 9 | Product Owner defined | References in docs (manual Backstage check) |

### SHOULD (recommended)

| # | Check | How it's verified |
|---|-------|-------------------|
| 10 | CODEOWNERS | `.github/CODEOWNERS` exists |
| 11 | API documentation | OpenAPI/Swagger/AsyncAPI specs or api docs |
| 12 | Design documentation | Design/architecture files in docs |
| 13 | C4 diagrams | `.puml` files or C4/Structurizr references |
| 14 | ADRs | `adr/` or `decisions/` directory |
| 15 | Standards documentation | Style guides or linter configs |
| 16 | Road map | `ROADMAP.md` or section in README |
| 17 | FAQs | `FAQ.md` or section in README |
| 18 | Backstage TechDocs | `mkdocs.yml` + techdocs workflow |
| 19 | Observability | OTel/DataDog references in source |

### 2. PlatformMetadata PR Validator (`validate-pmd-pr.sh`)

Validates a PlatformMetadata pull request for InnerSource certification correctness:

| Category | What it checks |
|----------|----------------|
| Feature JSON fields | `contribution_type`, `id`, `description`, `owners`, `tier`, `lifecycle`, `github_repository`, `run_book_path`, `trusted_committers` |
| Team cross-checks | Team file exists, `slack_channel_name` set, trusted committers in team engineers |
| PR checklist | Checklist items in PR body (Slack channel, TCs, PM, README, runbook, CONTRIBUTING, COMMUNICATION, tests, SonarQube) |
| Team file (if modified) | `slack_channel_name`, `engineers`, `description` |
| Repo cross-check (optional) | Clones linked repo and runs full `validate.sh` against it |

## Installation

```bash
npx skills add git@github.je-labs.com:ai-platform/skills.git
```

## Prerequisites

- `gh` CLI authenticated with GitHub Enterprise
- The target repository must be cloned locally

## Usage

The skill is triggered automatically when you ask about InnerSource readiness, certification, or compliance. Examples:

- "Is this repo InnerSource ready?"
- "Check InnerSource certification for this repository"
- "Run InnerSource audit"
- "Validate InnerSource compliance"
- "Review this PlatformMetadata PR: https://github.je-labs.com/metadata/PlatformMetadata/pull/23149"

You can also run the scripts directly:

```bash
# Repository validation (run from within the target repo)
bash scripts/validate.sh          # Formatted output
bash scripts/validate.sh --json   # JSON output

# PlatformMetadata PR validation
bash scripts/validate-pmd-pr.sh 23149                    # By PR number
bash scripts/validate-pmd-pr.sh https://github.je-labs.com/metadata/PlatformMetadata/pull/23149  # By URL
bash scripts/validate-pmd-pr.sh 23149 --repo-check       # Also validate linked repo
bash scripts/validate-pmd-pr.sh 23149 --json              # JSON output
```

## Project structure

```
.
├── SKILL.md                              # Skill definition and agent instructions
├── scripts/
│   ├── validate.sh                       # Repository validation script
│   └── validate-pmd-pr.sh               # PlatformMetadata PR validation script
├── references/
│   └── certification-criteria.md         # Full certification criteria reference
└── templates/
    ├── CONTRIBUTING.md                   # Contributing guidelines template
    └── COMMUNICATION.md                  # Team communication template
```

## Sources

- [Becoming InnerSource Ready](https://docs.google.com/document/d/1aaAi5y56gFgtaZt30o9ck0upIwBt7VtIB7jfRAlCNfE)
- [InnerSource Setup Guide](https://github.je-labs.com/Architecture/InnerSource/blob/main/docs/Component%20Owning%20Teams/setup.md)
- [Trusted Committer Guidelines](https://github.je-labs.com/Architecture/InnerSource/blob/main/docs/Component%20Owning%20Teams/trusted-committers.md)
- [InnerSource Contributing Guide](https://github.je-labs.com/Architecture/InnerSource/blob/main/docs/contributing.md)
