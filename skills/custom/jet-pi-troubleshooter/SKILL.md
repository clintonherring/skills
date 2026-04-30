---
name: jet-pi-troubleshooter
description: >-
  Investigate and root-cause production incidents (PIs) at JET by correlating infrastructure
  changes, Datadog observability data, and GitHub PR history. Use this skill when a user wants
  to troubleshoot, investigate, debug, or find the root cause of a production incident -- whether
  they provide a PI ticket number (e.g. "investigate PI-33288"), a symptom description
  (e.g. "COQ is down", "customers can't log in", "database connection errors"), or ask
  about recent infrastructure changes that may have caused an outage. Also use when the user
  asks to check what changed before an incident, look for DNS changes, networking changes,
  IAM/SSO changes, or correlate Datadog errors with code changes. Triggers on phrases like
  "troubleshoot this PI", "what caused this outage", "find the root cause", "what changed",
  "investigate this incident", "check recent infra changes", "why is X service down", or any
  request to correlate changes with production failures.
  Do NOT use for pi timeline, pi catchup, pi post-mortem, or pi prodmeet commands -- those
  belong to jet-pi-summary.
---

# PI Troubleshooter

## Self-Improving Context

Before starting any investigation:
1. **Check `examples/`** for past PI investigations with similar symptoms or affected services
2. **Apply `learnings.md`** patterns -- known root causes, common correlations, shortcuts

After completing an investigation:
- The user may say **"new pi example"** to capture this PI as a reference for future investigations

---

Systematically investigate production incidents by correlating five evidence streams:
1. **Jira ticket data** -- timeline, impacted components, comments, linked tickets
2. **Datadog observability** -- error logs, metrics spikes, events during the incident window
3. **GitHub PR history** -- recent infrastructure and application changes in key repositories
4. **AWS events** -- CloudTrail console changes, CloudWatch alarms, Route53 record modifications
5. **Wiz security** -- vulnerabilities, misconfigurations, and security issues on affected resources

The goal is to move from "something is broken" to "this specific change caused it" as fast as possible.

## Prerequisites

Load these skills before starting (they provide the tools you need):
- **jet-company-standards** -- for `acli` (Jira), `gh` (GitHub Enterprise)
- **jet-datadog** -- for `pup` (Datadog logs, metrics, events)
- **jet-aws** -- for AWS CLI operations (CloudTrail, CloudWatch, Route53 lookups)
- **wiz-skill** -- for Wiz security issues, vulnerabilities, and cloud resource graph

If a tool is not on PATH, check `toolkit/` for Windows-specific locations and setup instructions.

## Investigation Workflow

The investigation is **evidence-driven**. You start broad, and whenever a finding from one source gives you new information (a hostname, an ARN, a timestamp, a username), you take that back to the other sources to narrow down. Don't loop for the sake of looping -- only go back when you have something new to look for.

```
  Jira → incident window, components, symptoms
                    │
                    ▼
         ┌──── Start broad ────┐
         │                     │
      Datadog               GitHub PRs
      (errors)              (recent changes)
         │                     │
         └──── new info? ──────┘
                    │
        ┌───yes─────┴─────no──────┐
        │                         │
   Take the new info         Widen the search
   (hostname, ARN,           or check CloudTrail /
    error code, IP)          Wiz for other angles
   back to the other
   sources to narrow
        │                         │
        └─────────┬───────────────┘
                  │
       ┌──────────┴──────────┐
       │                     │
  AWS CloudTrail /       Wiz Security
  CloudWatch             (vulnerabilities,
  (confirm state         misconfigs on
   changes, catch        affected resources,
   console changes)      security context)
       │                     │
       └──────────┬──────────┘
                  │
           Correlate & Conclude
```

### Phase 1: Establish the Facts

The first job is to understand what happened, when, and what was affected. Without this, you're searching blind.

**If given a PI ticket number:**
```bash
acli jira workitem view <TICKET> --json --fields="*all"
```

Extract from the ticket:
- **Summary and description** -- what was reported
- **Incident start time** (`customfield_31570`) and end time (`customfield_21029`)
- **Impacted components** (`customfield_21014`) -- the list of affected services
- **Root cause category** (`customfield_20612`, `customfield_20613`) -- if already filled
- **Linked tickets** (`issuelinks`) -- related PIs, retro tickets, follow-up tasks
- **Comments** -- often contain the real investigation details
- **Timeline field** (`customfield_12341`) -- structured incident timeline if populated
- **RCA field** (`customfield_12520`) -- root cause analysis if populated
- **Labels** -- e.g. `releasewarranty` indicates a recent deployment

