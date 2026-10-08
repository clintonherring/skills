# NOW

## Goal

Ship ECC-adapted memory skills + stdlib vault in `clintonherring/skills`, then wire NocoDB **Agent Memory** secrets/env for live sync.

## Active task

PR https://github.com/clintonherring/skills/pull/4 (`cursor/ecc-memory-skills-917e`) — open, ready to merge.

## Constraints

- Vault is `ecc.memory.v1` via `python3 scripts/memory_vault.py` (no npm required)
- Compaction survival still depends on hooks + `memory/NOW.md` reinjection
- This VM still has no `NOCODB_*` credentials

## Next action

1. Merge PR #4
2. Create NocoDB base **Agent Memory** + set `NOCODB_*` secrets on the Cloud env
3. `python3 scripts/nocodb_sync.py check` / optional `ecc-universal` MCP later
