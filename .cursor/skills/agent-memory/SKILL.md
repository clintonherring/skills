---
name: agent-memory
description: >-
  Maintain and sync project agent memory (NOW.md, facts, decisions) so intent
  survives context compaction and model switches. Use when updating memory,
  after compaction, diagnosing memory hooks, or syncing with NocoDB Agent Memory.
---

# Agent memory

## Layers

| Layer | Role | Cost |
| --- | --- | --- |
| Rule `.cursor/rules/agent-memory.mdc` | Tiny always-on reflex | Every turn |
| This skill | Procedure: when/what to write, promote, sync | On demand |
| Hooks in `.cursor/hooks.json` | Enforcement: restore after compact, checkpoint nag | Automatic |

A skill alone is not enough. Hooks reinject memory after compaction:

```
preCompact  → write per-conversation needs_restore flag
              (compaction runs; transcript becomes a summary)
postToolUse → see flag → inject NOW + task state + facts + decisions
              (budget ~3000 tokens, NOW first) → clear flag
```

`preCompact` can only return `user_message` (not model context). That is why restore happens on `postToolUse` / `postToolUseFailure`.

## Files

| Path | Purpose |
| --- | --- |
| `memory/NOW.md` | Current goal, constraints, next action (≤ ~80 lines) |
| `memory/facts.md` | Durable project truths |
| `memory/decisions.md` | Recent decisions, newest first |
| `memory/vault/` | Portable `ecc.memory.v1` entries (`scripts/memory_vault.py`) |
| `memory/sessions/` | Save/resume session handoff files |
| `tasks/ACTIVE` | Optional one-line slug |
| `tasks/<slug>/state.md` | Overflow task state |
| `memory.config.json` | Budgets + NocoDB env var names |

## When to write

1. **Goal shift** → rewrite `memory/NOW.md`.
2. **Durable discovery** → add a row to `memory/facts.md`.
3. **Choice made** → prepend to `memory/decisions.md`.
4. **Cross-agent handoff / lesson** → `python3 scripts/memory_vault.py save|handoff` (see `unified-memory`).
5. **End of session** → `save-session` skill + NOW checkpoint (stop-hook may remind once).
6. **Before phase change** → `strategic-compact` (write to disk first).

## Companion skills (ECC-adapted)

| Skill | Role |
| --- | --- |
| `unified-memory` | Vault save/search/read/handoff |
| `strategic-compact` | When to checkpoint before compaction |
| `knowledge-ops` | Which layer to store knowledge in |
| `save-session` / `resume-session` | Session files under `memory/sessions/` |
| `session-lessons` | Distill lessons without ECC learning daemons |

## NocoDB (Agent Memory base)

One-way each direction — do not bidirectional-merge:

- **Pull facts:** NocoDB `facts` → regenerate `memory/facts.md` cache  
  `python3 scripts/nocodb_sync.py pull-facts`
- **Push decisions:** `memory/decisions.md` rows → NocoDB `decisions`  
  `python3 scripts/nocodb_sync.py push-decisions`
- **Schema check:** `python3 scripts/nocodb_sync.py check`  
  NocoDB silently accepts unknown column names on write (HTTP 200, blank fields).

Env vars (see `memory.config.json`):

- `NOCODB_BASE_URL` — API base, e.g. `https://app.nocodb.com/api/v2`
- `NOCODB_TOKEN` — XC token
- `NOCODB_FACTS_TABLE` — table id for facts
- `NOCODB_DECISIONS_TABLE` — table id for decisions

Create the base once with `python3 scripts/nocodb_bootstrap.py` (needs URL + token + base id) or via the NocoDB UI using `nocodb/tables.csv`.

## Diagnose

```bash
python3 scripts/memory_doctor.py
```

Hooks fail open by design; doctor reports missing config, flags, and script errors.

## Install into another repo

Copy `.cursor/hooks.json`, `.cursor/hooks/`, `.cursor/rules/agent-memory.mdc`, `.cursor/skills/agent-memory/`, `memory/`, `memory.config.json`, `scripts/memory_doctor.py`, `scripts/memory_vault.py`, `scripts/nocodb_sync.py`, `scripts/nocodb_bootstrap.py`, `schemas/memory.schema.json`, and `nocodb/tables.csv`. Then run `memory_doctor.py` and `memory_vault.py init`.
