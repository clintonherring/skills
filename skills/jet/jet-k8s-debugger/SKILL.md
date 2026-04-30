---
name: jet-k8s-debugger
description: >
  Kubernetes and Helm deployment debugging for JET OneEKS clusters. Covers pod
  failures, Helm/Helmfile errors, Argo Rollouts, Istio networking, and KEDA
  autoscaling. Use this skill whenever the user mentions kubectl, helm,
  helmfile, pod crashes, CrashLoopBackOff, OOMKilled, ImagePullBackOff, failed
  deployments, Argo Rollout issues, Istio networking problems, VirtualService
  errors, KEDA autoscaling, or any OneEKS operational issue — even if they
  don't explicitly ask for "debugging help". Also use when the user pastes
  Kubernetes error messages, asks about rollback procedures, mentions canary
  deployments getting stuck, wants to inspect Helm release history, or asks why
  a service is unreachable in a cluster. Covers the full JET stack:
  basic-application chart, helmfile, Argo Rollouts, Istio, KEDA, Vault, and
  Kyverno. Targets developer (human) access via AWS SSO and JET VPN — not
  CI/CD pipelines. For CI/CD or cluster setup, see jet-company-standards.
metadata:
  owner: ai-platform
---

# Kubernetes & Helm Debugger for JET OneEKS

Debug failed deployments, pod crashes, rollout issues, and networking problems across JET's OneEKS clusters.

## Prerequisites

Verify required tools before starting any debugging session:

| Tool | Minimum Version | Required | Purpose |
|------|----------------|----------|---------|
| Node.js | v22+ | Yes (for `npx skills`) | Skill installation via npx |
| `kubectl` | v1.28 | Yes | Core Kubernetes CLI |
| `helm` | v3.12 | Yes | Helm release management |
| `helmfile` | v0.x or v1.x | Recommended | Helmfile-based deployments |
| `kubectl-argo-rollouts` | any | Recommended | Argo Rollouts plugin |
| `jq` | v1.6+ | Recommended | JSON processing for structured output |
| `istioctl` | any | Optional | Istio mesh analysis |

```bash
# Verify installed versions
kubectl version --client
helm version
helmfile --version
kubectl argo rollouts version
jq --version
istioctl version
```

**Install missing tools:**

```bash
# kubectl (macOS)
brew install kubectl

# helm
brew install helm

# helmfile
brew install helmfile

# Argo Rollouts kubectl plugin
brew install argoproj/tap/kubectl-argo-rollouts

# jq (JSON processor)
brew install jq

# istioctl
brew install istioctl
```

## Safety Protocol

**Always follow these rules during debugging:**

1. **Specify context and namespace on every command** — never rely on defaults
   ```bash
   kubectl --context=<ctx> -n <namespace> get pods
   ```
   > **Helmfile exception:** helmfile uses `-e <cluster>` (environment) instead of `--context`/`-n`. The environment name maps to a cluster via `helmfile.yaml` environments. Example: `helmfile -e euw1-pdv-prd-6 diff`.
2. **Read-only first** — use `get`, `describe`, `logs`, `diff` before any mutations
3. **Confirm before mutations** — ask the user before running **any command that changes cluster state**. This includes, but is not limited to: `delete`, `rollback`, `restart`, `abort`, `force-sync`, `promote`, `promote --full`, `retry`, `patch`, `scale`, `annotate --overwrite`, `label --overwrite`, `helm upgrade`, and `helm uninstall`. If a command modifies a rollout, Helm release, resource ownership, traffic distribution, or replica count, it is a mutation — confirm first
4. **Use JSON output for parsing** — append `-o json` when the agent needs to reason over structured data
5. **Never run `kubectl delete pod` on production** without explicit user confirmation and understanding of impact
6. **Sensitive output** — never decode or display Kubernetes secret values (`.data` fields). Use key-listing variants (`jq '.data | keys'`) to verify secrets exist without exposing credentials. Warn the user before outputting Helm values or rendered templates that may contain interpolated secrets

## Cluster Access

JET OneEKS clusters use AWS SSO (IAM Identity Center) for developer access. Authenticate daily with `aws sso login --sso-session one-eks`, then generate kubeconfig per cluster with `aws eks update-kubeconfig`. CI/CD pipelines use Vault JWT instead — this skill targets developer (human) access.

