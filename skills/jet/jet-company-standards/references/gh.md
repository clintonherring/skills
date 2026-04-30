# gh - GitHub CLI Reference

Command-line interface for GitHub. At JET, use with GitHub Enterprise at `github.je-labs.com`.

## Authentication

```bash
gh auth login                    # Interactive login
gh auth login --hostname github.je-labs.com  # Login to JET GitHub Enterprise
gh auth status                   # Check auth status
gh auth refresh -s project       # Add project scope for PR projects
```

## Pull Requests

### Create PR
```bash
# Basic creation
gh pr create --title "PROJ-123: Add feature" --body "Description"

# With reviewers and labels
gh pr create \
  --title "PROJ-123: Fix bug" \
  --body "Fixes the login issue" \
  --reviewer "username,team-name" \
  --label "bug"

# Auto-fill from commits
gh pr create --fill

# Draft PR
gh pr create --title "WIP: Feature" --draft

# Specify base branch
gh pr create --base develop --title "Feature"

# Open in browser to create
gh pr create --web
```

**Flags:**
- `-t, --title` - PR title
- `-b, --body` - PR description
- `-B, --base` - Target branch (default: repo default)
- `-H, --head` - Source branch (default: current)
- `-r, --reviewer` - Request reviewers (comma-separated)
- `-a, --assignee` - Assign users (`@me` for self)
- `-l, --label` - Add labels
- `-p, --project` - Add to project
- `-m, --milestone` - Add to milestone
- `-d, --draft` - Create as draft
- `-f, --fill` - Use commit info for title/body
- `-w, --web` - Open browser

### View PR
```bash
gh pr view                       # View PR for current branch
gh pr view 123                   # View PR by number
gh pr view --web                 # Open in browser
gh pr view --json title,state    # JSON output
gh pr view --comments            # Include comments
```

### List PRs
```bash
gh pr list                       # List open PRs
gh pr list --state all           # All PRs
gh pr list --state merged        # Merged PRs
gh pr list --author "@me"        # Your PRs
gh pr list --assignee "@me"      # Assigned to you
gh pr list --label "bug"         # By label
gh pr list --search "review:required"  # Search query
gh pr list --json number,title   # JSON output
```

### PR Actions
```bash
# Checkout PR locally
gh pr checkout 123

# Check CI status
gh pr checks 123

# Merge PR
gh pr merge 123
gh pr merge 123 --squash
gh pr merge 123 --rebase
gh pr merge 123 --merge          # Create merge commit

# Close/Reopen
gh pr close 123
gh pr reopen 123

# Mark ready for review
gh pr ready 123

# Add comment
gh pr comment 123 --body "LGTM!"

# Request review
gh pr edit 123 --add-reviewer "username"

# Add labels
gh pr edit 123 --add-label "approved"

# View diff
gh pr diff 123
```

### PR Review
```bash
gh pr review 123 --approve
gh pr review 123 --request-changes --body "Please fix X"
gh pr review 123 --comment --body "Looks good overall"
```

## Issues

### Create Issue
```bash
gh issue create --title "Bug report" --body "Description"
gh issue create --label "bug,urgent"
gh issue create --assignee "@me"
gh issue create --web              # Open browser
```

### View/List Issues
```bash
gh issue view 123
gh issue view 123 --web
gh issue list
gh issue list --assignee "@me"
gh issue list --label "bug"
gh issue list --state closed
```

### Issue Actions
```bash
gh issue close 123
gh issue reopen 123
gh issue comment 123 --body "Comment"
gh issue edit 123 --title "New title"
gh issue edit 123 --add-label "priority"
```

## Repositories

### Clone/Create
```bash
gh repo clone owner/repo
gh repo clone owner/repo -- --depth 1  # Shallow clone
gh repo create my-repo --private
gh repo fork owner/repo
```

### View
```bash
gh repo view                     # Current repo
gh repo view owner/repo
gh repo view --web               # Open in browser
```

### List
```bash
gh repo list                     # Your repos
gh repo list org-name            # Org repos
gh repo list --limit 50
```

## GitHub API

Direct API access for advanced operations:

```bash
# GET request
gh api repos/{owner}/{repo}
gh api repos/{owner}/{repo}/pulls

# POST request
gh api repos/{owner}/{repo}/issues -f title="Bug" -f body="Description"

# With pagination
gh api repos/{owner}/{repo}/issues --paginate

# JSON filtering
gh api repos/{owner}/{repo}/pulls --jq '.[].title'

# PR comments
gh api repos/{owner}/{repo}/pulls/123/comments

# PR reviews
gh api repos/{owner}/{repo}/pulls/123/reviews
```

## Workflow Runs (GitHub Actions)

```bash
gh run list                      # List recent runs
gh run view RUN-ID               # View run details
gh run watch RUN-ID              # Watch run progress
gh run rerun RUN-ID              # Rerun workflow
gh run download RUN-ID           # Download artifacts
```

## Search

```bash
# Search repos
gh search repos "language:python stars:>100"

# Search issues/PRs
gh search issues "is:open label:bug"
gh search prs "is:open review:required"

# Search code
gh search code "function login"
```

## Working with JET GitHub Enterprise

Always specify the hostname for JET repos:

```bash
# Set default host
gh config set -h github.je-labs.com git_protocol ssh

# Clone from JET
gh repo clone github.je-labs.com/org/repo

# Specify repo explicitly
gh pr list -R github.je-labs.com/org/repo
gh issue list -R github.je-labs.com/org/repo
```

## Common Workflows

### Create PR with Jira Link
```bash
gh pr create \
  --title "PROJ-123: Implement feature" \
  --body "## Summary
Implements the feature described in PROJ-123.

## Changes
- Added new endpoint
- Updated tests

## Jira
https://justeattakeaway.atlassian.net/browse/PROJ-123"
```

### Check PR Status
```bash
gh pr status                     # Status of relevant PRs
gh pr checks                     # CI checks for current PR
```

### Review Workflow
```bash
gh pr checkout 123               # Checkout PR
gh pr diff                       # View changes
gh pr review --approve           # Approve
gh pr merge --squash             # Merge with squash
```
