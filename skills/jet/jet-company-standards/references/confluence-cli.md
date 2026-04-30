# confluence-cli - Confluence CLI Reference

Command-line interface for Atlassian Confluence. This is the recommended tool for Confluence operations at JET.

**Repository**: https://github.com/pchuri/confluence-cli

## Installation

```bash
npm install -g confluence-cli
```

Or run directly with npx:
```bash
npx confluence-cli
```

## Configuration

### Option 1: Interactive Setup

```bash
confluence init
```

The wizard helps you choose the right API endpoint and authentication method.

### Option 2: Environment Variables

```bash
export CONFLUENCE_DOMAIN="justeattakeaway.atlassian.net"
export CONFLUENCE_API_TOKEN="your-api-token"
export CONFLUENCE_EMAIL="your.email@justeattakeaway.com"
export CONFLUENCE_API_PATH="/wiki/rest/api"  # Cloud default
export CONFLUENCE_AUTH_TYPE="basic"
```

### Getting Your API Token

1. Go to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click "Create API token"
3. Give it a label (e.g., "confluence-cli")
4. Copy the generated token

## Commands

### List Spaces

```bash
confluence spaces
```

### Read a Page

```bash
# Read by page ID (text format)
confluence read 123456789

# Read in markdown format
confluence read 123456789 --format markdown

# Read in HTML format
confluence read 123456789 --format html

# Read by URL
confluence read "https://justeattakeaway.atlassian.net/wiki/viewpage.action?pageId=123456789"
```

**Flags:**
- `-f, --format <format>` - Output format: `html`, `text`, `markdown` (default: `text`)

### Get Page Information

```bash
confluence info 123456789
```

Returns: Title, ID, Type, Status, Space

### Search Pages

```bash
# Basic search
confluence search "search term"

# Limit results
confluence search "API documentation" --limit 5
```

**Flags:**
- `-l, --limit <limit>` - Limit number of results (default: 10)

### Find Page by Title

```bash
# Find page by title
confluence find "Project Documentation"

# Find in a specific space
confluence find "Getting Started" --space MYTEAM
```

**Flags:**
- `-s, --space <spaceKey>` - Limit search to specific space

### List Child Pages

```bash
# List direct child pages
confluence children 123456789

# List all descendants recursively
confluence children 123456789 --recursive

# Display as tree structure
confluence children 123456789 --recursive --format tree

# Show page IDs and URLs
confluence children 123456789 --show-id --show-url

# Limit recursion depth
confluence children 123456789 --recursive --max-depth 3

# Output as JSON for scripting
confluence children 123456789 --recursive --format json > children.json
```

**Flags:**
- `-r, --recursive` - List all descendants recursively
- `--max-depth <number>` - Maximum depth for recursive listing (default: 10)
- `--format <format>` - Output format: `list`, `tree`, `json` (default: `list`)
- `--show-url` - Show page URLs
- `--show-id` - Show page IDs

### Create a Page

```bash
# Create with inline content (markdown format)
confluence create "My New Page" SPACEKEY --content "**Hello** World!" --format markdown

# Create from a file
confluence create "Documentation" SPACEKEY --file ./content.md --format markdown

# Create with HTML content
confluence create "HTML Page" SPACEKEY --content "<p>Hello</p>" --format html
```

**Flags:**
- `-c, --content <content>` - Page content as string
- `-f, --file <file>` - Read content from file
- `--format <format>` - Content format: `storage`, `html`, `markdown` (default: `storage`)

### Create a Child Page

```bash
# Create child page with inline content
confluence create-child "Meeting Notes" 123456789 --content "This is a child page"

# Create child page from a file
confluence create-child "Tech Specs" 123456789 --file ./specs.md --format markdown
```

**Flags:**
- Same as `create` command

### Update a Page

```bash
# Update title only
confluence update 123456789 --title "New Title"

# Update content only
confluence update 123456789 --content "Updated page content."

# Update content from a file
confluence update 123456789 --file ./updated-content.md --format markdown

# Update both title and content
confluence update 123456789 --title "New Title" --content "And new content"
```

**Flags:**
- `-t, --title <title>` - New page title
- `-c, --content <content>` - Page content as string
- `-f, --file <file>` - Read content from file
- `--format <format>` - Content format: `storage`, `html`, `markdown` (default: `storage`)

