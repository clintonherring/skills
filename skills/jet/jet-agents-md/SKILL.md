---
name: jet-agents-md
description: >
  Creates and manages agent guidance files (AGENTS.md, CLAUDE.md) for any codebase. Use this skill when a developer wants to create, update, or improve guidance files that help AI agents work effectively with their repo — triggered by phrases like "create an AGENTS.md", "update my CLAUDE.md", "set up agent context", "help the AI understand my repo", or any mention of AGENTS.md, CLAUDE.md, agent context, or agent guidance files. Also triggers when the user wants to improve how AI agents interact with their codebase, even without using the exact filename. Does not generate README files, API documentation, or linter configurations.
metadata:
  owner: ai-platform
---

# agents.md / AGENTS.md / CLAUDE.md Skill

This skill covers all three naming conventions:
- **`AGENTS.md`** — the uppercase convention, used by OpenCode and multi-agent harnesses
- **`agents.md`** — lowercase variant, same purpose
- **`CLAUDE.md`** — Claude Code's native format; supports `@import` and `.claude/rules/` path-scoped files

All three are **control layers, not documentation systems**. Their job is to guide decisions, define constraints, and point to deeper documentation — not to document everything. Every line loads on every session, so every line must earn its cost.

When creating or updating, use whatever convention is already in the repo. If starting fresh, ask which the developer prefers or which agent harness they're using.

**Interaction rule: always use the `question` tool when asking the developer anything.** Never present questions as inline text or blockquotes. Use structured options so the developer can select rather than type free-form answers. Always enable `custom` input on open-ended questions so the developer can type their own answer when none of the options fit.

---

## Step 1: Determine the Mode

If the user's intent isn't clear, use the `question` tool:

```
question tool call:
  header: "Mode"
  question: "How can I help with your agent guidance file?"
  options:
    - label: "Create"
      description: "Explore the repo and generate files from scratch"
    - label: "Manage"
      description: "Make targeted updates after a change (new module, refactor, new integration)"
  custom: true  (user may want to clarify a hybrid intent)
```

---

## Core Principles

These apply to everything this skill produces:

- **200-line limit for root files.** Compliance degrades measurably above this. Files exceeding 200 lines will be partially ignored. Sub-files don't have this constraint — they only load when the agent is working in that area.
- **Two failure modes.** (1) *Length* — too many instructions, agent compliance drops. (2) *Task-irrelevant requirements* — correct but unneeded instructions still get followed, increasing cost. Both hurt.
- **Don't list inferrable content.** The agent reads build files, manifests, and package managers directly. Never document commands whose names reveal their purpose (`dev`, `build`, `start`, `lint`, `test`). Only document non-obvious commands (e.g., `db:migrate`, `cf-typegen`, `dotnet ef database update`). Never list directory trees deeper than 2 levels — replace with a sentence.
- **Don't send an LLM to do a linter's job.** Style and formatting rules belong in a linter config, not in agents.md.
- **Architecture in root: one sentence.** Name the pattern and key top-level boundaries. Deeper context — invariants, module responsibilities, where business logic lives — belongs in sub-files where it loads only when relevant.
- **Never repeat what a parent file already covers.** Sub-files extend, never duplicate. Shared facts belong in the shallowest file covering all relevant paths (Least Common Ancestor).
- **Output is always language-specific.** The skill instructions are stack-agnostic, but the agents.md files you produce must contain concrete, repo-specific details discovered from the codebase — the actual language, framework, library names, patterns, and conventions used. Generic placeholder content is a failure.

---

## File Hierarchy

AI agents read context relative to where they're working. Place each file as close as possible to the code it describes. Keep each file focused on what isn't obvious from that level.

### Depth

- **Single service** → one root file is enough.
- **Monorepo / multi-service** → root (shared conventions) + per-service files.
- **Complex layered service** (distinct architectural layers with different rules) → service root + per-layer files. Layer files are worth creating whenever layers have meaningfully different conventions — the language doesn't matter.

See `references/section-templates.md` for annotated hierarchy examples across common patterns (monorepo, Clean Architecture, Hexagonal, etc.).

### Hierarchy Rules

- **Plan leaf-first, write top-down** — think through what belongs at each depth before writing anything. Then write root first (it establishes the contract and pointers), then sub-files. The root must know what it's pointing to before sub-files exist.
- **Sub-files can be richer** — architecture details, invariants, performance conventions, security patterns all belong in sub-files rather than crowding the root.
- **Claude Code harness mechanics** (`@import`, path-scoped rules, `claudeMdExcludes`) — see `references/detection-guide.md` § "Harness-Specific Mechanics".
- **Harness copies** (`.amazonq/`, `.cursor/`, `.kiro/`) — see `references/detection-guide.md` § "Harness-Specific Copies".