Also fetch comments separately for the full discussion:
```bash
acli jira workitem comment list --key <TICKET> --json
```

Check all linked tickets too -- retro tickets and related PIs often contain the actual root cause details.

**If given a symptom description:**
Ask the user:
1. When did the issue start? (approximate time)
2. Which service(s) or market(s) are affected?
3. What's the user-visible symptom?

Then search for matching PI tickets:
```bash
acli jira workitem search --jql "project = PI AND summary ~ '<keywords>' AND created >= '-7d'" --json --fields="summary,status,created"
```

### Phase 2: Recursive Investigation Loop

This is the core of the investigation. You iterate between Datadog, GitHub, and AWS until you can pinpoint the exact change that caused the failure. Each iteration should narrow the search.

**Time window**: Start from the incident start time and look back **up to 24 hours**. Even if the ticket has a precise start time, go back further because changes can have delayed effects (e.g., DNS TTL expiry, cron-triggered config reloads, gradual connection pool exhaustion).

Always set Datadog to the EU site:
```bash
export DD_SITE=datadoghq.eu
```

#### Start Broad: Get the Initial Picture

Run these in parallel to see what's going on:

**Datadog -- error landscape:**
```bash
# Broad error count by service during incident window
pup logs aggregate \
  --query="status:error" \
  --from="<incident-start-minus-30min>" \
  --to="<incident-end-plus-30min>" \
  --compute="count" \
  --group-by="service" \
  --storage=flex
```

**GitHub -- recent PRs in symptom-relevant repos** (see Symptom-to-Repo Mapping below):
```bash
# Include ALL PRs (open and merged) -- open PRs may have applied changes via CI
gh api --hostname github.je-labs.com "/repos/IFA/<repo>/pulls?state=all&sort=updated&direction=desc&per_page=30" \
  | jq '.[] | {number, title, state, merged_at, updated_at, user: .user.login}'
```

**CloudTrail -- infrastructure API calls:**
```bash
# Check for changes to the relevant AWS service (route53, iam, ec2, rds, etc.)
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventSource,AttributeValue=<service>.amazonaws.com \
  --start-time <24h-before-incident-UTC> \
  --end-time <incident-end-UTC> \
  --output json
```

**CloudWatch -- check for alarm state changes and anomalies:**
```bash
# List alarms that fired during the incident window
aws cloudwatch describe-alarm-history \
  --start-date <24h-before-incident-UTC> \
  --end-date <incident-end-UTC> \
  --history-item-type StateUpdate \
  --output json

# Check for specific metric anomalies (e.g., DNS query failures, error rates)
aws cloudwatch get-metric-statistics \
  --namespace AWS/Route53 \
  --metric-name DNSQueries \
  --dimensions Name=HostedZoneId,Value=<zone-id> \
  --start-time <start> --end-time <end> \
  --period 60 --statistics Sum \
  --output json
```

**Wiz -- check for security issues on affected components:**
```bash
# See toolkit/wiz.md for the correct path to wiz_api.sh on this machine
source C:/.agents/skills/wiz-skill/scripts/wiz_api.sh

# Search for the affected service's Wiz project
wiz_search_projects "<component-name>"

# List open security issues for the affected service
wiz_list_issues --project-name "<component-name>" --status OPEN --severity CRITICAL,HIGH --limit 10

# Check for vulnerabilities on the affected service
wiz_vuln_report "<component-name>"
```

#### Follow the Leads: Use New Information to Narrow Down

When you find something specific -- a hostname in an error message, an ARN in a CloudTrail event, a timestamp from a CI run -- take it back to the other sources to narrow the search.

**Datadog → extract specific identifiers from errors:**
```bash
# Sample actual error messages from the highest-count service
pup logs search \
  --query="status:error AND service:<name>" \
  --from="<start>" --to="<end>" \
  --limit=5 \
  --storage=flex
```

