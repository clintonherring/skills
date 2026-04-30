---
name: jet-company-standards
description: JET (Just Eat Takeaway) company development standards, internal documentation, and resources. Use this skill when working on JET projects, searching for internal documentation, or looking up JET-specific terms, services, APIs, teams, or people. Triggers include any Jira operation, use of acli, gh, or aws, questions about JET conventions, commit formats, finding documentation about any internal topic (e.g. "how do I deploy to EKS", "what is OneEKS", "find docs about helm charts"), looking up components/services/APIs, finding teams or people (e.g. "who owns this service", "find the ai-platform team", "look up john.smith"), or accessing JET resources like GitHub Enterprise, Jira, Confluence, Backstage, or PlatformMetadata. Also use when the user asks to search for, find, or look up any internal JET documentation, runbooks, guides, teams, people, or how-to information.
metadata:
  owner: ai-platform
---

# JET Company Standards

Standards and conventions for Just Eat Takeaway development.

## Commit Message Format

All commits MUST include a Jira ticket ID prefix. The separator between the ticket ID and description varies by repository — some use a colon (`:`) and some do not.

### Detecting the repo convention

Before making the first commit in a repository, run:

```bash
git log --oneline -20
```

Examine the output to determine which format the repository uses:

- **With colon**: `PROJ-123: Description`
- **Without colon**: `PROJ-123 Description`

**Decision rules:**
1. If all or most commits use one format, follow that format.
2. If usage is clearly mixed (roughly even split), ask the user which format to use.
3. If there is no git history (new repo), default to `PROJ-123: Description`.

### Requirements

- **Jira ticket ID prefix**: Required for all commits (e.g. `PLAT-456`, `DATA-789`)
- **Description**: Brief description of changes in imperative mood

### Examples

With colon:
- `PLAT-456: Add user authentication endpoint`
- `DATA-789: Fix null pointer in payment processing`

Without colon:
- `PLAT-456 Add user authentication endpoint`
- `DATA-789 Fix null pointer in payment processing`

## Authentication Policy (applies to ALL tools)

**CRITICAL**: When any tool or API call fails due to authentication (401, 403, "not logged in", expired token, missing credentials, etc.), you MUST:

1. **Stop immediately** -- do not attempt to work around the authentication failure.
2. **Tell the user** that authentication is required/expired for the specific tool.
3. **Provide the exact commands** the user needs to run to authenticate.
4. **Wait for user confirmation** that they have authenticated before retrying.

**Never** try alternative approaches, skip the failing step, or use cached/stale data to avoid authentication. Always surface auth issues to the user promptly.

## Company Tools

### acli (Atlassian CLI)
Use for Jira operations. See [references/acli.md](references/acli.md) for full command reference.

**Installation (macOS/Linux):**
```bash
brew tap atlassian/acli
brew install acli
```

**Installation (Windows):** See [internal Atlassian install docs](https://developer.atlassian.com/cloud/jira/software/acli/)

Common Jira operations:
```bash
# View issue
acli jira workitem view PROJ-123 --json --fields="*all"

# Create issue
acli jira workitem create --summary "Title" --project "PROJ" --type "Task"

# Search issues
acli jira workitem search --jql "project = PROJ AND assignee = currentUser()" --json --fields="*all"

# Transition issue
acli jira workitem transition --key "PROJ-123" --status "Done"

# Add comment
acli jira workitem comment create --key "PROJ-123" --body "Comment"
```

#### Jira Formatting

**CRITICAL**: Markdown (`## Heading`, `**bold**`) and Jira Server wiki markup (`h2. Heading`, `*bold*`) will both appear as **literal unrendered text** in Jira Cloud. Rich formatting requires Atlassian Document Format (ADF).

##### Formatted Descriptions (via acli)

Use `--from-json` with ADF for formatted descriptions on `workitem create` and `workitem edit`:

```bash
# Create: write ADF to file, then create
acli jira workitem create --from-json /tmp/workitem.json

# Edit: write ADF to file, then edit
acli jira workitem edit --from-json /tmp/description.json --yes
```

The JSON file must have this structure:
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
        "content": [{ "type": "text", "text": "Section Title" }]
      },
      {
        "type": "paragraph",
        "content": [
          { "type": "text", "text": "Regular text, " },
          { "type": "text", "text": "bold text", "marks": [{ "type": "strong" }] },
          { "type": "text", "text": ", and " },
          { "type": "text", "text": "code", "marks": [{ "type": "code" }] }
        ]
      },
      {
        "type": "bulletList",
        "content": [
          { "type": "listItem", "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Item one" }] }] },
          { "type": "listItem", "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Item two" }] }] }
        ]
      }
    ]
  }
}
```

For `create`, replace `"issues"` with the required fields (`"project"`, `"summary"`, `"type"`). See [references/acli.md](references/acli.md) for the complete ADF node type reference.

##### Plain Text Comments (via acli)

For simple comments without formatting, use `acli` directly:

```bash
acli jira workitem comment create --key "PROJ-123" --body "Plain text comment"
```

##### Formatted Comments (via jira-comment.sh)

**WARNING**: `acli comment create --body/--body-file` silently strips ADF text marks (bold, italic, code, links) and rejects heading nodes. Do NOT use `acli` for formatted comments.

Use the [scripts/jira-comment.sh](scripts/jira-comment.sh) helper script instead, which posts ADF directly to the Jira REST API v3:

```bash
# From a JSON file
scripts/jira-comment.sh PROJ-123 /tmp/comment.json

