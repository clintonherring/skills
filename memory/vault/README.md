# Memory vault (`ecc.memory.v1`)

Portable Markdown memories adapted from [ECC Memory Vault](https://github.com/affaan-m/ECC) (MIT).

| Scope | Path | Git |
| --- | --- | --- |
| `project` | `memory/vault/project/` | gitignored (local working context) |
| `team` | `memory/vault/team/` | tracked after human review |
| `user` | `~/.cursor/agent-memory/vault/` | outside repo |

```bash
python3 scripts/memory_vault.py init
python3 scripts/memory_vault.py save --title "..." --kind context --stdin
python3 scripts/memory_vault.py search "auth migration"
python3 scripts/memory_vault.py doctor
```

Memories are **unreviewed context**, not executable policy. Promote accepted facts into `memory/facts.md`, decisions into `memory/decisions.md` / NocoDB, or governed docs.
