# ODL Table Schemas

All tables are in the `transformed_data` database unless noted otherwise.

## Table of Contents

- [Deployments](#deployments)
  - [all_dora_deployments](#all_dora_deployments)
  - [dora_deployments_v2](#dora_deployments_v2)
  - [dora_deployment_db_history](#dora_deployment_db_history)
- [Platform Metadata](#platform-metadata)
  - [platformmetadata_teams](#platformmetadata_teams)
  - [platformmetadata_features](#platformmetadata_features)
  - [platformmetadata_projects](#platformmetadata_projects)
  - [platformmetadata_environments](#platformmetadata_environments)
  - [platformmetadata_aws_accounts](#platformmetadata_aws_accounts)
  - [platformmetadata_departments / subdepartments](#platformmetadata_departments--subdepartments)
- [Services Metadata](#services-metadata)
  - [services_metadata_services](#services_metadata_services)
  - [services_metadata_channels](#services_metadata_channels)
  - [services_metadata_gateways](#services_metadata_gateways)
- [Security](#security)
  - [wiz_issues](#wiz_issues)
  - [wiz_vulnerabilities](#wiz_vulnerabilities)
  - [wiz_secrets / wiz_compliance_summary](#wiz_secrets--wiz_compliance_summary)
- [GitHub](#github)
  - [github_pr_logs_clean](#github_pr_logs_clean)
  - [github_git_logs](#github_git_logs)
  - [github_repo_logs](#github_repo_logs)
  - [github_business_logs](#github_business_logs)
  - [github_copilot_metrics](#github_copilot_metrics)
  - [github_copilot_seats](#github_copilot_seats)
  - [github_repo_languages / ghe_repo_languages](#github_repo_languages--ghe_repo_languages)
- [Reliability](#reliability)
  - [reliability_peak_availability_mom](#reliability_peak_availability_mom)
  - [reliability_missed_orders_wow](#reliability_missed_orders_wow)
  - [reliability_mttd_mom](#reliability_mttd_mom)
- [Cost](#cost)
  - [finout_wow_by_component](#finout_wow_by_component)
- [Audit Logs](#audit-logs)
  - [okta_logs](#okta_logs)
  - [vault_logs](#vault_logs)
  - [confluent_logs](#confluent_logs)
  - [artifactory_logs](#artifactory_logs)
  - [rdscloudwatch_logs](#rdscloudwatch_logs)
- [DORA / PMD Stats](#dora--pmd-stats)
  - [pmd_stats](#pmd_stats)

---

## Deployments

### all_dora_deployments

**The canonical deployment table.** Live data, ~6.5M records, updated continuously.

All columns are nested structs -- access via dot notation (e.g., `deployment.start_time`).

| Column | Type | Description |
|--------|------|-------------|
| `application.name` | string | Application name |
| `application.owners` | string | Owning team name |
| `environment.name` | string | Environment name (e.g., `production`, `aus-production`) |
| `environment.type` | string | Environment type: `production`, `prod`, `prd`, `staging`, `qa`, `dev`, `sandbox`, `dr` |
| `deployment.start_time` | string | ISO 8601 timestamp (e.g., `2026-02-18T12:10:09Z`) |
| `deployment.end_time` | string | ISO 8601 timestamp |
| `deployment.status` | string | `success` or `fail` |
| `deployment.app_version` | string | Application version/build number |
| `deployment.app_version_url` | string | URL to the version (e.g., Git tag) |
| `deployment.deployment_url` | string | URL to the deployment pipeline run |
| `deployment.orchestrator` | string | `concourse`, `sonic`, `github`, `jenkins`, `marathon` |
| `deployment.host_technology` | string | `eks`, `ec2`, `ecs`, `s3`, `serverless`, `gke`, `cloudrun`, etc. |
| `deployment.user` | string | User who triggered the deployment |
| `deployment.trigger` | string | What triggered the deployment |
| `deployment.tenant` | string | Tenant (often `all`) |
| `deployment.merged` | string | Merge timestamp |
| `deployment.tier` | string | Application tier |
| `deployment.orchestrator_deployment_id` | string | ID in the orchestrator system |
| `deployment.app_repository` | string | Source repository |

**Important:** `environment.type` values are inconsistent -- production is stored as `production`, `prod`, or `prd`. Always filter with `IN ('production', 'prod', 'prd')`.

**Important:** `deployment.start_time` is a string in ISO 8601 format, not a timestamp. Use string comparison for filtering (e.g., `>= '2026-02-18'`).

### dora_deployments_v2

Same structure as `all_dora_deployments` but missing `deployment.app_repository`. Prefer `all_dora_deployments`.

### dora_deployment_db_history

Historical Parquet-based table with flattened column names. Data up to March 2025 only.

| Column | Type | Description |
|--------|------|-------------|
| `application__name` | string | Application name |
| `application__owners` | string | Owning team |
| `environment__name` | string | Environment name |
| `environment__type` | string | Environment type |
| `deployment__start_time` | timestamp | Deployment start (native timestamp) |
| `deployment__end_time` | timestamp | Deployment end |
| `deployment__status` | string | `success` or `fail` |
| `deployment__app_version` | string | Version |
| `deployment__orchestrator` | string | Orchestrator |
| `deployment__user` | string | Deploying user |
| `deployment__host_technology` | string | Host technology |
| `deployment__tenant` | string | Tenant |
| `deployment__trigger` | string | Trigger |
| `deployment__tier` | smallint | Tier |
| `deployment__merged` | timestamp | Merge time |
| `deployment__deployment_url` | string | Pipeline URL |
| `deployment__app_version_url` | string | Version URL |
| `deployment__first_deployed` | timestamp | First deployment time |
| `deployment__orchestrator_deployment_id` | string | Orchestrator ID |
| `id` | string | Record ID |

---

## Platform Metadata

### platformmetadata_teams

Team directory with ownership and contact information.

| Column | Type | Description |
|--------|------|-------------|
| `id` | string | Team identifier (e.g., `ai-platform`) |
| `sid` | string | Short ID |
| `description` | string | Team description |
| `department` | string | Department name |
| `sub_department` | string | Sub-department name |
| `engineers` | array\<string\> | List of engineer email addresses |
| `tech_manager` | string | Tech manager |
| `senior_tech_manager` | string | Senior tech manager |
| `slack_channel_name` | string | Team Slack channel |
| `jira_project_id` | string | Jira project ID |
| `jira_team_owner` | string | Jira team owner |
| `primary_github_orgs` | array\<string\> | GitHub orgs the team uses |
| `pagerduty_escalation_policy_key` | string | PagerDuty escalation policy |
| `pagerduty_emergency_service_key` | string | PagerDuty emergency service |
| `pagerduty_schedule_key` | string | PagerDuty schedule |
| `timestamp` | string | Last updated |
| `version` | string | Version |

### platformmetadata_features

Application/component registry with ownership, tier, and repository info.

| Column | Type | Description |
|--------|------|-------------|
| `id` | string | Feature/component ID |
| `description` | string | Description |
| `owners` | string | Owning team |
| `type` | string | Component type |
| `contribution_type` | string | Contribution type |
| `tier` | bigint | Application tier (1-4) |
| `sonic_ring` | boolean | Whether part of Sonic Ring |
| `tags` | array\<string\> | Tags |
| `lifecycle.status` | string | Lifecycle status |
| `lifecycle.dueDateForNextStatus` | string | Due date for next status |
| `lifecycle.explanation` | string | Lifecycle explanation |
| `github_repository.owner` | string | GitHub org |
| `github_repository.name` | string | GitHub repo name |
| `github_repository.github_server` | string | GitHub server |
| `github_repository.locations` | array\<string\> | Locations |
| `app_group` | string | Application group |
| `sonarqube_project_id` | string | SonarQube project |
| `gitlab_project_id` | string | GitLab project |
| `trusted_committers` | array\<string\> | Trusted committers |
| `info.type` | string | Info type |
| `timestamp` | string | Last updated |
| `version` | string | Version |

### platformmetadata_projects

Project/namespace registry.

| Column | Type | Description |
|--------|------|-------------|
| `id` | string | Project ID |
| `owner` | string | Owning team |
| `process_group` | string | Process group |
| `namespace` | string | Kubernetes namespace |
| `description` | string | Description |
| `environments` | array\<string\> | Associated environments |
| `timestamp` | string | Last updated |
| `version` | string | Version |

### platformmetadata_environments

Environment registry with AWS account mapping.

| Column | Type | Description |
|--------|------|-------------|
| `id` | string | Environment ID |
| `alias` | string | Environment alias |
| `env_type` | string | Environment type |
| `owner` | string | Owner |
| `team` | string | Owning team |
| `platform` | string | Platform |
| `aws_account_alias` | string | AWS account alias |
| `aws_region` | string | AWS region |
| `tags` | array\<string\> | Tags |
| `timestamp` | string | Last updated |
| `version` | string | Version |

### platformmetadata_aws_accounts

AWS account directory.

| Column | Type | Description |
|--------|------|-------------|
| `id` | string | Account ID |
| `account_number` | string | AWS account number |
| `administrator` | string | Administrator |
| `administrator_email_address` | string | Admin email |
| `consolidated_billing_account_number` | string | Billing account |
| `account_groups` | array\<string\> | Account groups |
| `root_account_policy` | string | Root account policy |
| `is_part_of_core_platform` | boolean | Part of core platform |
| `timestamp` | string | Last updated |
| `version` | string | Version |

### platformmetadata_departments / subdepartments

Department hierarchy tables. Schema is minimal -- query them to discover the org structure.

---

## Services Metadata

### services_metadata_services

Business service catalog.

| Column | Type | Description |
|--------|------|-------------|
| `processid` | string | Process ID |
| `process` | string | Process name |
| `processgroupid` | string | Process group ID |
| `processgroup` | string | Process group name |
| `activityid` | string | Activity ID |
| `activity` | string | Activity name |
| `categoryid` | string | Category ID |
| `category` | string | Category |
| `level` | string | Level |
| `description` | string | Description |
| `owner.type` | string | Owner type |
| `owner.who` | string | Owner identity |
| `applicationlist` | array\<string\> | Associated applications |
| `subsystems` | array\<string\> | Subsystems |
| `smes` | array\<string\> | Subject matter experts |
| `appgroupid` | string | App group ID |
| `apqcidentifier` | string | APQC identifier |
| `timestamp` | string | Last updated |
| `version` | string | Version |

### services_metadata_channels

Communication channel catalog.

| Column | Type | Description |
|--------|------|-------------|
| `channelid` | string | Channel ID |
| `channel` | string | Channel name |
| `type` | string | Channel type |
| `audience` | string | Target audience |
| `description` | string | Description |
| `owner.type` | string | Owner type |
| `owner.who` | string | Owner |
| `applicationlist` | array\<string\> | Associated applications |
| `referenceslist` | array\<struct\> | References (referenceType, id) |
| `smes` | array\<string\> | SMEs |
| `timestamp` | string | Last updated |
| `version` | string | Version |

### services_metadata_gateways

API gateway catalog.

| Column | Type | Description |
|--------|------|-------------|
| `gatewayid` | string | Gateway ID |
| `gateway` | string | Gateway name |
| `type` | string | Gateway type |
| `description` | string | Description |
| `owner.type` | string | Owner type |
| `owner.who` | string | Owner |
| `appgroupid` | string | App group ID |
| `applicationlist` | array\<string\> | Applications behind this gateway |
| `smes` | array\<string\> | SMEs |
| `timestamp` | string | Last updated |
| `version` | string | Version |

---

## Security

### wiz_issues

Wiz security issues with SCD (slowly changing dimension) history.

| Column | Type | Description |
|--------|------|-------------|
| `id` | string | Issue ID |
| `title` | string | Issue title |
| `severity` | string | Severity level |
| `status` | string | Issue status |
| `description` | string | Issue description |
| `remediation` | string | Remediation guidance |
| `finding_url` | string | URL to Wiz finding |
| `resource_type` | string | Affected resource type |
| `resource_name` | string | Affected resource name |
| `resource_tags` | string | Resource tags |
| `resource_uid` | string | Resource UID |
| `cloud_account` | string | Cloud account |
| `cloud_platform` | string | Cloud platform |
| `cloud_region` | string | Cloud region |
| `risks` | array\<string\> | Associated risks |
| `team` | array\<string\> | Owning team(s) |
| `created_time` | timestamp | When the issue was created |
| `last_updated_time` | timestamp | Last update time |
| `year` | int | Partition: year |
| `month` | int | Partition: month |
| `is_latest` | boolean | Whether this is the current version |
| `valid_from` | timestamp | SCD valid from |
| `valid_to` | timestamp | SCD valid to |

**Important:** Filter with `is_latest = true` to get current issues only.

### wiz_vulnerabilities

Wiz vulnerability findings with SCD history.

| Column | Type | Description |
|--------|------|-------------|
| `id` | string | Vulnerability ID |
| `name` | string | Vulnerability name (CVE) |
| `severity` | string | Severity |
| `status` | string | Status |
| `description` | string | Description |
| `remediation` | string | Remediation |
| `score` | float | CVSS score |
| `finding_url` | string | URL to finding |
| `resource_type` | string | Resource type |
| `resource_technology` | string | Technology |
| `resource_name` | string | Resource name |
| `resource_tags` | string | Tags |
| `resource_uid` | string | Resource UID |
| `cloud_account` | string | Cloud account |
| `cloud_platform` | string | Cloud platform |
| `cloud_region` | string | Cloud region |
| `team` | array\<string\> | Owning team(s) |
| `first_seen_time` | timestamp | First detection |
| `last_seen_time` | timestamp | Last detection |
| `resolved_at` | timestamp | Resolution time |
| `has_exploit` | string | Whether an exploit exists |
| `fixed_version` | string | Fixed version |
| `exploitation_probability_epss` | float | EPSS score |
| `exploitation_probability_percentile_epss` | float | EPSS percentile |
| `exploitation_probability_severity_epss` | string | EPSS severity |
| `critical_related_issues_count` | string | Related critical issues |
| `high_related_issues_count` | string | Related high issues |
| `medium_related_issues_count` | string | Related medium issues |
| `low_related_issues_count` | string | Related low issues |
| `info_related_issues_count` | string | Related info issues |
| `year` | int | Partition: year |
| `month` | int | Partition: month |
| `is_latest` | boolean | Whether this is the current version |
| `valid_from` | timestamp | SCD valid from |
| `valid_to` | timestamp | SCD valid to |

**Important:** Filter with `is_latest = true` for current vulnerabilities.

### wiz_secrets / wiz_compliance_summary

Additional Wiz tables. Query `athena_describe_table` for full schemas when needed.

---

## GitHub

### github_pr_logs_clean

GitHub Enterprise pull request audit logs. Each row is a PR event (open, merge, review, etc.).

Key columns:

| Column | Type | Description |
|--------|------|-------------|
| `repo` | string | Full repo path (e.g., `org/repo`) |
| `actor` | string | User who performed the action |
| `action` | string | PR action (e.g., `create`, `merge`, `review`) |
| `pull_request_title` | string | PR title |
| `pull_request_url` | string | PR URL |
| `pull_request_id` | bigint | PR ID |
| `timestamp` | bigint | Unix timestamp in milliseconds |
| `org` | string | GitHub org |
| `reviewer` | string | Reviewer username |
| `actor_is_bot` | boolean | Whether actor is a bot |
| `operation_type` | string | Operation type |
| `category_type` | string | Category |

**Note:** `timestamp` is a Unix epoch in milliseconds. Convert with: `FROM_UNIXTIME(timestamp / 1000)`.

### github_git_logs

Git push/fetch events.

Key columns:

| Column | Type | Description |
|--------|------|-------------|
| `repository` | string | Repository name |
| `repository_owner` | string | Org/owner |
| `actor` | string | User |
| `action` | string | Git action |
| `result` | string | Result |
| `git_protocol_negotiated` | string | Protocol |
| `transport_protocol_name` | string | Transport |
| `timestamp` | bigint | Unix timestamp (ms) |
| `is_fetch_command` | boolean | Fetch vs push |

### github_repo_logs

Repository administration events (create, delete, visibility changes, settings, etc.).

Key columns: `repo`, `actor`, `action`, `visibility`, `timestamp` (bigint, ms).

### github_business_logs

GitHub Enterprise business-level audit events.

Key columns: `actor`, `action`, `org`, `business`, `timestamp` (bigint, ms).

### github_copilot_metrics

Daily Copilot usage metrics. Nested structs for IDE chat, code completions, and dotcom features.

| Column | Type | Description |
|--------|------|-------------|
| `date` | string | Date (YYYY-MM-DD) |
| `total_active_users` | bigint | Total active users |
| `total_engaged_users` | bigint | Engaged users |
| `copilot_ide_code_completions` | struct | Code completion metrics by editor/model/language |
| `copilot_ide_chat` | struct | Chat metrics by editor/model |
| `copilot_dotcom_chat` | struct | Dotcom chat metrics |
| `copilot_dotcom_pull_requests` | struct | PR summary metrics |

### github_copilot_seats

Copilot seat assignments. Query for schema when needed.

### github_repo_languages / ghe_repo_languages

Repository language statistics. Query for schema when needed.

---

## Reliability

### reliability_peak_availability_mom

Monthly peak availability metrics.

| Column | Type | Description |
|--------|------|-------------|
| `year` | int | Year |
| `month` | int | Month |
| `days_in_month` | int | Days in month |
| `num_markets_in_month` | int | Number of markets |
| `peak_minutes` | double | Total peak minutes |
| `peak_jug_avail_used_minutes` | double | Available minutes used |
| `monthly_peak_avail_pct` | double | Monthly availability % |
| `peak_avail_running_ytd_pct` | double | Year-to-date availability % |

### reliability_missed_orders_wow

Weekly missed orders metrics.

| Column | Type | Description |
|--------|------|-------------|
| `year` | int | Year |
| `week_from` | int | Week start |
| `week_to` | int | Week end |
| `weekly_pct` | double | Weekly missed order % |
| `ytd_pct` | double | Year-to-date % |

### reliability_mttd_mom

Monthly Mean Time To Detect.

| Column | Type | Description |
|--------|------|-------------|
| `year` | int | Year |
| `month` | int | Month |
| `running_ytd` | double | Running YTD MTTD |

---

## Cost

### finout_wow_by_component

Weekly infrastructure cost by application/component.

| Column | Type | Description |
|--------|------|-------------|
| `app` | string | Application name |
| `environment` | string | Environment |
| `cost` | double | Cost amount |
| `department` | string | Department |
| `sub_department` | string | Sub-department |
| `team` | string | Team |
| `cost_center` | string | Cost center |
| `date` | date | Date |
| `year` | int | Partition: year |
| `week_from` | int | Week start |
| `week_to` | int | Week end |

---

## Audit Logs

### okta_logs

Okta SSO/authentication audit logs. Complex nested structure.

Key columns:

| Column | Type | Description |
|--------|------|-------------|
| `eventtype` | string | Okta event type |
| `published` | string | Event timestamp |
| `severity` | string | Event severity |
| `displaymessage` | string | Human-readable message |
| `outcome.result` | string | Outcome (SUCCESS, FAILURE, etc.) |
| `outcome.reason` | string | Failure reason |
| `actor.alternateId` | string | Actor email/identifier |
| `actor.displayName` | string | Actor display name |
| `target_alternateid` | string | Target identifier |
| `target_displayname` | string | Target display name |
| `target_type` | string | Target type |
| `client.ipAddress` | string | Client IP |
| `client.userAgent.browser` | string | Browser |
| `client.userAgent.os` | string | OS |
| `client.geographicalContext.country` | string | Country |
| `client.geographicalContext.city` | string | City |

### vault_logs

HashiCorp Vault audit logs.

| Column | Type | Description |
|--------|------|-------------|
| `time` | string | Timestamp |
| `type` | string | Log type |
| `operation` | string | Vault operation |
| `path` | string | Vault path |
| `display_name` | string | Identity |
| `client_id` | string | Client ID |
| `environment` | string | Environment |
| `service` | string | Service name |
| `vault_platform` | string | Platform |
| `host` | string | Host |
| `kube_cluster_name` | string | Kubernetes cluster |
| `is_audit_event` | boolean | Whether this is an audit event |
| `request_id` | string | Request ID |
| `response` | string | Response |
| `message` | string | Message |

### confluent_logs

Confluent Cloud (Kafka) audit logs.

| Column | Type | Description |
|--------|------|-------------|
| `time` | string | Timestamp |
| `service_name` | string | Service |
| `method_name` | string | Method |
| `result_status` | string | Result |
| `user_email` | string | User email |
| `user_id` | string | User ID |
| `principal_resource_id` | string | Principal resource |
| `resource_name` | string | Resource name |
| `request_data` | string | Request data (JSON string) |
| `validate_only` | boolean | Dry run flag |

### artifactory_logs

JFrog Artifactory logs.

| Column | Type | Description |
|--------|------|-------------|
| `timestamp` | string | Timestamp |
| `message` | string | Log message |
| `environment` | string | Environment |
| `account_id` | string | AWS account |
| `region` | string | AWS region |
| `availability_zone` | string | AZ |
| `k8s_namespace` | string | Kubernetes namespace |
| `k8s_container` | string | Container name |
| `k8s_pod` | string | Pod name |
| `instance_id` | string | Instance ID |
| `vpc_id` | string | VPC ID |
| `private_ip` | string | Private IP |

### rdscloudwatch_logs

RDS CloudWatch audit logs.

| Column | Type | Description |
|--------|------|-------------|
| `date_time` | string | Timestamp |
| `user_name` | string | Database user |
| `query` | string | SQL query |
| `server_host` | string | RDS host |
| `account_id` | string | AWS account |
| `region` | string | AWS region |
| `is_cluster` | boolean | Whether cluster |

---

## DORA / PMD Stats

### pmd_stats

Repository-level engineering metrics (PRs, contributors, SLA compliance, etc.). Very wide table.

Key columns:

| Column | Type | Description |
|--------|------|-------------|
| `repo_link` | string | Repository URL |
| `department` | string | Department |
| `sub_department` | string | Sub-department |
| `tier` | string | Application tier |
| `component_type` | string | Component type |
| `#_prs_merged` | bigint | PRs merged |
| `#_of_internal_prs` | bigint | Internal PRs |
| `#_of_external_prs` | bigint | External PRs (cross-team) |
| `avg_pr_time_(hours)` | double | Average PR merge time |
| `total_contributors` | bigint | Number of contributors |
| `total_teams` | bigint | Number of contributing teams |
| `total_external_teams` | bigint | External contributing teams |
| `commits_time_period` | bigint | Commits in period |
| `weeks_since_last_change` | bigint | Weeks since last change |
| `is_archived?` | boolean | Whether archived |
| `repo_visibility` | string | Repo visibility |
| `is_sonic_ring?` | boolean | Part of Sonic Ring |
| `total_additions` | bigint | Lines added |
| `total_deletions` | bigint | Lines deleted |

Additional `pmd_stats_*` tables provide aggregated views: `pmd_stats_wow_by_component`, `pmd_stats_wow_by_repo`, `pmd_stats_wow_by_repo_team`, `pmd_stats_mom_by_component`, `pmd_stats_mom_by_repo`, `pmd_stats_mom_by_repo_team`.
