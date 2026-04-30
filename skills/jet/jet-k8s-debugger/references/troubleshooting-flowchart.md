# Troubleshooting Flowchart

Step-by-step decision trees for diagnosing the most common failure categories in JET OneEKS clusters.

## Before Diagnosis: Establish Target Context

Before running any diagnosis flow, identify which cluster you are debugging:

```bash
# Check the currently active context
kubectl config current-context 2>/dev/null

# List all JET contexts available in kubeconfig
# (matches canonical names AND team aliases via the cluster ARN column)
kubectl config get-contexts --no-headers | \
  grep -E '(euw1|apse2|usw2)-[a-z]+-[a-z]+-[0-9]+'
```

- If the current context matches a JET pattern, use it as `<ctx>` throughout.
- If multiple JET contexts exist, ask the user which cluster to debug.
- If no JET contexts are found, guide the user to run `aws eks update-kubeconfig --profile <cluster> --name <cluster> --alias <cluster>` first.

Once `<ctx>` is confirmed, substitute it in every command below.

## Flow 1: Deployment Failed

The `deploy-helmfile` workflow reported a failure, or `helmfile sync` did not complete successfully.

```
Deployment failed
├── Check helmfile output for error message
│   ├── "Error: UPGRADE FAILED" or "Error: INSTALLATION FAILED"
│   │   ├── "timed out waiting for the condition"
│   │   │   └── Go to → Flow 2: Pods Not Starting
│   │   ├── "rendered manifests contain a resource that already exists"
│   │   │   └── Orphaned resource. Check if a previous release was deleted without cleanup.
│   │   │       kubectl --context=<ctx> -n <ns> get <resource> -l app.kubernetes.io/managed-by=Helm
│   │   │       Fix: Re-label the orphaned resource to the correct Helm release.
│   │   │       See helm-helmfile-debugging.md for the label and annotation commands.
│   │   ├── "cannot patch ... field is immutable"
│   │   │   └── Immutable field change (e.g., Service type, PVC storageClass).
│   │   │       Fix: Use force-sync mode in deploy-helmfile (replaces resources).
│   │   │       WARNING: This causes brief downtime.
│   │   └── "values don't meet the specifications of the schema"
│   │       └── Values validation failed against values.schema.json.
│   │           Common: env var starting with JET_, invalid application.name, wrong strategy config.
│   │           Fix: Check values against schema. See references/basic-application-values.md.
│   ├── "Error: context deadline exceeded"
│   │   └── Cluster auth timeout.
│   │       Verify: kubectl --context=<ctx> cluster-info
│   │       Check AWS SSO token expiry: aws sso login --sso-session one-eks
│   ├── Kyverno policy violation
│   │   └── kubectl --context=<ctx> -n <ns> get policyreport -o json
│   │       Common: missing required labels, disallowed image registries, privileged containers.
│   │       Fix: Add required labels/annotations per Kyverno policy.
│   └── "helmfile" command not found or version mismatch
│       └── Check helmfile version matches workflow input. JET uses helmfile v0.x and v1.x.
│           helmfile version
└── If no clear error
    ├── Check GitHub Actions workflow logs for the exact step that failed
    ├── Check if deployment protection rules blocked the deployment
    └── Check if the cluster is reachable from the runner
```

## Flow 2: Pods Not Starting

Pods are in `Pending`, `CrashLoopBackOff`, `ImagePullBackOff`, `Init:Error`, or `ContainerCreating` states.

```
Pods not starting
├── kubectl --context=<ctx> -n <ns> get pods -l app.kubernetes.io/name=<app>
│
├── Status: Pending
│   ├── kubectl --context=<ctx> -n <ns> describe pod <pod> → look at Events section
│   ├── "Insufficient cpu" or "Insufficient memory"
│   │   └── Cluster capacity exhausted. Check node availability:
│   │       kubectl --context=<ctx> get nodes -o wide
│   │       kubectl --context=<ctx> top nodes
│   │       Wait for Karpenter to provision new nodes, or reduce resource requests.
│   ├── "no nodes available to schedule pods" + affinity/taint issues
│   │   └── Check nodeSelector and tolerations in values:
│   │       helm --kube-context=<ctx> -n <ns> get values <app> | grep -A5 nodeSelector
│   │       helm --kube-context=<ctx> -n <ns> get values <app> | grep -A5 tolerations
│   │       Check: deployment.capacityType (spot vs on-demand)
│   └── "persistentvolumeclaim ... not found"
│       └── PVC not provisioned. Check PVC status:
│           kubectl --context=<ctx> -n <ns> get pvc
│
├── Status: ImagePullBackOff
│   ├── kubectl --context=<ctx> -n <ns> describe pod <pod> → Events → "Failed to pull image"
│   ├── "unauthorized: authentication required"
│   │   └── Artifactory credentials expired or missing.
│   │       Check image pull secret keys: kubectl --context=<ctx> -n <ns> get secret <pullsecret> -o json | jq '{name: .metadata.name, type: .type, keys: (.data | keys)}'
│   │       Verify image exists: check artifacts.takeaway.com for the tag.
│   └── "manifest unknown" or "not found"
│       └── Image tag does not exist. Verify the correct tag was built and pushed.
│           Check CI build job output for the pushed image:tag.
│
├── Status: CrashLoopBackOff
│   ├── kubectl --context=<ctx> -n <ns> logs <pod> --previous --tail=200
│   ├── Exit code 1 — application error
│   │   └── Check logs for stack traces, missing config, connection failures.
│   │       Common: missing env vars, wrong DB connection string, missing secrets.
│   ├── Exit code 137 — SIGKILL (most commonly OOMKilled)
│   │   └── kubectl --context=<ctx> -n <ns> describe pod <pod> | grep -A3 "Last State"
│   │       Fix: Increase deployment.resources.limits.memory in helmfile values.
│   │       Verify current: kubectl --context=<ctx> -n <ns> top pods -l app.kubernetes.io/name=<app>
│   └── Exit code 143 — SIGTERM (process terminated by signal, e.g., rolling update or scale-down)
│       └── Two common causes:
│           1. App's graceful shutdown is too slow — increase terminationGracePeriodSeconds
│           2. Liveness probe failure is triggering the SIGTERM — check probe config:
│              kubectl --context=<ctx> -n <ns> get pod <pod> -o json | jq '.spec.containers[].livenessProbe'
│
├── Status: Init:Error or Init:CrashLoopBackOff
│   └── Init container failed. Check init container logs:
│       kubectl --context=<ctx> -n <ns> logs <pod> -c <init-container-name>
│       Common: Vault agent init failed (check Vault connectivity, role, policy).
│
└── Status: ContainerCreating (stuck)
    ├── kubectl --context=<ctx> -n <ns> describe pod <pod> → Events
    ├── "MountVolume.SetUp failed"
    │   └── Secret or ConfigMap not found. Check if helmfile rendered them:
    │       kubectl --context=<ctx> -n <ns> get configmap -l app.kubernetes.io/name=<app>
    │       kubectl --context=<ctx> -n <ns> get secret -l app.kubernetes.io/name=<app>
    └── CSI driver timeout
        └── EBS volume attach issue. Check node capacity for volumes.
```

