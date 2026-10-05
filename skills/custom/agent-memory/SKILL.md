---
name: agent-memory
description: >-
  Maintain and sync project agent memory (NOW.md, facts, decisions) so intent
  survives context compaction and model switches. Use when updating memory,
  after compaction, diagnosing memory hooks, or syncing with NocoDB Agent Memory.
---

# Agent memory (catalog)

Canonical installable skill + kit lives at the repo root:

- Project skill: `.cursor/skills/agent-memory/SKILL.md`
- Hooks / rule / memory files / scripts: see [tasks/setup.md](../../../tasks/setup.md)

Agents working in this skills repository should follow the project skill path above.
When copying the kit into another repo, copy the root `.cursor/`, `memory/`, `memory.config.json`, `scripts/`, and `nocodb/` pieces listed in setup.