### Delete a Page

```bash
# Delete by page ID (prompts for confirmation)
confluence delete 123456789

# Delete by URL
confluence delete "https://justeattakeaway.atlassian.net/wiki/viewpage.action?pageId=123456789"

# Skip confirmation (useful for scripts)
confluence delete 123456789 --yes
```

**Flags:**
- `--yes` - Skip confirmation prompt

### Edit Workflow

Export page content for editing, then re-import:

```bash
# 1. Export page content to a file (in Confluence storage format)
confluence edit 123456789 --output ./page-to-edit.xml

# 2. Edit the file with your preferred editor
vim ./page-to-edit.xml

# 3. Update the page with your changes
confluence update 123456789 --file ./page-to-edit.xml --format storage
```

### List/Download Attachments

```bash
# List all attachments on a page
confluence attachments 123456789

# Filter by filename
confluence attachments 123456789 --pattern "*.png"

# Limit the number returned
confluence attachments 123456789 --limit 5

# Download matching attachments to a directory
confluence attachments 123456789 --pattern "*.png" --download --dest ./downloads
```

**Flags:**
- `-l, --limit <limit>` - Maximum number of attachments to fetch
- `-p, --pattern <glob>` - Filter attachments by filename (e.g., `*.png`)
- `-d, --download` - Download matching attachments
- `--dest <directory>` - Directory to save downloads (default: current directory)

### Export a Page with Attachments

```bash
# Export page content (markdown by default) and all attachments
confluence export 123456789 --dest ./exports

# Custom content format and filename
confluence export 123456789 --format html --file content.html

# Filter attachments
confluence export 123456789 --pattern "*.png"

# Skip attachments (content only)
confluence export 123456789 --skip-attachments

# Only download attachments referenced in page content
confluence export 123456789 --referenced-only
```

**Flags:**
- `--format <format>` - Content format: `html`, `text`, `markdown` (default: `markdown`)
- `--dest <directory>` - Base directory to export into (default: `.`)
- `--file <filename>` - Content filename (default: `page.<ext>`)
- `--attachments-dir <name>` - Subdirectory for attachments (default: `attachments`)
- `--pattern <glob>` - Filter attachments by filename
- `--referenced-only` - Download only attachments referenced in the page content
- `--skip-attachments` - Do not download attachments

### Copy Page Tree

```bash
# Copy a page and all its children to a new location
confluence copy-tree 123456789 987654321 "Project Docs (Copy)"

# Copy with maximum depth limit
confluence copy-tree 123456789 987654321 --max-depth 3

# Exclude pages by title (supports wildcards)
confluence copy-tree 123456789 987654321 --exclude "temp*,test*,*draft*"

# Dry run (preview only)
confluence copy-tree 123456789 987654321 --dry-run

# Control pacing and naming
confluence copy-tree 123456789 987654321 --delay-ms 150 --copy-suffix " (Backup)"
```

**Flags:**
- `--max-depth <number>` - Maximum depth for copying
- `--exclude <patterns>` - Exclude pages by title (supports wildcards `*` and `?`)
- `--delay-ms <ms>` - Delay between page creations to avoid rate limits
- `--copy-suffix <text>` - Suffix for root page title (default: `(Copy)`)
- `--dry-run` - Preview only, don't actually copy
- `--fail-on-error` - Exit non-zero if any page fails to copy
- `--quiet` - Suppress progress output

### View Usage Statistics

```bash
confluence stats
```

## Common Workflows

### Find and Read a Page

```bash
# Find page by title to get its ID
confluence find "Project Documentation" --space MYTEAM

# Read the page content
confluence read 8449754017 --format markdown
```

### Create Documentation Structure

```bash
# Create a parent page
confluence create "Project Documentation" MYSPACE --content "# Project Docs" --format markdown

# Note the page ID from output, then create child pages
confluence create-child "Getting Started" 123456789 --file ./getting-started.md --format markdown
confluence create-child "API Reference" 123456789 --file ./api-reference.md --format markdown
```

### Backup a Page with Attachments

```bash
# Export page and all attachments
confluence export 123456789 --dest ./backup --format markdown
```

### Update Page from Markdown File

```bash
confluence update 123456789 --file ./updated-docs.md --format markdown
```
