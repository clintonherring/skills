# Agent memory setup checklist

## 1. In this repo (already on the PR branch)

- [x] `.cursor/hooks.json` + hook scripts
- [x] `.cursor/rules/agent-memory.mdc`
- [x] `.cursor/skills/agent-memory/SKILL.md`
- [x] `memory/NOW.md`, `facts.md`, `decisions.md`
- [x] `memory.config.json`
- [x] `scripts/memory_doctor.py`, `nocodb_sync.py`, `nocodb_bootstrap.py`, `memory_vault.py`
- [x] `nocodb/tables.csv` + `schemas/memory.schema.json`
- [x] ECC-adapted skills: unified-memory, strategic-compact, knowledge-ops, save/resume-session, session-lessons
- [x] Run `python3 scripts/memory_doctor.py` (expect OK / WARN only)
- [x] Run `python3 scripts/memory_vault.py init && python3 scripts/memory_vault.py doctor`

## 2. Create NocoDB base **Agent Memory**

- [x] Base `Agent Memory` (`pbvl82n18u5mtvr`) in workspace `wzrgpf7n`
- [x] Tables bootstrapped: `facts`=`mpj7s77tld5967c`, `decisions`=`mk6usl9kkjsimw2`
- [x] `python3 scripts/nocodb_sync.py check` — columns match `nocodb/tables.csv`
- [x] Seeded facts + decisions; local MCP entry in `~/.cursor/mcp.json`
- [x] Decisions auto-upsert: `afterFileEdit` on `memory/decisions.md` + `stop` retry; `push-decisions` is idempotent
- [x] NOW snapshot: Noco table `now` (`mn7hsjdbx0uiwh7`); `push-now` / `pull-now`; auto on `NOW.md` edit

## 3. Wire env + MCP (desktop / Cloud Agent env)

Local (done on this machine — User env + gitignored `.env.nocodb.local`):

```bash
export NOCODB_BASE_URL='https://ufm.remoteconsulting.eu/api/v2'
export NOCODB_TOKEN='...'   # API xc-token (not the MCP token)
export NOCODB_FACTS_TABLE='mpj7s77tld5967c'
export NOCODB_DECISIONS_TABLE='mk6usl9kkjsimw2'
export NOCODB_NOW_TABLE='mn7hsjdbx0uiwh7'   # also in memory.config.json as nocodb.now_table
```

Desktop MCP: `NocoDB Base - Agent Memory` via `mcp-remote` (already in `~/.cursor/mcp.json`).

- [x] Cloud Agents: `NOCODB_*` Runtime Secrets live (see PR #5); add `NOCODB_NOW_TABLE` if not reading `memory.config.json`
- Cloud session start (optional live intent): `python3 scripts/nocodb_sync.py pull-now`

## 4. Verify compaction restore

1. Work until the context ring is high.
2. Let compaction run (watch for the user_message from `preCompact`).
3. On the next tool call, confirm a block headed **Restored project memory**.
4. If missing: `python3 scripts/memory_doctor.py`.

## 5. Copy kit to other working repos

Copy `.cursor/hooks.json`, `.cursor/hooks/`, `.cursor/rules/agent-memory.mdc`, `.cursor/skills/agent-memory/`, `memory/`, `memory.config.json`, the three scripts, and `nocodb/tables.csv`.
