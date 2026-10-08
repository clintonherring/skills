---
name: strategic-compact
description: >-
  Suggests checkpointing and context compaction at logical task boundaries
  rather than mid-task auto-compaction. Use when a session approaches context
  limits, after a milestone, or before switching unrelated work.
origin: ECC-adapted
---

# Strategic Compact

Adapted from [affaan-m/ECC](https://github.com/affaan-m/ECC) `strategic-compact` (MIT).
Cursor Cloud Agents do not expose Claude’s `/compact` the same way — the durable
action here is **write state to disk**, then let compaction run safely because
this repo’s hooks reinject `memory/NOW.md` (+ vault/task state).

## When to activate

- Long sessions approaching high context usage
- Multi-phase work (research → plan → implement → test)
- Switching unrelated tasks in the same session
- After a major milestone before starting new work
- Responses feel less coherent (context pressure)

## Decision guide

| Phase transition | Checkpoint + allow compact? | Why |
| --- | --- | --- |
| Research → Planning | Yes | Research is bulky; keep the distilled plan |
| Planning → Implementation | Yes | Plan must be on disk first |
| Implementation → Testing | Maybe | Keep if tests need recent code context |
| Debugging → Next feature | Yes | Debug traces pollute unrelated work |
| Mid-implementation | No | Losing paths/partial state is costly |
| After a failed approach | Yes | Clear dead-end reasoning |

## Before compaction (required)

1. Update `memory/NOW.md` (goal, constraints, next action)
2. If work is large, write `tasks/<slug>/state.md` and put the slug in `tasks/ACTIVE`
3. Promote durable items to `memory/facts.md` / `memory/decisions.md`
4. Optionally save a vault entry or session file:

```bash
printf '%s\n' '...' | python3 scripts/memory_vault.py save --title "Checkpoint" --kind context --stdin
# and/or follow the save-session skill → memory/sessions/
```

## What survives vs what is lost

| Persists (if written to disk) | Lost on compact |
| --- | --- |
| `memory/NOW.md`, facts, decisions | Intermediate reasoning |
| Vault entries / session files | Nuanced verbal preferences not filed |
| Git state | Unsaved tool-call history |
| Hooks reinject **Restored project memory** | Raw file contents previously read into chat |

Do **not** rely on in-chat todos alone — write the plan to a file.

## Best practices

1. Compact (or start a fresh agent) **after** the plan is on disk
2. Compact after debugging before unrelated features
3. Never compact mid-implementation without a NOW/task checkpoint
4. Prefer a short custom summary in NOW over hoping the auto-summary is enough

## Related

- `.cursor/hooks.json` — `preCompact` → `postToolUse` reinjection
- `unified-memory`, `save-session`, `agent-memory`
