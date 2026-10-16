# Recent decisions

<!-- Newest first. Push durable rows to NocoDB Agent Memory → decisions table. -->

| Date | Decision | Rationale |
| --- | --- | --- |
| 2026-10-16 | `resume-writer` skill owns the canonical CV fact base and JD workflow; `clinton-cv` keeps the Rituals notes and original extract | One fact file to correct; AI-era rules (ATS layout, map-not-stuff, brain-dump bullets, verified numbers, proven AI) apply to every application |
| 2026-10-08 | Treat NocoDB Agent Memory as live on this Cloud env | `nocodb_sync.py check` + doctor both pass with all `NOCODB_*` vars set |
| 2026-10-08 | Port ECC memory skills via stdlib Python vault, not full `ecc-universal` | Cloud Agents need repo-local tooling; optional npm later for official MCP |
| 2026-09-23 | Use repo files + hooks for compaction survival | Cursor Memories is per-user/app-scoped and unreachable to Cloud Agents |
