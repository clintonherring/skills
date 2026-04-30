# Known Gotchas and Error Handling

> **Purpose**: Detailed fpdf2 gotchas, error handling patterns, and defensive coding techniques for JET PDF reports. See SKILL.md for the critical gotchas that must be kept top-of-mind.

## Known Gotchas

### CRITICAL: local_context(font_size=) Uses Millimetres, Not Points

`local_context(font_size=X)` interprets X as **millimetres** and converts to points internally (1mm ≈ 2.8346pt). This means `font_size=15` renders at ~42.5pt, not 15pt.

```python
# WRONG -- renders at ~42.5pt (15mm converted to points)
with pdf.local_context(font_size=15):
    pdf.cell(0, 8, "This text is 42.5pt, not 15pt!")

# CORRECT -- renders at 15pt
pdf.set_font("Inter", "B", 15)
pdf.cell(0, 8, "This text is 15pt")
```

**Rule**: Use `set_font()` for font sizing. Use `local_context()` only for non-font properties that do not involve unit conversion:
- `text_color`, `fill_color`, `draw_color`
- `fill_opacity`, `blend_mode`
- `line_width`, `dash_pattern`
- `font_style` (safe: "B", "I", "BI", "")
- `font_family` (safe: "Helvetica", etc.)

`set_font()` inside a `local_context()` block works correctly AND reverts when the context exits — so you get scoped sizing without the mm-to-pt conversion bug.

### solid_arc() at 360 Degrees Leaves a Visible Gap

`solid_arc(cx, cy, r, 0, 360)` does NOT render a clean filled circle -- it leaves a visible crescent/gap artifact. Use `ellipse()` for full circles instead:

```python
# WRONG -- visible gap at the seam
pdf.solid_arc(cx, cy, r, 0, 360, style="F")

# CORRECT -- clean filled circle
pdf.ellipse(cx - r, cy - r, r * 2, r * 2, style="F")
```

Only use `solid_arc()` for partial arcs (< 360 degrees). For the pie chart pattern: use `ellipse()` for the background track, and `solid_arc()` only for the value arc.

### Inter Font Supports Full Unicode

Inter (registered via `add_font()` with TTF files) supports the full Unicode character set including:
- En-dash `\u2013`, em-dash `\u2014`, curly quotes, arrows, check marks
- All Latin extended characters for European languages

Helvetica (the built-in fpdf2 fallback) does NOT support Unicode. If you must use Helvetica, avoid Unicode characters:
- Use hyphen `-` instead of en-dash
- Use ` - ` instead of em-dash
- Use straight quotes instead of curly quotes

**Always prefer Inter** -- it's the JET brand font AND it handles Unicode correctly.

### Float Font Sizes Are Fine

fpdf2 accepts float values for font sizes at runtime (e.g. `set_font("Helvetica", "", 6.5)`). LSP/type checkers may flag this as an error because the type stub says `int`. **Ignore these warnings** - they are false positives.

### KPI Cards Must Use Fixed Y Position

When drawing multiple KPI cards in a row, use a fixed `card_y` variable for all cards. **Do NOT use `pdf.get_y()`** - it drifts after each card is drawn, causing misalignment.

### Rounded Rectangles

fpdf2 supports rounded corners on `rect()`:

```python
pdf.rect(x, y, w, h, style="F", round_corners=True, corner_radius=3)
```

Both `round_corners=True` and a `corner_radius` value are required.

### Manual Pagination

Since `auto_page_break` is disabled, you must check page overflow manually before each table row:

```python
if pdf.get_y() + ROW_H > MAX_Y:
    pdf.add_page()
    pdf.continuation_header(...)
```

### CRITICAL: cell() Silently Truncates Long Text

`cell(w, h, text)` clips text that exceeds the cell width — **no error, no warning, no wrapping**. The text simply disappears at the boundary. This is the #1 cause of headings being cut off mid-word (e.g., "...TypeScript and Java lead for com" instead of "...completions").

