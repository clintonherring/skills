---
name: resume-session
description: >-
  Load the most recent memory/sessions/*-session.md and orient fully before
  doing new work. Use when continuing prior work or after compaction/fresh agent.
origin: ECC-adapted
---

# Resume Session

Counterpart to `save-session`. Adapted from ECC `/resume-session` (MIT).

## When to use

- Starting a new agent to continue prior work
- After compaction or a fresh session due to context limits
- User provides an explicit session file path

## Process

### 1. Find the file

If no path given:

1. List `memory/sessions/*-session.md`
2. Prefer newest non-empty file with real content (reject placeholders only)
3. If none: tell the user to run `save-session` next time; stop

If a date `YYYY-MM-DD` is given: pick the best file for that date.
If a path is given: read **exactly** that file.

### 2. Orient (before coding)

Read the session file **and**:

- `memory/NOW.md`
- `memory/facts.md` / `memory/decisions.md` if referenced
- `python3 scripts/memory_vault.py search` for the topic if useful
- `git status` / current branch

### 3. Confirm with the user

Summarize in a few bullets: topic, last next-actions, blockers. Ask whether to
continue with the listed next action or change course. **Do not** start large
implementation until confirmed (unless the user already ordered a specific task).

### 4. Update NOW

Rewrite `memory/NOW.md` to match the resumed goal and next action.

## Related

- `save-session`, `unified-memory`, `agent-memory`