# Inline ADF
scripts/jira-comment.sh PROJ-123 --body '{"type":"doc","version":1,"content":[...]}'
```

The ADF JSON file for comments uses the raw ADF document (no wrapper):
```json
{
  "type": "doc",
  "version": 1,
  "content": [
    {
      "type": "heading",
      "attrs": { "level": 2 },
      "content": [{ "type": "text", "text": "Section Title" }]
    },
    {
      "type": "paragraph",
      "content": [
        { "type": "text", "text": "This is " },
        { "type": "text", "text": "bold", "marks": [{ "type": "strong" }] },
        { "type": "text", "text": " and " },
        { "type": "text", "text": "italic", "marks": [{ "type": "em" }] }
      ]
    }
  ]
}
```

### confluence-cli (Confluence CLI)
Use for Confluence operations. See [references/confluence-cli.md](references/confluence-cli.md) for full command reference.

**Installation:**
```bash
npm install -g confluence-cli
```

Common Confluence operations:
```bash
# List spaces
confluence spaces

# Read a page
confluence read 123456789 --format markdown

# Search pages
confluence search "search term" --limit 10

# Find page by title
confluence find "Project Documentation" --space MYTEAM

# Get page info
confluence info 123456789

# Create a page
confluence create "My Page" SPACEKEY --file content.md --format markdown

# Update a page
confluence update 123456789 --file updated.md --format markdown

# List child pages
confluence children 123456789 --recursive --format tree

# Export page with attachments
confluence export 123456789 --dest ./backup
```

### gh (GitHub CLI)
Use for GitHub operations on JET GitHub Enterprise. See [references/gh.md](references/gh.md) for full command reference.

**IMPORTANT**: The `gh auth switch` command does NOT affect all gh commands. Many commands like `gh search repos` always default to github.com regardless of the active account.

For reliable GitHub Enterprise operations, use one of these approaches:

1. **Use `gh api --hostname` for searches** (recommended for searching):
```bash
# Search for repositories on GHE
gh api --hostname github.je-labs.com /search/repositories -X GET -f q="repo-name"

# Get repository info
gh api --hostname github.je-labs.com /repos/org/repo-name
```

2. **Use `-R` flag with full repo path** for repo-specific commands:
```bash
# Clone from GHE
gh repo clone github.je-labs.com/org/repo-name

# View repo on GHE
gh repo view -R github.je-labs.com/org/repo-name
```

3. **Commands that work after `gh auth switch`** (when inside a GHE repo):
```bash
# These work when you're inside a cloned GHE repository
gh pr create --title "PROJ-123: Description" --body "Details"
gh pr list --author "@me"
gh pr view 123
gh pr checkout 123
gh pr review 123 --approve
gh pr merge 123 --squash
```

If you haven't authenticated with the internal GitHub yet, run:
```bash
gh auth login --hostname github.je-labs.com
```

### aws
Use for AWS resource management.

### PlatformMetadata (Component Registry)
Use for finding component repositories. See [references/pmd.md](references/pmd.md) for full reference.

```bash
# Find a component's repository
gh api --hostname github.je-labs.com /repos/metadata/PlatformMetadata/contents/Data/global_features/COMPONENT_NAME.json | jq -r '.content' | base64 -d
```

### Backstage (Documentation & Catalog Search)
Use for searching internal documentation, components, APIs, teams, and people. See [references/backstage.md](references/backstage.md) for full API reference.

Before using the Backstage API, ensure you're authenticated:
```bash
# Login (one-time, opens browser for Okta SSO)
npx @backstage/cli auth login --backend-url https://backstagebackend.eu-west-1.production.jet-internal.com

# Set the token for API calls
export BACKSTAGE_API_KEY="$(npx @backstage/cli auth print-token)"
```

Common searches:
```bash
# Search documentation
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "https://backstagebackend.eu-west-1.production.jet-internal.com/api/search/query?term=YOUR_TERM&types%5B0%5D=techdocs" \
  | jq '.results[:5][] | {title: .document.title, url: "https://backstage.eu-west-1.production.jet-internal.com\(.document.location)", preview: (.document.text[:100] + "...")}'

