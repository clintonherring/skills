# acli - Atlassian CLI Reference

Command-line interface for Jira Cloud.

**Note**: For Confluence operations, use [confluence-cli](confluence-cli.md) instead.

## Installation

**macOS/Linux:**
```bash
brew tap atlassian/acli
brew install acli
```

**Windows:** See [Atlassian CLI Windows install guide](https://developer.atlassian.com/cloud/acli/guides/install-windows/)

## Authentication

```bash
acli auth          # Authenticate to Atlassian
acli jira auth     # Authenticate for Jira
```

## Default Output Flags

**ALWAYS** include these flags on all work-item read operations:

```bash
--json --fields="*all"
```

This ensures:
- Output is structured JSON (easier to parse and process)
- All fields are returned, including custom fields that are often excluded by default but frequently needed

Applies to:
- `acli jira workitem view` — viewing a specific ticket
- `acli jira workitem search` — searching/querying tickets via JQL or filter
- `acli jira workitem comment list` — listing comments on a ticket

## Jira Commands

### Work Items (Issues)

#### View Work Item
```bash
# Primary (with all fields including custom fields)
acli jira workitem view KEY-123 --json --fields="*all"

# Alternative formats
acli jira workitem view KEY-123                            # Plain text
acli jira workitem view KEY-123 --fields summary,comment   # Specific fields only
acli jira workitem view KEY-123 --web                      # Open in browser
```

#### Create Work Item
```bash
# Basic creation
acli jira workitem create --summary "Task title" --project "PROJ" --type "Task"

# With description and assignee
acli jira workitem create \
  --summary "Fix login bug" \
  --project "PROJ" \
  --type "Bug" \
  --assignee "user@company.com" \
  --description "Description here"

# Self-assign with @me
acli jira workitem create --summary "My task" --project "PROJ" --type "Task" --assignee "@me"

# With labels
acli jira workitem create --summary "Task" --project "PROJ" --type "Task" --label "bug,urgent"

# From file
acli jira workitem create --from-file "workitem.txt" --project "PROJ" --type "Task"

# Using editor
acli jira workitem create --project "PROJ" --type "Task" --editor
```

**Flags:**
- `-s, --summary` - Work item title
- `-p, --project` - Project key (e.g., PROJ, TEAM)
- `-t, --type` - Type: Epic, Story, Task, Bug
- `-a, --assignee` - Email, account ID, `@me`, or `default`
- `-d, --description` - Description text or ADF
- `-l, --label` - Comma-separated labels
- `--parent` - Parent work item ID (for subtasks)
- `-e, --editor` - Open text editor

#### Search Work Items
```bash
# Primary (with all fields including custom fields)
acli jira workitem search --jql "project = PROJ" --json --fields="*all"
acli jira workitem search --jql "project = PROJ AND status = 'In Progress'" --json --fields="*all"
acli jira workitem search --jql "assignee = currentUser()" --json --fields="*all"

# Alternative formats
acli jira workitem search --jql "project = PROJ"                              # Plain text
acli jira workitem search --jql "project = PROJ" --fields "key,summary"       # Specific fields only

# CSV export (with all fields)
acli jira workitem search --jql "project = PROJ" --csv --json --fields="*all"

# Count only (with all fields)
acli jira workitem search --jql "project = PROJ" --count --json --fields="*all"

# Pagination
acli jira workitem search --jql "project = PROJ" --json --fields="*all" --paginate
acli jira workitem search --jql "project = PROJ" --json --fields="*all" --limit 50

# Using saved filter
acli jira workitem search --filter 10001 --json --fields="*all"
```

#### Edit Work Item
```bash
# Edit by key
acli jira workitem edit --key "KEY-123" --summary "New Summary"
acli jira workitem edit --key "KEY-1,KEY-2" --assignee "user@company.com"

# Edit by JQL
acli jira workitem edit --jql "project = PROJ" --assignee "@me"

# Multiple edits
acli jira workitem edit --key "KEY-123" \
  --summary "Updated title" \
  --description "Updated description" \
  --labels "new-label"

# Remove assignee
acli jira workitem edit --key "KEY-123" --remove-assignee

# Skip confirmation
acli jira workitem edit --key "KEY-123" --summary "New" --yes
```

#### Transition Work Item
```bash
# Change status
acli jira workitem transition --key "KEY-123" --status "Done"
acli jira workitem transition --key "KEY-123" --status "In Progress"

# Bulk transition
acli jira workitem transition --jql "project = PROJ" --status "Done" --yes
```

#### Comments

**Plain text comments** (use `acli`):
```bash
# Add comment
acli jira workitem comment create --key "KEY-123" --body "Comment text"

# Comment from file
acli jira workitem comment create --key "KEY-123" --body-file "comment.txt"

# Using editor
acli jira workitem comment create --key "KEY-123" --editor

# List comments
acli jira workitem comment list KEY-123 --json --fields="*all"

# Update last comment
acli jira workitem comment create --key "KEY-123" --body "Updated" --edit-last
```

**Formatted comments** (use `jira-comment.sh`):

> **WARNING**: `acli comment create --body/--body-file` silently strips ADF inline
> marks (bold, italic, code, links) and rejects `heading` nodes with `INVALID_INPUT`.
> Despite the flag description claiming ADF support, only structural nodes like
> `bulletList` survive — text marks are lost. Use the helper script for formatted
> comments. See [../scripts/jira-comment.sh](../scripts/jira-comment.sh).

```bash
# Formatted comment from ADF JSON file
scripts/jira-comment.sh KEY-123 /tmp/comment.json

# Formatted comment with inline ADF
scripts/jira-comment.sh KEY-123 --body '{"type":"doc","version":1,"content":[...]}'
```

#### Other Operations
```bash
# Assign
acli jira workitem assign --key "KEY-123" --assignee "user@company.com"

# Clone
acli jira workitem clone KEY-123

# Delete
acli jira workitem delete KEY-123

# Archive/Unarchive
acli jira workitem archive KEY-123
acli jira workitem unarchive KEY-123

# Link work items
acli jira workitem link KEY-123 KEY-456

# Attachments
acli jira workitem attachment add --key "KEY-123" --file "doc.pdf"
```

### Sprints

```bash
# View sprint
acli jira sprint view SPRINT-ID

# List work items in sprint
acli jira sprint list-workitems SPRINT-ID

# Create sprint
acli jira sprint create --name "Sprint 1" --board BOARD-ID

# Update sprint
acli jira sprint update SPRINT-ID --name "New Name"
```

### Boards

```bash
# Search boards
acli jira board search
acli jira board search --name "Team Board"

# Get board details
acli jira board get BOARD-ID

# List sprints on board
acli jira board list-sprints BOARD-ID

# List projects on board
acli jira board list-projects BOARD-ID
```

### Projects

```bash
# List projects
acli jira project list

# View project
acli jira project view PROJ

# Create project
acli jira project create --key "NEW" --name "New Project"
```

### Filters

```bash
# List filters
acli jira filter list

# View filter
acli jira filter view FILTER-ID
```

## Common JQL Queries

```bash
# My open issues
acli jira workitem search --jql "assignee = currentUser() AND status != Done" --json --fields="*all"

# Issues created this week
acli jira workitem search --jql "project = PROJ AND created >= startOfWeek()" --json --fields="*all"

# High priority bugs
acli jira workitem search --jql "project = PROJ AND type = Bug AND priority = High" --json --fields="*all"

# Issues updated recently
acli jira workitem search --jql "project = PROJ AND updated >= -7d" --json --fields="*all"

# Unassigned issues
acli jira workitem search --jql "project = PROJ AND assignee IS EMPTY" --json --fields="*all"

# Issues in current sprint
acli jira workitem search --jql "project = PROJ AND sprint in openSprints()" --json --fields="*all"
```

## Output Formats

**Default for work-item operations**: Always use `--json --fields="*all"` on read operations (`view`, `search`, `comment list`) to ensure all fields including custom fields are returned.

Available output flags:
- `--json` - JSON output (for programmatic use)
- `--csv` - CSV output (for spreadsheets)
- `--web` - Open in web browser
- `--fields` - Select specific fields to display (use `"*all"` to include custom fields)

## Atlassian Document Format (ADF)

> **Scope**: The `--from-json` flag and ADF workflow below apply to **descriptions only**
> (via `workitem create` and `workitem edit`). The `comment create` command does NOT
> support `--from-json`. For formatted comments, use
> [scripts/jira-comment.sh](../scripts/jira-comment.sh) instead.

The `--description` flag only supports plain text. For rich formatting (headings, lists, code blocks), use `--from-json` with ADF.

### JSON Wrapper Structure

```json
{
  "issues": ["KEY-123"],
  "description": {
    "type": "doc",
    "version": 1,
    "content": [ ...nodes... ]
  }
}
```

Generate a starter template with:
```bash
acli jira workitem edit --generate-json
```

### Node Types

| Node | Purpose | Key attrs |
|------|---------|-----------|
| `heading` | Section heading | `attrs.level`: 1-6 |
| `paragraph` | Text container | — |
| `bulletList` | Unordered list | children: `listItem` |
| `orderedList` | Numbered list | `attrs.order`: start number, children: `listItem` |
| `listItem` | List entry | must wrap content in `paragraph` |
| `codeBlock` | Code block | `attrs.language` (optional) |

### Text Marks

| Mark | Renders as | Attrs |
|------|-----------|-------|
| `code` | `inline code` | — |
| `link` | hyperlink | `attrs.href` |
| `strong` | **bold** | — |
| `em` | *italic* | — |

Marks are applied to text nodes via `"marks": [{ "type": "<mark>", "attrs": {...} }]`.

### Complete Example

```json
{
  "issues": ["PROJ-123"],
  "description": {
    "type": "doc",
    "version": 1,
    "content": [
      {
        "type": "heading",
        "attrs": { "level": 2 },
        "content": [{ "type": "text", "text": "Summary" }]
      },
      {
        "type": "paragraph",
        "content": [
          { "type": "text", "text": "See " },
          { "type": "text", "text": "PR #100", "marks": [{ "type": "link", "attrs": { "href": "https://github.je-labs.com/org/repo/pull/100" } }] },
          { "type": "text", "text": " for the " },
          { "type": "text", "text": "feature-x", "marks": [{ "type": "code" }] },
          { "type": "text", "text": " implementation." }
        ]
      },
      {
        "type": "orderedList",
        "attrs": { "order": 1 },
        "content": [
          { "type": "listItem", "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "First step" }] }] },
          { "type": "listItem", "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Second step" }] }] },
          { "type": "listItem", "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Third step" }] }] }
        ]
      },
      {
        "type": "bulletList",
        "content": [
          { "type": "listItem", "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Item A" }] }] },
          { "type": "listItem", "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Item B" }] }] },
          { "type": "listItem", "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Item C" }] }] }
        ]
      },
      {
        "type": "codeBlock",
        "attrs": { "language": "bash" },
        "content": [{ "type": "text", "text": "echo 'hello world'" }]
      }
    ]
  }
}
```

### Usage

Use `--from-json` with `--yes` to skip confirmation:
```bash
acli jira workitem edit --from-json description.json --yes
acli jira workitem create --from-json workitem.json
```
