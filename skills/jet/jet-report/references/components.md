# JET PDF Component Library

> **Purpose**: This file defines every visual component available for PDF reports.
> Each component has a clear description, when to use it, and fpdf2 implementation code.
> The AI agent should select components based on the **type of information** being presented,
> not default to cards for everything.

## Design Philosophy

The JET template is fundamentally about **restraint**. Content is structured through:

1. **Typography weight and scale** — not boxes or borders
2. **Whitespace** — generous spacing replaces dividers
3. **Colour blocks** — full-width background colours, not card borders
4. **Consistent vertical rhythm** — elements aligned to a 4mm grid

**Default to open layouts.** Only use cards/containers when content genuinely benefits
from visual grouping (e.g., comparing 3 discrete alternatives side by side).

---

## Core Helper: Rounded-Rect Clipping Path

This helper is **required** by all accent-bar components (TLDR_BLOCK, QUOTE_BLOCK, QUOTE_COLUMNS).
It creates a pixel-perfect rounded-rectangle clip region using raw PDF operators. Draw flat
rects inside the clip to get perfectly rounded corners with no colour bleed.

See `pdf-patterns.md` for the full `_rounded_rect_clip()` and `_restore_gfx_state()` implementations.

**CRITICAL:** Always call `_restore_gfx_state(pdf)` after drawing inside a clip — never raw
`pdf._out("Q")`. Raw Q restores the PDF state but leaves fpdf2's colour cache stale, causing
subsequent fill/draw/text colour calls to be silently skipped.

**Usage pattern:**
```python
_rounded_rect_clip(pdf, x, y, w, h, corner_radius)
# Draw flat rects for accent bar + background inside the clip...
_restore_gfx_state(pdf)  # MUST restore state + re-sync fpdf2 colour cache
```

---

## Component Selection Guide

Use this decision tree when choosing how to present content:

```
What type of information?
│
├─ Executive summary / TLDR (one key message)
│  └─ Use: TLDR_BLOCK (one per report, first content page)
│
├─ A single key metric or finding
│  └─ Use: HERO_KPI (cover) or STAT_ROW (inner page)
│
├─ 2-4 key metrics side by side
│  └─ Use: STAT_ROW (open, no cards) or STAT_CARDS (when metrics need labels + deltas)
│
├─ 3 sequential steps or phases
│  └─ Use: NUMBERED_COLUMNS (open, no cards — the 01/02/03 pattern)
│
├─ A list of items with status
│  └─ How many items?
│     ├─ 5 or fewer → OPEN_LIST with status dots
│     └─ 6+ → STATUS_LIST or DATA_TABLE with status column
│
├─ A list of items with progress/percentage
│  └─ How many items?
│     ├─ 2-4 with descriptions → GRAPH_CARD (pie chart + bar + text, 2x2 grid)
│     └─ 5+ → PROGRESS_LIST or DATA_TABLE with PROGRESS_BAR column
│
├─ Narrative text (findings, analysis)
│  └─ Use: BODY_TEXT with KEY_TAKEAWAY header
│
├─ A quote or testimonial
│  └─ Use: QUOTE_BLOCK (full-width, left accent bar) or QUOTE_COLUMNS (2-3 side by side)
│
├─ A timeline or sequence of events
│  └─ Use: TIMELINE_HORIZONTAL
│
├─ A methodology or source description
│  └─ Use: METHODOLOGY_BOX (subtle container, only exception to no-cards rule)
│
├─ Tabular data (rows + columns)
│  └─ Use: DATA_TABLE
│
├─ Category/department grouping
│  └─ Use: COLOUR_MATRIX or BADGE_ROW
│
├─ Important note, warning, or callout
│  └─ Use: CALLOUT_BOX (accent bar, auto text colour)
│
├─ Content separation within a page
│  └─ Use: DIVIDER (subtle) or whitespace (preferred)
│
├─ Visual emphasis block with colour
│  └─ Use: COLOUR_BLOCK (1/3 or 1/4 ratio per style guide)
│
├─ Checklist of completed items
│  └─ Use: CHECKLIST (better than progress bars when most items 100%)
│
├─ Sub-section heading
│  └─ Use: SECTION_TITLE (bold heading, NO underline — purely typographic hierarchy)
│
├─ Section transition
│  └─ Use: SECTION_HEADER with band_color for strong section breaks, or SECTION_TITLE for sub-sections
│
└─ Cover / closing
   └─ Use: COVER_PAGE or CLOSING_PAGE
```

---

## Page-Level Components

### COVER_PAGE

Full-bleed JET Orange background with white title, hero KPI, and metadata.
The cover is the opening bookend — matching the closing page's full-bleed orange.

**When to use**: First page of every report.

**Structure**:
- Full JET Orange background (bookend principle — first and last pages are orange)
- Report type label (small, warm-tinted text)
- Title in InterBlack 38-44pt, white, left-aligned
- Thin decorative divider line (warm-tinted)
- Hero KPI: single massive number (InterBlack 80pt, white)
- KPI descriptor below in InterMedium 13pt, warm-tinted
- Optional KPI cards at bottom (`COVER_KPI_BG` warm sandy-orange tint fill, white text, 5mm corner radius — NOT charcoal)
- **KPI card consistency**: If any KPI card has a delta/qualifier label (e.g., "+12% WoW", "vs target"), ALL cards in the row must have one. A card missing its context label while siblings have theirs looks broken. If a delta is not available for one card, use a neutral qualifier like "current" or "to date".

```python
def draw_cover(pdf, title_lines, hero_value, hero_label, period, metadata_line):
    pdf.add_page()
    pdf._is_cover = True
    pdf._no_footer_pages.add(pdf.page_no())

    # Full-bleed JET Orange — bookend principle
    pdf.set_fill_color(*JET_ORANGE)
    pdf.rect(0, 0, PAGE_W, PAGE_H, style="F")

    # Report type label
    pdf.set_xy(MARGIN, 55)
    pdf.set_font("Inter", "B", 10)
    pdf.set_text_color(*COVER_TEXT_WARM)
    pdf.cell(0, 5, "REPORT")

    # Title (multi-line)
    y = 66
    pdf.set_font("InterBlack", "", 44)
    pdf.set_text_color(*WHITE)
    for line in title_lines:
        pdf.set_xy(MARGIN, y)
        pdf.cell(0, 22, line)
        y += 22

    # Divider
    pdf.set_draw_color(*COVER_DIVIDER)
    pdf.line(MARGIN, y + 8, MARGIN + 60, y + 8)

    # Hero KPI
    pdf.set_xy(MARGIN, y + 20)
    pdf.set_font("InterBlack", "", 80)
    pdf.set_text_color(*WHITE)
    pdf.cell(0, 35, str(hero_value))

    pdf.set_xy(MARGIN, y + 55)
    pdf.set_font("InterMedium", "", 13)
    pdf.set_text_color(*COVER_TEXT_WARM)
    pdf.cell(0, 7, hero_label)

    # Bottom metadata
    pdf.set_xy(MARGIN, PAGE_H - 35)
    pdf.set_font("Inter", "", 9)
    pdf.set_text_color(*COVER_TEXT_SAND)
    pdf.cell(0, 5, metadata_line)

    pdf.set_xy(MARGIN, PAGE_H - 25)
    pdf.set_font("Inter", "B", 9)
    pdf.set_text_color(*WHITE)
    pdf.cell(0, 5, "Just Eat Takeaway.com")
```

---

### CLOSING_PAGE

Full-bleed JET Orange with centred thank-you message. Bookend principle.

**When to use**: Last page of every report.

```python
def draw_closing(pdf, subtitle="", period=""):
    pdf.add_page()
    pdf._is_closing = True
    pdf._no_footer_pages.add(pdf.page_no())

    pdf.set_fill_color(*JET_ORANGE)
    pdf.rect(0, 0, PAGE_W, PAGE_H, style="F")

    pdf.set_xy(MARGIN, PAGE_H * 0.42)
    pdf.set_font("InterBlack", "", 36)
    pdf.set_text_color(*WHITE)
    pdf.cell(CONTENT_W, 18, "Thank you", align="C")

    if subtitle:
        pdf.set_xy(MARGIN, PAGE_H * 0.50)
        pdf.set_font("Inter", "", 11)
        pdf.cell(CONTENT_W, 6, subtitle, align="C")

    pdf.set_xy(MARGIN, PAGE_H * 0.58)
    pdf.set_font("Inter", "B", 9)
    pdf.cell(CONTENT_W, 6, "Just Eat Takeaway.com", align="C")
```

