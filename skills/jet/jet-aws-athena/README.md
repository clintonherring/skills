# AWS Athena CLI Skill

This skill enables running SQL queries against AWS Athena, exploring databases and table schemas, and retrieving query results using the AWS CLI.

## Installation

```bash
npx skills add git@github.je-labs.com:ai-platform/skills.git
```

## Prerequisites

### Required Tools

| Tool | Purpose | Installation (MacOS/Linux) | Installation (Windows PowerShell) |
|------|---------|----------------------------|------------------------|
| `aws` | AWS CLI v2 | `brew install awscli` | `winget install Amazon.AWSCLI` |
| `jq` | JSON processing | `brew install jq` | `winget install jqlang.jq` |

### Authentication Setup

```bash
# Login via SSO (most common at JET)
aws sso login --profile <profile-name>

# Set the profile for the session
export AWS_PROFILE=<profile-name>
```

Ensure the IAM identity has permissions for `athena:*` and read/write access to the query results S3 bucket.

## Usage

Once installed, the skill is automatically triggered when you:

- Ask to run a SQL query against Athena
- Want to explore Athena databases, tables, or schemas
- Need to check query execution status or fetch results
- Reference AWS Athena or querying data in S3

## Skill Contents

| File | Description |
|------|-------------|
| `SKILL.md` | Main skill instructions, workflows, and best practices |
| `scripts/athena_query.sh` | Bash helper functions for Athena operations (query, explore, poll) |