---

## Step 2: Phase 1 — Ask Before Exploring

**For Create mode: ask these questions before touching the repo.** They cover things that cannot be inferred from code. Skip any the user already answered. If the intent makes some answers obvious (e.g., "write a CLAUDE.md for my monorepo" → harness is Claude Code, hierarchy is likely needed), state your inference and confirm rather than asking.

**Exceptions — proceed without Phase 1 questions:**
- User asks a specific, pointed question (e.g., "should we add N+1 rules?") → answer it; don't redirect to a questionnaire
- User is asking about one specific aspect → answer it; Phase 1 is for building a complete file from scratch

**Phase 1 questions — always use the `question` tool:**

**Batch 1 — ask Q1–Q4 together in a single `question` tool call (4 independent questions, no conditional follow-ups):**

```
Q1 — header: "Agent harness"
  question: "Which agent are you writing this for?"
  options:
    - label: "Claude Code"         description: "Produces CLAUDE.md"
    - label: "OpenCode / multi-agent"  description: "Produces AGENTS.md"
    - label: "No preference"       description: "I'll follow whatever's already in the repo"
  custom: true

Q2 — header: "Audience"
  question: "Who is this guidance file for?"
  options:
    - label: "AI agents only"
    - label: "Human developers too"
    - label: "Both"
  custom: false

Q3 — header: "Source"
  question: "Where should I discover conventions from?"
  options:
    - label: "Explore the repo"         description: "Discover conventions from the codebase"
    - label: "Start from existing file" description: "Refine what you already have"
    - label: "Both"                     description: "Explore the repo and incorporate the existing file"
  custom: false

Q4 — header: "Convention depth"
  question: "For each convention I document, how much detail do you want?"
  options:
    - label: "Rule only"           description: "One line stating the rule"
    - label: "Rule + rationale"    description: "Rule plus a brief explanation of why"
  custom: false
```

**Q5 — ask individually (has conditional follow-up):**

```
Q5 — header: "Architecture pattern"
  question: "Does the codebase follow a specific architectural pattern?"
  options:
    - label: "Clean Architecture"
    - label: "DDD"
    - label: "Hexagonal"
    - label: "CQRS"
    - label: "Layered"
    - label: "Event-driven"
    - label: "Infer from code"    description: "I'm not sure — discover it from the repo"
  custom: true

  → If a specific pattern is named, immediately use the `question` tool for the follow-up:
    header: "Architecture boundaries"
    question: "What are the key boundaries? Where does business logic live vs. infrastructure?"
    options: []  (custom: true — open-ended, no preset options)

  → If DDD: also ask via `question` tool:
    header: "Bounded contexts"
    question: "What are the main bounded contexts? Any aggregates or domain events the agent should know about?"
    custom: true

  → If event-driven: also ask via `question` tool:
    header: "Event system"
    question: "What's the event bus or broker? What are the main event types?"
    custom: true
```

**Q6 — ask individually (has conditional follow-up):**

```
Q6 — header: "Performance conventions"
  question: "Are there performance conventions to document?"
  options:
    - label: "Yes"          description: "N+1 prevention, pagination strategy, caching rules, batch limits"
    - label: "No"           description: "No specific conventions"
    - label: "Not sure"     description: "Infer from the codebase"
  custom: false

  → If Yes and ORM is mentioned, use the `question` tool:
    header: "ORM query rules"
    question: "Which ORM? Are there rules about eager/lazy loading or query patterns to avoid?"
    custom: true

  → If Yes and caching is mentioned, use the `question` tool:
    header: "Caching strategy"
    question: "What's the caching strategy? (TTL, invalidation approach, cache-aside?) Any cache boundaries?"
    custom: true
```

**Q7 — ask individually (has conditional follow-up):**

```
Q7 — header: "Security patterns"
  question: "Are there security patterns to follow?"
  options:
    - label: "Yes"          description: "Auth/authz approach, secrets management, validation layer, agent constraints"
    - label: "No"           description: "No specific patterns"
    - label: "Not sure"     description: "Infer from the codebase"
  custom: false

  → If Yes and auth is mentioned, use the `question` tool:
    header: "Auth pattern"
    question: "What's the auth pattern? (JWT, session, OAuth?) Where does authorization logic live?"
    custom: true

  → If Yes and secrets are mentioned, use the `question` tool:
    header: "Secrets management"
    question: "How are secrets managed? Is there anything that must never be hardcoded?"
    custom: true
```

