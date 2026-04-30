---
name: jet-jira-repo-finder
description: |
  **What it does:** Given a Jira key, fetches all portfolio children using `portfolioChildIssuesOf` (with pagination), searches GitHub Enterprise for PRs whose title starts with each child ticket key, and returns the unique set of repositories touched by that Jira entity. Uses `acli` for Jira and `gh` for GitHub Enterprise.

  **When to use it:**
  - Someone asks which repos are involved in an epic, initiative, or theme
  - A user wants to map a Jira entity to GitHub repositories
  - A user asks "what repos does this epic touch?" or "which services are part of this initiative?"
  - A user asks to "find all repos linked to this Jira key"
  - A user needs a GitHub footprint for any Jira hierarchy node (epic, initiative, theme, or any ticket with portfolio children)
metadata:
  owner: ai-platform
---

# Jira → GitHub Repo Finder

You help users discover which GitHub repositories are involved in a Jira entity by finding all portfolio children and mapping them to PRs.

## How it works

1. Use `acli` to fetch every ticket that is a portfolio child of the given Jira key (`portfolioChildIssuesOf`).
2. For each child ticket, search GitHub Enterprise for PRs whose title starts with that ticket key.
3. Collect the unique set of repositories those PRs belong to.

The result is a list of repos that have actually had work done against this Jira entity — far more reliable than manual cross-referencing.

## Prerequisites

Both `acli` (Atlassian CLI) and `gh` (GitHub CLI, configured for `github.je-labs.com`) must be installed and authenticated.

Check before running:

```bash
command -v acli && acli jira auth 2>&1 | head -3
command -v gh && gh auth status --hostname github.je-labs.com 2>&1 | head -3
```

If `acli` is missing: `brew tap atlassian/acli && brew install acli`, then `acli jira auth`.
If `gh` is not authenticated against GHE: `gh auth login --hostname github.je-labs.com`.

## Running the script

The bundled script at `scripts/find_repos.py` handles everything: Jira pagination, GitHub PR search pagination, filtering, deduplication, and output.

**Basic usage** (writes `<key>_pr_repos.json` and `<key>_pr_repos.log` in the current directory):

```bash
python3 scripts/find_repos.py <JIRA_KEY>
```

**With options:**

```bash
python3 /path/to/scripts/find_repos.py EPF-8501 \
  --ghe-hostname github.je-labs.com \
  --output epf8501_repos.json
```

**Arguments:**

| Argument | Default | Description |
|---|---|---|
| `jira_key` | *(required)* | Parent Jira key, e.g. `EPF-8501` |
| `--ghe-hostname` | `github.je-labs.com` | GitHub Enterprise hostname |
| `--output` | `<key>_pr_repos.json` | Path for the JSON summary file |

## What to tell the user afterwards

Once the script finishes, present:

1. **The unique repository list** — sorted, one per line, in `org/repo` format.
2. **Counts** — number of child tickets searched, total PRs matched, number of unique repos.
3. **Output files** — paths to the `.json` summary and `.log` file for detailed inspection.

If the repo list is long (>15 repos), group them by GitHub org prefix to make it easier to scan.

## Interpreting results

- A ticket with **no matching PRs** doesn't necessarily mean no work was done — the developer may not have used the ticket key in the PR title, or the work may have been committed directly.
- The same repo appearing for many tickets signals it's a **core service** for this initiative.
- Repos that appear only once are likely **peripheral** (config, infra one-offs, etc.).

## Troubleshooting

| Symptom | Fix |
|---|---|
| `acli: command not found` | Install acli: `brew tap atlassian/acli && brew install acli` |
| `acli` auth error | Run `acli jira auth` and follow the prompts |
| `gh api` returns 401 | Run `gh auth login --hostname github.je-labs.com` |
| `gh api` returns empty results | The ticket key may be too short/generic — GitHub search may rate-limit or return noisy results |
| Script very slow | Normal — it makes one API call per child ticket with a 150ms delay. 100 children ≈ 3–5 minutes |
| JSON parse error from acli | Try running the `acli` command manually to inspect raw output |