Cluster naming follows these patterns:

| Pattern | Example | Meaning |
|---------|---------|---------|
| `euw1-pdv-prd-N` | `euw1-pdv-prd-6` | eu-west-1, product development, production |
| `euw1-pdv-stg-N` | `euw1-pdv-stg-5` | eu-west-1, product development, staging |
| `euw1-pdv-qa-N` | `euw1-pdv-qa-2` | eu-west-1, product development, QA |
| `euw1-pdv-sbx-N` | `euw1-pdv-sbx-2` | eu-west-1, product development, sandbox |
| `euw1-plt-prd-N` | `euw1-plt-prd-2` | eu-west-1, platform (global), production |
| `euw1-plt-stg-N` | `euw1-plt-stg-2` | eu-west-1, platform (global), staging |
| `apse2-pdv-prd-N` | `apse2-pdv-prd-3` | ap-southeast-2, product development, production |
| `apse2-pdv-stg-N` | `apse2-pdv-stg-2` | ap-southeast-2, product development, staging |
| `usw2-pdv-prd-N` | `usw2-pdv-prd-2` | us-west-2, product development, production |

> **Note:** Teams often configure kubeconfig aliases (e.g., `ai-pdv-prd-5`, `ai-plt-stg-2`) that point to the same clusters. The alias name won't match the pattern above — use the cluster ARN to identify the canonical cluster name.

**Verify access:**
```bash
kubectl --context=<ctx> cluster-info
kubectl --context=<ctx> auth can-i get pods -n <namespace>
```

## Preflight Checks

Run these checks **before any debugging**. Auth failures are the most common reason commands fail, and discovering this mid-triage wastes time and confuses the output.

```bash
# 1. Verify the kubeconfig context exists
kubectl config get-contexts <ctx> 2>&1
# If "error: context was not found", the user needs to configure the cluster first.

# 2. Verify cluster connectivity and auth
kubectl --context=<ctx> cluster-info 2>&1
```

**If the connectivity check fails**, inspect the error and guide the user:

| Error pattern | Cause | Fix |
|---------------|-------|-----|
| `Unable to connect to the server: getting credentials: exec: executable aws failed` | AWS SSO token expired | `aws sso login --sso-session one-eks` |
| `Unable to connect to the server: dial tcp: lookup ... no such host` | Cluster endpoint unreachable / VPN not connected | Connect to the JET VPN first |
| `error: context "<ctx>" does not exist` | Kubeconfig not set up for this cluster | `aws eks update-kubeconfig --profile <cluster> --name <cluster> --alias <cluster>` |
| `Unauthorized` or `forbidden` | RBAC — user lacks permissions in this namespace | Verify namespace access: `kubectl --context=<ctx> auth can-i get pods -n <ns>` |

**Do not proceed with triage until the connectivity check succeeds.** There is no point running kubectl/helm commands against a cluster you cannot reach — every command will fail with the same auth error.

## Session Initialization

At the start of every debugging session, auto-detect the target cluster from the user's kubeconfig. This eliminates the need to ask "which cluster?" in most cases.

```bash
# Check the currently active context
kubectl config current-context 2>/dev/null

# List all contexts pointing to JET clusters
# (matches canonical names AND team aliases via the cluster ARN column)
kubectl config get-contexts --no-headers | \
  grep -E '(euw1|apse2|usw2)-[a-z]+-[a-z]+-[0-9]+'
```

**Resolution logic:**

> **Note:** The `grep` above matches against the entire row, including the CLUSTER column (which contains the ARN). This means it will match contexts with team aliases (e.g., `ai-pdv-prd-5`) if their cluster ARN contains a JET cluster name. When presenting matches to the user, show the context NAME (column 1), not the ARN.

| Situation | Action |
|-----------|--------|
| Current context's cluster ARN matches JET pattern | Use it as `<ctx>`. Confirm: *"Detected cluster `<ctx>` — debugging that one?"* |
| Current context is non-JET but JET contexts exist | List matching JET context names and ask the user to pick one |
| User already named a cluster in their message | Use that directly as `<ctx>`; skip detection |
| No JET contexts found | Guide through setup: `aws eks update-kubeconfig --profile <cluster> --name <cluster> --alias <cluster>` |

