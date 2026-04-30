"""
Merlin Case Study Report Template
===================================
Generates a JET-branded PDF for Merlin data analysis case studies.

This template produces a receipt-style report with:
  - Compact JET Orange header band with "Merlin" branding + JET icon
  - Structured sections: Title, Summary, Keywords, Numbers, Key Findings,
    SQL Queries, Methodology
  - No cover/closing bookend pages (unlike standard JET reports)
  - Warm background (#F6F3EF) with white stat cards

Usage:
    python merlin_report.py              # generates sample report
    python merlin_report.py data.json    # generates from JSON data

Data format (JSON dict):
{
    "title": "Total Orders in Amsterdam",
    "subtitle": "Last week by order type: Feb 17 2026 - Feb 23 2026",
    "generated_at": "2 March 2026 at 15:45",
    "summary": "Analysis of total orders placed in Amsterdam ...",
    "keywords": {
        "tags": ["order_type", "orders", "amsterdam"],
        "metadata": {
            "Business Domain": "Orders",
            "Region": "NL (Netherlands - Amsterdam)",
            "Time Period": "Last 7 Days (2026-02-17 to 2026-02-23)",
            "Tables Used": "core_dwh.fact_order, core_dwh.dim_ordertype"
        }
    },
    "numbers": [
        {"value": "72,186", "label": "Total orders"},
        {"value": "34,578", "label": "Restaurant delivery"},
        {"value": "47.91%", "label": "Courier delivery"}
    ],
    "key_findings": [
        {"label": "Total Orders", "detail": "72,186 orders in Amsterdam over the last 7 days"},
        {"label": "Delivery", "detail": "34,581 orders (47.91%) - courier / DaaS delivery"}
    ],
    "sql_queries": [
        {
            "query": "01_amsterdam_orders_by_type_last_week.sql",
            "description": "Orders grouped by order type",
            "output": "results/01_amsterdam_orders_by_type_last_week.txt"
        }
    ],
    "methodology": [
        "Amsterdam is identified via `core_dwh.dim_city.cityid = 1` (Amsterdam, NL)",
        "`fact_order.restaurantcityid` is joined to `dim_city` to filter Amsterdam orders"
    ]
}
"""

import json
import os
import sys
from datetime import datetime

from fpdf import FPDF

# ── Page constants ─────────────────────────────────────────────────
PAGE_W = 210
PAGE_H = 297
MARGIN = 20
CONTENT_W = PAGE_W - 2 * MARGIN  # 170mm
CONTENT_X = MARGIN
MAX_Y = 275

# ── Spacing system (4mm base unit) ─────────────────────────────────
SPACE_XS = 2
SPACE_SM = 4
SPACE_MD = 8
SPACE_LG = 12
SPACE_XL = 16

# ── Font directory ─────────────────────────────────────────────────
FONT_DIR = os.path.expanduser("~/.agents/skills/jet-report/references/fonts")
IMAGE_DIR = os.path.expanduser("~/.agents/skills/jet-report/references/images")

# ── Merlin colour palette ──────────────────────────────────────────
# Based on Figma design: "Report templates > Option 1 – Strong brand"
JET_ORANGE = (255, 128, 0)
JET_ORANGE_TEXT = (243, 104, 5)
CHARCOAL = (36, 46, 48)
DARK_TEXT = (50, 50, 55)
MID_TEXT = (89, 89, 89)
LIGHT_TEXT = (158, 158, 158)
WHITE = (255, 255, 255)

# Merlin-specific background (from Figma: #F6F3EF)
MERLIN_BG = (246, 243, 239)

# Stat card styling (from Figma)
CARD_BG = (255, 255, 255)
CARD_BORDER = (240, 236, 230)  # #F0ECE6

# Tag pill styling
TAG_BG = (255, 255, 255)

# Code block background (Figma: support-info-tonal #e4e9fb - light blue)
CODE_BG = (228, 233, 251)

