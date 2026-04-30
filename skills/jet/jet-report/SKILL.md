---
name: jet-report
description: >
  Generate professional PDF reports at JET with correct JET branding (JET Orange,
  Inter font, Mozzarella backgrounds, bookend pages). Use this skill for ANY of
  these requests: "make this a PDF", "turn this into a report", "create a PDF",
  "JET branded report", "JET report", "PDF document", "weekly report", "executive
  summary", "incident report", "PI report", "adoption report", "reliability report",
  "data snapshot", or any request to produce a formatted output document. This skill
  MUST be loaded before writing any PDF generation code — without it the output will
  not be JET branded. Generates PDFs programmatically using fpdf2 in Python with the
  full JET design system (Inter font family, colour palette, layout patterns).
metadata:
  owner: ai-platform
---

# JET Report Generator

Generate polished, professional PDF reports using fpdf2 in Python. This skill provides the design system, layout conventions, communication principles, and ready-to-use code patterns for producing branded reports at JET. Supports all report types: executive summaries, adoption reports, weekly summaries, incident reviews, data snapshots, and more.

> **MANDATORY — Load this skill before writing any PDF code.** Every PDF report at JET must use the `ReportPDF` subclass, Inter font family, JET colour palette, and bookend pages defined in this skill. Generating PDF code without loading this skill first will produce an unbranded output that does not meet JET visual identity standards. If you have already started writing PDF code without loading this skill, stop and reload it now.

> **fpdf2 version**: All patterns require fpdf2 >= 2.8.0. Verified on v2.8.7.

## Prerequisites

Before generating any report, verify that fpdf2 is installed. If not, install it automatically:

**macOS/Linux:**
```bash
python3 -c "from fpdf import FPDF; print('fpdf2 OK')" 2>/dev/null || pip3 install fpdf2
```

