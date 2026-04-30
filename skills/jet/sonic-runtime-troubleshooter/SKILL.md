---
name: sonic-runtime-troubleshooter
description: Troubleshoot unhealthy applications running on Sonic Runtime (OneEKS). Use when investigating pod failures, application errors, deployment issues, network access issues or performance problems in OneEKS clusters. Triggers on requests to debug, troubleshoot, investigate, or diagnose issues with components running on Sonic Runtime, OneEKS, or EKS clusters at JET. Requires environment name and component backstage id.
metadata:
  owner: core-platform-services-ca-uk
---

# OneEKS Component Troubleshooting

Troubleshoot applications running on Sonic Runtime (OneEKS) by systematically investigating Kubernetes cluster state, pod health, container logs, and Datadog telemetry (APM, logs, monitors, error tracking).

## Safety Rules

- **All read operations do NOT require user confirmation** — freely run kubectl get/describe/logs, Datadog queries, etc.
- **All write operations REQUIRE explicit user confirmation** — never patch, delete, scale, restart, or modify Kubernetes resources without asking first
- Examples of write operations requiring confirmation: `kubectl delete pod`, `kubectl rollout restart`, `kubectl patch`, `kubectl scale`, `kubectl set image`, `kubectl apply`, `kubectl edit`

## Prerequisites

### Required Tools

| Tool      | Verify          | Purpose |
|-----------|-----------------|---------|
| `kubectl` | `which kubectl` | Kubernetes CLI |
| `aws`     | `which aws`     | AWS CLI — for STS identity verification and kubeconfig updates |
| `pup`     | `which pup`     | Datadog CLI (v0.37+) — for logs, APM, monitors, events |
| `gh`      | `which gh`      | GitHub CLI — for fetching files from GitHub Enterprise |

For every tool name kubectl, aws, pup check if we have it using verify command from table above.
If not found ask user to install tool or provide full path to it.

### Authentication Requirements

- **AWS SSO**: Active AWS session (see "Phase 2" below for details)
- **Datadog**: Authenticated via `pup auth login` with `DD_SITE=datadoghq.eu`
- **GHE**: Authenticated via `gh auth login --hostname github.je-labs.com`

Verify Datadog auth:
```bash
DD_SITE=datadoghq.eu pup auth status
```
Use skill jet-datadog to authenticate if needed.

Verify GHE auth:
```bash
gh auth status
```
Use skill jet-company-standards to authenticate if needed.

## User Inputs Required

Before starting troubleshooting, collect from the user:

1. **Environment name** (required) — e.g., `euw1-pdv-qa-2`, `euw1-pdv-stg-6`
2. **Component backstage id** (required) — e.g., `couriersupportsendbirdadapter`. Note: it should have only letters a-z, i.e. ^[a-z]+$ in regexp form.

Optional:
- **Symptom description** — error messages, timeframe, user-facing impact

## Workflow

### Phase 1: Get component repository and K8s namespace

#### Step 1.1: Get component repository

Get component configuration from https://github.je-labs.com/metadata/PlatformMetadata/tree/master/Data/global_features/[Component backstage id].json
From the JSON above obtain:
- ORG: .github_repository.owner
- REPO: .github_repository.name

COMPONENT_REPOSITORY = https://github.je-labs.com/<ORG>/<REPO>

#### Step 1.2: Get K8s namespace

The K8s namespace is defined in `helmfile.d/helmfile.yaml` (or `helmfile.d/helmfile.yaml.gotmpl`) under the `releases[].namespace` field. Fetch it with:

```bash
gh api repos/<ORG>/<REPO>/contents/helmfile.d/helmfile.yaml --hostname github.je-labs.com --jq '.content' | base64 -d
```

Look for `namespace:` under the `releases:` section. For example: `namespace: cu-payment-cfs-fin`.

If the file is `.yaml.gotmpl`, the namespace may use Go templating but is usually a plain string.

### Phase 2: Gain cluster access

Use jet-aws skill to get AWS credentials and configure kubectl to get access to EKS cluster.

