# Section Templates & Examples

These templates show what good agents.md content looks like for each section. The goal is always repo-specific, actionable content — not generic filler.

**Important**: The output agents.md must always contain language-specific details discovered from the actual repo — the real language, framework, library names, patterns, and conventions used. These templates provide the structure; you fill in the specifics from what you find during exploration.

---

## Monorepo Root Example

When creating the root agents.md for a monorepo, the overview describes the whole repo and service-level specifics are deferred to individual files.

```markdown
# agents.md (root)

## Monorepo Overview
This repo contains the core backend services for the ordering platform. Each service is independently deployable.

**Services:**
- `services/order-service` — order lifecycle management
- `services/payment-service` — payment processing
- `services/menu-service` — restaurant menu data
- `packages/shared-events` — event schemas shared across services

See each service's `agents.md` for service-specific architecture and conventions.

## Shared Architecture
[One sentence per service group: pattern name + where things live.
E.g.: "All backend services follow Clean Architecture. Frontend packages use feature-sliced design."]

## Shared Conventions
- **Event naming**: [document the actual naming convention found in the repo]
- **Logging**: [document the actual logging approach — library, format, required fields]
- **Error responses**: [document the actual error response structure]

## Shared Tooling
- **Build**: [how to build across services — root command vs per-service]
- **CI/CD**: [pipeline tool and where configs live]
- **Local dev**: [how to spin up the local environment]

## Testing (Shared)
- [What's shared — test utilities, test infrastructure, naming conventions that apply everywhere]
```

---

## Layer-Level Examples

Layer-level files apply whenever a project has meaningful separation between layers — the principle is the same regardless of language or framework. Each layer has its own non-obvious rules, and an agent working in one layer doesn't need to read about another.

### Service Root (any layered service)

```markdown
# agents.md — [ServiceName]

## Overview
[What this service does. Its domain, key consumers, upstream/downstream dependencies.]

## Architecture
[Pattern name and how layers relate. Dependency direction if applicable.]
[Reference to layer sub-files: "See domain/agents.md, application/agents.md, etc."]

## Shared Conventions
- [Cross-cutting error handling approach]
- [Logging conventions — library, required fields]
- [Any rules that apply across all layers]

## Testing
- [Unit test location and how to run]
- [Integration test location and how to run]
- [Key testing rules — what gets mocked, what doesn't]
```

### Domain Layer (any stack)

```markdown
# agents.md — [domain/ or equivalent]

[One sentence: what this layer is and what it must NOT depend on.]

## What lives here
- [Entities / aggregate roots and their purpose]
- [Value objects and what makes them distinct]
- [Repository interfaces (definitions only, not implementations)]
- [Domain error types]

## Rules
- [Invariant enforcement — where and how]
- [What dependencies are forbidden in this layer]
- [How domain events work, if applicable]
```

### Application Layer (any stack)

```markdown
# agents.md — [application/ or equivalent]

[One sentence: orchestrates domain to execute use cases. What it knows about vs what it doesn't.]

## What lives here
- [Use case classes / handlers / commands]
- [DTOs — inputs and outputs]
- [Interfaces for infrastructure (defined here, implemented elsewhere)]

## Conventions
- [Return type convention — exceptions vs result types]
- [How validation works relative to handlers]
- [Event publishing pattern]
```

### Infrastructure Layer (any stack)

```markdown
# agents.md — [infrastructure/ or equivalent]

[One sentence: implements interfaces from domain/application. Lists what external systems live here.]

## What lives here
- [Database: ORM/query library, repository implementations, migrations]
- [Messaging: event publishers, consumers]
- [External HTTP clients]
- [Dependency injection registration]

## Conventions
- [ORM-specific rules (e.g., transaction boundaries, soft deletes, naming)]
- [Any rules about what infrastructure classes must NOT do]
```

---

*Concrete illustration (Kotlin/Spring Boot with Clean Architecture — adapt the specifics to your stack):*

```markdown
# agents.md — order-service

## Overview
Order lifecycle management service. Publishes to the orders Kafka topic.

## Architecture
Clean Architecture with multi-module Gradle. Modules: `domain`, `application`, `infrastructure`.
Dependency rule: infrastructure depends on application, application depends on domain. Domain has no external deps.
See each module's agents.md for layer-specific conventions.

## Shared Conventions
- Errors modelled as sealed classes (`DomainError`, subclasses) — no checked exceptions for business logic
- Logging: SLF4J with MDC, always include `orderId` and `correlationId`
- All Kafka consumers are idempotent — check for duplicate processing before acting

## Testing
- Unit: `./gradlew :domain:test :application:test` — pure JUnit 5 + MockK, no Spring context
- Integration: `./gradlew :infrastructure:integrationTest` — @SpringBootTest + Testcontainers
```

---

## Section Templates by Type

### Project Overview

**What to include**: What the service/app does, its domain, key consumers or upstream/downstream dependencies. Enough context that an agent understands *why* the repo exists and what it's responsible for.

**What to avoid**: Marketing language, vague descriptions, duplicating the README.

```markdown
## Project Overview
[service-name] is a [language/framework] [service type — microservice, API, worker, etc.] responsible for [core domain responsibility].

- [Key input: what it consumes or responds to]
- [Key output: what it produces or exposes]
- [Persistence: what it stores and where]
- [Consumers: who depends on it]
```

---

### Architecture & Structure

**What to include**: Folder structure with purpose, key layers, where new code should go. Be specific enough that an agent placing a new file gets it right the first time.

**What to avoid**: Listing every folder without explanation, generic layer descriptions that don't say what's actually in them.

```markdown
## Architecture & Structure
[Pattern name]. [Dependency direction if applicable].

[Folder structure — 2 levels max, with a phrase per folder explaining what belongs there]

New [feature type] goes in [path]. New [other type] goes in [other path].
```

*Example (Go, layered — illustrative):*
```markdown
## Architecture & Structure
Layered structure: handlers call services, services call stores.

├── cmd/server/    — Entry point, dependency wiring
├── handler/       — HTTP handlers (parse request, call service, write response — no business logic)
├── service/       — Business logic
├── store/         — Database access
├── model/         — Shared data types
└── testutil/      — Test helpers and fixtures

Handlers must not contain business logic. Store methods must not call services.
```

---

### Coding Conventions

**What to include**: Naming conventions, error handling patterns, patterns the team consistently uses that differ from language/framework defaults. Include short examples where a pattern isn't obvious from the name alone.

**What to avoid**: Language basics, things covered by the linter, things that are obvious from reading the code.

```markdown
## Coding Conventions
- **[Pattern name]**: [What it is and why — brief]
- **[Error handling]**: [The approach — exceptions vs result types vs error returns, with the specific type/library used]
- **[Naming]**: [Any non-obvious naming conventions for key concepts]
- **[Key constraint]**: [Anything that differs from framework defaults that would surprise a developer]
```

---

### Testing Strategy

**What to include**: Where tests live, how to run them, what test types exist, conventions about mocking/not mocking, how tests are named.

**What to avoid**: Generic advice about why testing is good, duplicating what the build file already documents obviously.

```markdown
## Testing Strategy
- **Unit tests**: [Location]. [Framework and mocking library]. [What gets mocked — interfaces, external systems].
- **Integration tests**: [Location and how to trigger]. [What infrastructure it needs — Docker, test DB, etc.].
- **Naming**: [The actual naming convention found in the repo]
- **Run unit tests**: [command]
- **Run integration tests**: [command] [(any prerequisites)]
- **Key rule**: [Anything non-obvious about the testing approach — e.g., "never mock the DB in integration tests", "always use the real message broker"]
```
