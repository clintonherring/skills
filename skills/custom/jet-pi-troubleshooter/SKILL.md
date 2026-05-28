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

Ensure `acli` is on PATH. If not found, check `C:\Users\ClintonHerring` or ask the user where it's installed and add it:
```bash
$env:PATH = "C:\Users\ClintonHerring;$env:PATH"
```

### AWS SSO Authentication

All AWS profiles share a single SSO portal. If any `aws` command fails with an expired token or authorization error, re-authenticate by running:
```bash
aws sso login --profile clinton-idm-node
```
This opens a browser for Okta authentication. Once completed, all AWS profiles are usable (the SSO session is shared across the single portal `d-93676bf05c.awsapps.com`). Run this proactively at the start of any investigation that will need AWS access (CloudTrail, CloudWatch, EKS, etc.).

### Wiz Authentication

The Wiz auth file is stored at `C:\Users\ClintonHerring\AppData\Local\Wiz\auth.json` (NOT the default `~/.wiz/auth.json`). When using the wiz_api.sh script, you must set the `WIZ_AUTH_FILE` environment variable:
```bash
export WIZ_AUTH_FILE="C:/Users/ClintonHerring/AppData/Local/Wiz/auth.json"
```

To authenticate (opens browser for device code flow):
```bash
wizcli auth --use-device-code
```

Since the wiz_api.sh script requires Git Bash (not PowerShell), run Wiz queries via a temp script or use:
```bash
& "C:\Program Files\Git\bin\bash.exe" <script.sh>
```

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

#### Blast Radius Check: App-Level vs Platform-Level?

**Before diving into any specific service**, determine whether the incident is isolated to one service or affecting many. This single query can save hours of misdirected investigation:

```bash
# Count errors by service across the ENTIRE cluster during the incident window
pup logs aggregate \
  --query="status:error" \
  --from="<incident-start-minus-30min>" \
  --to="<incident-end-plus-30min>" \
  --compute="count" \
  --group-by="service" \
  --storage=flex
```

**Interpret the results:**
- **1-2 services spiking** → app-level issue. Proceed with the service-specific investigation below.
- **Many unrelated services spiking simultaneously** → **shared infrastructure issue**. The root cause is NOT in any individual application. Pivot immediately to shared layers:
  - **Helm charts**: `helm-charts/basic-application` -- the shared chart used by most OneEKS services. Check recent releases/tags.
  - **Istio/service mesh**: Istio control plane issues, VirtualService CRD changes.
  - **Cluster-level events**: Node scaling, cluster upgrades, KEDA/Kyverno policy changes.
  - **Shared dependencies**: DNS (Route53), shared databases, message brokers.
  - **Platform announcements**: Check `#announce-platform` and `#announce-oneeks` Slack channels for known issues.

Use the Datadog Orchestration Explorer to confirm blast radius across a shared component:
```bash
# Check if many pods share the same failing Helm chart version
pup logs aggregate \
  --query="status:error AND label#helm.sh/chart:<chart-name-and-version>" \
  --from="<start>" --to="<end>" \
  --compute="count" \
  --group-by="service" \
  --storage=flex
```

This check is critical because PI tickets are usually filed by the team that notices the problem first, naming only *their* services. The root cause often lies in a shared layer that affects everyone. (See PI-34282 worked example below.)

#### Start Broad: Get the Initial Picture

Run these in parallel to see what's going on:

