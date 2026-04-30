# Merlin Report Template

> **Purpose**: Design specification for Merlin data analysis case study PDFs.
> This template overrides specific base design rules from the JET report skill.
> All shared rules (colours, fonts, spacing, WCAG, data integrity) still apply
> unless explicitly overridden below.

## Overview

Merlin is an AI-powered data analysis tool that produces structured case studies
from BigQuery data. Each case study has a fixed set of sections and follows a
"receipt-style" layout — clean, compact, and information-dense.

The template implementation is at [templates/merlin_report.py](merlin_report.py).

## Design Source

Figma: `Report templates > Option 1 – Strong brand`
File key: `KughXDCcQ2VJtDRPh8fOqw`

## Overrides from Base JET Report Design

| Base Rule | Merlin Override | Reason |
|---|---|---|
| Full-bleed JET Orange **cover page** (bookend) | **No cover page** — starts with content | Receipt-style format |
| Full-bleed JET Orange **closing page** (bookend) | **No closing page** — ends with content | Receipt-style format |
| Section header bands (25mm) or thin accent lines | **Compact orange header band** (~22mm) with "Merlin" branding + JET icon on **every page** | Consistent per-page identity |
| No logos on any page | **JET chef-hat icon** in header (top right) | Merlin brand identity |
| Mozzarella (#EFEDEA) background | **#F6F3EF** (warmer, lighter) background | Matches Figma design |
| Footer: `page# \| date \| title` | Footer: `page#` (left) + `date at time` (right) | Compact format |
| Headings: Inter Bold 15pt | Headings: Inter **ExtraBold** 15pt | Matches Figma |
| Title: InterBlack 44pt left-aligned | Title: InterBlack **25pt centred**, wraps via `multi_cell()` | Receipt-style |
| Free-form section order | **Fixed section order** (see below) | Structured case study |
| Min 20% JET Orange pages | Header band on every page provides brand presence | Replaces bookends |

## Section Order (fixed)

1. **Title** — Centred InterBlack 25pt + subtitle (date range). Must use `multi_cell()` so long titles wrap within margins instead of overflowing.
2. **Summary** — Prose analysis paragraph
3. **Keywords** — Tag pills + metadata key-value pairs
4. **Numbers** — Row of stat cards (white bg, orange values, 1-4 cards)
5. **Key Findings** — Bulleted list with bold labels
6. **SQL Queries** — Table: query filename, description, output path (code-styled)
7. **Methodology** — Bulleted list with inline code blocks

All sections are optional — if data is missing for a section, it is skipped.
Page breaks happen automatically when content overflows.

## Data Interface

The template accepts a Python dict (or JSON) with these keys:

```python
{
    "title": str,           # Case study title (e.g. "Total Orders in Amsterdam")
    "subtitle": str,        # Date range or qualifier
    "generated_at": str,    # Timestamp for the footer (e.g. "2 March 2026 at 15:45")
    "summary": str,         # Analysis paragraph
    "keywords": {
        "tags": [str],      # Tag labels for pills
        "metadata": {       # Bold-label key-value pairs
            "Business Domain": str,
            "Region": str,
            "Time Period": str,
            "Tables Used": str
        }
    },
    "numbers": [            # 1-4 stat cards
        {"value": str, "label": str}
    ],
    "key_findings": [       # Bulleted findings
        {"label": str, "detail": str}   # or plain strings
    ],
    "sql_queries": [        # Table rows
        {"query": str, "description": str, "output": str}
    ],
    "methodology": [str]    # Steps with optional `backtick` code spans
}
```

## Visual Details (from Figma)

### Header Band
- Height: ~22mm (64px at Figma's 595px canvas scale)
- Background: JET Orange (#FF8000)
- Text: "Merlin  •  AI-powered data analysis case studies from Merlin VIP"
  - Inter Medium 8pt, white ~90% opacity
- Icon: JET chef-hat (white), top-right, ~10mm

### Stat Cards
- White background, 1px border (#F0ECE6), 1.5mm corner radius
- Value: InterBlack 13pt, JET Accessible Orange (#F36805)
- Label: InterMedium 8pt, subdued grey

### Tag Pills
- White background, fully rounded capsule (corner_radius = pill_h/2 - 0.01)
- Inter Regular 10pt, Charcoal text
- Wrapping row layout with 1.5mm gap

### Code Blocks (inline)
- Blue tonal background pill (#E4E9FB / Figma: support-info-tonal), 1.5mm corner radius
- Courier Regular 9pt, Charcoal text
- Used in SQL Query table filenames and Methodology inline code spans

### SQL Query Table
- Rounded border container (#E7E2DA, 4mm corner radius)
- Header: warm grey background (#F0ECE6), Inter Bold 10pt
- Three equal-width columns
- Cell filenames: blue code pills (#E4E9FB) with Courier 9pt, dark text
- Descriptions: Inter Regular 10pt, Charcoal text
- Row dividers: subtle rgba(0,0,0,0.08) equivalent

## Usage

When Merlin requests a PDF report, the agent should:

1. Import from the template: `from templates.merlin_report import generate`
2. Pass the structured data dict from Merlin's output
3. Call `generate(data, output_path)`

Or copy and adapt `merlin_report.py` if the data structure differs.
