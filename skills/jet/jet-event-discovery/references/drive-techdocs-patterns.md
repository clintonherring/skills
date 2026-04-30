# Google Drive & Backstage TechDocs Patterns

Search patterns for discovering event-driven architecture documentation in Google Drive spreadsheets and Backstage TechDocs pages.

## Case Sensitivity

- **sheets-cli `sheets find --name`**: Search is **case-insensitive by default**. A search for `kafka topics` matches `Kafka Topics`, `KAFKA TOPICS`, etc.
- **Backstage TechDocs search**: The `term` parameter is **case-insensitive by default**. Searching for `myevent` matches content containing `MyEvent`.
- **jq filtering on results**: When using jq `test()` to filter locally, always include the `"i"` flag: `test("pattern"; "i")`.

## Google Drive (sheets-cli)

`sheets-cli sheets find` searches Google Drive for spreadsheets by name. It only returns Google Sheets -- not Docs, Slides, or other file types. Returns spreadsheet ID, name, and URL.

### Search Patterns

**Event-driven architecture spreadsheets:**

```bash
# Topic registries / catalogs
sheets-cli sheets find --name "kafka topics"
sheets-cli sheets find --name "topic registry"
sheets-cli sheets find --name "event catalog"
sheets-cli sheets find --name "event registry"

# Schema / contract docs
sheets-cli sheets find --name "message schema"
sheets-cli sheets find --name "event schema"
sheets-cli sheets find --name "async api"
sheets-cli sheets find --name "event contract"

# Integration and architecture
sheets-cli sheets find --name "integration matrix"
sheets-cli sheets find --name "event-driven"
sheets-cli sheets find --name "async messaging"
sheets-cli sheets find --name "service dependencies"
sheets-cli sheets find --name "message flow"

# Platform-specific
sheets-cli sheets find --name "kafka"
sheets-cli sheets find --name "sns sqs"
sheets-cli sheets find --name "rabbitmq"
sheets-cli sheets find --name "redpanda"
```

**By service or team name:**

```bash
sheets-cli sheets find --name "SERVICE_NAME"
sheets-cli sheets find --name "SERVICE_NAME events"
sheets-cli sheets find --name "SERVICE_NAME topics"
sheets-cli sheets find --name "TEAM_NAME"
sheets-cli sheets find --name "TEAM_NAME messaging"
```

**By topic name:**

```bash
sheets-cli sheets find --name "TOPIC_NAME"
```

### Reading Spreadsheet Data

Once you find a relevant spreadsheet, use these commands to read its contents:

```bash
# List all tabs/sheets in the spreadsheet
sheets-cli sheets list --spreadsheet SPREADSHEET_ID

# Get the header row to understand the structure
sheets-cli header --spreadsheet SPREADSHEET_ID --sheet "Sheet1"

# Read table data (limited to 50 rows for safety)
sheets-cli table read --spreadsheet SPREADSHEET_ID --sheet "Sheet1" --limit 50

# Read specific rows by key value
sheets-cli table read --spreadsheet SPREADSHEET_ID --sheet "Sheet1" --key "Topic Name" --value "order-events"
```

### Tips

- Search terms are matched against the spreadsheet **name only**, not content. Teams may name spreadsheets generically (e.g., "Architecture Overview") so try multiple search terms.
- Use `--limit 10` to cap results if you get too many matches.
- If a spreadsheet has multiple tabs, list them first with `sheets list` and then read the most relevant tab.
- Common spreadsheet structures for topic registries: columns like "Topic Name", "Producer", "Consumer", "Owner Team", "Schema", "Environment".

## Backstage TechDocs

TechDocs are technical documentation pages published by teams to Backstage. They often contain architecture docs, design decisions (ADRs), runbooks, and event contracts.

### Search Patterns

**Base URL:** `https://backstagebackend.eu-west-1.production.jet-internal.com/api/search/query`
**Browsable URL prefix:** `https://backstage.eu-west-1.production.jet-internal.com`

Always include `types%5B0%5D=techdocs` to filter for documentation only.

**Event-driven architecture docs:**

```bash
# General event-driven docs
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "https://backstagebackend.eu-west-1.production.jet-internal.com/api/search/query?term=kafka+topics&types%5B0%5D=techdocs" \
  | jq '.results[:10][] | {title: .document.title, owner: .document.owner, url: "https://backstage.eu-west-1.production.jet-internal.com\(.document.location)", preview: (.document.text[:150] + "...")}'

# Event schema / contract docs
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "https://backstagebackend.eu-west-1.production.jet-internal.com/api/search/query?term=event+schema&types%5B0%5D=techdocs" \
  | jq '.results[:10][] | {title: .document.title, owner: .document.owner, url: "https://backstage.eu-west-1.production.jet-internal.com\(.document.location)"}'

# AsyncAPI definitions
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "https://backstagebackend.eu-west-1.production.jet-internal.com/api/search/query?term=asyncapi&types%5B0%5D=techdocs" \
  | jq '.results[:10][] | {title: .document.title, owner: .document.owner, url: "https://backstage.eu-west-1.production.jet-internal.com\(.document.location)"}'

# Message broker docs
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "https://backstagebackend.eu-west-1.production.jet-internal.com/api/search/query?term=message+broker&types%5B0%5D=techdocs" \
  | jq '.results[:10][] | {title: .document.title, owner: .document.owner, url: "https://backstage.eu-west-1.production.jet-internal.com\(.document.location)"}'
```

