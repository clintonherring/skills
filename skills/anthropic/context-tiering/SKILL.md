---
name: context-tiering
description: >
  Tiered context management system for projects. Reduces token consumption
  by organizing project knowledge into L0 (abstract), L1 (overview), and L2
  (full content) tiers stored in a per-project .context/ directory. Includes
  continuous state tracking via current_task.md and current_spec.md for
  persistent session memory. Use this skill proactively at the start of every
  session when exploring unfamiliar code, when the project has a .context/
  directory, when asked to "index", "summarize", or "map" a project, when
  context or token usage is a concern, or when the user mentions "tiering",
  "L0/L1/L2", or "context management".
---

# Context Tiering

Manage project knowledge using a three-tier filesystem hierarchy that
mirrors how a human expert approaches a codebase: scan titles first, read
summaries if relevant, then dive into source only when necessary.

State tracking files provide persistent memory across sessions.

## Per-Project Scoping

Context is managed per project folder, NOT per workspace. Each project that
has been indexed maintains its own `.context/` directory independently.
When work spans multiple project folders, update state files in EACH
project's `.context/` separately.

## Directory Structure

```
project-root/
  .context/
    current_task.md       # Living work-state ledger (this project only)
    current_spec.md       # Feature spec and test tracker (this project only)
    _root.l0.md           # L0: one-sentence project abstract
    _root.l1.md           # L1: project overview (structure, tech, entry points)
    src/
      _dir.l0.md          # L0: what this directory is about
      _dir.l1.md          # L1: directory overview (key files, relationships)
      auth/
        _dir.l0.md
        _dir.l1.md
        login.l0.md       # L0: what login.ts does
        login.l1.md       # L1: login.ts exports, dependencies, key logic
    backend/
      _dir.l0.md
      _dir.l1.md
      app.l0.md
      app.l1.md
```

L2 is always the original source file itself - never duplicated.

## Tier Definitions

### L0 - Abstract (~1-2 sentences, <100 tokens)
Purpose: decide whether to look deeper. Contains ONLY what the file/dir IS.

Format for files:
```
[filename] - [what it does in one sentence]. Key exports: [top 3 exports].
```

Format for directories:
```
[dirname/] - [what this directory contains/manages in one sentence]. [count] files.
```

### L1 - Overview (~10-30 lines, <500 tokens)
Purpose: understand structure and decide which L2 to read.

Format:
```markdown
# [name]

## Purpose
[2-3 sentences on what and why]

## Key Exports / Entry Points
- `functionName(args)` - what it does
- `ClassName` - what it represents

## Dependencies
- [key imports and what they provide]

## Relationships
- Called by: [callers]
- Calls: [callees]
```

### L2 - Full Content (original source)
Read the actual file only after L0 and L1 confirm relevance.

## Indexing Gate

Before working in any project folder, the agent MUST check for `.context/`
at the project root:

1. **`.context/` exists with `_root.l0.md`** - Project is indexed. Read state
   files and proceed.
2. **`.context/` does NOT exist** - Prompt the user:
   *"This project folder has not been indexed yet. Would you like me to index
   `[folder name]` before proceeding? Indexing creates `.context/` with L0/L1
   summaries and state tracking files."*
3. **Working in a subfolder whose parent project root lacks `.context/`** -
   Prompt: *"The parent project `[parent folder]` has not been indexed. Would
   you like me to index it first?"*

The agent must NOT create state files in an unindexed project. Indexing is
a prerequisite.

## State Tracking Files

Two living documents in each project's `.context/` provide persistent memory
across sessions. They are always read FIRST (before L0/L1 tiers) and updated
continuously during work.

### current_task.md - Work State Ledger

Tracks what the agent is doing and has done in THIS project.

```markdown
# Current Task State

## Active Task
- **Task**: [short description]
- **Status**: in_progress | blocked | awaiting_user
- **Started**: [date]
- **Files touched**: [list]
- **Plan summary**: [2-3 sentences]

## Completed Tasks (newest first)
### [date] - [task title]
- **What**: [description]
- **Files changed**: [list]
- **Test result**: passed | failed | skipped
- **Committed**: yes/no (commit hash if yes)
- **Pushed**: yes/no (branch if yes)

## Pending / Next Steps
- [bullet list of upcoming work]
```

### current_spec.md - Feature Specification Tracker

Tracks specifications and requirements for the current feature/phase in
THIS project.

