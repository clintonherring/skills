# Jira & Confluence Search Patterns

Patterns for discovering event-driven architecture context from Jira tickets and Confluence pages using `acli` (Jira) and `confluence-cli` (Confluence).

## Tools

| Tool | Scope | Installation (macOS/Linux) | Installation (Windows) | Auth |
|------|-------|--------------------------|------------------------|------|
| `acli` | Jira Cloud | `brew tap atlassian/acli && brew install acli` | See [Atlassian CLI Windows install guide](https://developer.atlassian.com/cloud/acli/guides/install-windows/) | `acli jira auth` |
| `confluence-cli` | Confluence Cloud | `npm install -g confluence-cli` | `npm install -g confluence-cli` | `confluence init` |

These are **separate tools** with separate authentication. See **jet-company-standards** skill for full setup.

## Jira Search (acli)

### Default Flags

**ALWAYS** include these flags on all work-item read operations:

```bash
--json --fields="*all"
```

This ensures structured JSON output with all fields (including custom fields that are often excluded by default).

### Event Discovery via JQL

JQL `text ~ "term"` searches summary, description, and comments. It is **case-insensitive** by default.

```bash
# Find all tickets mentioning an event name
acli jira workitem search --jql "text ~ \"EVENT_NAME\"" --json --fields="*all" --limit 20

# Search for naming variants separately (JQL text search doesn't support regex)
acli jira workitem search --jql "text ~ \"MyEvent\"" --json --fields="*all" --limit 20
acli jira workitem search --jql "text ~ \"my-event\"" --json --fields="*all" --limit 20
acli jira workitem search --jql "text ~ \"my_event\"" --json --fields="*all" --limit 20
```

### Production Incident (PI) Tickets

PI tickets are a high-signal source. Root cause analysis sections typically name specific events, topics, and impacted services.

```bash
# PI tickets mentioning an event
acli jira workitem search --jql "project = PI AND text ~ \"EVENT_NAME\"" --json --fields="*all" --limit 10

# Recent PIs only (last 90 days)
acli jira workitem search --jql "project = PI AND text ~ \"EVENT_NAME\" AND created >= -90d" --json --fields="*all" --limit 10

# High-severity PIs mentioning a topic/event
acli jira workitem search --jql "project = PI AND text ~ \"EVENT_NAME\" AND priority in (Critical, High)" --json --fields="*all" --limit 10

# PIs mentioning a messaging platform
acli jira workitem search --jql "project = PI AND text ~ \"kafka\" AND text ~ \"EVENT_NAME\"" --json --fields="*all" --limit 10
acli jira workitem search --jql "project = PI AND text ~ \"sns\" AND text ~ \"EVENT_NAME\"" --json --fields="*all" --limit 10
```

### Design & Architecture Tickets

Teams often create ADR, RFC, or design tickets when introducing new events or changing existing ones.

```bash
# ADR or design tickets mentioning an event
acli jira workitem search --jql "text ~ \"EVENT_NAME\" AND (summary ~ \"ADR\" OR summary ~ \"design\" OR summary ~ \"RFC\")" --json --fields="*all" --limit 10

# Migration or deprecation tickets
acli jira workitem search --jql "text ~ \"EVENT_NAME\" AND (summary ~ \"migration\" OR summary ~ \"deprecat\" OR summary ~ \"sunset\")" --json --fields="*all" --limit 10

# Integration work tickets
acli jira workitem search --jql "text ~ \"EVENT_NAME\" AND (summary ~ \"integration\" OR summary ~ \"consumer\" OR summary ~ \"subscribe\")" --json --fields="*all" --limit 10
```

### Team/Project-Scoped Searches

When you know the team's Jira project key, scope searches to reduce noise.

```bash
# Messaging-related tickets in a specific project
acli jira workitem search --jql "project = PROJ AND text ~ \"EVENT_NAME\"" --json --fields="*all" --limit 20

# All event/messaging tickets in a project
acli jira workitem search --jql "project = PROJ AND (text ~ \"kafka\" OR text ~ \"sns\" OR text ~ \"sqs\" OR text ~ \"rabbitmq\" OR text ~ \"event\")" --json --fields="*all" --limit 20

# Recent activity (last 30 days)
acli jira workitem search --jql "project = PROJ AND text ~ \"EVENT_NAME\" AND updated >= -30d" --json --fields="*all" --limit 20
```

### Viewing Ticket Details

After finding relevant tickets in search results, get full details:

```bash
# View a specific ticket (all fields, JSON)
acli jira workitem view KEY-123 --json --fields="*all"

# View just specific fields
acli jira workitem view KEY-123 --fields "summary,description,comment"

# Open in browser for visual inspection
acli jira workitem view KEY-123 --web
```

### Extracting Event Context from Tickets

When processing search results with `jq`, extract the most relevant fields:

```bash
# Get key, summary, status, and assignee from search results
acli jira workitem search --jql "text ~ \"EVENT_NAME\"" --json --fields="*all" --limit 20 \
  | jq '.[] | {key: .key, summary: .fields.summary, status: .fields.status.name, assignee: .fields.assignee.displayName, updated: .fields.updated}'

# Get ticket keys only (for batch processing)
acli jira workitem search --jql "text ~ \"EVENT_NAME\"" --json --fields="*all" --limit 20 \
  | jq -r '.[].key'
```

## Confluence Search (confluence-cli)

### Full-Text Search

`confluence search` performs full-text search across all pages. It is **case-insensitive** by default.

```bash
# Search for pages mentioning an event name
confluence search "EVENT_NAME" --limit 10

# Search for architecture documentation
confluence search "EVENT_NAME architecture" --limit 5
confluence search "EVENT_NAME design" --limit 5
confluence search "EVENT_NAME consumer" --limit 5

# Search for event catalogs or registries
confluence search "event catalog" --limit 5
confluence search "topic registry" --limit 5
confluence search "event schema registry" --limit 5

# Search for messaging platform docs
confluence search "kafka topics EVENT_NAME" --limit 5
confluence search "sns sqs EVENT_NAME" --limit 5
```

### Find by Title

`confluence find` searches by page title, optionally scoped to a Confluence space.

```bash
# Find pages with the event name in the title
confluence find "EVENT_NAME"

# Find in a specific team's Confluence space
confluence find "EVENT_NAME" --space TEAM_SPACE

# Find architecture decision records
confluence find "ADR" --space TEAM_SPACE
confluence find "event architecture" --space TEAM_SPACE
```

### Reading Page Content

Once you find a relevant page, read its content:

```bash
# Read page in markdown format (best for processing)
confluence read PAGE_ID --format markdown

# Read page as plain text
confluence read PAGE_ID --format text

# Read page as HTML (preserves all formatting)
confluence read PAGE_ID --format html

# Get page metadata (title, space, status)
confluence info PAGE_ID

# List child pages (for finding sub-pages under an architecture doc)
confluence children PAGE_ID --recursive --max-depth 2
```

### Reading by URL

If you find a Confluence URL in a Jira ticket or another page:

```bash
# Read directly by URL
confluence read "https://justeattakeaway.atlassian.net/wiki/viewpage.action?pageId=123456789" --format markdown
```

### Space Exploration

When you know a team's Confluence space, explore it for event-related documentation:

```bash
# Find event-related pages in a space
confluence find "events" --space TEAM_SPACE
confluence find "messaging" --space TEAM_SPACE
confluence find "kafka" --space TEAM_SPACE
confluence find "integration" --space TEAM_SPACE

# List all children of a known architecture parent page
confluence children PARENT_PAGE_ID --recursive --format tree
```

## Investigation Patterns

### Pattern 1: Event Discovery via PI Tickets

PI tickets are one of the best sources for understanding which services interact with an event, because root cause analysis sections name specific producers, consumers, and failure points.

```bash
# 1. Search for PIs mentioning the event
acli jira workitem search --jql "project = PI AND text ~ \"EVENT_NAME\"" --json --fields="*all" --limit 10

# 2. For each PI, read the full details to extract service names
acli jira workitem view PI-12345 --json --fields="*all"

# 3. The description and comments typically mention:
#    - Which service failed (consumer or producer)
#    - What the impact was (which downstream services were affected)
#    - The fix (which often reveals the event flow)
```

### Pattern 2: Cross-Reference Jira <-> Confluence

Jira tickets often link to Confluence design docs, and vice versa. Follow these links:

```bash
# 1. Find a relevant ticket
acli jira workitem search --jql "text ~ \"EVENT_NAME\" AND summary ~ \"design\"" --json --fields="*all" --limit 5

# 2. View it to find Confluence links in description/comments
acli jira workitem view KEY-123 --json --fields="*all"
# Look for URLs matching justeattakeaway.atlassian.net/wiki/...

# 3. Read the linked Confluence page
confluence read PAGE_ID --format markdown
```

### Pattern 3: Migration/Deprecation Tracking

When investigating whether an event is still active or being replaced:

```bash
# Find deprecation/migration tickets
acli jira workitem search --jql "text ~ \"EVENT_NAME\" AND (summary ~ \"deprecat\" OR summary ~ \"migrat\" OR summary ~ \"sunset\" OR summary ~ \"replace\")" --json --fields="*all" --limit 10

# Search Confluence for migration plans
confluence search "EVENT_NAME migration" --limit 5
confluence search "EVENT_NAME deprecated" --limit 5
```

## Case Sensitivity

- **Jira JQL `text ~`**: Case-insensitive by default. `text ~ "MyEvent"` matches `myevent`, `MYEVENT`, etc. However, JQL text search tokenizes on word boundaries, so `MyEvent` may match differently than `my-event`. Search for both naming variants separately.
- **Confluence search**: Case-insensitive by default for full-text search.
- **Confluence find**: Case-insensitive by default for title search.
- **jq post-processing**: Use `test("pattern"; "i")` for case-insensitive filtering of JSON results.

## Gotchas

- **JQL text search tokenization**: JQL `text ~ "EVENT_NAME"` may not match if the term appears as part of a larger token (e.g., inside a URL or code block). Consider searching for shorter substrings if needed.
- **Confluence search is not CQL**: `confluence search` takes plain text, not Confluence Query Language. There is no CQL support in `confluence-cli`.
- **Rate limits**: Both Jira and Confluence APIs have rate limits. Use `--limit` to control result counts and avoid excessive pagination.
- **acli has no user lookup**: You cannot look up user profiles or creation dates via `acli jira`. If you need to find a person, use Backstage people search instead.
- **Large result sets**: Use `--limit` and time-based JQL filters (`created >= -90d`, `updated >= -30d`) to keep result sets manageable.
- **Pagination**: For large result sets, use `acli jira workitem search ... --paginate` to get all results, or `--limit N` to cap.
