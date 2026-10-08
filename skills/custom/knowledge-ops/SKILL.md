---
name: knowledge-ops
description: >-
  Route knowledge into the right storage layer (NOW/facts/decisions, vault,
  NocoDB Agent Memory, GitHub). Use when saving, organizing, syncing,
  deduplicating, or searching across memory systems.
origin: ECC-adapted
---

# Knowledge Operations

Adapted from [affaan-m/ECC](https://github.com/affaan-m/ECC) `knowledge-ops` (MIT),
mapped onto this skills repo’s stack.

## When to activate

- “Save this”, “what do we know about X”, “sync memory”, “ingest this”
- Choosing where a fact/decision/handoff should live
- Deduplicating notes across layers

## Layers (this repo)

| Layer | Store | Use for |
| --- | --- | --- |
| 1 Active execution | GitHub issues/PRs | Live engineering truth |
| 2 Session intent | `memory/NOW.md`, `tasks/*/state.md` | Current goal (≤80 lines) |
| 3 Durable project | `memory/facts.md`, `memory/decisions.md` | Reviewed truths / choices |
| 4 Portable vault | `memory/vault/` via `memory_vault.py` | Handoffs, lessons, cross-agent context (`ecc.memory.v1`) |
| 5 Shared DB | NocoDB **Agent Memory** (`nocodb_sync.py`) | Cross-machine facts/decisions |
| 6 OpenSAR / Tax | `opensar-nocodb` MCP | Domain ops data — not agent memory |

## Ingestion workflow

### 1. Classify

- Active roadmap / release state → GitHub first
- Current session goal → `memory/NOW.md`
- Verified durable fact → `memory/facts.md` (+ optional NocoDB pull/push)
- Decision → prepend `memory/decisions.md`
- Cross-agent handoff / lesson → vault (`kind: handoff|lesson`)
- Large doc → link from vault/note; don’t paste secrets

### 2. Deduplicate

```bash
python3 scripts/memory_vault.py search "<terms>"
rg -n "<terms>" memory/
python3 scripts/nocodb_sync.py pull-facts   # if NOCODB_* set
```

Update existing rows/files; don’t create parallel copies.

### 3. Store + promote

Verified vault entries → promote into facts/decisions (and NocoDB).
Unreviewed vault entries stay `trust: unreviewed`.

## Quality gate

- No duplicate canonical homes for the same fact
- Secrets redacted from anything Git-tracked
- NOW stays short; overflow in `tasks/<slug>/state.md`
- Ambiguous “memory” requests: ask whether they mean vault, NOW, or NocoDB

## Related

- `unified-memory`, `agent-memory`, `opensar-nocodb`, `save-session`
