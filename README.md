# skills

Personal and team Cursor skills, plus an **agent memory kit** at the repo root.

## Agent memory

Survives context compaction and model switches via repo files + hooks (not Cursor Memories).
Memory workflow skills are adapted from [ECC](https://github.com/affaan-m/ECC) (MIT).

| Piece | Path |
| --- | --- |
| Always-on rule | `.cursor/rules/agent-memory.mdc` |
| Procedure skill | `.cursor/skills/agent-memory/SKILL.md` |
| Hooks | `.cursor/hooks.json` |
| Working memory | `memory/NOW.md`, `facts.md`, `decisions.md` |
| Vault (`ecc.memory.v1`) | `memory/vault/` + `python3 scripts/memory_vault.py` |
| Sessions | `memory/sessions/` |
| Setup checklist | `tasks/setup.md` |
| Doctor | `python3 scripts/memory_doctor.py` |
| NocoDB sync | `python3 scripts/nocodb_sync.py` |
| Table contract | `nocodb/tables.csv` |

### ECC-adapted catalog skills

| Skill | Purpose |
| --- | --- |
| `unified-memory` | Portable vault save/search/handoff |
| `strategic-compact` | Checkpoint before compaction |
| `knowledge-ops` | Route knowledge to the right layer |
| `save-session` / `resume-session` | Session handoff files |
| `session-lessons` | Extract lessons without ECC daemons |

Create a NocoDB base named **Agent Memory**, then follow `tasks/setup.md`.

## Skill catalog

See `skills/` (`custom/`, `cursor/`, `jet/`, `anthropic/`). Registry: `skills/registry.json`.
