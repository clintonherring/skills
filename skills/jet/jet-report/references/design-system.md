# JET Report Design System Reference

> **Purpose**: Complete colour palette, typography scale, spacing system, accessibility rules, and layout conventions for JET PDF reports. This is the encyclopedic reference — see SKILL.md for the condensed runbook.

## JET Colour Palette

> Canonical Python definitions are in `pdf-patterns.md` (boilerplate section). This is a quick reference.

```python
# ── Primary brand ──────────────────────────────────────────────────
JET_ORANGE        = (255, 128, 0)      # #FF8000 - Primary brand, bookend pages, accent bars
JET_ORANGE_TEXT   = (243, 104, 5)      # #F36805 - WCAG-accessible orange for text on light backgrounds

# ── Text hierarchy ─────────────────────────────────────────────────
CHARCOAL   = (36, 46, 48)             # #242E30 - Headings, body text (14.3:1). ONLY for text, never bg.
DARK_TEXT   = (50, 50, 55)             # #323237 - Body text (12.6:1)
MID_TEXT    = (89, 89, 89)             # #595959 - Secondary text, labels (7.0:1 WCAG AA)
LIGHT_TEXT  = (158, 158, 158)          # #9E9E9E - Metadata, decorative (3.5:1)
MUTED_TEXT  = (176, 171, 171)          # #B0ABAB - Out-of-scope / greyed text
WHITE       = (255, 255, 255)          # Text on orange/dark backgrounds

# ── Neutral surfaces (official JET names) ─────────────────────────
MOZZARELLA    = (239, 237, 234)        # #EFEDEA - Primary warm background
MOZZARELLA_T1 = (245, 243, 241)       # #F5F3F1 - Card/container fill
MOZZARELLA_T2 = (252, 252, 252)       # #FCFCFC - Near-white background
BORDER        = (220, 218, 214)        # Warm-toned dividers, borders

# ── Supporting brand colours (structural use — backgrounds, content cards) ──
BERRY     = (242, 166, 176)            # #F2A6B0 - Pink, for status/alert cards
TURMERIC  = (246, 194, 67)             # #F6C243 - Golden yellow, for accents and outliers
CUPCAKE   = (193, 218, 222)            # #C1DADE - Blue-green, for table headers and bars
LATTE     = (231, 205, 162)            # #E7CDA2 - Warm beige, for full-page backgrounds

# ── Extended light palette (tints of supporting colours) ──────────
LIGHT_ORANGE = (253, 223, 195)         # #FDDFC3 - Light JET Orange tint
LIGHT_PINK   = (249, 210, 215)         # #F9D2D7 - Light Berry tint
LIGHT_YELLOW = (250, 224, 161)         # #FAE0A1 - Light Turmeric tint
LIGHT_BLUE   = (224, 236, 238)         # #E0ECEE - Light Cupcake tint
LIGHT_TAN    = (241, 227, 201)         # #F1E3C9 - Light Latte tint

# ── Restricted colours ────────────────────────────────────────────
AUBERGINE = (91, 61, 91)              # #5B3D5B - ONLY for highlights in product placements

# ── Traffic light / status colours ─────────────────────────────────
# True traffic light colours for instant visual recognition.
# Warm-toned variants that sit comfortably alongside the JET palette.
TL_GREEN   = (34, 197, 94)              # #22C55E - done, healthy, ready
TL_ORANGE  = (255, 146, 0)              # #FF9200 - in progress, warning, degraded
TL_RED     = (239, 68, 68)              # #EF4444 - blocked, critical, failed
TL_GRAY    = (156, 163, 175)            # #9CA3AF - to do, inactive, N/A

# Semantic aliases
SUCCESS    = TL_GREEN
WARNING    = TL_ORANGE
DANGER     = TL_RED
INFO       = TL_ORANGE  # Intentionally same as WARNING — both use orange for visibility
MUTED      = TL_GRAY

# Status tint backgrounds (light washes for row/card backgrounds)
SUCCESS_BG = (220, 252, 231)            # #DCFCE7 - light green wash
WARNING_BG = (255, 237, 213)            # #FFEDD5 - light orange wash
DANGER_BG  = (254, 226, 226)            # #FEE2E2 - light red wash
INFO_BG    = (255, 237, 213)            # #FFEDD5 - light orange wash (same as WARNING_BG — intentional)
ALT_ROW    = (245, 243, 241)           # = MOZZARELLA_T1

# Bar chart gradients (10 steps each, from saturated to light)
BAR_COLORS_ORANGE = [...]  # See pdf-patterns.md
BAR_COLORS_BLUE = [...]    # See pdf-patterns.md
```

