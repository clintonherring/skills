# Argo Rollouts Guide

JET's `basic-application` chart (v1.1+) uses Argo Rollouts as the primary workload type instead of native Kubernetes Deployments. This guide covers status interpretation, canary management, and rollback procedures.

## Key Concept: Rollout vs Deployment

- The `basic-application` chart renders an **Argo Rollout** (`argoproj.io/v1alpha1`), not a Deployment
- The legacy Deployment template only renders during migration (auto-scales to 0 after 1 week)
- Use `kubectl argo rollouts` commands, not `kubectl rollout status deployment/`

## Status Reference

```bash
# Quick status check
kubectl argo rollouts --context=<ctx> -n <ns> status <app>

# Detailed status with revision info and pod details
kubectl argo rollouts --context=<ctx> -n <ns> get rollout <app>

# Watch in real-time
kubectl argo rollouts --context=<ctx> -n <ns> get rollout <app> --watch
```

### Status Values

| Status | Meaning | Action |
|--------|---------|--------|
| `Healthy` | All pods running, stable revision active | No action needed |
| `Progressing` | New revision rolling out | Monitor — check pod status if stuck |
| `Paused` | Canary paused at a step, waiting for promotion | Promote or abort |
| `Degraded` | New revision failed, not enough healthy pods | Investigate pod failures, then abort or fix |
| `ScaledDown` | Rollout scaled to 0 replicas | Check if intentional (migration) |

## Canary Deployments

The `basic-application` chart supports canary strategy with Istio traffic management.

### Default Canary Steps

When `deployment.strategy.canary` is configured with explicit steps (no steps specified defaults to a simple rollout), a typical JET canary configuration looks like:

```yaml
# Example from basic-application-values.md
deployment:
  strategy:
    canary:
      steps:
        - setWeight: 1
        - pause: {}
        - setWeight: 10
        - pause: {}
        - setWeight: 50
        - pause: {}
```

This produces three manual gates before full promotion:
1. **1% traffic** → pause (manual gate)
2. **10% traffic** → pause (manual gate)
3. **50% traffic** → pause (manual gate)

After the final promotion, traffic shifts to 100% on the new revision.

### Canary with VirtualService Traffic Splitting

The chart creates:
- **Stable Service**: `<app>` — serves stable revision
- **Preview Service**: `<app>-preview` — serves canary revision
- **Stable VirtualService**: `<app>` — routes traffic based on canary weight
- **Preview VirtualService**: `<app>-preview` — 100% traffic to preview (for testing)

Preview URL pattern: `preview-<host>` for `*.jet-internal.com` hosts.

### Canary Operations

```bash
# Check current canary step
kubectl argo rollouts --context=<ctx> -n <ns> get rollout <app>
# Look for "Step: X/Y" and current weight percentage

# Promote to next step (manual gate)
# ⚠ MUTATION — confirm with user before running
kubectl argo rollouts --context=<ctx> -n <ns> promote <app>

# Skip all remaining steps and go to 100%
# ⚠ MUTATION — this immediately shifts 100% traffic to the new revision. Confirm with user.
kubectl argo rollouts --context=<ctx> -n <ns> promote <app> --full

# Abort canary and roll back to stable
# ⚠ MUTATION — aborts the rollout and reverts traffic to stable. Confirm with user.
kubectl argo rollouts --context=<ctx> -n <ns> abort <app>

# Retry a failed/aborted rollout (re-attempts with same revision)
# ⚠ MUTATION — this restarts the rollout process. Confirm with user.
kubectl argo rollouts --context=<ctx> -n <ns> retry rollout <app>
```

### Debugging a Stuck Canary

```bash
# 1. Check rollout status and current step
kubectl argo rollouts --context=<ctx> -n <ns> get rollout <app>

# 2. Check if canary pods are healthy
kubectl --context=<ctx> -n <ns> get pods -l rollouts-pod-template-hash

# 3. Check VirtualService weight distribution
kubectl --context=<ctx> -n <ns> get vs <app> -o json | \
  jq '.spec.http[0].route[] | {destination: .destination.host, weight: .weight}'

# 4. Test the preview endpoint directly
# Preview VirtualService routes to: preview-<original-host>

# 5. Check analysis runs (if using automated analysis)
kubectl --context=<ctx> -n <ns> get analysisrun -l rollouts-pod-template-hash --sort-by='.metadata.creationTimestamp'
```

