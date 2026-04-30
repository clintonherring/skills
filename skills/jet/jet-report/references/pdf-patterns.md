# PDF Patterns Reference

Ready-to-paste fpdf2 code snippets for executive reports. Each pattern is self-contained. Adapt variable names, colours, and data to your specific report.

> **fpdf2 version**: These patterns require fpdf2 >= 2.8.0. All features (`table()`, `local_context()`, `start_section()`, `solid_arc()`, `rotation()`) are verified working on v2.8.7.

---

## Table of Contents

**Foundation**
- [Critical Design Rules](#critical-design-rules)
- [Setup and Boilerplate](#setup-and-boilerplate)
- [Rounded-Rect Clipping Path Helper](#rounded-rect-clipping-path-helper)
- [PDF Subclass with Header, Footer, and Helpers](#pdf-subclass-with-header-footer-and-helpers)

**Page-Level Patterns**
- [Cover Page](#cover-page)
- [KPI Cards (Cover Page)](#kpi-cards-cover-page)
- [Content Page Helper](#content-page-helper)
- [Cover Page: Dynamic Titles and KPI Card Count](#cover-page-dynamic-titles-and-kpi-card-count)

**Text & Layout**
- [Executive Summary Text](#executive-summary-text)
- [Using local_context()](#using-local_context)
- [Methodology / Callout Box](#methodology--callout-box)
- [Three-Column Numbered Steps](#three-column-numbered-steps)
- [Numbered Insight Cards](#numbered-insight-cards)

**Data Visualisation**
- [Side-by-Side Chart Cards](#side-by-side-chart-cards)
- [Data Table with Inline Bars](#data-table-with-inline-bars)
- [Totals Row](#totals-row)
- [Data Table with table() API](#data-table-with-table-api)
- [Traffic Light Status Table](#traffic-light-status-table)
- [Sparkline in Table](#sparkline-in-table)
- [Pie Charts](#pie-charts)
- [Colour-Coded Matrix / Grid](#colour-coded-matrix--grid)
- [Graph Card Grid](#graph-card-grid)

**Cards & Metrics**
- [Inner-Page KPI Row](#inner-page-kpi-row)
- [Stat Card (Reusable Helper)](#stat-card-reusable-helper)
- [Compact Tile Grid](#compact-tile-grid)

**Callouts & Quotes**
- [Callout Box Variants](#callout-box-variants)
- [Quote / Testimonial Cards](#quote--testimonial-cards)
- [Wide Quote Card](#wide-quote-card)

**Navigation & Structure**
- [Pagination: Totals Row Safety](#pagination-totals-row-safety)
- [Pagination: Page Break Before Section](#pagination-page-break-before-section)
- [Multi-Line Table Rows](#multi-line-table-rows)
- [PDF Bookmarks / Document Outline](#pdf-bookmarks--document-outline)
- [Table of Contents / TOC Page](#table-of-contents--toc-page)

**Utility Components**
- [Source Footnote](#source-footnote)
- [Draft Watermark](#draft-watermark)
- [Category / Tag Badge](#category--tag-badge)
- [Timeline / Milestone Indicator](#timeline--milestone-indicator)
- [Progress Bar (Reusable Helper)](#progress-bar-reusable-helper)

**Output & Reference**
- [Output](#output)
- [JET Visual Identity Style Guide Patterns](#jet-visual-identity-style-guide-patterns)

---

## Critical Design Rules

These rules are confirmed across 177 JET Global Product and Tech template slides AND the 50-slide JET Visual Identity style guide, and must be followed in every report:

1. **NO underlines under titles** — hierarchy is purely typographic (font weight + scale). Zero slides use underlines.
2. **NEVER use `__underline__` in markdown text** — the `markdown=True` parameter on `multi_cell()` and `cell()` supports `__text__` as underline. **Never use this.** Underlined text in PDFs looks like broken hyperlinks. Only use `**bold**` for emphasis. The sole exception is the `HYPERLINK` component which draws underlines manually with `link=`. This is the #1 most common visual defect in generated reports.
3. **Consistent x-offsets** — all content uses `CONTENT_X = MARGIN` (20mm). No `MARGIN + 5` shifts. Title and content share the same left margin.
4. **Quote blocks use vertical LEFT accent bar** (2.5mm wide), not top accent bar. More aligned with JET presentation conventions. **Use the clipping path technique**: (1) call `_rounded_rect_clip(pdf, x, y, w, h, cr)` to set a rounded-rect clip, (2) draw a flat accent rect for the bar, (3) draw a flat bg rect for the rest, (4) call `_restore_gfx_state(pdf)` to restore state and re-sync colours. This produces pixel-perfect rounded corners with no colour bleed. Never use `round_corners=("TOP_LEFT", "BOTTOM_LEFT")` layering — it causes artefacts.
5. **Page-level colour unity** — maximum 2 accent colours per page. No "rainbow" effect.
6. **Card-free by default** — the 01/02/03 pattern uses NO cards. Prefer open layouts; only use containers when content genuinely benefits from visual grouping.
7. **Warm Mozzarella background on content pages** — use `MOZZARELLA` (#EFEDEA) as a full-page background colour, not plain white. This is a page background, NOT a header band or strip.
8. **TLDR block** — first content page should have a `tldr_block()` with the single most important message.
9. **Footer format** — `NN | Month Year | **Title**` at bottom of page (not top), 7-8pt Inter, thin horizontal rule above, pipe-separated. Rendered from `header()` so it can be conditionally skipped on cover and closing pages.
10. **Bookend principle** — first and last pages MUST use JET Orange background. Minimum 20% of pages should have JET Orange backgrounds.
11. **Charcoal is NOT a page background** — Charcoal (#242E30) is only for text and badges/pills. Table headers use Cupcake background with Charcoal text. Never use Charcoal as a full-page background.
12. **Rounded corners everywhere** — ~8-12px radius on cards, fully rounded on pills/badges. No sharp-cornered containers.
13. **No borders/rules on content** — separation achieved through whitespace and colour contrast, not visible borders or divider lines.
14. **12-column grid system** — all content widths MUST use `grid_span(n)` to snap to column boundaries. Margin = 20mm, Gutter = 9mm. Common layouts: 2-column = `grid_span(6)`, 3-column = `grid_span(4)`, 4-column = `grid_span(3)`. For inter-column gaps, always use `GUTTER` (9mm). Never compute column widths with ad-hoc formulas like `(CONTENT_W - gap) / n` — use `grid_span()` instead.
15. **Section header bands on content pages** — the first page of each major section uses a coloured band (~25mm tall) at the top of the page containing the section title, section number, and document metadata. The band colour varies by section using primary supporting colours (Latte, Cupcake, Turmeric, Berry). Content starts immediately below the band on the SAME page — no wasted full-page dividers. Subsequent pages in the same section use the thin 1.5mm JET Orange accent line only.
16. **Card background contrast** — on Mozzarella pages, `MOZZARELLA_T1` (#F5F3F1) is acceptable as card fill **only when paired with a 0.3mm `BORDER`-coloured stroke** (style `"DF"`). Without a stroke, prefer `MOZZARELLA_T2` (#FCFCFC) or `WHITE` for stronger visual separation.
17. **Never hallucinate names, titles, or quotes** — if you don't have a person's exact name and title from a verified source (API, user input, document), ask the user before generating. Never leave `[TODO: verify]` or placeholder text in a generated PDF — omit the section or rephrase instead. Getting a C-level executive's name wrong in a report read by 1300+ people is a critical failure.
18. **Always measure before drawing containers** — use `multi_cell(..., dry_run=True, output="HEIGHT")` to calculate text height before drawing any background rect or clipped region. Never hardcode box heights (`block_h = 24`) — content length varies and hardcoded heights cause text overflow or wasted whitespace.
19. **No logo on ANY page** — do NOT place the JET logo or icon on cover pages, content pages, or closing pages. Brand presence comes exclusively from the JET Orange bookend pages and the colour palette. The bundled logo image files (`jet_icon_white.png`, `jet_logo_badge.png`) are reference assets only and must NOT be embedded in generated PDFs.
20. **Bold/highlight inversion prevention** — when using `markdown=True` with `**bold**` highlights, the base font MUST be regular weight (e.g., `Inter ""` or `Inter ""`), NEVER bold (`Inter "B"`). The `**` markers TOGGLE the bold state — if the base font is already bold, `**text**` turns bold OFF (rendering those words in regular weight), which is the opposite of the intended effect. If a paragraph must be entirely bold with no highlights, set the font to bold and do NOT use `**markers**`. If a paragraph needs bold highlights within regular text, set the font to regular and use `**key phrases**`. This is the #2 most common visual defect in generated reports.
21. **`bg_color` and `band_color` must differ** — when calling `content_page()` with a `band_color`, the `bg_color` must be a different colour (or left as the default `MOZZARELLA`). If both are identical, the 25mm section header band becomes invisible against the page background, breaking the visual hierarchy. The band exists to create contrast with the page — same-colour bg and band defeats the purpose. Typical correct pairings: `bg_color=MOZZARELLA` (default) + `band_color=LATTE`, or `bg_color=MOZZARELLA` + `band_color=CUPCAKE`.
22. **Standard component gap** — use `SPACE_MD` (8mm) as the default vertical gap between successive components on a page (e.g., after a stat card row, after a callout box, after a data table). Use `SPACE_SM` (4mm) between tightly related elements within a component. Use `SPACE_LG` (12mm) for major visual breaks between distinct content sections on the same page. Always use named spacing tokens — never bare numbers.
23. **Heading breathing room** — `section_heading()` (15pt) uses `SPACE_MD` (8mm) after the title before content starts. Sub-headings (11pt, via `sub_heading()`) use `SPACE_MD` (8mm) above to separate from preceding content and `SPACE_MD` (8mm) below before their own content. `key_takeaway()` uses `SPACE_SM` (4mm) after. Titles must never crowd the content beneath them, but excessive spacing wastes vertical real estate on content-dense pages.
24. **Chart colour consistency** — all charts on the same page MUST use the same bar colour palette (default: `BAR_COLORS_ORANGE`). Only use a second colour when charts compare fundamentally distinct categories (e.g., revenue vs cost). Two top-10 rankings on the same page must both use orange, not orange and blue.
25. **Two-column Y alignment** — side-by-side elements (charts, cards, tables) must anchor to the same Y. Save `start_y = pdf.get_y()` before column 1, `pdf.set_xy(right_x, start_y)` before column 2, `pdf.set_y(max(left_end_y, right_end_y))` after both. See gotchas-and-errors.md for the full pattern.
26. **Section heading wrapping** — `section_heading()` uses `multi_cell()`, not `cell()`. Long insight-as-headline titles wrap to a second line instead of being silently clipped. Never use `cell()` for any heading or title text that could exceed the printable width — this includes centred titles, where `cell()` with `align="C"` causes text to overflow **both** margins symmetrically. Always use `multi_cell()` with `align="C"` for centred titles.
27. **Multi-row grid pre-flight check** — before rendering any grid component that spans multiple rows (graph card grids, tile grids, icon grids), calculate the **total height** of all rows: `total_h = num_rows * (card_h + row_gap) - row_gap`. If `pdf.get_y() + total_h > MAX_Y` and the grid **would** fit on a fresh page (i.e., `MARGIN + total_h <= MAX_Y`), call `pdf.add_page()` to start the grid on a new page rather than splitting it mid-row. A 2×2 grid that overflows after 1 row creates an orphaned row with ~60% whitespace — one of the most visually jarring layout defects. If the grid is too tall even for a fresh page, reduce `card_h` or split into separate grids with explicit sub-headings. See `gotchas-and-errors.md` → "Grid/Multi-Row Component Page Overflow" for the failure mode.
28. **All colours must reference named palette constants** — never use inline RGB tuples (e.g., `set_text_color(255, 240, 220)`) in report code. Every colour must be a named constant from the boilerplate palette section (e.g., `set_text_color(*COVER_TEXT_WARM)`). If a new colour is genuinely needed, add it to the palette section with a descriptive name and a hex comment first. The only exception is the `(255, 255, 254)` sentinel in `_restore_gfx_state()`. This prevents off-palette colours from silently entering reports — unnamed tuples are invisible to visual review and impossible to audit.

## Setup and Boilerplate

```python
# ── Report metadata (update for each report) ──────────────────────
# Report: <Full report title, e.g. "AI Adoption Report — March 2026">
# Type:   <stable snake_case identifier, e.g. "ai_adoption_report">
# Last generated: <YYYY-MM-DD>
# Description: <One-line summary of what this report covers>

import json, os
from fpdf import FPDF
from fpdf.fonts import FontFace
from fpdf.enums import TableBordersLayout, TableCellFillMode

# ── Page constants ─────────────────────────────────────────────────
PAGE_W    = 210
PAGE_H    = 297
MARGIN    = 20
CONTENT_W = PAGE_W - 2 * MARGIN
CONTENT_X = MARGIN                   # Left edge of content area
MAX_Y     = 275  # Page overflow threshold (leave 22mm at bottom)

# ── Spacing system (4mm base unit) ─────────────────────────────────
SPACE_XS = 2    # 0.5x -- within components
SPACE_SM = 4    # 1x   -- between related elements
SPACE_MD = 8    # 2x   -- between sections
SPACE_LG = 12   # 3x   -- major section breaks
SPACE_XL = 16   # 4x   -- page-level breathing room

# ── 12-column grid system (Rule #14) ──────────────────────────────
GUTTER    = 9
GRID_COLS = 12
COL_W     = (CONTENT_W - (GRID_COLS - 1) * GUTTER) / GRID_COLS  # ≈5.92mm

def grid_span(n):
    """Width of n grid columns including internal gutters."""
    return n * COL_W + (n - 1) * GUTTER

# Common layout widths:
#   grid_span(6)  ≈ 80.5mm  — half-page (2-column layouts)
#   grid_span(4)  ≈ 50.7mm  — third-page (3-column layouts)
#   grid_span(3)  ≈ 35.8mm  — quarter-page (4-column layouts)
#   grid_span(12) = 170mm   — full content width (== CONTENT_W)

# ── Inter font directory ──────────────────────────────────────────
FONT_DIR = os.path.expanduser(
    "~/.agents/skills/jet-report/references/fonts"
)

# ── JET colour palette (official brand names from VI Style Guide) ─
JET_ORANGE         = (255, 128, 0)     # #FF8000 - Primary brand — MUST appear in every communication
JET_ORANGE_TEXT    = (243, 104, 5)     # #F36805 - Accessible Orange (text on light bg)
CHARCOAL   = (36, 46, 48)             # #242E30 - Text/interactive ONLY, never as bg
DARK_TEXT   = (50, 50, 55)             # Body text (12.6:1 contrast)
MID_TEXT    = (89, 89, 89)             # #595959 - Labels, captions (7.0:1)
LIGHT_TEXT  = (158, 158, 158)          # #9E9E9E - Metadata (3.5:1, large text only)
MUTED_TEXT  = (176, 171, 171)          # #B0ABAB - Out-of-scope / greyed text
WHITE      = (255, 255, 255)

# Neutral surfaces (Mozzarella family — warm, never cold grey)
MOZZARELLA     = (239, 237, 234)       # #EFEDEA - Primary background colour
MOZZARELLA_T1  = (245, 243, 241)       # #F5F3F1 - Card/container fill
MOZZARELLA_T2  = (252, 252, 252)       # #FCFCFC - Near-white
BORDER     = (220, 218, 214)           # Warm-toned divider
ALT_ROW    = (245, 243, 241)           # #F5F3F1 - Alternating rows (= MOZZARELLA_T1)

# Supporting brand colours (for colour blocks and backgrounds)
# Rule: NEVER combine two supporting colours in one layout.
# Always pair ONE supporting colour with JET Orange.
BERRY      = (242, 166, 176)           # #F2A6B0 - Pink
TURMERIC   = (246, 194, 67)            # #F6C243 - Golden yellow
CUPCAKE    = (193, 218, 222)           # #C1DADE - Blue-green
LATTE      = (231, 205, 162)           # #E7CDA2 - Warm beige
AUBERGINE  = (91, 61, 91)             # #5B3D5B - Highlights only, sparingly

# Light tints of supporting colours
LIGHT_ORANGE = (253, 223, 195)         # #FDDFC3
LIGHT_PINK   = (249, 210, 215)         # #F9D2D7 - Berry tint
LIGHT_YELLOW = (250, 224, 161)         # #FAE0A1 - Turmeric tint
LIGHT_BLUE   = (224, 236, 238)         # #E0ECEE - Cupcake tint
LIGHT_TAN    = (241, 227, 201)         # #F1E3C9 - Latte tint

# Semantic / status colours — TRUE traffic light colours for instant recognition
# These are warm-toned variants that sit comfortably alongside the JET palette
# while being unmistakably green/orange/red/gray at a glance.
TL_GREEN   = (34, 197, 94)              # #22C55E - clear green (done, healthy, ready)
TL_ORANGE  = (255, 146, 0)              # #FF9200 - warm orange (in progress, warning, degraded)
TL_RED     = (239, 68, 68)              # #EF4444 - clear red (blocked, critical, failed)
TL_GRAY    = (156, 163, 175)            # #9CA3AF - neutral gray (to do, inactive, N/A)

# Semantic aliases (map to traffic light colours)
SUCCESS    = TL_GREEN
WARNING    = TL_ORANGE
DANGER     = TL_RED
INFO       = TL_ORANGE                   # Info uses orange (visible, not critical)
MUTED      = TL_GRAY

# Status tint backgrounds (light washes behind status rows/cards)
SUCCESS_BG = (220, 252, 231)            # #DCFCE7 - light green wash
WARNING_BG = (255, 237, 213)            # #FFEDD5 - light orange wash
DANGER_BG  = (254, 226, 226)            # #FEE2E2 - light red wash
INFO_BG    = (255, 237, 213)            # #FFEDD5 - light orange wash (same as WARNING_BG)

# Cover page accent colours (on JET Orange backgrounds)
COVER_TEXT_WARM = (255, 240, 220)    # warm white for labels on orange cover
COVER_TEXT_SAND = (255, 220, 180)    # sandy white for dates/metadata on orange cover
COVER_DIVIDER   = (255, 200, 130)    # muted orange for decorative divider on cover
COVER_KPI_BG    = (255, 178, 102)    # warm sandy-orange tint for cover KPI cards
WATERMARK_TEXT  = (180, 180, 180)    # light grey for DRAFT/CONFIDENTIAL watermarks

BAR_COLORS_ORANGE = [
    (255, 128, 0), (255, 140, 25), (255, 155, 50), (255, 168, 70),
    (255, 180, 90), (255, 192, 110), (255, 202, 130), (255, 212, 150),
    (255, 222, 170), (255, 232, 190),
]
BAR_COLORS_BLUE = [
    (59, 130, 246), (75, 140, 245), (90, 150, 242), (105, 160, 240),
    (120, 170, 237), (135, 180, 234), (150, 190, 230), (165, 200, 227),
    (180, 210, 224), (195, 218, 220),
]

# Reusable FontFace for table headings (Cupcake bg, Charcoal bold text)
TABLE_HEADING_STYLE = FontFace(
    color=CHARCOAL, fill_color=CUPCAKE, emphasis="BOLD", size_pt=8
)


# ── Number formatting helpers ──────────────────────────────────────
def fmt_number(n):
    """Format number with thousands separators or abbreviation."""
    if abs(n) >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if abs(n) >= 10_000:
        return f"{n / 1_000:.1f}K"
    return f"{n:,}"


def fmt_pct(n, decimals=1):
    """Format as percentage with consistent precision."""
    return f"{n:.{decimals}f}%"


def fmt_delta(n, suffix=""):
    """Format as delta with explicit sign."""
    sign = "+" if n > 0 else ""
    return f"{sign}{n}{suffix}"


def darken(rgb, factor=0.5):
    """Return a colour that is `factor` darker (0.5 = 50% darker).
    Use for colour swatch borders: darken(swatch_rgb, 0.5)."""
    return tuple(int(c * (1 - factor)) for c in rgb)
```

## Rounded-Rect Clipping Path Helper

This helper is **essential** for accent bar rendering on quote blocks and TLDR blocks.
It creates a pixel-perfect rounded-rectangle clip region using raw PDF operators. All
drawing between the call and the matching `_restore_gfx_state(pdf)` is clipped to the rounded rect.

**CRITICAL:** After drawing inside the clip, you MUST call `_restore_gfx_state(pdf)` (not
raw `pdf._out("Q")`). Raw Q restores the PDF graphics state but leaves fpdf2's internal
colour cache stale, causing subsequent `set_fill_color` calls to be silently skipped. The
`_restore_gfx_state` helper handles both the Q restore and the cache invalidation.

```python
def _rounded_rect_clip(pdf, x, y, w, h, r):
    """Set a rounded-rectangle clipping path using raw PDF operators.

    Everything drawn after this call (until the matching _restore_gfx_state)
    will be clipped to the rounded rectangle.
    Caller MUST call _restore_gfx_state(pdf) when done — never raw _out('Q').
    """
    pdf._out("q")  # save graphics state
    k = pdf.k
    px, py, pw, ph, pr = x * k, (pdf.h - y) * k, w * k, h * k, r * k
    kp = 0.5523 * pr  # bezier approximation of quarter-circle

    ops = [
        f"{px + pr:.4f} {py:.4f} m",
        f"{px + pw - pr:.4f} {py:.4f} l",
        f"{px + pw - pr + kp:.4f} {py:.4f} {px + pw:.4f} {py - kp:.4f} {px + pw:.4f} {py - pr:.4f} c",
        f"{px + pw:.4f} {py - ph + pr:.4f} l",
        f"{px + pw:.4f} {py - ph + pr - kp:.4f} {px + pw - pr + kp:.4f} {py - ph:.4f} {px + pw - pr:.4f} {py - ph:.4f} c",
        f"{px + pr:.4f} {py - ph:.4f} l",
        f"{px + pr - kp:.4f} {py - ph:.4f} {px:.4f} {py - ph + pr - kp:.4f} {px:.4f} {py - ph + pr:.4f} c",
        f"{px:.4f} {py - pr:.4f} l",
        f"{px:.4f} {py - pr + kp:.4f} {px + pr - kp:.4f} {py:.4f} {px + pr:.4f} {py:.4f} c",
        "W n",
    ]
    for op in ops:
        pdf._out(op)


def _restore_gfx_state(pdf):
    """Restore PDF graphics state AND re-sync fpdf2's colour cache.

    Raw ``pdf._out("Q")`` restores the PDF reader's graphics state (fill,
    draw, text colours revert to pre-``q`` values), but fpdf2's Python-side
    cache still holds the colours set *inside* the q…Q block.  If you then
    call ``set_fill_color`` with the same values fpdf2 thinks are current,
    fpdf2 silently skips emitting the PDF operator — the fill stays wrong.

    This helper emits ``Q`` and then forces fpdf2 to re-emit all three
    colour operators by briefly toggling to a sentinel value.

    Always use this instead of raw ``pdf._out("Q")`` after ``_rounded_rect_clip``.
    """
    pdf._out("Q")
    # Invalidate fpdf2's fill / draw / text colour cache
    fc = tuple(int(c) for c in pdf.fill_color.colors255)
    pdf.set_fill_color(255, 255, 254)   # sentinel
    pdf.set_fill_color(*fc)

    dc = tuple(int(c) for c in pdf.draw_color.colors255)
    pdf.set_draw_color(255, 255, 254)
    pdf.set_draw_color(*dc)

    tc = tuple(int(c) for c in pdf.text_color.colors255)
    pdf.set_text_color(255, 255, 254)
    pdf.set_text_color(*tc)
```

## PDF Subclass with Header, Footer, and Helpers

```python
class ReportPDF(FPDF):
    def __init__(self):
        super().__init__()
        self._section_title = ""      # e.g. "EXECUTIVE SUMMARY"
        self._section_num = ""        # e.g. "Section 01"
        self._is_cover = False
        self._is_closing = False
        self._bg_color = MOZZARELLA   # default page background
        self._no_footer_pages = set() # pages that should not have footer
        self._section_band_color = None  # set to (R,G,B) tuple for section header band
        self.report_title = "Report Title"
        self.report_date = "March 2026"

    # ── Underline safeguard ────────────────────────────────
    # fpdf2's markdown=True interprets __text__ as underline, which looks
    # like broken hyperlinks and is the #1 visual defect in generated PDFs.
    # These overrides automatically strip double-underscores from any text
    # rendered with markdown=True, so underlines can NEVER appear.

    @staticmethod
    def _strip_underline(text):
        """Remove __ sequences that fpdf2 would interpret as underline."""
        return text.replace("__", "") if isinstance(text, str) else text

    def cell(self, *args, markdown=False, **kwargs):
        if markdown:
            if len(args) >= 3:
                args = args[:2] + (self._strip_underline(args[2]),) + args[3:]
            if "text" in kwargs:
                kwargs["text"] = self._strip_underline(kwargs["text"])
        return super().cell(*args, markdown=markdown, **kwargs)

    def multi_cell(self, *args, markdown=False, **kwargs):
        if markdown:
            # text is typically the 3rd positional arg (w, h, text) or via kwargs
            if len(args) >= 3:
                args = args[:2] + (self._strip_underline(args[2]),) + args[3:]
            if "text" in kwargs:
                kwargs["text"] = self._strip_underline(kwargs["text"])
        return super().multi_cell(*args, markdown=markdown, **kwargs)

    def header(self):
        if self._is_cover or self._is_closing:
            return

        # Full-page background (supports MOZZARELLA, LATTE, etc.)
        self.set_fill_color(*self._bg_color)
        self.rect(0, 0, PAGE_W, PAGE_H, style="F")

        if self._section_band_color:
            # ── Section header band (~25mm) ──────────────────────
            band_h = 25
            self.set_fill_color(*self._section_band_color)
            self.rect(0, 0, PAGE_W, band_h, style="F")

            # Document title + date (small text at top of band)
            # Use CHARCOAL on all supporting colours (per JET rules)
            self.set_xy(MARGIN, 4)
            self.set_font("Inter", "", 7)
            self.set_text_color(*CHARCOAL)
            self.cell(0, 3, f"{self.report_title}  |  {self.report_date}")

            # Section title (bold, prominent)
            self.set_xy(MARGIN, 9)
            self.set_font("Inter", "B", 14)
            self.set_text_color(*CHARCOAL)
            self.cell(0, 7, self._section_title)

            # Section number (small, below title)
            if self._section_num:
                self.set_xy(MARGIN, 17)
                self.set_font("Inter", "", 7)
                self.set_text_color(*CHARCOAL)
                self.cell(0, 3, self._section_num)

            # Content starts below band
            self.set_y(band_h + SPACE_SM)
        else:
            # ── Standard thin accent line header ─────────────────
            # Thin 1.5mm JET Orange accent line at very top
            self.set_fill_color(*JET_ORANGE)
            self.rect(0, 0, PAGE_W, 1.5, style="F")

            # Section title in JET Accessible Orange (WCAG AA on Mozzarella)
            if self._section_title:
                self.set_xy(MARGIN, 5)
                self.set_font("Inter", "B", 9)
                self.set_text_color(*JET_ORANGE_TEXT)
                self.cell(0, 5, self._section_title.upper())

            # Section number in grey (below section title)
            if self._section_num:
                self.set_xy(MARGIN, 11)
                self.set_font("Inter", "", 8)
                self.set_text_color(*MID_TEXT)
                self.cell(0, 4, self._section_num)

            # Content starts below section info area
            self.set_y(20)

    def footer(self):
        """Footer: page# | date | report name. Skipped on cover and closing pages."""
        if self.page_no() in self._no_footer_pages:
            return
        self.set_y(-15)
        self.set_font("Inter", "", 8)
        self.set_text_color(*MID_TEXT)
        self.cell(0, 4, f"{self.page_no()}  |  {self.report_date}  |  {self.report_title}")

    def content_page(self, section_title="", section_num="", bg_color=None,
                     band_color=None):
        """Add a new content page.

        bg_color: tuple (R,G,B) for the full-page background.
                  Defaults to MOZZARELLA if not specified.
        band_color: tuple (R,G,B) for a section header band at the top.
                    When set, draws a ~25mm coloured band with section title/number.
                    When None, uses the thin 1.5mm JET Orange accent line.
        IMPORTANT: bg_color and band_color must be DIFFERENT colours.
                   If they match, the header band becomes invisible (Rule #21).
        """
        self._is_cover = False
        self._is_closing = False
        self._section_title = section_title
        self._section_num = section_num
        self._bg_color = bg_color if bg_color else MOZZARELLA
        self._section_band_color = band_color
        self.add_page()

    def section_heading(self, title, subtitle="", bookmark=True):
        """Section heading WITHOUT underline. Hierarchy is purely typographic
        (Inter Bold 15pt vs Inter Regular body text). NO orange bar under titles.
        Confirmed across all 50 JET template slides: zero slides use underlines.

        Title should be an insight, not a label:
          BAD:  section_heading("Incident Summary")
          GOOD: section_heading("Payment failures drove 48% of all incidents")
        """
        if bookmark:
            self.start_section(title)
        self.set_font("Inter", "B", 15)
        self.set_text_color(*CHARCOAL)
        # MUST use multi_cell — cell() silently clips long titles at page width
        self.multi_cell(CONTENT_W, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(SPACE_MD)
        if subtitle:
            self.set_font("Inter", "", 8)
            self.set_text_color(*MID_TEXT)
            self.cell(0, 4, subtitle, new_x="LMARGIN", new_y="NEXT")
            self.ln(SPACE_SM)

    def sub_heading(self, title):
        """Secondary heading within a section (Inter Bold 11pt).
        Used for sub-sections like 'Report Type Coverage', 'How It Works',
        'Supported Output Formats', 'Typography Scale', etc.
        Adds SPACE_MD above (to separate from preceding content) and
        SPACE_MD below (before the sub-section content)."""
        self.ln(SPACE_MD)
        self.set_font("Inter", "B", 11)
        self.set_text_color(*CHARCOAL)
        self.cell(CONTENT_W, 6, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(SPACE_MD)

    def tldr_block(self, text):
        """Executive pull-quote at top of report. Orange left accent bar on
        warm cream background. Place immediately below the first section header.
        One per report maximum."""
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

    def key_takeaway(self, text):
        """Bold insight sentence at the top of a section -- the 'so what?'
        Use insight-as-headline style: state the conclusion, not a label.
        Example: 'Payment failures drove 48% of all incidents this week'"""
        with self.local_context(text_color=CHARCOAL):
            self.set_font("Inter", "B", 11)
            self.multi_cell(CONTENT_W, 5.5, text, markdown=True, align="L")
        self.ln(SPACE_SM)

    def source_footnote(self, text):
        """Data source attribution below a table or chart.
        Example: 'Source: BigQuery production data, 2026-02-23 to 2026-02-27'"""
        self.ln(1)  # sub-SPACE_XS: tight coupling to preceding chart
        with self.local_context(text_color=LIGHT_TEXT):
            self.set_font("Inter", "", 7)
            self.cell(CONTENT_W, 3, text, new_x="LMARGIN", new_y="NEXT")
        self.ln(SPACE_XS)

    def draft_watermark(self):
        """Diagonal 'DRAFT' watermark using rotation + opacity.
        Call this AFTER adding the page content (draws on top with low opacity)."""
        with self.local_context(fill_opacity=0.06):
            self.set_font("Inter", "B", 60)
            self.set_text_color(*WATERMARK_TEXT)
            with self.rotation(45, PAGE_W / 2, PAGE_H / 2):
                self.set_xy(30, PAGE_H / 2 - 15)
                self.cell(PAGE_W - 60, 30, "DRAFT", align="C")

    def table_header(self, col_widths, headers, aligns):
        self.set_font("Inter", "B", 8)
        self.set_fill_color(*CUPCAKE)
        self.set_text_color(*CHARCOAL)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 7, h, border=0, fill=True, align=aligns[i])
        self.ln()

    def continuation_header(self, title, col_widths, headers, aligns):
        self.set_font("Inter", "I", 7)
        self.set_text_color(*LIGHT_TEXT)
        self.cell(0, 4, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)  # sub-SPACE_XS: tight coupling to table header
        self.table_header(col_widths, headers, aligns)

    def traffic_light(self, x, y, status):
        """Draw a coloured status dot (3mm circle). Uses true traffic light colours.
        status: 'green', 'orange', 'red', 'gray'/'grey'.
        ALWAYS pair with a text label — never rely on colour alone."""
        colours = {
            "green": TL_GREEN, "orange": TL_ORANGE,
            "red": TL_RED, "gray": TL_GRAY, "grey": TL_GRAY,
        }
        self.set_fill_color(*colours.get(status, TL_GRAY))
        self.ellipse(x, y, 3, 3, style="F")

    def traffic_light_inline(self, x, y, status, label, row_h=7,
                             label_font_size=8, label_style=""):
        """Draw a status dot with properly-spaced text label inline.
        Dot (3mm) is vertically centred in row_h, text starts 5mm right of dot x.
        Returns the x position after the label text."""
        dot_y = y + (row_h - 3) / 2
        self.traffic_light(x, dot_y, status)
        text_x = x + 5  # 3mm dot + 2mm gap
        self.set_xy(text_x, y)
        self.set_font("Inter", label_style, label_font_size)
        self.set_text_color(*CHARCOAL)
        lbl_w = self.get_string_width(label) + 2
        self.cell(lbl_w, row_h, label)
        return text_x + lbl_w

    def sparkline(self, x, y, w, h, values, color=JET_ORANGE):
        """Draw a mini trend line. values is a list of numbers.
        Recommended: 6-10mm height, 0.5pt line width, endpoint dot."""
        if len(values) < 2:
            return
        mn, mx = min(values), max(values)
        rng = mx - mn or 1
        step = w / (len(values) - 1)
        points = []
        for i, v in enumerate(values):
            px = x + i * step
            py = y + h - ((v - mn) / rng) * h
            points.append((px, py))
        with self.local_context(draw_color=color, line_width=0.5):
            for i in range(len(points) - 1):
                self.line(points[i][0], points[i][1],
                          points[i + 1][0], points[i + 1][1])
        # End dot
        self.set_fill_color(*color)
        self.ellipse(points[-1][0] - 0.75, points[-1][1] - 0.75, 1.5, 1.5, style="F")

    def pie_chart(self, cx, cy, r, pct, color=JET_ORANGE,
                  track_color=BORDER):
        """Draw a two-segment pie chart showing a percentage.
        cx, cy = centre. r = outer radius. pct = 0-100.
        IMPORTANT — solid_arc() coordinate convention:
          - x, y = upper-left corner of the bounding box (NOT the centre)
          - a = DIAMETER of the circle (full width), despite the docstring
            calling it "semi-major axis". Internally, arc() does a /= 2.
          - Angles: 0° = 3 o'clock, counter-clockwise by default.
          - Use clockwise=True to sweep clockwise from start to end.
        Use ellipse() for full circles — solid_arc near 360° can leave gaps.
        The pie chart is a visual-only element — labels and percentages
        are handled by the parent component (e.g. draw_graph_card_grid)."""
        d = r * 2  # diameter — this is the 'a' param for solid_arc
        # Background track (full circle via ellipse)
        self.set_fill_color(*track_color)
        self.ellipse(cx - r, cy - r, d, d, style="F")
        # Value segment (starts at 12 o'clock, sweeps clockwise)
        if 0 < pct < 100:
            sweep = pct / 100 * 360
            # 12 o'clock = 90°. Clockwise by 'sweep' degrees → end at (90 - sweep)°
            self.set_fill_color(*color)
            self.solid_arc(cx - r, cy - r, d, 90, 90 - sweep,
                           clockwise=True, style="F")
        elif pct >= 100:
            # Full circle — use ellipse, not solid_arc (avoids gap artefacts)
            self.set_fill_color(*color)
            self.ellipse(cx - r, cy - r, d, d, style="F")


pdf = ReportPDF()
pdf.set_left_margin(MARGIN)
pdf.set_right_margin(MARGIN)
pdf.alias_nb_pages()
pdf.set_auto_page_break(auto=False)

# ── Register Inter font family ─────────────────────────────────────
pdf.add_font("Inter", "", f"{FONT_DIR}/Inter-Regular.ttf")
pdf.add_font("Inter", "B", f"{FONT_DIR}/Inter-Bold.ttf")
pdf.add_font("Inter", "I", f"{FONT_DIR}/Inter-Italic.ttf")
pdf.add_font("Inter", "BI", f"{FONT_DIR}/Inter-BoldItalic.ttf")
pdf.add_font("InterMedium", "", f"{FONT_DIR}/Inter-Medium.ttf")
pdf.add_font("InterSemiBold", "", f"{FONT_DIR}/Inter-SemiBold.ttf")
pdf.add_font("InterExtraBold", "", f"{FONT_DIR}/Inter-ExtraBold.ttf")
pdf.add_font("InterBlack", "", f"{FONT_DIR}/Inter-Black.ttf")
pdf.add_font("InterLight", "", f"{FONT_DIR}/Inter-Light.ttf")
```

## Cover Page

Full-bleed JET Orange background with white title, hero KPI, and metadata. The cover is the opening bookend — first and last pages must be JET Orange per the brand guidelines.

```python
pdf.add_page()
pdf._is_cover = True
pdf._no_footer_pages.add(pdf.page_no())

# Full-bleed JET Orange — bookend principle
pdf.set_fill_color(*JET_ORANGE)
pdf.rect(0, 0, PAGE_W, PAGE_H, style="F")

# Report type label
pdf.set_xy(MARGIN, 50)
pdf.set_font("Inter", "B", 10)
pdf.set_text_color(*COVER_TEXT_WARM)
pdf.cell(0, 5, "WEEKLY REPORT", new_x="LMARGIN", new_y="NEXT")

# Title (using InterBlack — official JET cover headline weight)
pdf.set_x(MARGIN)
pdf.set_font("InterBlack", "", 44)
pdf.set_text_color(*WHITE)
pdf.cell(0, 24, "Report Title", new_x="LMARGIN", new_y="NEXT")
pdf.set_x(MARGIN)
pdf.cell(0, 24, "Line Two", new_x="LMARGIN", new_y="NEXT")

# Date range
pdf.ln(SPACE_SM)
pdf.set_x(MARGIN)
pdf.set_font("InterMedium", "", 10)
pdf.set_text_color(*COVER_TEXT_SAND)
pdf.cell(0, 6, "Mon 2026-02-23 to Fri 2026-02-27")

# Decorative divider
pdf.ln(SPACE_MD + SPACE_XS)
pdf.set_draw_color(*COVER_DIVIDER)
pdf.line(MARGIN, pdf.get_y(), MARGIN + 60, pdf.get_y())
pdf.ln(SPACE_LG)

# Hero KPI (large number, white on orange)
pdf.set_x(MARGIN)
pdf.set_font("InterBlack", "", 80)
pdf.set_text_color(*WHITE)
pdf.cell(0, 35, "592", new_x="LMARGIN", new_y="NEXT")
pdf.set_x(MARGIN)
pdf.set_font("InterMedium", "", 13)
pdf.set_text_color(*COVER_TEXT_WARM)
pdf.cell(0, 6, "description of the hero metric")
```

## KPI Cards (Cover Page)

Row of metric cards at a fixed vertical position with optional delta indicators. On an orange cover page, use a **warm sandy-orange tint** (`COVER_KPI_BG`) as card background — lighter than JET Orange, with white text throughout and generous rounded corners (~5mm). **Always use a fixed `card_y`, never `pdf.get_y()`.**

```python
card_y = 210  # Fixed y-position for all cards
kpi_data = [
    # (value, label, delta_text_or_None)
    ("5,258", "Total Items",    "+12% WoW"),
    ("11.3%", "Adoption Rate",  "+2.1pp"),
    ("58",    "Teams",          None),
    ("127",   "Repositories",   "+8 new"),
]
kpi_x = MARGIN + 3
kpi_gap = 3
kpi_w = (CONTENT_W - 6 - kpi_gap * (len(kpi_data) - 1)) / len(kpi_data)
kpi_h = 32 if any(d for *_, d in kpi_data) else 28  # Taller if deltas

for val, label, delta in kpi_data:
    # Card background (warm sandy-orange tint on orange cover page)
    pdf.set_fill_color(*COVER_KPI_BG)
    pdf.rect(kpi_x, card_y, kpi_w, kpi_h, style="F",
             round_corners=True, corner_radius=5)
    # Inset text by CARD_PADDING to prevent clipping at card edges
    CARD_PADDING = 4
    text_w = kpi_w - 2 * CARD_PADDING
    text_x = kpi_x + CARD_PADDING
    # Value (white)
    pdf.set_xy(text_x, card_y + 4)
    pdf.set_font("InterExtraBold", "", 22 if len(kpi_data) <= 4 else 18)
    pdf.set_text_color(*WHITE)
    pdf.cell(text_w, 10, val, align="C")
    # Label (white, not grey)
    pdf.set_xy(text_x, card_y + 15)
    pdf.set_font("Inter", "", 7)
    pdf.set_text_color(*WHITE)
    pdf.cell(text_w, 4, label, align="C")
    # Delta (optional) — WHITE on cover page (orange bg makes green/red illegible)
    if delta:
        pdf.set_xy(text_x, card_y + 22)
        pdf.set_font("Inter", "B", 6.5)
        pdf.set_text_color(*WHITE)
        pdf.cell(text_w, 4, delta, align="C")
    kpi_x += kpi_w + kpi_gap
```

## Executive Summary Text

Open with a **key takeaway** (the "so what?"), then supporting detail. Section headings should be insights, not labels. Content pages use the warm Mozzarella background (`MOZZARELLA` / `#EFEDEA`) — not plain white. Use `band_color` on the first page of each section for a coloured header band.

```python
pdf.content_page(section_title="Executive Summary", section_num="Section 01")

# Heading states the insight, not just "Executive Summary"
pdf.section_heading("Payment failures drove 48% of all incidents")

# Key takeaway -- the one sentence an exec reads if they read nothing else
pdf.key_takeaway(
    "Incident volume rose **12% WoW** to **592**, with payment service "
    "instability accounting for nearly half of all production issues."
)

# Supporting detail
pdf.set_font("Inter", "", 11)
pdf.set_text_color(*DARK_TEXT)
pdf.multi_cell(
    CONTENT_W, 5,
    "During the week of ..., [subject] was adopted across "
    "**N organisations** and **N repositories**, processing **N items**.",
    markdown=True,
    align="L",
)
pdf.ln(1)  # sub-SPACE_XS: tight coupling between TLDR paragraphs
pdf.multi_cell(
    CONTENT_W, 5,
    "A total of **N items** were created this week, giving an adoption "
    "rate of **X%**. Team A leads with **N items** (X% of total).",
    markdown=True,
    align="L",
)
```

## Using local_context()

`local_context()` scopes style changes (font, colour, opacity) so they auto-revert when the block exits. Use it everywhere to prevent colour/font "leaking" bugs.

```python
# Style is scoped -- no need to manually reset after the block
with pdf.local_context(text_color=CHARCOAL, fill_color=ALT_ROW):
    pdf.set_font("Inter", "B", 12)
    pdf.cell(CONTENT_W, 8, "This is bold 12pt charcoal", fill=True)

# Back to whatever font/colour was set before the block
pdf.cell(CONTENT_W, 8, "This uses the previous style")

# Also works for draw styles
with pdf.local_context(draw_color=JET_ORANGE, line_width=0.8):
    pdf.line(MARGIN, pdf.get_y(), PAGE_W - MARGIN, pdf.get_y())

# Transparency (useful for watermarks or layered charts)
with pdf.local_context(fill_opacity=0.3):
    pdf.set_fill_color(*JET_ORANGE)
    pdf.rect(MARGIN, pdf.get_y(), CONTENT_W, 20, style="F")
```

**When to use `local_context()`:**
- Drawing helper methods (sparklines, pie charts, traffic lights)
- Any block where you change colours temporarily
- Overlaying transparent elements
- Anywhere you'd otherwise need a "reset" call after

## Methodology / Callout Box

Rounded rectangle callout box with auto-sized height using `dry_run=True`.

```python
def draw_callout(pdf, title="", body="", accent_color=JET_ORANGE, bg_color=MOZZARELLA_T1):
    """Callout box with left accent bar. Height auto-calculated from content."""
    y = pdf.get_y()
    pad_y = 4
    cr = 3
    bar_w = 2.5
    text_x = CONTENT_X + 8
    text_w = CONTENT_W - 14

    # ── Measure actual body height via dry-run multi_cell ────────
    title_h = 5 if title else 0
    body_h = 0
    if body:
        pdf.set_font("Inter", "", 8)
        body_h = pdf.multi_cell(
            text_w, 3.5, body, align="L", dry_run=True, output="HEIGHT"
        )

    box_h = pad_y + title_h + body_h + pad_y

    _rounded_rect_clip(pdf, CONTENT_X, y, CONTENT_W, box_h, cr)
    pdf.set_fill_color(*accent_color)
    pdf.rect(CONTENT_X, y, bar_w, box_h, style="F")
    pdf.set_fill_color(*bg_color)
    pdf.rect(CONTENT_X + bar_w, y, CONTENT_W - bar_w, box_h, style="F")
    _restore_gfx_state(pdf)

    inner_y = y + pad_y
    if title:
        pdf.set_xy(text_x, inner_y)
        pdf.set_font("Inter", "B", 8)
        pdf.set_text_color(*CHARCOAL)
        pdf.cell(text_w, 4, title)
        inner_y += title_h
    if body:
        pdf.set_xy(text_x, inner_y)
        pdf.set_font("Inter", "", 8)
        pdf.set_text_color(*CHARCOAL)
        pdf.multi_cell(text_w, 3.5, body, align="L")

    pdf.set_y(y + box_h + SPACE_MD)
```

**Key technique**: `multi_cell(..., dry_run=True, output="HEIGHT")` returns the exact rendered height without emitting any PDF content. This ensures symmetric `pad_y` above and below the text — no more oversized boxes.

## Side-by-Side Chart Cards

Two top-10 horizontal bar charts displayed as cards next to each other. Best placed below the executive summary on page 2.

> **CRITICAL — Two-column Y alignment**: Both cards MUST use the same `cards_y` variable — never compute Y independently for left vs right. For any ad-hoc two-column layout, always save `start_y = pdf.get_y()` before drawing column 1, then `pdf.set_xy(right_x, start_y)` before column 2. After both columns, `pdf.set_y(max(left_end_y, right_end_y))`. See gotchas-and-errors.md for the full pattern.

> **CRITICAL — Chart colour consistency**: All charts on one page MUST use the same colour palette (default: `BAR_COLORS_ORANGE`) unless the charts compare fundamentally distinct categories that need visual distinction (e.g., "Revenue" vs "Cost"). Two charts showing the same type of metric (e.g., two top-10 rankings) should both use orange.

```python
# Card layout constants
cards_y = box_y + box_h + SPACE_MD   # Position below methodology box
CARD_GAP = GUTTER
CARD_W = grid_span(6)
CARD_PADDING = 5
CARD_BG = MOZZARELLA_T1
ROW_H_CHART = 13
CARD_HEADER_H = 22
CARD_INNER_W = CARD_W - 2 * CARD_PADDING
CARD_CONTENT_H = 10 * ROW_H_CHART + 4
CARD_H = CARD_HEADER_H + CARD_CONTENT_H

# ── Left card ───────────────────────────────────────────────────
card_x_l = MARGIN
pdf.set_fill_color(*CARD_BG)
pdf.set_draw_color(*BORDER)
pdf.rect(card_x_l, cards_y, CARD_W, CARD_H, style="DF",
         round_corners=True, corner_radius=3)

# Card title + subtitle
pdf.set_xy(card_x_l + CARD_PADDING, cards_y + 7)
pdf.set_font("Inter", "B", 10)
pdf.set_text_color(*CHARCOAL)
pdf.cell(CARD_INNER_W, 5, "Top 10 Category A")
pdf.set_xy(card_x_l + CARD_PADDING, cards_y + 13)
pdf.set_font("Inter", "", 6.5)
pdf.set_text_color(*MID_TEXT)
pdf.cell(CARD_INNER_W, 4, "Ranked by metric")

# Rows
top10_left = sorted_items_a[:10]
max_val_left = top10_left[0][1]
bar_max_w = CARD_INNER_W * 0.38

for i, (name, count) in enumerate(top10_left):
    row_y = cards_y + CARD_HEADER_H + i * ROW_H_CHART
    bar_w = (count / max_val_left) * bar_max_w
    bar_w = min(bar_w, bar_max_w)  # clamp to allocated width

    # Rank
    pdf.set_xy(card_x_l + CARD_PADDING, row_y + 1)
    pdf.set_font("Inter", "B", 7)
    pdf.set_text_color(*MID_TEXT)
    pdf.cell(8, 5, str(i + 1), align="C")

    # Name (truncate if needed)
    display = name if len(name) <= 22 else name[:20] + ".."
    pdf.set_xy(card_x_l + CARD_PADDING + 9, row_y + 1)
    pdf.set_font("Inter", "B" if i == 0 else "", 7)
    pdf.set_text_color(*DARK_TEXT)
    pdf.cell(CARD_INNER_W * 0.45, 5, display)

    # Bar
    bar_x = card_x_l + CARD_PADDING + CARD_INNER_W * 0.52
    pdf.set_fill_color(*BAR_COLORS_ORANGE[i])
    pdf.rect(bar_x, row_y + 2.5, max(bar_w, 1.5), 3.5, style="F",
             round_corners=True, corner_radius=1.2)

    # Count (clamp position so label stays inside card)
    count_x = min(bar_x + bar_w + 2,
                  card_x_l + CARD_W - CARD_PADDING - 12)
    pdf.set_xy(count_x, row_y + 1)
    pdf.set_font("Inter", "B", 7)
    pdf.set_text_color(*MID_TEXT)
    pdf.cell(12, 5, str(count))

    # Separator (except last)
    if i < 9:
        sep_y = row_y + ROW_H_CHART - 0.5
        pdf.set_draw_color(*BORDER)
        pdf.line(card_x_l + CARD_PADDING + 8, sep_y,
                 card_x_l + CARD_W - CARD_PADDING, sep_y)

# ── Right card ──────────────────────────────────────────────────
card_x_r = MARGIN + CARD_W + CARD_GAP
pdf.set_fill_color(*CARD_BG)
pdf.set_draw_color(*BORDER)
pdf.rect(card_x_r, cards_y, CARD_W, CARD_H, style="DF",
         round_corners=True, corner_radius=3)

# Card title + subtitle
pdf.set_xy(card_x_r + CARD_PADDING, cards_y + 7)
pdf.set_font("Inter", "B", 10)
pdf.set_text_color(*CHARCOAL)
pdf.cell(CARD_INNER_W, 5, "Top 10 Category B")
pdf.set_xy(card_x_r + CARD_PADDING, cards_y + 13)
pdf.set_font("Inter", "", 6.5)
pdf.set_text_color(*MID_TEXT)
pdf.cell(CARD_INNER_W, 4, "Ranked by metric")

# Rows
top10_right = sorted_items_b[:10]
max_val_right = top10_right[0][1]
bar_max_w_r = CARD_INNER_W * 0.28

for i, (name, count) in enumerate(top10_right):
    row_y = cards_y + CARD_HEADER_H + i * ROW_H_CHART
    bar_w = (count / max_val_right) * bar_max_w_r
    bar_w = min(bar_w, bar_max_w_r)  # clamp to allocated width

    # Rank
    pdf.set_xy(card_x_r + CARD_PADDING, row_y + 1)
    pdf.set_font("Inter", "B", 7)
    pdf.set_text_color(*MID_TEXT)
    pdf.cell(8, 5, str(i + 1), align="C")

    # Name (truncate if needed - longer names for right card)
    display = name if len(name) <= 28 else name[:26] + ".."
    pdf.set_xy(card_x_r + CARD_PADDING + 9, row_y + 1)
    pdf.set_font("Inter", "B" if i == 0 else "", 7)
    pdf.set_text_color(*DARK_TEXT)
    pdf.cell(CARD_INNER_W * 0.55, 5, display)

    # Bar (blue)
    bar_x = card_x_r + CARD_PADDING + CARD_INNER_W * 0.62
    pdf.set_fill_color(*BAR_COLORS_BLUE[i])
    pdf.rect(bar_x, row_y + 2.5, max(bar_w, 1.5), 3.5, style="F",
             round_corners=True, corner_radius=1.2)

    # Count (clamp position so label stays inside card)
    count_x = min(bar_x + bar_w + 2,
                  card_x_r + CARD_W - CARD_PADDING - 12)
    pdf.set_xy(count_x, row_y + 1)
    pdf.set_font("Inter", "B", 7)
    pdf.set_text_color(*MID_TEXT)
    pdf.cell(12, 5, str(count))

    # Separator (except last)
    if i < 9:
        sep_y = row_y + ROW_H_CHART - 0.5
        pdf.set_draw_color(*BORDER)
        pdf.line(card_x_r + CARD_PADDING + 8, sep_y,
                 card_x_r + CARD_W - CARD_PADDING, sep_y)
```

## Data Table with Inline Bars

Full-width table with ranking, alternating rows, inline gradient bars, and a totals row.
Uses the **rect-first approach**: draw a full-width row background rect first, then overlay text cells (without fill), then draw the gradient bar on top. This avoids colour desync when `set_fill_color` is called for the bar, which would corrupt subsequent `cell(..., fill=True)` calls.

```python
pdf.add_page()
pdf.section_heading("All Items", f"Breakdown of all {len(items)} items")

col_w = [9, 80, 16, 16, 59]
hdrs = ["#", "Name", "Count", "%", ""]
aligns = ["C", "L", "C", "C", "L"]
ROW_H = 5.5
MAX_Y = 275  # Page overflow threshold
total_row_w = sum(col_w)

pdf.table_header(col_w, hdrs, aligns)

sorted_items = sorted(items.items(), key=lambda x: -x[1])
max_bar = sorted_items[0][1]
total = sum(v for _, v in sorted_items)

for rank, (name, count) in enumerate(sorted_items, 1):
    pct = count / total * 100
    bar_w = (count / max_bar) * (col_w[4] - 5)
    bar_w = min(bar_w, col_w[4] - 5)  # defensive clamp to column width

    # Page overflow check
    if pdf.get_y() + ROW_H > MAX_Y:
        pdf.add_page()
        pdf.continuation_header("All Items (cont.)", col_w, hdrs, aligns)

    row_y = pdf.get_y()

    # Full-width row background rect (drawn first)
    row_bg = ALT_ROW if rank % 2 == 0 else WHITE
    pdf.set_fill_color(*row_bg)
    pdf.rect(MARGIN, row_y, total_row_w, ROW_H, style="F")

    # Text cells (no fill — background already drawn by rect)
    pdf.set_xy(MARGIN, row_y)
    pdf.set_text_color(*DARK_TEXT)

    # Rank
    pdf.set_font("Inter", "", 8)
    pdf.cell(col_w[0], ROW_H, str(rank), align="C")

    # Name (bold for top 5)
    pdf.set_font("Inter", "B" if rank <= 5 else "", 8)
    pdf.cell(col_w[1], ROW_H, name)

    # Count
    pdf.set_font("Inter", "B", 8)
    pdf.cell(col_w[2], ROW_H, str(count), align="C")

    # Percentage
    pdf.set_font("Inter", "", 8)
    pdf.set_text_color(*MID_TEXT)
    pdf.cell(col_w[3], ROW_H, f"{pct:.1f}%", align="C")

    # Inline gradient bar (drawn on top of background)
    bar_x = pdf.get_x() + 2
    bar_y_pos = row_y + 1.2
    if bar_w > 0.5:
        # Use BAR_COLORS_ORANGE gradient (index capped at 9)
        pdf.set_fill_color(*BAR_COLORS_ORANGE[min(rank - 1, 9)])
        pdf.rect(bar_x, bar_y_pos, bar_w, 3, style="F",
                 round_corners=True, corner_radius=1)

    pdf.set_xy(MARGIN, row_y + ROW_H)
```

## Totals Row

Place immediately after the last data row of a table.

```python
y = pdf.get_y()
total_w = sum(col_w)
pdf.set_draw_color(*CHARCOAL)
pdf.line(MARGIN, y, MARGIN + total_w, y)
pdf.set_font("Inter", "B", 8)
pdf.set_text_color(*CHARCOAL)
pdf.set_fill_color(*MOZZARELLA_T1)
pdf.cell(col_w[0], 6, "", fill=True)
pdf.cell(col_w[1], 6, f"TOTAL ({len(items)} items)", fill=True)
pdf.cell(col_w[2], 6, str(total), fill=True, align="C")
pdf.cell(col_w[3], 6, "100%", fill=True, align="C")
pdf.cell(col_w[4], 6, "", fill=True)
pdf.ln()
```

## Inner-Page KPI Row

Lightweight KPI cards for inner pages (light background, unlike the dark cover page cards). Supports an optional delta/change indicator showing period-over-period change.

```python
# ── Inner-page KPI row ──────────────────────────────────────────
kpi_inner_data = [
    ("592", "Total Incidents", "+12%", "up"),
    ("48%", "Mitigation Rate", "-3%", "down"),
    ("4.2h", "Avg Resolution", "+0.5h", "up"),
    ("97.8%", "Uptime", "+0.1%", "up"),
]

kpi_count = len(kpi_inner_data)
kpi_gap = GUTTER
kpi_w = grid_span(3)  # 4-column layout
kpi_h = 30
kpi_y = pdf.get_y()

for idx, (value, label, delta, direction) in enumerate(kpi_inner_data):
    kpi_x = MARGIN + idx * (kpi_w + kpi_gap)

    # Card background (light, warm)
    pdf.set_fill_color(*MOZZARELLA_T1)
    pdf.set_draw_color(*BORDER)
    pdf.rect(kpi_x, kpi_y, kpi_w, kpi_h, style="DF",
             round_corners=True, corner_radius=3)

    # Inset text by CARD_PADDING to prevent clipping at card edges
    CARD_PADDING = 4
    text_w = kpi_w - 2 * CARD_PADDING
    text_x = kpi_x + CARD_PADDING

    # Value
    pdf.set_xy(text_x, kpi_y + 5)
    pdf.set_font("InterExtraBold", "", 20)
    pdf.set_text_color(*CHARCOAL)
    pdf.cell(text_w, 9, value, align="C")

    # Label
    pdf.set_xy(text_x, kpi_y + 15)
    pdf.set_font("Inter", "", 7)
    pdf.set_text_color(*MID_TEXT)
    pdf.cell(text_w, 4, label, align="C")

    # Delta indicator (optional)
    if delta:
        # Colour: green for positive-good, red for negative-bad
        # Adapt logic to your metric's polarity
        is_positive = direction == "up"
        delta_color = JET_ORANGE
        arrow = chr(9650) if is_positive else chr(9660)  # ▲ or ▼
        # Inter supports Unicode arrows -- ▲/▼ work with Inter font
        prefix = "+" if is_positive else ""
        pdf.set_xy(text_x, kpi_y + 21)
        pdf.set_font("Inter", "B", 6.5)
        pdf.set_text_color(*delta_color)
        pdf.cell(text_w, 4, delta, align="C")

pdf.set_y(kpi_y + kpi_h + SPACE_SM)  # Advance cursor past KPI row
```

**Notes:**
- Use `MOZZARELLA_T1` background for inner pages (not the dark cover card style).
- `kpi_w` is auto-calculated from `kpi_count` so the pattern works for 2-5 cards.
- Delta indicators use `JET_ORANGE` — consistent with the STAT_ROW component. Arrows (▲/▼) indicate direction.
- Inter supports Unicode characters including arrows -- you can use `\u25B2` (▲) and `\u25BC` (▼) for trend indicators.

## Callout Box Variants

Three callout box variants using the **left accent bar** style (clipping path technique) — consistent with the JET quote block design. Each variant uses a different accent colour for the left bar, with a subtle tinted background.

### Warning Box

```python
# Use draw_callout() for consistent auto-height calculation:
draw_callout(pdf, title="WARNING", body="Warning message text goes here.",
             accent_color=WARNING, bg_color=WARNING_BG)
```

### Info Box

```python
draw_callout(pdf, title="NOTE", body="Informational note text goes here.",
             accent_color=INFO, bg_color=INFO_BG)
```

### Success Box

```python
draw_callout(pdf, title="COMPLETE", body="Success/completion message text goes here.",
             accent_color=SUCCESS, bg_color=SUCCESS_BG)
```

**Design notes:**
- All callout boxes use the **left accent bar + clipping path** technique, consistent with the JET quote block style.
- The accent bar colour matches the callout type (WARNING orange, INFO orange, SUCCESS green).
- Background uses a subtle tint matching the accent — not a solid colour.

**Colour mapping for callout boxes:**

| Variant | Background | Accent Bar | Title colour |
|---------|-----------|------------|-------------|
| Warning | `WARNING_BG` | `WARNING` | `CHARCOAL` |
| Info | `INFO_BG` | `INFO` | `CHARCOAL` |
| Success | `SUCCESS_BG` | `SUCCESS` | `CHARCOAL` |

## Pagination: Totals Row Safety

When a table's totals row might land on a different page from the last data row, ensure it stays together by checking available space before rendering.

```python
TOTALS_ROW_H = 6
SEPARATOR_H = 1

# After the last data row, check if there's room for separator + totals
if pdf.get_y() + SEPARATOR_H + TOTALS_ROW_H > MAX_Y:
    pdf.add_page()
    pdf.continuation_header("Table Title (cont.)", col_w, hdrs, aligns)

# Now render the totals row (separator line + row)
y = pdf.get_y()
total_w = sum(col_w)
pdf.set_draw_color(*CHARCOAL)
pdf.line(MARGIN, y, MARGIN + total_w, y)
pdf.set_font("Inter", "B", 8)
pdf.set_text_color(*CHARCOAL)
pdf.set_fill_color(*MOZZARELLA_T1)
pdf.cell(col_w[0], TOTALS_ROW_H, "", fill=True)
pdf.cell(col_w[1], TOTALS_ROW_H, f"TOTAL ({count} items)", fill=True)
pdf.cell(col_w[2], TOTALS_ROW_H, str(total), fill=True, align="C")
pdf.cell(col_w[3], TOTALS_ROW_H, "100%", fill=True, align="C")
pdf.cell(col_w[4], TOTALS_ROW_H, "", fill=True)
pdf.ln()
```

## Pagination: Page Break Before Section

Force a new page before a section if there isn't enough space to fit the heading plus at least a few lines of content.

```python
MIN_SECTION_SPACE = 50  # mm - heading + at least a few rows or a paragraph

if pdf.get_y() + MIN_SECTION_SPACE > MAX_Y:
    pdf.add_page()

pdf.section_heading("New Section Title", "Optional subtitle")
```

This avoids orphaned section headings at the bottom of a page with no content beneath them.

## Multi-Line Table Rows

For table rows where a cell's text may wrap to multiple lines, use `multi_cell()` for the wrapping column and fixed `cell()` for the others. Key technique: measure the height first, then draw all cells at the same row height.

```python
ROW_H_MIN = 5.5  # Minimum row height (single-line)
WRAP_COL_IDX = 1  # Which column wraps (e.g. "Description")

for rank, row_data in enumerate(rows, 1):
    name, description, count, pct = row_data

    # 1. Measure the height of the wrapping cell
    wrap_w = col_w[WRAP_COL_IDX]
    pdf.set_font("Inter", "", 8)
    # get_multi_cell_height is not available in fpdf2 -- use this approach:
    line_h = 4.0
    # Estimate wrapped lines by splitting on width
    n_lines = max(1, len(pdf.multi_cell(
        wrap_w, line_h, description,
        dry_run=True, output="LINES"
    )))
    row_h = max(ROW_H_MIN, n_lines * line_h + 1.5)

    # 2. Page overflow check (with the actual row height)
    if pdf.get_y() + row_h > MAX_Y:
        pdf.add_page()
        pdf.continuation_header("Table (cont.)", col_w, hdrs, aligns)

    row_y = pdf.get_y()

    # 3. Alternating row background (draw full-width rect first)
    pdf.set_fill_color(*(ALT_ROW if rank % 2 == 0 else WHITE))
    pdf.rect(MARGIN, row_y, sum(col_w), row_h, style="F")

    # 4. Fixed-height cells (rank, count, pct)
    pdf.set_xy(MARGIN, row_y)
    pdf.set_font("Inter", "", 8)
    pdf.set_text_color(*DARK_TEXT)
    pdf.cell(col_w[0], row_h, str(rank), align="C")

    # 5. Wrapping cell (description)
    pdf.set_xy(MARGIN + col_w[0], row_y + 0.75)
    pdf.set_font("Inter", "", 8)
    pdf.multi_cell(wrap_w, line_h, description)

    # 6. Remaining fixed cells
    pdf.set_xy(MARGIN + col_w[0] + col_w[1], row_y)
    pdf.set_font("Inter", "B", 8)
    pdf.cell(col_w[2], row_h, str(count), align="C")
    pdf.set_font("Inter", "", 8)
    pdf.set_text_color(*MID_TEXT)
    pdf.cell(col_w[3], row_h, f"{pct:.1f}%", align="C")

    # 7. Advance y to below this row
    pdf.set_y(row_y + row_h)
```

**Key points:**
- Use `multi_cell(..., dry_run=True, output="LINES")` (fpdf2 >= 2.7.6) to measure line count without rendering.
- Draw the background `rect()` first at the full `row_h`, then overlay the text cells.
- Position each cell explicitly with `set_xy()` since `multi_cell()` moves the cursor.
- For older fpdf2 versions without `dry_run`, estimate lines manually: `ceil(pdf.get_string_width(text) / wrap_w)`.

## Cover Page: Dynamic Titles and KPI Card Count

### Multi-Line Titles

For titles that may span 1-3 lines, use `multi_cell()` instead of separate `cell()` calls. Calculate font size based on title length to prevent overflow.

```python
title = "Production Incident Report"

# Choose font size based on title length
if len(title) <= 20:
    title_size = 48
elif len(title) <= 35:
    title_size = 44
else:
    title_size = 34

pdf.set_x(MARGIN)
pdf.set_font("InterBlack", "", title_size)
pdf.set_text_color(*WHITE)
pdf.multi_cell(CONTENT_W - 10, title_size * 0.55, title)
```

### Dynamic KPI Card Count

Auto-calculate card widths based on the number of KPI items (supports 2-5 cards). See the [KPI Cards (Cover Page)](#kpi-cards-cover-page) pattern above -- it already auto-calculates widths.

## Data Table with table() API

fpdf2's built-in `table()` context manager replaces manual cell-by-cell table construction. It handles column widths, heading repetition on page breaks, alternating row fills, and markdown in cells automatically.

```python
pdf.add_page()
pdf.section_heading("All Items", f"Breakdown of all {len(items)} items")

sorted_items = sorted(items.items(), key=lambda x: -x[1])
total = sum(v for _, v in sorted_items)

with pdf.table(
    col_widths=(9, 80, 20, 20, 51),
    borders_layout=TableBordersLayout.NONE,
    cell_fill_mode=TableCellFillMode.ROWS,
    cell_fill_color=ALT_ROW,
    headings_style=TABLE_HEADING_STYLE,
    line_height=6,
    markdown=True,
    repeat_headings=1,       # Repeat header row on each new page
    padding=1,
) as table:
    # Header row
    row = table.row()
    for h in ["#", "Name", "Count", "%", ""]:
        row.cell(h)

    # Data rows
    for rank, (name, count) in enumerate(sorted_items, 1):
        pct = count / total * 100
        row = table.row()
        row.cell(str(rank))
        row.cell(f"**{name}**" if rank <= 5 else name)
        row.cell(str(count))
        row.cell(f"{pct:.1f}%")
        row.cell("")  # Could add inline bar via custom rendering

# Totals row (outside the table context, drawn manually)
y = pdf.get_y()
total_w = 180  # sum of col_widths
pdf.set_draw_color(*CHARCOAL)
pdf.line(MARGIN, y, MARGIN + total_w, y)
with pdf.local_context(
    text_color=CHARCOAL, fill_color=MOZZARELLA_T1,
):
    pdf.set_font("Inter", "B", 8)
    pdf.cell(9, 6, "", fill=True)
    pdf.cell(80, 6, f"TOTAL ({len(sorted_items)} items)", fill=True)
    pdf.cell(20, 6, str(total), fill=True, align="C")
    pdf.cell(20, 6, "100%", fill=True, align="C")
    pdf.cell(51, 6, "", fill=True)
    pdf.ln()
```

**When to use `table()` vs manual cells:**
- Use `table()` for standard data tables, especially multi-page ones -- it handles header repetition and alternating fills automatically.
- Use manual cells when you need pixel-precise control, e.g. inline gradient bars, custom row backgrounds, or mixed-height rows.
- Both approaches work. The `table()` API produces cleaner code with fewer bugs.

### ColSpan and RowSpan

The `table()` API supports `colspan` and `rowspan` on individual cells:

```python
with pdf.table(
    col_widths=(40, 40, 40, 60),
    borders_layout=TableBordersLayout.NONE,
    cell_fill_mode=TableCellFillMode.ROWS,
    cell_fill_color=ALT_ROW,
    headings_style=TABLE_HEADING_STYLE,
    line_height=6,
) as table:
    # Header with colspan
    row = table.row()
    row.cell("Service")
    row.cell("Region")
    row.cell("Metrics", colspan=2)  # Spans 2 columns

    # Data rows
    row = table.row()
    row.cell("Payment Gateway")
    row.cell("EU")
    row.cell("99.2%")
    row.cell("1.2s p99")
```

## Traffic Light Status Table

Table with coloured status dots for instant at-a-glance scanning. Best for incident status, service health, or any categorical status display.

```python
pdf.section_heading("Service health degraded in 3 of 12 regions")

statuses = [
    ("Payment Gateway",  "red",    "P1 - 45min outage, 12K orders affected"),
    ("Order Service",    "orange", "Degraded - elevated latency p99 > 2s"),
    ("Menu Service",     "green",  "Healthy - no incidents"),
    ("Delivery Tracker", "green",  "Healthy - no incidents"),
    ("Auth Service",     "orange", "Degraded - intermittent 401s from cache"),
    ("Search",           "green",  "Healthy - no incidents"),
]

col_w = [6, 50, 12, 112]
hdrs = ["", "Service", "Status", "Detail"]
aligns = ["C", "L", "C", "L"]
ROW_H = 7

pdf.table_header(col_w, hdrs, aligns)

for i, (service, status, detail) in enumerate(statuses):
    row_y = pdf.get_y()

    # Row background
    pdf.set_fill_color(*(ALT_ROW if i % 2 == 0 else WHITE))
    pdf.rect(MARGIN, row_y, sum(col_w), ROW_H, style="F")

    # Traffic light dot
    dot_x = MARGIN + 1.5
    dot_y = row_y + 2
    pdf.traffic_light(dot_x, dot_y, status)

    # Service name
    pdf.set_xy(MARGIN + col_w[0], row_y)
    with pdf.local_context(text_color=DARK_TEXT):
        pdf.set_font("Inter", "B" if status == "red" else "", 8)
        pdf.cell(col_w[1], ROW_H, service)

    # Status label (always Charcoal text — dots carry the colour)
    status_labels = {"green": "OK", "orange": "WARN", "red": "CRIT", "gray": "N/A", "grey": "N/A"}
    pdf.set_xy(MARGIN + col_w[0] + col_w[1], row_y)
    with pdf.local_context(text_color=CHARCOAL):
        pdf.set_font("Inter", "B", 7)
        pdf.cell(col_w[2], ROW_H, status_labels.get(status, "?"), align="C")

    # Detail
    pdf.set_xy(MARGIN + col_w[0] + col_w[1] + col_w[2], row_y)
    with pdf.local_context(text_color=MID_TEXT):
        pdf.set_font("Inter", "", 8)
        pdf.cell(col_w[3], ROW_H, detail)

    pdf.set_y(row_y + ROW_H)
```

**Inline status variant** — when you need dot + label in a single cell without a dedicated dot column, use `traffic_light_inline()`:

```python
# Inline dot + label (no separate dot column needed)
row_y = pdf.get_y()
pdf.traffic_light_inline(MARGIN + 4, row_y, "green", "Ready", row_h=7)
```

## Sparkline in Table

Add mini trend lines inside table rows to show directional trends alongside numbers. Best used in KPI summary tables or ranking tables.

```python
# Example: Team performance table with sparklines
col_w = [50, 20, 20, 30, 60]
hdrs = ["Team", "This Week", "Last Week", "Change", "Trend (8w)"]
aligns = ["L", "C", "C", "C", "C"]
ROW_H = 10  # Taller rows to fit sparklines

teams = [
    ("Payments",  142, 128, [95, 102, 88, 110, 115, 120, 128, 142]),
    ("Logistics", 89,  94,  [70, 75, 80, 85, 90, 88, 94, 89]),
    ("Menu",      56,  52,  [40, 42, 45, 48, 50, 51, 52, 56]),
]

pdf.table_header(col_w, hdrs, aligns)

for i, (name, this_week, last_week, trend) in enumerate(teams):
    row_y = pdf.get_y()
    change = this_week - last_week
    change_pct = change / last_week * 100

    pdf.set_fill_color(*(ALT_ROW if i % 2 == 0 else WHITE))
    pdf.rect(MARGIN, row_y, sum(col_w), ROW_H, style="F")

    pdf.set_xy(MARGIN, row_y)
    with pdf.local_context(text_color=DARK_TEXT):
        pdf.set_font("Inter", "B", 8)
        pdf.cell(col_w[0], ROW_H, name)
    with pdf.local_context(text_color=DARK_TEXT):
        pdf.set_font("Inter", "B", 8)
        pdf.cell(col_w[1], ROW_H, str(this_week), align="C")
    with pdf.local_context(text_color=MID_TEXT):
        pdf.set_font("Inter", "", 8)
        pdf.cell(col_w[2], ROW_H, str(last_week), align="C")

    # Change with colour
    delta_color = SUCCESS if change >= 0 else DANGER
    sign = "+" if change >= 0 else ""
    with pdf.local_context(text_color=delta_color):
        pdf.set_font("Inter", "B", 8)
        pdf.cell(col_w[3], ROW_H, f"{sign}{change_pct:.0f}%", align="C")

    # Sparkline in last column
    spark_x = MARGIN + sum(col_w[:4]) + 5
    spark_y = row_y + 2
    spark_w = col_w[4] - 10
    spark_h = ROW_H - 4
    line_color = SUCCESS if trend[-1] >= trend[0] else DANGER
    pdf.sparkline(spark_x, spark_y, spark_w, spark_h, trend, color=line_color)

    pdf.set_y(row_y + ROW_H)
```

## Pie Charts

The `pie_chart()` method on `ReportPDF` draws a simple two-segment pie (filled arc + track). It is a low-level visual primitive — **always use it inside a higher-level component** like `draw_graph_card_grid()` rather than rendering standalone pies with inline layout code. The Graph Card Grid pairs each pie with a title, progress bar, percentage label, and description in a reusable 2-column layout.

See **Graph Card Grid** below for the recommended usage pattern.

## PDF Bookmarks / Document Outline

Use `pdf.start_section()` to create navigable bookmarks in the PDF sidebar. The `section_heading()` helper does this automatically when `bookmark=True` (default).

For sub-sections or manual bookmarks:

```python
# Top-level bookmark (created automatically by section_heading)
pdf.section_heading("Incident Breakdown")

# Sub-section bookmark (level 1 = nested under last level 0)
pdf.start_section("By Severity", level=1)
# ... render severity table ...

pdf.start_section("By Service", level=1)
# ... render service table ...
```

This creates a navigable outline in PDF viewers:
```
- Incident Breakdown
  - By Severity
  - By Service
```

## Source Footnote

Add data source attribution below every table and chart. Use italic light text to keep it unobtrusive.

```python
# After any table or chart:
pdf.source_footnote(
    "Source: BigQuery production data, 2026-02-23 to 2026-02-27. Excludes test accounts."
)
```

The `source_footnote()` helper uses 7pt `LIGHT_TEXT` and adds `SPACE_XS` after. For manual rendering:

```python
pdf.ln(1)  # sub-SPACE_XS: tight coupling to preceding chart
with pdf.local_context(text_color=LIGHT_TEXT):
    pdf.set_font("Inter", "", 7)
    pdf.cell(CONTENT_W, 3, "Source: Production database, Feb 2026",
             new_x="LMARGIN", new_y="NEXT")
pdf.ln(SPACE_XS)
```

## Draft Watermark

Diagonal "DRAFT" or "CONFIDENTIAL" watermark using `rotation()` + `fill_opacity`. Call this AFTER page content is drawn (it overlays with low opacity).

```python
# On each page that needs a watermark:
pdf.draft_watermark()
```

The helper uses `fill_opacity=0.06` and `rotation(45)`. For custom text:

```python
with pdf.local_context(fill_opacity=0.06):
    pdf.set_font("Inter", "B", 60)
    pdf.set_text_color(*WATERMARK_TEXT)
    with pdf.rotation(45, PAGE_W / 2, PAGE_H / 2):
        pdf.set_xy(30, PAGE_H / 2 - 15)
        pdf.cell(PAGE_W - 60, 30, "CONFIDENTIAL", align="C")
```

### Closing Page (Orange Bookend)

The last page mirrors the cover's orange presence — full-bleed JET Orange background with a simple closing message.

```python
pdf.add_page()
pdf._is_closing = True
pdf._no_footer_pages.add(pdf.page_no())

# Full-bleed JET Orange
pdf.set_fill_color(*JET_ORANGE)
pdf.rect(0, 0, PAGE_W, PAGE_H, style="F")

# Centred message — position text group at ~45% from top for true visual centre
pdf.set_xy(MARGIN, PAGE_H * 0.45)
pdf.set_font("InterBlack", "", 36)
pdf.set_text_color(*WHITE)
pdf.cell(CONTENT_W, 18, "Thank you", align="C", new_x="LMARGIN", new_y="NEXT")

# Contact / attribution
pdf.ln(SPACE_SM)
pdf.set_font("Inter", "", 11)
pdf.set_text_color(*WHITE)
pdf.cell(CONTENT_W, 6, "team@justeattakeaway.com", align="C")

# Company name (NOT in a badge -- plain text)
pdf.set_xy(MARGIN, PAGE_H * 0.56)
pdf.set_font("Inter", "B", 9)
pdf.set_text_color(*WHITE)
pdf.cell(CONTENT_W, 6, "Just Eat Takeaway.com", align="C")
```

## Table of Contents / TOC Page

Numbered list of sections on a warm-toned background. Use `JET_ORANGE_TEXT` for section numbers on light backgrounds. Includes dotted leaders and page numbers for functional navigation.

```python
pdf.add_page()

# Warm background (full page)
pdf.set_fill_color(*MOZZARELLA)
pdf.rect(0, 0, PAGE_W, PAGE_H, style="F")

# TOC title
pdf.set_xy(MARGIN, 30)
pdf.set_font("InterBlack", "", 28)
pdf.set_text_color(*CHARCOAL)
pdf.cell(0, 14, "Contents")

# Section entries (two-column layout with dotted leaders + page numbers)
toc_items = [
    ("01", "Executive Summary", "2"),
    ("02", "Key Metrics", "3"),
    ("03", "Incident Analysis", "4"),
    ("04", "Service Health", "5"),
    ("05", "Recommendations", "6"),
    ("06", "Appendix", "7"),
]

col_w_toc = (CONTENT_W - 10) / 2
start_y = 55
items_per_col = (len(toc_items) + 1) // 2

for idx, (num, title, pg) in enumerate(toc_items):
    col = 0 if idx < items_per_col else 1
    row = idx if col == 0 else idx - items_per_col
    item_x = MARGIN + col * (col_w_toc + 10)
    item_y = start_y + row * 14

    # Fixed right edge for page numbers (consistent across all entries)
    pg_x = item_x + col_w_toc - 10

    # Number in orange
    pdf.set_xy(item_x, item_y)
    pdf.set_font("Inter", "B", 12)
    pdf.set_text_color(*JET_ORANGE_TEXT)
    pdf.cell(12, 7, num)

    # Title
    pdf.set_xy(item_x + 14, item_y)
    pdf.set_font("Inter", "", 11)
    pdf.set_text_color(*CHARCOAL)
    title_w = pdf.get_string_width(title)
    pdf.cell(title_w + 2, 7, title)

    # Dotted leader (fills space between title end and page number)
    leader_x = item_x + 14 + title_w + 4
    leader_end = pg_x - 2  # stop 2mm before page number
    dot_y = item_y + 4
    pdf.set_fill_color(*LIGHT_TEXT)
    dx = leader_x
    while dx < leader_end:
        pdf.ellipse(dx, dot_y, 0.6, 0.6, style="F")
        dx += 2.5

    # Page number (fixed x position, right-aligned)
    pdf.set_xy(pg_x, item_y)
    pdf.set_font("Inter", "", 10)
    pdf.set_text_color(*MID_TEXT)
    pdf.cell(10, 7, pg, align="R")
```

## Category / Tag Badge

Dark rounded-rectangle pill with white text, used for metadata labels like report type, department, or status tags. **Never use badges for company name branding** -- they are for topic/department tags only (e.g. "Customer UX", "WEEKLY REPORT", "Q1 2026").

```python
def draw_badge(pdf, x, y, text, bg_color=CHARCOAL, text_color=WHITE,
               font_size=7, h=6, padding=4):
    """Draw a rounded-rect pill badge. Returns the badge width for positioning."""
    pdf.set_font("Inter", "B", font_size)
    text_w = pdf.get_string_width(text)
    badge_w = text_w + padding * 2
    pdf.set_fill_color(*bg_color)
    pdf.rect(x, y, badge_w, h, style="F",
             round_corners=True, corner_radius=h / 2)
    pdf.set_xy(x, y)
    pdf.set_text_color(*text_color)
    pdf.cell(badge_w, h, text, align="C")
    return badge_w


# Usage: row of badges
badge_x = MARGIN
badge_y = pdf.get_y()
for label in ["WEEKLY REPORT", "ENGINEERING", "Q1 2026"]:
    w = draw_badge(pdf, badge_x, badge_y, label)
    badge_x += w + 3  # 3mm gap between badges

# Department-coloured badge
draw_badge(pdf, MARGIN, pdf.get_y(), "CUSTOMER UX",
           bg_color=TURMERIC, text_color=CHARCOAL)
```

## Three-Column Numbered Steps

Large numbered steps in a 3-column layout. Two variants: open (no card background) and carded (with rounded-rect fill).

### Open Variant

```python
pdf.add_page()
pdf.section_heading("How it works")

steps = [
    ("01", "Identify", "Automated monitoring detects anomalies in real-time across all services."),
    ("02", "Respond", "On-call team is alerted and begins triage within the SLA window."),
    ("03", "Resolve", "Root cause is identified, fix deployed, and post-mortem scheduled."),
]

step_w = grid_span(4)  # 3-column layout
step_y = pdf.get_y() + SPACE_SM

for i, (num, heading, body) in enumerate(steps):
    step_x = MARGIN + i * (step_w + GUTTER)

    # Large number
    pdf.set_xy(step_x, step_y)
    pdf.set_font("InterBlack", "", 32)
    pdf.set_text_color(*CHARCOAL)
    pdf.cell(step_w, 16, num)

    # Heading
    pdf.set_xy(step_x, step_y + 18)
    pdf.set_font("Inter", "B", 11)
    pdf.set_text_color(*CHARCOAL)
    pdf.cell(step_w, 6, heading)

    # Body text
    pdf.set_xy(step_x, step_y + 26)
    pdf.set_font("Inter", "", 9)
    pdf.set_text_color(*DARK_TEXT)
    pdf.multi_cell(step_w, 4.5, body)
```

### Carded Variant

```python
step_w = (CONTENT_W - 2 * SPACE_SM) / 3
step_h = 55  # Fixed card height
step_y = pdf.get_y() + SPACE_SM

for i, (num, heading, body) in enumerate(steps):
    step_x = MARGIN + i * (step_w + SPACE_SM)

    # Card background
    pdf.set_fill_color(*MOZZARELLA_T1)
    pdf.set_draw_color(*BORDER)
    pdf.rect(step_x, step_y, step_w, step_h, style="DF",
             round_corners=True, corner_radius=3)

    # Large number
    pdf.set_xy(step_x + 6, step_y + 5)
    pdf.set_font("InterBlack", "", 28)
    pdf.set_text_color(*CHARCOAL)
    pdf.cell(step_w - 12, 14, num)

    # Heading
    pdf.set_xy(step_x + 6, step_y + 21)
    pdf.set_font("Inter", "B", 10)
    pdf.set_text_color(*CHARCOAL)
    pdf.cell(step_w - 12, 5, heading)

    # Body
    pdf.set_xy(step_x + 6, step_y + 28)
    pdf.set_font("Inter", "", 8)
    pdf.set_text_color(*DARK_TEXT)
    pdf.multi_cell(step_w - 12, 4, body)

pdf.set_y(step_y + step_h + SPACE_MD)
```

## Quote / Testimonial Cards

Coloured cards with a **vertical left accent bar**, used for user quotes, testimonials, or stakeholder feedback. Colour-code by department. Uses left accent bar (not top bar) to match JET presentation conventions.

```python
pdf.section_heading("What stakeholders are saying")

quotes = [
    ("The new dashboard saves us 2 hours per week on reporting.",
     "Sarah Chen", "Product Lead, Customer UX", TURMERIC, LIGHT_YELLOW),
    ("Delivery tracking accuracy improved by 15% this quarter.",
     "James Okonkwo", "Ops Manager, Logistics", LATTE, LIGHT_TAN),
    ("Partner onboarding time reduced from 5 days to 2.",
     "Maria Lopez", "Partner Success", BERRY, LIGHT_PINK),
]

quote_w = (CONTENT_W - 2 * SPACE_SM) / 3
quote_h = 50
quote_y = pdf.get_y()

for i, (text, name, role, accent_color, bg_color) in enumerate(quotes):
    qx = MARGIN + i * (quote_w + SPACE_SM)
    cr = 3
    bar_w = 2.5

    # Clipped rounded-rect background with accent bar
    _rounded_rect_clip(pdf, qx, quote_y, quote_w, quote_h, cr)
    pdf.set_fill_color(*accent_color)
    pdf.rect(qx, quote_y, bar_w, quote_h, style="F")
    pdf.set_fill_color(*bg_color)
    pdf.rect(qx + bar_w, quote_y, quote_w - bar_w, quote_h, style="F")
    _restore_gfx_state(pdf)  # restore state + re-sync colour cache

    # Quote text
    pdf.set_xy(qx + 8, quote_y + 7)
    pdf.set_font("Inter", "I", 8)
    pdf.set_text_color(*CHARCOAL)
    pdf.multi_cell(quote_w - 13, 4, f'"{text}"')

    # Attribution
    pdf.set_xy(qx + 8, quote_y + quote_h - 12)
    pdf.set_font("Inter", "B", 7)
    pdf.set_text_color(*CHARCOAL)
    pdf.cell(quote_w - 13, 4, name, new_x="LEFT", new_y="NEXT")
    pdf.set_font("Inter", "", 7)
    pdf.set_text_color(*MID_TEXT)
    pdf.cell(quote_w - 13, 4, role)

pdf.set_y(quote_y + quote_h + SPACE_LG)
```

## Timeline / Milestone Indicator

Horizontal timeline with labelled milestones. Supports solid segments (completed), dotted segments (future), and alternating above/below content placement. **Dashed future segments must use the same colour as the incomplete milestone dot** (BORDER grey) to visually distinguish them from solid completed segments. Completed segments use JET_ORANGE; dashed segments use BORDER.

```python
pdf.section_heading("Project timeline")

milestones = [
    ("Q1 2025", "Discovery", "Research and\nrequirements", True),
    ("Q2 2025", "Design", "UX design and\nprototyping", True),
    ("Q3 2025", "Build", "Development\nand testing", True),
    ("Q4 2025", "Launch", "Rollout to\nall markets", False),  # Future
]

timeline_y = pdf.get_y() + 20
timeline_x_start = MARGIN + 10
timeline_x_end = PAGE_W - MARGIN - 10
timeline_w = timeline_x_end - timeline_x_start
segment_w = timeline_w / (len(milestones) - 1) if len(milestones) > 1 else timeline_w

# Draw timeline line
for i in range(len(milestones) - 1):
    seg_x = timeline_x_start + i * segment_w
    is_completed = milestones[i][3] and milestones[i + 1][3]
    if is_completed:
        # Solid line for completed segments
        with pdf.local_context(draw_color=JET_ORANGE, line_width=1.2):
            pdf.line(seg_x, timeline_y, seg_x + segment_w, timeline_y)
    else:
        # Dashed line for future segments — SAME colour as incomplete dot (BORDER)
        with pdf.local_context(draw_color=BORDER, line_width=1.0):
            dash_len = 3
            gap_len = 2
            dx = 0
            while dx < segment_w:
                end_x = min(seg_x + dx + dash_len, seg_x + segment_w)
                pdf.line(seg_x + dx, timeline_y, end_x, timeline_y)
                dx += dash_len + gap_len

# Draw milestone dots and labels
for i, (date, title, detail, completed) in enumerate(milestones):
    mx = timeline_x_start + i * segment_w if len(milestones) > 1 else timeline_x_start
    dot_r = 3

    # Milestone dot
    dot_color = JET_ORANGE if completed else BORDER
    pdf.set_fill_color(*dot_color)
    pdf.ellipse(mx - dot_r, timeline_y - dot_r, dot_r * 2, dot_r * 2, style="F")

    # Alternate above/below for readability
    if i % 2 == 0:
        # Above the line
        pdf.set_xy(mx - 15, timeline_y - 22)
        pdf.set_font("Inter", "B", 8)
        pdf.set_text_color(*CHARCOAL)
        pdf.cell(30, 4, title, align="C", new_x="LEFT", new_y="NEXT")
        pdf.set_font("Inter", "", 7)
        pdf.set_text_color(*MID_TEXT)
        pdf.multi_cell(30, 3.5, detail, align="C")
    else:
        # Below the line
        pdf.set_xy(mx - 15, timeline_y + 6)
        pdf.set_font("Inter", "B", 8)
        pdf.set_text_color(*CHARCOAL)
        pdf.cell(30, 4, title, align="C", new_x="LEFT", new_y="NEXT")
        pdf.set_font("Inter", "", 7)
        pdf.set_text_color(*MID_TEXT)
        pdf.multi_cell(30, 3.5, detail, align="C")

    # Date label (always below dot)
    pdf.set_xy(mx - 12, timeline_y + (22 if i % 2 == 0 else -8))
    pdf.set_font("Inter", "", 6.5)
    pdf.set_text_color(*LIGHT_TEXT)
    pdf.cell(24, 3, date, align="C")

pdf.set_y(timeline_y + 35)
```

## Colour-Coded Matrix / Grid

Rounded-rect cells in supporting brand colours for categorisation grids, capability matrices, or feature comparisons.

```python
pdf.section_heading("Capability matrix")

# Matrix data: (label, category)
# Category determines the cell colour
category_colors = {
    "customer": (TURMERIC, LIGHT_YELLOW),       # accent, bg
    "partner":  (BERRY, LIGHT_PINK),
    "logistics": (LATTE, LIGHT_TAN),
    "operations": (CUPCAKE, LIGHT_BLUE),
}

matrix = [
    [("Search", "customer"), ("Menu", "customer"), ("Checkout", "customer")],
    [("Onboarding", "partner"), ("Analytics", "partner"), ("Support", "partner")],
    [("Routing", "logistics"), ("Tracking", "logistics"), ("ETA", "logistics")],
    [("Monitoring", "operations"), ("Alerting", "operations"), ("Scaling", "operations")],
]

cell_w = (CONTENT_W - (len(matrix[0]) - 1) * SPACE_XS) / len(matrix[0])
cell_h = 14
matrix_y = pdf.get_y()

for row_idx, row in enumerate(matrix):
    for col_idx, (label, category) in enumerate(row):
        cx = MARGIN + col_idx * (cell_w + SPACE_XS)
        cy = matrix_y + row_idx * (cell_h + SPACE_XS)
        accent, bg = category_colors[category]

        # Cell background
        pdf.set_fill_color(*bg)
        pdf.rect(cx, cy, cell_w, cell_h, style="F",
                 round_corners=True, corner_radius=3)

        # Cell text
        pdf.set_xy(cx, cy + 3)
        pdf.set_font("Inter", "B", 8)
        pdf.set_text_color(*CHARCOAL)
        pdf.cell(cell_w, 8, label, align="C")

pdf.set_y(matrix_y + len(matrix) * (cell_h + SPACE_XS) + SPACE_MD)
```

## Stat Card (Reusable Helper)

A self-contained card with a large number, label, and optional delta indicator. Clean and minimal — no accent bars or decorative lines. Use for KPI dashboards, executive summary stat rows, or any at-a-glance metric display. Renders a single card at an explicit (x, y) position — call in a loop for a row of cards.

```python
def draw_stat_card(pdf, x, y, w, h, value, label,
                   bg_color=WHITE, delta=None):
    """Card with large number, label, and optional delta indicator.

    Args:
        pdf: FPDF instance
        x, y: top-left corner position
        w, h: card dimensions (recommended: w=42-44, h=38 for 4-col layout)
        value: display string for the large number (e.g. "35", "100%", "4.2h")
        label: short descriptor below the number (e.g. "Patterns", "Uptime")
        bg_color: card fill colour (default WHITE; use MOZZARELLA_T1 on warm-bg pages)
        delta: optional change indicator string (e.g. "+8 new", "+12% WoW")
    """
    # Card background
    pdf.set_fill_color(*bg_color)
    pdf.set_draw_color(*BORDER)
    pdf.rect(x, y, w, h, style="DF", round_corners=True, corner_radius=4)

    # Large value (bold, prominent)
    pdf.set_xy(x, y + 10)
    pdf.set_font("InterExtraBold", "", 26)
    pdf.set_text_color(*CHARCOAL)
    pdf.cell(w, 12, value, align="C")

    # Label (regular weight, secondary)
    pdf.set_xy(x, y + 24)
    pdf.set_font("Inter", "", 7.5)
    pdf.set_text_color(*MID_TEXT)
    pdf.cell(w, 4, label, align="C")

    # Delta (optional)
    if delta:
        pdf.set_xy(x, y + 30)
        pdf.set_font("Inter", "B", 6.5)
        pdf.set_text_color(*JET_ORANGE)
        pdf.cell(w, 4, delta, align="C")


# Usage: row of 4 stat cards
card_gap = GUTTER
card_count = 4
card_w = grid_span(3)  # 4-column layout
card_h = 38
card_y = pdf.get_y()

stat_cards = [
    ("35", "Patterns", "+8 new"),
    ("17", "Page Types", "+8 new"),
    ("25", "Colour Tokens", "+10 new"),
    ("100%", "WCAG AA", None),
]

for i, (val, label, delta) in enumerate(stat_cards):
    cx = MARGIN + i * (card_w + card_gap)
    draw_stat_card(pdf, cx, card_y, card_w, card_h, val, label, MOZZARELLA_T1, delta)

pdf.set_y(card_y + card_h + SPACE_MD)
```

**Design notes:**
- Use `MOZZARELLA_T1` background on warm-bg pages, `WHITE` on plain pages.
- Cards are clean and minimal — no accent bars or decorative lines.
- Delta text uses `JET_ORANGE` on content pages (not SUCCESS green). On cover pages, delta text is WHITE (see Cover Page KPI Cards).
- For a 2-column layout, use `card_w ≈ 85mm, card_h = 38mm`.
- For a 3-column layout, use `card_w ≈ 57mm`.

## Progress Bar (Reusable Helper)

Rounded progress bar with track and fill. Use inside cards, tables, or standalone.

```python
def draw_progress_bar(pdf, x, y, w, h, pct,
                      bar_color=JET_ORANGE, track_color=BORDER):
    """Rounded progress bar.

    Args:
        pdf: FPDF instance
        x, y: position of the bar
        w: total width of the bar
        h: bar height (recommended: 3mm for compact, 5mm for standalone)
        pct: fill percentage (0-100)
        bar_color: fill colour
        track_color: background track colour
    """
    # Track (full width)
    pdf.set_fill_color(*track_color)
    pdf.rect(x, y, w, h, style="F", round_corners=True, corner_radius=h / 2)
    # Fill (proportional)
    if pct > 0:
        fill_w = max((pct / 100) * w, h)  # minimum = height for proper rounding
        fill_w = min(fill_w, w)
        pdf.set_fill_color(*bar_color)
        pdf.rect(x, y, fill_w, h, style="F",
                 round_corners=True, corner_radius=h / 2)
    # 0% treatment: track-only bar with a "Not started" label is handled by
    # the caller — this function just renders an empty track, which is correct.


# Usage: standalone progress bar
draw_progress_bar(pdf, MARGIN, pdf.get_y(), CONTENT_W, 5, 72, JET_ORANGE)

# Usage: inside a card
draw_progress_bar(pdf, card_x + 5, card_y + 20, card_w - 10, 3, score, TURMERIC)

# Usage: 0% item — draw bar (shows track only) + optional label
draw_progress_bar(pdf, x, y, w, 3, 0, JET_ORANGE)
pdf.set_font("Inter", "", 7)
pdf.set_text_color(*MUTED_TEXT)
pdf.cell(w, 3, "Not started", align="L")  # or omit label for clean look
```

**Notes:**
- The minimum fill width is set to `h` (bar height) so the rounded corners render correctly even at very low percentages.
- Use `h=3` inside cards, `h=5` for standalone bars.
- Pair with a percentage label above or beside the bar.

## Compact Tile Grid

A dense grid of small tiles, each showing a status dot and name. Ideal for pattern status, feature coverage, or checklist displays. Replaces the traffic-light table when you have 15+ items and want a scannable overview.

```python
# Data: list of (name, status, detail)
items = [
    ("Cover Page + KPIs", "green", "Full pattern with deltas"),
    ("Section Dividers", "green", "Orange + coloured variants"),
    ("Traffic Lights", "green", "Coloured dots with text labels"),
    ("Google Slides", "orange", "Planned - requires API"),
    # ... more items
]

# Grid layout: 4 columns, compact tiles
card_gap = GUTTER
cols = 4
card_w = grid_span(3)  # 4-column layout
card_h = 18  # Compact height — just status dot + name
row_gap = 4
start_y = pdf.get_y()

status_colors = {"green": SUCCESS, "orange": WARNING, "red": DANGER}

for idx, (pattern, status, _detail) in enumerate(items):
    col = idx % cols
    row = idx // cols

    cx = MARGIN + col * (card_w + card_gap)
    cy = start_y + row * (card_h + row_gap)

    # Page break check (only on first column of a new row)
    if col == 0 and cy + card_h > MAX_Y:
        pdf.add_page()
        start_y = pdf.get_y()
        cy = start_y

    # Tile background (vary by status)
    card_bg = MOZZARELLA_T1 if status == "green" else WARNING_BG
    pdf.set_fill_color(*card_bg)
    pdf.set_draw_color(*BORDER)
    pdf.rect(cx, cy, card_w, card_h, style="DF",
             round_corners=True, corner_radius=3)

    # Status dot
    dot_color = status_colors.get(status, MUTED)
    pdf.set_fill_color(*dot_color)
    pdf.ellipse(cx + 4, cy + 4, 3, 3, style="F")

    # Status label (READY / PLANNED)
    status_label = "READY" if status == "green" else "PLANNED"
    pdf.set_xy(cx + 9, cy + 3)
    pdf.set_font("Inter", "B", 5.5)
    pdf.set_text_color(*dot_color)
    pdf.cell(card_w - 13, 3.5, status_label)

    # Pattern name (truncate if needed)
    name = pattern if len(pattern) <= 18 else pattern[:16] + ".."
    pdf.set_xy(cx + 4, cy + 10)
    pdf.set_font("Inter", "B", 7)
    pdf.set_text_color(*CHARCOAL)
    pdf.cell(card_w - 8, 4, name)

# Advance cursor past grid
total_rows = (len(items) + cols - 1) // cols
pdf.set_y(start_y + total_rows * (card_h + row_gap))
```

**Design notes:**
- 4 columns works well for 15-25 items on A4 portrait.
- 3 columns gives more room for longer names.
- Use `card_h = 18mm` for the compact variant (status dot + name only).
- Use `card_h = 28mm` if you want to include a description line.
- Background colour varies by status for instant visual scanning.

## Graph Card Grid

A 2-column grid of graph cards, each showing a pie chart (left) paired with title, progress bar, and description (right). Based on the JET "Graphs" slide pattern (slide_070). Each card uses a different JET supporting colour. Ideal for 2-4 key metrics that benefit from visual proportion + text explanation.

> **Guidance**: Use for 2-4 items. For more than 4 items, prefer a `PROGRESS_LIST` or data table with inline progress bars. For single-metric highlights, use `STAT_CARD` or `PIE_CHART` instead.

```python
def draw_graph_card_grid(pdf, items, cols=2, card_h=60, pie_r=14,
                         card_gap=GUTTER, row_gap=SPACE_MD, cr=4):
    """Draw a grid of graph cards, each with a pie chart + progress bar + text.
    items: list of (title, pct, description, accent_color, track_tint)
    Renders cards on WHITE with BORDER outline for contrast on Mozzarella."""
    card_w = grid_span(GRID_COLS // cols)

    # ── Pre-flight height check (Rule #27) ─────────────────────────
    num_rows = (len(items) + cols - 1) // cols
    total_grid_h = num_rows * (card_h + row_gap) - row_gap
    if pdf.get_y() + total_grid_h > MAX_Y and MARGIN + total_grid_h <= MAX_Y:
        # Grid won't fit here but WILL fit on a fresh page — move it
        pdf.add_page()
    # If it won't fit even on a fresh page, reduce card_h or split items
    # before calling this function.

    start_y = pdf.get_y()

    for idx, (title, pct, desc, accent, tint) in enumerate(items):
        col = idx % cols
        row = idx // cols
        cx = MARGIN + col * (card_w + card_gap)
        cy = start_y + row * (card_h + row_gap)

        # Page break check
        if col == 0 and cy + card_h > MAX_Y:
            pdf.add_page()
            start_y = pdf.get_y()
            cy = start_y

        # Card background
        pdf.set_fill_color(*WHITE)
        pdf.set_draw_color(*BORDER)
        pdf.rect(cx, cy, card_w, card_h, style="DF",
                 round_corners=True, corner_radius=cr)

        # Pie chart (left side)
        pie_cx = cx + pie_r + 8
        pie_cy = cy + card_h * 0.43
        pdf.pie_chart(pie_cx, pie_cy, pie_r, pct,
                      color=accent, track_color=tint)

        # Text area (right of pie, with right-side padding)
        # text_x is inset past the pie; text_w ends 8mm before card right edge
        text_x = cx + pie_r * 2 + 14
        text_w = card_w - (pie_r * 2 + 22)  # leaves ~8mm right padding

        # Title (10pt to avoid clipping long titles like "Blockchain Sandwich")
        pdf.set_xy(text_x, cy + 8)
        pdf.set_font("Inter", "B", 10)
        pdf.set_text_color(*CHARCOAL)
        pdf.cell(text_w, 6, title)

        # Calculate fixed % label width from "100%" string
        pdf.set_font("Inter", "B", 8)
        pct_label_w = pdf.get_string_width("100%") + 2  # fixed width for all cards
        pct_gap = 3  # gap between bar and % label

        # Right edge of text box
        text_right = text_x + text_w
        # % label: right-aligned with text_right, fixed width
        pct_label_x = text_right - pct_label_w
        # Progress bar: left edge = text_x, right edge = pct_label_x - gap
        bar_w_actual = pct_label_x - pct_gap - text_x

        # Progress bar (left-aligned with title)
        bar_h = 3
        bar_y = cy + 18
        draw_progress_bar(pdf, text_x, bar_y, bar_w_actual, bar_h, pct, accent)

        # % label (y-centered with progress bar, right-aligned with title right edge)
        pct_label_h = 5
        pct_label_y = bar_y + (bar_h / 2) - (pct_label_h / 2)
        pdf.set_xy(pct_label_x, pct_label_y)
        pdf.set_font("Inter", "B", 8)
        pdf.set_text_color(*CHARCOAL)
        pdf.cell(pct_label_w, pct_label_h, f"{pct}%", align="R")

        # Description
        pdf.set_xy(text_x, bar_y + 7)
        pdf.set_font("Inter", "", 7.5)
        pdf.set_text_color(*MID_TEXT)
        pdf.multi_cell(text_w, 3.5, desc, align="L")

    total_rows = (len(items) + cols - 1) // cols
    pdf.set_y(start_y + total_rows * (card_h + row_gap))
```

**Usage:**

```python
graph_items = [
    ("PDF Generation", 95,
     "Core templating engine with full component coverage across all layouts.",
     BERRY, LIGHT_PINK),
    ("Design System", 88,
     "Colour palette, typography, spacing, and grid system fully aligned with JET VI.",
     CUPCAKE, LIGHT_BLUE),
    ("Data Visualisation", 72,
     "Charts, tables, and progress indicators with consistent styling throughout.",
     LATTE, LIGHT_TAN),
    ("Documentation", 60,
     "Skill files, pattern library, and usage guidance for all components.",
     TURMERIC, LIGHT_YELLOW),
]

draw_graph_card_grid(pdf, graph_items)
```

**Design notes:**
- Each card uses a **different JET supporting colour** for its pie chart and progress bar — this is one of the few cases where multiple supporting colours appear on one page, because each card is a self-contained unit.
- The lighter tint variant is used as the pie chart track (background segment), giving contrast between filled and unfilled.
- Cards have WHITE fill with subtle BORDER outline for contrast on the Mozzarella page background.
- For 0% items, the pie shows only the track colour and the label reads "Not started".
- Keep descriptions to 2-3 short lines to maintain visual balance with the pie chart.

## Numbered Insight Cards

Three-column cards with a large number (01/02/03), heading, and body text. Use for key insights, recommendations, or ordered findings. Similar to numbered steps but designed for analytical content rather than process flows.

```python
insights = [
    ("01", "Complete Design System",
     "Colours, typography, spacing, and layout rules "
     "extracted from 50 JET template slides.",
     JET_ORANGE),
    ("02", "Communication Framework",
     "Pyramid principle, insight-as-headline, and 5-30-300 "
     "rule baked into every pattern.",
     TURMERIC),
    ("03", "Self-Contained",
     "Zero external dependencies beyond fpdf2. All fonts, "
     "colours, and helpers included.",
     CUPCAKE),
]

insight_w = (CONTENT_W - 2 * SPACE_SM) / 3
insight_h = 62
insight_y = pdf.get_y()

for i, (num, heading, body, accent) in enumerate(insights):
    ix = MARGIN + i * (insight_w + SPACE_SM)

    # Card background
    pdf.set_fill_color(*MOZZARELLA_T1)
    pdf.set_draw_color(*BORDER)
    pdf.rect(ix, insight_y, insight_w, insight_h, style="DF",
             round_corners=True, corner_radius=4)

    # Number (Charcoal, not accent-coloured — keep it clean)
    pdf.set_xy(ix + 6, insight_y + 8)
    pdf.set_font("InterBlack", "", 24)
    pdf.set_text_color(*CHARCOAL)
    pdf.cell(insight_w - 12, 12, num)

    # Heading
    pdf.set_xy(ix + 6, insight_y + 22)
    pdf.set_font("Inter", "B", 9.5)
    pdf.set_text_color(*CHARCOAL)
    pdf.cell(insight_w - 12, 5, heading)

    # Body (ALWAYS use align="L" to avoid ugly justified word gaps in narrow columns)
    pdf.set_xy(ix + 6, insight_y + 30)
    pdf.set_font("Inter", "", 7.5)
    pdf.set_text_color(*DARK_TEXT)
    pdf.multi_cell(insight_w - 12, 3.8, body, align="L")

pdf.set_y(insight_y + insight_h + SPACE_MD)
```

**Design notes:**
- Numbers use Charcoal colour for a clean, professional look. No accent bars or coloured numbers.
- `insight_h = 62mm` fits a 2-line heading and 3-4 lines of body text. Adjust if content is shorter.
- **Critical**: Always use `align="L"` for `multi_cell()` in narrow columns. The fpdf2 default is justified (`align="J"`), which creates ugly word-spacing gaps in columns under ~60mm wide.

## Wide Quote Card

A full-width quote/testimonial card spanning the content area. Uses a **vertical left accent bar** (not top accent bar) — more aligned with JET presentation conventions. Use for featured quotes, executive commentary, or highlighted stakeholder feedback. Uses the **clipping path technique** for pixel-perfect corners.

```python
quote_y = pdf.get_y()
quote_h = 32
cr = 3
bar_w = 2.5
quote_pad = 7  # equal top and bottom padding

# Clipped rounded-rect background with accent bar
_rounded_rect_clip(pdf, MARGIN, quote_y, CONTENT_W, quote_h, cr)
pdf.set_fill_color(*TURMERIC)
pdf.rect(MARGIN, quote_y, bar_w, quote_h, style="F")
pdf.set_fill_color(*LIGHT_YELLOW)
pdf.rect(MARGIN + bar_w, quote_y, CONTENT_W - bar_w, quote_h, style="F")
_restore_gfx_state(pdf)  # restore state + re-sync colour cache

# Quote text — positioned using quote_pad from top
pdf.set_xy(MARGIN + 10, quote_y + quote_pad)
pdf.set_font("Inter", "I", 9)
pdf.set_text_color(*CHARCOAL)
pdf.cell(0, 5, '"The skill went from 27 to 35 patterns in one sprint,')
pdf.set_xy(MARGIN + 10, quote_y + quote_pad + 5.5)
pdf.cell(0, 5, 'covering every layout in the corporate template."')

# Attribution — positioned from bottom edge to guarantee equal bottom padding
attr_y = quote_y + quote_h - quote_pad - 8  # 8 = two lines of 4pt
pdf.set_xy(MARGIN + 10, attr_y)
pdf.set_font("Inter", "B", 7)
pdf.set_text_color(*CHARCOAL)
pdf.cell(0, 4, "Template Analysis", new_x="LEFT", new_y="NEXT")
pdf.set_font("Inter", "", 7)
pdf.set_text_color(*MID_TEXT)
pdf.cell(0, 4, "Design System")

pdf.set_y(quote_y + quote_h + SPACE_XS)
```

**Notes:**
- Use `quote_pad` for both top and bottom padding to guarantee symmetry. Quote text is positioned at `quote_y + quote_pad` from the top; attribution is positioned at `quote_y + quote_h - quote_pad - line_heights` from the bottom.
- Attribution uses a two-line format: bold name on first line, regular role on second line. Do not use the inline pipe separator (`|`) format.
- For longer quotes, use `multi_cell()` instead of separate `cell()` calls per line.
- The accent bar is vertical (left side), not horizontal (top). This matches JET slide conventions.
- The accent colour should match the department/source of the quote.
- **Critical**: Always use the `_rounded_rect_clip()` clipping path technique for accent bars. This produces pixel-perfect rounded corners with no colour bleed. Never use the old `round_corners=("TOP_LEFT", "BOTTOM_LEFT")` layering approach — it causes artefacts. Never draw the accent bar as a separate narrow rounded rect — `corner_radius` gets capped to half the bar width, creating mismatched corners.

## Content Page Helper

Content pages in the JET template use a warm Mozzarella background (`MOZZARELLA` / `#EFEDEA`), not plain white. The `content_page()` method sets the background colour and section title, drawn automatically in `header()`. Use the `bg_color` parameter for pages with supporting colour backgrounds (e.g. full Latte or Cupcake backgrounds). Use `band_color` to add a section header band on the first page of each major section.

```python
# Content page with warm Mozzarella background (default)
pdf.content_page(section_title="Executive Summary", section_num="Section 01")
pdf.section_heading("Executive Summary")

# Content page with Latte background
pdf.content_page(section_title="Design System", bg_color=LATTE)

# Content page with section header band
pdf.content_page(section_title="Executive Summary", section_num="Section 01",
                 band_color=LATTE)

# Content page without band (continuation page in same section)
pdf.content_page(section_title="Executive Summary", section_num="Section 01")
```

**Why this matters:**
- The background must be drawn in `header()` because fpdf2 calls `header()` automatically when `add_page()` is invoked. Drawing it after `add_page()` would overlay the header elements.
- The `_is_cover` and `_is_closing` flags control which pages skip the standard header.
- Footer suppression uses `_no_footer_pages` — add the page number to this set immediately after `add_page()`.
- Content pages can optionally have a section header band via `band_color` — used on the first page of each major section.

## Output

### Naming convention

Scripts use **stable, type-based names** that match the `# Type:` metadata field:
- Script: `<type>.py` (e.g., `ai_adoption_report.py`)
- PDF: `<type>_<YYYY-MM-DD>.pdf` (e.g., `ai_adoption_report_2026-03-06.pdf`)

This makes scripts discoverable for reuse. Never use ephemeral names like `report_v2.py` or `untitled.py`.

### Save

```python
from datetime import date

# Save to reports/ subdirectory (create if needed) — never ask the user where to save
reports_dir = os.path.join(os.getcwd(), "reports")
os.makedirs(reports_dir, exist_ok=True)
report_type = "report_name"  # Must match the # Type: metadata field
output_path = os.path.join(reports_dir, f"{report_type}_{date.today()}.pdf")
pdf.output(output_path)
print(f"PDF saved to: {os.path.abspath(output_path)}")
print(f"Pages: {pdf.page_no()}")
```

After generating, open the PDF for the user to review:

```bash
open reports/report_name.pdf
```

---

## JET Visual Identity Style Guide Patterns

### Official Colour Constants

All colour variables are defined in the boilerplate section at the top of this file. The canonical names come from the JET Visual Identity Style Guide. Key points:

```python
# See boilerplate for full definitions. Summary of names:
# Primary:    JET_ORANGE, JET_ORANGE_TEXT (accessible), CHARCOAL
# Supporting: BERRY, TURMERIC, CUPCAKE, LATTE, AUBERGINE
# Neutrals:   MOZZARELLA, MOZZARELLA_T1, MOZZARELLA_T2
# Tints:      LIGHT_ORANGE, LIGHT_PINK, LIGHT_YELLOW, LIGHT_BLUE, LIGHT_TAN
# Text:       DARK_TEXT, MID_TEXT, LIGHT_TEXT, MUTED_TEXT, WHITE
# Status:     SUCCESS, WARNING, DANGER, INFO, MUTED
```

### Type Colour Rules

```python
def text_color_for_bg(bg):
    """Return correct text colour per JET style guide."""
    if bg in (JET_ORANGE, AUBERGINE):
        return WHITE
    return CHARCOAL  # supporting colours + Mozzarella family
```

**Rules:**
- JET Orange bg → White text ONLY
- Aubergine bg → White text ONLY
- Supporting colours (Berry, Turmeric, Cupcake, Latte) → Charcoal ONLY
- Mozzarella family → Charcoal or JET Orange
- NEVER set type in supporting colours

### Grid System

The 12-column grid system is defined in the boilerplate section above. All column
widths MUST use `grid_span(n)` and inter-column gaps MUST use `GUTTER`.

```python
# These are defined in the boilerplate — do NOT redefine them:
# GUTTER, GRID_COLS, COL_W, grid_span()

# Common layouts:
half_w    = grid_span(6)   # ≈80.5mm — 2-column layouts
third_w   = grid_span(4)   # ≈50.7mm — 3-column layouts
quarter_w = grid_span(3)   # ≈35.8mm — 4-column layouts
full_w    = grid_span(12)  # =170mm  — full content width

# BAD — ad-hoc width calculation (violates Rule #14)
card_gap = 6
card_w = (CONTENT_W - card_gap) / 2

# GOOD — grid-aligned width with GUTTER gap
card_gap = GUTTER
card_w = grid_span(6)
```

### Typography Leading

```python
LEADING_HEADLINE = 0.85   # tight headlines
LEADING_SUBHEAD = 1.00    # subheadings/CTA
LEADING_BODY = 1.20       # body copy

def line_h(font_size, leading=LEADING_BODY):
    return round(font_size * leading * 0.3528, 1)  # pt → mm
```

### Callout Box

```python
def draw_callout(pdf, title="", body="", accent_color=JET_ORANGE,
                 bg_color=MOZZARELLA_T1, icon_char=None):
    """Rounded box with coloured accent bar on the left edge.
    Uses clipping-path technique for clean rounded corners + inset bar.
    Padding is symmetric: 4mm top and bottom."""
    y = pdf.get_y()
    pad_y = 4  # symmetric vertical padding
    cr = 3
    bar_w = 2.5
    text_x = CONTENT_X + 8
    text_w = CONTENT_W - 14

    # ── Measure actual content height via dry-run ────────
    title_h = 5 if (icon_char or title) else 0
    body_h = 0
    if body:
        pdf.set_font("Inter", "", 8)
        body_h = pdf.multi_cell(
            text_w, 3.5, body, align="L", dry_run=True, output="HEIGHT"
        )

    box_h = pad_y + title_h + body_h + pad_y

    _rounded_rect_clip(pdf, CONTENT_X, y, CONTENT_W, box_h, cr)
    pdf.set_fill_color(*accent_color)
    pdf.rect(CONTENT_X, y, bar_w, box_h, style="F")
    pdf.set_fill_color(*bg_color)
    pdf.rect(CONTENT_X + bar_w, y, CONTENT_W - bar_w, box_h, style="F")
    _restore_gfx_state(pdf)  # end clipping path + re-sync colours

    text_x = CONTENT_X + 8
    text_w = CONTENT_W - 14
    inner_y = y + pad_y

    if icon_char:
        pdf.set_xy(CONTENT_X + 4, inner_y)
        pdf.set_font("Inter", "B", 10)
        pdf.set_text_color(*accent_color)
        pdf.cell(5, 4, icon_char)
        text_x += 4
        text_w -= 4

    if title:
        pdf.set_xy(text_x, inner_y)
        pdf.set_font("Inter", "B", 8)
        pdf.set_text_color(*CHARCOAL)
        pdf.cell(text_w, 4, title)
        inner_y += 5

    if body:
        pdf.set_xy(text_x, inner_y)
        pdf.set_font("Inter", "", 8)
        pdf.set_text_color(*CHARCOAL)
        pdf.multi_cell(text_w, 3.5, body, align="L")

    pdf.set_y(y + box_h + SPACE_MD)
```

### Divider

```python
def draw_divider(pdf, color=BORDER, thickness=0.5, margin_y=SPACE_SM):
    """Thin horizontal rule spanning the content width."""
    pdf.ln(margin_y)
    y = pdf.get_y()
    pdf.set_draw_color(*color)
    pdf.set_line_width(thickness)
    pdf.line(CONTENT_X, y, CONTENT_X + CONTENT_W, y)
    pdf.set_line_width(0.2)  # reset to default
    pdf.ln(margin_y)
```

### Hyperlink

```python
def draw_hyperlink(pdf, text, url, font_size=8, font_style=""):
    """Render a clickable hyperlink in JET Accessible Orange with underline.
    Exception to the no-underline rule: actual hyperlinks use underline.
    Call inline within text flow — advances cursor like cell()."""
    pdf.set_text_color(*JET_ORANGE_TEXT)
    pdf.set_font("Inter", font_style, font_size)
    link_w = pdf.get_string_width(text)
    y = pdf.get_y()
    x = pdf.get_x()
    pdf.cell(link_w, 4, text, link=url)
    # Manual underline (0.3pt, same colour)
    pdf.set_draw_color(*JET_ORANGE_TEXT)
    pdf.set_line_width(0.3)
    pdf.line(x, y + 4, x + link_w, y + 4)
    pdf.set_line_width(0.2)  # reset
```

### Colour Block

```python
def draw_colour_block(pdf, title="", body_text="", bg_color=JET_ORANGE,
                      ratio=0.333, full_width=True):
    """Full-width (or fractional) coloured background block with text overlay.
    Used for pull quotes, highlight sections, or visual breaks.
    Text colour auto-determined by background brightness."""
    block_w = CONTENT_W if full_width else CONTENT_W * ratio
    block_x = CONTENT_X
    y = pdf.get_y()
    block_h = 30  # default height, adjust based on content

    # Determine text colour based on background
    text_col = WHITE if sum(bg_color) < 400 else CHARCOAL

    cr = 4
    pdf.set_fill_color(*bg_color)
    pdf.rect(block_x, y, block_w, block_h, style="F",
             round_corners=True, corner_radius=cr)

    if title:
        pdf.set_xy(block_x + 8, y + 6)
        pdf.set_font("Inter", "B", 12)
        pdf.set_text_color(*text_col)
        pdf.cell(block_w - 16, 6, title)

    if body_text:
        pdf.set_xy(block_x + 8, y + (14 if title else 6))
        pdf.set_font("Inter", "", 9)
        pdf.set_text_color(*text_col)
        pdf.multi_cell(block_w - 16, 4, body_text, align="L")

    pdf.set_y(y + block_h + SPACE_MD)
```

### Colour Swatch Group

```python
def draw_swatch_group(pdf, group_name, swatches, swatch_size=8):
    """Render a labelled row of colour swatches with name + hex value.

    swatches: list of (name, (R,G,B)) tuples.
    Each swatch is a rounded square with a darkened border,
    the colour name below, and the hex code below that.

    Spacing: SPACE_MD (8mm) above the group title to separate from
    preceding content. SPACE_SM (4mm) between title and swatches.
    SPACE_MD (8mm) after swatch labels before the next group title,
    ensuring clear visual separation between groups.
    """
    swatch_stride = swatch_size + 14  # swatch + label width

    if pdf.get_y() + swatch_size + 12 + SPACE_SM > MAX_Y:
        pdf.add_page()
        pdf.set_y(20)

    # Group title — uppercase, bold, small
    pdf.set_font("Inter", "B", 7)
    pdf.set_text_color(*CHARCOAL)
    pdf.cell(CONTENT_W, 4, group_name.upper())
    pdf.ln(SPACE_SM)  # 4mm gap between title and swatches

    sx = CONTENT_X
    sy = pdf.get_y()

    for name, rgb in swatches:
        # Swatch square with darkened border
        pdf.set_fill_color(*rgb)
        pdf.set_draw_color(*darken(rgb, 0.5))
        pdf.rect(sx, sy, swatch_size, swatch_size, style="DF",
                 round_corners=True, corner_radius=1.5)

        # Colour name below swatch
        pdf.set_xy(sx, sy + swatch_size + 1)
        pdf.set_font("InterLight", "", 5)
        pdf.set_text_color(*CHARCOAL)
        pdf.cell(swatch_stride, 3, name)

        # Hex code below name
        hex_code = f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"
        pdf.set_xy(sx, sy + swatch_size + 4)
        pdf.set_font("InterLight", "", 4.5)
        pdf.set_text_color(*MID_TEXT)
        pdf.cell(swatch_stride, 3, hex_code)

        sx += swatch_stride

    # Advance y past swatch + labels + gap before next group
    pdf.set_y(sy + swatch_size + 9 + SPACE_MD)
```

```python
# Checkmark (✓) / cross (✗) checklist
checklist = [
    ("Feature complete", True),   # ✓ JET Orange
    ("Feature pending", False),   # ✗ grey, grey italic
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

### Bookend Principle

Start and end on JET Orange. Min 20% of pages use JET Orange background. Supporting colours in SECTIONS, not randomly.
