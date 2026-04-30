# Coverage Checklist

Use this during repo exploration and gap analysis (Create mode).

Not every topic applies to every project — a static site needs 3 of these; a distributed microservice needs most. Use this as an investigation guide, not a mandatory list. For each topic: check whether the repo has signals for it, and check whether the existing agents.md system covers it. Present gaps to the developer and let them classify each as "add / not needed / handled elsewhere".

---

## 1. Architecture & Design Patterns

**Signals to look for:**
- Folder names: `domain/`, `application/`, `ports/`, `adapters/`, `infrastructure/`, `contexts/`
- Import direction (do infrastructure files import domain? Or vice versa — violations signal drift)
- Naming conventions (aggregates, entities, value objects, use cases, commands, events)

**What belongs in root:** One sentence — pattern name + key top-level boundaries.
E.g., `"Clean Architecture. Domain in src/domain/, adapters in src/infrastructure/."`

**What belongs in sub-files:** Invariants the agent must respect, module responsibilities, where new features of each type go, bounded context descriptions.

---

## 2. Performance

**Signals to look for:**
- ORM configuration (eager/lazy loading defaults, N+1 detection tools)
- Pagination patterns in controllers (cursor-based, offset, max page sizes)
- Caching infrastructure (Redis, Memcached, in-memory)
- Batch processing patterns

**What belongs in root:** Universal constraints. E.g., `"All list endpoints must be paginated. No unbounded queries."`

**What belongs in sub-files:** ORM-specific query patterns, cache invalidation rules for a specific domain, batch processing conventions for a specific worker.

**Hard fail:** Missing when the repo clearly uses an ORM with N+1 risk, or has list endpoints without documented pagination rules.

---

## 3. Security, Authentication & Identity

**Signals to look for:**
- Auth middleware location and pattern (JWT decode, session validation, OAuth)
- Identity provider SDKs in deps (Okta, Keycloak, Auth0, AWS Cognito, Firebase Auth, IdentityServer)
- Authorization checks (role guards, policy objects, CASL, casbin — where do they live?)
- Input validation libraries and where validation happens (class-validator, zod, joi, FluentValidation)
- Secrets management (env files, vault, AWS Param Store, cloud secrets manager)
- SAST/security scanning config (Semgrep, Wiz, Snyk, SonarQube, CodeQL workflows) — does it block CI?
- Audit logging patterns (CloudTrail integration, custom audit log writes)
- Any hardcoded credentials to flag

**What belongs in root:** Universal rules. E.g., `"Never hardcode secrets. Validate all external input before it reaches domain logic. Auth via Okta — tokens validated in middleware."`

**What belongs in sub-files:** Auth/authz patterns scoped to the API layer, security conventions for a specific service, identity provider config details, audit logging requirements for specific domains.

**Hard fail:** Missing when the repo clearly involves secrets, auth/authz, production access, PII, or external integrations. Note: agent-specific constraints also go here (e.g., "don't run destructive commands without confirmation", "don't access production data directly").

---

## 4. Error Handling

**Signals to look for:**
- Custom error classes or error type hierarchy
- Global error handlers or middleware
- Error propagation patterns (throw vs. return error objects, Result types, Either monads)
- Retry logic, circuit breakers
- Error logging conventions

**What belongs in root:** Universal strategy. E.g., `"Use typed errors (extend AppError). Log before re-throwing across service boundaries."`

**What belongs in sub-files:** Service-specific retry policies, circuit breaker config for external dependencies, error response format for API layer.

---

## 5. Data Access

**Signals to look for:**
- Repository pattern vs. direct ORM calls
- Transaction boundaries (where transactions start/end)
- Migration tools (Flyway, Liquibase, Alembic, EF Core migrations)
- Soft deletes vs. hard deletes
- Read/write splitting

**What belongs in root:** Key rules affecting all code. E.g., `"Never call ORM directly from service layer — use repository interfaces."`

**What belongs in sub-files:** Transaction patterns for a specific domain, migration naming conventions, replica routing rules.

---

## 6. API Contracts, Messaging & Interoperability

**Signals to look for:**
- Response envelope structure (`{ data, meta }`, `{ result, error }`, etc.)
- Versioning strategy (URL path `/v1/`, header versioning)
- Pagination format in responses
- Error response format
- OpenAPI/Swagger specs
- Kafka/event schemas (AsyncAPI, schema registry, inline docs)
- Message broker clients in deps (Kafka, SQS/SNS, RabbitMQ, NATS)
- Cloud Events library or envelope format
- Message body format conventions (JSON, Avro, Protobuf)
- Schema files (`.avsc`, `.proto`) and schema registry usage
- gRPC proto files and code generation commands
- Event/message folders (`events/`, `messages/`, `schemas/`)

