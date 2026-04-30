# PlatformMetadata API Reference

Central registry for finding JET applications, services, and components.

## Repository

| Resource | URL |
|----------|-----|
| PlatformMetadata | https://github.je-labs.com/metadata/PlatformMetadata |

## Repository Structure

```
Data/
├── global_features/     # Application/service definitions
├── projects/            # Project-level metadata
├── teams/               # Team definitions
├── aws_accounts/        # AWS account mappings
├── environments/        # Environment configurations
└── ...
```

## Finding Components

Component metadata is stored in `Data/global_features/`:

```bash
# Search for a component
gh api --hostname github.je-labs.com "/search/code?q=COMPONENT_NAME+repo:metadata/PlatformMetadata"

# Get a component's metadata file
gh api --hostname github.je-labs.com /repos/metadata/PlatformMetadata/contents/Data/global_features/COMPONENT_NAME.json | jq -r '.content' | base64 -d
```

### Component Metadata Structure

```json
{
  "id": "component-name",
  "description": "Description of the component",
  "owners": "team-name",
  "github_repository": {
    "owner": "org-name",
    "name": "repo-name"
  },
  "tier": 1,
  "lifecycle": {
    "status": "production"
  },
  "run_book_path": "/path/to/RUNBOOK.md"
}
```

### Example: Find and Clone a Component

```bash
# 1. Find the component metadata
gh api --hostname github.je-labs.com /repos/metadata/PlatformMetadata/contents/Data/global_features/helixapi.json | jq -r '.content' | base64 -d

# Output shows: "github_repository": { "owner": "ai-platform", "name": "helixapi" }

# 2. Clone the repository
gh repo clone github.je-labs.com/ai-platform/helixapi
```

## Fetching Team Metadata

Team metadata is stored in `Data/teams/`, and a team's metadata can be fetched using the following command:

``` bash
gh api --hostname github.je-labs.com /repos/metadata/PlatformMetadata/contents/Data/teams/TEAM_NAME.json | jq -r '.content' | base64 -d
```

The team metadata structure will look something like this:

``` json
{
  "id": "team-name",
  "sid": "short-team-name",
  "department": "department-name",
  "sub_department": "sub-department-name",
  "description": "A brief description for the team.",
  "jira_project_id": "jira-project-id",
  "tech_manager": "tech-manager-name",
  "jira_team_owner": "jira-team",
  "lead_engineer": "staff-engineer-name",
  "pagerduty_schedule_key": "pagerduty-key",
  "pagerduty_escalation_policy_key": "pagerduty-key",
  "pagerduty_emergency_service_key": "pagerduty-key",
  "primary_github_orgs": [
    "github-org"
  ],
  "engineers": [
    "engineer-name",
    "another-engineer-name",
    "and-another-engineer-name"
  ],
  "slack_channel_name": "slack-channel-name",
  "slack_channel_name_for_scorecard": "slack-channel-name",
  "slack_channel_names_for_monitoring": {
    "*": "slack-channel-name"
  },
  "slack_channel_names_for_sonic_pipeline": {
    "default": "slack-channel-name"
  },
  "slack_channel_names_for_pipeline": {
    "*": "slack-channel-name"
  }
}
```

## Fetching Environment Metadata Structure

Environment metadata is stored in `Data/environments/`, and a environment's metadata can be fetched using the following command:

``` bash
gh api --hostname github.je-labs.com /repos/metadata/PlatformMetadata/contents/Data/environment/ENVIRONMENT_NAME.json | jq -r '.content' | base64 -d
```

The environment metadata structure will look something like this:

``` json
{
  "bulkhead": "bulkhead",
  "aws_account_alias": "aws-account-name",
  "id": "environment-name",
  "alias": "environment-alias",
  "dns_account": "dns-aws-account-name",
  "hosted_zone": "pdv-2.eu-west-1.qa.jet-internal.com",
  "ingress_account": "eu-west-1-ing-qa-1",
  "team": "owning-team",
  "owner": "owning-team",
  "env_type": "environment-type",
  "aws_region": "aws-region",
  "tags": [
    "tag",
    "another-tag",
    "and-another-tag"
  ],
  "isProduction": false,
  "isStaging": false,
  "platform": "jet",
  "confluent_cluster_alias": "confluent-cluster-name",
  "sid": "environment-short-name",
  "disaster_recovery": {
    "role": "source",
    "secure_env": "environment-name"
  },
  "oidc_issuer_uri": "oidc.environment.issuer.com/path",
  "lifecycle": {
    "status": "production",
    "dueDateForNextStatus": "2026-07-01",
    "explanation": "To Be Defined"
  }
}
```

## AWS Account Metadata Structure

AWS account metadata is stored in `Data/aws_accounts/`, and an AWS account's metadata can be fetched using the following command:

``` bash
gh api --hostname github.je-labs.com /repos/metadata/PlatformMetadata/contents/Data/environment/AWS_ACCOUNT_NAME.json | jq -r '.content' | base64 -d
```

The AWS account metadata structure will look something like this:

``` json
{
  "id": "aws-account-name",
  "account_number": "aws-account-name",
  "is_part_of_core_platform": true,
  "administrator": "administrator-team",
  "administrator_email_address": "administrator@justeattakeaway.com",
  "consolidated_billing_account_number": "billing-aws-account-name",
  "account_groups": [
    "account-group",
    "another-account-group"
  ]
}
```
