# kubectl Recipes for JET OneEKS

Categorized kubectl commands for debugging. All commands include `--context` and `-n` flags for safety. JSON output variants are provided for agent-parseable responses.

## Pod Inspection

```bash
# List pods with status and restart counts
kubectl --context=<ctx> -n <ns> get pods -l app.kubernetes.io/name=<app> -o wide

# JSON: pod status, conditions, container statuses
kubectl --context=<ctx> -n <ns> get pods -l app.kubernetes.io/name=<app> -o json | \
  jq '.items[] | {
    name: .metadata.name,
    phase: .status.phase,
    conditions: .status.conditions,
    containers: [.status.containerStatuses[]? | {
      name: .name,
      ready: .ready,
      restartCount: .restartCount,
      state: .state
    }]
  }'

# Detailed pod description (events, volumes, conditions)
kubectl --context=<ctx> -n <ns> describe pod <pod>

# JSON: pod spec and status combined
kubectl --context=<ctx> -n <ns> get pod <pod> -o json

# Check all containers in a pod (including init containers)
kubectl --context=<ctx> -n <ns> get pod <pod> -o jsonpath='{range .spec.containers[*]}{.name}{"\n"}{end}'
kubectl --context=<ctx> -n <ns> get pod <pod> -o jsonpath='{range .spec.initContainers[*]}{.name}{"\n"}{end}'
```

## Logs

```bash
# Current container logs (last 200 lines)
kubectl --context=<ctx> -n <ns> logs <pod> --tail=200

# Previous container instance (after crash)
kubectl --context=<ctx> -n <ns> logs <pod> --previous --tail=200

# Specific container in multi-container pod
kubectl --context=<ctx> -n <ns> logs <pod> -c <container> --tail=200

# Logs from all pods matching a label (requires stern for better output)
kubectl --context=<ctx> -n <ns> logs -l app.kubernetes.io/name=<app> --tail=50 --prefix

# Logs with timestamps
kubectl --context=<ctx> -n <ns> logs <pod> --timestamps --tail=200

# Logs since a specific time
kubectl --context=<ctx> -n <ns> logs <pod> --since=30m
```

## Events

```bash
# All events in namespace (sorted by time, most recent last)
# Note: .lastTimestamp is deprecated in K8s 1.25+; use .metadata.creationTimestamp
kubectl --context=<ctx> -n <ns> get events --sort-by='.metadata.creationTimestamp'

# Events for a specific pod
kubectl --context=<ctx> -n <ns> get events --field-selector involvedObject.name=<pod> --sort-by='.metadata.creationTimestamp'

# JSON: events with type filtering (Warning events only)
kubectl --context=<ctx> -n <ns> get events --field-selector type=Warning -o json | \
  jq '.items[] | {time: .metadata.creationTimestamp, reason: .reason, message: .message, object: .involvedObject.name}'

# Events for all pods whose name starts with <app>
kubectl --context=<ctx> -n <ns> get events --field-selector involvedObject.kind=Pod -o json | \
  jq '[.items[] | select(.involvedObject.name | startswith("<app>"))] | sort_by(.metadata.creationTimestamp) | .[-10:]'
```

## Resource Usage

```bash
# Current CPU and memory usage per pod
kubectl --context=<ctx> -n <ns> top pods -l app.kubernetes.io/name=<app>

# Node-level resource usage
kubectl --context=<ctx> top nodes

# JSON: resource requests vs limits for an app
kubectl --context=<ctx> -n <ns> get pods -l app.kubernetes.io/name=<app> -o json | \
  jq '.items[] | {name: .metadata.name, containers: [.spec.containers[] | {name: .name, requests: .resources.requests, limits: .resources.limits}]}'

# Check if pods are being throttled (compare top output vs limits)
# If CPU usage is consistently near the limit, the pod is likely throttled.
```

## Rollouts (Argo)

```bash
# Rollout status overview
kubectl argo rollouts --context=<ctx> -n <ns> status <app>

# Detailed rollout info (steps, revisions, pods per revision)
kubectl argo rollouts --context=<ctx> -n <ns> get rollout <app>

# JSON: rollout status
kubectl --context=<ctx> -n <ns> get rollout <app> -o json | \
  jq '{status: .status.phase, message: .status.message, currentStepIndex: .status.currentStepIndex, stableRS: .status.stableRS, canary: .status.canary}'

# List all rollouts in namespace
kubectl --context=<ctx> -n <ns> get rollouts

# Watch rollout progress in real-time
kubectl argo rollouts --context=<ctx> -n <ns> get rollout <app> --watch
```