**Datadog -- error landscape:**
```bash
# Broad error count by service during incident window (also serves as blast radius check above)
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
**Symptoms**: 403 errors, "access denied" to AWS resources, SSO failures
**Check first**: IFA/jet-aws-sso PRs, CloudTrail IAM events, Wiz issues on the affected resource
**Common causes**:
- SSO permission set changes
- IAM policy modifications
- IRSA (IAM Roles for Service Accounts) configuration changes
- Security policy enforcement (Wiz-detected misconfigurations leading to automated remediation)
**Key Datadog query**: `*AccessDenied* OR *403* OR *not authorized* OR *AssumeRole*`

### ZScaler / Cloudflare / Network-Layer Access Issues
**Symptoms**: Intermittent Cloudflare timeout errors, "connection timed out" from Cloudflare, internal tools inaccessible for some users but not others, issues that come and go randomly
**Check first**: ZScaler ZPA app-segment and app-connector configuration, Cloudflare origin settings in IFA/cloudflareplatformproduction, Route53 CNAME chains
**Common causes**:
- **ZPA App Connector DNS misconfiguration**: ZPA Server Groups load-balance across multiple App Connector Groups (e.g., production `-p-` and disaster recovery `-d-`). If one group has incorrect `/etc/resolv.conf` entries, requests hitting that group fail DNS resolution while the other group works fine -- producing intermittent failures that look random. (See PI-34099.)
- **Stale Cloudflare origins after decommissioning**: When backend services like WAPS are decommissioned, Cloudflare CNAME records may still point to the dead origin. The service may appear to work intermittently if ZScaler sometimes resolves via internal DNS (bypassing Cloudflare) and sometimes via Cloudflare (hitting the dead origin).
- **ZScaler DNS caching**: After Route53 fixes, ZScaler/ZPA may hold stale DNS records. This is not simple TTL caching -- it's related to how ZPA app-connectors handle CNAME resolution via Windows DNS servers on the connector host. Machine reboots or ZScaler service restarts may be needed.
- **App-segment-specific DNS hiding**: ZPA app-segments with bespoke configurations can hide the CNAME chain from standard `dig` lookups. You need to query using the resolver used by the ZScaler app-connector to see the real resolution chain.
**Key investigation approach**: Datadog will likely show **nothing** for these incidents because the affected services are internal web apps accessed via browsers that don't emit application logs. The failure is in the DNS/networking layer between the user and the service. Instead, check:
1. Jira ticket comments and Slack threads for the real investigation details
2. ZScaler ZPA admin console for app-connector and app-segment configuration
3. Route53 for CNAME chains that pass through Cloudflare
4. IFA/cloudflareplatformproduction for origin configurations pointing to decommissioned services
**Key Datadog query**: Usually returns nothing -- this is itself a diagnostic signal (see Tips)

### Shared Infrastructure / Helm Chart Failures
**Symptoms**: Multiple unrelated services failing simultaneously, canary deployments stuck or failing, `invalidSpec` errors in pod events, rollout failures across teams
**Check first**: `helm-charts/basic-application` releases/tags, Argo Rollouts status, Istio control plane, cluster node events, `#announce-platform` / `#announce-oneeks` Slack channels
**Common causes**:
- **Helm chart regression**: A new release of `basic-application` (the shared Helm chart) introduces a spec error that breaks all canary deployments. Pods fail with `invalidSpec` or similar CRD validation errors. (See PI-34282.)
- **Istio/service mesh update**: Control plane upgrade or sidecar injection changes cause widespread networking failures.
- **Cluster-level event**: Node pool scaling, Kubernetes version upgrade, KEDA operator update, Kyverno policy change.
- **Shared dependency outage**: A database, message broker, or external API used by many services goes down simultaneously.
**Key diagnostic**: Run the blast radius check (Phase 2) first. If 5+ unrelated services spike errors at the same time, stop investigating individual services and focus on shared layers.
**Key Datadog query**: `*invalidSpec* OR *FailedCreate* OR *rollout* OR *canary*` grouped by service; also check Orchestration Explorer with `label#helm.sh/chart:<chart-version>`

### Security / Misconfiguration
**Symptoms**: Unexpected resource behavior, access patterns changing, compliance-driven service disruption
**Check first**: Wiz open issues on the affected component/project, recent Wiz issue status changes
**Common causes**:
- Automated remediation of a Wiz-detected misconfiguration (e.g., public access revoked, encryption enforced)
- Vulnerability patching causing service restart or incompatibility
- Security group / network policy tightened due to a Wiz finding
**Key Wiz query**: `wiz_list_issues --project-name "<component>" --status OPEN,IN_PROGRESS,RESOLVED --severity CRITICAL,HIGH --limit 25` (include RESOLVED to see recently-fixed issues that may have caused disruption)

## Key IFA Repositories Reference

| Repository | Purpose | Check for |
|---|---|---|
| `IFA/route53` | DNS record management (Terraform) | DNS-related outages |
| `IFA/domain-routing` | Domain routing configuration | DNS routing / service discovery issues |
| `IFA/cloudflareplatformproduction` | Cloudflare production config | CDN/WAF/DNS proxy issues |
| `IFA/cloudflareplatformstaging` | Cloudflare staging config | Staging DNS issues |
| `IFA/aws-infrastructure` | Core AWS infra (VPCs, TGWs, SGs) | Networking issues |
| `IFA/jet-aws-sso` | AWS SSO / IAM config | Auth/permission failures |
| `IFA/puppet7-control-*` | Puppet config management | ProxySQL, server config |
| `helm-charts/basic-application` | Shared Helm chart for OneEKS services | Canary/rollout failures across multiple services |

All IFA repositories: `https://github.je-labs.com/orgs/IFA/repositories`

## Tips