**By specific topic or service:**

```bash
# Search for a specific topic name in TechDocs
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "https://backstagebackend.eu-west-1.production.jet-internal.com/api/search/query?term=TOPIC_NAME&types%5B0%5D=techdocs" \
  | jq '.results[:5][] | {title: .document.title, owner: .document.owner, url: "https://backstage.eu-west-1.production.jet-internal.com\(.document.location)", preview: (.document.text[:150] + "...")}'

# Search for a specific service's event documentation
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "https://backstagebackend.eu-west-1.production.jet-internal.com/api/search/query?term=SERVICE_NAME+events&types%5B0%5D=techdocs" \
  | jq '.results[:5][] | {title: .document.title, owner: .document.owner, url: "https://backstage.eu-west-1.production.jet-internal.com\(.document.location)"}'
```

**Architecture decision records (ADRs):**

```bash
# ADRs about messaging decisions
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "https://backstagebackend.eu-west-1.production.jet-internal.com/api/search/query?term=adr+kafka&types%5B0%5D=techdocs" \
  | jq '.results[:5][] | {title: .document.title, owner: .document.owner, url: "https://backstage.eu-west-1.production.jet-internal.com\(.document.location)"}'

curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "https://backstagebackend.eu-west-1.production.jet-internal.com/api/search/query?term=adr+event-driven&types%5B0%5D=techdocs" \
  | jq '.results[:5][] | {title: .document.title, owner: .document.owner, url: "https://backstage.eu-west-1.production.jet-internal.com\(.document.location)"}'
```

**Runbooks for messaging infrastructure:**

```bash
# Runbooks for Kafka issues
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "https://backstagebackend.eu-west-1.production.jet-internal.com/api/search/query?term=runbook+kafka&types%5B0%5D=techdocs" \
  | jq '.results[:5][] | {title: .document.title, owner: .document.owner, url: "https://backstage.eu-west-1.production.jet-internal.com\(.document.location)"}'

# Runbooks for SQS/SNS
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "https://backstagebackend.eu-west-1.production.jet-internal.com/api/search/query?term=runbook+sqs&types%5B0%5D=techdocs" \
  | jq '.results[:5][] | {title: .document.title, owner: .document.owner, url: "https://backstage.eu-west-1.production.jet-internal.com\(.document.location)"}'
```

### Combined Search (TechDocs + Catalog)

When you want both documentation and service metadata in one query:

```bash
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "https://backstagebackend.eu-west-1.production.jet-internal.com/api/search/query?term=SEARCH_TERM&types%5B0%5D=techdocs&types%5B1%5D=software-catalog" \
  | jq '.results[] | {type: .type, title: .document.title, owner: .document.owner, url: "https://backstage.eu-west-1.production.jet-internal.com\(.document.location)"}'
```

### Pagination

TechDocs results are paginated (25 per page). Use `nextPageCursor` for more results:

```bash
RESPONSE=$(curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "https://backstagebackend.eu-west-1.production.jet-internal.com/api/search/query?term=kafka&types%5B0%5D=techdocs")

# Check if there are more pages
CURSOR=$(echo "$RESPONSE" | jq -r '.nextPageCursor')
if [ "$CURSOR" != "null" ]; then
  curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
    "https://backstagebackend.eu-west-1.production.jet-internal.com/api/search/query?term=kafka&types%5B0%5D=techdocs&pageCursor=$CURSOR" \
    | jq '.results[:10][] | {title: .document.title, owner: .document.owner}'
fi
```

### TechDocs Response Structure

```json
{
  "type": "techdocs",
  "document": {
    "kind": "group|component",
    "name": "component-name",
    "title": "Page Title",
    "text": "Full document content (can be very long!)...",
    "location": "/docs/default/group/team-name/path/to/page/",
    "owner": "team-name"
  }
}
```

### Tips

- **Always truncate `document.text`** -- it contains the full page content and can be thousands of characters. Use `.document.text[:150]` in jq for previews.
- Construct browsable URLs by prepending `https://backstage.eu-west-1.production.jet-internal.com` to the `location` field.
- TechDocs search is full-text -- it searches both the title and the body content of documentation pages.
- Results are paginated at 25 per page. Use `nextPageCursor` if you need more results.
- Not all teams publish TechDocs. If you find nothing, fall back to code search and Datadog.
- TechDocs content may be outdated. Cross-reference findings with code search and runtime data.
