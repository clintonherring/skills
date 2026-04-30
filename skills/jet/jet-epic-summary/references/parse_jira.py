import json, sys


def extract_text_from_adf(node):
    """Recursively extract plain text from an ADF (Atlassian Document Format) node."""
    texts = []
    if isinstance(node, dict):
        if node.get('type') == 'text':
            texts.append(node.get('text', ''))
        for child in node.get('content', []):
            texts.extend(extract_text_from_adf(child))
    elif isinstance(node, list):
        for item in node:
            texts.extend(extract_text_from_adf(item))
    return texts


def get_description(issue, fields):
    """Extract description text from various Jira response formats."""
    desc_obj = fields.get('description') if fields else issue.get('description')
    if desc_obj and isinstance(desc_obj, dict):
        return ' '.join(extract_text_from_adf(desc_obj))
    elif isinstance(desc_obj, str):
        return desc_obj
    return 'No description'


def get_status(issue, fields):
    """Extract status name from various Jira response formats."""
    if fields:
        status = fields.get('status', {})
        if isinstance(status, dict):
            return status.get('name', 'N/A')
        if isinstance(status, str):
            return status
    status = issue.get('status', {})
    if isinstance(status, dict):
        return status.get('name', 'N/A')
    if isinstance(status, str):
        return status
    return 'N/A'


def normalise_issues(data):
    """Return a flat list of issues from any supported format.

    Supported shapes:
      - Jira REST API search: {"issues": [...]}
      - Direct JSON array:    [{"key": "...", ...}, ...]
      - Single issue object:  {"key": "...", ...}
    """
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if 'errorMessages' in data:
            print('ERROR:', data['errorMessages'], file=sys.stderr)
            sys.exit(1)
        if 'issues' in data:
            return data['issues']
        if 'key' in data:
            return [data]
    return []


raw = sys.stdin.read().strip()
if not raw:
    print('No input received.', file=sys.stderr)
    sys.exit(1)

data = json.loads(raw)
issues = normalise_issues(data)

print(f"Total issues found: {len(issues)}")
print()

for i, issue in enumerate(issues, 1):
    key = issue.get('key', 'N/A')
    fields = issue.get('fields')  # present in REST API format; None for flat format
    summary = (fields or issue).get('summary', 'N/A')
    status = get_status(issue, fields)
    desc = get_description(issue, fields)

    print(f'--- [{i}] {key} ---')
    print(f'Summary:     {summary}')
    print(f'Status:      {status}')
    print(f'Description: {desc}')
    print()