- **Timing is everything**: The most powerful signal is a change that was merged/applied minutes before the first error. Always sort PRs by merge time and compare with Datadog error timestamps.
- **Negative DNS caching**: A 2-minute DNS gap can cause a 30-minute outage. When DNS is involved, the duration of the record being missing is NOT the duration of the outage.
- **Check staging too**: Staging ProxySQL/infra issues (e.g., PI-31994) sometimes indicate production risk.
- **Follow the links**: PI tickets often have linked retro tickets, related PIs, and follow-up tasks that contain the actual root cause analysis.
- **Console changes are invisible in code**: Always check CloudTrail for manual AWS console changes that bypass the IaC pipeline.
- **Terraform apply != PR merge**: In IaC repos, the infrastructure change happens at `terraform apply` time during CI, which can be well before the PR is merged -- or the PR may never be merged at all. A partial apply on an unmerged PR can cause an outage, and a subsequent apply on a different PR can silently revert the change, making the root cause hard to trace from diffs alone. Always check CI run history and apply logs.
- **Vault credentials**: Username patterns like `v-kubernetes-*` indicate Vault-issued dynamic credentials. If these get "access denied", the issue is usually at the ProxySQL layer, not the database.
- **Wiz as a resource map**: Wiz knows which AWS accounts, regions, and subscriptions resources live in. When you have a service name but don't know which account to query CloudTrail or CloudWatch in, use Wiz graph search to find the resource and read its `subscriptionExternalId` (AWS account ID), `subscriptionName`, and `region`. Wiz also maps dependencies -- what databases, queues, buckets, and endpoints a service connects to -- which helps identify blast radius and trace failures across service boundaries.
- **Datadog silence is a signal**: If Datadog returns zero logs for an affected service, that's diagnostic information -- it likely means the failure is in the network/DNS/proxy layer *before* traffic reaches the application. Internal web tools (Invoicing Management, Customer Management, Payment Management, etc.) often don't emit logs to Datadog at all. When you see this pattern, pivot immediately to Jira comments, ZScaler/ZPA configuration, Cloudflare settings, and Route53 CNAME chains instead of trying more Datadog queries.
- **Intermittent failures suggest load-balanced infrastructure**: When users report random success/failure for the same service, think about what sits in the path that load-balances: ZPA App Connector Groups (round-robin across production and DR connectors), Cloudflare edge nodes, internal DNS servers. If one member of a pool is misconfigured, you get intermittent failures proportional to the pool ratio.
- **Decommissioning creates time bombs**: When a backend service (WAPS, old LBs, etc.) is decommissioned, all DNS records, Cloudflare origins, and ZScaler app-segments pointing to it must be audited across all markets. The service may appear to keep working for weeks/months if there are alternative resolution paths, then suddenly break when the alternative path changes.
- **Blast radius before deep-dive**: PI tickets name only the services the filing team cares about. Always check whether *other* services are failing simultaneously before spending time on the named services' dependencies. Simultaneous 5XX spikes across unrelated services = shared infra layer (Helm chart, Istio, cluster, DNS), not an application dependency. (Lesson from PI-34282.)

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

## Worked Example: PI-34099 -- ZScaler App Connector DNS Failure

This example illustrates an incident where Datadog was a dead end and the root cause was found entirely through Jira comments and ZScaler configuration investigation.

### The Incident

**Summary**: Intermittent Cloudflare timeout errors for agents accessing Invoicing Management, Customer Management, and Payment Management across UK, IE, IT, and ES markets.

**Initial symptoms**: 15 UK agents and 7 IE agents couldn't access Invoicing Management. Cloudflare error pages shown intermittently.

### Investigation Path

**Step 1: Jira ticket** -- Established the timeline and affected services. The ticket identified three components: invoicemanagement, customermanagement, paymentmanagement. Markets: UK, IE, IT.

**Step 2: Datadog** -- Searched for error logs across all three services. **Result: zero logs.** No application errors, no Cloudflare logs, no ZScaler logs in Datadog. This was the key signal -- the failure was in the network layer before traffic reached the applications.

**Step 3: Initial (wrong) hypothesis** -- WAPS decommissioning. The team discovered that Cloudflare origins for these services still pointed to `waps.just-eat.com`, which was decommissioned in April. Route53 records for UK/IT pointed through Cloudflare CDN while ES/IE pointed directly to internal LBs. This seemed like the root cause.

**Step 4: Fix applied but problems continued** -- Route53 records were updated to bypass Cloudflare and point directly to internal endpoints (e.g., `invoicingmanagement.internal.je-apis.com`). However, ZScaler DNS caching prevented immediate resolution. Users needed machine reboots.

