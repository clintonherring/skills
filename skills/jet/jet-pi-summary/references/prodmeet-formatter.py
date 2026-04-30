#!/usr/bin/env python3
"""
Prod Meet Briefing Formatter

Reads Athena JSON output (All Open PIs query) from stdin and produces a
structured markdown briefing for the Daily Production Meeting host.

Usage:
    athena_query "..." "odl_athena_workgroup" 2>/dev/null | python3 prodmeet-formatter.py
    athena_query "..." "odl_athena_workgroup" 2>/dev/null | python3 prodmeet-formatter.py --hours 96
    athena_query "..." "odl_athena_workgroup" 2>/dev/null | python3 prodmeet-formatter.py --day 2
    athena_query "..." "odl_athena_workgroup" 2>/dev/null | python3 prodmeet-formatter.py --output custom.md

Arguments:
    --hours N       Override the lookback window in hours (e.g. 96 for post-Bank-Holiday)
    --day DOW       Override the day of week (1=Monday ... 7=Sunday). Default: auto-detect.
    --output FILE   Override output filename (default: yyyy-mm-dd-prodmeet-notes.md).
    --no-output     Disable file output (print to stdout only).

Input format (athena_query JSON):
    {"columns": [{"Name": "key", "Type": "varchar"}, ...], "rows": [["PI-123", ...], ...]}

The script auto-detects day-of-week to set the lookback window and weekly focus:
    Monday:         72h (covers Fri-Sun)
    Tuesday-Friday: 24h
"""

import argparse
import json
import re
import sys
from datetime import datetime


def parse_labels(labels_str: str) -> list:
    """Parse Athena array string like '[Track, onhold]' into a Python list."""
    if not labels_str or labels_str.strip() in ("", "[]", "NULL"):
        return []
    cleaned = labels_str.strip().strip("[]")
    if not cleaned:
        return []
    return [l.strip() for l in cleaned.split(",") if l.strip()]


def has_label(labels_list: list, target: str) -> bool:
    """Check for an exact label match (case-insensitive)."""
    return any(l.lower() == target.lower() for l in labels_list)


def read_athena_json_from_stdin() -> list:
    """Read athena_query JSON from stdin, return list of dicts.

    Handles ANSI escape codes that may be present in the output.
    Skips non-JSON diagnostic lines (e.g. 'Query started:', 'Waiting for').
    """
    raw = sys.stdin.read()
    if not raw.strip():
        return []

    # Strip ANSI escape codes
    raw = re.sub(r'\x1b\[[0-9;]*m', '', raw)

    # Find the JSON object (skip diagnostic lines from athena_query)
    json_start = raw.find('{')
    if json_start == -1:
        print("Error: No JSON found in input", file=sys.stderr)
        return []

    json_str = raw[json_start:]
    # Trim trailing non-JSON content (diagnostic lines after the closing brace)
    json_end = json_str.rfind('}')
    if json_end != -1:
        json_str = json_str[:json_end + 1]

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse Athena JSON output: {e}", file=sys.stderr)
        print(f"Input starts with: {json_str[:200]!r}", file=sys.stderr)
        return []

    if "columns" not in data or "rows" not in data:
        print("Error: Unexpected Athena JSON structure — missing 'columns' or 'rows' keys", file=sys.stderr)
        return []
    col_names = [c.get("Name", "") if isinstance(c, dict) else str(c) for c in data["columns"]]
    rows = []
    for raw_row in data["rows"]:
        row = dict(zip(col_names, raw_row))
        row["age_days"] = int(row.get("age_days", 0) or 0)
        row["age_hours"] = int(row.get("age_hours", 0) or 0)
        row["days_since_update"] = int(row.get("days_since_update", 0) or 0)
        row["labels_list"] = parse_labels(row.get("labels", ""))
        row["owners"] = (row.get("owners") or "").strip()
        row["priority"] = (row.get("priority") or "").strip()
        row["status"] = (row.get("status") or "").strip()
        rows.append(row)
    return rows


def get_window_hours(dow: int) -> int:
    """Return default lookback window hours for the given day of week (1=Mon)."""
    return 72 if dow == 1 else 24


def day_name(dow: int) -> str:
    return ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][dow - 1]


# ── Table rendering ──────────────────────────────────────────────────────────

