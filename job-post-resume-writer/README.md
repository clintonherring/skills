# Job post resume writer

Two agent skills that turn a job posting plus your own facts into a tailored CV (and cover letter) that reads like you wrote it and follows the five résumé rules for the AI era: readable by screening software, mapped to the posting without keyword stuffing, written from your own brain dump, backed by verified numbers, and proving the skills the posting leans on.

- **job-post-resume-writer** — onboarding (base CV → `facts.md`), job-posting workflow (match → draft → check → Markdown CV), `.docx`/`.pdf` on request.
- **my-voice** — builds a portable `voice.md` profile of how you write, from your own emails, posts and documents, and is reused by any writing task.

Nothing personal is stored in this repository. Your facts, voice profile and CVs live in a data folder you choose at install time.

## Quick start

```bash
git clone <this repo> && cd job-post-resume-writer
python3 install.py            # macOS / Linux
py install.py                 # Windows (or: python install.py)
```

The installer asks three things: which agent you use (Cursor, Claude Code, Claude Desktop, other), where your private data should live, and then checks dependencies. It copies the two skills to your agent's skills folder, creates the data folder from templates, and writes `~/.job-post-resume-writer/config.json`.

Then open your agent and say:

> set up my resume

The skill walks you through it: it asks for your current CV (a `.docx`, `.pdf`, `.txt`, or pasted text; or none, and it interviews you), extracts the facts into `facts.md`, shows them to you to correct in chat, asks for results and numbers per role, asks whether any portfolio links may be used, and then hands over to `my-voice` to collect three or more samples of your writing.

After that, paste a job posting and say:

> tailor my cv to this

You get `cv.md` and `cv-review.md` (the scorecard) in `<data>/applications/<date>-<company>-<role>/`. Ask for a `.docx` or `.pdf` if you need one.

## Requirements

| Need | Required for | Notes |
|------|--------------|-------|
| Python 3.8+ | everything | stdlib only; no pip packages needed |
| Node.js 18+ | `.docx` output | installer runs `npm install` for the `docx` package |
| LibreOffice (`soffice`) | `.pdf` output | optional; without it you export PDF from Word |
| `pdftotext` (poppler) or `pypdf` | reading a PDF base CV | optional; the agent falls back to pasted text |

Run `python3 install.py --check` at any time to see what is available.

## Install options

| Command | Effect |
|---------|--------|
| `python3 install.py` | interactive install |
| `python3 install.py --check` | dependency check only |
| `python3 install.py --upgrade` | re-copy the skills; never touches your data folder |
| `python3 install.py --uninstall` | remove the skills; keeps your data folder |
| `python3 install.py --ide cursor --data ~/ResumeData --yes` | non-interactive |

## Per-agent notes

- **Cursor**: skills go to `~/.cursor/skills/`. Scripts run in the agent terminal.
- **Claude Code**: skills go to `~/.claude/skills/`. Scripts run in the agent terminal.
- **Claude Desktop**: skills cannot run local scripts. The installer prints steps to upload the two `SKILL.md` folders as project knowledge; onboarding, matching and the Markdown CV work conversationally, the automated checker and `.docx`/`.pdf` builder do not. Paste the text of your CV instead of a file.
- **Other agents**: the installer prints the skill path; point your agent at `skills/job-post-resume-writer/SKILL.md` and `skills/my-voice/SKILL.md`.

## Where your data lives

```
~/.job-post-resume-writer/config.json    data_dir, ide, locale, dependency flags
<data_dir>/
├── facts.md                             your fact base (identity, roles, numbers, skills, links)
├── voice.md                             your voice profile (from my-voice)
└── applications/
    └── 2026-10-northwind-service-delivery-manager/
        ├── jd.md  match.md  cv.md  cv-review.md  cover-letter.md  cv.docx  cv.pdf
```

Back it up like any personal document. Delete it and the skill starts onboarding again.

## Verify the install

```bash
python3 skills/job-post-resume-writer/scripts/selftest.py
```

Runs the whole chain on the fictional persona in `examples/` (extract → match → check → docx/pdf where available).

## Layout of this repository

```
install.py  install.sh  install.ps1  config.example.json
skills/job-post-resume-writer/   SKILL.md  references/  templates/  scripts/
skills/my-voice/                 SKILL.md  templates/  scripts/
examples/                        Sam Example: resume, job posting, facts, voice, match, cv, review
```

## Licence

MIT. The five rules are condensed from publicly reported hiring research (summarised in `skills/job-post-resume-writer/references/ai-era-guidelines.md`).
