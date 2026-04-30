#!/usr/bin/env python3
"""
Clean Athena query output for the PI summary skill.

Reads Athena JSON from stdin (the format produced by athena_query),
strips Slack mrkdwn formatting, decodes HTML entities, and normalises
whitespace. Writes cleaned JSON to stdout in the same schema.

Usage:
    athena_query "..." "odl_athena_workgroup" | python3 references/clean-athena-output.py
"""

import json
import re
import sys
import html


def clean_slack_mrkdwn(text: str) -> str:
    """Strip Slack mrkdwn formatting from a string."""
    if not text:
        return text

    # <@U04K08YGMPY> → @user  (user mention)
    text = re.sub(r'<@(\w+)>', r'@\1', text)

    # <!subteam^S07CU80JXUG|@group> → @group  (user group with label)
    text = re.sub(r'<!subteam\^[^|>]+\|([^>]+)>', r'\1', text)
    # <!subteam^S07CU80JXUG> → @group  (user group without label)
    text = re.sub(r'<!subteam\^(\w+)>', r'@\1', text)

    # <!here>, <!channel>, <!everyone>
    text = re.sub(r'<!(\w+)(?:\|[^>]*)?>', r'@\1', text)

    # <https://example.com|Display Text> → Display Text  (rich link with label)
    text = re.sub(r'<(https?://[^|>]+)\|([^>]+)>', r'\2', text)

    # <https://example.com> → https://example.com  (bare link)
    text = re.sub(r'<(https?://[^>]+)>', r'\1', text)

    # <mailto:user@example.com|user@example.com> → user@example.com
    text = re.sub(r'<mailto:[^|>]+\|([^>]+)>', r'\1', text)
    text = re.sub(r'<mailto:([^>]+)>', r'\1', text)

    # HTML entities: &amp; &lt; &gt;
    text = html.unescape(text)

    # :emoji: → remove (require at least one letter to avoid matching timestamps like 14:44:)
    text = re.sub(r'(?<!\d):(?=[^:\s]*[a-zA-Z])[\w+-]+:', '', text)

    # Strip bold/italic/strikethrough markers: *bold*, _italic_, ~strike~
    # Only strip when they wrap a word (not mid-sentence asterisks like 116*)
    text = re.sub(r'(?<!\w)\*([^*\n]+)\*(?!\w)', r'\1', text)
    text = re.sub(r'(?<!\w)_([^_\n]+)_(?!\w)', r'\1', text)
    text = re.sub(r'(?<!\w)~([^~\n]+)~(?!\w)', r'\1', text)

    # Inline code: `code` → code
    text = re.sub(r'`([^`\n]+)`', r'\1', text)

    # Code blocks: ```code``` → code
    text = re.sub(r'```([^`]*)```', r'\1', text)

    # Collapse multiple spaces (but preserve newlines)
    text = re.sub(r'[^\S\n]+', ' ', text)

    # Collapse multiple blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def clean_row(row: list, columns: list) -> list:
    """Clean all string values in a row."""
    cleaned = []
    for val in row:
        if isinstance(val, str):
            cleaned.append(clean_slack_mrkdwn(val))
        else:
            cleaned.append(val)
    return cleaned


def extract_json(raw: str) -> dict:
    """Extract the JSON object from raw input that may have status lines before it.

    athena_query writes progress lines to stderr, but when the agent captures
    combined output (stdout+stderr) those lines appear before the JSON.  This
    finds the first '{' and last '}' and parses just that slice.
    """
    start = raw.find('{')
    end = raw.rfind('}')
    if start == -1 or end == -1 or end <= start:
        raise json.JSONDecodeError("No JSON object found in input", raw, 0)
    return json.loads(raw[start:end + 1])


def main():
    raw = sys.stdin.read()
    if not raw.strip():
        print("{}", file=sys.stdout)
        return

    try:
        data = extract_json(raw)
    except json.JSONDecodeError as e:
        print(f"Error: Could not extract JSON from input: {e}", file=sys.stderr)
        sys.exit(1)

    if "rows" not in data or "columns" not in data:
        print(json.dumps(data))
        return

    columns = data["columns"]
    cleaned_rows = [clean_row(row, columns) for row in data["rows"]]

    output = {
        "columns": columns,
        "rows": cleaned_rows,
    }
    if "next_token" in data:
        output["next_token"] = data["next_token"]

    json.dump(output, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
