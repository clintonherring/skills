# jet-github-actions

A skill for writing, debugging, and maintaining GitHub Actions CI/CD workflows on JET's GitHub Enterprise Server (GHES).

## What This Skill Does

This skill provides context-aware assistance for GitHub Actions at JET, including:

- **GHES-specific constraints** — no GitHub Connect, imported action version pinning, built-in action version limits
- **Available actions catalog** — first-party, imported, and in-house custom actions
- **Runners & secrets** — runner groups, Vault integration, Artifactory tokens
- **Troubleshooting** — common issues and their solutions

## When It Activates

The skill activates when you're working with:
- GitHub Actions workflow files (`.github/workflows/*.yml`)
- CI/CD pipeline configuration
- Questions about runners, actions, secrets, or deployments on GHES

## Installation

```bash
npx skills add git@github.je-labs.com:ai-platform/skills.git
```

## Skill Contents

```
jet-github-actions/
├── SKILL.md                          # Core instructions & critical rules
├── README.md                         # This file
└── references/
    ├── ghes-constraints.md           # GHES-specific rules & gotchas
    ├── available-actions.md          # Actions catalog with version guidance
    ├── runners-and-secrets.md        # Runner groups, Vault, Artifactory
    └── faqs-and-troubleshooting.md   # Common issues & solutions
```

## Key Rules This Skill Enforces

1. **No GitHub Connect** — all actions must come from `github.je-labs.com/actions` or `github.je-labs.com/github-actions/`
2. **Version resolution gotcha** for imported actions (some need explicit tags if `@v1` fails)
3. **upload-artifact/download-artifact pinned to v3** (v4 doesn't support GHES)
4. **Vault for secrets** (not GitHub Secrets for sensitive data)
5. **Self-hosted runners only** (`runs-on: [self-hosted, ubuntu-latest]`)