**Step 5: The real root cause (from Jira comments)** -- Fredrik Wilandh's investigation revealed that the ZScaler ZPA Server Group `JET-IE-Apps` contained two App Connector Groups:
- `aws-networks-ew1-p-zac-grp-v2` (production) -- healthy, correct DNS
- `aws-networks-ew1-d-zac-grp-v2` (disaster recovery) -- **broken `/etc/resolv.conf`**

ZPA load-balances round-robin across both groups. Requests hitting the DR connectors failed DNS resolution; requests hitting production connectors succeeded. This explained the intermittent nature perfectly.

**Fix**: Manually corrected `/etc/resolv.conf` on the affected DR App Connectors. Permanent remediation: migrate app-segments to a Server Group using App Connectors in the Networks production VPC (`10.18.0.0/16`).

### Key Lessons from This Incident

1. **Datadog returning nothing IS the finding** -- don't keep trying more queries. Pivot to other sources.
2. **Jira comments contain the real RCA** -- the ticket timeline had the initial (incomplete) hypothesis, but the comment from Fredrik had the actual root cause. Always read comments.
3. **Intermittent = load-balanced infrastructure** -- random success/failure across users pointed to a pool with a broken member.
4. **The obvious cause wasn't the real cause** -- WAPS decommissioning was a contributing factor (stale Cloudflare config) but the actual trigger was the DR App Connector DNS misconfiguration.
5. **Scope expands** -- what started as one service (Invoicing Management) in one market (UK) turned out to affect three services across four markets. Always check related services when you find a network-layer root cause.

## Worked Example: PI-34282 -- Shared Helm Chart Breaking All Canary Deployments

This example illustrates a platform-wide incident where the PI ticket named only two services, but the root cause was a shared Helm chart regression affecting all OneEKS applications. It demonstrates why the **blast radius check** must come before service-specific investigation.

### The Incident

**Summary**: AutocompleteAPI and AddressGeocodingAPI returning 5XX errors in production (UK, AU, NZ markets). PI ticket named these two location-services components.

**Incident window**: 2025-05-15, first errors ~08:25 BST, alert at 08:28, PI created 08:40, resolved ~10:30 BST.

### Investigation Path

**Step 1: Jira ticket** -- Established the affected services (autocompleteapi, addressgeocodingapi) and timeline. Comments showed the team initially investigating their own services and their shared dependency, GeodataAPI.

**Step 2: Wrong path -- service-specific deep-dive** -- Investigation anchored on the two named services and their dependency chain. Found that GeodataAPI had a recent PR (#1099, OpenRasta removal) and database connection errors. This looked plausible as a root cause: GeodataAPI down → autocompleteapi/addressgeocodingapi fail. **This was a coincidence, not the cause.**

**Step 3: Blast radius check (should have been Step 2)** -- Querying Datadog errors across ALL services revealed that **many unrelated services** were failing simultaneously: PartnerListingAPI, DishSearchAPI, SmartGateway, and others. These services have no dependency on GeodataAPI. This immediately ruled out an application-level root cause.

**Step 4: Shared infrastructure investigation** -- With the blast radius established, focus shifted to shared layers. The common factor: all affected services were on OneEKS and used the `basic-application` Helm chart. Checking the Helm chart repository revealed:
- `basic-application` v1.1.29 was released shortly before the incident
- The chart introduced a spec error that caused `invalidSpec` errors on canary deployments
- Any service that attempted a canary rollout after the chart update failed

**Step 5: Confirmation** -- Datadog Orchestration Explorer filtered by `label#helm.sh/chart:basic-application-1.1.29` showed widespread pod failures. Platform announcements confirmed the issue. Fix was `basic-application` v1.1.30, released ~10:15 BST.

### Key Lessons from This Incident

1. **Blast radius check FIRST** -- If the first query had been "how many services are erroring?" instead of "what's wrong with autocompleteapi?", the shared-infra root cause would have been obvious within minutes. The PI ticket naming only two services was misleading.
2. **Simultaneous failures across unrelated services = shared layer** -- AutocompleteAPI, PartnerListingAPI, and DishSearchAPI have no common application dependency. When they all fail at the same time, the cause must be in a layer they all share: Helm chart, Istio, cluster, or DNS.
3. **Coincidental failures are traps** -- GeodataAPI genuinely had database issues during the same window. This made it look like the root cause for the location-services failures. But correlation is not causation -- the blast radius check disproves this by showing non-location-services also failing.
4. **Helm charts are shared infrastructure** -- `basic-application` is used by most OneEKS services. A single bad release can break every service that does a canary deployment. Treat Helm chart releases like cluster-level changes.
5. **Check `#announce-platform` early** -- Platform teams often know about shared-infra issues before individual service teams do. A quick Slack check can short-circuit hours of investigation.
