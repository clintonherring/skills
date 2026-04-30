# jet-assess-agent-guidance-files

## Purpose

Evaluate the **agentic readiness** of a repository by assessing the quality and coverage of its `AGENTS.md` or `CLAUDE.md` files. The skill helps teams ensure their agent guidance files are correct, concise, and complete enough to effectively guide an AI coding agent.

## Installation

```bash
npx skills add git@github.je-labs.com:ai-platform/skills.git --skill jet-assess-agent-guidance-files
```

## What It Does

Given a repository, the skill inspects the root `AGENTS.md` / `CLAUDE.md` file (and any nested ones that are explicitly referenced) and evaluates them across eight criteria:

| # | Check | What is verified |
|---|-------|-----------------|
| 1 | **Root agent file** | File exists and its line count is within the allowed limit (≤150 ideal, ≤200 max) |
| 2 | **Monorepo structure** | If a monorepo is detected, all significant sub-projects are covered or have their own agent guidance files |
| 3 | **Tech stack** | Language(s), framework(s), databases, and message brokers are explicitly specified |
| 4 | **Architecture** | Key design patterns and architectural style are described |
| 5 | **Performance requirements** | Concrete, testable expectations are present (e.g., pagination rules, latency targets) |
| 6 | **Testing strategy** | Test types, expectations, and how to run tests are defined or referenced |
| 7 | **Endpoint & event documentation** | API endpoints and async events are documented in any accepted format (OpenAPI, AsyncAPI, Markdown, etc.) |
| 8 | **Security & authentication** | Secret handling, auth mechanisms, authorization model, and agent-specific constraints are specified |

## Output

The skill produces a structured assessment report:

```
Verdict: PASS | PARTIAL PASS | FAIL
Score: X/100

Checks:

1. Root agent file
   - Found: yes/no
   - Lines: N
   - Status: PASS / WARN / FAIL

2. Monorepo structure
   - Detected: yes/no
   - Coverage: adequate / incomplete
   - Status: PASS / FAIL

3. Tech stack
   - Status: PASS / WARN / FAIL
   - Missing: [...]

4. Architecture
   - Status: PASS / WARN / FAIL

5. Performance
   - Status: PASS / WARN / FAIL

6. Testing
   - Status: PASS / FAIL

7. Docs (API/events)
   - Status: PASS / FAIL

8. Security & authentication
   - Status: PASS / WARN / FAIL
   - Missing: [...]
```

Each check is rated **PASS**, **WARN**, or **FAIL**, and an overall verdict with a score out of 100 is provided.
