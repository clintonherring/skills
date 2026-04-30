---
name: jet-code-swarm
description: >-
  Multi-agent code quality and refactoring orchestration for JET services. Use
  this skill when you want to refactor a module or service, reduce technical
  debt, improve code quality, coordinate a multi-agent code review, migrate a
  pattern across a codebase, improve a service's architecture, or clean up
  legacy code. Triggers include: refactor, restructure, rewrite, clean up, tech
  debt, multi-agent review, swarm review, code quality improvement, pattern
  migration, decompose, extract service, reduce coupling, improve cohesion,
  eliminate duplication. Works across Kotlin/Spring Boot, TypeScript/Node.js,
  C#/.NET, and Python stacks. Integrates with gh and acli for PR creation and
  Jira context.
metadata:
  owner: ai-platform
---

# JET Code Swarm

Coordinate a swarm of specialised sub-agents to analyse, plan, implement, review, and test code quality improvements on any JET service.

## When to Use

- Refactoring a module, package, or service that has grown complex
- Migrating a pattern across multiple files (e.g. replacing a deprecated API, updating an abstraction)
- Performing a thorough multi-perspective code review before a major release
- Reducing technical debt in a bounded area with a structured, reviewable approach
- Any task where you want a second (and third) opinion before touching the code

## When NOT to Use

- Single-file fixes or trivial renames — a single agent is faster
- Hotfixes under time pressure — the checkpoint workflow is deliberate, not fast
- Tasks with no clear scope boundary — define the target first, then invoke the swarm

## Prerequisites