**Windows:** Install [Python for Windows](https://www.python.org/downloads/windows/) if not already present, then:
```powershell
py -c "from fpdf import FPDF; print('fpdf2 OK')" 2>$null; if ($LASTEXITCODE -ne 0) { pip install fpdf2 }
```

## Before You Start

Infer the following from the user's request and available context. **Do not ask** unless genuinely ambiguous:

1. **Report title** — derive from the topic/request
2. **Date range or period** — use the most recent period, or today's date if unspecified
3. **Output path** — always save to `reports/` subdirectory in the current working directory (create it if needed). Print the absolute path after generating. Never ask where to save.
4. **Data source** — use whatever data the user has provided or referenced in the conversation

Only ask clarifying questions when the request is genuinely ambiguous and you cannot make a reasonable inference.

## Script & PDF Reuse

Before generating a new report script from scratch, **always check for existing scripts and PDFs** in the `reports/` directory. Reusing a proven script saves time, avoids styling regressions, and produces consistent output.

### Step 1: Check for existing scripts

```bash
ls -la reports/*.py 2>/dev/null
```

Scan the metadata header at the top of each `.py` file (see pdf-patterns.md boilerplate) to find a matching report type. Match on the `# Type:` field, not the filename.

### Step 2: If a matching script exists — adapt it

1. **Read the existing script** and understand its structure
2. **Update only the data** — swap in new values, date ranges, titles, and content
3. **Preserve the layout code** — do not rewrite working boilerplate, page composition, or styling
4. **Update the metadata header** — set `# Last generated:` to today's date
5. **Run it** — execute the adapted script and verify the PDF output

### Step 3: If a matching PDF exists — ask the user

Before regenerating, check for an existing PDF of the same report type:

```bash
ls -lt reports/*.pdf 2>/dev/null
```

If a recent PDF exists, **ask the user** before regenerating:

> "I found an existing **[Report Title]** generated on **[date]**. Would you like me to serve that, or generate a fresh one with current data?"

- If the user wants the existing PDF → serve it directly (upload or open it)
- If the user wants a fresh report → adapt the existing `.py` script and regenerate

**Do NOT ask** if the existing PDF is clearly stale (e.g., a "Weekly Report" from more than 7 days ago, or a report whose data source has obviously changed).

### Step 4: If no matching script exists — generate fresh

Follow the standard report generation workflow below. Use a stable, descriptive filename for the script (see naming convention in pdf-patterns.md Output section).

### Naming Convention

Scripts use **stable, type-based names** so they can be found and reused:

| Good (stable) | Bad (ephemeral) |
|---|---|
| `ai_adoption_report.py` | `report_20260306.py` |
| `weekly_platform_summary.py` | `report_v2_final.py` |
| `incident_review.py` | `untitled_report.py` |

PDFs include the date to distinguish versions: `ai_adoption_report_2026-03-06.pdf`.

The script filename should match the `# Type:` field in the metadata header.

## Data Gathering for Person Reports

When generating a report about a specific person (engineer profile, executive summary, performance review), actively gather data from available sources — do not rely on the user providing everything. Use GHE user profile (`gh api users/<username>`) for account creation date/tenure, GHE search API for commits and PRs, and `acli jira` for active work items.

**Key guardrails:** Account creation date ≠ company join date. Say "active on GHE since" not "joined JET in". Never infer job title, role, seniority, or reporting lines from API data — ask the user.

> **Full reference**: Data gathering commands, endpoints, data points checklist, and presentation guidelines are in [references/person-reports.md](references/person-reports.md).

## Data Integrity Rules

Reports are read by 1300+ people including senior leadership. **Factual errors are career-damaging** — both for the report author and the people misrepresented. Follow these rules strictly.

### Never Hallucinate Names, Titles, or Quotes

- **NEVER guess or infer a person's surname, job title, or role.** If you don't have the exact name from a verified source (API response, user input, or document), **ask the user** before generating the report. Keep questions to a minimum — batch them into a single prompt.
- **NEVER fabricate quotes or attribute statements** to named individuals. Only include quotes that the user provides verbatim, or that come from a verified source (Confluence page, Slack message, meeting notes).
- **NEVER guess organisational structure** — CTO, VP, Director names and reporting lines must come from the user or verified sources. Getting a C-level name wrong is a critical failure.
- **Common hallucination patterns to avoid:**
  - Inventing surnames for people you only know by first name
  - Guessing job titles based on context clues
  - Making up Jira ticket numbers, ADR references, or Confluence page titles
  - Inventing team names or organisational units

### No Placeholders in Output

**NEVER leave `[TODO: ...]`, `[TBD]`, `[PLACEHOLDER]`, or similar markers in a generated PDF.** A PDF with placeholder text looks unprofessional and broken. If you lack information needed to complete a section:

1. **Ask the user before generating** — batch missing items into a single question
2. **Omit the section entirely** if the data isn't available and the section isn't critical
3. **Rephrase to avoid the gap** — e.g., instead of "[TODO: verify CTO name]", simply don't include the name

### Verify Before Including

For any factual claim in the report, you must have **at least one verified source**:

| Claim type | Acceptable sources |
|---|---|
| Person's name + title | User provides it, or GHE/Jira API response |
| Metric or KPI | API query result, BigQuery output, or user-provided data |
| Quote or testimonial | User provides the exact text |
| Team or org name | GHE org API, or user confirmation |
| Date or timeline | API data, or user-provided |
| Tool or platform name | User confirms, or verified from documentation |

If in doubt, **ask the user** rather than guessing — but keep questions minimal and batched.

## Communication Principles

These reports will be read by 1300+ people. Every design choice must maximise scannability and comprehension.

### The 5-30-300 Rule

Structure every report around three reading speeds:
- **5 seconds** -- the cover page tells the full story (hero KPI + title)
- **30 seconds** -- the executive summary gives all key findings (key takeaway + insight headings)
- **300 seconds** -- the full report provides supporting evidence (tables, charts, detail sections)

If a reader stops at any level, they still got the message.

### Lead With the Conclusion (Pyramid Principle)

The McKinsey pyramid principle: **answer first, evidence second**. Every report should open with the key finding, not build up to it.

- **Wrong**: "This report covers incident data for the week of Feb 23-27..."
- **Right**: "Payment failures drove 48% of all incidents, up 12% WoW"

Structure each section as: conclusion -> supporting arguments (2-4, MECE) -> evidence.

### Key Takeaway Box

Every executive summary page MUST start with a `key_takeaway()` -- a single bold sentence stating the most important finding. This is the one sentence an exec reads if they read nothing else.

### Insight-as-Headline Section Titles

Section headings should be complete sentences stating the finding, NOT generic labels.

| Bad (label) | Good (insight) |
|-------------|---------------|
| Executive Summary | Payment failures drove 48% of all incidents |
| Service Health | 3 of 12 regions showed degraded availability |
| Adoption Metrics | Copilot adoption reached 11.3% across 58 teams |

### Numbers Need Context

A number without context is meaningless. Every KPI must show at least one of:
- **Period-over-period delta**: "+12% WoW", "-3pp MoM"
- **Target comparison**: "vs 99.9% SLO"
- **Ranking**: "#1 of 12 services"

### Number Formatting

Apply consistent formatting to all numbers:
- **Thousands separators**: `f"{value:,}"` -- display `5,258` not `5258`
- **Percentages**: one decimal place (`48.3%`), never `48.29341%`
- **Large numbers**: `1.2M`, `45.3K` for numbers over 10,000
- **Deltas**: always include sign: `+12%`, `-3pp`, `+8 new`

Use the `fmt_number()`, `fmt_pct()`, and `fmt_delta()` helpers from pdf-patterns.md.

### Bold Key Data Points

Use `markdown=True` on `multi_cell()` and `cell()` to render `**text**` as bold inline. Apply bold to key figures and labels in executive summary paragraphs. Do NOT bold entire sentences or general prose -- only the data points that an executive would scan for.

### Data Source Attribution

Every table MUST end with a source footnote using the `source_footnote()` helper.

### Sort by Value, Not Alphabet

Always sort tables by the primary metric (descending). Never sort alphabetically unless the user specifically requests it. For long lists, show top 10 with an "Other" grouping.

## Design System

The design system is extracted from the official **JET Global Product and Tech presentation template** (177 slides, 45+ layouts) and the **JET Visual Identity Style Guide**. All colours, fonts, and spacing match the corporate identity.

Key principles:
- **Colours**: JET Orange (`#FF8000`) is primary brand. Use `JET_ORANGE_TEXT` (`#F36805`) for WCAG-accessible orange text. Charcoal (`#242E30`) for all text on light backgrounds. Supporting colours (Berry, Turmeric, Cupcake, Latte) are structural only — never as text.
- **Typography**: Inter font family (bundled at `references/fonts/`). Body text 11pt, headings 15pt, table body 8-9pt.
- **Spacing**: 4mm base unit (`SPACE_XS=2`, `SPACE_SM=4`, `SPACE_MD=8`, `SPACE_LG=12`, `SPACE_XL=16`).
- **Bookend principle**: First and last pages use full-bleed JET Orange. At least 20% of pages feature JET Orange.
- **No logo on ANY page** — brand presence comes from JET Orange bookends and colour palette only.
- **NEVER use `__underline__` in markdown** — renders as broken hyperlinks. Only use `**bold**`.
- **Bold inversion bug**: Base font MUST be regular weight when using `**bold**` highlights with `markdown=True`. If base font is bold, `**text**` turns bold OFF.

> **Full reference**: Complete colour palette (50+ colours), type scale table, WCAG accessibility rules, spacing system, page dimensions, markdown rules, layout conventions, and header/footer patterns are in [references/design-system.md](references/design-system.md).

### Critical Settings

```python
import os
from fpdf.fonts import FontFace
from fpdf.enums import TableBordersLayout, TableCellFillMode

pdf = ReportPDF()       # Always use the ReportPDF subclass
pdf.set_left_margin(MARGIN)   # MUST set - fpdf2 defaults to 10mm, not MARGIN
pdf.set_right_margin(MARGIN)
pdf.alias_nb_pages()  # Required for {nb} total page count in headers
pdf.set_auto_page_break(auto=False)  # ALWAYS disable - handle pagination manually

# Register Inter font family (MUST do before any set_font("Inter", ...))
FONT_DIR = os.path.expanduser("~/.agents/skills/jet-report/references/fonts")
pdf.add_font("Inter", "", f"{FONT_DIR}/Inter-Regular.ttf")
pdf.add_font("Inter", "B", f"{FONT_DIR}/Inter-Bold.ttf")
pdf.add_font("Inter", "I", f"{FONT_DIR}/Inter-Italic.ttf")
pdf.add_font("Inter", "BI", f"{FONT_DIR}/Inter-BoldItalic.ttf")
# Weight variants
pdf.add_font("InterMedium", "", f"{FONT_DIR}/Inter-Medium.ttf")
pdf.add_font("InterSemiBold", "", f"{FONT_DIR}/Inter-SemiBold.ttf")
pdf.add_font("InterExtraBold", "", f"{FONT_DIR}/Inter-ExtraBold.ttf")
pdf.add_font("InterBlack", "", f"{FONT_DIR}/Inter-Black.ttf")
pdf.add_font("InterLight", "", f"{FONT_DIR}/Inter-Light.ttf")
```

## Component Library

The skill includes a **component library** at [references/components.md](references/components.md) that defines every visual component available for PDF reports, including a **decision tree** for selecting the right component based on the type of information being presented.

**Default to open layouts.** The JET template is fundamentally card-free — content is structured through typography, whitespace, and colour blocks. Only use card containers when content genuinely benefits from visual grouping.

Before building a page, consult the decision tree in `components.md`. Key component selection rules:
- **3 key points or steps?** → `NUMBERED_COLUMNS` (open, no cards)
- **List with status?** → `STATUS_LIST` (dots + text)
- **2-4 hero metrics?** → `STAT_ROW` (open) or `STAT_CARDS` (emphasis only)
- **Narrative text?** → `BODY_TEXT` with `KEY_TAKEAWAY` header
- **Quote?** → `QUOTE_BLOCK` (full-width, left accent bar)

> **Full reference**: All component definitions, code snippets, and composition rules are in [references/components.md](references/components.md). Ready-to-paste fpdf2 code for every component is in [references/pdf-patterns.md](references/pdf-patterns.md).

## Common Mistakes to Avoid

### Layout
- **Inconsistent spacing** -- use the 4mm base unit system, not arbitrary values
- **Elements touching page edges** -- maintain 20mm margins everywhere
- **More than 3 font sizes on one page** -- pick heading, body, and caption sizes
- **Orphaned headings** -- always check `if pdf.get_y() + MIN_SECTION_SPACE > MAX_Y`

### Colour & Typography
- **Using JET_ORANGE as body text** on white backgrounds -- fails WCAG AA (3.4:1)
- **Bolding everything** -- bold only top 5 table rows, headings, and key numbers
- **ALL CAPS for long text** -- only for labels under 3 words (e.g., "METHODOLOGY", "WEEKLY REPORT")
- **Underlining text** -- NEVER use `__underline__` markdown syntax. This is the #1 most common visual defect. As a code-level safeguard, strip double underscores before any `markdown=True` call: `text = text.replace("__", "")`
- **Rainbow effect** -- max 6 functional colours per report
- **Bold inversion** -- base font MUST be regular weight when using `**bold**` with `markdown=True`. If base is bold, `**text**` toggles bold OFF. This is the #2 most common visual defect.

### Layout Integrity
- **Heading truncation** -- `cell()` silently clips long text. Always use `multi_cell()` for section headings, insight titles, and centred titles (including template titles). `cell()` with `align="C"` overflows both margins when text exceeds the cell width. See gotchas-and-errors.md.
- **Footer/content collision** -- every draw loop (chart rows, table rows, list items) must check `pdf.get_y() + item_h > MAX_Y` before EACH iteration, not just once at the start.
- **Two-column misalignment** -- side-by-side elements must anchor to the same Y. Save `start_y` before column 1, restore before column 2. See gotchas-and-errors.md.
- **Chart colour inconsistency** -- all charts on one page use the same palette (default: orange) unless comparing distinct categories. Two rankings on the same page must both be orange.
- **Fixed-width label truncation** -- never hardcode column widths for variable-length labels. Measure with `get_string_width()` or use `multi_cell()`. This causes name/description text to merge.
- **Status dots rendered black** -- always use `pdf.traffic_light()` for status dots. Never draw dots manually — `set_fill_color("green")` silently renders black.
- **Horizontal bar overflow** -- bar width must be clamped with `min(bar_w, bar_max_w)` after calculation. Count labels beside bars must also be clamped to stay inside the card. See gotchas-and-errors.md.

### Data & Content
- **Numbers without context** -- always show a delta, target, or ranking
- **Precision theatre** -- use `48.3%` not `48.29341%`; use `5,258` not `5258`
- **Sorting alphabetically** -- always sort by primary metric, descending
- **Too many categories** -- show top 10 with "Other" grouping; full list in appendix
- **Chart title describes the chart** -- title should state the insight, not "Bar chart of X"
- **Missing data source** -- always include a `source_footnote()` or methodology box

## Known Gotchas

The most critical fpdf2 gotchas to keep top-of-mind:

1. **`local_context(font_size=)` uses millimetres, not points** — `font_size=15` renders at ~42.5pt. Always use `set_font()` for sizing. Use `local_context()` only for `text_color`, `fill_color`, `draw_color`, `fill_opacity`, etc.
2. **`solid_arc()` at 360° leaves a visible gap** — use `pdf.ellipse()` for full circles. Only use `solid_arc()` for partial arcs.
3. **`cell()` silently truncates long text** — use `multi_cell()` for any heading or label that could exceed the printable width. This is the #1 cause of headings being cut off mid-word.
4. **Footer/content collision** — draw loops must check `get_y() + item_h > MAX_Y` before **every** item, not just once at the start.
5. **`set_fill_color("green")` renders black** — always use `pdf.traffic_light()` for status dots, never draw manually with string colour names.
6. **Fixed-width label truncation** — `cell(55, h, name)` clips long labels, causing name and description text to merge. Measure with `get_string_width()`.
7. **Horizontal bar overflow** — bar width calculated as `(value / max_value) * bar_max_w` must always be clamped with `min(bar_w, bar_max_w)`. Count labels beside bars must also be clamped so they stay inside the card boundary. The `draw_progress_bar()` helper already does this correctly — apply the same `min()` pattern to all inline bar calculations.

> **Full reference**: All gotchas (Unicode, float sizes, KPI card alignment, rounded rects, pagination, table API, two-column alignment) and error handling patterns (empty data, page overflow, box sizing, font loading, input validation, graceful degradation) are in [references/gotchas-and-errors.md](references/gotchas-and-errors.md).

## Google Slides (Planned)

Google Slides output is planned but not yet available. It requires the Google Slides API to be enabled on the `jet-agent-skills` GCP project.

- **Template**: `1M-8jgsBKitaL6pkVg_78DcoFm__9_MoEmmkpazKkv9k`
- **Approach**: Copy the JET company theme via Drive API, populate via Slides API batchUpdate
- **Auth**: Same OAuth2 credentials as `jet-google-sheets` (project `jet-agent-skills`), with `presentations` and `drive` scopes added
- **Prerequisites**: `pip3 install google-auth-oauthlib google-api-python-client`

When Slides support is added, default to PDF output. Only generate Slides if the user explicitly requests it.

## Templates

Some tools and skills have **dedicated report templates** with specific layouts, headers, and section structures that differ from the standard free-form JET report. Templates live in `templates/` and override specific design rules while inheriting everything else (colours, fonts, spacing, WCAG, data integrity).

**When to use a template:** If the report is requested by or for a specific tool (e.g., Merlin), check `templates/` for a matching template before generating. If a template exists, use it as the basis.

**Available templates:**

| Template | Tool | Description |
|---|---|---|
| [Merlin report](templates/merlin_report.md) | jet-merlin | Data analysis case study PDF with compact header, stat cards, code blocks. Uses [merlin_report.py](templates/merlin_report.py) |

**How templates work:**
- Each template has a `.md` spec (design overrides + data interface) and a `.py` implementation
- The `.py` file is a complete, runnable script — copy and adapt it for the specific data
- Templates override specific rules (e.g., no bookend pages, different header) — the overrides are documented in the template's `.md` file
- All shared rules not explicitly overridden still apply

## Reference Material

- [Design system](references/design-system.md) - colour palette, typography, spacing, accessibility, layout conventions
- [Person reports](references/person-reports.md) - data gathering commands and guardrails for person-focused reports
- [Gotchas and errors](references/gotchas-and-errors.md) - fpdf2 gotchas and error handling patterns
- [Component library](references/components.md) - decision tree + all component definitions with usage guidance
- [PDF patterns](references/pdf-patterns.md) - ready-to-paste fpdf2 code snippets for every component
- [Merlin report template](templates/merlin_report.md) - Merlin case study design spec and overrides
