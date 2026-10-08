# ECC memory skills port

## Source

[affaan-m/ECC](https://github.com/affaan-m/ECC) (MIT) — README + skills:
`unified-memory`, `strategic-compact`, `knowledge-ops`, `save-session`, `resume-session`.

## Approach

- Adapt skills for Cursor + this repo’s existing `memory/` + hooks kit.
- Add a **stdlib Python** vault (`scripts/memory_vault.py`) compatible with `ecc.memory.v1` Markdown documents — no npm/`ecc-universal` required for Cloud Agents.
- Optional later: install `ecc-universal` if you want the official CLI/MCP; point it at the same vault root via config.
- Skip continuous-learning-v2 observer daemon (ECC runtime-heavy); ship a thin `session-lessons` skill instead.

## Status

Implementing on `cursor/ecc-memory-skills-917e`.