Look for actionable identifiers in the error messages:
- **Hostnames**: `consumerorderqueriesapi-production.je-apis.com` → search Route53 PRs for this hostname
- **Resource ARNs**: `arn:aws:iam::123456:role/foo` → search CloudTrail for this ARN
- **Database names / usernames**: `v-kubernetes-live-orders-*` → search for ProxySQL/Vault changes
- **IP addresses**: `10.x.x.x connection refused` → search security group / NACL changes
- **Error codes**: `NXDOMAIN`, `AccessDenied`, `SQLSTATE` → classifies the failure type

**GitHub → match identifiers to PR diffs:**
```bash
# Search for the specific hostname/resource across IFA repos
gh api --hostname github.je-labs.com "/search/code?q=org:IFA+<hostname-or-identifier>" \
  | jq '.items[] | {repository: .repository.full_name, path: .path}'

# Once you find a candidate PR, get its diff
gh api --hostname github.je-labs.com "/repos/IFA/<repo>/pulls/<number>/files" \
  | jq '.[] | {filename, status, additions, deletions, patch}'
```

**GitHub → check CI apply times (not just merge times):**

In IaC repos, `terraform apply` runs during CI on push -- often well before the PR is merged. The actual infrastructure change happens at apply time.

```bash
# Get the PR's branch name
gh api --hostname github.je-labs.com "/repos/IFA/<repo>/pulls/<number>" \
  | jq '{head_ref: .head.ref, created_at, updated_at, merged_at, state}'

# List CI workflow runs on that branch -- look for apply steps and their timestamps
gh api --hostname github.je-labs.com "/repos/IFA/<repo>/actions/runs?branch=<head_ref>&per_page=10" \
  | jq '.workflow_runs[] | {id, name, status, conclusion, created_at, updated_at}'
```

**Important -- drift and reverts**: An unmerged PR's apply can make a change, and a *subsequent* apply on a different PR can revert it. The PR that caused the outage might not contain the problematic change in its final diff -- the damage was done by an intermediate apply. Always check multiple PRs' CI runs to understand the sequence of applies.

**CloudTrail → confirm the actual infrastructure change:**
```bash
# Confirm a specific DNS record change happened
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=ChangeResourceRecordSets \
  --start-time <apply-time-minus-5min> --end-time <apply-time-plus-5min> \
  --output json | jq '.Events[] | {EventTime, Username, CloudTrailEvent}' 

# Confirm IAM policy changes
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=PutRolePolicy \
  --start-time <start> --end-time <end> \
  --output json

# Confirm security group changes
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=AuthorizeSecurityGroupIngress \
  --start-time <start> --end-time <end> \
  --output json
```

**CloudWatch → confirm the impact timeline:**
```bash
# Check error rate metrics for the affected service
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name HTTPCode_Target_5XX_Count \
  --dimensions Name=TargetGroup,Value=<tg-arn> \
  --start-time <start> --end-time <end> \
  --period 60 --statistics Sum \
  --output json

# Check for connection/health check failures
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name UnHealthyHostCount \
  --dimensions Name=TargetGroup,Value=<tg-arn> \
  --start-time <start> --end-time <end> \
  --period 60 --statistics Maximum \
  --output json
```

**Wiz → find where resources live and what they connect to:**

When you have a service or resource name but need to know which AWS account, region, or VPC it's in -- or what it depends on -- Wiz's cloud resource graph has this.

```bash
# Find a resource and its account/region (use the entity type that fits: VIRTUAL_MACHINE, SERVERLESS, CONTAINER, ENDPOINT, DATABASE, etc.)
wiz_query 'query {
  graphSearch(query: {type: [VIRTUAL_MACHINE, SERVERLESS, CONTAINER, ENDPOINT, DATABASE], 
    where: {name: {CONTAINS: ["<resource-name>"]}}}, first: 5) {
    nodes { entities { id name type properties } }
  }
}' '{}'
# Look for subscriptionExternalId (AWS account ID), subscriptionName, region in the properties

# Find what the resource connects to (databases, queues, buckets, endpoints)
wiz_query 'query {
  graphSearch(query: {type: [SERVERLESS], where: {name: {EQUALS: ["<resource-name>"]}},
    relationships: [{type: [{type: ANY_OUTGOING}], with: {type: [DATABASE, BUCKET, ENDPOINT, MESSAGING_SERVICE], select: true}}]
  }, first: 20) {
    nodes { entities { id name type } }
  }
}' '{}'

# Check open security issues on the resource's project
wiz_list_issues --project-name "<project-name>" --status OPEN --severity CRITICAL,HIGH --limit 10
```

