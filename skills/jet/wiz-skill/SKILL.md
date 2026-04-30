---
name: wiz-skill
description: Wiz cloud security platform integration for retrieving and analyzing vulnerability findings and security issues. Use this skill when working with Wiz issue URLs (app.wiz.io), investigating security vulnerabilities, reviewing Wiz findings, generating vulnerability priority reports for teams, remediating cloud misconfigurations, or when the user references Wiz issues, CVEs, or security findings that need fixing.
metadata:
  owner: ai-platform
---

# Wiz Security Issues

Query the Wiz GraphQL API to retrieve security issues, vulnerabilities, cloud resources, and more. Authenticated through `wizcli` device code flow.

## Prerequisites

| Tool | Purpose | Installation (MacOS/Linux) | Installation (Windows PowerShell) |
|------|---------|----------------------------|------------------------|
| `wizcli` | Authentication and token refresh | `brew install wizcli` or download from Wiz portal | Download from the Wiz portal |
| `jq` | JSON processing | `brew install jq` | `winget install jqlang.jq` |
| `curl` | HTTP requests | Pre-installed on macOS/Linux | `winget install cURL.cURL` |

## Authentication

```bash
# Authenticate (opens browser for SSO)
wizcli auth --use-device-code
```

Credentials are stored in `~/.wiz/auth.json`. Token TTL is ~15 minutes; the helper script auto-refreshes via `wizcli`. If the refresh token has expired, it prompts re-authentication.

### Re-authentication

When the helper script prints `Error: Token refresh failed`, the refresh token has expired. Re-authenticate manually:

```bash
# This is a BLOCKING command — use a long timeout (120s+) so the user has time to authenticate
wizcli auth --use-device-code
```

Show the user the device code URL and code from the output, then wait for them to complete browser auth.

## Quick Usage

```bash
source /path/to/scripts/wiz_api.sh

# Fetch a single issue by ID or Wiz URL
wiz_get_issue "5c9fd9c2-ba97-41e4-acad-2df01def1585"
wiz_get_issue "https://app.wiz.io/issues#%7E%28...%7E%275c9fd9c2-...%29"

# Find a project by team/service name (do this first when user gives a team name)
wiz_search_projects "<project-name>"

# List issues by project name (auto-resolves to project UUID)
wiz_list_issues --project-name "<project-name>" --status OPEN --severity CRITICAL,HIGH --limit 25

# List issues with filters (status: OPEN|IN_PROGRESS|RESOLVED|REJECTED, severity: CRITICAL|HIGH|MEDIUM|LOW|INFORMATIONAL)
wiz_list_issues --status OPEN --severity CRITICAL,HIGH --limit 10

# Prioritized vulnerability report for a team (compact)
wiz_vuln_report "<team-name>"
wiz_vuln_report "<team-name>" --has-fix              # only vulns with a fix available
wiz_vuln_report "<team-name>" --has-fix --has-exploit # only fixable + exploitable

# Full vulnerability analysis report (detailed tables, more tiers)
wiz_vuln_report_full "<team-name>"

# Run any GraphQL query
wiz_query 'query { issue(id: "UUID") { id status severity } }' '{}'
```

**When a user asks about issues for a team or service name, always use `--project-name` first** — Wiz projects map to teams, not to individual resource names.

## Exploring the Wiz GraphQL API

The Wiz API is a full GraphQL API at `https://api.<data_center>.app.wiz.io/graphql`. Beyond the convenience functions above, you can use `wiz_query` with introspection to explore the schema and build queries for any use case.

### API conventions

- **List queries** follow the pattern: `(first: Int, after: String, filterBy: <Type>Filters, orderBy: <Type>Order)` with paginated results via `pageInfo { hasNextPage endCursor }`
- **Singular queries** use `(id: ID!)` for direct lookup
- **Filter types** are named `<Entity>Filters` (e.g., `IssueFilters`, `VulnerabilityFilters`)
- **Always start with small `first` values** (5-10) to avoid huge responses
- **Use `jq`** to extract relevant fields from JSON responses

### Schema introspection

Use these patterns to discover what's available:

```bash
# Find queries matching a keyword (e.g., "vuln", "cloud", "issue")
wiz_query '{ __type(name: "Query") { fields { name args { name type { name kind ofType { name } } } } } }' '{}' \
  | jq '[.data.__type.fields[] | select(.name | test("vuln"; "i")) | {name, args: [.args[].name]}]'

# List all fields on a type (e.g., Issue, Vulnerability, CloudAccount)
wiz_query '{ __type(name: "Issue") { fields { name type { name kind ofType { name kind ofType { name } } } } } }' '{}' \
  | jq '[.data.__type.fields[] | {name, type: (.type.name // .type.ofType.name // .type.ofType.ofType.name)}]'

# Inspect a filter/input type to see what you can filter by
wiz_query '{ __type(name: "IssueFilters") { inputFields { name type { name kind ofType { name } } } } }' '{}' \
  | jq '[.data.__type.inputFields[] | {name, type: (.type.name // .type.ofType.name)}]'

# List valid values for an enum type
wiz_query '{ __type(name: "Severity") { enumValues { name } } }' '{}' \
  | jq '[.data.__type.enumValues[].name]'
```

