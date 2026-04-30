# Backstage API Reference

Search for internal documentation (TechDocs), components, APIs, teams, and people.

## URLs

| Resource | URL |
|----------|-----|
| Backstage UI | https://backstage.eu-west-1.production.jet-internal.com/ |
| Backstage API | https://backstagebackend.eu-west-1.production.jet-internal.com |

## Authentication

All API requests require the `Authorization: Bearer $BACKSTAGE_API_KEY` header.

### Getting a Token

**Option 1: @backstage/cli (recommended)**

Use `@backstage/cli` to authenticate via Okta SSO and retrieve a token:

```bash
# One-time login (opens browser for Okta SSO)
npx @backstage/cli auth login --backend-url https://backstagebackend.eu-west-1.production.jet-internal.com

# Set the token for API calls (add to ~/.zshrc or ~/.bashrc for persistence)
export BACKSTAGE_API_KEY="$(npx @backstage/cli auth print-token)"
```

**Option 2: Service Account Token (longer-lived)**
- Contact DevEx to request a longer-lived service account token for automation

### Verifying Authentication

Test that your token is working:

```bash
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "https://backstagebackend.eu-west-1.production.jet-internal.com/api/search/query?term=test" \
  | jq '.results | length'
```

If this returns a number (e.g., `25`), authentication is working. If you get an error, your token may have expired — re-run `export BACKSTAGE_API_KEY="$(npx @backstage/cli auth print-token)"` to refresh it.

## Search API

**Endpoint:** `GET /api/search/query`

### Query Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `term` | Search term (URL encoded) | `term=kubernetes` |
| `types[0]` | Filter by type | `types%5B0%5D=techdocs` |
| `pageCursor` | Pagination cursor | `pageCursor=MQ==` |

### Search Types

| Type | Description | Example Location |
|------|-------------|------------------|
| `techdocs` | Technical documentation pages | `/docs/default/component/myapp/...` |
| `software-catalog` | Components, APIs, Groups, Users, Systems | `/catalog/default/component/myapp` |

### Software Catalog Kinds

When searching `software-catalog`, filter results by `document.kind`:

| Kind | Description |
|------|-------------|
| `Component` | Services, libraries, websites |
| `API` | OpenAPI, AsyncAPI, GraphQL APIs |
| `Group` | Teams |
| `User` | People |
| `System` | Collection of components |
| `Concept` | Documentation concepts |

## Basic Search Examples

```bash
# Search all types (default)
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "https://backstagebackend.eu-west-1.production.jet-internal.com/api/search/query?term=YOUR_SEARCH_TERM"

# Search only TechDocs (documentation)
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "https://backstagebackend.eu-west-1.production.jet-internal.com/api/search/query?term=YOUR_SEARCH_TERM&types%5B0%5D=techdocs"

# Search only Software Catalog (components, APIs, teams, users)
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "https://backstagebackend.eu-west-1.production.jet-internal.com/api/search/query?term=YOUR_SEARCH_TERM&types%5B0%5D=software-catalog"

# Search multiple types
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "https://backstagebackend.eu-west-1.production.jet-internal.com/api/search/query?term=YOUR_SEARCH_TERM&types%5B0%5D=techdocs&types%5B1%5D=software-catalog"
```

## Pagination

Results are paginated (25 per page). Use `nextPageCursor` to fetch more results:

```bash
# First page
RESPONSE=$(curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "https://backstagebackend.eu-west-1.production.jet-internal.com/api/search/query?term=kubernetes")

# Get cursor for next page
CURSOR=$(echo "$RESPONSE" | jq -r '.nextPageCursor')

# Fetch next page (if cursor is not null)
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "https://backstagebackend.eu-west-1.production.jet-internal.com/api/search/query?term=kubernetes&pageCursor=$CURSOR"
```

## Response Structure

### TechDocs Result

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

### Software Catalog Result

```json
{
  "type": "software-catalog",
  "document": {
    "kind": "Component|API|Group|User",
    "title": "my-service",
    "text": "Service description...",
    "location": "/catalog/default/component/my-service",
    "owner": "group:default/my-team",
    "lifecycle": "production",
    "componentType": "service"
  }
}
```

## jq Snippets

**IMPORTANT:** Always exclude or truncate `document.text` to avoid flooding the terminal with long content.

### Search Documentation

```bash
# List top 5 doc titles and URLs (no text)
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "https://backstagebackend.eu-west-1.production.jet-internal.com/api/search/query?term=helm&types%5B0%5D=techdocs" \
  | jq -r '.results[:5][] | "\(.document.title): https://backstage.eu-west-1.production.jet-internal.com\(.document.location)"'

# Search TechDocs with truncated preview (100 chars)
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "https://backstagebackend.eu-west-1.production.jet-internal.com/api/search/query?term=YOUR_TERM&types%5B0%5D=techdocs" \
  | jq '.results[:5][] | {title: .document.title, url: "https://backstage.eu-west-1.production.jet-internal.com\(.document.location)", preview: (.document.text[:100] + "...")}'
```

### Find Components

```bash
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "https://backstagebackend.eu-west-1.production.jet-internal.com/api/search/query?term=order-api&types%5B0%5D=software-catalog" \
  | jq '.results[] | select(.document.kind == "Component") | {title: .document.title, owner: .document.owner, lifecycle: .document.lifecycle, url: "https://backstage.eu-west-1.production.jet-internal.com\(.document.location)"}'
```

### Find APIs

```bash
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "https://backstagebackend.eu-west-1.production.jet-internal.com/api/search/query?term=payments&types%5B0%5D=software-catalog" \
  | jq '.results[] | select(.document.kind == "API") | {title: .document.title, type: .document.componentType, url: "https://backstage.eu-west-1.production.jet-internal.com\(.document.location)"}'
```

### Find Teams/Groups

```bash
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "https://backstagebackend.eu-west-1.production.jet-internal.com/api/search/query?term=ai-platform&types%5B0%5D=software-catalog" \
  | jq '.results[] | select(.document.kind == "Group") | {name: .document.title, url: "https://backstage.eu-west-1.production.jet-internal.com\(.document.location)"}'
```

### Find People/Users

```bash
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "https://backstagebackend.eu-west-1.production.jet-internal.com/api/search/query?term=john.smith&types%5B0%5D=software-catalog" \
  | jq '.results[] | select(.document.kind == "User") | {name: .document.title, url: "https://backstage.eu-west-1.production.jet-internal.com\(.document.location)"}'
```

### Find Systems

```bash
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "https://backstagebackend.eu-west-1.production.jet-internal.com/api/search/query?term=platform&types%5B0%5D=software-catalog" \
  | jq '.results[] | select(.document.kind == "System") | {name: .document.title, type: .document.componentType, url: "https://backstage.eu-west-1.production.jet-internal.com\(.document.location)"}'
```

### Read Full Document Text

```bash
# Read full text of first result (when needed)
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "https://backstagebackend.eu-west-1.production.jet-internal.com/api/search/query?term=YOUR_TERM&types%5B0%5D=techdocs" \
  | jq -r '.results[0].document.text'
```

## View in Browser

Construct the full URL by combining the base URL with the location:

| Resource | URL Pattern |
|----------|-------------|
| TechDocs | `https://backstage.eu-west-1.production.jet-internal.com/docs/default/component/myapp/` |
| Component | `https://backstage.eu-west-1.production.jet-internal.com/catalog/default/component/myapp` |
| Team | `https://backstage.eu-west-1.production.jet-internal.com/catalog/default/group/team-name` |
| User | `https://backstage.eu-west-1.production.jet-internal.com/catalog/default/user/john.smith` |