Use the account ID and region from Wiz to target your CloudTrail and CloudWatch queries to the right account.

#### Keep Narrowing If Needed

Only continue digging if the evidence so far doesn't clearly connect a change to the failure. Use what you've learned to ask more specific questions:

| If you found... | Then check... |
|---|---|
| NXDOMAIN for a specific hostname | Route53 PRs + CloudTrail `ChangeResourceRecordSets` for that zone |
| Access denied with a specific role ARN | CloudTrail `PutRolePolicy`/`DeleteRolePolicy` + jet-aws-sso PRs |
| Connection refused to a specific IP | Security group changes in CloudTrail + aws-infrastructure PRs |
| ProxySQL error with a Vault username | Vault audit logs, Puppet run history, ProxySQL config PRs |
| Error spike at a specific time | All CI workflow runs across candidate repos at that exact time |
| CloudTrail shows a change but no matching PR | Manual console change -- check `userIdentity` for who did it |
| PR diff matches but apply time doesn't align | Check for other PRs on the same Terraform state -- drift from competing applies |
| Unexplained access/auth failure | Wiz -- check for misconfigurations or security policy changes on the resource |
| Resource behaving unexpectedly | Wiz graph search -- check what it connects to, look for security issues on dependencies |

**Datadog -- refine with narrower queries as you learn more:**
```bash
# Once you know the error pattern, get precise first/last occurrence
pup logs aggregate \
  --query="*<specific-error-string>* AND service:<name>" \
  --from="<wider-window-start>" --to="<wider-window-end>" \
  --compute="count" \
  --group-by="@timestamp" \
  --storage=flex

# Check if the error existed before the incident (pre-existing vs new)
pup logs aggregate \
  --query="*<specific-error-string>*" \
  --from="<24h-before-incident>" --to="<incident-start>" \
  --compute="count" \
  --group-by="service" \
  --storage=flex
```

**Datadog -- deployment and config change events:**
```bash
pup events list --from="<24h-before>" --to="<incident-end>"
```

**Datadog -- metrics for performance-related incidents:**
```bash
# Error rate spike
pup metrics query \
  --query="sum:trace.servlet.request.errors{service:<name>}.as_count()" \
  --from="<start>" --to="<end>"

# Latency spike
pup metrics query \
  --query="avg:trace.servlet.request.duration{service:<name>}" \
  --from="<start>" --to="<end>"
```

**Application repository changes** -- if the ticket identifies specific components:
```bash
# Find the repo in PlatformMetadata
gh api --hostname github.je-labs.com /repos/metadata/PlatformMetadata/contents/Data/global_features/<component>.json \
  | jq -r '.content' | base64 -d

# Check recent PRs (deployments)
gh api --hostname github.je-labs.com "/repos/<org>/<repo>/pulls?state=all&sort=updated&direction=desc&per_page=10" \
  | jq '.[] | select(.merged_at != null) | {number, title, merged_at}'
```

**Date-filtered PR search** when the default list doesn't go back far enough:
```bash
gh api --hostname github.je-labs.com "/search/issues?q=repo:IFA/<repo>+type:pr+updated:<date-start>..<date-end>" \
  | jq '.items[] | {number, title, state, closed_at, user: .user.login}'
```

#### Stop Condition

Stop iterating when you can state all three:
1. **What changed** -- the specific PR, apply, or console action
2. **When it changed** -- the apply/action timestamp from CI runs or CloudTrail (not the merge time)
3. **How it caused the failure** -- the mechanism connecting the change to the Datadog errors (e.g., "deleted DNS record → NXDOMAIN → service unreachable for 25 min due to negative caching")

If after 3-4 iterations you cannot pinpoint a specific change, the issue may be:
- A non-IaC change (application config, feature flag, external dependency)
- A capacity/scaling issue rather than a change-induced failure
- A delayed effect from a much older change (TTL expiry, cert rotation, lease expiry)

Report what you found and what you ruled out.

### Phase 3: Correlate and Conclude

Build a timeline combining all evidence. Every entry should cite its source.

