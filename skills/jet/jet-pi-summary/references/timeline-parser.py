import re
import json
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from typing import Optional, List, Dict, Any, Union


def _parse_iso(s: str) -> datetime:
    """Parse an ISO 8601 string using stdlib only (handles trailing Z)."""
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _parse_time(date: datetime.date, time_str: str, am_pm: str = "") -> datetime:
    """Parse a date + HH:MM + optional AM/PM into a naive datetime."""
    if am_pm:
        return datetime.strptime(f"{date} {time_str} {am_pm}", "%Y-%m-%d %I:%M %p")
    return datetime.strptime(f"{date} {time_str}", "%Y-%m-%d %H:%M")


def _get_tz(name: str) -> Optional[ZoneInfo]:
    """Resolve an IANA timezone name, returning None if invalid."""
    try:
        return ZoneInfo(name)
    except (KeyError, Exception):
        return None


def extract_jira_timestamps(text_blob: Union[str, list], jira_creation_date: Optional[datetime.date] = None) -> \
List[Dict[str, Any]]:
    """
    Parses a complex Jira text blob (either a single string or a list of strings)
    for timestamps and converts them to UTC.
    """
    if isinstance(text_blob, list):
        text_blob = "\n".join(s.replace(",", "\n") for s in text_blob)
    elif not isinstance(text_blob, str):
        return []

    text_blob = re.sub(r'(\d{1,2}:\d{2})(?=[^\s\-:])', r'\1 ', text_blob)

    converted_timestamps = []
    timezone_map = {
        "GMT": "Europe/London", "WET": "Europe/Lisbon", "WEST": "Europe/Lisbon",
        "CET": "Europe/Paris", "CEST": "Europe/Paris", "EET": "Europe/Athens",
        "EEST": "Europe/Athens", "BST": "Europe/London", "IST-IRELAND": "Europe/Dublin",
        "EST": "America/New_York", "EDT": "America/New_York", "CST": "America/Chicago",
        "CDT": "America/Chicago", "MST": "America/Denver", "MDT": "America/Denver",
        "PST": "America/Los_Angeles", "PDT": "America/Los_Angeles", "AKST": "America/Anchorage",
        "AKDT": "America/Anchorage", "HST": "Pacific/Honolulu", "AEST": "Australia/Sydney",
        "AEDT": "Australia/Sydney", "ACST": "Australia/Adelaide", "ACDT": "Australia/Adelaide",
        "AWST": "Australia/Perth", "NZST": "Pacific/Auckland", "NZDT": "Pacific/Auckland",
        "JST": "Asia/Tokyo", "KST": "Asia/Seoul", "SGT": "Asia/Singapore",
        "HKT": "Asia/Hong_Kong", "IRST": "Asia/Tehran", "IRDT": "Asia/Tehran",
        "IDT": "Asia/Jerusalem", "IST-ISRAEL": "Asia/Jerusalem", "IST-INDIA": "Asia/Kolkata",
        "UTC": "UTC",
    }

    source_tz = ZoneInfo("UTC")
    current_date = jira_creation_date or datetime.now().date()
    last_parsed_time = None

    timezone_pattern = re.compile(r"TIMEZONE: ?[\[]?([\w/]+)[]]?", re.IGNORECASE)
    timezone_match = timezone_pattern.search(text_blob)

    if timezone_match:
        tz_abbrev_list = timezone_match.group(1).upper().split('/')
        tz_abbrev = tz_abbrev_list[0]
        canonical_tz_name = timezone_map.get(tz_abbrev, tz_abbrev)
        new_source_tz = _get_tz(canonical_tz_name)
        if new_source_tz:
            source_tz = new_source_tz

    # Handles: "08:19 AM - Event", "08:31 AM- Event", "14:44: Event", "14:44 : Event", "08:19 - Event"
    timestamp_pattern = re.compile(
        r"(\d{1,2}:\d{2})\s*(AM|PM|am|pm|Am|Pm)?\s*[-:]\s*(.*?(?=\s*\d{1,2}:\d{2}\s*(?:AM|PM|am|pm|Am|Pm)?\s*[-:]|$))",
        re.DOTALL
    )

    matches = list(timestamp_pattern.finditer(text_blob))
    if not matches and text_blob.strip():
        converted_timestamps.append({
            "utc_datetime": datetime.combine(current_date, datetime.min.time()).replace(tzinfo=source_tz).astimezone(
                timezone.utc),
            "source": "Jira",
            "event": text_blob.strip()
        })
        return converted_timestamps

    for match in matches:
        time_part = match.group(1).strip()
        am_pm = (match.group(2) or "").strip().upper()
        event_text = match.group(3).strip()

        if len(time_part.split(':')[0]) == 1:
            time_part = "0" + time_part

        parsed_dt = _parse_time(current_date, time_part, am_pm)

        if last_parsed_time and parsed_dt.time() < last_parsed_time:
            current_date += timedelta(days=1)
            parsed_dt = parsed_dt.replace(year=current_date.year, month=current_date.month, day=current_date.day)

        last_parsed_time = parsed_dt.time()
        parsed_dt = parsed_dt.replace(tzinfo=source_tz)
        utc_dt = parsed_dt.astimezone(timezone.utc)

        converted_timestamps.append({
            "utc_datetime": utc_dt,
            "source": "Jira",
            "event": event_text.strip()
        })

    return converted_timestamps