**What belongs in root:** Envelope format and versioning rule (brief). Event/topic naming convention if consistent across services. Message format (JSON/Avro/Protobuf). E.g., `"All responses use { data, meta }. Events use Cloud Events envelope. Schemas in schemas/ — Avro with schema registry."`

**What belongs in sub-files or linked docs:** Full API conventions for a specific service. Event schema location and naming conventions. Consumer idempotency requirements. Schema evolution rules. gRPC service boundaries and proto generation commands.

**Hard fail:** Missing when APIs or async messaging clearly exist and there's no pointer to where they're documented.

---

## 7. Observability

**Signals to look for:**
- Logging library and structured logging format
- Trace/span instrumentation (OpenTelemetry, Datadog APM)
- Metrics conventions (naming patterns, what gets measured)
- Log level usage conventions

**What belongs in root:** Logging library and key rules. E.g., `"Structured logging via pino. Always include requestId in log context. No console.log in production."`

**What belongs in sub-files:** Service-specific metric naming, tracing conventions for a specific integration.

---

## 8. Deployment, Platform & Infrastructure

**Signals to look for:**
- CI/CD pipeline config (GitHub Actions, Jenkinsfile)
- Environment differentiation (feature flags, env-specific config)
- Container/orchestration setup (Dockerfile, docker-compose, Kubernetes, Podman)
- Secrets injection patterns (Vault, AWS Param Store, `${{secrets.*}}` in CI)
- Config store references (AWS Param Store paths, Vault paths, ConfigMaps)
- Artifact registries (Artifactory, Nexus, GitHub Packages, npm registry overrides in `.npmrc`)
- Task runners (Makefile, Taskfile.yml, justfile) — read them, they reveal non-obvious commands
- Infrastructure as code (Terraform, Pulumi, CDK)

**What belongs in root:** Only facts the agent needs for code decisions. E.g., `"Cold start time matters — avoid heavy module-level initialization."`, `"All config from Param Store — never use local config files in production."`, `"Private registry: Artifactory — see .npmrc for auth setup."` Usually not needed unless deployment/platform constraints affect how code is written.

---

## 9. State Management (frontend)

**Signals to look for:**
- State management library (Redux, Zustand, Pinia, MobX, Jotai)
- Server state library (React Query, SWR, Apollo)
- Local vs. server state separation patterns

**What belongs in root:** Library names and key rules. E.g., `"Zustand for local UI state. React Query for server state. Never use Redux."`

---

## 10. Concurrency & Background Jobs

**Signals to look for:**
- Background job frameworks and queue libraries
- Scheduling libraries in deps (Quartz, Hangfire, `node-cron`, EventBridge rules)
- Kubernetes CronJob manifests
- Locking patterns (optimistic locking, advisory locks)
- Idempotency handling (queues, webhooks, retried requests)
- Race condition mitigations
- Job registration patterns and schedule config location

**What belongs in root:** Universal rules. E.g., `"All queue consumers must be idempotent. Use idempotency keys for external API calls. CronJobs must be idempotent — no locking guarantees."`

**What belongs in sub-files:** Scheduled job inventory (what runs when), job registration patterns for a specific service, retry and DLQ policies.

---

## 11. Accessibility (frontend)

**Signals to look for:**
- a11y testing tools (axe, jest-axe, Playwright accessibility checks)
- ARIA patterns in components
- Focus management conventions

**What belongs in root:** `"All new components must pass axe audits. Keyboard navigation required for all interactive elements."`

---

## Gap Presentation Format

After investigating the repo, present what was found and what wasn't using this format:

```
I found documented conventions for: [topics covered].

These topics appear relevant to this repo but aren't covered:

| Topic         | Signal found                           | Suggested action                      |
|---------------|----------------------------------------|---------------------------------------|
| Architecture  | Layered structure — pattern not named  | Document in root (1 line) + sub-file  |
| Performance   | Pagination in controllers — no rules   | Ask: N+1/caching conventions?         |
| Security      | JWT middleware present — no auth docs  | Document auth pattern in API sub-file |
| Error handling| Custom AppError class found            | Ask if propagation strategy exists    |

Which of these gaps matter for your project? (add / not needed / handled elsewhere)
```

Let the developer classify each gap before adding anything. Don't add coverage for topics they say are handled elsewhere or not needed.
