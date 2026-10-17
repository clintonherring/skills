# Adapt clinton-voice from videos → skills

## Intent
The OpenSAR `clinton-voice` skill in `clintonherring/videos` is the updated how-he-writes skill, but framed for video/marketing (hooks, Room, captions). Bring the same register into this repo for career and professional prose.

## Done
- Added `skills/custom/clinton-voice` (SKILL + guide excerpts + abstract/overview)
- **Re-synced 2026-10-17:** first pass used a stale videos checkout (8d1ee16, 2026-10-10). Rebuilt from `videos` `origin/main` clinton-voice (P21 origin/pricing, no em dashes, cost-and-place not "trade-off", origin-excerpts.md).
- Stripped video pipeline; kept habits 0–15, slogan→sentence, hedged numbers, no-hype
- Added career word table alongside OpenSAR/origin table; copied `origin-excerpts.md`
- Wired `resume-writer` and `clinton-cv` to load it; refreshed CV `voice.md` quick reference
- Registered in `skills/registry.json` and `skills/custom/.overview.md`

## Not in scope
- Changing `job-post-resume-writer/skills/my-voice` (generic builder; business-voice in smma-videos is its marketing cousin)
- Porting video hooks / Rover / Room rules into this repo
