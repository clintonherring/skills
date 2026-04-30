# jet-report

Generate professional PDF reports at JET using fpdf2 (Python). Supports executive summaries, adoption reports, weekly summaries, incident reviews, data snapshots, and any structured report. All reports follow the official JET Visual Identity Style Guide and presentation template design system.

## Prerequisites

**macOS/Linux:**
```bash
pip3 install fpdf2
```

**Windows:** Install [Python for Windows](https://www.python.org/downloads/windows/) if not already present, then:
```powershell
pip install fpdf2
```

## Design System Reference

### Typography (Inter Font Family)

All text uses the **Inter** font family. The following scale is derived from the official JET brand specification:

| Element | Weight | Size (slides) | PDF Equivalent | Font Registration |
|---------|--------|---------------|----------------|-------------------|
| Section header band title | Inter Bold (700) | 14pt | 14pt | `Inter B` |
| Cover page headline | Inter Black (900) | 25pt | 25-44pt (dynamic — 44pt ≤30 chars, 34pt ≤60 chars, 25pt >60 chars) | `InterBlack` |
| Section heading | Inter Bold (700) | 19pt | 15pt | `Inter B` |
| Subtitle | Inter Bold (700) | 11pt | 11pt | `Inter B` |
| Body text | Inter Regular (400) | 11pt | 11pt | `Inter` |
| Footer | Inter Regular/Bold | 8pt | 7-8pt | `Inter` / `Inter B` |
| Source attribution | Inter Regular (400) | 7pt | 7pt | `Inter` |

- **Default line spacing**: 1.15
- **Default alignment**: Left-aligned
- **Copy style**: Sentence case (not UPPERCASE except for labels/badges under 3 words)

### Colour Palette (Official JET Brand Names)

#### Primary colour

| Brand Name | Hex | RGB | Usage |
|-----------|-----|-----|-------|
| **JET Orange** | `#FF8000` | (255, 128, 0) | Primary brand — MUST appear in every communication |
| **JET Accessible Orange** | `#F36805` | (243, 104, 5) | WCAG-accessible orange for text on light backgrounds (4.5:1 on white) |

#### Neutral colours

| Brand Name | Hex | RGB | Usage |
|-----------|-----|-----|-------|
| **Charcoal** | `#242E30` | (36, 46, 48) | Text and interactive elements ONLY. Never as background. |
| **Mozzarella** | `#EFEDEA` | (239, 237, 234) | Primary background colour |
| **Mozzarella Tint 1** | `#F5F3F1` | (245, 243, 241) | Card/container fill, alternating table rows |
| **Mozzarella Tint 2** | `#FCFCFC` | (252, 252, 252) | Near-white background |

#### Text colours

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| Charcoal | `#242E30` | (36, 46, 48) | Headings (14.3:1 contrast) |
| Dark Text | `#323237` | (50, 50, 55) | Body text (12.6:1 contrast) |
| Mid Text | `#595959` | (89, 89, 89) | Labels, captions (7.0:1) |
| Light Text | `#9E9E9E` | (158, 158, 158) | Metadata (3.5:1, large text only) |
| Muted Text | `#B0ABAB` | (176, 171, 171) | Out-of-scope / greyed-out text |

#### Supporting brand colours

Used for colour blocks and backgrounds — structural, not decorative. **Never combine two supporting colours in one report.** Always pair ONE supporting colour with JET Orange.

| Brand Name | Hex | RGB | Light Tint | Light Hex |
|-----------|-----|-----|-----------|-----------|
| **Berry** | `#F2A6B0` | (242, 166, 176) | Light Berry | `#F9D2D7` |
| **Turmeric** | `#F6C243` | (246, 194, 67) | Light Turmeric | `#FAE0A1` |
| **Cupcake** | `#C1DADE` | (193, 218, 222) | Light Cupcake | `#E0ECEE` |
| **Latte** | `#E7CDA2` | (231, 205, 162) | Light Latte | `#F1E3C9` |

#### Light tints of JET Orange

| Name | Hex | RGB |
|------|-----|-----|
| Light Orange | `#FDDFC3` | (253, 223, 195) |

#### Restricted

| Brand Name | Hex | RGB | Usage |
|-----------|-----|-----|-------|
| **Aubergine** | `#5B3D5B` | (91, 61, 91) | ONLY for highlights in product placements |

### Colour Rules (from JET Visual Identity Style Guide)

1. **JET Orange must appear in EVERY communication**
2. **Supporting colours are for colour blocks and backgrounds** — structural, not decorative
3. **Never combine two supporting colours in one report** — always pair ONE with JET Orange
4. **Charcoal is ONLY for text** — never as a solid background fill
5. **Bookend principle**: Start AND end on JET Orange; supporting colours in the middle
6. **Min 20% of pages** must feature JET Orange prominently (cover, section header bands, closing)
7. **Supporting colours used in SECTIONS** (grouped consecutive pages), not randomly alternating

### Layout Grid

The JET template uses a **12-column grid system** on A4 pages:

- **Page size**: 210 x 297mm (A4 portrait)
- **Margins**: 20mm all sides
- **Content width**: 170mm
- **Grid column**: 170 / 12 ≈ 14.2mm per column
- **Page overflow threshold**: Y = 275mm (leave 22mm at bottom)
- **Spacing system**: 4mm base unit (XS=2, SM=4, MD=8, LG=12, XL=16)

### Bookend Principle

The first and last pages of every report **must** feature JET Orange prominently:

- **Cover page**: Full-bleed JET Orange background with white title text, hero KPI, and metadata — the opening bookend
- **Closing page**: Full-bleed JET Orange background with white text
- **Section header bands**: Coloured bands (~25mm) at top of first page in each major section
- **Content pages**: Mozzarella background. First page of each section has a coloured header band (~25mm); continuation pages have a thin 1.5mm orange accent line. Footer at bottom.

### Footer Format

Inner pages display a footer at page bottom: `page | Month Year | **Title of project**` with a thin horizontal rule above and pipe separators. Font: Inter Regular/Bold, 7-8pt. Omitted on cover and closing pages.

## Component Library

The skill includes a **component library** at `references/components.md` with a decision tree for selecting the right visual component based on the type of information being presented.

**Key principle**: Default to open layouts (no cards/boxes). The JET template achieves structure through typography weight, whitespace, and colour blocks — not containers.

Components are categorised as:
- **Open** (preferred): `NUMBERED_COLUMNS`, `STAT_ROW`, `PROGRESS_LIST`, `STATUS_LIST`, `OPEN_LIST`
- **Contained** (use sparingly): `STAT_CARDS`, `NUMBERED_CARDS`, `QUOTE_BLOCK`, `METHODOLOGY_BOX`
- **Page-level**: `COVER_PAGE`, `CLOSING_PAGE`, `SECTION_HEADER`

See `references/components.md` for full decision tree and code.

## Available Page Types

The `references/pdf-patterns.md` file contains ready-to-paste fpdf2 code for all page types:

1. **Cover Page** — Full-bleed JET Orange, white InterBlack title, hero KPI
2. **Section Header Band** — Coloured band (~25mm) at top of section's first page with title, number, and metadata
3. **Table of Contents** — Numbered section list on Mozzarella background
4. **Executive Summary** — Key takeaway, split panel with TLDR, hero stats
5. **KPI Cards** — Row of metric cards (cover dark variant + inner light variant)
6. **Data Tables** — Full-width with Cupcake headers (Charcoal text), alternating rows, inline bars
7. **Traffic Light Table** — Status dots for service health / incident status
8. **Side-by-Side Charts** — Two top-10 horizontal bar chart cards
9. **Pie Charts** — Percentage gauges in a row
10. **Sparkline Tables** — Mini trend lines in table rows
11. **Callout Boxes** — Methodology, warning, info, success variants
12. **Three-Column Steps** — Numbered steps (open and carded variants)
13. **Quote/Testimonial Cards** — Supporting-colour feedback cards
14. **Timeline/Milestone** — Horizontal timeline with solid/dotted segments
15. **Colour-Coded Matrix** — Categorisation grid with supporting colours
16. **Category Badges** — Rounded-rect pill labels for metadata
17. **Closing Page** — JET Orange bookend with closing message

## Report Structure Guidelines

A well-structured executive report typically follows this order:

1. Cover page (full-bleed JET Orange — bookend)
2. Table of contents (if > 6 sections)
3. Executive summary (key takeaway first)
4. Section header band on first page of each major topic
5. Content pages with data, tables, charts on Mozzarella background
6. Recommendations / next steps
7. Appendix (if needed)
8. Closing page (full-bleed JET Orange — bookend)

**Content principles:**
- Section headings should state insights, not labels ("Payment failures drove 48% of incidents" not "Incident Summary")
- Lead every section with a `key_takeaway()` — the one sentence an exec reads if they read nothing else
- Add `source_footnote()` below every table and chart
- Use `traffic_light()` dots always paired with text labels — never rely on colour alone
- Apply the bookend principle: first and last pages orange, 20%+ pages featuring orange

## Future: Google Slides

Google Slides output is planned but requires the Google Slides API to be enabled on the `jet-agent-skills` GCP project (`602299916251`). Once enabled, this skill will also support creating branded slide decks from the JET company template.

Template: https://docs.google.com/presentation/d/1M-8jgsBKitaL6pkVg_78DcoFm__9_MoEmmkpazKkv9k/edit