### Colour Philosophy

The JET design system uses supporting brand colours **structurally** — for full-page backgrounds, content cards, table headers, chart bars, and timeline milestones. The five rules:

1. **JET Orange must appear in every communication** — bookend pages, accent bars, at least 20% of pages
2. **Supporting colours (Berry, Turmeric, Cupcake, Latte) are for colour blocks and backgrounds** — used structurally, not decoratively
3. **Never combine two supporting colours in one report** — always pair ONE supporting colour with JET Orange
4. **Charcoal is ONLY for text and interactive elements** — never as a solid page background
5. **Warm colour temperature throughout** — Mozzarella replaces cold greys, never pure white backgrounds

### Colour-to-Purpose Mapping

| Supporting Colour | Typical Use |
|---|---|
| **Latte** | Full-page backgrounds, split panels, warm card fills |
| **Cupcake** | Table headers, bar charts, section header bands |
| **Berry** | Status/alert cards, outstanding items |
| **Turmeric** | Outlier highlights, timeline milestones, planned items |

### Semantic Colour Mapping

Status indicators use **true traffic light colours** (`TL_GREEN`, `TL_ORANGE`, `TL_RED`, `TL_GRAY`) — not JET brand colours — so readers can instantly recognise status at a glance. These are warm-toned variants that sit comfortably alongside the JET palette without clashing. Status dots use the traffic light colour directly; status **text** labels always use Charcoal for readability; delta text ("+8 new") uses JET Orange.

## Colour Accessibility (WCAG 2.1 AA)

All text colours must meet minimum contrast ratios against their background:
- **Normal text** (< 18pt): 4.5:1 minimum
- **Large text** (>= 18pt or >= 14pt bold): 3:1 minimum

