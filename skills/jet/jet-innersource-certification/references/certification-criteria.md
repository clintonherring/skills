# InnerSource Certification Criteria

Complete reference of all InnerSource certification requirements for JET repositories.

---

## MUST Requirements

These are mandatory. A repository cannot be InnerSource certified without meeting all of them.

### 1. README.md

The repository MUST contain a `README.md` that provides orientation about the repository and its contents. It should give a basic overview of what the component is and how to run it. A stub with just a title is not sufficient.

**Checked by:** File existence + content length (minimum 5 non-empty lines).

### 2. CONTRIBUTING.md

The repository MUST contain contribution guidelines. This document should explain how to successfully contribute to the project, including:
- Suitability for InnerSource
- Prerequisites
- How to contact the team
- Alignment meeting process
- ADR requirements
- Timelines and PR review expectations
- Code quality standards
- Testing requirements

**Template available:** `templates/CONTRIBUTING.md`
**Official template:** [Architecture/InnerSource - contributing.md](https://github.je-labs.com/Architecture/InnerSource/blob/main/docs/Component%20Owning%20Teams/Templates/contributing.md)

### 3. COMMUNICATION.md

The repository MUST contain a communication document explaining how to work with the owning team. This should include:
- Team Slack channel link
- Contact information for different request types (general queries, bug reports, contribution questions, PR reviews, feature requests, etc.)
- Roles and responsibilities

**Template available:** `templates/COMMUNICATION.md`
**Official template:** [Architecture/InnerSource - team-communication.md](https://github.je-labs.com/Architecture/InnerSource/blob/main/docs/Component%20Owning%20Teams/Templates/team-communication.md)

### 4. Runbook

The repository MUST contain an up-to-date runbook. This should provide all details required for an on-call engineer to address any alerts. Common locations: `runbook.md`, `RUNBOOK.md`, `docs/runbook.md`.

**Checked by:** File search for `*runbook*` pattern + content length check (minimum 3 non-empty lines).

### 5. Test Automation

All components MUST have test automation in place with good code coverage. This is tracked via Scorecard. Testing is even more vital when you have external contributors.

**Checked by:** Presence of test directories (`test/`, `tests/`, `__tests__/`, `spec/`, `*.Tests/`) or test configuration files (jest, vitest, pytest, xunit, nunit, etc.).

### 6. SonarQube Integration

SonarQube MUST be integrated into all components and run as part of Pull Requests. This is tracked via Scorecard.

**Checked by:** SonarQube references in GHA workflows or `sonar-project.properties` file.
**Support:** [#help-sonarqube](https://justeat.slack.com/archives/CGMQT84TB) Slack channel.

### 7. GitHub Actions CI/CD

JET has standardized on GitHub and GitHub Actions for source control and CI. The repository MUST have CI/CD workflows configured.

**Checked by:** Existence of `.github/workflows/` with at least one `.yml`/`.yaml` file.

### 8. Trusted Committer(s) Defined

At least one Trusted Committer MUST be active at any time. They must:
- Be an engineer with deep technical and domain knowledge of the component
- SHOULD be a Senior+ engineer
- SHOULD be in the component-owning team
- Be registered in [PlatformMetadata](https://github.je-labs.com/metadata/PlatformMetadata/tree/master/Data/global_features)

The Trusted Committer MUST review PRs from external contributors within 48 hours. Recommended capacity: 20% of one engineer.

**Checked by:** References to "trusted committer" in repo docs. Manual verification in PlatformMetadata required.
**Slack group convention:** `@team-<team-abbreviation>-trusted-committer`

### 9. Product Owner Defined

The team's Product Manager MUST be added to the team definition in [Backstage entities](https://github.je-labs.com/backstage/backstage-entities/tree/main/group).

**Checked by:** References to "product owner" or "product manager" in repo docs. Manual verification in Backstage required.

### 10. Team Slack Channel

A team Slack channel MUST be created for public requests, using the naming convention `#help-{team-name}`. The channel MUST be added to PlatformMetadata under the team's definition (`slack_channel_name` property).

For contribution-specific communication: `#team-{team-name}-contributions`.

**Checked by:** Manual verification in PlatformMetadata and Slack.

---

## SHOULD Requirements

These are recommended and demonstrate higher InnerSource maturity.

### 11. API Documentation

Service API contracts MUST be documented (HTTP and messaging). Use OpenAPI/Swagger for HTTP APIs and AsyncAPI for messaging contracts.

**Checked by:** Presence of OpenAPI/Swagger/AsyncAPI spec files or API documentation in `docs/`.

### 12. Design Documentation

The repository SHOULD contain documentation explaining how the software works "under the hood."

**Checked by:** Presence of design/architecture documents or relevant content in `docs/`.

### 13. C4 Diagrams

Context, Container, and Component diagrams SHOULD exist. Use PlantUML with C4 extensions and check into source control.

**Checked by:** Presence of `.puml` files or C4/Structurizr references.

### 14. ADRs (Architecture Decision Records)

The history of design decisions for the project SHOULD be documented. Internal decisions can be kept in the repository; external-facing decisions should be mirrored to Confluence. ADRs presented to Architecture Hubs / Advice Forums enable transparent decision making.

**Checked by:** Presence of `adr/`, `adrs/`, or `decisions/` directory, or files matching `*adr*`.

### 15. Standards Documentation

The repository SHOULD define coding standards used within the component. At minimum, reference applicable JET-wide standards. If team-specific standards exist, link them from `CONTRIBUTING.md`.

**Checked by:** Presence of standards documents or linter/formatter configuration files (`.editorconfig`, `.eslintrc`, `.prettierrc`, etc.).

### 16. Road Map

A visible road map SHOULD exist so contributors can determine if the team already has plans for a feature.

**Checked by:** Presence of `ROADMAP.md` or a "Roadmap" section in `README.md`.

### 17. FAQs

The repository SHOULD contain a FAQ documenting what usually goes wrong when contributing.

**Checked by:** Presence of `FAQ.md` or a "FAQ" section in `README.md`.

### 18. CODEOWNERS

A `.github/CODEOWNERS` file SHOULD exist to enforce that Trusted Committers review and approve changes from external contributors.

Example:
```
* @MyGithubOrgName/MyTeamName
```

**Checked by:** File existence at `.github/CODEOWNERS`, `CODEOWNERS`, or `docs/CODEOWNERS`.

### 19. Backstage TechDocs Integration

Documentation SHOULD be surfaced via Backstage. This requires:
- `mkdocs.yml` in the repository root
- A `techdocs.yml` GitHub Actions workflow
- Optionally, a `techdocs-adhoc.yml` workflow for PR previews

**Checked by:** Presence of `mkdocs.yml` and techdocs workflow files.

### 20. Observability

JET has standardized on OpenTelemetry (OTel) with DataDog as an APM tool. The component SHOULD have observable instrumentation.

**Checked by:** References to `opentelemetry`, `otel`, `datadog`, `dd-trace` in source/config files.

### 21. Branch Protection

Branch protection policies SHOULD be configured:
- Require a pull request before merging
- Require approvals
- Require review from Code Owners
- Require status checks to pass before merging
- Require conversation resolution before merging
- Restrict who can push to matching branches

**Checked by:** Manual verification in GitHub repository settings.

---

## Manual / External Verification Checklist

These items cannot be checked from the repository alone:

| Check | Where to verify |
|-------|----------------|
| Trusted Committers in PlatformMetadata | [PlatformMetadata/Data/global_features](https://github.je-labs.com/metadata/PlatformMetadata/tree/master/Data/global_features) |
| Product Manager in Backstage | [backstage-entities/group](https://github.je-labs.com/backstage/backstage-entities/tree/main/group) |
| Slack channel in PlatformMetadata | [PlatformMetadata/Data/teams](https://github.je-labs.com/metadata/PlatformMetadata/tree/master/Data/teams) |
| SonarQube Scorecard status | JET Scorecard |
| Launch Control Checklist compliance | Organizational process |
| Architecture Hub participation | ADRs presented to Advice Forums |
| SLIs defined and monitored | DataDog / observability platform |
| Hosted in EKS (or Lambda) | Infrastructure config |
| Conforms to MUST practices from guilds | Guild standards |
| Architecture Principles compliance | [Architecture Principles](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/architectureprinciples) |
| Quality Principles compliance | [Quality Principles](https://docs.google.com/presentation/d/1M3Jg3MOQQLoLmEGIWBBY24vlNfVsuORlqsQaArMPoyw) |
| 30-day warranty process documented | Contributing guidelines |

---

## PlatformMetadata Requirements

When registering a component for InnerSource via a PlatformMetadata PR, the following fields and cross-checks apply.

### Feature JSON (`Data/global_features/<feature>.json`)

| Field | Requirement | Notes |
|-------|-------------|-------|
| `id` | MUST match the filename (without `.json`) | Enforced by schema |
| `type` | MUST be set | Usually `frontend`, `backend`, `library`, etc. |
| `description` | MUST be present (min 3 chars) | Should be meaningful (10+ chars recommended) |
| `owners` | MUST be set to the owning team slug | Must match a file in `Data/teams/` |
| `tier` | MUST be 1, 2, or 3 | Defines the component's criticality |
| `lifecycle.status` | MUST be set | e.g. `production`, `development`, `deprecated` |
| `contribution_type` | MUST be `innerSourceBasic` or `innerSourceAdvanced` | The key InnerSource field |
| `trusted_committers` | MUST have at least 1 entry | Array of GitHub usernames |
| `github_repository.owner` | MUST be set | GitHub org for the repository |
| `github_repository.name` | MUST be set | GitHub repo name |
| `run_book_path` | MUST be set for InnerSource types | Path to the runbook within the repository |

Valid `contribution_type` values (from schema):
- `innerSourceBasic` -- InnerSource with basic contribution model
- `innerSourceAdvanced` -- InnerSource with advanced contribution model (more open)
- `openSource` -- Open source
- `ownersOnly` -- Only the owning team can contribute
- `ownersOnlyReviewed` -- Only the owning team, with mandatory review

### Team JSON (`Data/teams/<team>.json`)

| Field | Requirement | Notes |
|-------|-------------|-------|
| `slack_channel_name` | MUST be set for InnerSource teams | e.g. `help-partner-hub-contributors` (without `#`) |
| `engineers` | SHOULD list all team engineers | Trusted committers should appear here |
| `description` | SHOULD be meaningful (10+ chars) | Describes what the team does |

### Cross-checks

| Check | Description |
|-------|-------------|
| Team file exists | `Data/teams/<owners>.json` must exist in PlatformMetadata |
| Trusted committers in team | All `trusted_committers` should be listed in the team's `engineers` array |
| Product Manager in Backstage | Team's PM should be registered in [backstage-entities](https://github.je-labs.com/backstage/backstage-entities/tree/main/group) |

### PR Checklist

PlatformMetadata InnerSource PRs should include a checklist in the PR body confirming:

- [ ] Team Slack channel is created and configured
- [ ] Trusted Committer(s) are nominated and registered
- [ ] Product Manager is registered in Backstage
- [ ] README exists in the repository
- [ ] Runbook exists in the repository
- [ ] Contribution document (CONTRIBUTING.md) exists
- [ ] Communication document (COMMUNICATION.md) exists
- [ ] Test automation is in place
- [ ] SonarQube is integrated