- [jet-company-standards](https://github.je-labs.com/ai-platform/skills/tree/master/skills/jet-company-standards) skill installed — used for `gh` PR creation and `acli` Jira integration

## References

| File | Load when... |
|------|-------------|
| [references/agent-role-prompts.md](references/agent-role-prompts.md) | Starting any agent step — contains the full prompt template for each role |
| [references/refactoring-patterns.md](references/refactoring-patterns.md) | Analyst and Architect steps — contains stack-specific patterns and anti-patterns |
| [references/review-checklist.md](references/review-checklist.md) | Reviewer step — contains the quality gate checklist |

## Step 1 — Gather Context

Before spawning any agents, gather the information needed to run the swarm effectively.

**Collect from the user:**

1. **Target scope** — Which files, package, module, or service? Be specific. Ask the user to confirm if ambiguous.
2. **Goal** — What problem are they solving? (e.g. "this service is hard to test", "too much duplication", "coupling to an external library we need to replace")
3. **Constraints** — Any files that must NOT change? API contracts to preserve? Deadlines?
4. **Jira context** — Is there a ticket? If so, fetch it:
   ```bash
   acli jira workitem view TICKET-123 --json --fields="summary,description,acceptanceCriteria"
   ```
5. **Stack detection** — Determine the tech stack by checking the project root:
   ```bash
   ls -1
   ```
   Then match against:

   | File present | Stack |
   |---|---|
   | `build.gradle.kts` or `build.gradle` | Kotlin / Spring Boot |
   | `package.json` | TypeScript / Node.js |
   | `*.csproj` or `*.sln` | C# / .NET |
   | `pyproject.toml` or `setup.py` | Python |

   Set `STACK` and `TEST_CMD` for use in later steps:

   | Stack | `TEST_CMD` |
   |---|---|
   | Kotlin | `./gradlew test` |
   | TypeScript | `npm test` or `npx jest` |
   | C# | `dotnet test` |
   | Python | `pytest` |

**Do not proceed to Step 2 until you have confirmed the target scope and goal with the user.**

**Sync with remote before starting:**

Before proceeding to Step 2, ensure the codebase is up-to-date with the base branch to prevent merge conflicts later. A refactoring PR that conflicts with `main` on day one is a waste of the whole swarm's work.

1. Fetch the latest from remote:
   ```bash
   git fetch origin
   ```
2. Check whether the current branch is behind:
   ```bash
   git status
   ```
3. If on a feature branch, rebase onto the base branch:
   ```bash
   git rebase origin/main
   ```
   (Replace `main` with the actual base branch if different — check `git remote show origin`.)
4. If there are conflicts, resolve them before proceeding. The swarm should always start from a conflict-free, up-to-date state.

## Step 2 — Analyst Agent

Spawn an **explore** sub-agent to perform a deep read-only analysis of the target scope.

Load [references/agent-role-prompts.md](references/agent-role-prompts.md) and use the **Analyst prompt template**.

**Task tool invocation:**
```
Use the Task tool with subagent_type="explore" and the Analyst prompt from references/agent-role-prompts.md,
injecting: target scope, goal, stack, and any constraints gathered in Step 1.
```

**Expected output from Analyst:**
- Inventory of files in scope with a one-line characterisation of each
- Top issues found: complexity hotspots, duplication, tight coupling, naming, SOLID violations, stack anti-patterns
- Risk assessment: which areas are most fragile or most impactful to change
- Suggested entry points for refactoring

**Do not edit any files in this step.** The Analyst is read-only.

## Step 3 — Architect Agent

Spawn a **general** sub-agent to turn the Analyst's report into a concrete, prioritised refactoring plan.

Load [references/agent-role-prompts.md](references/agent-role-prompts.md) and use the **Architect prompt template**.
Load [references/refactoring-patterns.md](references/refactoring-patterns.md) for stack-specific pattern guidance.

**Task tool invocation:**
```
Use the Task tool with subagent_type="general" and the Architect prompt from references/agent-role-prompts.md,
injecting: Analyst report, target scope, goal, stack, constraints.
```

**Expected output from Architect:**

A structured plan in this format:

```
## Refactoring Plan

**Goal:** <one sentence>
**Stack:** <detected stack>
**Total steps:** <N>

### Step 1 — <short name>
- Files affected: <list>
- What to do: <clear description>
- Acceptance criteria: <how we know this step is done>
- Risk: Low / Medium / High
- Rationale: <why this order>

### Step 2 — ...
```

**The Architect must NOT write any code.** The plan is a document, not an implementation.

## Step 4 — User Checkpoint

**STOP. Present the Architect's plan to the user and ask for approval before making any code changes.**

Say explicitly:
> "Here is the proposed refactoring plan. Please review it and confirm you'd like to proceed, or let me know what to change."

Only continue to Step 5 after receiving explicit approval. If the user requests changes, loop back to Step 3 with the feedback.

This checkpoint exists because:
- The user may know about constraints the agents do not
- The plan may surface scope issues worth discussing before spending time on implementation
- It keeps the human in control of what changes are made to their codebase

## Step 5 — Coder Agent

Spawn a **general** sub-agent to implement the approved plan, one step at a time.

Load [references/agent-role-prompts.md](references/agent-role-prompts.md) and use the **Coder prompt template**.

**Task tool invocation:**
```
Use the Task tool with subagent_type="general" and the Coder prompt from references/agent-role-prompts.md,
injecting: approved plan, stack, TEST_CMD, constraints.
```

**The Coder must:**
- Work through plan steps in order
- After each step: run `TEST_CMD` and confirm it passes before proceeding
- If a step causes test failures it cannot fix within 2 attempts, document the failure and move on — do not silently skip
- Produce a completion report listing: steps done, steps skipped (with reason), test results

**Safety rules for the Coder:**
- Never modify files outside the agreed scope without asking
- Never delete files — mark them as candidates for removal in the completion report
- Preserve all public API contracts unless the plan explicitly says otherwise
- Do not change unrelated formatting or whitespace in untouched files

## Step 6 — Reviewer Agent

Spawn a **general** sub-agent to review all changes made by the Coder against the plan and quality checklist.

Load [references/agent-role-prompts.md](references/agent-role-prompts.md) and use the **Reviewer prompt template**.
Load [references/review-checklist.md](references/review-checklist.md) for the quality gate checklist.

**Task tool invocation:**
```
Use the Task tool with subagent_type="general" and the Reviewer prompt from references/agent-role-prompts.md,
injecting: approved plan, Coder completion report, stack, constraints, review checklist.
```

**Expected output from Reviewer:**

```
## Review Report

### Plan Compliance
- Step 1: ✅ Implemented as specified / ⚠️ Partial / ❌ Not implemented
  - Notes: ...

### Quality Gate Results
- [ ] Issue found: <file>:<line> — <description> — Severity: Minor / Major / Blocking

### Verdict
PASS / PASS WITH NOTES / FAIL

### Recommended follow-up actions (if any)
```

If the Reviewer returns **FAIL**, loop back to Step 5 with the blocking issues listed. If the Reviewer returns **PASS WITH NOTES**, proceed to Step 7 but ensure all Major issues are resolved before opening a PR.

## Step 7 — Tester Agent

Spawn a **general** sub-agent to write or update tests for the refactored code.

Load [references/agent-role-prompts.md](references/agent-role-prompts.md) and use the **Tester prompt template**.

**Task tool invocation:**
```
Use the Task tool with subagent_type="general" and the Tester prompt from references/agent-role-prompts.md,
injecting: approved plan, Coder completion report, Reviewer report, stack, TEST_CMD, constraints.
```

**The Tester must:**
- Add or update tests that cover the refactored behaviour
- Follow the stack's testing conventions (see [references/refactoring-patterns.md](references/refactoring-patterns.md))
- Run `TEST_CMD` and confirm all tests pass before finishing
- Report: tests added, tests updated, coverage delta if measurable, final test result

## Step 8 — Wrap Up

After all agents complete, you (the orchestrator) handle the final actions.

### Summary report

Present a concise summary to the user:

```
## Swarm Complete

**Goal:** <goal>
**Steps completed:** N / N
**Tests:** <pass/fail count>
**Reviewer verdict:** PASS / PASS WITH NOTES / FAIL

### What changed
- <file> — <one-line summary>
- ...

### Recommended follow-up
- ...
```

### Git + PR (requires user confirmation)

Only create a commit and PR if the user explicitly asks. When they do:

1. Detect the commit message convention:
   ```bash
   git log --oneline -10
   ```
   Match `TICKET-123: description` or `TICKET-123 description` pattern from existing commits.

2. Create a feature branch and commit:
   ```bash
   git checkout -b refactor/<short-description>
   git add <changed files>
   git commit -m "TICKET-123: <summary of refactoring>"
   ```

3. Push and open a PR:
   ```bash
   GH_HOST=github.je-labs.com gh pr create \
     --title "TICKET-123: <summary>" \
     --body "$(cat <<'EOF'
   ## Summary

   - <bullet 1>
   - <bullet 2>

   ## Jira

   [TICKET-123](https://justeattakeaway.atlassian.net/browse/TICKET-123)
   EOF
   )"
   ```

4. Update Jira ticket to "Review" status:
   ```bash
   acli jira workitem transition TICKET-123 "In Review"
   ```

### Never push without explicit user confirmation.

## Safety Rules

- **Always** confirm scope and goal with the user before Step 2
- **Always** checkpoint at Step 4 before any code changes
- **Never** push to remote without explicit user permission
- **Never** modify files outside the agreed scope
- **Never** delete files — flag them as removal candidates instead
- **Never** break public API contracts unless explicitly planned
- Run `TEST_CMD` after every Coder step — a failing test suite is a blocker
- If any agent fails to produce its expected output, report it clearly and ask the user how to proceed