**Centred text overflow**: `cell(w, h, text, align="C")` is even worse — when text is wider than the cell, it overflows **both** the left and right edges symmetrically, bleeding past page margins. This causes titles to be clipped on both sides (e.g., "rlands Order Volume by Region and City (Last 90" instead of "Netherlands Order Volume by Region and City (Last 90 Days)").

```python
# WRONG — clips long titles silently
pdf.set_font("Inter", "B", 15)
pdf.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")

# WRONG — centred text overflows both margins when too wide
pdf.set_font("InterBlack", "", 25)
pdf.cell(CONTENT_W, 10, title, align="C", new_x="LMARGIN", new_y="NEXT")

# CORRECT — wraps to next line if needed
pdf.set_font("Inter", "B", 15)
pdf.multi_cell(CONTENT_W, 8, title, new_x="LMARGIN", new_y="NEXT")

# CORRECT — centred title wraps within margins
pdf.set_font("InterBlack", "", 25)
pdf.multi_cell(CONTENT_W, 10, title, align="C", new_x="LMARGIN", new_y="NEXT")
```

**Rule**: Use `multi_cell()` for any text that could exceed the available width — especially section headings, insight titles, centred titles, and chart titles. `cell()` is only safe for short, fixed-length labels (dates, numbers, short status text).

For titles that must stay on one line, measure first and shrink:

```python
title_w = pdf.get_string_width(title)
if title_w > CONTENT_W:
    ratio = CONTENT_W / title_w
    pdf.set_font("Inter", "B", int(15 * ratio))
```

### CRITICAL: Footer/Content Collision in Draw Loops

When `auto_page_break` is disabled, content drawn past `MAX_Y` overlaps the footer. This happens when draw loops (chart rows, table rows, list items) check overflow only once at the start instead of before **every** item.

```python
# WRONG — only checks once, remaining rows overflow past footer
if pdf.get_y() + total_chart_h > MAX_Y:
    pdf.add_page()
for i, row in enumerate(data):
    draw_row(row)  # rows 8-12 may overlap footer

# CORRECT — check before EVERY row
for i, row in enumerate(data):
    if pdf.get_y() + ROW_H > MAX_Y:
        pdf.add_page()
        draw_continuation_header()
    draw_row(row)
```

**Rule**: Every loop that draws variable-length content must check `pdf.get_y() + item_h > MAX_Y` before each iteration. This applies to chart bars, table rows, list items, and grid tiles.

### Status Dot Colours — Always Use traffic_light()

`set_fill_color()` requires an RGB tuple `(r, g, b)`. Passing a string like `"green"` doesn't raise an error — it silently renders black. **Always use `pdf.traffic_light(x, y, status)`** which maps status strings to proper RGB values internally.

```python
# WRONG — renders black dot, "green" is not an RGB tuple
pdf.set_fill_color("green")
pdf.ellipse(x, y, 3, 3, style="F")

# CORRECT — uses the built-in colour mapping
pdf.traffic_light(x, y, "green")  # maps to TL_GREEN = (34, 197, 94)
```

Never draw status dots manually. The `traffic_light()` method handles the colour mapping:
```python
colours = {
    "green": TL_GREEN, "orange": TL_ORANGE,
    "red": TL_RED, "gray": TL_GRAY, "grey": TL_GRAY,
}
```

### Two-Column Y Alignment

Side-by-side elements (charts, cards, tables) must start at the same Y position. fpdf2 moves the cursor after each draw, so the second column starts lower than the first unless you explicitly save and restore Y.

```python
# WRONG — second column starts below the first
draw_left_chart()   # cursor moves down
draw_right_chart()  # starts at wrong Y

# CORRECT — anchor both columns to same Y
start_y = pdf.get_y()

# Draw left column
pdf.set_xy(left_x, start_y)
draw_left_chart()
left_end_y = pdf.get_y()

# Draw right column at same Y
pdf.set_xy(right_x, start_y)
draw_right_chart()
right_end_y = pdf.get_y()

# Resume below the tallest column
pdf.set_y(max(left_end_y, right_end_y))
```