```
## Investigation Summary

### Timeline
| Time (UTC) | Event | Source |
|---|---|---|
| HH:MM | Terraform apply on PR #X (branch Y) | GitHub Actions |
| HH:MM | CloudTrail: ChangeResourceRecordSets on zone Z | AWS CloudTrail |
| HH:MM | First NXDOMAIN errors for hostname A | Datadog |
| HH:MM | CloudWatch alarm triggered | AWS CloudWatch |
| HH:MM | User reports issue in Slack | PI ticket |
| HH:MM | Service restored (errors stop) | Datadog |

### Root Cause
<What changed, when it was applied (not merged), and the mechanism that caused the failure>

### Evidence Chain
<Datadog error → specific identifier → PR diff / CloudTrail event → CI apply timestamp>

### Contributing Factors
<Why detection was slow, why impact was wider than expected, drift from competing applies, etc.>

### Recommendations
<What to fix to prevent recurrence>
```

## Investigation Patterns by Symptom Type

> **Note**: These patterns are enhanced over time. When a new PI reveals a novel pattern, add it to `examples/` and update this section with a summary + reference. Check `examples/` for detailed step-by-step investigation patterns beyond what's summarised here.

### DNS Issues
**Symptoms**: Service unreachable, NXDOMAIN, "cannot resolve hostname"
**Check first**: IFA/route53 PRs, IFA/domain-routing PRs, IFA/cloudflareplatformproduction PRs
**Common causes**: 
- Terraform delete-then-create race condition on record type changes
- Negative DNS caching extending outage beyond the actual record gap
- SmartPipelines recreating old DNS records after migration
**Key Datadog query**: `*NXDOMAIN* OR *no such host* OR *connection refused*`

### Database Connection Failures
**Symptoms**: "Access denied", ProxySQL errors, connection pool exhaustion
**Check first**: ProxySQL config changes (Puppet repos), Vault lease expiry
**Common causes**:
- ProxySQL restart loading stale user config (Vault-issued credentials not in on-disk config)
- Vault credential rotation failure
- Puppet run resetting ProxySQL mysql_users table
**Key Datadog query**: `*ProxySQL Error* OR *Access denied* OR *connection pool* OR *SQLSTATE*`

### Networking Issues
**Symptoms**: Timeouts between services, cross-account access failures
**Check first**: IFA/aws-infrastructure PRs (transit gateways, security groups, NACLs)
**Common causes**:
- Security group rule changes
- Transit gateway route table modifications
- VPC peering changes
**Key Datadog query**: `*connection timed out* OR *connection refused* OR *network unreachable*`

### IAM / Authentication Failures
**Symptoms**: 403 errors, "access denied" to AWS resources, SSO failures, RDS IAM auth failures
**Check first**: IFA/jet-aws-sso PRs, IFA/aws-sso-legacy-takeaway PRs, CloudTrail IAM events, Wiz issues on the affected resource
**Common causes**:
- SSO permission set changes
- IAM policy modifications
- IRSA (IAM Roles for Service Accounts) configuration changes
- Security policy enforcement (Wiz-detected misconfigurations leading to automated remediation)
- **ABAC / session tag misconfiguration** -- IAM policies referencing `${aws:PrincipalTag/*}` variables that never resolve because Identity Center ABAC attribute mapping is missing or broken (see ABAC investigation pattern below)
- **One SSO profile works, another doesn't** -- often means the working profile has a broad managed policy (e.g., `AdministratorAccess`) that bypasses tag-based or resource-scoped restrictions entirely
**Key Datadog query**: `*AccessDenied* OR *403* OR *not authorized* OR *AssumeRole*`

#### ABAC / Session Tag Investigation Pattern

> **See**: `examples/abac-rds-iam-auth.md` for the full step-by-step investigation pattern including IAM Policy Simulator usage, Identity Center ABAC checks, and permission set discovery.

**Quick summary**: When IAM policies use `${aws:PrincipalTag/<tagName>}`, the tag must be passed via Identity Center ABAC. If ABAC is not configured, the variable resolves to empty and policies silently fail. Use IAM Policy Simulator to confirm, then check `describe-instance-access-control-attribute-configuration` in mgmt account `778305418618`.

### Security / Misconfiguration
**Symptoms**: Unexpected resource behavior, access patterns changing, compliance-driven service disruption
**Check first**: Wiz open issues on the affected component/project, recent Wiz issue status changes
**Common causes**:
- Automated remediation of a Wiz-detected misconfiguration (e.g., public access revoked, encryption enforced)
- Vulnerability patching causing service restart or incompatibility
- Security group / network policy tightened due to a Wiz finding
**Key Wiz query**: `wiz_list_issues --project-name "<component>" --status OPEN,IN_PROGRESS,RESOLVED --severity CRITICAL,HIGH --limit 25` (include RESOLVED to see recently-fixed issues that may have caused disruption)