### Key query domains

| Domain | Singular | List | Filters type |
|--------|----------|------|-------------|
| **Issues** | `issue(id)` | `issuesV2(filterBy, first, after, orderBy)` | `IssueFilters` |
| **Vulnerabilities (CVEs)** | `vulnerability(id)`, `vulnerabilityByExternalId(externalId)` | `vulnerabilities(filterBy, first, after, orderBy)` | `VulnerabilityFilters` |
| **Vulnerability findings** | `vulnerabilityFinding(id)` | `vulnerabilityFindings(filterBy, first, after, orderBy)` | `VulnerabilityFindingFilters` |
| **Cloud accounts** | `cloudAccount(id)` | `cloudAccounts(filterBy, first, after)` | `CloudAccountFilters` |
| **Projects** | `project(id)` | `projects(filterBy, first, after)` | `ProjectFilters` |
| **Controls** | `control(id)` | `controls(filterBy, first, after)` | `ControlFilters` |
| **Cloud config rules** | `cloudConfigurationRule(id)` | `cloudConfigurationRules(filterBy, first, after)` | `CloudConfigurationRuleFilters` |
| **Security frameworks** | `securityFramework(id)` | `securityFrameworks(filterBy, first, after)` | `SecurityFrameworkFilters` |
| **Graph search** | `graphEntity(id)`, `graphEntityByProviderUniqueId(...)` | `graphSearch(query, first, after)` | `GraphEntityQueryInput` |
| **Container images** | `containerImage(id)` | `containerImages(filterBy, first, after)` | `ContainerImageFilters` |
| **Attack surface** | `attackSurfaceFinding(id)` | `attackSurfaceFindings(filterBy, first, after)` | `AttackSurfaceFindingFilters` |
| **Data findings** | `dataFinding(id)` | `dataFindings(filterBy, first, after)` | `DataFindingFilters` |
| **Host config** | `hostConfigurationRule(id)` | `hostConfigurationRules(filterBy, first, after)` | `HostConfigurationRuleFilters` |

### Example queries

**Look up a CVE:**
```bash
wiz_query 'query ($f: VulnerabilityFilters) {
  vulnerabilities(filterBy: $f, first: 1) {
    nodes { id name severity description exploitable hasCisaKevExploit epssProbability baseScore }
  }
}' '{"f":{"name":"CVE-2024-3094"}}'
```

**Graph search — find resources by name:**
```bash
wiz_query 'query {
  graphSearch(query: {type: [SERVERLESS], where: {name: {CONTAINS: ["<service-name>"]}}}, first: 10) {
    totalCount
    nodes { entities { id name type properties } }
  }
}' '{}'
```

**Graph search — find connected resources (use `select: true` on the `with` clause to return connected entities):**
```bash
wiz_query 'query {
  graphSearch(query: {type: [SERVERLESS], where: {name: {EQUALS: ["<service-name>"]}},
    relationships: [{type: [{type: ANY_OUTGOING}], with: {type: [DATABASE, BUCKET, ENDPOINT, MESSAGING_SERVICE], select: true}}]
  }, first: 20) {
    nodes { entities { id name type } }
  }
}' '{}'
```

### Graph search reference

**Common entity types** (full list: introspect `GraphEntityType` enum):

| Type | Description |
|------|-------------|
| `SERVERLESS` | Lambda/Cloud Functions |
| `VIRTUAL_MACHINE` | EC2/VMs |
| `CONTAINER` | Running containers |
| `CONTAINER_IMAGE` | Container images |
| `DATABASE` | DynamoDB/RDS/etc |
| `DB_SERVER` | Database servers |
| `BUCKET` | S3/GCS/Blob storage |
| `ENDPOINT` | HTTP/HTTPS endpoints |
| `API_GATEWAY` | API Gateways |
| `MESSAGING_SERVICE` | SQS/SNS/EventBridge (NOT "QUEUE" or "TOPIC") |
| `SECRET` | Secrets Manager/SSM |
| `SERVICE_ACCOUNT` | IAM roles/service accounts |
| `USER_ACCOUNT` | IAM users |
| `REPOSITORY` | Code repositories |
| `KUBERNETES_CLUSTER` | K8s clusters |
| `LOAD_BALANCER` | ALB/NLB/etc |
| `SUBSCRIPTION` | Cloud accounts/subscriptions |

**Common relationship types** (full list: introspect `GraphRelationshipType` enum):

`ANY` | `ANY_OUTGOING` | `USES` | `CALLS` | `INVOKES` | `CONNECTED_TO` | `CONTAINS` | `RUNS` | `HOSTS` | `READS_DATA_FROM` | `STORES_DATA_IN` | `SEND_MESSAGES_TO` | `ACTING_AS` | `EXPOSES` | `DEPLOYED_TO`

**Pitfalls:** `QUEUE`/`TOPIC` types don't exist (use `MESSAGING_SERVICE`). `CONNECTS_TO` doesn't exist (use `CONNECTED_TO`). `select: true` goes on the `with` clause inside `relationships` (NOT on the parent query) — this makes `nodes.entities` return the connected resources instead of the source. `type` is required in `GraphEntityQueryInput` — always specify it. Multi-type queries can timeout — query one entity type at a time.

