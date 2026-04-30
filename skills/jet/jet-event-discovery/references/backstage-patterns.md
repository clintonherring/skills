# Backstage Lookup Patterns for Event-Driven Discovery

Patterns for using the Backstage API to find services, APIs, teams, and event contracts.

## Case Sensitivity

- **Backstage search API**: The `term` query parameter is **case-insensitive by default**. A search for `myevent` matches `MyEvent` in titles, descriptions, and text.
- **jq `test()` function**: When filtering results locally with jq, use the `"i"` flag for case-insensitive regex matching: `test("pattern"; "i")`. Without the flag, `test()` is case-sensitive.
- **jq `contains()`**: This is always case-sensitive. Prefer `test("pattern"; "i")` over `contains("Pattern")` for filtering results.

## Prerequisites

You need `$BACKSTAGE_API_KEY` set. See the [jet-company-standards backstage reference](/Users/biagio.capece/.agents/skills/jet-company-standards/references/backstage.md) for setup instructions.

**Base URLs:**
- UI: `https://backstage.eu-west-1.production.jet-internal.com/`
- API: `https://backstagebackend.eu-west-1.production.jet-internal.com`

---

## Finding Services That Use Messaging

### Search for components with messaging-related terms

```bash
# Search for services related to "kafka"
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "https://backstagebackend.eu-west-1.production.jet-internal.com/api/search/query?term=kafka&types%5B0%5D=software-catalog" \
  | jq '.results[] | select(.document.kind == "Component") | {name: .document.title, owner: .document.owner, lifecycle: .document.lifecycle, url: "https://backstage.eu-west-1.production.jet-internal.com\(.document.location)"}'

# Search for services related to "events"
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "https://backstagebackend.eu-west-1.production.jet-internal.com/api/search/query?term=events&types%5B0%5D=software-catalog" \
  | jq '.results[] | select(.document.kind == "Component") | {name: .document.title, owner: .document.owner, lifecycle: .document.lifecycle}'

# Search for services related to "messaging" or "queue"
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "https://backstagebackend.eu-west-1.production.jet-internal.com/api/search/query?term=messaging&types%5B0%5D=software-catalog" \
  | jq '.results[] | select(.document.kind == "Component") | {name: .document.title, owner: .document.owner}'
```

### Find AsyncAPI definitions (event contracts)

AsyncAPI specs define the contract for event-driven APIs -- which topics a service publishes to or subscribes from.

```bash
# Search for APIs (includes AsyncAPI, OpenAPI, GraphQL)
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "https://backstagebackend.eu-west-1.production.jet-internal.com/api/search/query?term=SEARCH_TERM&types%5B0%5D=software-catalog" \
  | jq '.results[] | select(.document.kind == "API") | {name: .document.title, type: .document.componentType, owner: .document.owner, url: "https://backstage.eu-west-1.production.jet-internal.com\(.document.location)"}'

# Search specifically for "asyncapi"
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "https://backstagebackend.eu-west-1.production.jet-internal.com/api/search/query?term=asyncapi&types%5B0%5D=software-catalog" \
  | jq '.results[] | {name: .document.title, kind: .document.kind, type: .document.componentType, owner: .document.owner}'
```

## Finding Service Owners

When you've identified a producer/consumer from GitHub code search, look up who owns it:

```bash
# Find the owner of a specific service
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "https://backstagebackend.eu-west-1.production.jet-internal.com/api/search/query?term=SERVICE_NAME&types%5B0%5D=software-catalog" \
  | jq '.results[] | select(.document.kind == "Component" and (.document.title | test("SERVICE_NAME"; "i"))) | {name: .document.title, owner: .document.owner, lifecycle: .document.lifecycle}'
```

## Finding All Services for a Team

When the user asks "what messaging does team X use?", start by finding all their services:

```bash
# Find all components owned by a team
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "https://backstagebackend.eu-west-1.production.jet-internal.com/api/search/query?term=TEAM_NAME&types%5B0%5D=software-catalog" \
  | jq '.results[] | select(.document.kind == "Component" and (.document.owner | test("TEAM_NAME"; "i"))) | {name: .document.title, lifecycle: .document.lifecycle, type: .document.componentType}'
```

## Finding Documentation About Event-Driven Systems

```bash
# Search TechDocs for event-driven documentation
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "https://backstagebackend.eu-west-1.production.jet-internal.com/api/search/query?term=kafka&types%5B0%5D=techdocs" \
  | jq '.results[:10][] | {title: .document.title, url: "https://backstage.eu-west-1.production.jet-internal.com\(.document.location)", preview: (.document.text[:150] + "...")}'

# Search for event schema documentation
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "https://backstagebackend.eu-west-1.production.jet-internal.com/api/search/query?term=event+schema&types%5B0%5D=techdocs" \
  | jq '.results[:10][] | {title: .document.title, url: "https://backstage.eu-west-1.production.jet-internal.com\(.document.location)"}'
```

## Finding Systems (Groups of Related Services)

Systems in Backstage represent a collection of services that work together. Useful for finding all services in a domain:

```bash
# Find systems
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "https://backstagebackend.eu-west-1.production.jet-internal.com/api/search/query?term=DOMAIN_TERM&types%5B0%5D=software-catalog" \
  | jq '.results[] | select(.document.kind == "System") | {name: .document.title, owner: .document.owner, url: "https://backstage.eu-west-1.production.jet-internal.com\(.document.location)"}'
```

## Pagination

Backstage returns 25 results per page. For thorough searches, paginate:

```bash
# First page
RESPONSE=$(curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "https://backstagebackend.eu-west-1.production.jet-internal.com/api/search/query?term=kafka&types%5B0%5D=software-catalog")

# Get cursor for next page
CURSOR=$(echo "$RESPONSE" | jq -r '.nextPageCursor')

# Fetch next page if cursor exists
if [ "$CURSOR" != "null" ]; then
  curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
    "https://backstagebackend.eu-west-1.production.jet-internal.com/api/search/query?term=kafka&types%5B0%5D=software-catalog&pageCursor=$CURSOR"
fi
```

## Tips

- **Truncate text fields**: Always use jq to exclude or truncate `.document.text` -- it can be very long and flood your terminal.
- **Combine with GitHub search**: Use Backstage to find the repo, then `gh search code` to find the messaging code within that repo.
- **Check lifecycle**: Filter by `.document.lifecycle == "production"` to focus on live services.
- **AsyncAPI is gold**: If a service has an AsyncAPI spec registered, it's the most reliable source of truth for what it produces and consumes.
