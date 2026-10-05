# NOW

## Goal

Land the agent-memory kit in `clintonherring/skills` and wire a NocoDB base named **Agent Memory**.

## Active task

`tasks/agent-memory/` — hooks + sync + setup checklist on branch `cursor/agent-memory-kit-917e`.

## Constraints

- Hooks fail open; Python 3 stdlib only
- This VM has no NocoDB credentials — base creation is a local/UI follow-up
- Prefer repo files over Cursor Memories for Cloud Agents

## Next action

- Merge PR; create NocoDB **Agent Memory** base; set `NOCODB_*` env; run `nocodb_sync.py check`
