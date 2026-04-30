# Common Failures Reference

Quick-reference mapping symptoms to root causes, diagnostic commands, and fixes for JET OneEKS deployments.

## Pod Failures

### `CrashLoopBackOff` — application startup failure

```bash
kubectl --context=<ctx> -n <ns> logs <pod> --previous --tail=200
```

**Fix:** Check logs for stack traces. Common causes: missing config, DB unreachable, bad secrets.

### `CrashLoopBackOff` with exit code 137 — OOMKilled

```bash
kubectl --context=<ctx> -n <ns> describe pod <pod>
# Look for "Last State: Terminated / Reason: OOMKilled"
kubectl --context=<ctx> -n <ns> top pods -l app.kubernetes.io/name=<app>
```

**Fix:** Increase `deployment.resources.limits.memory` in helmfile values. Compare actual usage against limits.

### `CrashLoopBackOff` with exit code 143 — SIGTERM received

```bash
kubectl --context=<ctx> -n <ns> describe pod <pod>
# Check "Last State: Terminated / Reason: ..." and "Restart Count"
# Also check liveness probe configuration:
kubectl --context=<ctx> -n <ns> get pod <pod> -o json | jq '.spec.containers[].livenessProbe'
```

**Fix:** Exit code 143 means the process received SIGTERM. This is normal during rolling updates and scale-downs, but problematic when it causes repeated CrashLoopBackOff. Two common causes:
1. **Graceful shutdown too slow** — increase `terminationGracePeriodSeconds` or optimize the app's shutdown path
2. **Liveness probe failure** — if the pod is being killed repeatedly, a failing liveness probe may be triggering the SIGTERM. Check that the probe endpoint is healthy and that `initialDelaySeconds` / `timeoutSeconds` are sufficient for the app's startup time

### `ImagePullBackOff`

```bash
kubectl --context=<ctx> -n <ns> describe pod <pod>
# Look in Events for "Failed to pull image" reason
```

**Fix:** Verify image:tag exists in `artifacts.takeaway.com`. If "unauthorized", check image pull secrets exist and have the expected keys:
```bash
kubectl --context=<ctx> -n <ns> get secret <pullsecret> -o json | jq '{name: .metadata.name, type: .type, keys: (.data | keys)}'
# ⚠ Never output raw .data values — they contain encoded credentials
```

### `Pending` — insufficient resources

```bash
kubectl --context=<ctx> get nodes -o wide
kubectl --context=<ctx> top nodes
```

**Fix:** Wait for Karpenter to provision new nodes, or reduce resource requests.

### `Pending` — no matching nodes

```bash
kubectl --context=<ctx> -n <ns> describe pod <pod>
# Look in Events for scheduling failures
```

**Fix:** Check `deployment.nodeSelector`, `tolerations`, and `capacityType` in helmfile values.

### `Pending` — PVC not bound

```bash
kubectl --context=<ctx> -n <ns> get pvc
```

**Fix:** Verify storageClassName exists and EBS CSI driver is healthy.

### `Init:Error` or `Init:CrashLoopBackOff`

```bash
# List init containers to find the failing one
kubectl --context=<ctx> -n <ns> get pod <pod> -o jsonpath='{.spec.initContainers[*].name}'

# Get logs from the failing init container
kubectl --context=<ctx> -n <ns> logs <pod> -c <init-container-name>
```

**Fix:** The most common cause is Vault agent init failure. Diagnose with:
```bash
# Check Vault agent init logs specifically
kubectl --context=<ctx> -n <ns> logs <pod> -c vault-agent-init

# Inspect Vault annotations on the pod to verify role/path config
kubectl --context=<ctx> -n <ns> get pod <pod> -o json | \
  jq '.metadata.annotations | with_entries(select(.key | startswith("vault.hashicorp.com")))'
```
Verify the Vault role exists, the Kubernetes service account is bound to it, and the Vault policy grants access to the requested secret paths.

### `ContainerCreating` (stuck)

```bash
kubectl --context=<ctx> -n <ns> describe pod <pod>
# Look in Events for "MountVolume.SetUp failed" or CSI errors
```

**Fix:** Verify ConfigMaps and Secrets exist. Check CSI driver health.

### `Evicted`

