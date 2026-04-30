---
name: cost-optimized-routing
description: Optimizes token cost by routing tasks to the cheapest effective agent. Classifies work into phases (explore, plan, build, troubleshoot) and delegates to fast subagents for simple work while keeping the main agent as orchestrator for context and escalation. Use at the start of every task, when planning work, when building features, or when the user asks about cost optimization.
---

# Cost-Optimized Agent Routing

Route every task to the cheapest agent that can handle it. The main agent (user's selected model) acts as orchestrator and never loses context. Cheap subagents do the grunt work.

## Task Classification

When the user presents a task, classify it IMMEDIATELY before doing anything else:

| Category | Cost | Route To | When |
|----------|------|----------|------|
| **EXPLORE** | Lowest | `Task` subagent, `model="fast"`, `subagent_type="explore"` | Finding files, understanding structure, searching code |
| **PLAN** | Low | `SwitchMode` to Plan mode | Architecture decisions, multi-approach trade-offs, large scope tasks |
| **BUILD-SIMPLE** | Low | `Task` subagent, `model="fast"`, `subagent_type="generalPurpose"` | Boilerplate, config changes, single-file edits, repetitive code, straightforward implementations |
| **BUILD-COMPLEX** | Higher | Main agent directly | Multi-file refactors with dependencies, novel logic, security-sensitive code |
| **TROUBLESHOOT** | Higher | Main agent directly | Debugging, fixing broken code, issues requiring conversation context |

### Classification Rules

1. **Default to cheap**: If unsure between SIMPLE and COMPLEX, try SIMPLE first
2. **Never cheap for debugging**: Troubleshooting always needs the main agent's full context
3. **Plan before build**: If the task has multiple valid approaches, PLAN first, then BUILD
4. **Parallel exploration**: Launch multiple EXPLORE subagents simultaneously for different areas
5. **Avoid Max Agents**: Never use max mode or an agent that is only available in max mode. Take into account the cost limits, e.g. over 200k context agents get more expensive.

## Workflow

### Step 1: Classify and Announce

Tell the user: "This is a [CATEGORY] task. I'll [route description] to keep costs down."

### Step 2: Write Context Brief (for subagent tasks)

Before delegating to any subagent, write a task brief to `tasks/` with:

```
File: tasks/[task-name]-[date].md

## Objective
[What needs to be done]

## Relevant Files
- [file paths and what they contain]

## Constraints
- [Any rules, patterns, or requirements]

## What Was Tried
- [Previous attempts and results, if any]
```

This persists context across sessions and helps escalation.

### Step 3: Delegate or Execute

**For EXPLORE tasks:**
```
Task(subagent_type="explore", model="fast", prompt="[detailed search query]")
```

**For BUILD-SIMPLE tasks:**
```
Task(subagent_type="generalPurpose", model="fast", prompt="[complete implementation brief]")
```

Write thorough subagent prompts. The subagent starts fresh with NO conversation history. Include:
- Exact file paths to read/modify
- The specific change to make
- Code patterns to follow (paste examples if needed)
- Expected output/behavior

**For PLAN tasks:**
Switch to Plan mode. Discuss approach with user. When plan is agreed, classify the implementation work and route accordingly.

**For BUILD-COMPLEX and TROUBLESHOOT tasks:**
Execute directly as the main agent. Full tools, full context.

### Step 4: Review Subagent Output

After every subagent completes:
1. Verify the output is correct
2. If correct: update task file, move to next step
3. If wrong: follow Escalation Path below

## Escalation Path

When a fast subagent produces incorrect output:

```
LEVEL 1: Re-delegate with better instructions
  - Analyze what went wrong
  - Write a more detailed prompt with explicit constraints
  - Try fast subagent again (one retry only)

LEVEL 2: Main agent handles directly
  - If retry also fails, the main agent fixes it directly
  - The main agent has full conversation context - no information is lost
  - Update the task file with what failed and why

LEVEL 3: Suggest model upgrade (cross-session)
  - If the main agent also struggles, note in the task file
  - Suggest the user try with a more capable model for this specific task
```

## Context Preservation

### Within a session
The main agent retains ALL conversation context. Subagent failures do not lose context because the main agent is always the orchestrator reviewing results.

### Across sessions
Task files in `tasks/` preserve context. Always update them with:
- What was completed
- What failed and why
- Next steps remaining
- File paths that were modified

### When the user returns
If a task file exists for ongoing work, read it first and summarize the current state before proceeding.

## Cost Optimization Tips

### Do
- Launch multiple EXPLORE subagents in parallel (e.g., search frontend and backend simultaneously)
- Use BUILD-SIMPLE for each independent file change, even in a large feature
- Break large features into small, independently-delegatable pieces
- Use Plan mode to think through architecture before coding

### Do Not
- Use the main agent to search for files (EXPLORE is much cheaper)
- Use BUILD-COMPLEX for config files, boilerplate, or simple edits
- Skip the task brief (it saves money long-term by preventing repeated context building)
- Use AUTO model selection (tends to pick poorly; explicit routing is more reliable)

## Quick Reference: Subagent Prompt Template

When delegating BUILD-SIMPLE work, use this structure:

```
You are implementing [feature/change] in [project type: Docker/Android/etc].

FILES TO READ FIRST:
- [path1] - understand [what]
- [path2] - this is where you will make changes

TASK:
[Specific, concrete description of what to do]

PATTERNS TO FOLLOW:
[Paste relevant code examples from the codebase]

CONSTRAINTS:
- [List any rules]
- [Do not change X]
- [Must be compatible with Y]

EXPECTED RESULT:
[What the output should look like or do]
```

## Domain Notes

Currently optimized for:
- **Docker/containerized services** - compose files, Dockerfiles, service configs
- **Android (Kotlin/Java)** - fragments, layouts, Gradle, navigation

These can be updated as the project evolves.
