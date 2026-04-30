# Repo Detection Guide

Use this guide when exploring a repo to understand its tech stack and structure before generating an agents.md. The goal is to discover — not assume. Every signal below is a starting point; always verify by reading the actual files.

---

## Build System & Language Detection

The build file is the most reliable signal. Find it first, then read its contents to identify the language, framework, and key dependencies.

| Build file found | Language implied | What to read next |
|-----------------|-----------------|-------------------|
| `package.json` + `.ts` files | TypeScript/Node.js | `package.json` → `dependencies`, `devDependencies`, `scripts` |
| `package.json` + `.js` files only | JavaScript/Node.js | Same as above |
| `go.mod` + `.go` files | Go | `go.mod` → module path and key imports |
| `build.gradle` or `build.gradle.kts` | JVM (Kotlin or Java) | Build file → `dependencies` block for framework |
| `pom.xml` + `.java` files | Java/Maven | `pom.xml` → `dependencies` for framework and libraries |
| `*.csproj` or `*.sln` | .NET (C#) | `.csproj` → `PackageReference` entries; `.sln` reveals all projects |
| `pyproject.toml`, `setup.py`, `requirements.txt` | Python | Deps file → framework (Django, FastAPI, Flask, etc.) |
| `Cargo.toml` + `.rs` files | Rust | `Cargo.toml` → dependencies block |
| `Package.swift` | Swift | `Package.swift` → dependencies and targets |
| `*.lua`, `*.rockspec` | Lua | Rockspec or runtime config for framework |
| Multiple of the above | Monorepo or multi-language | Note each independently |

**Key: read the contents, not just the filename.** A `package.json` might be NestJS, Express, Next.js, or a CLI tool — the framework matters for what to document. Look for the main framework in the dependency list.

**Polyglot awareness:** In monorepos, the same language may serve different purposes — Kotlin for backend services but also Kotlin Multiplatform for frontend, Python for a web API but also for data pipelines or DevOps tooling, JavaScript/TypeScript for both frontend and backend. Note the _purpose_ alongside the language when documenting: it determines which conventions apply. Each purpose may warrant its own agents.md.

For solutions with multiple projects (e.g., a `.sln` file listing `Service.Domain`, `Service.Application`, `Service.Infrastructure`), project names often encode the architecture — this is a strong signal for layer-level agents.md files.

---

## Messaging & Interoperability Detection

Messaging infrastructure is often the most architecturally significant integration in a service. Look for it early — it affects event naming, schema conventions, idempotency rules, and error handling.

| Signal | What it implies |
|--------|----------------|
| Kafka client in dependencies (`kafka-clients`, `kafkajs`, `confluent-kafka`, `sarama`) | Kafka messaging — check for topic naming conventions, consumer group patterns, schema registry usage |
| `@aws-sdk/client-sqs`, `@aws-sdk/client-sns`, or equivalent | AWS SNS/SQS messaging — check for queue names, DLQ setup, message format |
| Cloud Events library (`cloudevents` SDK in deps) | Cloud Events spec for event envelope — document the envelope format |
| Schema registry config or Avro/Protobuf schemas (`.avsc`, `.proto` files) | Structured message formats — document schema location, evolution rules, registry URL |
| AsyncAPI spec files (`asyncapi.yml`, `asyncapi.json`) | Formal event documentation — reference it rather than duplicating |
| OpenAPI/Swagger specs (`openapi.yml`, `swagger.json`) | REST API documentation — reference it, note if it's auto-generated or hand-maintained |
| gRPC proto files (`*.proto` + gRPC deps) | gRPC services — document proto location, code generation commands, service boundaries |
| Event/message folders (`events/`, `messages/`, `schemas/`) | Event-driven architecture — check naming conventions, shared vs service-specific schemas |

**What to document:** Event/topic naming conventions, message body format (JSON, Avro, Protobuf), where schemas live, idempotency requirements for consumers, and any shared event libraries or schema registries.

---

## Security & Identity Detection

Security signals are scattered across config, middleware, and dependencies. Check all three.

| Signal | What it implies |
|--------|----------------|
| Auth middleware in routes (JWT decode, session validation, OAuth middleware) | Authentication approach — document where it lives and how it's configured |
| Identity provider SDKs in deps (Okta, Keycloak, Auth0, IdentityServer, AWS Cognito, Firebase Auth) | External identity provider — document which one, how tokens are validated, where config lives |
| Authorization libraries (CASL, casbin, policy files, role guards, `@Authorize` attributes) | Authorization layer — document where authorization checks live and the pattern used |
| Input validation libraries in deps (class-validator, zod, joi, FluentValidation, Bean Validation) | Validation layer — document where validation happens relative to the request lifecycle |
| SAST/scanning config (`.semgrep.yml`, `wiz.yaml`, `.snyk`, SonarQube config, CodeQL workflows) | Security scanning — note which tool and whether it blocks CI |
| WAF or edge security config (Cloudflare config, AWS WAF rules) | Edge security — document if it affects how the application handles certain request patterns |
| Secret references (`vault://`, AWS Param Store paths, `${{secrets.*}}` in CI, `.env.example`) | Secrets management — document the approach and what must never be hardcoded |
| Audit logging patterns (CloudTrail integration, custom audit log writes) | Audit requirements — document what gets audited and where logs go |

**What to document:** The auth/authz pattern (which provider, how tokens are validated, where authorization lives), secrets management approach, validation layer location, and any agent-specific constraints ("don't run destructive commands without confirmation", "don't access production data directly").

---

## Platform & Infrastructure Detection

Platform signals tell you what constraints affect how code should be written — containerization, scheduling, config management, and deployment patterns.

| Signal | What it implies |
|--------|----------------|
| `Dockerfile` | Container build — check for multi-stage builds, base image conventions |
| `Containerfile` or Podman config | Podman/OCI container build — note if it differs from Docker patterns |
| `docker-compose.yml` | Local dev environment — note what services it spins up |
| `k8s/`, `helm/`, `charts/` | Kubernetes deployment — check for CronJob definitions, ConfigMaps |
| EKS-specific config (`eksctl`, AWS load balancer annotations) | AWS EKS — may have specific networking or IAM patterns |
| Kubernetes CronJob manifests | Scheduled jobs — document the schedule, what they run, idempotency requirements |
| Scheduling library in deps (Quartz, Hangfire, `node-cron`, EventBridge rules) | Application-level scheduling — document job registration patterns, schedule config location |
| AWS Param Store / Systems Manager references | Config/secret management via AWS — document the parameter path convention |
| Vault config or client (`hvac`, `vault-action`, Vault agent sidecar) | HashiCorp Vault for secrets — document how secrets are injected at runtime |
| Artifact registry config (Artifactory, Nexus, GitHub Packages, npm registry overrides in `.npmrc`) | Private artifact registry — document the registry URL and any auth setup needed for local dev |
| `.github/workflows/` | GitHub Actions CI/CD |
| `Jenkinsfile` | Jenkins pipeline |
| `terraform/`, `infra/`, `pulumi/`, `cdk/` | Infrastructure as code — note which tool |
| `.env.example` | Environment variable documentation |
| `Makefile`, `Taskfile.yml`, `justfile` | Task runner — read it, it often reveals non-obvious commands |
| `scripts/` | Build/utility scripts — check what's in here |

**What to document:** Only platform facts that affect code decisions. E.g., "Cold start time matters — avoid heavy module-level initialization", "CronJobs must be idempotent", "All config comes from Param Store — never use local config files in production". Don't document platform setup that's only relevant to ops teams.

---

## Architecture Pattern Detection

Architecture signals come from folder names, module structure, and import conventions — not the language.

### Clean Architecture
**Signals**: Top-level packages/folders named `domain`, `application`, `infrastructure` (and optionally `presentation`, `api`, or `web`)

This pattern appears across all major stacks — the signal is the folder/module structure:
- **Strongest signal**: Separate compilation units per layer (e.g., separate projects, modules, or packages with explicit dependency declarations)
- **Moderate signal**: Folder-based separation with distinct import rules per layer
- **Deciding question**: Do the layers have meaningfully different conventions or allowed dependencies? If yes, layer-level agents.md files are worth creating.

What to document at service root (overview):
- What lives in each layer and how they relate
- The dependency direction rule (domain ← application ← infrastructure/API)
- How layers communicate (commands, direct interface injection, module imports)

Then create layer-specific files for what's non-obvious within each layer. See `section-templates.md` for examples.

### Hexagonal (Ports & Adapters)
**Signals**: Folders named `ports`, `adapters`, `driven`, `driving`, `primary`, `secondary`

What to document:
- Inbound vs outbound ports
- Where adapters live and how they're named

### Layered / MVC
**Signals**: Folders named `controllers`, `services`, `repositories`, `models` (exact names vary by framework and language convention)

What to document:
- The layers and what goes in each
- Any rules about what can call what

### Feature-Sliced / Module-per-Feature
**Signals**: Top-level folders named after business domains: `orders`, `payments`, `users`, `notifications`

What to document:
- How features are structured internally (do they each have their own layers?)
- How cross-cutting concerns are handled (shared/, common/, lib/)

### Monorepo / Multi-Module
**Signals**: Multiple build files in subdirectories, workspace configuration files (`pnpm-workspace.yaml`, `lerna.json`, `nx.json`), `packages/`, `services/`, or `apps/` folders with their own build files, CI/CD matrix jobs per service

What to document:
- Which modules exist and what each does
- Where shared code lives
- Build and test commands per module vs root-level

---

## Testing Detection

Testing signals are consistent across stacks — look for the same patterns regardless of language.

**Where do tests live?**
- Co-located with source (e.g., `*.test.ts` next to `*.ts`, `*_test.go` next to `*.go`)
- Separate test folder (`test/`, `__tests__/`, `spec/`)
- Separate project or module (e.g., `Service.Tests/`, `src/test/`)

**What framework?** Read from the build file's test dependencies (e.g., `jest` in `package.json`, `testify` in `go.mod`, `xunit` in `.csproj`, `pytest` in `pyproject.toml`).

**What types of tests exist?**
- Look for integration test markers: build tags (`//go:build integration`), separate source sets, separate projects, or folder names (`integration/`, `e2e/`)
- Look for end-to-end test setup: browser automation libraries, docker-compose for test environments, Testcontainers usage
- Look for contract tests: Pact files, consumer-driven contract test setup

**Naming conventions?** Check existing test files. Common patterns: `should_verb_when_condition`, `TestFunction_WhenCondition_ExpectOutcome`, BDD-style descriptions, `given_when_then`. Document whatever pattern the repo actually uses.

**Mocking approach?** Check whether the repo uses a mocking library, manual test doubles, or real implementations with test databases. This affects what to document in the testing conventions.

*Example (illustrative — adapt to what you find):*
A Go repo might have `*_test.go` files alongside source with `testify` assertions, and a separate `integration/` folder tagged with `//go:build integration` run via `make test-integration`. Document what you actually discover, using the actual commands and library names from the repo.

---

## Monorepo & Hierarchy Detection

Before exploring tech stack details, check whether this is a monorepo:

| Signal | Meaning |
|--------|---------|
| Multiple build manifests in subdirectories | Multi-module or monorepo |
| `pnpm-workspace.yaml`, `lerna.json`, or `nx.json` | Node.js monorepo tooling |
| `packages/`, `services/`, `apps/` folders with own build files | Monorepo regardless of language |
| CI/CD with per-service job matrices | Strong monorepo signal |
| Single build manifest including multiple modules | Multi-module build (Gradle `settings`, Cargo workspace, etc.) |

**Checking for existing hierarchy:**
```bash
find . \( -name "agents.md" -o -name "AGENTS.md" -o -name "CLAUDE.md" \) \
  | grep -v node_modules | grep -v .git
```
Note which naming convention is in use and stick to it. If you find files at multiple levels:
1. Read the root one first — it sets the baseline
2. Note which services have their own files
3. When working on a specific service, read both the root and service-level file
4. When creating new content, decide which level it belongs at before writing

**What typically lives at each level in a monorepo:**

Root `agents.md`:
- What the monorepo contains (list of services and their purpose)
- Shared build setup and internal library conventions
- Shared observability setup (logging format, tracing approach)
- Shared CI/CD patterns
- Cross-service conventions (event naming, API conventions, error handling)

Service `agents.md`:
- What this specific service does (domain, ownership, upstream/downstream)
- Service-specific architecture (e.g., "this service uses CQRS, others don't")
- Service-specific external integrations
- Service-specific testing setup
- Anything the root didn't cover or this service does differently

---

## Harness-Specific Mechanics (Claude Code)

Claude Code supports two loading mechanisms beyond the root file:

**`@import` pointers** — load an additional file alongside root:
```
- @docs/api-conventions.md
```

**Path-scoped rules** (`.claude/rules/`) — load only when matching files are touched:
```yaml
---
paths:
  - "src/api/**"
---
All API endpoints must include input validation.
```

**Monorepo exclusions** (`claudeMdExcludes`) — exclude ancestor files from other teams in `.claude/settings.local.json`:
```json
{ "claudeMdExcludes": ["**/other-team/CLAUDE.md"] }
```

---

## Harness-Specific Copies

Some repos maintain copies of the root guidance file in harness-specific locations:
- `.amazonq/rules/AGENTS.md` — Amazon Q
- `.cursor/rules/` — Cursor
- `.kiro/` — Kiro AI

When you find these, they are almost always duplicates that drift out of sync. Use the `question` tool:

```
header: "Harness copies found"
question: "I found copies at <paths>. What should we do with them?"
options:
  - label: "Sync with root"      description: "Keep them, update to match root after all changes"
  - label: "Delete"              description: "Remove duplicates — the root file is enough"
  - label: "Leave as-is"        description: "Don't touch them"
custom: false
```

If syncing: treat the root file as the source of truth. Update harness copies last, after all root changes are finalised.