Once `<ctx>` is established, use it on every subsequent command for this session without asking again.

## Triage Flowchart

When a deployment fails or a service is unhealthy, follow this decision tree:

1. **Check rollout status** — is the Argo Rollout progressing, degraded, or paused?
   ```bash
   kubectl argo rollouts --context=<ctx> -n <ns> status <app>
   ```
   > **If `kubectl-argo-rollouts` is not installed**, fall back to raw kubectl:
   > ```bash
   > kubectl --context=<ctx> -n <ns> get rollout <app> -o yaml | grep -A5 'status:'
   > ```
2. **Check pod health** — are pods running, crashing, or pending?
   ```bash
   kubectl --context=<ctx> -n <ns> get pods -l app.kubernetes.io/name=<app>
   ```
3. **Check events** — what does the cluster say happened?
   ```bash
   kubectl --context=<ctx> -n <ns> get events --sort-by='.metadata.creationTimestamp' --field-selector involvedObject.name=<pod>
   ```
4. **Check logs** — what does the application say?
   ```bash
   kubectl --context=<ctx> -n <ns> logs <pod> --previous --tail=100
   ```
5. **Check Helm state** — is the release in a consistent state?
   ```bash
   helm --kube-context=<ctx> -n <ns> history <release> --max 5
   ```
6. **Check Istio config** — are networking resources valid?
   ```bash
   istioctl --context=<ctx> -n <ns> analyze
   ```
7. **Check Datadog** — what do metrics and logs show?
   If the `jet-datadog` skill is in your available skills list, use it — it provides
   structured queries via the `pup` CLI that are easier to reason over than browser URLs.
   ```bash
   # With jet-datadog skill: ask it to query logs/events for the service
   pup logs search --query="cluster_name:<cluster> kube_namespace:<ns> service:<app>" --from=1h --storage=flex
   pup events search --query="cluster_name:<cluster> kube_namespace:<ns>" --from=4h
   ```
   If `jet-datadog` is not available, fall back to direct Datadog URLs:
   - Events: `https://app.datadoghq.eu/event/explorer?query=cluster_name:<cluster>%20kube_namespace:<ns>`
   - Logs: `https://app.datadoghq.eu/logs?query=cluster_name:<cluster>%20kube_namespace:<ns>%20service:<app>`

## Quick Reference — Most Common Commands

```bash
# Pod status overview
kubectl --context=<ctx> -n <ns> get pods -l app.kubernetes.io/name=<app> -o wide

# Describe a failing pod (shows events, conditions, resource usage)
kubectl --context=<ctx> -n <ns> describe pod <pod>

# Logs from a crashed container (previous instance)
kubectl --context=<ctx> -n <ns> logs <pod> --previous --tail=200

# Argo Rollout detailed status
kubectl argo rollouts --context=<ctx> -n <ns> get rollout <app>

# Helm release history (last 5 revisions)
helm --kube-context=<ctx> -n <ns> history <app> --max 5

# Compare current vs previous Helm values
helm --kube-context=<ctx> -n <ns> get values <app> --revision <N>

# Helmfile diff (preview changes before sync)
helmfile -e <cluster> diff

# Istio analysis
istioctl --context=<ctx> -n <ns> analyze

# All events in namespace (sorted by time)
kubectl --context=<ctx> -n <ns> get events --sort-by='.metadata.creationTimestamp' | tail -30

# Resource consumption (requires metrics-server)
kubectl --context=<ctx> -n <ns> top pods -l app.kubernetes.io/name=<app>
```

## JET Tech Stack Context

All JET OneEKS applications use the `sre/basic-application` Helm chart with:

- **Argo Rollouts** as the primary workload (not native Deployments)
- **Istio** service mesh (VirtualService, DestinationRule, AuthorizationPolicy)
- **KEDA** for autoscaling (ScaledObject, not raw HPA)
- **Vault** for secret injection (JWT auth via OIDC)
- **Kyverno** for policy enforcement
- **Helmfile** as the deployment orchestrator (wraps Helm)