# Search components, APIs, teams, users
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "https://backstagebackend.eu-west-1.production.jet-internal.com/api/search/query?term=YOUR_TERM&types%5B0%5D=software-catalog" \
  | jq '.results[:5][] | {title: .document.title, kind: .document.kind, url: "https://backstage.eu-west-1.production.jet-internal.com\(.document.location)"}'
```

## Company Resources

| Resource | URL |
|----------|-----|
| Jira | https://justeattakeaway.atlassian.net/ |
| Confluence | https://justeattakeaway.atlassian.net/wiki/ |
| GitHub Enterprise | https://github.je-labs.com/ |
| Platform Metadata | https://github.je-labs.com/metadata/PlatformMetadata |
| Backstage | https://backstage.eu-west-1.production.jet-internal.com/ |

## Helm Charts

### basic-application

The `basic-application` Helm chart is the standard chart used for deploying applications at JET.

- **Repository**: https://github.je-labs.com/helm-charts/basic-application
- **Chart reference in helmfile**: `sre/basic-application`

When migrating or upgrading basic-application versions, check the repository for:
- CHANGELOG.md for breaking changes
- Migration guides between major versions

## Platform Metadata - Finding Components

The **PlatformMetadata** repository is the central registry for all JET applications, services, and components. Use it to find where a component's source code lives.

See [references/pmd.md](references/pmd.md) for full reference.

### Quick Reference

```bash
# Find a component's repository
gh api --hostname github.je-labs.com /repos/metadata/PlatformMetadata/contents/Data/global_features/COMPONENT_NAME.json | jq -r '.content' | base64 -d

# Clone the repository (after finding the owner/name from above)
gh repo clone github.je-labs.com/ORG/REPO
```

## Working on a Jira Ticket

When given a Jira ticket to work on, follow this workflow:

### 1. Fetch the Jira ticket details
```bash
acli jira workitem view TICKET-ID --json --fields="*all"
```

### 2. Transition ticket to "In Progress"
Before starting any work, move the ticket to "In Progress" status:
```bash
acli jira workitem transition --key "TICKET-ID" --status "In Progress"
```

### 3. Identify the component/repository
If the ticket references a component (e.g., "helixapi"), **always look up its repository location** in PlatformMetadata. Never guess or assume the repository path.

```bash
# Look up the component in PlatformMetadata
gh api --hostname github.je-labs.com /repos/metadata/PlatformMetadata/contents/Data/global_features/COMPONENT_NAME.json | jq -r '.content' | base64 -d
```

This returns the repository location:
```json
{
  "github_repository": {
    "owner": "org-name",
    "name": "repo-name"
  }
}
```

### 4. Clone the repository
```bash
gh repo clone github.je-labs.com/ORG/REPO
```

### 5. Make changes and commit
Follow the repository's detected commit message format (see "Commit Message Format" section above).

### 6. Push and create a PR
Ask the user if they want to push to a feature branch and create a PR. Do not push or create PRs without explicit user confirmation. See Pull Request Workflow below.

## Workflow Guidelines

1. **Before committing**: Ensure a Jira ticket exists for the work
2. **Look up repositories**: Always use PlatformMetadata to find where a component lives - never guess
3. **Test changes locally**: Before pushing, always run available tests/linters in the repository to ensure changes work (e.g., `helmfile lint`, `npm test`, `uv run pytest`, etc.)
4. **Commit format**: Always use `TICKET-ID` prefix; detect separator convention (`: ` vs ` `) from git history (see "Commit Message Format" section)
5. **Push and PR**: Always ask the user before pushing to a feature branch or creating a pull request. Do not push or open PRs automatically.
6. **PR creation**: Link to the relevant Jira ticket in the PR description
7. **Code review**: Follow team-specific review guidelines

## Pull Request Workflow

**Important**: Always ask the user for confirmation before pushing branches or creating pull requests.

After making commits and receiving user confirmation, follow this workflow:

1. **Create a feature branch** (if not already on one):
   ```bash
   git checkout -b TICKET-ID-short-description
   ```

2. **Push to remote**:
   ```bash
   git push -u origin TICKET-ID-short-description
   ```

3. **Create PR** (use the detected commit format for the title):
   ```bash
   gh pr create --title "TICKET-ID: Description" --body "$(cat <<'EOF'
   ## Summary
   - Brief description of changes

   ## Jira
   [TICKET-ID](https://justeattakeaway.atlassian.net/browse/TICKET-ID)
   EOF
   )"
   ```

4. **Transition ticket to "Review"**:
   After creating the PR, move the Jira ticket to "Review" status:
   ```bash
   acli jira workitem transition --key "TICKET-ID" --status "Review"
   ```

**Important**: Main branches are typically protected. Always use feature branches and PRs for changes.