### Phase 3: Identify unhealthy pods in the namespace using "kubectl get pods ..."

### Phase 4: Investigate unhealthy pods using kubectl

For each unhealthy pod identified, run the following **in parallel**:

#### Step 4.1: Run "kubectl describe pod ..."

#### Step 4.2: Get logs using "kubectl logs ..."

#### Step 4.3: Check events using "kubectl get events ..."

#### Step 4.4: Check controller

Sonic Runtime uses **Argo Rollouts**: use "kubectl get rollout ..."
Legacy EKS platforms use deployments: use "kubectl get deployment ..."

#### Step 4.5: Compare with healthy pods if any using "kubectl get pod ..."

#### Step 4.6: Fetch source repository and Helm configuration

All OneEKS apps have a `helmfile.d/` folder that configures values for the `basic-application` Helm chart (source: https://github.je-labs.com/helm-charts/basic-application, published to https://artifactory.takeaway.com/sre-helm-prod-virtual).

Use the `gh` CLI to fetch Helm configuration from COMPONENT_REPOSITORY and `helmfile.d/` folder. Use these commands to navigate the directory structure:

```bash
# List helmfile.d contents
gh api repos/<ORG>/<REPO>/contents/helmfile.d --hostname github.je-labs.com --jq '.[].name'

# Fetch a specific file (base64-decode the content field)
gh api repos/<ORG>/<REPO>/contents/helmfile.d/helmfile.yaml --hostname github.je-labs.com --jq '.content' | base64 -d

# Fetch values template
gh api repos/<ORG>/<REPO>/contents/helmfile.d/values/<COMPONENT>.yaml.gotmpl --hostname github.je-labs.com --jq '.content' | base64 -d

# Fetch state values (defaults + environment-specific)
gh api repos/<ORG>/<REPO>/contents/helmfile.d/state_values/defaults.yaml --hostname github.je-labs.com --jq '.content' | base64 -d

# List environment-specific state values directories (typically: eu1/, eu2/, na1/, oc1/)
gh api repos/<ORG>/<REPO>/contents/helmfile.d/state_values --hostname github.je-labs.com --jq '.[].name'

# Fetch environment-specific overrides
gh api repos/<ORG>/<REPO>/contents/helmfile.d/state_values/<BULKHEAD>/<ENV>.yaml --hostname github.je-labs.com --jq '.content' | base64 -d
```

Run the values template, defaults, and environment-specific state values fetches **in parallel** to save time.

### Phase 5: Extract Datadog Metadata

Before querying Datadog, extract the service name and tags from the pod labels:

```bash
kubectl get pod <POD_NAME> -n <NAMESPACE> -o jsonpath='{.metadata.labels}' | python3 -m json.tool
```

Key labels for Datadog correlation:
- `tags.datadoghq.com/service` — Datadog service name (usually same as component name)
- `tags.datadoghq.com/version` — application version
- `jet_envtype` — maps to `DD_ENV` (qa, stg, prd)
- `jet_env` — full environment name (e.g., `euw1-pdv-qa-2`)
- `jet_project` — namespace/project name

Additional Datadog tags available in logs/metrics:
- `kube_namespace:<NAMESPACE>`
- `kube_cluster_name:<ENVIRONMENT_NAME>`
- `kube_deployment:<COMPONENT_NAME>` (or `kube_argo_rollout`)
- `env:<ENVTYPE>` (qa, stg, prd)
- `service:<SERVICE_NAME>`

### Phase 6: Query Datadog

All pup commands require `DD_SITE=datadoghq.eu` prefix.

#### Step 6.1: Application error logs

Search logs (returns raw log entries):
```bash
# Errors for a specific service (always use --storage=flex for JET)
DD_SITE=datadoghq.eu pup logs search --query "service:<SVC> AND status:error" --from=1h --storage=flex --limit=50

# Errors across the whole namespace
DD_SITE=datadoghq.eu pup logs search --query "kube_namespace:<NS> AND status:error" --from=1h --storage=flex --limit=50

# Search for specific error patterns
DD_SITE=datadoghq.eu pup logs search --query "service:<SVC> AND (Exception OR OOMKilled OR CrashLoopBackOff)" --from=4h --storage=flex --limit=50
```

**Important**: If `status:error` queries return 0 results for a crashing service, remove the status filter and search all logs. Applications that crash during startup (e.g., missing config, dependency injection failures) often emit fatal error messages to stdout which Datadog ingests as `status:info` because no log-level parsing is configured. In that case use:
```bash
# All recent logs for the service (no status filter) — useful for startup crashes
DD_SITE=datadoghq.eu pup logs search --query "service:<SVC> AND kube_cluster_name:<CLUSTER>" --from=1h --storage=flex --limit=20
```

Count errors (returns aggregated counts — prefer this over fetching all logs):
```bash
# Total error count for a namespace
DD_SITE=datadoghq.eu pup logs aggregate --query "kube_namespace:<NS> AND status:error" --from=4h --storage=flex --compute=count

# Error count grouped by service
DD_SITE=datadoghq.eu pup logs aggregate --query "kube_namespace:<NS> AND status:error" --from=4h --storage=flex --compute=count --group-by=service

# Grouped by service AND status (comma-separated fields)
DD_SITE=datadoghq.eu pup logs aggregate --query "kube_namespace:<NS>" --from=4h --storage=flex --compute=count --group-by=service,status --limit=20
```

#### Step 6.2: APM traces and service health

```bash
# List all APM services (--env uses jet_envtype: prd, stg, qa)
DD_SITE=datadoghq.eu pup apm services list --env=prd --from=1h

# Get service stats (latency, error rate, throughput) — output includes latencyP50/P95/P99 in NANOSECONDS
# WARNING: This returns stats for ALL services in the environment (can be very large output).
# Always pipe through python3/jq to filter for the specific service:
DD_SITE=datadoghq.eu pup apm services stats --env=<ENVTYPE> --from=1h 2>&1 | python3 -c "
import json, sys
data = json.load(sys.stdin)
for svc in data.get('data', {}).get('attributes', {}).get('services_stats', []):
    if '<SERVICE_NAME>' in svc.get('service', '').lower():
        print(json.dumps(svc, indent=2))
"
```

Output structure for `apm services list`: `.data.attributes.services` is a flat list of service name strings.
Output structure for `apm services stats`: `.data.attributes.services_stats` is a list of objects with `service`, `operation`, `hits`, `latencyP50`, `latencyP99`, `requestPerSecond`, etc.

Search and aggregate APM traces directly:
```bash
# Search error spans for a service
DD_SITE=datadoghq.eu pup traces search --query "service:<SVC> AND status:error" --from=1h --limit=50

# Aggregate span counts by resource (endpoint) — NOTE: --compute is REQUIRED for traces aggregate (unlike logs aggregate which defaults to count)
DD_SITE=datadoghq.eu pup traces aggregate --query "service:<SVC>" --from=1h --compute=count --group-by=resource_name

# Aggregate error rate by status code
DD_SITE=datadoghq.eu pup traces aggregate --query "service:<SVC> AND status:error" --from=1h --compute=count --group-by=@http.status_code
```

#### Step 6.3: Monitors and alerts

```bash
# Search monitors by free text (searches name, query, message) — use for broad search
DD_SITE=datadoghq.eu pup monitors search --query "<NAMESPACE_OR_SERVICE>" --per-page=30

# List monitors filtered by tag — use for precise filtering (--limit default=200, max=1000)
DD_SITE=datadoghq.eu pup monitors list --tags="service:<SVC>"

# Filter by monitor name substring (--name does substring match)
DD_SITE=datadoghq.eu pup monitors list --name="<SUBSTRING>" --limit=50
```

**Note**: `monitors list --tags` returns empty (not an error) if no monitors have that exact tag. `monitors search --query` does full-text search across monitor definitions, which is more likely to find relevant monitors.

#### Step 6.4: Error tracking

```bash
# Search error-tracking issues for a service (--track is required: trace, logs, or rum)
DD_SITE=datadoghq.eu pup error-tracking issues search --query "service:<SVC>" --track=trace --from=7d --limit=10

# Get full details for a specific issue (search returns IDs + total_count only)
DD_SITE=datadoghq.eu pup error-tracking issues get <ISSUE_ID>
```

**Note**: `--track` and `--persona` are mutually exclusive. Use `--track=trace` for backend APM services, `--track=logs` for log-based errors, `--track=rum` for frontend. The `search` response only contains issue IDs and total_count — use `get` to retrieve full details (error_type, error_message, service, language, state).

#### Step 6.5: Recent events (deployments, config changes)

Two commands available — `events list` (v1 API) and `events search` (v2 API):

```bash
# events list: filter by tags (returns more results, v1 API)
# IMPORTANT: Always include kube_cluster_name tag to scope to the target cluster,
# otherwise events from ALL clusters with the same namespace will be returned
DD_SITE=datadoghq.eu pup events list --tags="kube_namespace:<NS>,kube_cluster_name:<CLUSTER>" --from=4h

# events list: combine source filter with tag filter
DD_SITE=datadoghq.eu pup events list --filter="source:kubernetes" --tags="kube_namespace:<NS>,kube_cluster_name:<CLUSTER>" --from=4h

# events search: filter by query string (v2 API, returns structured data)
DD_SITE=datadoghq.eu pup events search --query="kube_namespace:<NS> AND kube_cluster_name:<CLUSTER>" --from=4h --limit=50
```

**Note**: `events list` uses `--tags` and `--filter` flags (NOT `--query`) and has **no `--limit` flag**. `events search` uses `--query` flag and supports `--limit`. They return different JSON structures. The `--tags` flag accepts comma-separated tags (e.g., `--tags="kube_namespace:my-ns,kube_cluster_name:my-cluster"`).

#### Step 6.6: Kubernetes metrics

Two commands: `metrics search` (v1, returns pointlist arrays) and `metrics query` (v2, same output format). **Always prefer `metrics search`** — `metrics query` (v2 Timeseries API) is significantly slower and frequently times out (>30s) for queries with many series or wide time ranges.

**Known issue**: `metrics search` with `by {kube_deployment}` and `--from=4h` (or longer) may return `"error": "Timeseries query failed."` for some metrics (e.g., `kubernetes.containers.restarts`). **Workaround**: reduce the time range to `--from=1h` or remove the `by` clause. If you need a longer range, try without `by` first, then add `by` with `--from=1h`.

```bash
# Memory/CPU requests across a namespace
DD_SITE=datadoghq.eu pup metrics search --query "sum:kubernetes.memory.requests{kube_namespace:<NS>,kube_cluster_name:<CLUSTER>}" --from=1h
DD_SITE=datadoghq.eu pup metrics search --query "sum:kubernetes.cpu.requests{kube_namespace:<NS>,kube_cluster_name:<CLUSTER>}" --from=1h

# Break down by deployment (use "by {kube_deployment}")
DD_SITE=datadoghq.eu pup metrics search --query "sum:kubernetes.memory.requests{kube_namespace:<NS>,kube_cluster_name:<CLUSTER>} by {kube_deployment}" --from=1h

# HPA current vs max replicas
DD_SITE=datadoghq.eu pup metrics search --query "sum:kubernetes_state.hpa.current_replicas{kube_namespace:<NS>,kube_cluster_name:<CLUSTER>} by {horizontalpodautoscaler}" --from=1h
DD_SITE=datadoghq.eu pup metrics search --query "sum:kubernetes_state.hpa.max_replicas{kube_namespace:<NS>,kube_cluster_name:<CLUSTER>} by {horizontalpodautoscaler}" --from=1h

# Container restarts (use --from=1h to avoid "Timeseries query failed" errors; see known issue above)
DD_SITE=datadoghq.eu pup metrics search --query "sum:kubernetes.containers.restarts{kube_namespace:<NS>,kube_cluster_name:<CLUSTER>}" --from=1h
# Only add "by {kube_deployment}" if the above succeeds; group-by with wide time ranges may fail
DD_SITE=datadoghq.eu pup metrics search --query "sum:kubernetes.containers.restarts{kube_namespace:<NS>,kube_cluster_name:<CLUSTER>} by {kube_deployment}" --from=1h

# CPU/memory usage (actual, not requests)
DD_SITE=datadoghq.eu pup metrics search --query "avg:kubernetes.cpu.usage.total{kube_namespace:<NS>,kube_cluster_name:<CLUSTER>} by {kube_deployment}" --from=1h
DD_SITE=datadoghq.eu pup metrics search --query "avg:kubernetes.memory.usage{kube_namespace:<NS>,kube_cluster_name:<CLUSTER>} by {kube_deployment}" --from=1h
```

Output structure: `.data.series[]` — each series has `.expression`, `.metric`, `.pointlist` (array of `[timestamp_ms, value]`). Memory values are in **bytes**. CPU values are in **nanocores**.

### Phase 7: Check infrastructure context

#### Step 7.1: Run "kubectl get resourcequota ..."

#### Step 7.2: Run "kubectl get hpa ..."

#### Step 7.3: Run "kubectl get networkpolicy ..."

#### Step 7.4: Run "kubectl describe node ..." if pods are pending

### Phase 8: Plan and perform additional steps if needed

Based on the information obtained from the steps above decide if any other troubleshooting steps are needed. If the answer is yes - plan them and execute.
For example, if there are networking issues, you should check K8s service and Istio configuration.

### Phase 9: Summarize and recommend

After gathering all data, provide a structured summary. When remediation involves Helm configuration changes, always specify the exact file path and values to change in the component's repository.

```markdown
## Findings Summary

### Unhealthy Pods
| Component | Pod | Status | Duration | Root Cause |
|-----------|-----|--------|----------|------------|
| ... | ... | ... | ... | ... |

### Root Cause Analysis
<detailed explanation with evidence from kubectl describe, logs, and Datadog>

### Datadog Correlation
<what Datadog logs/APM/monitors showed, or why they showed nothing>

### Helm Configuration Changes
When the fix requires changing deployment configuration, specify exactly which file(s) and value(s) to change:

**Repository**: `github.je-labs.com/<ORG>/<REPO>`
**File**: `helmfile.d/values/<COMPONENT>.yaml.gotmpl` (or `helmfile.d/state_values/<FILE>.yaml`)
**Change**:
- `<yaml.path>`: `<old value>` → `<new value>`

Example for an OOMKilled Java app needing more memory:
- **File**: `helmfile.d/values/mycomponent.yaml.gotmpl`
- **Change**: `deployment.resources.limits.memory`: `256Mi` → `512Mi`
- **Change**: `deployment.resources.requests.memory`: `256Mi` → `512Mi`
- **Add** to `deployment.env`: `JAVA_TOOL_OPTIONS` with value `-XX:MaxRAMPercentage=75.0`

Note: Scaleops adjusts only resources requests, and never changes limits.

### Remediation Steps
<numbered steps, marking which require write access>

### Additional Recommendations
<preventive measures, monitoring suggestions>
```

## Sonic Runtime / OneEKS Architecture Notes

### Key Concepts
- **Bulkheads**: Isolated cluster environments — EU1, EU2, OC1, NA1
- **Projects/Namespaces**: A project maps 1:1 to a namespace across all bulkheads
- **Argo Rollouts**: Sonic uses Argo Rollouts (not Deployments) for progressive delivery
- **basic-application chart**: Standard Helm chart for all Sonic deployments
- **ScaleOps**: Automatic resource right-sizing (labels: `scaleops.sh/*`)
- **Karpenter**: Node provisioning (label: `karpenter_nodepool`)

### Namespace ResourceQuotas (cps/projects repo)

Namespace-level ResourceQuotas are **not** defined in the application's own repo. They are managed centrally in the **`cps/projects`** repository (`github.je-labs.com/justeat/cps-projects`):

- **Quota config files**: `projects/<bulkhead>/<namespace>.yml` (e.g., `projects/pdv/lm-dlv-proc-dl.yml`)
- **Terraform defaults**: `modules/namespace/variables.tf` defines default quotas:
  - `requests.cpu: 8`
  - `requests.memory: 32Gi`
  - `limits.memory: 32Gi`
- **Merge logic**: `modules/namespace/locals.tf` uses `merge(var.default_quotas, try(var.config.namespace.resource_quota, {}))` — project-specific overrides merge on top of defaults. **Any quota dimension not explicitly overridden keeps its default value.**
- **Terraform resources**: `modules/namespace/resource_control.tf` creates the actual K8s ResourceQuota and LimitRange objects
- **Common mistake**: When increasing some quotas (e.g., `limits.memory`, `requests.cpu`), engineers forget to also override `requests.memory`, leaving it at the 32Gi default

### ScaleOps vs ResourceQuota Interaction

ScaleOps and ResourceQuota operate at **different layers** and are enforced independently:

| Layer | Managed by | What it controls |
|---|---|---|
| Per-pod `resources.requests` | **ScaleOps** (automatic) | Right-sizes individual pod resource requests based on actual usage |
| Per-pod `resources.limits` | **Engineers** (in Helm values) | Hard ceiling per container; ScaleOps never changes limits |
| Namespace `ResourceQuota` | **Engineers** (in `cps/projects` repo) | Hard ceiling on **total** requests and limits across all pods in namespace |

**Critical**: Kubernetes admission controller enforces `requests.*` and `limits.*` quotas as **independent gates**. Even if `limits.memory` quota has room, pods will be rejected if `requests.memory` quota is exceeded. ScaleOps can reduce per-pod requests but **cannot change the namespace ResourceQuota** — that requires a PR to `cps/projects`.

### HPA Quota Overcommit Alert

A proactive alert that fires when worst-case HPA scaling would exceed the namespace ResourceQuota:

- **Runbook**: https://github.je-labs.com/PlatformEngineering/oneeksdocs/blob/main/docs/administer/runbooks/kubernetes/hpa-quota-overcommit.md
- **Schedule**: Weekly check, Monday 14:00 UTC
- **Calculation**: `worst_case = sum(HPA_maxReplicas × per_pod_resource_request)` for each deployment in the namespace
- **Fires when**: worst-case exceeds the corresponding ResourceQuota dimension (e.g., `requests.cpu`, `requests.memory`)
- **Auto-resolves**: On the next Monday 14:00 UTC check after the quota is increased or HPA maxReplicas are reduced
- **Key Datadog metrics for investigation**:
  - `kubernetes.memory.requests` / `kubernetes.cpu.requests` — actual resource requests summed across pods
  - `kubernetes_state.hpa.max_replicas` — HPA ceiling per deployment
  - `kubernetes_state.hpa.current_replicas` — current replica count

### Datadog Tagging Convention
Tags are applied via pod labels and picked up by the Datadog agent:
- `service` = `tags.datadoghq.com/service` label (= component name)
- `env` = `jet_envtype` label (qa, stg, prd)
- `version` = `tags.datadoghq.com/version` label
- `kube_namespace`, `kube_cluster_name`, `kube_deployment` auto-populated

### Image Registry
Image registry paths use the GitHub organization name as a prefix:
- Production images: `artifacts.takeaway.com/<GITHUB_ORG>-docker-prod-local/<component>:<tag>`
- Dev/PR images: `artifacts.takeaway.com/<GITHUB_ORG>-docker-dev-local/<component>/prs:pr-<N>`

The `<GITHUB_ORG>` corresponds to the GitHub organization that owns the repository. For example: `logistics-courier-support-automation-docker-prod-local/couriersupportsendbirdadapter:3`.

### Datadog Metrics Explorer Shareable URLs

When building Metrics Explorer links to share with developers, use the `exp_*` parameter format (NOT the `queries` JSON format):

```
https://app.datadoghq.eu/metric/explorer?exp_metric=kubernetes.memory.requests&exp_scope=kube_namespace%3A<NS>%2Ckube_cluster_name%3A<CLUSTER>&exp_agg=sum&exp_row_type=metric&from_ts=<EPOCH_MS>&to_ts=<EPOCH_MS>&live=false
```

Parameters:
- `exp_metric` — metric name (e.g., `kubernetes.cpu.requests`)
- `exp_scope` — URL-encoded comma-separated tags (e.g., `kube_namespace%3Amy-ns%2Ckube_cluster_name%3Amy-cluster`)
- `exp_agg` — aggregation function (`sum`, `avg`, `max`, `min`)
- `exp_row_type` — always `metric`
- `from_ts` / `to_ts` — epoch milliseconds
- `live` — `true` for live view, `false` for fixed time range

### Datadog Notebooks for Sharing Analysis

Use `pup notebooks create --file <path>.json` to create shareable Datadog Notebooks with annotated graphs. Useful for presenting quota overcommit analysis to developers with:
- Timeseries graphs with horizontal marker lines (e.g., quota limits, worst-case thresholds)
- Markdown cells explaining root cause and remediation
- Formula-based queries (e.g., converting bytes to Gi with `a / 1073741824`, or constant lines with `0 * a + <constant>`)

The notebook URL format is: `https://app.datadoghq.eu/notebook/<ID>`

## Integration with Other Skills

- **jet-datadog**: Provides the full pup CLI reference and Datadog query syntax
- **jet-company-standards**: For looking up components in GitHub Enterprise
- **jet-aws**: For authentication in AWS environment

## Quick Reference: Troubleshooting Checklist

```
1. [ ] Authenticate: aws sts get-caller-identity
2. [ ] Kubeconfig: aws eks update-kubeconfig --region <R> --name <ENV>
3. [ ] List pods: kubectl get pods -n <NS> -o wide
4. [ ] Identify unhealthy: status != Running/Completed, READY != expected, high restarts
5. [ ] For each unhealthy pod:
   a. [ ] kubectl describe pod — events, conditions, image, probes
   b. [ ] kubectl logs (current + --previous)
   c. [ ] kubectl get events -n <NS> --sort-by=.lastTimestamp
6. [ ] Check parent controller: kubectl get rollout / deployment
7. [ ] Compare with healthy pod if applicable
8. [ ] Fetch helmfile.d config from GHE (jet_repo annotation → gh api → read values template + state_values)
9. [ ] Extract DD service name from labels (tags.datadoghq.com/service)
10. [ ] DD logs: pup logs search --query "service:<SVC> AND status:error" --from=1h --storage=flex --limit=50
   [ ] If 0 results, retry WITHOUT status:error (startup crashes often log as status:info)
11. [ ] DD log count: pup logs aggregate --query "kube_namespace:<NS> AND status:error" --from=4h --storage=flex --compute=count --group-by=service
12. [ ] DD APM: pup apm services stats --env=<ENVTYPE> --from=1h
13. [ ] DD traces: pup traces aggregate --query "service:<SVC>" --from=1h --compute=count --group-by=resource_name
14. [ ] DD monitors: pup monitors search --query "<NS_OR_SVC>" --per-page=30
15. [ ] DD error-tracking: pup error-tracking issues search --query "service:<SVC>" --track=trace --from=7d --limit=10
16. [ ] DD events: pup events list --tags="kube_namespace:<NS>,kube_cluster_name:<CLUSTER>" --from=4h
17. [ ] DD metrics: pup metrics search --query "sum:kubernetes.memory.requests{kube_namespace:<NS>,kube_cluster_name:<CLUSTER>}" --from=1h (add "by {kube_deployment}" only with --from=1h)
18. [ ] Check resourcequota, HPA, networkpolicy, node health
19. [ ] Perform additional steps
20. [ ] Summarize findings with evidence
21. [ ] Propose remediation with exact Helm file paths and values (mark write operations clearly)
```
