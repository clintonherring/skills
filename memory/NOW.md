# NOW

## Goal

Keep ECC memory kit healthy: hooks + vault + live NocoDB **Agent Memory** sync.

## Active task

Memory smoke verified on this VM (`nocodb_sync.py check` + `memory_doctor.py` both OK). PR #4 merged.

## Constraints

- Vault is `ecc.memory.v1` via `python3 scripts/memory_vault.py` (no npm required)
- Compaction survival still depends on hooks + `memory/NOW.md` reinjection
- `NOCODB_*` env vars are set; live facts/decisions tables match `nocodb/tables.csv`

## Next action

1. Optional: `python3 scripts/nocodb_sync.py pull-facts` / `push-decisions` when facts or decisions change
2. Optional: wire `ecc-universal` MCP later
3. Clear `/workspace/.cursor/memory-state` warn flag if it keeps nagging
