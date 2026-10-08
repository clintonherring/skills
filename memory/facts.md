# Durable facts

<!-- Long-lived project truths. Synced from NocoDB Agent Memory → facts table. -->

| Key | Value | Updated |
| --- | --- | --- |
| project | clintonherring/skills | 2026-09-23 |
| memory_base | Agent Memory (NocoDB) — tables `facts` / `decisions` per `nocodb/tables.csv` | 2026-09-23 |
| memory_kit | Repo files + hooks: `memory/NOW.md`, facts, decisions; `.cursor/hooks.json` reinjects after compact | 2026-10-08 |
| memory_vault | `scripts/memory_vault.py` + `memory/vault/` (`ecc.memory.v1`); project scope gitignored | 2026-10-08 |
| ecc_source | Memory skills adapted from affaan-m/ECC (MIT); not full `ecc-universal` runtime | 2026-10-08 |
| ecc_memory_pr | https://github.com/clintonherring/skills/pull/4 (merged) | 2026-10-08 |
| memory_skills | agent-memory, unified-memory, strategic-compact, knowledge-ops, save-session, resume-session, session-lessons | 2026-10-08 |
| nocodb_env | Cloud env has NOCODB_BASE_URL, NOCODB_TOKEN, NOCODB_FACTS_TABLE, NOCODB_DECISIONS_TABLE; `nocodb_sync.py check` matches contract | 2026-10-08 |