See `references/basic-application-values.md` in the Detailed References section below for the full chart values reference.

## Rollback Guidance

> **Terminology:** JET distinguishes two rollback mechanisms:
> - **Application Rollback** — deploying a previous application version via `helm upgrade` (or the `rollback-helmfile` workflow). This is the standard rollback method for `sre/basic-application` chart >= v1.1.0 because it correctly recreates Argo Rollout resources.
> - **Helm State Recovery** — using `helm rollback` to revert a stuck/failed Helm release to a previous revision. This only fixes Helm's release state; it does **not** safely roll back Argo Rollout workloads. Use this only when the Helm release itself is broken (e.g., `STATUS: failed` or `STATUS: pending-upgrade`).

JET's `rollback-helmfile` workflow supports three **Application Rollback** strategies:

| Type | When to Use | Example |
|------|-------------|---------|
| `image-tag` | Roll back to a known-good container image | The new build crashes |
| `application-version` | Roll back to a full application version | New feature broke production |
| `release-revision` | Roll back to a specific Helm revision's values | Config change caused issues |

**Critical**: For `sre/basic-application` chart >= v1.1.0, application rollback uses `helm upgrade` (not `helm rollback`) to ensure Argo Rollout resources are handled correctly. Only use `helm rollback` for Helm State Recovery (stuck releases), never as an application rollback mechanism.

**After any rollback**, verify it succeeded:

```bash
kubectl argo rollouts --context=<ctx> -n <ns> status <app>
kubectl --context=<ctx> -n <ns> get pods -l app.kubernetes.io/name=<app>
helm --kube-context=<ctx> -n <ns> history <app> --max 3
```

See `references/argo-rollouts-guide.md` for detailed rollback procedures.

## Worked Example

A realistic debugging walkthrough using example values. Replace these with your actual cluster, namespace, and app name.

> **Example values used below:**
> - Cluster context: `euw1-pdv-stg-5`
> - Namespace: `ai-platform`
> - Application: `helixapi`

**Scenario:** A deployment to staging failed — pods are crash-looping.

```bash
# 1. Verify cluster access
kubectl --context=euw1-pdv-stg-5 cluster-info

# 2. Check rollout status
kubectl argo rollouts --context=euw1-pdv-stg-5 -n ai-platform status helixapi

# 3. Check pod health
kubectl --context=euw1-pdv-stg-5 -n ai-platform get pods -l app.kubernetes.io/name=helixapi
# NAME                        READY   STATUS             RESTARTS   AGE
# helixapi-7f8b9c6d4-x2k9p   0/1     CrashLoopBackOff   4          6m

# 4. Get logs from the crashing pod
kubectl --context=euw1-pdv-stg-5 -n ai-platform logs helixapi-7f8b9c6d4-x2k9p --previous --tail=100
# Example output: "Failed to connect to database at mysql-primary:3306 — Connection refused"

# 5. Root cause identified: database connection issue
#    → Check if there's a ServiceEntry for the external database
kubectl --context=euw1-pdv-stg-5 -n ai-platform get serviceentry

# 6. Check Helm release state to confirm the deploy went through
helm --kube-context=euw1-pdv-stg-5 -n ai-platform history helixapi --max 3
```

**Resolution:** The ServiceEntry for `mysql-primary` had not been applied to this cluster, so Istio's `REGISTRY_ONLY` outbound policy was blocking the connection. After applying the ServiceEntry, the pods connected successfully and the rollout completed.

## Detailed References

- `references/troubleshooting-flowchart.md` — Step-by-step decision tree for common failure categories
- `references/kubectl-recipes.md` — Categorized kubectl commands with JSON output variants
- `references/helm-helmfile-debugging.md` — Helmfile and Helm debugging workflows
- `references/argo-rollouts-guide.md` — Argo Rollouts status, canary, abort, retry, rollback
- `references/istio-debugging.md` — Istio VirtualService, DestinationRule, AuthorizationPolicy troubleshooting
- `references/basic-application-values.md` — Full values reference for the sre/basic-application chart
- `references/common-failures.md` — Symptom-to-fix lookup table for 30+ common scenarios
