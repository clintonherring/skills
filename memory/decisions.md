# Recent decisions

<!-- Newest first. Push durable rows to NocoDB Agent Memory → decisions table. -->

| Date | Decision | Rationale |
| --- | --- | --- |
| 2026-11-10 | All memory goes to the NocoDB Agent Memory DB; never install or keep the older NOW.md-only kit | Clinton's memory lives in the DB; a repo that only writes NOW.md silently drops state for Cloud and other machines |
| 2026-11-06 | Install the memory kit into `opensarcompanion` and `pocketatc` by copying from this repo | App repos need compaction survival too; this repo stays the source of truth for the kit |
| 2026-10-16 | `resume-writer` skill owns the canonical CV fact base and JD workflow; `clinton-cv` keeps the Rituals notes and original extract | One fact file to correct; AI-era rules (ATS layout, map-not-stuff, brain-dump bullets, verified numbers, proven AI) apply to every application |
| 2026-10-08 | Snapshot `memory/NOW.md` to Noco `now` table on edit (pull-now for Cloud) | Lets Cloud read live intent without merging every session; still checkpoint via git for branch history |
| 2026-10-08 | Global ECC in Cursor via junctions + always-on `ecc-way-of-working`; Ultra default model = Auto (Cost) | Intentional ECC workflow across all projects; Auto Cost beats pinning frontier models on Ultra |
| 2026-10-08 | Treat NocoDB Agent Memory as live on this Cloud env | `nocodb_sync.py check` + doctor both pass with all `NOCODB_*` vars set |
| 2026-10-08 | Port ECC memory skills via stdlib Python vault, not full `ecc-universal` | Cloud Agents need repo-local tooling; optional npm later for official MCP |
| 2026-09-23 | Use repo files + hooks for compaction survival | Cursor Memories is per-user/app-scoped and unreachable to Cloud Agents |