**Rule**: For any two-column layout, save `start_y = pdf.get_y()` before drawing column 1, then `pdf.set_xy(right_x, start_y)` before column 2. After both columns, `pdf.set_y(max(col1_end_y, col2_end_y))`.

### Fixed-Width Label Truncation

`cell(55, h, name)` clips labels longer than 55mm. This causes bold capability names to merge with description text (e.g., "**BUG INVESTIGATIO**Nads logs, traces..." instead of "**BUG INVESTIGATION** — Reads logs, traces...").

```python
# WRONG — clips "JIRA TICKET MANAGEMENT" at 55mm, remaining chars merge with description
pdf.set_font("Inter", "B", 8)
pdf.cell(55, row_h, name)          # clipped at 55mm
pdf.set_font("Inter", "", 7.5)
pdf.cell(remaining_w, row_h, description)  # starts with leftover chars from name

# CORRECT — measure first, use adequate width
name_w = max(70, pdf.get_string_width(name) + 4)
pdf.set_font("Inter", "B", 8)
pdf.cell(name_w, row_h, name)
pdf.set_font("Inter", "", 7.5)
pdf.cell(CONTENT_W - name_w - dot_col_w, row_h, f"\u2014 {description}")
```

**Rule**: Never hardcode column widths for variable-length text labels. Either measure with `get_string_width()` and add padding, or use `multi_cell()` with wrapping. Always verify the longest label fits within the column width.

### Bare-Number Spacing and Ad-Hoc Column Widths

Using bare numbers for component gaps (e.g., `card_gap = 6`) and computing column widths with ad-hoc formulas (e.g., `(CONTENT_W - gap) / 2`) leads to inconsistent spacing across pages and columns that don't align to the grid. Different sections end up with different gap sizes, breaking the visual rhythm.

```python
# WRONG — bare numbers for gaps, ad-hoc width calculation
CARD_GAP = 6
CARD_W = (CONTENT_W - CARD_GAP) / 2
step_w = (CONTENT_W - 2 * SPACE_MD) / 3
kpi_gap = 5
kpi_w = (CONTENT_W - (4 - 1) * kpi_gap) / 4

# CORRECT — grid_span() for widths, named tokens for gaps
CARD_GAP = GUTTER                  # 9mm for column-to-column gaps
CARD_W = grid_span(6)              # 2-column layout
step_w = grid_span(4)              # 3-column layout
kpi_gap = GUTTER
kpi_w = grid_span(3)               # 4-column layout
```

Similarly, use named spacing tokens for vertical gaps:

```python
# WRONG — bare numbers for vertical spacing
pdf.ln(4)
pdf.ln(10)
pdf.ln(12)
pdf.set_y(kpi_y + kpi_h + 6)   # bare number in set_y() offset

# CORRECT — named spacing tokens
pdf.ln(SPACE_SM)   # 4mm
pdf.ln(SPACE_MD)   # 8mm, or SPACE_MD + SPACE_XS for 10mm
pdf.ln(SPACE_LG)   # 12mm
pdf.set_y(kpi_y + kpi_h + SPACE_SM)   # named token in set_y() offset
```

**Watch for `set_y()` arithmetic**: bare numbers hide inside `pdf.set_y(y + h + N)` just as easily as inside `pdf.ln(N)`. Both must use named spacing tokens.

**Exception for dense lists**: In compact layouts (8+ row status lists, compact tile grids), spacing between rows may go below `SPACE_XS` (2mm) to fit content. Use `1` or `1.5` as explicit values with a comment explaining the exception: `pdf.ln(1)  # sub-SPACE_XS: dense list`. This is preferable to reducing font size below readability thresholds.