def pi_table(rows: list, columns: list) -> str:
    """Render a markdown table for a list of PI rows.

    columns is a list of (header, accessor_fn) tuples.
    """
    if not rows:
        return ""
    header = "| " + " | ".join(h for h, _ in columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    lines = [header, sep]
    for r in rows:
        cells = []
        for _, fn in columns:
            cells.append(str(fn(r)).replace("|", "\\|"))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def link(row: dict) -> str:
    key = row.get("key", "?")
    url = row.get("issue_url", f"https://justeattakeaway.atlassian.net/browse/{key}")
    return f"[{key}]({url})"


STD_COLUMNS = [
    ("Key", link),
    ("Summary", lambda r: r.get("summary", "")),
    ("Priority", lambda r: r.get("priority", "")),
    ("Status", lambda r: r.get("status", "")),
    ("Owner", lambda r: "—" if is_no_owner(r.get("owners", "")) else r.get("owners", "—")),
]


# ── Section builders ─────────────────────────────────────────────────────────

def section_new_pis(rows: list, hours: int) -> str:
    new = [r for r in rows if r["age_hours"] <= hours]
    title = f"### 1. New PIs (last {hours} hrs)\n"
    if not new:
        return title + f"✅ No new PIs in the last {hours} hours\n"
    return title + pi_table(new, STD_COLUMNS) + "\n"


def is_no_owner(owners: str) -> bool:
    """Check if an owner field effectively means 'no owner'."""
    return not owners or owners.lower() in ("unknown", "null", "none", "")


def section_tracked(rows: list) -> str:
    tracked = [r for r in rows if has_label(r["labels_list"], "Track")]
    title = "### 2. Tracked PIs\n"
    if not tracked:
        return title + "✅ No tracked PIs\n"
    return title + pi_table(tracked, STD_COLUMNS) + "\n"


def section_no_owner(rows: list) -> str:
    no_owner = [r for r in rows if is_no_owner(r["owners"])]
    title = "### 3. PIs with No Owner\n"
    if not no_owner:
        return title + "✅ All PIs have an owner\n"
    return title + pi_table(no_owner, STD_COLUMNS) + "\n"


def section_in_progress_outside_window(rows: list, hours: int) -> str:
    ips = [r for r in rows if r["status"] == "In Progress" and r["age_hours"] > hours]
    title = f"### 4. In-Progress PIs (outside {hours}h window)\n"
    if not ips:
        return title + "✅ No In-Progress PIs outside the window\n"
    cols = STD_COLUMNS + [("Age (days)", lambda r: str(r["age_days"]))]
    note = "> **Review these** — In Progress means impact is ongoing. Move to Investigating if impact has stopped.\n\n"
    return title + note + pi_table(ips, cols) + "\n"


def section_open_summary(rows: list) -> str:
    title = "### 5. Open PI Summary\n"
    counts: dict = {}
    for r in rows:
        s = r["status"] or "Unknown"
        counts[s] = counts.get(s, 0) + 1
    if not counts:
        return title + "No open PIs found.\n"
    lines = ["| Status | Count |", "| --- | --- |"]
    for s in sorted(counts, key=lambda x: -counts[x]):
        lines.append(f"| {s} | {counts[s]} |")
    return title + "\n".join(lines) + "\n"


# ── Weekly focus sections ────────────────────────────────────────────────────

def weekly_pending_risk_accept(rows: list) -> str:
    pra = [r for r in rows if r["status"] == "Pending Risk Accept"]
    title = "### Pending Risk Accept\n"
    if not pra:
        return title + "✅ No PIs pending risk acceptance\n"
    note = "> Remind the meeting audience to either accept these or return them for further investigation.\n\n"
    cols = STD_COLUMNS + [("Age (days)", lambda r: str(r["age_days"]))]
    return title + note + pi_table(pra, cols) + "\n"


def weekly_stale(rows: list) -> str:
    stale = sorted([r for r in rows if r["days_since_update"] >= 7],
                   key=lambda r: -r["days_since_update"])
    title = "### PIs Not Updated in 7+ Days\n"
    if not stale:
        return title + "✅ All PIs have been updated within the last 7 days\n"
    note = "> Ask the assignee to update these PIs.\n\n"
    cols = STD_COLUMNS + [("Days Since Update", lambda r: str(r["days_since_update"]))]
    return title + note + pi_table(stale, cols) + "\n"


def weekly_crit_major(rows: list) -> str:
    cm = [r for r in rows if r["priority"] in ("Critical", "Major")]
    title = "### Open Critical & Major PIs\n"
    if not cm:
        return title + "✅ No open Critical or Major PIs\n"
    note = "> Review all and ask for updates.\n\n"
    cols = STD_COLUMNS + [("Age (days)", lambda r: str(r["age_days"]))]
    return title + note + pi_table(cm, cols) + "\n"


def weekly_srm_reminder() -> str:
    return "### SRM Report Reminder\n\n⏰ *Leave 15 minutes at the end for the weekly SRM report*\n"


def weekly_50_day(rows: list) -> str:
    old = sorted([r for r in rows if r["age_days"] >= 50], key=lambda r: -r["age_days"])
    title = "### PIs Over 50 Days Old\n"
    if not old:
        return title + "✅ No PIs over 50 days old\n"
    note = "> Review to ensure progress is genuine and not just token updates.\n\n"
    cols = STD_COLUMNS + [("Age (days)", lambda r: str(r["age_days"]))]
    return title + note + pi_table(old, cols) + "\n"


WEEKLY_SECTIONS = {
    1: [],  # Monday — no weekly focus
    2: ["pending_risk_accept", "stale"],
    3: ["crit_major"],
    4: ["srm_reminder"],
    5: ["fifty_day"],
    6: [],
    7: [],
}

WEEKLY_TITLES = {
    2: "Pending Risk Accept & Stale PIs",
    3: "Critical & Major PIs",
    4: "SRM Report",
    5: "Aged PIs Review",
}

WEEKLY_BUILDERS = {
    "pending_risk_accept": weekly_pending_risk_accept,
    "stale": weekly_stale,
    "crit_major": weekly_crit_major,
    "srm_reminder": lambda _: weekly_srm_reminder(),
    "fifty_day": weekly_50_day,
}


# ── Main ─────────────────────────────────────────────────────────────────────

def is_non_issue(status: str) -> bool:
    """Check if a status means 'Non Issue' (handles hyphen/space/case variants)."""
    normalised = status.lower().replace("-", "").replace(" ", "")
    return normalised == "nonissue"


def filter_non_issue(rows: list, hours: int) -> list:
    """Drop Non Issue PIs that fall outside the lookback window.

    Recent Non Issue PIs (age_hours <= hours) are kept so they appear in
    the New PIs section for triage review.  Older ones are discarded entirely
    — they don't count towards totals or any other section.
    """
    return [
        r for r in rows
        if not is_non_issue(r["status"]) or r["age_hours"] <= hours
    ]


def build_briefing(rows: list, hours: int, dow: int) -> str:
    today = datetime.now().strftime("%A, %d %B %Y")

    # Drop old Non-Issue PIs entirely (only recent ones kept for New PIs triage)
    rows = filter_non_issue(rows, hours)
    actionable_rows = [r for r in rows if not is_non_issue(r["status"])]
    non_issue_new = [r for r in rows if is_non_issue(r["status"])]
    total = len(actionable_rows)

    parts = []
    parts.append(f"# 🏭 Prod Meet Briefing — {today}")
    triage_note = f" (+ {len(non_issue_new)} Non-Issue in triage)" if non_issue_new else ""
    parts.append(f"**Window:** {hours}h | **Total open PIs:** {total}{triage_note}\n")
    parts.append("---\n")

    # Daily Focus
    parts.append("## 📋 Daily Focus\n")
    parts.append(section_new_pis(rows, hours))
    parts.append(section_tracked(actionable_rows))
    parts.append(section_no_owner(actionable_rows))
    parts.append(section_in_progress_outside_window(actionable_rows, hours))
    parts.append(section_open_summary(actionable_rows))

    # Weekly Focus (day-dependent)
    weekly_keys = WEEKLY_SECTIONS.get(dow, [])
    if weekly_keys:
        weekly_title = WEEKLY_TITLES.get(dow, "Weekly Focus")
        parts.append("---\n")
        parts.append(f"## 📅 Weekly Focus — {weekly_title}\n")
        for key in weekly_keys:
            builder = WEEKLY_BUILDERS[key]
            parts.append(builder(actionable_rows))

    parts.append("---")
    parts.append("*Briefing generated from ODL data. Check the [Prod Meet Dashboard](https://justeattakeaway.atlassian.net/) for real-time updates.*")

    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser(
        description="Format Athena All-Open-PIs CSV into a Prod Meet briefing"
    )
    parser.add_argument(
        "--hours", type=int, default=None,
        help="Override lookback window in hours (e.g. 96 for post-Bank-Holiday)"
    )
    parser.add_argument(
        "--day", type=int, default=None, choices=range(1, 8),
        help="Override day of week (1=Monday ... 7=Sunday). Default: auto-detect."
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Output markdown file. Default: yyyy-mm-dd-prodmeet-notes.md. Use --no-output to skip file writing."
    )
    parser.add_argument(
        "--no-output", action="store_true",
        help="Disable file output (print to stdout only)"
    )
    args = parser.parse_args()

    dow = args.day if args.day is not None else datetime.now().isoweekday()
    hours = args.hours if args.hours is not None else get_window_hours(dow)

    rows = read_athena_json_from_stdin()
    briefing = build_briefing(rows, hours, dow)
    print(briefing)

    if not args.no_output:
        output_path = args.output or datetime.now().strftime("%Y-%m-%d-prodmeet-notes.md")
        with open(output_path, "w") as f:
            f.write(briefing + "\n")
        print(f"\n📄 Briefing written to {output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