## Rolling Update Strategy

When canary is not configured, the chart uses a rolling update strategy:

```bash
# Check rollout progress
kubectl argo rollouts --context=<ctx> -n <ns> status <app>

# If stuck, check new ReplicaSet pods
kubectl --context=<ctx> -n <ns> get pods -l app.kubernetes.io/name=<app> --sort-by='.metadata.creationTimestamp'

# The newest pods belong to the new revision
# Check their status, logs, and events for issues
```

## Rollback Procedures

### Method 1: Via rollback-helmfile Workflow (Preferred)

JET's `rollback-helmfile` workflow is the standard way to roll back in CI. It supports three reference types:

**By image tag** (most common):
```yaml
# In GitHub Actions
uses: github-actions/pipelines/.github/workflows/rollback-helmfile.yml
with:
  rollback-reference-type: image-tag
  rollback-reference-value: "abc123"  # The known-good image tag
```

**By application version**:
```yaml
with:
  rollback-reference-type: application-version
  rollback-reference-value: "v2.3.1"
```

**By Helm release revision**:
```yaml
with:
  rollback-reference-type: release-revision
  rollback-reference-value: "42"
```

### Method 2: Manual Application Rollback via `helm upgrade` (Emergency)

For chart version >= 1.1.0, **application rollback uses `helm upgrade`** (not `helm rollback`):

```bash
# 1. Find the target revision
helm --kube-context=<ctx> -n <ns> history <app> --max 10

# 2. Extract values from the target revision
# ⚠ File write — overwrites rollback-values.yaml. May contain sensitive values (secrets, credentials).
#   Review the output before sharing or committing.
helm --kube-context=<ctx> -n <ns> get values <app> --revision <N> > rollback-values.yaml

# 3. ⚠ MUTATION — Upgrade to the target revision's values and chart version. Confirm with user.
helm --kube-context=<ctx> -n <ns> upgrade <app> sre/basic-application \
  --version <target-chart-version> \
  -f rollback-values.yaml \
  --wait --timeout 600s
```

**Why not `helm rollback`?** For Argo Rollout resources, `helm rollback` can leave the Rollout in an inconsistent state because it doesn't properly handle the Rollout's revision tracking. Use `helm rollback` only for **Helm State Recovery** — restoring a stuck/failed Helm release (e.g., `STATUS: failed` or `STATUS: pending-upgrade`) — never as an application rollback mechanism. See `references/helm-helmfile-debugging.md` for Helm State Recovery procedures.

### Method 3: Abort Canary (During Active Canary)

If a canary is in progress and needs to be stopped:

```bash
# Abort reverts traffic to 100% stable
# ⚠ MUTATION — aborts the rollout and reverts traffic to stable. Confirm with user.
kubectl argo rollouts --context=<ctx> -n <ns> abort <app>

# The rollout enters "Degraded" state — this is expected after abort
# The stable revision continues serving all traffic
```

## KEDA ScaledObject Edge Case

When rolling back across the chart v1.1.10 boundary downward, KEDA ScaledObjects may have taken ownership of HPAs. The rollback workflow handles this automatically, but if doing a manual rollback:

```bash
# Check if HPA has KEDA owner reference
kubectl --context=<ctx> -n <ns> get hpa -o json | \
  jq '.items[] | {name: .metadata.name, owners: .metadata.ownerReferences}'

# If KEDA owns the HPA and you're rolling back to pre-KEDA chart version:
# Remove the owner reference to prevent KEDA from deleting the HPA
# ⚠ MUTATION — modifies HPA ownership. Confirm with user and verify KEDA ScaledObject state afterward.
kubectl --context=<ctx> -n <ns> patch hpa <hpa-name> --type=json \
  -p='[{"op": "remove", "path": "/metadata/ownerReferences"}]'
```

## Monitoring Rollout Health

```bash
# Events related to rollout (shows step progressions, failures)
kubectl --context=<ctx> -n <ns> describe rollout <app> | grep -A30 "Events:"

# Check ReplicaSets managed by the rollout
kubectl --context=<ctx> -n <ns> get rs -l app.kubernetes.io/name=<app> --sort-by='.metadata.creationTimestamp'

# Datadog: events for the namespace (Argo Rollout events are not tagged with kube_deployment)
# https://app.datadoghq.eu/event/explorer?query=cluster_name:<cluster>%20kube_namespace:<ns>
```