### RDS IAM Authentication Failures

> **See**: `examples/rds-iam-auth-failure.md` for the full pattern including check-first list, common causes, key repos, and Datadog queries.

**Symptoms**: "Access denied" when connecting to RDS with IAM auth, `generate-db-auth-token` succeeds but connection fails, works with one SSO profile but not another
**Quick checks**: IAM Policy Simulator, Identity Center ABAC config, Terraform DB user provisioning, SSO policy repos
**Key Datadog query**: `*rds-db:connect* OR *Access denied* OR *authentication* AND service:<db-related-service>`

## Key IFA Repositories Reference

| Repository | Purpose | Check for |
|---|---|---|
| `IFA/route53` | DNS record management (Terraform) | DNS-related outages |
| `IFA/domain-routing` | Domain routing configuration | DNS routing / service discovery issues |
| `IFA/cloudflareplatformproduction` | Cloudflare production config | CDN/WAF/DNS proxy issues |
| `IFA/cloudflareplatformstaging` | Cloudflare staging config | Staging DNS issues |
| `IFA/aws-infrastructure` | Core AWS infra (VPCs, TGWs, SGs) | Networking issues |
| `IFA/jet-aws-sso` | AWS SSO / IAM config (JET) | Auth/permission failures, ABAC policies |
| `IFA/aws-sso-legacy-takeaway` | AWS SSO / IAM config (legacy Takeaway) | Auth/permission failures, ABAC policies |
| `IFA/puppet7-control-*` | Puppet config management | ProxySQL, server config |
| `Data-Infrastructure-Platform-Services/tkwy-aws-datastores` | RDS cluster definitions, DB user provisioning (Terraform) | RDS IAM auth failures, missing DB users |

All IFA repositories: `https://github.je-labs.com/orgs/IFA/repositories`

## Tips

> **Note**: Tips are accumulated from real PI investigations. When a new investigation reveals a reusable insight, add it here and create a detailed example in `examples/` if the pattern is complex enough to warrant step-by-step instructions.

- **Timing is everything**: The most powerful signal is a change that was merged/applied minutes before the first error. Always sort PRs by merge time and compare with Datadog error timestamps.
- **Negative DNS caching**: A 2-minute DNS gap can cause a 30-minute outage. When DNS is involved, the duration of the record being missing is NOT the duration of the outage.
- **Check staging too**: Staging ProxySQL/infra issues (e.g., PI-31994) sometimes indicate production risk.
- **Follow the links**: PI tickets often have linked retro tickets, related PIs, and follow-up tasks that contain the actual root cause analysis.
- **Console changes are invisible in code**: Always check CloudTrail for manual AWS console changes that bypass the IaC pipeline.
- **Terraform apply != PR merge**: In IaC repos, the infrastructure change happens at `terraform apply` time during CI, which can be well before the PR is merged -- or the PR may never be merged at all. A partial apply on an unmerged PR can cause an outage, and a subsequent apply on a different PR can silently revert the change, making the root cause hard to trace from diffs alone. Always check CI run history and apply logs.
- **Vault credentials**: Username patterns like `v-kubernetes-*` indicate Vault-issued dynamic credentials. If these get "access denied", the issue is usually at the ProxySQL layer, not the database.
- **Wiz as a resource map**: Wiz knows which AWS accounts, regions, and subscriptions resources live in. When you have a service name but don't know which account to query CloudTrail or CloudWatch in, use Wiz graph search to find the resource and read its `subscriptionExternalId` (AWS account ID), `subscriptionName`, and `region`. Wiz also maps dependencies -- what databases, queues, buckets, and endpoints a service connects to -- which helps identify blast radius and trace failures across service boundaries.
- **IAM Policy Simulator is your best friend for auth issues**: When debugging "access denied" or "implicit deny" problems, use `aws iam simulate-principal-policy` against the exact role ARN. It tells you which statement matched or didn't, and critically, which `MissingContextValues` (like session tags) the policy expected but didn't receive. This is often faster than reading policy JSON and guessing.
- **ABAC might not be configured**: If IAM policies use `${aws:PrincipalTag/*}` variables, those tags must be propagated via Identity Center ABAC attribute mapping. If ABAC was never enabled on the Identity Center instance, ALL such policies are silently broken. The management account for Identity Center is `778305418618`. Check with `describe-instance-access-control-attribute-configuration`.
- **IaC gaps are a root cause category**: Some critical AWS configurations (like Identity Center ABAC attribute mappings) are not managed as code in any repo. When you can't find the config in GitHub, it may only exist in the AWS console -- and may have been accidentally deleted or never created. Always check whether the config you're investigating is actually IaC-managed before assuming a PR caused the change.
- **"Works with one profile, broken with another" is a policy comparison problem**: When the same action works with one SSO profile but not another, immediately compare their managed policies. A profile with `AdministratorAccess` bypasses all resource-scoped and tag-based restrictions, masking underlying misconfigurations that affect least-privilege profiles.
- **"Missing" ≠ "never existed" — always check CloudTrail for deletion**: When a configuration is missing (e.g., `ResourceNotFoundException` from an AWS describe call), do NOT assume it was never created. Immediately query CloudTrail in the owning account for `Delete*` events on that resource. The pattern is: (1) confirm the config is missing, (2) search CloudTrail for creation and deletion events, (3) identify who deleted it, when, and from where (console vs CLI vs Terraform). This distinguishes accidental deletion from never-configured, which changes the remediation path entirely. For Identity Center ABAC: search for `DeleteInstanceAccessControlAttributeConfiguration` and `CreateInstanceAccessControlAttributeConfiguration` in management account `778305418618`.
- **Correlate with Datadog error onset**: When you find a CloudTrail mutation event, check Datadog for errors that started at the same time. For IAM/auth issues, search Flex Logs for `AccessDenied`, `AuthorizationError`, or connection failures in the affected services. The error onset time should match the CloudTrail event timestamp, confirming causation.

