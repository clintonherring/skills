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
- [ ] Run `python3 scripts/memory_doctor.py` (expect OK / WARN only)
- [ ] Run `python3 scripts/memory_vault.py init && python3 scripts/memory_vault.py doctor`

## 2. Create NocoDB base **Agent Memory**

This cloud VM has no NocoDB MCP or tokens. Do one of:

**A. UI**

1. In your NocoDB workspace, create a base named `Agent Memory`.
2. Create tables `facts` and `decisions` with columns from `nocodb/tables.csv` (names must match exactly).
3. Create an API token with access to that base.
4. Note table IDs (from table URL or API).

**B. API bootstrap** (from a machine with credentials)

```bash
export NOCODB_BASE_URL='https://<host>/api/v2'
export NOCODB_TOKEN='...'
export NOCODB_BASE_ID='...'   # existing empty base id, or omit to print instructions
python3 scripts/nocodb_bootstrap.py
python3 scripts/nocodb_sync.py check
```

## 3. Wire env + MCP (desktop / Cloud Agent env)

```bash
export NOCODB_BASE_URL='https://<host>/api/v2'
export NOCODB_TOKEN='...'
export NOCODB_FACTS_TABLE='...'
export NOCODB_DECISIONS_TABLE='...'
```

Add an MCP server entry for the Agent Memory base (same pattern as OpenSAR / Tax in `opensar-nocodb`), named e.g. `NocoDB Base - Agent Memory`.

For Cloud Agents: put the four env vars in the Cursor environment secrets for an environment named **Agent Memory** (or this skills env), then start agents from that environment.

## 4. Verify compaction restore

1. Work until the context ring is high.
2. Let compaction run (watch for the user_message from `preCompact`).
3. On the next tool call, confirm a block headed **Restored project memory**.
4. If missing: `python3 scripts/memory_doctor.py`.

## 5. Copy kit to other working repos

Copy `.cursor/hooks.json`, `.cursor/hooks/`, `.cursor/rules/agent-memory.mdc`, `.cursor/skills/agent-memory/`, `memory/`, `memory.config.json`, the three scripts, and `nocodb/tables.csv`.