```markdown
# Current Specification

## Active Feature
- **Feature**: [name]
- **Version**: [app version]
- **Branch**: [git branch]

## Requirements
- [ ] Requirement 1
- [x] Requirement 2 (completed)

## Architecture Decisions
- [key decisions made during implementation]

## Test Matrix
| Test | Status | Date | Notes |
|------|--------|------|-------|
| [test name] | passed/failed | [date] | [notes] |

## Release Checklist
- [ ] All tests passing
- [ ] Code committed (hash: ...)
- [ ] Pushed to remote
- [ ] Version bumped
```

## State Update Triggers

The agent MUST update state files for the project it is currently working in
at these moments:

1. **Session start**: Identify which project folder(s) the work targets. For
   each, check `.context/` exists (prompt to index if not). Read
   `current_task.md` and `current_spec.md` before any L0/L1. Create them from
   the templates above if indexed but state files are missing.
2. **Task begins**: Update `current_task.md` Active Task section.
3. **Plan created**: Write plan summary to `current_task.md`.
4. **Files edited**: Append to the "Files touched" list.
5. **Test run**: Update `current_spec.md` Test Matrix with result and date.
6. **Successful test**: Mark test as passed, add notes about what was verified.
7. **Commit made**: Record commit hash and message in `current_task.md`, move
   task from Active to Completed.
8. **Push made**: Record push status and branch in both files.
9. **Task completed**: Move from Active to Completed, update spec checklist.
10. **Session end / user leaves**: Ensure both files reflect final state.

## Workflow

### Indexing a Project

When asked to index/map/summarize a project or when `.context/` does not exist:

1. Read the project's top-level files (package.json, build.gradle, docker-compose, etc.)
2. Create `.context/_root.l0.md` and `.context/_root.l1.md`
3. Create `.context/current_task.md` and `.context/current_spec.md` from templates
4. Walk each significant directory (skip node_modules, .git, build, dist, __pycache__, .gradle)
5. For each directory: create `_dir.l0.md` and `_dir.l1.md`
6. For each significant source file: create `[filename].l0.md` and `[filename].l1.md`
7. Use the `scripts/generate_tiers.py` helper when batch-generating

Prioritize files that are:
- Entry points (main, index, app, server)
- Configuration (docker-compose, package.json, build.gradle)
- Core business logic
- API routes / controllers
- Models / schemas

Skip generating tiers for:
- Test files (generate on demand)
- Generated/compiled files
- Assets (images, fonts)
- Lock files

### Reading Context (Every Session)

Follow this protocol when starting work in a project with `.context/`:

1. **Read state files first**: Read `current_task.md` and `current_spec.md` to
   restore session memory (~200 tokens total). This tells you what was being
   worked on, what's completed, and what's next.
2. **Start with L0**: Read `_root.l0.md` to understand the project (~10 tokens)
3. **Scan directory L0s**: Read `_dir.l0.md` files to find relevant areas (~50 tokens total)
4. **Read relevant L1s**: For directories that matter, read `_dir.l1.md` (~200 tokens each)
5. **Read file L1s**: For files that seem relevant, read `[file].l1.md` (~300 tokens each)
6. **Read L2 only when needed**: Open the actual source file only when you must
   edit it or need exact implementation details

This typically reduces context loading from 50k+ tokens to under 3k tokens
for initial orientation.

### Updating Tiers

After modifying a source file:
1. Check if `.context/[filename].l1.md` exists
2. If yes, update the L0 and L1 to reflect changes
3. If directory structure changed, update parent `_dir.l0.md` and `_dir.l1.md`

## Rules

### Tier Rules
- Never put L2 content into L0 or L1 files (no code blocks in L0, minimal in L1)
- L0 must fit in a single line of text
- L1 must stay under 30 lines
- Always prefer reading L0 before L1 before L2
- When multiple files need context, batch-read all L0s first, then select L1s
- Generate tiers lazily: create them when first needed, not speculatively for every file
- The `.context/` directory mirrors the source tree structure

### State Tracking Rules
- State files are per-project, never shared across folders
- Agent must check for `.context/` before creating state files
- Agent must prompt user to index if `.context/` is missing
- `current_task.md` and `current_spec.md` are always read at session start
- State files are updated inline during work, not deferred
- Completed tasks are never deleted, only moved to history
- Test results always include date and pass/fail status
- Commit/push events are always recorded with hash/branch

## Helper Script

Run `scripts/generate_tiers.py` to batch-generate tiers for a directory.
See [references/examples.md](references/examples.md) for real L0/L1 examples.
