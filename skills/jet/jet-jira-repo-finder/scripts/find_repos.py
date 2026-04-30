#!/usr/bin/env python3
"""
Finds all portfolio children of a given Jira entity (epic, initiative, theme, etc.),
then searches GitHub Enterprise for PRs whose title starts with each child ticket key.
Outputs the unique repositories those PRs belong to.

Usage:
    python find_repos.py <JIRA_KEY> [--ghe-hostname <hostname>] [--output <file.json>]

Examples:
    python find_repos.py EPF-8501
    python find_repos.py COE-123 --output coe123_repos.json
    python find_repos.py TIG-400 --ghe-hostname github.je-labs.com
"""

import subprocess
import json
import time
import sys
import os
import argparse
from datetime import datetime

GHE_HOSTNAME = "github.je-labs.com"


def log(msg, logf=None):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    if logf:
        logf.write(line + "\n")
        logf.flush()


def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(cmd)}\nSTDERR: {result.stderr.strip()}"
        )
    return result.stdout


def fetch_jira_children(parent_key, logf=None):
    """
    Fetch all portfolio children of parent_key using portfolioChildIssuesOf.
    Uses acli's --paginate flag to retrieve the full result set in one call.
    """
    cmd = [
        "acli",
        "jira",
        "workitem",
        "search",
        "--jql",
        f"issuekey in portfolioChildIssuesOf('{parent_key}')",
        "--json",
        "--fields=key,summary",
        "--paginate",
    ]
    log(f"Fetching all portfolio children of {parent_key}...", logf)
    log(f"Running: {' '.join(cmd)}", logf)
    raw = run(cmd)
    issues = json.loads(raw)
    keys = [issue["key"] for issue in issues]
    log(f"Found {len(keys)} children of {parent_key}", logf)
    return keys


def search_prs_for_key(ticket_key, hostname, logf=None):
    """
    Search GHE for PRs whose title starts with ticket_key.
    Paginates through all result pages (100 per page).
    Returns list of dicts with ticket, repo, pr_number, title, state.
    """
    matches = []
    page = 1

    while True:
        url = f"/search/issues?q=is:pr+{ticket_key}+in:title&per_page=100&page={page}"
        cmd = ["gh", "api", "--hostname", hostname, url]
        try:
            raw = run(cmd)
        except RuntimeError as e:
            log(f"  ERROR searching PRs for {ticket_key}: {e}", logf)
            break

        data = json.loads(raw)
        items = data.get("items", [])
        total = data.get("total_count", 0)

        for item in items:
            title = item["title"].strip()
            # Only keep PRs whose title starts with the ticket key (case-insensitive)
            if title.upper().startswith(ticket_key.upper()):
                repo_url = item["repository_url"]
                # URL format: https://<hostname>/api/v3/repos/ORG/REPO
                repo = repo_url.split("/repos/", 1)[-1]
                matches.append(
                    {
                        "ticket": ticket_key,
                        "repo": repo,
                        "pr_number": item["number"],
                        "title": title,
                        "state": item["state"],
                    }
                )

        if page * 100 >= total or len(items) == 0:
            break
        page += 1
        time.sleep(0.2)  # be kind to the API

    return matches


def main():
    parser = argparse.ArgumentParser(
        description="Find all GitHub repos touched by PRs linked to children of a Jira entity."
    )
    parser.add_argument("jira_key", help="Parent Jira ticket key (e.g. EPF-8501)")
    parser.add_argument(
        "--ghe-hostname",
        default=GHE_HOSTNAME,
        help=f"GitHub Enterprise hostname (default: {GHE_HOSTNAME})",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional path to write the JSON summary (default: <jira_key>_pr_repos.json in CWD)",
    )
    args = parser.parse_args()

    parent_key = args.jira_key.upper()
    hostname = args.ghe_hostname
    output_file = args.output or f"{parent_key.lower().replace('-', '')}_pr_repos.json"
    log_file = output_file.replace(".json", ".log")

    with open(log_file, "w") as logf:
        log(f"=== Jira Repo Finder: {parent_key} ===", logf)
        log(f"Started at {datetime.now().isoformat()}", logf)
        log(f"GHE hostname: {hostname}", logf)
        log(f"Log file: {log_file}", logf)
        log("", logf)

        # Step 1: fetch all portfolio children via Jira
        log(f"Step 1: Fetching all portfolio children of {parent_key}...", logf)
        try:
            child_keys = fetch_jira_children(parent_key, logf)
        except RuntimeError as e:
            log(f"FATAL: Could not fetch Jira children: {e}", logf)
            sys.exit(1)

        log(f"Children: {child_keys}", logf)
        log("", logf)

        if not child_keys:
            log("No children found. Nothing to search for.", logf)
            print(f"\nNo children found under {parent_key}.")
            return

        # Step 2: search GitHub for PRs per child ticket
        log(
            f"Step 2: Searching GHE ({hostname}) for PRs for each child ticket...", logf
        )
        all_prs = []
        repos_set = set()

        for i, key in enumerate(child_keys):
            log(f"  [{i + 1}/{len(child_keys)}] Searching PRs for {key}...", logf)
            prs = search_prs_for_key(key, hostname, logf)
            if prs:
                for pr in prs:
                    log(
                        f"    MATCH: [{pr['state']}] {pr['repo']}#{pr['pr_number']} — {pr['title']}",
                        logf,
                    )
                    repos_set.add(pr["repo"])
                all_prs.extend(prs)
            else:
                log(f"    No matching PRs found.", logf)
            time.sleep(0.15)  # gentle rate limiting

        log("", logf)

        # Step 3: summarise
        log("=== RESULTS ===", logf)
        log(f"Total PRs matched: {len(all_prs)}", logf)
        log(f"Unique repositories ({len(repos_set)}):", logf)
        for repo in sorted(repos_set):
            log(f"  - {repo}", logf)

        log("", logf)
        log("=== FULL PR LIST ===", logf)
        for pr in all_prs:
            log(
                f"  {pr['ticket']}  [{pr['state']}]  {pr['repo']}#{pr['pr_number']}  |  {pr['title']}",
                logf,
            )

        log("", logf)
        log(f"Finished at {datetime.now().isoformat()}", logf)

        # Write JSON summary
        summary = {
            "parent": parent_key,
            "child_count": len(child_keys),
            "children": child_keys,
            "pr_count": len(all_prs),
            "unique_repos": sorted(repos_set),
            "prs": all_prs,
        }
        with open(output_file, "w") as jf:
            json.dump(summary, jf, indent=2)
        log(f"JSON summary written to: {output_file}", logf)

    # Final console output
    print(f"\n=== UNIQUE REPOSITORIES for {parent_key} ===")
    for repo in sorted(repos_set):
        print(f"  {repo}")
    print(f"\nTotal: {len(repos_set)} unique repos across {len(all_prs)} PRs")
    print(f"Full log: {log_file}")
    print(f"JSON summary: {output_file}")


if __name__ == "__main__":
    main()