**Rule**: Use `GUTTER` for horizontal inter-column gaps and `grid_span(n)` for column widths (matching the 12-column grid system — see Rule #14). Use `SPACE_*` tokens for vertical inter-component gaps. Never use bare numbers for spacing.

### table() API Requires headings_style

When using `pdf.table()` with `first_row_as_headings=True` (the default), you must provide `headings_style`. Use the `TABLE_HEADING_STYLE` constant from the boilerplate:

```python
from fpdf.fonts import FontFace
TABLE_HEADING_STYLE = FontFace(color=CHARCOAL, fill_color=CUPCAKE, emphasis="BOLD", size_pt=8)
```

Note: When using Inter with the `table()` API, the `FontFace` `emphasis="BOLD"` will use the bold variant of whatever font family is currently active. Set `pdf.set_font("Inter", "", 8)` before calling `pdf.table()` so the bold variant resolves to Inter Bold.

## Error Handling

### Empty or Missing Data

Always guard against empty datasets before rendering components:

```python
# Guard for empty data
if not items:
    pdf.set_font("Inter", "I", 9)
    pdf.set_text_color(*MUTED_TEXT)
    pdf.cell(CONTENT_W, 8, "No data available", align="C")
    pdf.ln(SPACE_MD)
    return  # or continue to next section
```

### Page Overflow

Since `auto_page_break` is disabled, always check before drawing anything with a known height:

```python
needed_h = card_h + SPACE_MD  # height of what you're about to draw
if pdf.get_y() + needed_h > MAX_Y:
    pdf.add_page()
```

For components that iterate (tables, lists, grids), check at the start of **every row/item**, not just once.

### Box Sizing — Always Measure Before Drawing

Text breaking out of its containing box is a critical visual defect. **Always use `dry_run=True`** to measure content height before drawing the container:

```python
# WRONG — guessing box height
box_h = 30  # hardcoded, will break with longer text

# CORRECT — measure actual content height
pdf.set_font("Inter", "", 8)
body_h = pdf.multi_cell(text_w, 3.5, body, dry_run=True, output="HEIGHT")
box_h = pad_y + title_h + body_h + pad_y  # symmetric padding
```

For callout boxes, TLDR blocks, methodology boxes, and any component with variable text:
1. Measure the text height with `dry_run=True, output="HEIGHT"`
2. Add symmetric padding (`pad_y` top and bottom)
3. Check if the total height fits on the current page (`pdf.get_y() + box_h > MAX_Y`)
4. If not, start a new page before drawing

### Font File Not Found

If Inter font files are missing, fpdf2 raises `FileNotFoundError`. The fonts are bundled at `references/fonts/`. Use an absolute path or `os.path.dirname(__file__)` relative path:

```python
import os
FONT_DIR = os.path.expanduser("~/.agents/skills/jet-report/references/fonts")
if not os.path.isdir(FONT_DIR):
    raise FileNotFoundError(f"Font directory not found: {FONT_DIR}")
```

### Input Validation

For percentage-based components (progress bars, pie charts), clamp values:

```python
pct = max(0, min(100, pct))  # clamp to 0-100
```

For text that might be `None`:

```python
title = title or ""
description = description or "—"
```

### Graceful Degradation

When a component fails (e.g., image not found, unexpected data shape), render a placeholder rather than crashing:

```python
try:
    pdf.image(img_path, x, y, w)
except Exception:
    # Draw a placeholder box
    pdf.set_fill_color(*MOZZARELLA_T1)
    pdf.rect(x, y, w, h, style="F", round_corners=True, corner_radius=3)
    pdf.set_xy(x, y + h / 2 - 3)
    pdf.set_font("Inter", "I", 8)
    pdf.set_text_color(*MUTED_TEXT)
    pdf.cell(w, 6, "[Image not available]", align="C")
```

---

### Grid/Multi-Row Component Page Overflow

**Symptom**: A 2×2 (or larger) grid of cards renders the first row on one page and the remaining row(s) on the next page. The overflow page shows 1-2 orphaned cards with ~60% empty whitespace, and the section header band is repeated.

**Root cause**: The per-card page-break check (`if cy + card_h > MAX_Y: add_page()`) fires mid-grid when there isn't enough vertical space for the second row. The grid starts too far down the page because preceding content (status lists, sub-headings, spacing) consumed too much vertical space.

**Why it's bad**: An orphaned row with massive whitespace is one of the most visually jarring layout defects. It also pushes all subsequent pages down by one, potentially causing the closing page to become page N+1 instead of page N.

**Fix**: Add a pre-flight height check before rendering the grid (Rule #27):

```python
num_rows = (len(items) + cols - 1) // cols
total_grid_h = num_rows * (card_h + row_gap) - row_gap

if pdf.get_y() + total_grid_h > MAX_Y and MARGIN + total_grid_h <= MAX_Y:
    # Grid won't fit here but WILL fit on a fresh page
    pdf.add_page()
```

If the grid won't fit even on a fresh page, either:
- Reduce `card_h` (e.g., from 60 to 48) and `pie_r` proportionally
- Split items into two separate grids with explicit sub-headings between them

**Applies to**: `draw_graph_card_grid()`, any custom tile/icon grid, and any component that renders items in a row×column layout. Always pre-measure total height before starting multi-row rendering.

### Card-Internal Text Clipping

**Symptom**: Text inside a card (KPI card, graph card, stat card) is visually clipped at the card's right edge. Titles like "Blockchain Sandwich" or labels like "Avg Resolution Time" are truncated with no warning. The card renders correctly in shape — only the text overflows.

**Root cause**: Text is rendered with `cell(card_w, h, text, align="C")` where `card_w` is the full card width. The cell's drawing region extends to the card's exact edge — there is zero internal padding. With center-aligned short text this looks fine, but longer text hits the boundary and `cell()` silently clips it.

**Why it's bad**: `cell()` never raises an error or warning when text exceeds the cell width. The clipping is invisible during code review — it only shows up visually in the rendered PDF, and only when a label is long enough to exceed the unpadded width.

```python
# WRONG — text width = full card width, no padding
pdf.set_xy(card_x, card_y + 5)
pdf.cell(card_w, 10, value, align="C")         # clips at card edge
pdf.set_xy(card_x, card_y + 16)
pdf.cell(card_w, 4, label, align="C")           # clips at card edge

# CORRECT — inset text by CARD_PADDING on both sides
CARD_PADDING = 4
text_w = card_w - 2 * CARD_PADDING
pdf.set_xy(card_x + CARD_PADDING, card_y + 5)
pdf.cell(text_w, 10, value, align="C")          # safe inner width
pdf.set_xy(card_x + CARD_PADDING, card_y + 16)
pdf.cell(text_w, 4, label, align="C")           # safe inner width
```

**Rule**: Every `cell()` or `multi_cell()` inside a card must use a text width of `card_w - 2 * CARD_PADDING` (or equivalent), never the raw `card_w`. Position text at `card_x + CARD_PADDING`. This applies to all card types: STAT_CARDS, KPI rows (cover and inner), graph cards, numbered cards, and any custom card component. Center-alignment does NOT protect against clipping — it only shifts where the clipping occurs.

### Horizontal Bar Overflow

**Symptom**: A horizontal bar in a chart card or inline data table extends past the card edge or column boundary. The count label next to the bar may also be clipped or overflow outside the card.

**Root cause**: Bar width is calculated as `(value / max_value) * bar_max_w` without clamping. When `value == max_value`, the bar fills the full allocated width, but the count label placed at `bar_x + bar_w + 2` has no room. If data anomalies cause `value > max_value`, the bar itself overflows.

**Fix**: Always clamp bar width after calculation:

```python
bar_w = (count / max_val) * bar_max_w
bar_w = min(bar_w, bar_max_w)  # clamp to allocated width
```

For count labels placed beside bars, clamp the label position so it stays inside the card:

```python
count_x = min(bar_x + bar_w + 2,
              card_x + CARD_W - CARD_PADDING - 12)
pdf.set_xy(count_x, row_y + 1)
```

For progress bar fill widths, apply both a minimum (for rounded corners) and a maximum (to stay within the track):

```python
fill_w = max((pct / 100) * bar_w, bar_h)  # min for proper rounding
fill_w = min(fill_w, bar_w)                # clamp to track width
```

**Note**: The `draw_progress_bar()` helper already does this correctly with `fill_w = min(fill_w, w)`. Apply the same pattern to all inline bar calculations — side-by-side chart cards, data tables with inline bars, and PROGRESS_LIST components.
