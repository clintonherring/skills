# Helm & Helmfile Debugging

Debugging workflows for Helmfile-based deployments in JET OneEKS clusters.

## Helmfile Architecture at JET

JET deployments use Helmfile as an orchestration layer on top of Helm. A typical helmfile config:

```yaml
# helmfile.yaml or helmfile.d/helmfile.yaml
repositories:
  - name: sre
    url: https://artifactory.takeaway.com/sre-helm-prod-virtual

releases:
  - name: {{ .Values.APPLICATION_NAME }}
    namespace: {{ .Values.K8S_SERVICE_NAMESPACE }}
    chart: sre/basic-application
    version: {{ .Values.CHART_VERSION | default "1.1.10" }}
    values:
      - values/{{ .Environment.Name }}/values.yaml
      - values/common.yaml
```

**State values** are injected by the `deploy-helmfile` workflow via `--state-values-set`:
- `APPLICATION_NAME` — from Sonic config or repo name
- `APPLICATION_VERSION` — git SHA or tag
- `K8S_SERVICE_NAMESPACE` — target namespace
- `CHART_NAME`, `CHART_VERSION` — chart coordinates
- `CI_COMMIT_TAG` — backward compat for GitLab migrations

## Helmfile Commands for Debugging

### Preview Changes (diff)

```bash
# Show what would change without applying
helmfile -e <cluster> diff

# With state values (mimicking CI)
helmfile -e <cluster> diff \
  --state-values-set APPLICATION_NAME=<app> \
  --state-values-set APPLICATION_VERSION=<tag> \
  --state-values-set CHART_VERSION=1.1.10

# Verbose diff (shows full resource changes)
HELM_DIFF_USE_UPGRADE_DRY_RUN=true helmfile -e <cluster> diff
```

### Lint (validate templates)

```bash
# Validate chart rendering
helmfile -e <cluster> lint

# With schema validation
helmfile -e <cluster> lint --args="--strict"
```

### Template (render without applying)

```bash
# Render templates to stdout
helmfile -e <cluster> template

# Save to file for inspection
# ⚠ File write — overwrites rendered.yaml. May contain interpolated secrets from Vault.
#   Do not commit or share this file without review.
helmfile -e <cluster> template > rendered.yaml
```

### Sync (apply)

```bash
# ⚠ MUTATION — Normal sync (applies changes to cluster). Confirm with user.
helmfile -e <cluster> sync

# ⚠ MUTATION — Force sync (for immutable field changes) — WARNING: causes brief downtime
# Passes --force to helm upgrade, which uses a replace strategy on Kubernetes
# resources that fail to patch (delete + recreate). Only affects resources where
# the upgrade would otherwise fail; unchanged resources are left alone.
# NOTE: This is distinct from the CI workflow's force-sync input, which runs
# kubectl replace --force — a different mechanism with different failure modes.
# Confirm with user — causes brief downtime.
helmfile -e <cluster> sync --args="--force"
```

> **Force-sync comparison:**
>
> | Mechanism | Trigger | Behavior | Scope |
> |-----------|---------|----------|-------|
> | `helmfile sync --args="--force"` | Manual / CLI | `helm upgrade --force` — replace strategy on resources that fail to patch (delete + recreate). Unchanged resources are not affected. | Single release |
> | `deploy-helmfile` with `force-sync: true` | CI workflow input | Runs `kubectl replace --force` on all rendered manifests. Deletes and recreates every resource unconditionally. | All resources in helmfile |
>
> Both cause brief downtime. Prefer the Helm `--force` approach when only specific resources have immutable field changes. Use the CI `force-sync` only when the Helm approach is insufficient (e.g., multiple resources with conflicts).

## Helm Debugging Commands

### Release History

```bash
# View last 10 revisions
helm --kube-context=<ctx> -n <ns> history <app> --max 10

# Output:
# REVISION  UPDATED                   STATUS      CHART                    APP VERSION  DESCRIPTION
# 42        2026-02-28 10:15:00       deployed    basic-application-1.1.10 1.0.0        Upgrade complete
# 41        2026-02-28 09:00:00       superseded  basic-application-1.1.10 1.0.0        Upgrade complete
# 40        2026-02-27 16:30:00       superseded  basic-application-1.1.9  1.0.0        Upgrade complete

# Key statuses:
# deployed    — current active release
# superseded  — previous successful release
# failed      — release failed to deploy
# pending-upgrade — upgrade in progress (or stuck)
# pending-rollback — rollback in progress (or stuck)
```

### Compare Values Between Revisions

```bash
# Current values
# ⚠ File write — overwrites current.yaml. May contain sensitive values (secrets, credentials).
helm --kube-context=<ctx> -n <ns> get values <app> > current.yaml

# Previous revision values
# ⚠ File write — overwrites previous.yaml. May contain sensitive values (secrets, credentials).
helm --kube-context=<ctx> -n <ns> get values <app> --revision <N> > previous.yaml

# Diff them
diff current.yaml previous.yaml
```

### Render Template Locally

```bash
# Add the JET chart repo
helm repo add sre https://artifactory.takeaway.com/sre-helm-prod-virtual

# Render with custom values
helm template <app> sre/basic-application \
  --version 1.1.10 \
  -f values.yaml \
  -n <ns>

# Validate against schema
helm template <app> sre/basic-application \
  --version 1.1.10 \
  -f values.yaml \
  --validate
```

### Helm State Recovery (Stuck Releases)