## Flow 3: Service Unhealthy (Running but Errors)

Pods are running but the service returns errors (5xx, timeouts, connection refused).

```
Service unhealthy
├── Verify pods are Ready (all containers passing readiness probes)
│   kubectl --context=<ctx> -n <ns> get pods -l app.kubernetes.io/name=<app>
│   Look for READY column: should be N/N (e.g., 2/2)
│
├── If pods are Ready but 503s
│   ├── Check Istio VirtualService routing
│   │   kubectl --context=<ctx> -n <ns> get vs <app> -o yaml
│   │   Verify hosts, destination service, and port match.
│   ├── Check Istio DestinationRule
│   │   kubectl --context=<ctx> -n <ns> get dr <app> -o yaml
│   │   Look for TLS mode mismatch (ISTIO_MUTUAL vs DISABLE).
│   ├── Check AuthorizationPolicy
│   │   kubectl --context=<ctx> -n <ns> get authorizationpolicy -o yaml
│   │   Look for missing allow rules for the calling service.
│   └── See references/istio-debugging.md for detailed Istio diagnosis.
│
├── If pods are Ready but timeouts
│   ├── Check resource utilization — is the pod CPU-throttled?
│   │   kubectl --context=<ctx> -n <ns> top pods -l app.kubernetes.io/name=<app>
│   │   Compare against resource limits.
│   ├── Check if KEDA is scaling correctly
│   │   kubectl --context=<ctx> -n <ns> get scaledobject <app> -o yaml
│   │   kubectl --context=<ctx> -n <ns> get hpa
│   └── Check downstream dependencies — is the app waiting on DB, cache, or another service?
│       If the jet-datadog skill is available:
│         pup apm dependencies list --env=<env>   # Use the actual environment: prod, staging, etc.
│       Otherwise check Datadog APM manually:
│         https://app.datadoghq.eu/apm/services?env=<env>&search=<app>
│
└── If intermittent errors during deployment
    ├── Canary in progress — traffic is split between old and new versions
    │   kubectl argo rollouts --context=<ctx> -n <ns> get rollout <app>
    │   Check canary step: small percentage may be hitting the new (broken) version.
    │   # ⚠ MUTATION — confirm with user before aborting
    │   Fix: kubectl argo rollouts --context=<ctx> -n <ns> abort <app>
    └── Rolling update — old pods are being terminated before new ones are ready
        Check: deployment.minReadySeconds and readiness probe configuration.
```

## Flow 4: Rollout Stuck or Degraded

Argo Rollout is not progressing or is in a degraded state.

```
Rollout stuck/degraded
├── kubectl argo rollouts --context=<ctx> -n <ns> get rollout <app>
│   (If kubectl-argo-rollouts not installed: kubectl --context=<ctx> -n <ns> get rollout <app> -o yaml | grep -A5 'status:')
│
├── Status: Paused
│   └── Canary is paused waiting for manual promotion.
│       # ⚠ MUTATION — confirm with user before promoting or aborting
│       Promote: kubectl argo rollouts --context=<ctx> -n <ns> promote <app>
│       Abort:   kubectl argo rollouts --context=<ctx> -n <ns> abort <app>
│
├── Status: Degraded
│   ├── Check rollout events
│   │   kubectl --context=<ctx> -n <ns> describe rollout <app> | grep -A20 Events
│   ├── New ReplicaSet pods failing — Go to Flow 2
│   └── Analysis run failed (if using analysis templates)
│       kubectl --context=<ctx> -n <ns> get analysisrun -l rollouts-pod-template-hash
│
├── Status: Progressing (but stuck at a step for too long)
│   └── Check if new pods are Ready:
│       kubectl --context=<ctx> -n <ns> get pods -l rollouts-pod-template-hash=<new-hash>
│       If pods are not Ready → Go to Flow 2
│
└── Need to rollback
    └── See references/argo-rollouts-guide.md for rollback procedures.
```
