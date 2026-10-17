# NOW

## Goal

Add `clinton-voice` to skills (professional prose), adapted from the OpenSAR video voice skill.

## Active task

Re-synced `clinton-voice` from videos `origin/main` `@49248b5` (P21 origin excerpts, no em dashes). Branch `cursor/clinton-voice-skill-0fbd`; PR #9.

## Constraints

- Vault is `ecc.memory.v1` via `python3 scripts/memory_vault.py` (no npm required)
- Compaction survival still depends on hooks + `memory/NOW.md` reinjection
- `NOCODB_*` env vars are set; live facts/decisions tables match `nocodb/tables.csv`

## Next action

1. Optional: `python3 scripts/nocodb_sync.py pull-facts` / `push-decisions` when facts or decisions change
2. Optional: wire `ecc-universal` MCP later
3. Clear `/workspace/.cursor/memory-state` warn flag if it keeps nagging