## Helm Releases

```bash
# Release history (last 5 revisions)
helm --kube-context=<ctx> -n <ns> history <app> --max 5

# Current deployed values
helm --kube-context=<ctx> -n <ns> get values <app>

# Values for a specific revision (for comparison)
helm --kube-context=<ctx> -n <ns> get values <app> --revision <N>

# All values including defaults
helm --kube-context=<ctx> -n <ns> get values <app> --all

# Rendered manifest of current release
helm --kube-context=<ctx> -n <ns> get manifest <app>

# Release status
helm --kube-context=<ctx> -n <ns> status <app> --show-resources
```

## ConfigMaps and Secrets

```bash
# List configmaps for app (note: basic-application uses hash-suffixed names)
kubectl --context=<ctx> -n <ns> get configmap -l app.kubernetes.io/name=<app>

# View configmap data
kubectl --context=<ctx> -n <ns> get configmap <name> -o yaml

# List secrets for app
kubectl --context=<ctx> -n <ns> get secret -l app.kubernetes.io/name=<app>

# List secret keys (without exposing values)
kubectl --context=<ctx> -n <ns> get secret <name> -o json | jq '{name: .metadata.name, keys: (.data | keys)}'
# ⚠ Never decode secret values in terminal output — risk of leaking credentials into logs/history

# Find stale hash-suffixed configmaps (not referenced by current pods)
# basic-application creates configmaps like <app>-<sha256[:8]>
# Old ones are kept (resource-policy: keep) and can accumulate.
kubectl --context=<ctx> -n <ns> get configmap -l app.kubernetes.io/name=<app> --sort-by='.metadata.creationTimestamp'
```

## Networking and Services

```bash
# List services
kubectl --context=<ctx> -n <ns> get svc -l app.kubernetes.io/name=<app>

# Check service endpoints (are pods registered?)
kubectl --context=<ctx> -n <ns> get endpoints <app>

# JSON: endpoint addresses
kubectl --context=<ctx> -n <ns> get endpoints <app> -o json | \
  jq '.subsets[]? | {addresses: [.addresses[]?.ip], ports: [.ports[]? | {port: .port, protocol: .protocol}]}'

# VirtualService configuration
kubectl --context=<ctx> -n <ns> get vs -o yaml

# DestinationRule configuration
kubectl --context=<ctx> -n <ns> get dr -o yaml

# AuthorizationPolicy rules
kubectl --context=<ctx> -n <ns> get authorizationpolicy -o yaml
```

## Autoscaling (KEDA)

```bash
# ScaledObject status
kubectl --context=<ctx> -n <ns> get scaledobject <app> -o yaml

# HPA created by KEDA
kubectl --context=<ctx> -n <ns> get hpa

# JSON: HPA current vs desired replicas
kubectl --context=<ctx> -n <ns> get hpa -o json | \
  jq '.items[] | {name: .metadata.name, minReplicas: .spec.minReplicas, maxReplicas: .spec.maxReplicas, currentReplicas: .status.currentReplicas, desiredReplicas: .status.desiredReplicas, conditions: .status.conditions}'

# KEDA trigger details
kubectl --context=<ctx> -n <ns> get triggerauthentication
```

## Nodes

```bash
# Node list with status and roles
kubectl --context=<ctx> get nodes -o wide

# Check node conditions (Ready, MemoryPressure, DiskPressure)
kubectl --context=<ctx> get nodes -o json | \
  jq '.items[] | {name: .metadata.name, conditions: [.status.conditions[] | {type: .type, status: .status}]}'

# Node labels (for scheduling/affinity debugging)
kubectl --context=<ctx> get nodes --show-labels

# Check Karpenter provisioner capacity
kubectl --context=<ctx> get nodeclaims
kubectl --context=<ctx> get nodepools
```

## Kyverno Policies

```bash
# Check policy reports for violations
kubectl --context=<ctx> -n <ns> get policyreport -o json | \
  jq '.items[]? | {name: .metadata.name, results: [.results[]? | select(.result == "fail") | {policy: .policy, rule: .rule, message: .message}]}'

# List cluster policies
kubectl --context=<ctx> get clusterpolicy

# Check admission reports (recent policy evaluations)
kubectl --context=<ctx> -n <ns> get admissionreport
```
