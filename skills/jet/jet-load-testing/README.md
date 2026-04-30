# JET Load Testing Skill

This skill enables writing, managing, and maintaining load and performance tests at Just Eat Takeaway.com using k6. It provides templates, best practices, and GitHub Actions workflows for performance testing.

## Installation

```bash
npx skills add git@github.je-labs.com:ai-platform/skills.git
```

## Prerequisites

### Required Tools

| Tool | Purpose | Installation (MacOS/Linux) | Installation (Windows PowerShell) |
|------|---------|----------------------------|------------------------|
| `k6` | Load testing tool | `brew install k6` | `winget install GrafanaLabs.k6` |

### Required Skills

| Skill | Purpose |
|-------|---------|
| `jet-company-standards` | JET development standards and conventions |

## Usage

Once installed, the skill is automatically triggered when you:

- Write new load or performance test scripts
- Modify or debug existing load tests
- Configure test thresholds, scenarios, or options
- Set up CI/CD pipelines for performance testing
- Create GitHub Actions workflows for load testing

## Skill Contents

- `SKILL.md` - Main skill instructions, best practices, and workflows
- `references/k6-options.md` - k6 options configuration reference
- `references/github-actions.md` - GitHub Actions workflow reference
- `templates/k6-test-script.js` - Base k6 test script template
- `templates/k6-inline-profile-script.js` - Template for tests with inline profiles
- `templates/k6-file-profile-script.js` - Template for tests with file-based profiles
- `templates/github-workflow-cicd.yml` - GitHub Actions CI/CD workflow template
- `templates/github-workflow-manual.yml` - GitHub Actions manual trigger workflow template