```bash
kubectl --context=<ctx> -n <ns> describe pod <pod>
# Look for eviction reason
kubectl --context=<ctx> describe node <node>
# Check for MemoryPressure, DiskPressure conditions
```

**Fix:** Set resource requests to improve QoS class (Guaranteed QoS is evicted last), or investigate node pressure.

---

## Helm/Helmfile Failures

### "values don't meet the specifications of the schema"

Schema validation failed against `values.schema.json`. Check the error message for the specific field.

**Fix:** See `basic-application-values.md` Common Misconfigurations table.

### "UPGRADE FAILED: timed out"

```bash
kubectl --context=<ctx> -n <ns> get pods -l app.kubernetes.io/name=<app>
```

**Fix:** Pods are not becoming Ready. Usually a readiness probe failure or CrashLoopBackOff — see Pod Failures above.

### "rendered manifests contain a resource that already exists"

```bash
kubectl --context=<ctx> -n <ns> get <resource> -o yaml
# Check labels: app.kubernetes.io/managed-by should be "Helm"
```

**Fix:** Re-apply the correct Helm ownership metadata. See `helm-helmfile-debugging.md` for the label and annotation commands.

### "cannot patch ... field is immutable"

Check which field changed with `helmfile diff`.

**Fix:** Use force-sync mode in `deploy-helmfile` workflow. Warning: this causes brief downtime as the resource is deleted and recreated.

### Release stuck in `pending-upgrade`

```bash
helm --kube-context=<ctx> -n <ns> history <app>
```

**Fix (Helm State Recovery only):** Rollback to last successful revision to unstick the Helm release state:
```bash
# ⚠ MUTATION — reverts Helm release to a previous revision. Confirm with user.
helm --kube-context=<ctx> -n <ns> rollback <app> <revision>
```
> **Note:** This is **Helm State Recovery** — it only fixes the Helm release state (e.g., `pending-upgrade` → `deployed`). It does **not** safely roll back Argo Rollout workloads. For an **Application Rollback** (reverting to a previous image/version), use the `rollback-helmfile` workflow or manual `helm upgrade` per the procedures in `argo-rollouts-guide.md`.

### Helmfile diff shows unexpected changes

```bash
helm --kube-context=<ctx> -n <ns> get values <app>
```

**Fix:** Pin chart version in helmfile. Compare values between revisions to find the drift.

### "context deadline exceeded"

```bash
kubectl --context=<ctx> cluster-info
```

**Fix:** Cluster auth timeout. Check cluster reachability and AWS SSO token expiry (`aws sso login --sso-session one-eks`).

---

## Argo Rollouts Failures

### Rollout `Degraded`

```bash
kubectl argo rollouts --context=<ctx> -n <ns> get rollout <app>
```

**Fix:** New revision pods are failing — check pod status (see Pod Failures above). Then abort:
```bash
# ⚠ MUTATION — aborts the rollout and reverts traffic to stable. Confirm with user.
kubectl argo rollouts --context=<ctx> -n <ns> abort <app>
```

### Rollout `Paused` (unexpected)

```bash
kubectl argo rollouts --context=<ctx> -n <ns> get rollout <app>
```

Canary is waiting for manual promotion. Either promote or abort:
```bash
# ⚠ MUTATION — promote shifts traffic to canary. Confirm with user.
kubectl argo rollouts --context=<ctx> -n <ns> promote <app>
# ⚠ MUTATION — aborts the rollout and reverts traffic to stable. Confirm with user.
kubectl argo rollouts --context=<ctx> -n <ns> abort <app>
```

### Canary stuck at low percentage

```bash
kubectl --context=<ctx> -n <ns> get pods -l rollouts-pod-template-hash
```

**Fix:** Preview pods are not Ready. Check canary pod logs and events.

### Rollout not progressing

```bash
kubectl --context=<ctx> -n <ns> get hpa
kubectl --context=<ctx> -n <ns> get scaledobject
```

**Fix:** Possible HPA/ScaledObject conflict. Check KEDA ScaledObject status and HPA ownership.

### Old Deployment still running (migration)

```bash
kubectl --context=<ctx> -n <ns> get deployment <app>
```

