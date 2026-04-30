# jet-k8s-debugger

An AI coding agent skill for debugging Kubernetes and Helm deployments on JET OneEKS clusters.

## Installation

### Quick start

```bash
npx skills add git@github.je-labs.com:ai-platform/skills.git --skill jet-k8s-debugger
```

Add `-g` to install globally (available across all projects):

```bash
npx skills add git@github.je-labs.com:ai-platform/skills.git --skill jet-k8s-debugger -g
```

### Dependencies

You need these CLI tools installed before the skill can run commands:

| Tool | Minimum Version | Required | Install |
|------|----------------|----------|---------|
| Node.js | v22+ | Yes (for `npx`) | [nodejs.org](https://nodejs.org) |
| `kubectl` | v1.28 | Yes | `brew install kubectl` |
| `helm` | v3.12 | Yes | `brew install helm` |
| AWS CLI | v2 | Yes (for SSO) | `brew install awscli` |
| `helmfile` | v0.x or v1.x | Recommended | `brew install helmfile` |
| `kubectl-argo-rollouts` | any | Recommended | `brew install argoproj/tap/kubectl-argo-rollouts` |
| `jq` | v1.6+ | Recommended | `brew install jq` |
| `istioctl` | any | Optional | `brew install istioctl` |

### Cluster access setup

Before the skill can interact with a cluster, you need an active AWS SSO session and a kubeconfig entry:

```bash
# 1. Login to AWS SSO (required daily)
aws sso login --sso-session one-eks

# 2. Add cluster to kubeconfig (one-time per cluster)
aws eks update-kubeconfig --profile <cluster> --name <cluster> --alias <cluster>

# 3. Verify connectivity
kubectl --context=<cluster> cluster-info
```

You must also be connected to the **JET VPN**.

### Verify installation

```bash
npx skills list
```

You should see `jet-k8s-debugger` in the output.

### Companion skills

These JET skills complement `jet-k8s-debugger` and can be installed alongside it:

| Skill | What it adds | Install |
|-------|-------------|---------|
| `jet-datadog` | Datadog `pup` CLI integration for log/event/APM queries during debugging | `npx skills add git@github.je-labs.com:ai-platform/skills.git --skill jet-datadog` |
| `jet-company-standards` | JET internal docs, CI/CD workflows, team/service lookup via Backstage and PlatformMetadata | `npx skills add git@github.je-labs.com:ai-platform/skills.git --skill jet-company-standards` |

## What this skill does

When loaded, this skill gives the agent:

- **Triage workflows** — step-by-step decision trees for deployment failures, pod crashes, rollout issues, and networking problems
- **kubectl recipes** — categorized commands with JSON output variants for agent-parseable responses
- **Helm/Helmfile debugging** — diff, lint, template, release history, stuck release recovery
- **Argo Rollouts guidance** — canary management, promote/abort, rollback procedures (including the `helm upgrade` vs `helm rollback` distinction for `basic-application` chart ≥ v1.1.0)
- **Istio diagnosis** — VirtualService, DestinationRule, AuthorizationPolicy, Envoy proxy debugging
- **KEDA autoscaling** — ScaledObject, HPA, TriggerAuthentication
- **Datadog integration** — correct `pup` CLI queries when the `jet-datadog` skill is also loaded, with browser URL fallback
- **Safety rules** — always specify `--context` and `-n`, read-only first, confirm before mutations

## Scope

This skill targets **developer (human) access** to JET OneEKS clusters via AWS SSO and JET VPN. It does not cover:
- CI/CD pipeline configuration → see [jet-company-standards](#companion-skills)
- AWS infrastructure management
- Datadog monitor/dashboard management → see [jet-datadog](#companion-skills)

## How the agent uses it — order of operations

When a user reports a deployment problem, the agent follows this sequence:

### 1. Session initialization (automatic)
Detect the target cluster from the user's active kubeconfig context:
```bash
kubectl config current-context
# Matches canonical names AND team aliases via the cluster ARN column
kubectl config get-contexts --no-headers | grep -E '(euw1|apse2|usw2)-[a-z]+-[a-z]+-[0-9]+'
```
If the current context's cluster ARN matches a JET cluster, use it. If multiple JET contexts exist, show the context names (not ARNs) and ask the user to pick. If no JET context is found, guide the user through AWS SSO login and `aws eks update-kubeconfig`.

### 2. Preflight checks
Verify connectivity before running any diagnostic commands:
```bash
kubectl config get-contexts <ctx>
kubectl --context=<ctx> cluster-info
```
If this fails (expired SSO token, VPN not connected, missing kubeconfig), resolve it first. No triage proceeds until the cluster is reachable.

### 3. Triage — identify the failure category

| Symptom | Decision tree |
|---------|--------------|
| `helmfile sync` or CI deploy failed | Flow 1 in `troubleshooting-flowchart.md` |
| Pods in `Pending`, `CrashLoopBackOff`, `ImagePullBackOff` | Flow 2 in `troubleshooting-flowchart.md` |
| Pods running but service returning errors | Flow 3 in `troubleshooting-flowchart.md` |
| Argo Rollout stuck, degraded, or paused | Flow 4 in `troubleshooting-flowchart.md` |

### 4. Deep diagnosis (per failure category)

The agent consults the relevant reference file:

- **Pod failures** → `references/common-failures.md` — symptom-to-fix lookup for 30+ scenarios
- **Helm/Helmfile errors** → `references/helm-helmfile-debugging.md` — diff, values comparison, stuck release recovery
- **Argo Rollouts** → `references/argo-rollouts-guide.md` — canary operations, rollback procedures
- **Istio/networking** → `references/istio-debugging.md` — VirtualService, DestinationRule, Envoy proxy
- **Chart values** → `references/basic-application-values.md` — full values reference and common misconfigurations
- **General kubectl** → `references/kubectl-recipes.md` — categorized commands with JSON variants

### 5. Rollback (if needed)

The preferred rollback path is via the `rollback-helmfile` CI workflow (image-tag, application-version, or release-revision). For emergency manual rollback, the agent uses `helm upgrade` (not `helm rollback`) for chart version ≥ v1.1.0. See `references/argo-rollouts-guide.md` for the full procedure.

### 6. Verify the fix

After any intervention:
```bash
kubectl argo rollouts --context=<ctx> -n <ns> status <app>
kubectl --context=<ctx> -n <ns> get pods -l app.kubernetes.io/name=<app>
helm --kube-context=<ctx> -n <ns> history <app> --max 3
```

## Reference files

| File | Purpose |
|------|---------|
| `SKILL.md` | Main skill entry point — prerequisites, safety rules, cluster access, triage flowchart, quick reference |
| `references/troubleshooting-flowchart.md` | Step-by-step decision trees for 4 common failure categories |
| `references/common-failures.md` | Symptom → root cause → fix lookup for 30+ scenarios |
| `references/helm-helmfile-debugging.md` | Helmfile diff/lint/sync, Helm history, stuck release recovery |
| `references/argo-rollouts-guide.md` | Canary management, rollback procedures, KEDA edge cases |
| `references/istio-debugging.md` | Istio analysis, VirtualService/DestinationRule/AuthorizationPolicy, Envoy proxy |
| `references/basic-application-values.md` | Full `sre/basic-application` chart values reference |
| `references/kubectl-recipes.md` | Categorized kubectl commands with JSON output variants |

## Datadog integration

If the `jet-datadog` skill is also loaded, the agent uses the `pup` CLI for structured log and event queries:

```bash
# Query application logs
pup logs search --query="cluster_name:<cluster> kube_namespace:<ns> service:<app>" --from=1h --storage=flex

# Query Kubernetes events
pup events search --query="cluster_name:<cluster> kube_namespace:<ns>" --from=4h

# Check APM service dependencies
pup apm dependencies list --env=<env>   # Use the actual environment: prod, staging, etc.
```

Without `jet-datadog`, the agent falls back to direct Datadog browser URLs.