def extract_slack_timestamps(slack_messages: list) -> list:
    """
    Parses a list of Slack messages (with timestamps) that are already in UTC.
    """
    converted_timestamps = []
    if not slack_messages:
        return []

    for message in slack_messages:
        utc_dt = _parse_iso(message['timestamp_utc'])
        converted_timestamps.append({
            "utc_datetime": utc_dt,
            "source": "Slack",
            "event": message["text"]
        })

    converted_timestamps.sort(key=lambda x: x["utc_datetime"])
    return converted_timestamps


def create_unified_timeline(jira_text: str, slack_messages: list, jira_created: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Combines events from Jira and Slack into a single, sorted timeline.
    """
    slack_events = []
    if slack_messages:
        slack_events = extract_slack_timestamps(slack_messages)

    jira_creation_date = _parse_iso(jira_created).date() if jira_created else None
    if slack_events:
        jira_creation_date = slack_events[0]['utc_datetime'].date()

    jira_events = []
    if jira_text:
        jira_events = extract_jira_timestamps(jira_text, jira_creation_date)

    all_events = jira_events + slack_events
    all_events.sort(key=lambda x: x["utc_datetime"])

    return all_events


def format_timeline_for_llm(events: List[Dict[str, Any]], display_tz=None) -> str:
    """
    Formats a list of event dictionaries into a string for LLM consumption.
    Converts timestamps to display_tz if provided, otherwise uses UTC.
    """
    formatted_lines = []
    for event in events:
        dt = event['utc_datetime']
        if display_tz:
            dt = dt.astimezone(display_tz)
        formatted_lines.append(
            f"[{dt.isoformat()}] | Source: {event['source']} | Event: {event['event']}"
        )
    return "\n".join(formatted_lines)


def get_local_timezone():
    """Detect the machine's local timezone."""
    local_tz = datetime.now().astimezone().tzinfo
    return local_tz


def _extract_column_index(columns: list, name: str) -> int:
    """Find a column index by name in Athena result metadata."""
    for i, col in enumerate(columns):
        if col.get("Name", "").lower() == name.lower():
            return i
    raise KeyError(f"Column '{name}' not found in Athena results")


def load_jira_from_athena(filepath: str) -> tuple:
    """Read Athena JSON for Jira and extract (timeline_text, created_date).

    Expects the output of: athena_query "..." | clean-athena-output.py
    """
    with open(filepath) as f:
        raw = f.read()
    start = raw.find('{')
    end = raw.rfind('}')
    data = json.loads(raw[start:end + 1]) if start != -1 and end > start else json.loads(raw)

    cols = data["columns"]
    if not data.get("rows"):
        raise ValueError(f"No Jira rows found in {filepath!r} — check the issue key and that the data extract has run")
    row = data["rows"][0]

    timeline_idx = _extract_column_index(cols, "timeline")
    created_idx = _extract_column_index(cols, "created")

    return row[timeline_idx], row[created_idx]


def load_slack_from_athena(filepath: str) -> list:
    """Read Athena JSON for Slack and return list of {timestamp_utc, text} dicts.

    Expects the output of: athena_query "..." | clean-athena-output.py
    """
    with open(filepath) as f:
        raw = f.read()
    start = raw.find('{')
    end = raw.rfind('}')
    data = json.loads(raw[start:end + 1]) if start != -1 and end > start else json.loads(raw)

    cols = data["columns"]
    if not data.get("rows"):
        return []
    ts_idx = _extract_column_index(cols, "timestamp_utc")
    text_idx = _extract_column_index(cols, "text")

    return [{"timestamp_utc": row[ts_idx], "text": row[text_idx]} for row in data["rows"]]


if __name__ == "__main__":
    import json
    import sys
    import argparse

    arg_parser = argparse.ArgumentParser(description="Parse and merge Jira/Slack incident timelines")
    arg_parser.add_argument("jira_text", nargs="?", default="", help="Jira timeline free-text blob (legacy)")
    arg_parser.add_argument("slack_json", nargs="?", default="[]", help="JSON array of Slack messages (legacy)")
    arg_parser.add_argument("jira_created", nargs="?", default=None, help="Jira created date ISO 8601 (legacy)")
    arg_parser.add_argument("--jira-athena", default=None, help="Path to Athena JSON file for Jira query results")
    arg_parser.add_argument("--slack-athena", default=None, help="Path to Athena JSON file for Slack query results")
    arg_parser.add_argument("--local-tz", action="store_true", help="Display timestamps in the machine's local timezone instead of UTC")
    arg_parser.add_argument("--tz", default=None, help="Display timestamps in a specific timezone (e.g. Europe/London, America/New_York)")
    args = arg_parser.parse_args()

    display_tz = None
    if args.tz:
        display_tz = _get_tz(args.tz)
        if not display_tz:
            print(f"Warning: Unknown timezone '{args.tz}', falling back to local", file=sys.stderr)
            display_tz = get_local_timezone()
    elif args.local_tz:
        display_tz = get_local_timezone()

    # Prefer --jira-athena / --slack-athena files over positional args
    if args.jira_athena or args.slack_athena:
        jira_text = ""
        jira_created = None
        slack_messages = []

        if args.jira_athena:
            jira_text, jira_created = load_jira_from_athena(args.jira_athena)
        if args.slack_athena:
            slack_messages = load_slack_from_athena(args.slack_athena)

        events = create_unified_timeline(jira_text, slack_messages, jira_created)
    else:
        slack_messages = json.loads(args.slack_json)
        events = create_unified_timeline(args.jira_text, slack_messages, args.jira_created)

    print(format_timeline_for_llm(events, display_tz=display_tz))