Expected behavior: migration Deployments auto-scale to 0 after 1 week. If needed immediately:
```bash
# ⚠ MUTATION — scales deployment to zero replicas. Confirm with user.
kubectl --context=<ctx> -n <ns> scale deployment <app> --replicas=0
```

---

## Networking / Istio Failures

### `503 Service Unavailable`

```bash
istioctl --context=<ctx> -n <ns> analyze
```

**Fix:** Usually an Istio mTLS mismatch. Check DestinationRule TLS mode — should be `ISTIO_MUTUAL`.

### `503 no healthy upstream`

```bash
kubectl --context=<ctx> -n <ns> get endpoints <app>
```

**Fix:** No ready endpoints. Check if pods are Ready and Service selector matches pod labels.

### `403 RBAC: access denied`

```bash
kubectl --context=<ctx> -n <ns> get authorizationpolicy -o yaml
```

**Fix:** Add an ALLOW rule for the calling service's principal (`cluster.local/ns/<ns>/sa/<sa>`).

### `404 Not Found`

```bash
kubectl --context=<ctx> -n <ns> get vs <app> -o yaml
```

**Fix:** VirtualService routing mismatch. Verify `.spec.hosts` matches the request's Host header.

### Connection timeout to external service

```bash
kubectl --context=<ctx> -n <ns> get serviceentry
```

**Fix:** Missing ServiceEntry. Add one for the external host if Istio outbound policy is `REGISTRY_ONLY`.

### Intermittent 5xx during deployment

```bash
kubectl argo rollouts --context=<ctx> -n <ns> get rollout <app>
```

Expected during canary — traffic is split between old and new versions. Abort if the new version is broken.

### JWT validation failure (401)

```bash
kubectl --context=<ctx> -n <ns> get requestauthentication -o yaml
```

**Fix:** Check issuer, JWKS URI, and audience fields match the incoming token.

---

## Autoscaling Failures

### Pods not scaling up

```bash
kubectl --context=<ctx> -n <ns> get scaledobject <app> -o yaml
```

**Fix:** KEDA ScaledObject misconfigured. Check trigger thresholds and authentication.

### Too many pods (over-scaling)

```bash
kubectl --context=<ctx> -n <ns> get hpa -o json
# Check currentReplicas vs desiredReplicas
```

**Fix:** KEDA trigger is too sensitive. Adjust trigger thresholds or increase `cooldownPeriod`.

### HPA shows `<unknown>` for metrics

```bash
kubectl --context=<ctx> -n <ns> describe hpa
```

**Fix:** Metrics server or KEDA not reporting. Check KEDA operator logs and verify TriggerAuthentication credentials.

### Kafka lag trigger not working

```bash
kubectl --context=<ctx> -n keda logs -l app=keda-operator --tail=100
kubectl --context=<ctx> -n <ns> get triggerauthentication -o yaml
```

**Fix:** Ensure the Kafka cluster name matches supported clusters (`default-euw1-*`, `default-apse2-*`, `default-usw2-*`, `stag`, `duck`).

---

## Policy Failures

### Pod creation blocked by Kyverno

```bash
kubectl --context=<ctx> -n <ns> get policyreport -o json
# Look for results where .result == "fail"
kubectl --context=<ctx> get clusterpolicy
```

**Fix:** Add required labels/annotations per the policy violation message.

### Admission webhook timeout

```bash
kubectl --context=<ctx> get mutatingwebhookconfigurations
# Check for kyverno webhooks
```

**Fix:** Kyverno webhook is slow or down. Escalate to CPS team if Kyverno is unhealthy.

---

## CI/CD Failures

### Workflow failed at "deploy" step

Helmfile sync error. Check GitHub Actions workflow logs for the exact error, then see Helm/Helmfile Failures above.

### Workflow failed at "check-rollout-status"

```bash
kubectl argo rollouts --context=<ctx> -n <ns> get rollout <app>
```

Argo Rollout did not complete. See Argo Rollouts Failures above.

### Deployment protection rules blocked

Missing environment approval. Check GitHub repository settings under Environments.

**Fix:** Request approval or adjust protection rules.

### Slack notification failed

Check workflow logs for Slack API errors.

**Fix:** Verify `slack-channel-id-for-*` inputs and bot token permissions.

### DORA message failed

Check the `setup-ci` step output.

**Fix:** Verify the app is registered in PlatformMetadata.
