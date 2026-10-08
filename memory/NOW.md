# NOW

## Goal

Port ECC memory-related skills into `clintonherring/skills` and wire a lightweight `ecc.memory.v1` vault that works without npm.

## Active task

`tasks/ecc-memory-skills/` on branch `cursor/ecc-memory-skills-917e`.

## Constraints

- Adapt ECC (MIT); do not require `ecc-universal` for Cloud Agents
- Keep existing NOW/facts/hooks/NocoDB kit as the compaction substrate
- Vault entries stay `trust: unreviewed` until promoted

## Next action

- Finish tests, commit, open PR; then optionally install `ecc-universal` locally if you want official MCP