**Q8 — always ask individually (cannot be inferred from code):**

```
Q8 — header: "Bug workflow"
  question: "When fixing a bug, what's the preferred workflow?"
  options:
    - label: "Test first"   description: "Write a failing test that reproduces the bug, then fix it"
    - label: "Fix directly" description: "Jump straight to the fix"
  custom: false
```

---

## Step 3: Explore the Repo

Detect before claiming. See `references/detection-guide.md` for specific signals. In summary:
- **Language/runtime**: build files, source extensions, package managers
- **Architecture**: top-level folder names, module structure, naming conventions
- **Testing**: test locations, framework imports, naming conventions
- **Messaging & interop**: broker clients, event schemas, Cloud Events, gRPC protos
- **Security & identity**: auth middleware, identity provider SDKs, SAST config, secrets management
- **Platform & infrastructure**: container setup, config stores, scheduling, artifact registries, CI/CD pipelines

After exploring, load `references/coverage-checklist.md` and work through each relevant topic area. Use repo signals to verify or challenge what the developer said in Phase 1. Bring findings to Phase 2.

When exploration leaves uncertainty about a pattern or domain concept, use the `question` tool:

```
header: "<topic being clarified, e.g. 'Caching layer'>"
question: "I see <X> in the codebase — how should I interpret it?"
options:
  - label: "<interpretation A>"
  - label: "<interpretation B>"
custom: true
```

---

## Step 4: Execute the Mode

### Mode: Create

**Phase 2 — Present findings before writing anything:**

After exploring, surface what you found and what's missing as a gap table (see `references/coverage-checklist.md` for format and gap presentation). For each gap, use the `question` tool with options: "Add" / "Not needed" / "Handled elsewhere" — all gaps in a single call.

Then:
1. **Propose the right hierarchy depth** — use the `question` tool to confirm (`Yes, proceed` / `Single root file only` / `Deeper hierarchy needed`) before generating.
2. **Work top-down, one level at a time** — root first, then service, then layers.
3. Keep root under 200 lines; move detail into sub-files.
4. Present each draft, get confirmation via the `question` tool, then move to the next level.

### Mode: Manage

Use the `question` tool to ask what changed (options: "New module or feature added" / "Refactoring or restructure" / "New external integration" / "Dependency or tooling change" / "Convention or process change"; `custom: true`).

Then:
1. Identify which level needs updating — shared convention (root), service-specific, or layer-specific
2. Read the relevant file(s) and explore the changed areas
3. Make targeted updates — preserve everything still accurate
4. If a new layer/module was added, offer to create a new agents.md for it and check if parent files need a pointer
5. Show a summary of what changed and at which level before saving

---

## Step 5: Verify

After writing all files, run a final consistency check:

1. **Read back every file written or modified.** Confirm the content on disk matches what was approved.
2. **Check root pointers.** For every sub-file pointer in the root (e.g., `See src/domain/AGENTS.md`), verify the sub-file exists at that exact path.
3. **Confirm no content was lost.** Every piece of information from any existing file either still exists somewhere in the hierarchy or was intentionally removed with a documented reason.
4. **Check for accidental duplication.** Scan sub-files for content already stated in root. Remove duplicates; root wins.
5. **Sync harness copies** if the developer chose "Sync with root" — update them last, after root is finalised.
6. **Present a final summary table:**

   | File | Action | Lines |
   |------|--------|-------|
   | `AGENTS.md` | Created | 57 |
   | `src/domain/AGENTS.md` | Created | 87 |
   | ... | | |

---

## Output Structure for Root Files

Root files should be lean — this is a template, not a minimum. Omit sections that don't apply. Use whatever filename convention (`agents.md`, `AGENTS.md`, or `CLAUDE.md`) is already established in the repo.

```markdown
# Project or Area Name

One sentence: what it does and why it exists.

## Stack
Language, framework, key infrastructure. Architecture pattern + key boundaries (1-2 lines max).
Non-standard path aliases if any.

## Development
Non-obvious commands only (skip dev, build, start, lint — agent reads build files directly).
E.g.: `db:migrate`, `cf-typegen`, `dotnet ef database update`

## Conventions
Only things the agent can't infer from reading the code.
Universal performance rules (N+1, pagination).
Universal security rules (secrets, validation layer).
Scoped or detailed rules → sub-files.
```

See `references/section-templates.md` for examples across different architectural patterns and stacks.

---

## Reference Files

| File | Load when |
|------|-----------|
| `references/detection-guide.md` | Exploring any new repo |
| `references/coverage-checklist.md` | Running gap analysis (Create mode) |
| `references/section-templates.md` | Writing content for any stack |
