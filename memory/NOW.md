# NOW

## Goal

Keep the ECC memory kit healthy (hooks + vault + live NocoDB Agent Memory) and the custom skills (resume-writer, clinton-voice, job-post-resume-writer) current, using ECC intentionally across Cursor with Auto (Cost) on Ultra.

## Active task

- Memory auto-sync is on `main`: decisions auto-upsert, `memory/NOW.md` snapshots to the NocoDB `now` table on edit; Cloud can `pull-now` at session start. Facts stay pull-owned by Noco.
- Kit installed into `opensarcompanion` and `pocketatc` (2026-11-06); keep their copies in sync when hooks/scripts change here.
- `clinton-voice` synced from videos `@49248b5` (PR #9/#10 merged).

## Constraints

- Vault is `ecc.memory.v1` via `python3 scripts/memory_vault.py` (no npm required)
- `NOCODB_*` set on Cloud + desktop; `nocodb.now_table` = `mn7hsjdbx0uiwh7`
- Never commit `.env.nocodb.local`
- Desktop `python3` = real Python 3.12 (Store alias removed 2026-11-06)
- Prefer Auto (Cost) on Ultra

## Next action

1. Cloud Agents: add Runtime Secret `NOCODB_NOW_TABLE=mn7hsjdbx0uiwh7` (or rely on config)
2. Cloud session start: `python3 scripts/nocodb_sync.py pull-now`
3. Optional: wire `ecc-universal` MCP later