## IFA Confluence Reference

The IFA team space at `https://justeattakeaway.atlassian.net/wiki/spaces/INFOPS/overview` contains documentation for troubleshooting. Use `acli confluence page view --id <page-id> --body-format storage --json` to read pages.

### Key Pages

| Page | ID | What it contains |
|---|---|---|
| **Important DNS Hosted Zones** | `6513295957` | List of all DNS zones, which AWS accounts they live in, account IDs, zone IDs, and which are IaC-managed vs manual. Essential for knowing where to look in CloudTrail. |
| **DNS in Route53 Repository** | `6599083795` | How the IFA/route53 repo works, when to use it, PR process. |
| **JET Networking** | `8467612150` | Full explanation of JET's network architecture: VPCs, subnets, transit gateways, firewalls, security groups, TGW classification by env type and region. |
| **Connectivity Test Runbook** | `8831009173` | Checklist for verifying basic connectivity after network changes. Links to a spreadsheet of SMG health checks, Vault endpoints, EKS cluster APIs, Kafka endpoints. |
| **Cloudflare Runbooks** | `8892186827` | Cloudflare operations: certificate auto-renewal failures (`8777269292`), general operations & access (`8894611463`). |
| **SSO** | `6470664207` | AWS SSO managed by IFA as IaC. Legacy TKWY and JE repos, elevated access procedure (`6800572630`). |
| **How to contact IFA** | `8449065070` | Slack channels: `#help-infra-foundations-aws` for questions/PRs, `@support-ifa` for help, `@on-call-ifa` for incidents only. Support hours 9:00-23:00 CEST Mon-Fri. |

### Navigating the Space

```
INFOPS Space (homepage: 6135481117)
├── About IFA (8448540761) -- team info, contact, contribution guide
├── Knowledge Space (8449163378)
│   ├── Infrastructure AWS (8448442469)
│   │   └── JET Networking (8467612150)
│   ├── DNS (8448213097)
│   │   ├── AWS Route53 (8449196162)
│   │   ├── CloudFlare (8448933994)
│   │   └── Important DNS Hosted Zones (6513295957)
│   └── IAM (8448704645)
│       ├── OneEKS (8448278659)
│       ├── Team Onboardings (8448245903)
│       └── SSO (6470664207)
├── Runbooks (8775991670)
│   ├── Connectivity Test (8831009173)
│   ├── Cloudflare Runbooks (8892186827)
│   └── Runbooks Old (6137152911)
├── Guides (8448213135)
│   ├── AWS Infrastructure (8448344429)
│   ├── Request Okta Group (6675923612)
│   └── Teleport (6307681922)
└── Internal (8448409740)
```