---

### SECTION_HEADER

Section header band placed at the top of the first page of each major section.
A coloured band (~25mm tall) contains the document title, section title, and
section number. Content starts immediately below on the SAME page — no wasted
full-page dividers.

Subsequent pages in the same section use the standard thin 1.5mm JET Orange
accent line (no band).

**When to use**: First page of each major section. Pass `band_color` to
`content_page()` to activate the band.

**Band colours by section position** (bookend principle):
- First section: `LATTE` (warm beige, near the opening orange bookend)
- Middle sections: `CUPCAKE` (blue-green), `TURMERIC` (golden yellow)
- Final sections: `LATTE` or `BERRY` (warm, leading to closing orange bookend)

`band_color` **must** be one of the four named supporting colours above (`LATTE`, `CUPCAKE`, `TURMERIC`, `BERRY`). Never pass an inline RGB tuple or a colour outside this set — the supporting colours are chosen to harmonise with each other and with the JET Orange bookend pages.

**What NOT to do**: Do NOT use full-page divider pages in PDF reports — they
waste entire pages. Full-page dividers are a presentation/slides pattern.

```python
# First page of a new section — with section header band
pdf.content_page(
    section_title="Executive Summary",
    section_num="Section 01",
    band_color=LATTE,
)
pdf.section_heading("Payment failures drove 48% of all incidents")

# Continuation page in the same section — no band
pdf.content_page(
    section_title="Executive Summary",
    section_num="Section 01",
)
```

---

## Content Components (Open / Card-Free)

These are the PRIMARY components. Default to these unless the content specifically
requires visual containment.

### NUMBERED_COLUMNS

The signature JET "01 / 02 / 03" pattern. Three columns with oversized numbers,
bold headings, and body text. **NO cards, NO borders, NO background fills.**

**When to use**: 3 sequential steps, phases, or key points. This is the preferred
layout for any "three things" content.

**Design rules** (from slide 039):
- Numbers: InterBlack, 28-32pt, dark charcoal (NOT coloured)
- Heading: Inter Bold, 10-11pt, charcoal
- Body: Inter Regular, 8pt, dark text
- Columns separated by whitespace only (no vertical lines)
- Consistent vertical rhythm: number → heading → body
- Left-aligned within each column

```python
def draw_numbered_columns(pdf, items, start_y=None):
    """Draw 01/02/03 columns WITHOUT cards.

    items: list of (number, heading, body) tuples (max 3-4)
    """
    cols = len(items)
    col_gap = GUTTER  # 9mm grid gutter
    col_w = grid_span(GRID_COLS // cols)  # e.g., grid_span(4) for 3 columns
    y = start_y or pdf.get_y()
    max_bottom = y  # track the tallest column's bottom edge

    for i, (num, heading, body) in enumerate(items):
        x = MARGIN + i * (col_w + col_gap)

        # Large number
        pdf.set_xy(x, y)
        pdf.set_font("InterBlack", "", 32)
        pdf.set_text_color(*CHARCOAL)
        pdf.cell(col_w, 14, num)

        # Heading
        pdf.set_xy(x, y + 18)
        pdf.set_font("Inter", "B", 10)
        pdf.set_text_color(*CHARCOAL)
        pdf.cell(col_w, 5, heading)

        # Body
        pdf.set_xy(x, y + 26)
        pdf.set_font("Inter", "", 8)
        pdf.set_text_color(*MID_TEXT)
        pdf.multi_cell(col_w, 4, body, align="L")
        max_bottom = max(max_bottom, pdf.get_y())

    # Position cursor below the tallest column + standard spacing
    pdf.set_y(max_bottom + SPACE_MD)
```

---

### OPEN_LIST

Simple numbered or bulleted list with generous vertical spacing. No cards, no boxes.
Items separated by whitespace only.

**When to use**: Any list of 3-8 items (TOC, key findings, recommendations).

**Design rules** (from slides 037, 042):
- Numbers in bold, same colour as text (or JET Orange for TOC)
- ~8-10mm vertical spacing between items
- No divider lines between items
- Left-aligned, generous left margin

```python
def draw_open_list(pdf, items, numbered=True, number_color=JET_ORANGE_TEXT):
    """Simple numbered list, no cards.

    items: list of strings (or tuples of (number, text) if custom numbering)
    """
    for i, item in enumerate(items):
        if isinstance(item, tuple):
            num, text = item
        else:
            num = f"{i + 1:02d}" if numbered else None
            text = item

        if num:
            pdf.set_font("Inter", "B", 13)
            pdf.set_text_color(*number_color)
            num_w = pdf.get_string_width(num) + 4
            pdf.cell(num_w, 7, num)

            pdf.set_font("Inter", "", 12)
            pdf.set_text_color(*CHARCOAL)
            pdf.cell(CONTENT_W - num_w, 7, text, new_x="LMARGIN", new_y="NEXT")
        else:
            pdf.set_font("Inter", "", 12)
            pdf.set_text_color(*CHARCOAL)
            pdf.cell(CONTENT_W, 7, text, new_x="LMARGIN", new_y="NEXT")

        pdf.ln(SPACE_SM)  # generous spacing between items
```

---

### STAT_ROW

A row of key metrics displayed as plain text — no cards. Large numbers with
labels below, separated by whitespace.

**When to use**: 2-5 key metrics on an inner page where cards would feel heavy.

```python
def draw_stat_row(pdf, stats, y=None):
    """Stats as plain text columns, no cards.

    stats: list of (value, label, delta?) tuples
    """
    y = y or pdf.get_y()
    cols = len(stats)
    col_w = grid_span(GRID_COLS // cols)  # Grid-aligned column widths

    for i, stat in enumerate(stats):
        value, label = stat[0], stat[1]
        delta = stat[2] if len(stat) > 2 else None

        x = MARGIN + i * (col_w + GUTTER)

        # Large value
        pdf.set_xy(x, y)
        pdf.set_font("InterExtraBold", "", 28)
        pdf.set_text_color(*CHARCOAL)
        pdf.cell(col_w, 14, str(value))

        # Label
        pdf.set_xy(x, y + 14)
        pdf.set_font("Inter", "", 8)
        pdf.set_text_color(*MID_TEXT)
        pdf.cell(col_w, 4, label)

        # Delta (JET Orange for contrast — semantic dots carry the colour meaning)
        if delta:
            pdf.set_xy(x, y + 19)
            pdf.set_font("Inter", "B", 7)
            pdf.set_text_color(*JET_ORANGE)
            pdf.cell(col_w, 4, delta)

    pdf.set_y(y + 28)
```

---

### KEY_TAKEAWAY

Bold single-sentence insight at the top of a section. The "so what?" that an
exec reads if they read nothing else.

**When to use**: Top of every section, immediately after the section heading.

**IMPORTANT**: This component sets `Inter "B"` (bold base font) with `markdown=True`. Because
the base font is bold, do NOT use `**highlights**` inside the text — `**` toggles bold OFF,
rendering those words in regular weight (inversion bug). Either pass plain text with no `**markers**`,
or switch the base font to regular and wrap the entire sentence in `**...**`.

```python
def key_takeaway(self, text):
    with self.local_context(text_color=CHARCOAL):
        self.set_font("Inter", "B", 11)
        self.multi_cell(CONTENT_W, 5.5, text, markdown=True, align="L")
    self.ln(SPACE_XS)
```

---

### TLDR_BLOCK

Executive pull-quote block placed at the very top of the first content section
(typically Executive Summary). Uses an orange left accent bar on a warm cream
background. Functions as a "TLDR" — the single most important message in the
entire report.

**When to use**: First content page, immediately below the section header. One per report.