### Exploration workflow

When you need to answer a question not covered by the convenience functions:

1. **Identify the domain** — which entity are you looking for? (see table above)
2. **Introspect the filter type** — run `__type(name: "<Entity>Filters")` to see what filters are available
3. **Introspect the return type** — run `__type(name: "<Entity>")` to see what fields you can query
4. **Build a query** — use `wiz_query` with a small `first` value to test
5. **Refine** — add/remove fields, adjust filters based on results

### Finding service integrations

To find what a service connects to: search for it by name across key entity types (`BUCKET`, `SERVERLESS`, `ENDPOINT`, `DATABASE`, `API_GATEWAY`) **one type at a time** (multi-type queries timeout). Once you find the resource, use a relationship query with `type: [ANY]` or `type: [ANY_OUTGOING]` and `select: true` on the `with` clause to discover connected resources.

## Issue Fields Reference

When retrieving an issue, these fields are most useful for remediation:

### Remediation

| Field Path | Description |
|---|---|
| `issue.severity` | `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `INFORMATIONAL` |
| `issue.status` | `OPEN`, `IN_PROGRESS`, `RESOLVED`, `REJECTED` |
| `issue.control.name` | Short name of the security control that triggered the issue |
| `issue.control.description` | Detailed description of what the issue is and why it matters |
| `issue.control.resolutionRecommendation` | Step-by-step remediation guidance (markdown) |
| `issue.control.sourceCloudConfigurationRule.remediationInstructions` | Specific remediation steps for cloud config rules |
| `issue.control.securitySubCategories` | Framework mappings (e.g., Wiz Risk Assessment, Attack Surface Management) |

### Affected resource

| Field Path | Description |
|---|---|
| `issue.entitySnapshot.name` | Resource name or endpoint URL |
| `issue.entitySnapshot.type` | Resource type (e.g., `ENDPOINT`, `VIRTUAL_MACHINE`, `BUCKET`) |
| `issue.entitySnapshot.nativeType` | Cloud-native resource type |
| `issue.entitySnapshot.cloudPlatform` | `AWS`, `Azure`, `GCP`, etc. |
| `issue.entitySnapshot.providerId` | Cloud provider resource identifier (e.g., ARN) |
| `issue.entitySnapshot.region` | Cloud region |
| `issue.entitySnapshot.subscriptionExternalId` | AWS account ID / Azure subscription / GCP project |
| `issue.entitySnapshot.subscriptionName` | Human-readable account/subscription name |
| `issue.entitySnapshot.tags` | Resource tags (JSON object) |

### Context

| Field Path | Description |
|---|---|
| `issue.project.name` | Wiz project name |
| `issue.project.slug` | Wiz project slug |
| `issue.serviceTickets` | Linked Jira/ServiceNow tickets (`externalId`, `name`, `url`) |
| `issue.createdAt` | When the issue was first detected |

## Workflow: Investigating and Remediating an Issue

1. **Fetch the issue** using `wiz_get_issue` with the URL or ID
2. **Read** `control.description` to understand what the issue is
3. **Read** `control.resolutionRecommendation` for remediation steps
4. **Identify the resource** from `entitySnapshot` (name, cloud platform, region, account)
5. **Check for linked tickets** in `serviceTickets` (may have a Jira ticket with additional context)
6. **Apply the fix** based on the remediation guidance and affected resource details

## Vulnerability Reports

Generate prioritized vulnerability reports for a team/project. These query `vulnerabilityFindings` (not issues) and group CVEs by risk priority.

### `wiz_vuln_report` -- Quick prioritized report

```bash
wiz_vuln_report "<team-name>" [--has-fix] [--has-exploit]
```

Shows CVEs grouped into 4 priority tiers:
1. **CISA KEV** -- actively exploited in real attacks (patch immediately)
2. **CRITICAL + known exploit** -- critical severity with a public exploit
3. **HIGH + known exploit** -- high severity with a public exploit (top 10 by instance count)
4. **HIGH, no fix** -- high severity with no fix available (monitor/mitigate)

Plus a severity summary. Use `--has-fix` to focus on actionable vulns, `--has-exploit` to focus on exploitable ones.

### `wiz_vuln_report_full` -- Comprehensive analysis

```bash
wiz_vuln_report_full "<team-name>"
```

Formatted report with:
- Severity breakdown (CRITICAL/HIGH/MEDIUM/LOW counts)
- 5 priority tiers (adds MEDIUM+exploit and no-fix-available tiers)
- Top 10 most common vulnerabilities by instance count
- Tabular output with CVE, CVSS score, fix availability, and instance counts

### When to use which

| Scenario | Function |
|----------|----------|
| Quick triage, "what should we fix first?" | `wiz_vuln_report` |
| Actionable items only | `wiz_vuln_report --has-fix` |
| Full security review or reporting | `wiz_vuln_report_full` |
| Specific CVE lookup | `wiz_query` with `vulnerabilities` or `vulnerabilityFindings` |
