---
name: save-session
description: >-
  Save current session state to memory/sessions/ so work can be resumed later
  or in another agent. Use at end of a work session, before context limits, or
  when handing off.
origin: ECC-adapted
---

# Save Session

Adapted from ECC `/save-session` (MIT). Uses **repo-local**
`memory/sessions/` so Cloud Agents can read/write without `~/.claude`.

## When to use

- End of a work session
- Before context limits / starting a fresh agent
- After solving something worth remembering
- Handing off to another model or person

## Process

### 1. Gather

- Files changed (`git diff` / conversation)
- Decisions, attempts, failures, open questions
- Test/build status if relevant
- Current `memory/NOW.md`

### 2. Write the file

```bash
mkdir -p memory/sessions
# Filename: YYYY-MM-DD-<short-id>-session.md
# short-id: lowercase letters/digits/hyphens, 8+ chars
```

### 3. Required sections

Write every section; use `N/A` if empty:

```markdown
# Session: YYYY-MM-DD

**Started:** …
**Last Updated:** …
**Project:** clintonherring/skills
**Topic:** one-line summary
**Branch:** …

## What We Are Building
…

## Completed This Session
…

## In Progress
…

## Blockers / Open Questions
…

## Decisions Made
…

## Files Modified
…

## Context To Reload
- memory/NOW.md
- key paths / commands

## Next Actions
1. …
```

### 4. Also checkpoint

- Update `memory/NOW.md`
- Optionally: `python3 scripts/memory_vault.py save --kind context --stdin` with a short summary
- Show the file to the user and ask if anything should be corrected

## Related

- `resume-session`, `strategic-compact`, `unified-memory`