**Design rules**:
- Orange left accent bar (2.5mm wide)
- Warm cream background (`MOZZARELLA_T1`)
- "TLDR" label in small `JET_ORANGE_TEXT` bold text (Inter Bold 7pt)
- Main text in Inter Regular 10pt, charcoal — with `markdown=True` so `**key figures**` render bold. **The base font MUST stay regular weight** (not bold) for `**highlights**` to work correctly (see Composition Rule #14).
- Rounded corners (3mm radius)
- Generous internal padding

```python
def tldr_block(self, text):
    """Executive pull-quote at top of report."""
    y = self.get_y()
    pad_y = 4
    cr = 3
    bar_w = 2.5
    text_w = CONTENT_W - 14
    label_h = 5  # "TLDR" label row

    # ── Measure actual text height via dry-run ────────
    self.set_font("Inter", "", 10)
    body_h = self.multi_cell(
        text_w, 4.5, text, markdown=True, align="L",
        dry_run=True, output="HEIGHT"
    )
    block_h = pad_y + label_h + body_h + pad_y

    # Clipped rounded-rect background with accent bar
    _rounded_rect_clip(self, CONTENT_X, y, CONTENT_W, block_h, cr)
    self.set_fill_color(*JET_ORANGE)
    self.rect(CONTENT_X, y, bar_w, block_h, style="F")
    self.set_fill_color(*MOZZARELLA_T1)
    self.rect(CONTENT_X + bar_w, y, CONTENT_W - bar_w, block_h, style="F")
    _restore_gfx_state(self)  # restore state + re-sync colour cache

    # "TLDR" label
    self.set_xy(CONTENT_X + 8, y + pad_y)
    self.set_font("Inter", "B", 7)
    self.set_text_color(*JET_ORANGE_TEXT)
    self.cell(0, 4, "TLDR")

    # Text (Regular weight + markdown so **bold** stands out for key data)
    self.set_xy(CONTENT_X + 8, y + pad_y + label_h)
    self.set_font("Inter", "", 10)
    self.set_text_color(*CHARCOAL)
    self.multi_cell(text_w, 4.5, text, markdown=True, align="L")

    self.set_y(y + block_h + SPACE_MD)
```

---

### BODY_TEXT

Standard paragraph text with optional inline bold via markdown.

**When to use**: Narrative sections, explanations, executive summary prose.

**CRITICAL — markdown emphasis**: When `markdown=True`, only use `**bold**` for emphasis.
**NEVER** use `__underline__` — fpdf2 renders it as underlined text, which looks like
broken hyperlinks and is the #1 visual defect in generated reports.
**NEVER** use `*italic*` in body text — italic is reserved for quote blocks only.

```python
def draw_body_text(pdf, text, width=None):
    w = width or CONTENT_W
    pdf.set_font("Inter", "", 11)
    pdf.set_text_color(*DARK_TEXT)
    pdf.multi_cell(w, 5, text, markdown=True, align="L")
    pdf.ln(SPACE_SM)
```

---

### SECTION_TITLE

Bold heading with PDF bookmark. **NO underline** — hierarchy is achieved purely
through font weight (Inter Bold 15pt) and whitespace. Confirmed across all 50
JET template slides: zero slides use underlines under titles.

**When to use**: To introduce each sub-section within a page.

> **Note**: This component is implemented as `section_heading()` in the PDF subclass (see `pdf-patterns.md`). Use `pdf.section_heading(title, subtitle)`.

```python
def section_heading(self, title, subtitle="", bookmark=True):
    if bookmark:
        self.start_section(title)
    self.set_font("Inter", "B", 15)
    self.set_text_color(*CHARCOAL)
    # MUST use multi_cell — cell() silently clips long titles
    self.multi_cell(CONTENT_W, 8, title, new_x="LMARGIN", new_y="NEXT")
    self.ln(SPACE_MD)  # 8mm breathing room after heading
    if subtitle:
        self.set_font("Inter", "", 8)
        self.set_text_color(*MID_TEXT)
        self.cell(0, 4, subtitle, new_x="LMARGIN", new_y="NEXT")
        self.ln(SPACE_SM)
```

---

### PROGRESS_LIST

A clean list of items with progress bars. No cards — just name, percentage, and bar
on the same line.

**When to use**: Capability scores, completion rates, any percentage-based list.

```python
def draw_progress_list(pdf, items, bar_color=JET_ORANGE):
    """Open progress list, no cards.

    items: list of (name, percentage) tuples, sorted by percentage descending
    """
    row_h = 10
    bar_h = 3
    bar_w = 60  # fixed bar width

    for name, pct in items:
        y = pdf.get_y()

        if y + row_h > MAX_Y:
            pdf.add_page()
            y = pdf.get_y()

        # Name (left)
        pdf.set_font("Inter", "", 8)
        pdf.set_text_color(*CHARCOAL)
        pdf.cell(CONTENT_W - bar_w - 25, row_h, name)

        # Percentage (right of name) — JET Orange for 100%, Charcoal otherwise
        score_color = JET_ORANGE if pct == 100 else (CHARCOAL if pct >= 50 else JET_ORANGE)
        pdf.set_font("InterExtraBold", "", 9)
        pdf.set_text_color(*score_color)
        pdf.cell(20, row_h, f"{pct:.0f}%", align="R")

        # Progress bar (rightmost)
        bar_x = MARGIN + CONTENT_W - bar_w
        bar_y = y + (row_h - bar_h) / 2

        # Track
        pdf.set_fill_color(*BORDER)
        pdf.rect(bar_x, bar_y, bar_w, bar_h, style="F",
                 round_corners=True, corner_radius=bar_h / 2)
        # Fill
        if pct > 0:
            fill_w = max((pct / 100) * bar_w, bar_h)
            fill_w = min(fill_w, bar_w)  # clamp to track width
            pdf.set_fill_color(*bar_color)
            pdf.rect(bar_x, bar_y, fill_w, bar_h, style="F",
                     round_corners=True, corner_radius=bar_h / 2)

        pdf.ln(row_h)

        # Subtle separator line
        pdf.set_draw_color(*BORDER)
        pdf.line(MARGIN, pdf.get_y(), MARGIN + CONTENT_W, pdf.get_y())
```

---

### GRAPH_CARD

A 2x2 grid of graph cards — each with a pie chart (left) + title, progress bar, and description (right). Based on JET "Graphs" slide pattern (slide_070). Each card uses a different JET supporting colour.

**When to use**: 2-4 key metrics where visual proportion (pie) + contextual text both add value. For 5+ items, prefer PROGRESS_LIST or a data table with inline bars.

See `pdf-patterns.md` → "Graph Card Grid" for full implementation.

```python
# Each card: (title, pct, description, accent_color, track_tint)
graph_items = [
    ("PDF Generation", 95, "Full component coverage.", BERRY, LIGHT_PINK),
    ("Design System", 88, "VI alignment complete.", CUPCAKE, LIGHT_BLUE),
    ("Data Visualisation", 72, "Charts and tables styled.", LATTE, LIGHT_TAN),
    ("Documentation", 60, "Skill files in progress.", TURMERIC, LIGHT_YELLOW),
]
```

**Design notes:**
- Each card uses a unique JET supporting colour (one of the few multi-colour exceptions)
- Pie charts are solid (no inner hole) — use `pdf.pie_chart()`
- No visible card borders — cards float on Mozzarella background
- Keep descriptions to 2-3 lines for visual balance with the pie

> **CRITICAL (Rule #27)**: Before rendering, calculate total grid height: `num_rows * (card_h + row_gap) - row_gap`. If this exceeds the remaining page space but fits on a fresh page, call `pdf.add_page()` first. Without this pre-flight check, a 2×2 grid can split across pages, leaving orphaned cards with ~60% whitespace on the overflow page. See `gotchas-and-errors.md` → "Grid/Multi-Row Component Page Overflow".

---

### STATUS_LIST

A clean list of items with status dots. No cards, no tiles.

**When to use**: Feature status, capability readiness, checklist-style content.

> **CRITICAL**: Always use `pdf.traffic_light(x, y, status)` for status dots — never draw dots manually with `set_fill_color()`. Passing a colour name string (e.g., `"green"`) to `set_fill_color()` silently renders black. The `traffic_light()` method maps status strings to proper RGB tuples internally.

> **CRITICAL**: Never concatenate name + description into a single string. Draw the name as a separate `cell()`, then the description as a separate `cell()` or `multi_cell()`. Use an em-dash separator. Measure the name width with `get_string_width()` to prevent truncation — never hardcode a fixed column width for variable-length labels.

```python
def draw_status_list(pdf, items):
    """Open status list with traffic light dots.

    items: list of (name, status, description) tuples
    status: "green", "orange", "red", "gray"/"grey"
    Uses true traffic light colours (green/orange/red/gray) for instant recognition.

    IMPORTANT: Always use pdf.traffic_light() for dots — never draw manually.
    IMPORTANT: Never hardcode name column width — measure with get_string_width().
    """
    STATUS_LABELS = {"green": "Ready", "orange": "Planned", "red": "Blocked",
                     "gray": "N/A", "grey": "N/A"}
    row_h = 8

    # Measure the widest name to set column width dynamically
    pdf.set_font("Inter", "B", 8)
    name_col_w = max(pdf.get_string_width(name) + 6 for name, _, _ in items)
    name_col_w = max(name_col_w, 55)  # minimum 55mm
    status_col_w = 18
    dot_col_w = 5
    desc_col_w = CONTENT_W - dot_col_w - name_col_w - status_col_w

    for name, status, description in items:
        y = pdf.get_y()

        if y + row_h > MAX_Y:
            pdf.add_page()
            y = pdf.get_y()

        # Status dot — ALWAYS use traffic_light(), never draw manually
        pdf.traffic_light(MARGIN, y + 2.5, status)

        # Name (separate cell — never concatenate with description)
        pdf.set_xy(MARGIN + dot_col_w, y)
        pdf.set_font("Inter", "B", 8)
        pdf.set_text_color(*CHARCOAL)
        pdf.cell(name_col_w, row_h, name)

        # Status label (Charcoal text for contrast — dots carry the colour)
        pdf.set_font("Inter", "B", 6.5)
        pdf.set_text_color(*CHARCOAL)
        pdf.cell(status_col_w, row_h, STATUS_LABELS.get(status, status).upper())

        # Description (separate cell with em-dash separator)
        pdf.set_font("Inter", "", 7.5)
        pdf.set_text_color(*MID_TEXT)
        pdf.cell(desc_col_w, row_h, f"\u2014 {description}")

        pdf.ln(row_h)

        # Subtle separator
        pdf.set_draw_color(*BORDER)
        pdf.line(MARGIN + dot_col_w, pdf.get_y(), MARGIN + CONTENT_W, pdf.get_y())
        pdf.ln(1)  # sub-SPACE_XS: tight coupling after separator
```

---

### QUOTE_BLOCK

Full-width quote with subtle background tint and **vertical left accent bar**.
The left bar style is more aligned with JET presentation conventions than a top bar.

**When to use**: Single testimonial or pull-quote. Use QUOTE_COLUMNS for 2-3 side by side.

**CRITICAL — never fabricate quotes**: Never invent quote text or attributions.
If you don't have an exact quote from a verified source (user input, document, API),
ask the user before generating. Never leave placeholder text in a PDF. See SKILL.md "Data Integrity Rules".

```python
def draw_quote_block(pdf, text, attribution, role="", bg_color=LIGHT_YELLOW, accent_color=TURMERIC):
    y = pdf.get_y()
    h = 32
    cr = 3
    bar_w = 2.5
    quote_pad = 7  # equal top and bottom padding

    # Clipped rounded-rect background with accent bar
    _rounded_rect_clip(pdf, MARGIN, y, CONTENT_W, h, cr)
    pdf.set_fill_color(*accent_color)
    pdf.rect(MARGIN, y, bar_w, h, style="F")
    pdf.set_fill_color(*bg_color)
    pdf.rect(MARGIN + bar_w, y, CONTENT_W - bar_w, h, style="F")
    _restore_gfx_state(pdf)  # restore state + re-sync colour cache

    # Quote text — positioned using quote_pad from top
    pdf.set_xy(MARGIN + 10, y + quote_pad)
    pdf.set_font("Inter", "I", 9)
    pdf.set_text_color(*CHARCOAL)
    pdf.multi_cell(CONTENT_W - 20, 4.5, f'"{text}"', align="L")

    # Attribution — positioned from bottom edge to guarantee equal bottom padding
    attr_y = y + h - quote_pad - 8  # 8 = two lines of 4pt
    pdf.set_xy(MARGIN + 10, attr_y)
    pdf.set_font("Inter", "B", 7)
    pdf.set_text_color(*CHARCOAL)
    pdf.cell(0, 4, attribution, new_x="LEFT", new_y="NEXT")
    if role:
        pdf.set_font("Inter", "", 7)
        pdf.set_text_color(*MID_TEXT)
        pdf.cell(0, 4, role)

    pdf.set_y(y + h + SPACE_SM)
```

---

### QUOTE_COLUMNS

Side-by-side quotes (2-3 columns) using the same accent bar style as QUOTE_BLOCK.

**When to use**: Comparing testimonials, multiple stakeholder perspectives, or 2-3 short quotes.

**CRITICAL — never fabricate quotes**: Same data integrity rules as QUOTE_BLOCK apply.
Never invent quote text or attributions. See SKILL.md "Data Integrity Rules".

```python
def draw_quote_columns(pdf, quotes, bg_color=LIGHT_YELLOW, accent_color=TURMERIC):
    """Side-by-side quote blocks.

    quotes: list of (text, attribution, role) tuples (2-3 items)
    """
    cols = len(quotes)
    gap = GUTTER
    col_w = grid_span(GRID_COLS // cols)  # Grid-aligned
    h = 32
    y = pdf.get_y()
    cr = 3
    bar_w = 2.5
    quote_pad = 5  # equal top and bottom padding (smaller for columns)

    for i, (text, attribution, role) in enumerate(quotes):
        x = MARGIN + i * (col_w + gap)

        # Clipped rounded-rect with accent bar
        _rounded_rect_clip(pdf, x, y, col_w, h, cr)
        pdf.set_fill_color(*accent_color)
        pdf.rect(x, y, bar_w, h, style="F")
        pdf.set_fill_color(*bg_color)
        pdf.rect(x + bar_w, y, col_w - bar_w, h, style="F")
        _restore_gfx_state(pdf)  # restore state + re-sync colour cache

        # Quote text — positioned using quote_pad from top
        pdf.set_xy(x + 6, y + quote_pad)
        pdf.set_font("Inter", "I", 8)
        pdf.set_text_color(*CHARCOAL)
        pdf.multi_cell(col_w - 12, 3.8, f'"{text}"', align="L")

        # Attribution — positioned from bottom edge to guarantee equal bottom padding
        attr_y = y + h - quote_pad - 8  # 8 = two lines of 4pt
        pdf.set_xy(x + 6, attr_y)
        pdf.set_font("Inter", "B", 6.5)
        pdf.set_text_color(*CHARCOAL)
        pdf.cell(0, 4, attribution, new_x="LEFT", new_y="NEXT")
        if role:
            pdf.set_font("Inter", "", 6.5)
            pdf.set_text_color(*MID_TEXT)
            pdf.cell(0, 4, role)

    pdf.set_y(y + h + SPACE_SM)
```

---

### TIMELINE_HORIZONTAL

Horizontal timeline with dots, segments (solid/dotted), and staggered labels.

**When to use**: Project milestones, development phases, roadmap.

```python
def draw_timeline(pdf, milestones, y_center=None):
    """Horizontal timeline with staggered above/below labels.

    milestones: list of (date, title, detail, completed) tuples
    """
    y = y_center or pdf.get_y() + 30
    x_start = MARGIN + 10
    x_end = PAGE_W - MARGIN - 10
    total_w = x_end - x_start
    seg_w = total_w / (len(milestones) - 1)

    # Draw segments
    for i in range(len(milestones) - 1):
        sx = x_start + i * seg_w
        is_done = milestones[i][3] and milestones[i + 1][3]
        if is_done:
            with pdf.local_context(draw_color=JET_ORANGE, line_width=1.2):
                pdf.line(sx, y, sx + seg_w, y)
        else:
            with pdf.local_context(draw_color=BORDER, line_width=1.0):
                dx = 0
                while dx < seg_w:
                    end = min(sx + dx + 3, sx + seg_w)
                    pdf.line(sx + dx, y, end, y)
                    dx += 5

    # Draw dots and labels
    for i, (date, title, detail, done) in enumerate(milestones):
        mx = x_start + i * seg_w
        r = 3
        pdf.set_fill_color(*(JET_ORANGE if done else BORDER))
        pdf.ellipse(mx - r, y - r, r * 2, r * 2, style="F")

        above = (i % 2 == 0)
        if above:
            label_y = y - 22
        else:
            label_y = y + 6

        pdf.set_xy(mx - 18, label_y)
        pdf.set_font("Inter", "B", 8)
        pdf.set_text_color(*CHARCOAL)
        pdf.cell(36, 4, title, align="C", new_x="LEFT", new_y="NEXT")
        pdf.set_font("Inter", "", 7)
        pdf.set_text_color(*MID_TEXT)
        pdf.multi_cell(36, 3.5, detail, align="C")

        # Date label on opposite side
        date_y = y + 20 if above else y - 12
        pdf.set_xy(mx - 12, date_y)
        pdf.set_font("Inter", "", 6.5)
        pdf.set_text_color(*LIGHT_TEXT)
        pdf.cell(24, 3, date, align="C")
```

---

### METHODOLOGY_BOX

Subtle container for methodology, data sources, or notes. This is one of the few
components that uses a visible container, because it represents meta-information
that should be visually distinct from primary content.

**When to use**: Explaining data sources, methodology, caveats.

**IMPORTANT — always measure first**: Use `dry_run=True` to calculate actual text
height before drawing the background rect. Never hardcode `box_h` — content length
varies and hardcoded heights cause text to overflow or clip at the bottom edge.

```python
def draw_methodology_box(pdf, title, text):
    y = pdf.get_y()

    # Measure required height
    pdf.set_font("Inter", "", 7.5)
    lines = pdf.multi_cell(CONTENT_W - 14, 3.8, text, dry_run=True, output="LINES")
    text_h = len(lines) * 3.8
    box_h = text_h + 18  # padding for title + margins

    pdf.set_fill_color(*MOZZARELLA_T1)
    pdf.set_draw_color(*BORDER)
    pdf.rect(MARGIN, y, CONTENT_W, box_h, style="DF",
             round_corners=True, corner_radius=3)

    pdf.set_xy(MARGIN + 7, y + 5)
    pdf.set_font("Inter", "B", 8)
    pdf.set_text_color(*CHARCOAL)
    pdf.cell(0, 4, title.upper())

    pdf.set_xy(MARGIN + 7, y + 12)
    pdf.set_font("Inter", "", 7.5)
    pdf.set_text_color(*MID_TEXT)
    pdf.multi_cell(CONTENT_W - 14, 3.8, text)

    pdf.set_y(y + box_h + SPACE_SM)
```

---

### BADGE_ROW

Row of small rounded-rectangle pill labels for category/department tagging.

**When to use**: Showing department ownership, tags, categories.

```python
def draw_badge_row(pdf, badges, y=None):
    """Row of pill badges.

    badges: list of (label, bg_color, text_color) tuples
    """
    y = y or pdf.get_y()
    x = MARGIN

    for label, bg, tc in badges:
        pdf.set_font("Inter", "B", 7)
        text_w = pdf.get_string_width(label)
        badge_w = text_w + 8
        h = 6

        pdf.set_fill_color(*bg)
        pdf.rect(x, y, badge_w, h, style="F", round_corners=True, corner_radius=h / 2)

        pdf.set_xy(x, y)
        pdf.set_text_color(*tc)
        pdf.cell(badge_w, h, label, align="C")

        x += badge_w + 3

    pdf.set_y(y + 10)
```

**Variant 1 — Metadata pills** (document classification):
Use JET Orange background with White text **only** for cover-page metadata tags (report type, date, classification).
On inner pages, use Charcoal background with White text for badge defaults.

```python
# Cover page metadata pills (JET Orange)
metadata_badges = [
    ("SKILL OVERVIEW", JET_ORANGE, WHITE),
    ("SELF-TEST REPORT", JET_ORANGE, WHITE),
    ("MARCH 2026", JET_ORANGE, WHITE),
]
draw_badge_row(pdf, metadata_badges)

# Inner page badges (Charcoal — default)
inner_badges = [
    ("OVERVIEW", CHARCOAL, WHITE),
    ("Q1 2026", CHARCOAL, WHITE),
]
draw_badge_row(pdf, inner_badges)
```

**Variant 2 — Status tags** (feature readiness):
Use JET supporting colours as pill backgrounds with Charcoal text for status indicators.

```python
# Status indicators using JET supporting colours
status_items = [
    ("READY", SUCCESS, CHARCOAL),
    ("PLANNED", WARNING, CHARCOAL),
    ("BLOCKED", DANGER, CHARCOAL),
]
draw_badge_row(pdf, status_items)
```

**Variant 3 — Category badges** (colour-coded by category):
Use supporting brand colours to colour-code badges by category, team, or grouping.

```python
category_badges = [
    ("Customer UX", TURMERIC, CHARCOAL),
    ("Partner UX", BERRY, CHARCOAL),
    ("Logistics", LATTE, CHARCOAL),
    ("Operations", CUPCAKE, CHARCOAL),
]
draw_badge_row(pdf, category_badges)
```

**Composition rules**:
- Place badge rows below the section heading and above the key takeaway
- Maximum 4 badges per row (wrap to next line if more)
- Use consistent badge variant within a single row (don't mix metadata and department badges)
- Badge height: 6mm for standard, 5mm for compact in tables

---

### COLOUR_MATRIX

Grid of colour-coded cells for categorisation. No borders — colour fill only.

**When to use**: Mapping capabilities to departments, pattern coverage grids.

```python
def draw_colour_matrix(pdf, rows, category_colors):
    """Grid of coloured cells.

    rows: list of lists of (label, category) tuples
    category_colors: dict of category -> (accent, bg) colour tuples
    """
    cols = len(rows[0])
    cell_w = (CONTENT_W - (cols - 1) * SPACE_XS) / cols
    cell_h = 12
    y = pdf.get_y()

    for row_idx, row in enumerate(rows):
        for col_idx, (label, category) in enumerate(row):
            cx = MARGIN + col_idx * (cell_w + SPACE_XS)
            cy = y + row_idx * (cell_h + SPACE_XS)
            _, bg = category_colors[category]

            pdf.set_fill_color(*bg)
            pdf.rect(cx, cy, cell_w, cell_h, style="F",
                     round_corners=True, corner_radius=3)

            pdf.set_xy(cx, cy + 2.5)
            pdf.set_font("Inter", "B", 7)
            pdf.set_text_color(*CHARCOAL)
            pdf.cell(cell_w, 7, label, align="C")

    final_y = y + len(rows) * (cell_h + SPACE_XS)
    pdf.set_y(final_y + SPACE_SM)
```

---

### SOURCE_FOOTNOTE

Small italic attribution text below tables and charts.

**When to use**: Below every data visualisation or table.

```python
def source_footnote(self, text):
    self.ln(1)
    with self.local_context(text_color=LIGHT_TEXT):
        self.set_font("Inter", "", 7)
        self.cell(CONTENT_W, 3, text, new_x="LMARGIN", new_y="NEXT")
    self.ln(SPACE_XS)
```

---

### HYPERLINK

Clickable hyperlink text using JET Accessible Orange. This is the **one exception**
to the "never underline" rule — actual hyperlinks use underline to indicate interactivity.

**When to use**: Jira ticket references, GitHub Enterprise links, external URLs.

**Design rules**:
- Colour: `JET_ORANGE_TEXT` (#F36805) — the accessible interactive colour
- Underline: yes (exception to no-underline rule — this IS a hyperlink)
- Font: same weight and size as surrounding text
- Works with fpdf2's `cell(link=)` and `write(link=)` for clickable PDF links

```python
def draw_hyperlink(pdf, text, url, font_size=8, font_style=""):
    """Render a clickable hyperlink in JET Accessible Orange with underline.
    Call this inline within a text flow — it advances the cursor like cell()."""
    pdf.set_text_color(*JET_ORANGE_TEXT)
    pdf.set_font("Inter", font_style, font_size)
    link_w = pdf.get_string_width(text)
    y = pdf.get_y()
    x = pdf.get_x()
    pdf.cell(link_w, 4, text, link=url)
    # Draw underline manually (0.3pt, same colour)
    pdf.set_draw_color(*JET_ORANGE_TEXT)
    pdf.set_line_width(0.3)
    pdf.line(x, y + 4, x + link_w, y + 4)
    pdf.set_line_width(0.2)  # reset
```

**Inline usage** (within body text):

```python
# Write body text, then hyperlink, then more text
pdf.set_font("Inter", "", 8)
pdf.set_text_color(*DARK_TEXT)
pdf.write(4, "See ticket ")
draw_hyperlink(pdf, "JIRA-1234", "https://jira.justeattakeaway.com/browse/JIRA-1234", font_size=8)
pdf.write(4, " for details.")
pdf.ln(SPACE_SM)
```

**Table cell usage**:

```python
# Inside a table row, render a cell value as a clickable link
pdf.set_xy(x, row_y)
draw_hyperlink(pdf, "PR #456", "https://github.com/example/repo/pull/456", font_size=8)
```

---

## Container Components (Use Sparingly)

These components use visible containers. Only use when content genuinely benefits
from visual grouping.

### STAT_CARDS

Cards with large number, label, and optional delta. Use for cover page
KPIs or when metrics need strong visual grouping. Clean and minimal — no accent bars or decorative lines.

**When to use**: 3-4 metrics that need to stand out (cover page, executive summary hero stats).
**Prefer STAT_ROW** for inner pages where cards would feel heavy.

```python
def draw_stat_card(pdf, x, y, w, h, value, label, bg_color=MOZZARELLA_T1, delta=None):
    pdf.set_fill_color(*bg_color)
    pdf.set_draw_color(*BORDER)
    pdf.rect(x, y, w, h, style="DF", round_corners=True, corner_radius=4)

    CARD_PADDING = 4
    text_w = w - 2 * CARD_PADDING
    text_x = x + CARD_PADDING

    # Value (bold, prominent)
    pdf.set_xy(text_x, y + h * 0.22)
    pdf.set_font("InterExtraBold", "", 26)
    pdf.set_text_color(*CHARCOAL)
    pdf.cell(text_w, 12, value, align="C")

    # Label (regular weight, secondary)
    pdf.set_xy(text_x, y + h * 0.58)
    pdf.set_font("Inter", "", 7.5)
    pdf.set_text_color(*MID_TEXT)
    pdf.cell(text_w, 4, label, align="C")

    # Delta (optional)
    if delta:
        pdf.set_xy(text_x, y + h * 0.73)
        pdf.set_font("Inter", "B", 6.5)
        pdf.set_text_color(*JET_ORANGE)
        pdf.cell(text_w, 4, delta, align="C")
```

---

### NUMBERED_CARDS

The carded version of NUMBERED_COLUMNS. Only use when the numbered items need
visual containment (e.g., side by side with different background contexts).

**Prefer NUMBERED_COLUMNS** in most cases.

```python
def draw_numbered_cards(pdf, items):
    """Carded version of 01/02/03 columns. Clean design — no accent bars or coloured numbers.

    items: list of (number, heading, body) tuples
    """
    cols = len(items)
    gap = GUTTER
    w = grid_span(GRID_COLS // cols)  # Grid-aligned
    h = 55
    y = pdf.get_y()

    for i, (num, heading, body) in enumerate(items):
        x = MARGIN + i * (w + gap)

        pdf.set_fill_color(*MOZZARELLA_T1)
        pdf.set_draw_color(*BORDER)
        pdf.rect(x, y, w, h, style="DF", round_corners=True, corner_radius=4)

        # Number (Charcoal, not accent-coloured)
        pdf.set_xy(x + 6, y + 8)
        pdf.set_font("InterBlack", "", 28)
        pdf.set_text_color(*CHARCOAL)
        pdf.cell(w - 12, 14, num)

        # Heading
        pdf.set_xy(x + 6, y + 24)
        pdf.set_font("Inter", "B", 10)
        pdf.set_text_color(*CHARCOAL)
        pdf.cell(w - 12, 5, heading)

        # Body
        pdf.set_xy(x + 6, y + 31)
        pdf.set_font("Inter", "", 7.5)
        pdf.set_text_color(*DARK_TEXT)
        pdf.multi_cell(w - 12, 3.8, body, align="L")

    pdf.set_y(y + h + SPACE_MD)
```

---

### DATA_TABLE

Full-width table with alternating rows, Cupcake header with Charcoal text, and optional inline bars.

**When to use**: Tabular data with 3+ columns. See pdf-patterns.md for full implementation.

---

## Utility Components

### PROGRESS_BAR

Standalone rounded progress bar. Used inside other components.

```python
def draw_progress_bar(pdf, x, y, w, h, pct, bar_color=JET_ORANGE, track_color=BORDER):
    pdf.set_fill_color(*track_color)
    pdf.rect(x, y, w, h, style="F", round_corners=True, corner_radius=h / 2)
    if pct > 0:
        fill_w = max((pct / 100) * w, h)
        fill_w = min(fill_w, w)
        pdf.set_fill_color(*bar_color)
        pdf.rect(x, y, fill_w, h, style="F", round_corners=True, corner_radius=h / 2)
```

---

### SPARKLINE

Mini trend line for embedding in tables or cards.

```python
def sparkline(self, x, y, w, h, values, color=JET_ORANGE):
    if len(values) < 2:
        return
    mn, mx = min(values), max(values)
    rng = mx - mn or 1
    step = w / (len(values) - 1)
    points = [(x + i * step, y + h - ((v - mn) / rng) * h)
              for i, v in enumerate(values)]
    with self.local_context(draw_color=color, line_width=0.5):
        for i in range(len(points) - 1):
            self.line(points[i][0], points[i][1], points[i + 1][0], points[i + 1][1])
    self.set_fill_color(*color)
    self.ellipse(points[-1][0] - 0.75, points[-1][1] - 0.75, 1.5, 1.5, style="F")
```

---

## Component Composition Rules

1. **Maximum 3 component types per page** — don't mix too many patterns on one page.
2. **Always lead with KEY_TAKEAWAY** after a section heading.
3. **Use TLDR_BLOCK once per report** — first content page, immediately below section header.
4. **Use SOURCE_FOOTNOTE after every data visualisation** — tables, charts, status lists.
5. **Prefer open components** (NUMBERED_COLUMNS, STAT_ROW, PROGRESS_LIST, STATUS_LIST)
   over their carded equivalents.
6. **Cards are for emphasis** — use STAT_CARDS only for hero metrics, NUMBERED_CARDS
   only when items need strong visual separation.
7. **One QUOTE_BLOCK per page maximum** — quotes are accent elements, not primary content.
   Use vertical left accent bar, not top accent bar.
8. **NO underlines anywhere** — hierarchy is purely typographic (weight + scale).
   Section header bands (via `band_color`) are the exception — used on the first page of each major
   section to provide a strong visual section break without wasting a full page.
   The ONLY exception is the HYPERLINK component, which uses underline to indicate interactivity.
9. **NEVER use `__text__` markdown syntax** — fpdf2's `markdown=True` interprets `__text__`
   as underline, which renders as broken-hyperlink-style lines under body text. This is the
   **#1 most common visual defect** in generated reports. Use `**text**` for bold emphasis only.
   If you need to emphasise text, bold is the only acceptable option.
10. **Consistent x-offsets** — all content uses `CONTENT_X = MARGIN` (20mm). No `MARGIN + 5`
    shifts for body content. Title and content must share the same left margin.
11. **Whitespace is a feature** — 30-40% of each page should be empty. If a page feels
    cramped, remove a component rather than shrinking everything.
12. **Page-level colour unity** — maximum 2 accent colours per page. No "rainbow" effect.
13. **Always measure before drawing containers** — use `multi_cell(..., dry_run=True, output="HEIGHT")`
    to calculate text height before drawing any background rect or clipped region. Never hardcode
    box heights — content length varies and hardcoded heights cause text overflow or wasted space.
14. **Bold/highlight inversion prevention** — when using `markdown=True` with `**bold**` highlights,
    the base font MUST be regular weight (`Inter ""` or `Inter ""`), NEVER bold (`Inter "B"`).
    The `**` markers toggle the bold state — if the base is already bold, `**text**` turns bold OFF
    (rendering in regular weight), which is the opposite of the intended effect.
    - All-bold paragraph with no highlights → set `Inter "B"`, do NOT use `**markers**`
    - Regular paragraph with bold highlights → set `Inter ""`, use `**key phrases**`
    - This applies to KEY_TAKEAWAY, TLDR_BLOCK, BODY_TEXT, and any component using `markdown=True`
15. **Component names in Title Case** — when displaying component names in reports (e.g., in
    ranked lists, tables, or labels), use human-readable Title Case ("Body Text", "Key Takeaway",
    "Data Table") not the internal UPPER_SNAKE_CASE identifiers ("BODY_TEXT", "KEY_TAKEAWAY").
    The UPPER_SNAKE names in this file are code identifiers for agent reference only.
16. **Card-internal text must respect padding** — every `cell()` or `multi_cell()` inside a card
    must use `text_w = card_w - 2 * CARD_PADDING` (typically 4mm each side), never the raw `card_w`.
    Position text at `card_x + CARD_PADDING`. Center-alignment does NOT prevent clipping — `cell()`
    silently truncates text that exceeds the cell width regardless of alignment. This applies to
    STAT_CARDS, KPI rows (cover and inner-page), graph cards, and any custom card component.
17. **No mid-page whitespace voids** — content must flow top-down with only standard spacing
    tokens (`SPACE_SM`, `SPACE_MD`, `SPACE_LG`) between sections. Never use arbitrary `set_y()`
    calls that push content down the page, and never leave large gaps between components mid-page.
    Multi-column components (NUMBERED_COLUMNS, NUMBERED_CARDS, etc.) MUST set the cursor to
    `max_bottom + SPACE_MD` after drawing, where `max_bottom` is the bottom edge of the tallest
    column. Whitespace should accumulate at the page bottom only — a 20% void at the bottom is
    acceptable, but a 20% void between two sections mid-page is a layout defect.

---

## Official JET Visual Identity Style Guide

### Official Colour Palette

> **Canonical source**: `pdf-patterns.md` boilerplate section. If values differ between files, `pdf-patterns.md` is authoritative. This table is a read-only quick reference using official names from the JET Visual Identity Style Guide.

| Official Name | Constant | HEX | RGB | Usage |
|---|---|---|---|---|
| JET Orange | `JET_ORANGE` | `#FF8000` | (255, 128, 0) | Primary brand. Must appear in every communication. Covers, section header bands, logo badge |
| JET Accessible Orange | `JET_ORANGE_TEXT` | `#F36805` | (243, 104, 5) | WCAG compliant for orange text on white/Mozzarella backgrounds |
| Charcoal | `CHARCOAL` | `#242E30` | (36, 46, 48) | ALL text on light backgrounds. Never as page background or solid fill |
| Berry | `BERRY` | `#F2A6B0` | (242, 166, 176) | Supporting section background (rose/pink) |
| Turmeric | `TURMERIC` | `#F6C243` | (246, 194, 67) | Supporting section background (gold/yellow) |
| Cupcake | `CUPCAKE` | `#C1DADE` | (193, 218, 222) | Supporting section background (dusty teal) |
| Latte | `LATTE` | `#E7CDA2` | (231, 205, 162) | Supporting section background (beige/sand) |
| Aubergine | `AUBERGINE` | `#5B3D5B` | (91, 61, 91) | Highlights in product, use sparingly |
| Mozzarella | `MOZZARELLA` | `#EFEDEA` | (239, 237, 234) | Content page background (warm grey) |
| Mozzarella T1 | `MOZZARELLA_T1` | `#F5F3F1` | (245, 243, 241) | Card/container fill (light cream) |
| Mozzarella T2 | `MOZZARELLA_T2` | `#FCFCFC` | (252, 252, 252) | Near-white |

**Extended Light Palette** (secondary tints for highlights on supporting colours):

| Name | Constant | HEX | RGB | Usage |
|---|---|---|---|---|
| Light Orange | `LIGHT_ORANGE` | `#FDDFC3` | (253, 223, 195) | Highlights on orange sections |
| Light Berry | `LIGHT_PINK` | `#F9D2D7` | (249, 210, 215) | Highlights on Berry backgrounds |
| Light Turmeric | `LIGHT_YELLOW` | `#FAE0A1` | (250, 224, 161) | Highlights on Turmeric backgrounds |
| Light Cupcake | `LIGHT_BLUE` | `#E0ECEE` | (224, 236, 238) | Highlights on Cupcake backgrounds |
| Light Latte | `LIGHT_TAN` | `#F1E3C9` | (241, 227, 201) | Highlights on Latte backgrounds |

### Type Colour Rules (CRITICAL)

| Background | Allowed Text Colours |
|---|---|
| White / Mozzarella / Mozzarella Tints | Charcoal or JET Orange |
| Berry / Turmeric / Cupcake / Latte | **Charcoal ONLY** |
| JET Orange | **White ONLY** |
| Aubergine | **White ONLY** |

**NEVER set type in supporting colours** (Berry, Turmeric, Cupcake, Latte).

Use the `text_color_for_bg(bg)` helper to automatically determine correct text colour:

```python
text_c = text_color_for_bg(bg_color)  # Returns WHITE or CHARCOAL
```

### Colour Usage Rules

- JET Orange **must appear in every communication**
- **Never use two supporting colours together** — always pair one with JET Orange
- **Charcoal only for text and interactive elements** — never as a solid background
- **Aubergine**: only for highlights in product placements, use sparingly

### Bookend Principle (slide 031)

- Start and end on JET Orange (Cover + Closing pages)
- Minimum 20% of pages should use JET Orange background
- Supporting colours used in **sections**, not randomly

### Grid System (slide 032)

- 12-column grid
- **Margin** = 6% of shortest side (20mm for A4)
- **Gutter** = 45% of margin (9mm)
- Use `grid_span(n)` to get width for n columns (defined in `pdf-patterns.md` boilerplate)
- **ALWAYS use `grid_span()` for column widths** — never compute ad-hoc with `(CONTENT_W - gap) / n`
- **ALWAYS use `GUTTER` for inter-column gaps** — never bare numbers like `5` or `6`

```python
# Common layouts — use these patterns for multi-column content:
half_w    = grid_span(6)   # ≈80.5mm — 2-column layouts, card_gap=GUTTER
third_w   = grid_span(4)   # ≈50.7mm — 3-column layouts, col_gap=GUTTER
quarter_w = grid_span(3)   # ≈35.8mm — 4-column layouts, card_gap=GUTTER
```

### Key Layout Rules (from 177-slide PPTX review)

- **No borders/rules on content** — separation achieved through whitespace and colour contrast
- **Rounded corners everywhere** — ~8-12px radius on cards, fully rounded on pills
- **Warm backgrounds** — never pure white; use Mozzarella (#EFEDEA), Mozzarella T1, or T2
- **No logo on ANY page** — the JET logo/icon is NEVER placed on PDF report pages — not on the cover, not on content pages, not on the closing page. Brand presence comes exclusively from the JET Orange bookend pages and colour palette. The bundled logo image files are reference assets only and must NOT be embedded in generated PDFs
- **Thin 1.5mm JET Orange accent line** at very top of content pages — NOT a wide coloured band
- **Footer format:** `[page#] | Month Year | **Title of project**` with horizontal rule above, pipe-separated, at page bottom
- **Maximum 2 accent colours per page** — no rainbow effect
- **30-40% of each page should be whitespace** — if cramped, remove a component rather than shrinking
- **Avoid excessive bottom whitespace** — aim for 85-95% page utilization on content pages. If >20% of the page is empty at the bottom, add a callout, key takeaway, or source footnote to fill the space rather than leaving a visible void above the footer
- **No mid-page gaps** — all inter-section spacing must use standard tokens (`SPACE_SM`/`SPACE_MD`/`SPACE_LG`). If a multi-column component (NUMBERED_COLUMNS, NUMBERED_CARDS) leaves the cursor partway up the page, the next section will appear to "float" far below. Every draw function MUST reposition the cursor to the bottom of its tallest element + `SPACE_MD` before returning

### Layout Templates (from 177-slide PPTX review)

1. **Cover/Title** — Left text (badge + title + subtitle + footer) / Right product imagery, ~45/55 split, JET Orange background
2. **Section Header Band** — Coloured band (~25mm) at top of first page in each section, containing section title + number + doc metadata
3. **Content (with band)** — Mozzarella background with coloured header band at top, content below
4. **Content** — Warm grey bg, title top-left, footer bottom-left
5. **Two-column content** — ~55/45 or ~60/40 splits, text left, image/visual right
6. **Three-column content** — Equal columns with optional cards (rounded-rect, lighter fill, no border)
7. **Card grids** — 2x2, 3x2, bento layouts with rounded-corner cards
8. **Data tables** — Colour-coded columns/rows, rounded-corner cells, no grid lines
9. **KPI cards** — Tinted backgrounds (green=positive, pink=negative), large numbers, trend arrows
10. **Timeline/process flows** — Horizontal bars with alternating above/below callouts, chevron arrows
11. **Quote/testimonial cards** — Speech-bubble shapes with triangular tails
12. **Sidebar layouts** — Coloured left panel (25-30%) + grey content area (70-75%)
13. **Closing/Thank You** — Full-bleed orange, centred white bold-italic "Thank you", no chrome

### Typography Leading

| Usage | Leading | Constant |
|---|---|---|
| Headlines (<40 chars) | 85% | `LEADING_HEADLINE` |
| Subheadings/CTA | 100% | `LEADING_SUBHEAD` |
| Body copy | 120% | `LEADING_BODY` |

Use `line_h(font_size, leading)` to compute line height in mm.

### Definitive Font Sizes (from PPTX slide 33)

| Element | Font | Size | Weight |
|---|---|---|---|
| Page divider title | Inter | 36pt | Black |
| Cover headlines | Inter | 25pt | Black |
| Long text headlines | Inter | 19pt | Bold |
| Subtitles | Inter | 11pt | Bold |
| Body text | Inter | 11pt | Regular |
| Footer | Inter | 8pt | Regular/Bold |
| Sources/footnotes | Inter | 7pt | Regular |

**Default alignment:** Left-aligned, sentence case
**Line spacing:** 1.15
**Text colour rule:** Always Charcoal (#242E30) on light backgrounds, White on orange/dark backgrounds

### Additional Components

#### CALLOUT_BOX

Informational callout with left accent bar. Uses clipping-path technique.
Height is auto-calculated from content using `multi_cell(..., dry_run=True, output="HEIGHT")` — ensures symmetric top/bottom padding.
See `pdf-patterns.md` → "Callout Box" for full implementation.

```python
draw_callout(
    pdf,
    title="Important Note",
    body="Details about the note.",
    accent_color=JET_ORANGE,
    bg_color=MOZZARELLA_T1,
    icon_char=None,  # optional leading character
)
```

**When to use**: Highlighting important information, warnings, or notes.
**Rules**: Text colour follows JET type colour rules automatically.

#### DIVIDER

Subtle horizontal rule for separating content sections.
See `pdf-patterns.md` → "Divider" for full implementation.

```python
draw_divider(pdf, color=BORDER, thickness=0.5, margin_y=SPACE_SM)
```

**When to use**: Between logical sections on the same page. Use sparingly — JET style guide prefers whitespace.

#### COLOUR_BLOCK

Solid colour section spanning a fraction of the page width.
See `pdf-patterns.md` → "Colour Block" for full implementation.

```python
draw_colour_block(
    pdf,
    title="Section Title",
    body_text="Description text.",
    bg_color=JET_ORANGE,
    ratio=0.333,      # 1/3 of page width
    full_width=True,   # edge-to-edge or within margins
)
```

**When to use**: Section transitions, visual breaks, emphasis blocks.
**Rules**: Ratios should be 1/3 or 1/4 per style guide. Text colour automatic.

#### CHECKLIST

Checklist with checkmark (✓) and cross (✗) icons for pass/fail status.

```python
checklist = [
    ("Feature A", True),   # ✓ orange checkmark, regular text
    ("Feature B", False),  # ✗ grey cross, grey italic text
]
check_row_h = 8
for label, done in checklist:
    y = pdf.get_y()
    icon_color = JET_ORANGE if done else BORDER
    icon_text = "\u2713" if done else "\u2717"
    pdf.set_xy(CONTENT_X, y)
    pdf.set_font("Inter", "B", 10)
    pdf.set_text_color(*icon_color)
    pdf.cell(6, check_row_h, icon_text)
    pdf.set_xy(CONTENT_X + 7, y)
    pdf.set_font("Inter", "" if done else "I", 8)
    pdf.set_text_color(*(CHARCOAL if done else LIGHT_TEXT))
    pdf.cell(CONTENT_W - 7, check_row_h, label)
    pdf.ln(check_row_h)
```

**When to use**: Status lists where most items are complete. Better than progress bars when everything is 100%.

#### SPLIT_PANEL

60/40 layout with a supporting colour panel on the left and content on the right.
Used in executive summary pages for visual warmth.

```python
def draw_split_panel(pdf, left_content_fn, right_content_fn, 
                     panel_color=LATTE, split=0.4):
    """Draw a 60/40 split layout with coloured left panel.
    
    left_content_fn: callable(pdf, x, y, w, h) to draw left panel content
    right_content_fn: callable(pdf, x, y, w, h) to draw right panel content
    panel_color: supporting colour for left panel background
    split: fraction of CONTENT_W for the left panel (default 0.4)
    """
    y = pdf.get_y()
    panel_w = CONTENT_W * split
    content_w = CONTENT_W * (1 - split) - 5  # 5mm gap
    panel_h = 60  # adjust based on content
    
    # Coloured left panel
    pdf.set_fill_color(*panel_color)
    pdf.rect(MARGIN, y, panel_w, panel_h, style="F",
             round_corners=True, corner_radius=4)
    
    left_content_fn(pdf, MARGIN + 6, y + 6, panel_w - 12, panel_h - 12)
    right_content_fn(pdf, MARGIN + panel_w + 5, y, content_w, panel_h)
    
    pdf.set_y(y + panel_h + SPACE_MD)
```

**When to use**: Executive summary pages, key findings with supporting visual.
**Rules**: Only ONE supporting colour per split panel. Never pair two supporting colours.

#### COLOURED_TABLE_HEADER

Table header row using Cupcake background with Charcoal text, replacing the old
dark header style.

```python
# Table header with Cupcake background
pdf.set_fill_color(*CUPCAKE)
pdf.set_text_color(*CHARCOAL)
pdf.set_font("Inter", "B", 8)
for i, (label, w) in enumerate(zip(headers, col_widths)):
    pdf.cell(w, TABLE_HEADER_H, f"  {label}", fill=True,
             new_x="RIGHT", new_y="TOP")
pdf.ln(TABLE_HEADER_H)
```

**When to use**: All data tables. This is the standard header style.
**Rules**: Always use Cupcake (#C1DADE) background with Charcoal (#242E30) text.

#### STATUS_CARD

Tinted card for highlighting outstanding items, blockers, or warnings.
Uses Berry or Light Berry background with a left accent bar.

```python
def draw_status_card(pdf, title, items, accent_color=BERRY, 
                     bg_color=LIGHT_PINK):
    """Card for outstanding items or warnings."""
    y = pdf.get_y()
    item_h = 6
    box_h = 14 + len(items) * item_h
    cr = 3
    bar_w = 2.5

    _rounded_rect_clip(pdf, MARGIN, y, CONTENT_W, box_h, cr)
    pdf.set_fill_color(*accent_color)
    pdf.rect(MARGIN, y, bar_w, box_h, style="F")
    pdf.set_fill_color(*bg_color)
    pdf.rect(MARGIN + bar_w, y, CONTENT_W - bar_w, box_h, style="F")
    _restore_gfx_state(pdf)  # restore state + re-sync colour cache

    pdf.set_xy(MARGIN + 8, y + 4)
    pdf.set_font("Inter", "B", 9)
    pdf.set_text_color(*CHARCOAL)
    pdf.cell(0, 5, title)

    for i, item in enumerate(items):
        pdf.set_xy(MARGIN + 8, y + 12 + i * item_h)
        pdf.set_font("Inter", "", 8)
        pdf.set_text_color(*CHARCOAL)
        pdf.cell(0, item_h, f"- {item}")

    pdf.set_y(y + box_h + SPACE_SM)
```

**When to use**: Outstanding items, blockers, risk summaries.
**Rules**: Use Berry accent for warnings/blockers. Use Turmeric for neutral highlights.

#### COLOURED_BACKGROUND_PAGE

Content page with a full supporting-colour background instead of the default Mozzarella.
Use `content_page(bg_color=...)` to set a supporting colour for the entire page background.

```python
# Latte background page
pdf.content_page(bg_color=LATTE)
pdf.section_heading("Market Context")
# ... draw content with Charcoal text (automatic on supporting colours)

# Cupcake background page
pdf.content_page(bg_color=CUPCAKE)
pdf.section_heading("Technical Details")
```

**When to use**: To add visual variety within a section while maintaining the warm,
branded feel. Use for 1-2 pages per section maximum — most pages should be Mozzarella.
**Rules**:
- Only ONE supporting colour per page
- Use Charcoal text on all supporting colour backgrounds
- Never combine two supporting colours on the same page
- Group supporting-colour pages together in a section (don't randomly alternate)