Rules:
- **Never use JET_ORANGE as text on a white background** -- it's 3.4:1 (fails AA). Use it only for decorative elements (accent bars, chart fills, dots) on light backgrounds. Use `JET_ORANGE_TEXT` (#F36805, 4.5:1) for orange text on light backgrounds.
- **LIGHT_TEXT (#9E9E9E)** has 3.5:1 contrast -- usable for large text (18pt+) and metadata captions, but not for body text.
- **Never rely on colour alone** for meaning (WCAG 1.4.1). Always pair colour with a text label.
- **Red-green colour blindness** affects ~8% of men. Always pair SUCCESS/DANGER with text labels or symbols.
- **JET supporting colours as text have very poor contrast** (1.3-1.9:1 on light backgrounds). Never use Berry, Turmeric, Cupcake, or Latte as text colour. Use Charcoal for status labels and JET Orange for delta text. Status dots (visual-only, no text) may use supporting colours freely.

## Typography

- **Font**: Inter (official JET brand font, from the corporate template)
- **Weights**: Regular (""), Bold ("B"), Italic ("I"), plus separate families for Medium, SemiBold, ExtraBold, Black, Light
- **Fallback**: If Inter font files are unavailable, fall back to Helvetica (built into fpdf2)

The Inter font files are bundled in this skill at `references/fonts/`. Register them in every report script (see boilerplate in SKILL.md "Critical Settings", or `pdf-patterns.md` for the full code).

### Weight Mapping (from the JET template analysis)

| JET template usage | Font family to use | Style |
|--------------------|--------------------|-------|
| `Inter` (regular body) | `"Inter"` | `""` |
| `Inter` bold | `"Inter"` | `"B"` |
| `Inter Medium` (subtitles) | `"InterMedium"` | `""` |
| `Inter SemiBold` (dates, labels) | `"InterSemiBold"` | `""` |
| `Inter ExtraBold` (card headings) | `"InterExtraBold"` | `""` |
| `Inter Black` (emphasis, timelines) | `"InterBlack"` | `""` |
| `Inter Light` (chart axis labels) | `"InterLight"` | `""` |

### Type Scale (from JET template — definitive sizes from slide 33 of the PPTX)

| Element | Size | Font family | Colour | Line height |
|---------|------|-------------|--------|-------------|
| Section header band title | 14pt | Inter "B" | WHITE | 8mm |
| Cover title | 25-44pt | InterBlack | WHITE | 12-24mm |
| Long text headlines | 19pt | Inter "B" | CHARCOAL | 10mm |
| Content heading | 15pt | Inter "B" | CHARCOAL | 8mm |
| Card heading | 13pt | InterExtraBold | CHARCOAL | 7mm |
| Subtitles | 11pt | Inter "B" | CHARCOAL | 6.5mm |
| Body text | 11pt | Inter | DARK_TEXT | 6mm |
| Key takeaway | 11pt | Inter "B" | CHARCOAL | 6.5mm |
| Body text (secondary) | 10pt | Inter | MID_TEXT | 5.5mm |
| Table body | 8-9pt | Inter | DARK_TEXT | 5.5mm |
| Table header | 8pt | Inter "B" | CHARCOAL on CUPCAKE | 7mm |
| Footer | 8pt | Inter | MID_TEXT | 4mm |
| Labels/captions | 7-8pt | Inter "B" | CHARCOAL | 4mm |
| Source footnotes | 7pt | Inter | LIGHT_TEXT | 3mm |
| Delta indicators | 6.5pt | Inter "B" | JET_ORANGE | 4mm |
| KPI card value | 20-22pt | InterExtraBold | WHITE/CHARCOAL | 10mm |
| KPI card label | 7-8pt | Inter | MID_TEXT | 4mm |

**Default alignment:** Left-aligned, sentence case. **Line spacing:** 1.15.

## Bookend Principle

From the JET brand guidelines: **start and end on JET Orange**. The first and last pages of a report must prominently feature `JET_ORANGE`. This creates visual "bookends" that reinforce the brand.

- Cover page: Full-bleed `JET_ORANGE` background with WHITE text — the opening bookend
- Final page / closing: `JET_ORANGE` full-bleed background with WHITE text — the closing bookend
- At least 20% of pages should feature JET Orange prominently (cover, section header bands, closing)
- Supporting colours used in sections (grouped consecutive pages), not randomly alternating

## Page Footer

All inner pages display a footer at the bottom: `‹page#› | Month Year | **Title of project**` in 7-8pt Inter, with a thin horizontal rule above and pipe separators. MID_TEXT colour. Omitted on cover and closing pages. See the `header()` method in pdf-patterns.md for the full implementation.

## Spacing System (4mm base unit)

Use the 4mm base unit for all spacing to create visual rhythm (2mm half-step available for tight internal spacing):

```python
SPACE_XS = 2    # 0.5x -- within components (after key takeaway, between label and value)
SPACE_SM = 4    # 1x   -- between related elements (after heading underline, between paragraphs)
SPACE_MD = 8    # 2x   -- between sections (before a new chart, after a table)
SPACE_LG = 12   # 3x   -- major section breaks
SPACE_XL = 16   # 4x   -- page-level breathing room
```

## Markdown in multi_cell / cell

The `markdown=True` parameter supports `**bold**`, `__underline__`, and `*italic*`. Limitations:
- Only works on `multi_cell()` and `cell()`, not `write()`
- Markers cannot be nested (no `***bold italic***`)
- The `**` markers are consumed and do not appear in the rendered text
- Set the base font before calling -- markdown bold uses the bold variant of the current font

**CRITICAL — Bold/Highlight Inversion Bug:** When `markdown=True` is active, `**text**` TOGGLES the bold state of the base font. If the base font is already bold (e.g., `Inter "B"`), then `**text**` turns bold OFF for those words — rendering them in regular weight while the surrounding text stays bold. This is the OPPOSITE of the intended effect. **The base font MUST be regular weight (not bold) when using `**bold**` highlights with `markdown=True`.** If a paragraph needs to be entirely bold with no highlights, set `Inter "B"` and do NOT use `**markers**`. If a paragraph needs bold highlights, set `Inter ""` (regular) and wrap key phrases in `**...**`.

**CRITICAL — NEVER use `__underline__` in markdown text.** The `__text__` syntax renders as underlined text in the PDF. Underlined text in digital documents is universally associated with hyperlinks — readers will try to click it, and when nothing happens, it looks like a broken link. This is a common source of visual defects in generated reports.

- **Only use `**bold**`** for emphasis in body text, key takeaways, and TLDR blocks
- **Never use `__underline__`** — not for emphasis, not for names, not for anything
- **Never use `*italic*`** in body text — italic is reserved for quote blocks only
- The **only place underline is acceptable** is in the `HYPERLINK` component, where it is drawn manually (not via markdown) and paired with an actual clickable `link=` parameter

## Page Dimensions

```python
PAGE_W    = 210      # A4 width in mm
PAGE_H    = 297      # A4 height in mm
MARGIN    = 20       # Page margins
CONTENT_W = PAGE_W - 2 * MARGIN  # Usable width = 170mm
CONTENT_X = MARGIN   # Left edge of content area
MAX_Y     = 275      # Page overflow threshold
```

## Layout Conventions

### Standard Page Structure

Reports follow this page order:

1. **Cover page** - Full-bleed JET Orange, white title, hero KPI (5-second scan)
2. **Executive summary** - Section header band + key takeaway, TLDR, hero stats (30-second scan)
3. **Detail pages** - Charts, tables, status lists with supporting colour accents
4. **More detail pages** - Additional analysis, capabilities, design system
5. **Closing page** - Full-bleed JET Orange bookend

**Section header bands** provide visual separation between major sections without wasting entire pages. The first page of each section uses a coloured band (~25mm tall) at the top containing section title, number, and document metadata. Content starts immediately below on the same page. Subsequent pages in the same section use the thin 1.5mm accent line only.

**Content pages** can use `bg_color` parameter to set full-page supporting colour backgrounds (e.g., Latte for the design rules page). Use `content_page("Title", "01", bg_color=LATTE)`.

### Use local_context() for Style Safety

`local_context()` scopes style changes (font, colour, opacity) so they auto-revert when the block exits. Use it to prevent colour/font "leaking" bugs:

```python
with pdf.local_context(text_color=CHARCOAL):
    pdf.set_font("Inter", "B", 12)
    pdf.cell(CONTENT_W, 8, "Bold charcoal text")
# Automatically reverted to previous style here
```

### PDF Bookmarks / Document Outline

Use `pdf.start_section()` to create navigable bookmarks in the PDF sidebar. The `section_heading()` helper does this automatically (pass `bookmark=False` to disable). Sub-sections use `level=1`:

```python
pdf.start_section("By Severity", level=1)
```

### Override footer()

The footer uses a `_no_footer_pages` set to suppress footers on cover and closing pages. This avoids timing issues with fpdf2's `footer()` being called during `add_page()` for the previous page:

```python
def __init__(self):
    super().__init__()
    self._no_footer_pages = set()  # pages that should not have footer

def footer(self):
    if self.page_no() in self._no_footer_pages:
        return
    # Thin horizontal rule above footer
    self.set_y(-15)
    self.set_draw_color(*BORDER)
    self.line(MARGIN, self.get_y(), PAGE_W - MARGIN, self.get_y())
    self.ln(2)
    self.set_font("Inter", "", 8)
    self.set_text_color(*MID_TEXT)
    # Title is bold per footer spec: page | Month Year | **Title**
    self.cell(0, 4, f"{self.page_no()}  |  {REPORT_PERIOD}  |  **{REPORT_FOOTER}**",
              markdown=True)
```

Register pages as no-footer immediately after `add_page()`:
```python
self.add_page()
self._no_footer_pages.add(self.page_no())
```

### Inner Page Header

Content pages use one of two header styles:

**Section header band** (first page of a major section):
- Coloured band (~25mm tall) at the very top of the page
- Band contains: document title + date (small grey text), section title (bold 14pt), section number (small grey)
- Band colour varies by section position — warm colours near bookends (Latte), bolder colours in middle (Cupcake, Turmeric)
- Content starts immediately below the band

**Standard accent line** (continuation pages within a section):
- Thin 1.5mm JET Orange accent line at the very top — a narrow horizontal rule, not a wide colour band
- Content starts at y=20mm

Both styles include a footer at the bottom: `NN | Month Year | **Title**` format. Omitted on cover and closing pages.

See pdf-patterns.md for the full `header()` implementation.