> **Terminology:** This section covers **Helm State Recovery** — fixing a stuck/broken Helm release (e.g., `pending-upgrade`, `pending-rollback`, `failed`). This is NOT an application rollback. For **Application Rollback** (reverting to a previous image/version), see `references/argo-rollouts-guide.md`.

If a Helm release is stuck in `pending-upgrade`, `pending-rollback`, or `pending-install`:

```bash
# Check the release status
helm --kube-context=<ctx> -n <ns> status <app>

# View the secret storing the release state
kubectl --context=<ctx> -n <ns> get secret -l owner=helm,name=<app> --sort-by='.metadata.creationTimestamp'

# Option 1: Rollback to last successful revision (unsticks Helm release state)
# ⚠ MUTATION — confirm with user before running
helm --kube-context=<ctx> -n <ns> rollback <app> <last-good-revision>
# NOTE: This only recovers the Helm release state. It does NOT safely roll back
# Argo Rollout workloads. For application rollback, use "helm upgrade" per
# argo-rollouts-guide.md.
# NOTE: Rollback is not possible for pending-install (no prior revision).
# Use Option 2 instead.

# Option 2 (nuclear): Delete the pending release secret and re-deploy
# ⚠ MUTATION — deletes the Helm release secret. Only do this if rollback fails. Requires re-deploy from CI.
# Confirm with user before running.
kubectl --context=<ctx> -n <ns> delete secret sh.helm.release.v1.<app>.v<stuck-revision>
```

## Common Helmfile/Helm Errors

### "values don't meet the specifications of the schema"

The `basic-application` chart has strict JSON Schema validation. Common violations:

| Error Pattern | Cause | Fix |
|--------------|-------|-----|
| `application.name` invalid | Name doesn't match `^[a-z][a-z0-9]*$` or exceeds 36 chars | Use lowercase alphanumeric only, 3-36 chars |
| `deployment.env[].name` reserved | Env var starts with `JET_` or is a reserved DD var | Rename the env var |
| `deployment.strategy` invalid | Both `rollingUpdate` and `canary` specified | Choose one strategy only |
| `virtualservices` conflict | Both `fault` and `http` specified | These are mutually exclusive |
| `capacityType` invalid | Not one of `""`, `"spot"`, `"on-demand"` | Use an allowed value |

### "rendered manifests contain a resource that already exists"

Typically caused by:
1. A previous release was deleted but resources were not cleaned up
2. Resources were created manually outside of Helm
3. Chart migration from Deployment to Rollout left orphaned resources

**Debug:**
```bash
# Find the conflicting resource
kubectl --context=<ctx> -n <ns> get <resource-type> <resource-name> -o yaml | \
  grep -A3 'labels:' | grep 'managed-by'

# If managed by Helm but wrong release:
# ⚠ MUTATION — changes resource ownership. Confirm with user before running.
kubectl --context=<ctx> -n <ns> annotate <resource-type> <resource-name> \
  meta.helm.sh/release-name=<correct-release> \
  meta.helm.sh/release-namespace=<ns> --overwrite

# ⚠ MUTATION — changes resource label. Confirm with user before running.
kubectl --context=<ctx> -n <ns> label <resource-type> <resource-name> \
  app.kubernetes.io/managed-by=Helm --overwrite
```

### "cannot patch ... field is immutable"

Certain K8s fields cannot be changed in-place (Service `clusterIP`, PVC `storageClassName`, Job `selector`).

**Fix options:**
1. **Force sync (CI)** — use the `force-sync` input in `deploy-helmfile` workflow. This runs `kubectl replace --force`, which deletes and recreates the resource. This is distinct from `helmfile sync --args="--force"`, which passes `--force` to `helm upgrade` and operates via the Kubernetes API.
2. **Manual delete** — delete the specific resource and let Helm recreate it:
   ```bash
   # ⚠ MUTATION — deletes the resource so Helm can recreate it. Confirm with user.
   kubectl --context=<ctx> -n <ns> delete <resource-type> <resource-name>
   # Then re-run helmfile sync
   ```

### ConfigMap Hash Drift

The `basic-application` chart creates ConfigMaps with hash-suffixed names (e.g., `myapp-a1b2c3d4`). Old ConfigMaps are not deleted automatically due to `helm.sh/resource-policy: keep`.

```bash
# List all configmaps for app (oldest first)
kubectl --context=<ctx> -n <ns> get configmap -l app.kubernetes.io/name=<app> \
  --sort-by='.metadata.creationTimestamp'

# Check which configmap the current pods reference
kubectl --context=<ctx> -n <ns> get pods -l app.kubernetes.io/name=<app> -o json | \
  jq '.items[0].spec.volumes[]? | select(.configMap) | .configMap.name'

# Clean up old configmaps (keep only the one referenced by current pods)
# WARNING: Verify no other workload references old configmaps before deleting.
```

### Helmfile v1 vs v0 Compatibility

JET is migrating from Helmfile v0.x to v1.x. The workflow detects legacy patterns:
- `helmfile.d/helmfile.yaml` with `helmfile.d/bases/` → legacy v0 pattern
- Direct `helmfile.yaml` at root → modern pattern

If you see warnings about helmfile version compatibility, check:
```bash
helmfile version
# Ensure it matches the helmfile-version input in the workflow
```

## Debugging Helmfile Environment Resolution

When values are not being applied as expected:

```bash
# Check which values files are loaded
helmfile -e <cluster> --debug template 2>&1 | grep "loading"

# Verify state values are passed correctly
helmfile -e <cluster> --debug diff 2>&1 | grep "state-values"

# Render values only (without chart templates)
helmfile -e <cluster> write-values
```
