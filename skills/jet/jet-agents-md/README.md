# jet-agents-md

Create, manage, and improve agent guidance files (`AGENTS.md`, `CLAUDE.md`) for any codebase. The skill guides you through an interactive workflow — asking questions, exploring the repo, presenting findings, and drafting files level by level with your approval before writing anything.

## Installation

```bash
npx skills add git@github.je-labs.com:ai-platform/skills.git --skill jet-agents-md
```

## Example Prompts

### Create Mode

Start from scratch — the skill explores your repo, asks clarifying questions, and builds the files:

```
Create an AGENTS.md for my Kotlin Spring Boot service
```

```
I have a .NET 8 solution with Clean Architecture — Domain, Application, Infrastructure, Api projects. Can you set up agent guidance files?
```

```
Write a CLAUDE.md for my React/Next.js frontend that uses Zustand and Playwright
```

```
We have a monorepo with three services: order-service, payment-service, and notification-service. Help me create AGENTS.md files.
```

```
I'm building a Go HTTP service with PostgreSQL and Redis. Create an AGENTS.md.
```

```
My Python FastAPI service uses Keycloak for auth, SQLAlchemy with Alembic, and Semgrep in CI. Can you create an AGENTS.md?
```

### Manage Mode

Make targeted updates after a change — the skill reads existing files and proposes minimal edits:

```
We just migrated from REST to GraphQL — update our AGENTS.md
```

```
I added a new payments module to the monorepo. Can you update the agent guidance?
```

```
We switched from Jest to Vitest — update the testing section in our CLAUDE.md
```

```
We added Kafka with Avro schemas. The AGENTS.md doesn't cover messaging yet.
```

## What Happens

The skill runs an interactive workflow:

1. **Mode** — Determines whether to create from scratch or manage an existing file
2. **Questions** — Asks about your harness, audience, architecture, performance, security, and bug workflow (skips what it can infer)
3. **Exploration** — Scans the repo for stack, patterns, messaging, security signals, and testing setup
4. **Gap analysis** — Presents what it found vs what's missing, and asks you to classify each gap (add / not needed / handled elsewhere)
5. **Drafting** — Proposes the file hierarchy, then writes one level at a time (root first, then services, then layers) — presenting each draft for your approval before moving on
6. **Verification** — Reads back every file, checks pointers, confirms no content was lost, and presents a summary table

## Supported Conventions

| Convention | Harness |
|-----------|---------|
| `AGENTS.md` | OpenCode, multi-agent harnesses |
| `CLAUDE.md` | Claude Code (supports `@import` and path-scoped rules) |

The skill also detects duplicate copies in harness-specific locations (`.amazonq/rules/`, `.cursor/rules/`, `.kiro/`) and offers to sync, delete, or leave them.

## Reference Files

Bundled references are loaded on demand during the workflow:

| File | Loaded when |
|------|-------------|
| `references/detection-guide.md` | Exploring any new repo |
| `references/coverage-checklist.md` | Running gap analysis (Create mode) |
| `references/section-templates.md` | Writing content for any stack |