# Table header (Figma: container-strong #f0ece6)
TABLE_HEADER_BG = (240, 236, 230)

# Table border (Figma: border-strong #e7e2da)
TABLE_BORDER = (231, 226, 218)

# Divider
DIVIDER_COLOR = (220, 218, 214)

# Table row divider (Figma: rgba(0,0,0,0.08) on page bg)
TABLE_ROW_DIVIDER = (226, 224, 220)

# Header band height (from Figma: 64px at 595px canvas ≈ 22mm at A4)
HEADER_BAND_H = 22


class MerlinReportPDF(FPDF):
    """PDF subclass for Merlin case study reports.

    Overrides header/footer to use the compact Merlin header band
    instead of standard JET report headers with bookend pages.
    """

    def __init__(self):
        super().__init__()
        self.generated_at = datetime.now().strftime("%-d %B %Y at %H:%M")

    def header(self):
        # Full-page warm background
        self.set_fill_color(*MERLIN_BG)
        self.rect(0, 0, PAGE_W, PAGE_H, style="F")

        # ── JET Orange header band ──────────────────────────────
        self.set_fill_color(*JET_ORANGE)
        self.rect(0, 0, PAGE_W, HEADER_BAND_H, style="F")

        # "Merlin • AI-powered data analysis case studies from Merlin VIP"
        self.set_xy(MARGIN, 8)
        self.set_font("InterMedium", "", 8)
        self.set_text_color(255, 255, 255)  # white
        self.cell(
            0,
            5,
            "Merlin  \u2022  AI-powered data analysis case studies from Merlin VIP",
        )

        # JET icon (top right) - pre-composited on orange to avoid alpha artifacts
        icon_path = os.path.join(IMAGE_DIR, "jet_icon_on_orange.png")
        if os.path.isfile(icon_path):
            icon_size = 10
            self.image(icon_path, PAGE_W - MARGIN - icon_size, 6, icon_size)

        # Content starts below header band
        self.set_y(HEADER_BAND_H + SPACE_MD)

    def footer(self):
        self.set_y(-15)
        # Page number left
        self.set_font("InterMedium", "", 8)
        self.set_text_color(*MID_TEXT)
        self.set_x(MARGIN)
        self.cell(20, 5, str(self.page_no()))
        # Date right-aligned
        self.set_x(MARGIN)
        self.cell(CONTENT_W, 5, self.generated_at, align="R")


def _register_fonts(pdf):
    """Register Inter font family. Falls back to Helvetica if fonts missing."""
    if not os.path.isdir(FONT_DIR):
        return
    pdf.add_font("Inter", "", f"{FONT_DIR}/Inter-Regular.ttf")
    pdf.add_font("Inter", "B", f"{FONT_DIR}/Inter-Bold.ttf")
    pdf.add_font("Inter", "I", f"{FONT_DIR}/Inter-Italic.ttf")
    pdf.add_font("Inter", "BI", f"{FONT_DIR}/Inter-BoldItalic.ttf")
    pdf.add_font("InterMedium", "", f"{FONT_DIR}/Inter-Medium.ttf")
    pdf.add_font("InterSemiBold", "", f"{FONT_DIR}/Inter-SemiBold.ttf")
    pdf.add_font("InterExtraBold", "", f"{FONT_DIR}/Inter-ExtraBold.ttf")
    pdf.add_font("InterBlack", "", f"{FONT_DIR}/Inter-Black.ttf")
    pdf.add_font("InterLight", "", f"{FONT_DIR}/Inter-Light.ttf")


def _check_page_break(pdf, needed_h):
    """If the next block won't fit, start a new page and return True."""
    if pdf.get_y() + needed_h > MAX_Y:
        pdf.add_page()
        return True
    return False


# ── Section renderers ──────────────────────────────────────────────


