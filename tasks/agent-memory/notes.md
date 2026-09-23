# Agent memory kit — setup notes

## Goal

Ship a repo-backed agent memory system in `clintonherring/skills` so key facts survive context compaction and model switches. Wire NocoDB as durable storage for facts/decisions under a base named **Agent Memory**.

## Constraints (this cloud run)

- Working tree is already `github.com/clintonherring/skills`.
- No NocoDB MCP servers or `NOCODB_*` credentials are configured in this VM — cannot create the live base from here.
- Kit must use Python 3 stdlib only; hooks fail open.

## Plan

1. Install project hooks + rule + skill + `memory/` stubs at repo root.
2. Add `scripts/memory_doctor.py`, `scripts/nocodb_sync.py`, `scripts/nocodb_bootstrap.py`.
3. Document NocoDB tables in `nocodb/tables.csv`; extend `opensar-nocodb` routing for Agent Memory.
4. Tests that drive hooks as subprocesses (no network).
5. PR + checklist for creating the NocoDB base and Cursor Cloud env locally.

## Status

In progress on branch `cursor/agent-memory-kit-917e`.
