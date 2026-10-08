---
name: session-lessons
description: >-
  Extract reusable lessons from the current session into the memory vault and
  decisions log without requiring ECC continuous-learning daemons. Use at
  session end or after a hard-won fix.
origin: ECC-adapted
---

# Session Lessons

Lightweight substitute for ECC `continuous-learning-v2` (observer daemon not
ported). Manually distill patterns the team should remember.

## When to use

- End of a session with a non-obvious fix, workaround, or correction
- User says “remember this pattern” / “extract lessons”
- After production incident or long debugging arc

## Process

1. List 1–5 lessons (skip typos and one-off noise)
2. For each lesson, write a vault entry:

```bash
printf '%s\n' '## Lesson
...
## When it applies
...
## Evidence
...' | python3 scripts/memory_vault.py save \
  --title "Lesson: <short name>" \
  --kind lesson \
  --tag lesson \
  --stdin
```

3. If it is a durable project choice, prepend `memory/decisions.md`
4. If it is a standing truth, add `memory/facts.md`
5. Do **not** auto-write new skills unless the user asks

## Related

- `unified-memory`, `knowledge-ops`, `save-session`