def draw_title(pdf, title, subtitle=""):
    """Centred title block below the header band.

    Uses multi_cell() so long titles wrap instead of overflowing margins.
    cell() with align="C" silently overflows both edges when text exceeds
    CONTENT_W — the #1 cause of titles bleeding past page margins.
    """
    pdf.ln(SPACE_LG)
    pdf.set_font("InterBlack", "", 25)
    pdf.set_text_color(*CHARCOAL)
    pdf.set_x(MARGIN)
    pdf.multi_cell(CONTENT_W, 10, title, align="C", new_x="LMARGIN", new_y="NEXT")

    if subtitle:
        pdf.ln(SPACE_SM)
        pdf.set_font("Inter", "", 11)
        pdf.set_text_color(*MID_TEXT)
        pdf.set_x(MARGIN)
        pdf.multi_cell(CONTENT_W, 6, subtitle, align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(SPACE_LG)


def _draw_divider(pdf):
    """Thin horizontal divider line."""
    y = pdf.get_y()
    pdf.set_draw_color(*DIVIDER_COLOR)
    pdf.set_line_width(0.3)
    pdf.line(MARGIN, y, PAGE_W - MARGIN, y)
    pdf.ln(SPACE_MD)


def _draw_section_heading(pdf, title):
    """ExtraBold 15pt section heading (matches Figma)."""
    _check_page_break(pdf, 20)
    pdf.set_font("InterExtraBold", "", 15)
    pdf.set_text_color(*CHARCOAL)
    pdf.cell(CONTENT_W, 8, title, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(SPACE_SM)


def draw_summary(pdf, text):
    """Summary section with heading + body text."""
    _draw_section_heading(pdf, "Summary")
    pdf.set_font("Inter", "", 11)
    pdf.set_text_color(*MID_TEXT)
    pdf.multi_cell(CONTENT_W, 5.5, text, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(SPACE_MD)


def draw_keywords(pdf, tags, metadata):
    """Keywords section: tag pills + bold-label metadata lines.

    tags: list of strings (displayed as rounded pills)
    metadata: dict of label->value pairs (e.g. {"Business Domain": "Orders"})
    """
    _draw_section_heading(pdf, "Keywords")

    # ── Tag pills ──────────────────────────────────────────────
    if tags:
        tag_x = MARGIN
        tag_y = pdf.get_y()
        pill_h = 5
        pill_gap = 1.5
        row_gap = 2

        for tag in tags:
            pdf.set_font("Inter", "", 10)
            tw = pdf.get_string_width(tag) + 4  # padding

            # Wrap to next row if overflowing
            if tag_x + tw > PAGE_W - MARGIN:
                tag_x = MARGIN
                tag_y += pill_h + row_gap

            # Draw pill background (Figma: rounded-c = 12px ≈ 4mm)
            # Note: fpdf2 clamps radius when r >= min/2, so use slightly less
            pdf.set_fill_color(*TAG_BG)
            pdf.rect(
                tag_x,
                tag_y,
                tw,
                pill_h,
                style="F",
                round_corners=True,
                corner_radius=pill_h / 2 - 0.01,
            )

            # Draw tag text
            pdf.set_xy(tag_x, tag_y)
            pdf.set_text_color(*CHARCOAL)
            pdf.cell(tw, pill_h, tag, align="C")

            tag_x += tw + pill_gap

        pdf.set_y(tag_y + pill_h + SPACE_SM)

    # ── Metadata key-value lines ───────────────────────────────
    if metadata:
        pdf.ln(SPACE_XS)
        for label, value in metadata.items():
            pdf.set_font("Inter", "B", 11)
            pdf.set_text_color(*CHARCOAL)
            lw = pdf.get_string_width(f"{label}: ") + 1
            pdf.cell(lw, 5.5, f"{label}: ")
            pdf.set_font("Inter", "", 11)
            pdf.set_text_color(*MID_TEXT)
            pdf.cell(CONTENT_W - lw, 5.5, value, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(SPACE_MD)


def draw_numbers(pdf, stats):
    """Row of stat cards with orange values.

    stats: list of dicts with "value" and "label" keys.
           Supports 1-4 items per row.
    """
    if not stats:
        return

    _draw_section_heading(pdf, "Numbers")
    _check_page_break(pdf, 25)

    card_gap = SPACE_SM
    n = min(len(stats), 4)  # max 4 per row
    card_w = (CONTENT_W - card_gap * (n - 1)) / n
    card_h = 20
    card_y = pdf.get_y()
    card_x = MARGIN

    for i, stat in enumerate(stats[:4]):
        # Card background (white with subtle border)
        pdf.set_fill_color(*CARD_BG)
        pdf.set_draw_color(*CARD_BORDER)
        pdf.set_line_width(0.3)
        pdf.rect(
            card_x,
            card_y,
            card_w,
            card_h,
            style="DF",
            round_corners=True,
            corner_radius=1.5,
        )

        # Value (orange, InterBlack)
        pdf.set_xy(card_x + 3, card_y + 3)
        pdf.set_font("InterBlack", "", 13)
        pdf.set_text_color(*JET_ORANGE_TEXT)
        pdf.cell(card_w - 6, 7, str(stat.get("value", "")))

        # Label (subdued)
        pdf.set_xy(card_x + 3, card_y + 11)
        pdf.set_font("InterMedium", "", 8)
        pdf.set_text_color(*MID_TEXT)
        pdf.cell(card_w - 6, 5, str(stat.get("label", "")))

        card_x += card_w + card_gap

    pdf.set_y(card_y + card_h + SPACE_MD)


def draw_key_findings(pdf, findings):
    """Bulleted list with bold labels.

    findings: list of dicts with "label" and "detail" keys,
              or list of plain strings.
    """
    if not findings:
        return

    _draw_section_heading(pdf, "Key Findings")

    bullet = "\u2022"
    for item in findings:
        _check_page_break(pdf, 10)

        if isinstance(item, dict):
            label = item.get("label", "")
            detail = item.get("detail", "")
            text = f"**{label}:** {detail}" if label else detail
        else:
            text = str(item)

        pdf.set_x(MARGIN + 3)
        pdf.set_font("Inter", "", 11)
        pdf.set_text_color(*MID_TEXT)

        # Bullet
        pdf.cell(4, 5.5, bullet)
        # Text with bold support via markdown
        pdf.set_font("Inter", "", 11)
        pdf.multi_cell(
            CONTENT_W - 7, 5.5, text, markdown=True, new_x="LMARGIN", new_y="NEXT"
        )

    pdf.ln(SPACE_MD)


def draw_sql_queries(pdf, queries):
    """Table of SQL queries with monospace filenames.

    queries: list of dicts with "query", "description", "output" keys.
    Renders a Figma-accurate table with rounded border, blue code pills,
    and Courier monospace text for file names.
    """
    if not queries:
        return

    _draw_section_heading(pdf, "SQL Queries")

    col_w = CONTENT_W / 3  # three equal columns (Figma: flex-[1_0_0])
    col_widths = [col_w, col_w, col_w]
    headers = ["Query", "Description", "Output"]
    pad_h = 5  # horizontal padding inside cells (~16px)
    pad_v = 3  # vertical padding inside cells (~8px)
    header_h = 9  # header row height (~32px in Figma)
    corner_r = 4  # rounded corners (~12px in Figma)

    # ── Pre-calculate all row heights ──────────────────────────
    row_heights = []
    for row in queries:
        pdf.set_font("Courier", "", 9)
        h1 = (
            pdf.multi_cell(
                col_w - 2 * pad_h - 4,
                4,
                row.get("query", ""),
                dry_run=True,
                output="HEIGHT",
            )
            + 2 * pad_v
            + 2
        )
        pdf.set_font("Inter", "", 10)
        h2 = (
            pdf.multi_cell(
                col_w - 2 * pad_h,
                5,
                row.get("description", ""),
                dry_run=True,
                output="HEIGHT",
            )
            + 2 * pad_v
        )
        pdf.set_font("Courier", "", 9)
        h3 = (
            pdf.multi_cell(
                col_w - 2 * pad_h - 4,
                4,
                row.get("output", ""),
                dry_run=True,
                output="HEIGHT",
            )
            + 2 * pad_v
            + 2
        )
        row_heights.append(max(h1, h2, h3))

    total_h = header_h + sum(row_heights)
    _check_page_break(pdf, total_h + 4)
    table_y = pdf.get_y()

    # ── Header row fill (top rounded corners) ──────────────────
    pdf.set_fill_color(*TABLE_HEADER_BG)
    pdf.rect(
        MARGIN,
        table_y,
        CONTENT_W,
        header_h,
        style="F",
        round_corners=True,
        corner_radius=corner_r,
    )
    # Fill bottom half of header to square off bottom corners
    pdf.rect(MARGIN, table_y + corner_r, CONTENT_W, header_h - corner_r, style="F")

    # Header text
    pdf.set_font("Inter", "B", 10)
    pdf.set_text_color(*CHARCOAL)
    for i, h in enumerate(headers):
        x = MARGIN + sum(col_widths[:i])
        pdf.set_xy(x + pad_h, table_y + pad_v)
        pdf.cell(col_widths[i] - 2 * pad_h, header_h - 2 * pad_v, h)

    # ── Data rows ──────────────────────────────────────────────
    cur_y = table_y + header_h
    for row_idx, row in enumerate(queries):
        query_name = row.get("query", "")
        description = row.get("description", "")
        output_name = row.get("output", "")
        row_h = row_heights[row_idx]

        # Row divider line
        pdf.set_draw_color(*TABLE_ROW_DIVIDER)
        pdf.set_line_width(0.3)
        pdf.line(MARGIN, cur_y, PAGE_W - MARGIN, cur_y)

        # ── Query cell: blue pill with Courier text ────────────
        cx = MARGIN + pad_h
        cy = cur_y + pad_v
        pdf.set_font("Courier", "", 9)
        pill_w = min(pdf.get_string_width(query_name) + 5, col_w - 2 * pad_h)
        pill_h = (
            pdf.multi_cell(
                col_w - 2 * pad_h - 4, 4, query_name, dry_run=True, output="HEIGHT"
            )
            + 3
        )
        pdf.set_fill_color(*CODE_BG)
        pdf.rect(
            cx, cy, pill_w, pill_h, style="F", round_corners=True, corner_radius=1.5
        )
        pdf.set_xy(cx + 2, cy + 1)
        pdf.set_text_color(*CHARCOAL)
        pdf.multi_cell(col_w - 2 * pad_h - 4, 4, query_name, new_x="LEFT", new_y="NEXT")

        # ── Description cell: regular Inter text ───────────────
        cx = MARGIN + col_w + pad_h
        pdf.set_xy(cx, cur_y + pad_v)
        pdf.set_font("Inter", "", 10)
        pdf.set_text_color(*CHARCOAL)
        pdf.multi_cell(col_w - 2 * pad_h, 5, description, new_x="LEFT", new_y="NEXT")

        # ── Output cell: blue pill with Courier text ───────────
        cx = MARGIN + 2 * col_w + pad_h
        cy = cur_y + pad_v
        pdf.set_font("Courier", "", 9)
        out_pill_w = min(pdf.get_string_width(output_name) + 5, col_w - 2 * pad_h)
        out_pill_h = (
            pdf.multi_cell(
                col_w - 2 * pad_h - 4, 4, output_name, dry_run=True, output="HEIGHT"
            )
            + 3
        )
        pdf.set_fill_color(*CODE_BG)
        pdf.rect(
            cx,
            cy,
            out_pill_w,
            out_pill_h,
            style="F",
            round_corners=True,
            corner_radius=1.5,
        )
        pdf.set_xy(cx + 2, cy + 1)
        pdf.set_text_color(*CHARCOAL)
        pdf.multi_cell(
            col_w - 2 * pad_h - 4, 4, output_name, new_x="LEFT", new_y="NEXT"
        )

        cur_y += row_h

    # ── Rounded border stroke around entire table ──────────────
    pdf.set_draw_color(*TABLE_BORDER)
    pdf.set_line_width(0.3)
    pdf.rect(
        MARGIN,
        table_y,
        CONTENT_W,
        total_h,
        style="D",
        round_corners=True,
        corner_radius=corner_r,
    )

    pdf.set_y(cur_y + SPACE_MD)


def draw_methodology(pdf, steps):
    """Bulleted methodology list with inline code blocks.

    steps: list of strings. Text wrapped in backticks (`code`) gets
           rendered with a grey background pill.
    """
    if not steps:
        return

    _draw_section_heading(pdf, "Methodology")

    bullet = "\u2022"

    for step_text in steps:
        _check_page_break(pdf, 10)

        # Parse inline code blocks: split on backticks
        parts = step_text.split("`")

        pdf.set_x(MARGIN + 3)
        pdf.set_font("Inter", "", 10)
        pdf.set_text_color(*CHARCOAL)
        pdf.cell(4, 5.5, bullet)

        x = pdf.get_x()
        y = pdf.get_y()
        line_w = CONTENT_W - 7
        cur_x = x

        for idx, part in enumerate(parts):
            if not part:
                continue

            is_code = idx % 2 == 1  # odd indices are inside backticks

            if is_code:
                # Add space before code pill if not at line start
                if cur_x > x:
                    cur_x += 1

                pdf.set_font("Courier", "", 9)
                tw = pdf.get_string_width(part) + 5

                # Wrap if doesn't fit
                if cur_x + tw > MARGIN + CONTENT_W:
                    y += 5.5
                    cur_x = x
                    pdf.set_xy(cur_x, y)

                # Code pill background (blue tonal, matching Figma)
                pdf.set_fill_color(*CODE_BG)
                pdf.rect(
                    cur_x,
                    y + 0.5,
                    tw,
                    4.5,
                    style="F",
                    round_corners=True,
                    corner_radius=1.5,
                )
                pdf.set_xy(cur_x + 2, y)
                pdf.set_text_color(*CHARCOAL)
                pdf.cell(tw - 4, 5.5, part)
                cur_x += tw + 1  # space after code pill
            else:
                pdf.set_font("Inter", "", 10)
                pdf.set_text_color(*CHARCOAL)
                tw = pdf.get_string_width(part)

                # Wrap if doesn't fit
                if cur_x + tw > MARGIN + CONTENT_W:
                    y += 5.5
                    cur_x = x
                    pdf.set_xy(cur_x, y)

                pdf.set_xy(cur_x, y)
                pdf.cell(tw, 5.5, part)
                cur_x += tw

        pdf.set_y(y + 6)

    pdf.ln(SPACE_MD)


# ── Main generation function ───────────────────────────────────────


def generate(data, output_path):
    """Generate a Merlin case study PDF from a data dictionary.

    Args:
        data: dict with keys matching the data format documented at the top.
        output_path: path to write the PDF file.
    """
    pdf = MerlinReportPDF()
    pdf.set_left_margin(MARGIN)
    pdf.set_right_margin(MARGIN)
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=False)

    _register_fonts(pdf)

    # Set generated_at from data if provided
    if data.get("generated_at"):
        pdf.generated_at = data["generated_at"]

    # ── Page 1: Main content ───────────────────────────────────
    pdf.add_page()

    draw_title(pdf, data.get("title", ""), data.get("subtitle", ""))
    _draw_divider(pdf)

    if data.get("summary"):
        draw_summary(pdf, data["summary"])

    kw = data.get("keywords", {})
    if kw:
        draw_keywords(pdf, kw.get("tags", []), kw.get("metadata", {}))

    if data.get("numbers"):
        draw_numbers(pdf, data["numbers"])

    if data.get("key_findings"):
        draw_key_findings(pdf, data["key_findings"])

    # ── Page 2+: Supporting data (auto page-breaks as needed) ──
    if data.get("sql_queries"):
        draw_sql_queries(pdf, data["sql_queries"])

    if data.get("methodology"):
        draw_methodology(pdf, data["methodology"])

    pdf.output(output_path)
    return output_path


# ── CLI entry point ────────────────────────────────────────────────

SAMPLE_DATA = {
    "title": "Total Orders in Amsterdam",
    "subtitle": "Last week by order type: Feb 17 2026 - Feb 23 2026",
    "generated_at": "2 March 2026 at 15:45",
    "summary": (
        "Analysis of total orders placed in Amsterdam (NL) over the last 7 days "
        "(Feb 17-23, 2026), grouped by order type. A total of 72,186 orders were "
        "placed across three order types: Delivery, Restaurant Delivery, and Pickup. "
        "The two delivery modes - Delivery and Restaurant Delivery - dominate "
        "nearly equally at ~48% each, while Pickup accounts for just over 4%."
    ),
    "keywords": {
        "tags": [
            "order_type",
            "orders",
            "amsterdam",
            "delivery",
            "restaurant_delivery",
            "pickup",
            "NL",
        ],
        "metadata": {
            "Business Domain": "Orders",
            "Region": "NL (Netherlands - Amsterdam)",
            "Time Period": "Last 7 Days (2026-02-17 to 2026-02-23)",
            "Tables Used": "core_dwh.fact_order, core_dwh.dim_ordertype, core_dwh.dim_city",
        },
    },
    "numbers": [
        {"value": "72,186", "label": "Total orders"},
        {"value": "34,578", "label": "Restaurant delivery"},
        {"value": "47.91%", "label": "Courier delivery"},
    ],
    "key_findings": [
        {
            "label": "Total Orders",
            "detail": "72,186 orders in Amsterdam over the last 7 days",
        },
        {
            "label": "Delivery",
            "detail": "34,581 orders (47.91%) - courier / DaaS delivery",
        },
        {
            "label": "Restaurant Delivery",
            "detail": "34,578 orders (47.90%) - restaurant-owned delivery fleet",
        },
        {
            "label": "Pickup",
            "detail": "3,027 orders (4.19%) - customer collection from restaurant",
        },
        {
            "label": "",
            "detail": "Delivery vs Restaurant Delivery split is nearly 50/50, suggesting a balanced use of both delivery models in Amsterdam",
        },
    ],
    "sql_queries": [
        {
            "query": "01_amsterdam_orders_by_type_last_week.sql",
            "description": "Orders grouped by order type (Delivery, Restaurant Delivery, Pickup)",
            "output": "results/01_amsterdam_orders_by_type_last_week.txt",
        },
        {
            "query": "02_amsterdam_orders_summary.sql",
            "description": "Total order count and date range summary",
            "output": "results/02_amsterdam_orders_summary.txt",
        },
    ],
    "methodology": [
        "Amsterdam is identified via `core_dwh.dim_city.cityid = 1` (Amsterdam, NL)",
        "`fact_order.restaurantcityid` is joined to `dim_city` to filter Amsterdam restaurant orders",
        "`fact_order.ordertypeid` is joined to `dim_ordertype` for human-readable order type labels",
        "Period: last 7 full days (excluding today), using `orderdatetime` partition column",
    ],
}


if __name__ == "__main__":
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        with open(sys.argv[1], "r") as f:
            data = json.load(f)
    else:
        data = SAMPLE_DATA

    out_dir = os.path.join(os.getcwd(), "reports")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "merlin_report.pdf")
    generate(data, out)
    print(f"Generated: {out}")
