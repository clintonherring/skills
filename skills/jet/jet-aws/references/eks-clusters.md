# EKS Cluster Topology & Kubernetes Patterns

## Table of Contents

1. [Legacy EKS Clusters](#legacy-eks-clusters)
2. [Sonic Runtime (OneEKS) Clusters](#sonic-runtime-oneeks-clusters)
3. [Profile-to-Cluster Mapping](#profile-to-cluster-mapping)
4. [Kubectl Setup](#kubectl-setup)
5. [Common Kubectl Commands](#common-kubectl-commands)
6. [Debugging & Troubleshooting Pods](#debugging--troubleshooting-pods)
7. [Resource Inspection](#resource-inspection)
8. [Helmfile Golden Path](#helmfile-golden-path)
9. [DNS Patterns](#dns-patterns)
10. [Namespace Conventions](#namespace-conventions)
11. [Secrets Management](#secrets-management)
12. [IRSA & Workload Roles](#irsa--workload-roles)
13. [Deployment Methods](#deployment-methods)
14. [Migration Paths](#migration-paths)
15. [Troubleshooting](#troubleshooting)

---

## Legacy EKS Clusters

Legacy clusters managed by SRE and CloudOps. Being phased out in favour of Sonic Runtime.

| Cluster Name | AWS Account (Profile) | kubectl Profile | Region |
|-------------|----------------------|-----------------|--------|
| `eks-cluster-dev` | 149679936287 (`cloudops-dev`) | `eks-cluster-dev-eks` | eu-west-1 |
| `eks-cluster-staging-2` | 917668556676 (`takeaway-staging`) | `takeaway-staging-eks` | eu-west-1 |
| `eks-cluster-prod` | 868502343283 (`takeaway-production`) | `takeaway-production-eks` | eu-west-1 |
| `eks-cluster-prod-ap` | (ap-southeast-2 account) | - | ap-southeast-2 |

**Key differences from Sonic Runtime:**
- Use `cloudops-platform-user` role for kubectl (separate `-eks` profile)
- Use `admin` role for AWS console / resource management
- Helm releases use `sre/basic-application` chart via helmfile
- Recommended kubectl version: 1.30

## Sonic Runtime (OneEKS) Clusters

New platform with multi-bulkhead architecture. Cluster names match AWS profile names.

### EU1 Bulkhead (eu-west-1) — Primary

| Env | Cluster / Profile | Account ID |
|-----|------------------|-----------|
| QA | `euw1-pdv-qa-2` | 149679936287 |
| Staging | `euw1-pdv-stg-5` | 917668556676 |
| Production | `euw1-pdv-prd-5` | 868502343283 |

EU1 is the recommended starting point for migrations. Has access to legacy Takeaway Vault secrets.

### EU2 Bulkhead (eu-west-1)

| Env | Cluster / Profile | Account ID |
|-----|------------------|-----------|
| QA | `euw1-pdv-qa-3` | 891377069564 |
| Staging | `euw1-pdv-stg-6` | 851725494124 |
| Production | `euw1-pdv-prd-6` | 654654467576 |

### OC1 Bulkhead (ap-southeast-2)

| Env | Cluster / Profile | Account ID |
|-----|------------------|-----------|
| QA | `apse2-pdv-qa-2` | 992382780937 |
| Staging | `apse2-pdv-stg-2` | 581114218460 |
| Production | `apse2-pdv-prd-3` | 901113000551 |

### NA1 Bulkhead (us-west-2)

| Env | Cluster / Profile | Account ID |
|-----|------------------|-----------|
| QA | `usw2-pdv-qa-1` | 242031136599 |
| Staging | `usw2-pdv-stg-1` | 891377176256 |
| Production | `usw2-pdv-prd-2` | 992382718146 |

### Platform Clusters (plt)

| Env | Cluster / Profile | Account ID | Region |
|-----|------------------|-----------|--------|
| Staging | `euw1-plt-stg-2` | 851725319446 | eu-west-1 |
| Production | `euw1-plt-prd-2` | 058264529639 | eu-west-1 |
| Production | `apse2-plt-prd-1` | 654654425804 | ap-southeast-2 |
| Production | `usw2-plt-prd-2` | 471112928224 | us-west-2 |

### Platform Management Clusters (pmt)

| Env | Cluster / Profile | Account ID | Region |
|-----|------------------|-----------|--------|
| Staging | `euw1-pmt-stg-1` | 043449893185 | eu-west-1 |
| Production | `euw1-pmt-prd-1` | 674832384991 | eu-west-1 |
| Staging | `apse2-pmt-stg-1` | 024345218262 | ap-southeast-2 |
| Production | `apse2-pmt-prd-1` | 576596237931 | ap-southeast-2 |

## Profile-to-Cluster Mapping

### Legacy: Use separate `-eks` profiles for kubectl

```bash
# Profile for kubectl          → Profile for AWS resources
eks-cluster-dev-eks            → cloudops-dev (or eks-cluster-dev)
takeaway-staging-eks           → takeaway-staging
takeaway-production-eks        → takeaway-production
```

### Sonic Runtime: Profile name = cluster name

```bash
# Same profile for both kubectl and AWS resources
aws eks update-kubeconfig --profile euw1-pdv-prd-5 --name euw1-pdv-prd-5
kubectl --context euw1-pdv-prd-5 get pods -n <namespace>
```

## Kubectl Setup

### Prerequisites

```bash
# Install tools (macOS/Linux)
brew install awscli kubectl k9s kubectx helm helmfile
```

```powershell
# Install tools available via winget
winget install Amazon.AWSCLI
winget install Kubernetes.kubectl
winget install Derailed.k9s
winget install ahmetb.kubectx
winget install Helm.Helm

# helmfile is not currently available in winget
scoop install helmfile
```

### Version Requirements

| Platform | Recommended kubectl |
|----------|-------------------|
| Legacy EKS | 1.30 |
| Sonic Runtime | 1.32 |

### Configure Kubeconfig

```bash
# Legacy EKS
aws sso login --profile eks-cluster-dev-eks
aws eks update-kubeconfig --profile eks-cluster-dev-eks --name eks-cluster-dev --alias eks-cluster-dev

# Sonic Runtime
aws sso login --profile euw1-pdv-stg-5
aws eks update-kubeconfig --profile euw1-pdv-stg-5 --name euw1-pdv-stg-5 --alias euw1-pdv-stg-5
```

### Quick Context Switching

```bash
# Switch context
kubectx euw1-pdv-prd-5

# Switch namespace
kubens <team-namespace>

# Or inline
kubectl --context euw1-pdv-prd-5 -n <namespace> get pods
```

## Common Kubectl Commands

All commands below assume correct context is set (via `kubectx`) and namespace (via `kubens` or `-n`).

### Listing Resources

```bash
# Pods in current namespace
kubectl get pods
kubectl get pods -o wide                    # Show node, IP
kubectl get pods --sort-by=.status.startTime  # Newest last

# All resources in namespace
kubectl get all -n <namespace>

# Deployments, services, ingresses
kubectl get deploy,svc,ing -n <namespace>

# Across all namespaces (careful on prod)
kubectl get pods -A | grep <app-name>

# Jobs and CronJobs
kubectl get jobs,cronjobs -n <namespace>

# ConfigMaps and Secrets (names only)
kubectl get cm,secret -n <namespace>
```

### Inspecting Resources

```bash
# Detailed pod info (events, conditions, containers, volumes)
kubectl describe pod <pod-name> -n <namespace>

# Deployment details (strategy, replicas, conditions)
kubectl describe deploy <deploy-name> -n <namespace>

# Service endpoints
kubectl describe svc <svc-name> -n <namespace>

# Get YAML of any resource
kubectl get pod <pod-name> -n <namespace> -o yaml

# Get specific field via jsonpath
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.status.phase}'

# Get container image versions
kubectl get pods -n <namespace> -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[*].image}{"\n"}{end}'
```

### Logs

```bash
# Current logs
kubectl logs <pod-name> -n <namespace>

# Follow logs (stream)
kubectl logs -f <pod-name> -n <namespace>

# Specific container (multi-container pods)
kubectl logs <pod-name> -c <container-name> -n <namespace>

# Previous container instance (after restart/crash)
kubectl logs <pod-name> --previous -n <namespace>

# Last N lines
kubectl logs <pod-name> --tail=100 -n <namespace>

# Logs since a time
kubectl logs <pod-name> --since=1h -n <namespace>

# All pods for a deployment
kubectl logs -l app=<app-name> -n <namespace> --tail=50

# Init container logs (useful for debugging startup failures)
kubectl logs <pod-name> -c <init-container-name> -n <namespace>
```

### Exec & Port-Forward

```bash
# Shell into a pod
kubectl exec -it <pod-name> -n <namespace> -- /bin/sh
kubectl exec -it <pod-name> -n <namespace> -- /bin/bash

# Run a single command
kubectl exec <pod-name> -n <namespace> -- env
kubectl exec <pod-name> -n <namespace> -- cat /etc/config/app.yaml
kubectl exec <pod-name> -n <namespace> -- curl -s localhost:8080/health

# Specific container
kubectl exec -it <pod-name> -c <container-name> -n <namespace> -- /bin/sh

# Port-forward to a pod
kubectl port-forward <pod-name> 8080:8080 -n <namespace>

# Port-forward to a service
kubectl port-forward svc/<svc-name> 8080:80 -n <namespace>
```

### Rollouts

```bash
# Check rollout status
kubectl rollout status deploy/<deploy-name> -n <namespace>

# Rollout history
kubectl rollout history deploy/<deploy-name> -n <namespace>

# Rollback to previous revision
kubectl rollout undo deploy/<deploy-name> -n <namespace>

# Rollback to specific revision
kubectl rollout undo deploy/<deploy-name> --to-revision=3 -n <namespace>

# Restart pods (rolling restart)
kubectl rollout restart deploy/<deploy-name> -n <namespace>
```

### Events

```bash
# All events in namespace (sorted by time)
kubectl get events -n <namespace> --sort-by='.lastTimestamp'

# Warning events only
kubectl get events -n <namespace> --field-selector type=Warning

# Events for a specific pod
kubectl get events -n <namespace> --field-selector involvedObject.name=<pod-name>
```

### Useful kubectl Plugins

| Plugin | Install (MacOS/Linux) | Install (Windows PowerShell) | Purpose |
|--------|-----------------------|-------------------|---------|
| `kubectx` | `brew install kubectx` | `winget install ahmetb.kubectx` | Fast context switching (`kubectx <ctx>`) |
| `kubens` | Included with kubectx | Included with kubectx | Fast namespace switching (`kubens <ns>`) |
| `k9s` | `brew install k9s` | `winget install Derailed.k9s` | Terminal UI — browse pods, logs, exec interactively |
| `kubectl neat` | `kubectl krew install neat` | `kubectl krew install neat` | Clean up `kubectl get -o yaml` output (strip managed fields) |
| `kubectl tree` | `kubectl krew install tree` | `kubectl krew install tree` | Show resource ownership hierarchy |

## Debugging & Troubleshooting Pods

### CrashLoopBackOff

Pod starts, crashes, and restarts repeatedly.

```bash
# 1. Check what the exit code is
kubectl describe pod <pod> -n <ns> | grep -A5 "Last State"

# 2. Check logs from the crashed container
kubectl logs <pod> --previous -n <ns>

# 3. Common causes:
#    - Exit code 1: Application error (check app logs)
#    - Exit code 137: OOMKilled (see OOMKilled section below)
#    - Exit code 143: SIGTERM (graceful shutdown failed / timeout)

# 4. If the container crashes too fast to exec in, override the command:
kubectl debug <pod> -it --copy-to=debug-pod --container=<container> -- /bin/sh
```

### OOMKilled

Container exceeded its memory limit.

```bash
# 1. Confirm OOMKilled
kubectl describe pod <pod> -n <ns> | grep -A3 "Last State"
# Look for: Reason: OOMKilled

# 2. Check current memory limits
kubectl get pod <pod> -n <ns> -o jsonpath='{.spec.containers[*].resources}'

# 3. Check actual memory usage (if pod is running)
kubectl top pod <pod> -n <ns>

# 4. Fix: Increase memory limits in Helm values
# Note: ScaleOps may auto-adjust — check ScaleOps annotations first
kubectl get pod <pod> -n <ns> -o jsonpath='{.metadata.annotations}' | grep -i scale
```

### ImagePullBackOff

Container image cannot be pulled.

```bash
# 1. Check the event for the exact error
kubectl describe pod <pod> -n <ns> | grep -A5 "Events"

# 2. Common causes:
#    - Wrong image tag (typo, tag doesn't exist)
#    - ECR auth expired (check imagePullSecrets)
#    - Private registry not accessible from cluster

# 3. Verify the image exists
aws ecr describe-images --profile <profile> \
  --repository-name <repo> --image-ids imageTag=<tag>
```

### Pending Pods

Pod stuck in Pending state — not scheduled to a node.

```bash
# 1. Check why it's pending
kubectl describe pod <pod> -n <ns> | grep -A10 "Events"

# 2. Common causes:
#    - Insufficient resources: "0/N nodes are available: insufficient cpu/memory"
#    - Node selector/affinity mismatch
#    - PVC not bound
#    - Namespace quota exceeded

# 3. Check namespace quotas
kubectl describe resourcequota -n <ns>
kubectl describe limitrange -n <ns>

# 4. Check node capacity
kubectl top nodes
kubectl describe node <node-name> | grep -A10 "Allocated resources"
```

### CreateContainerConfigError

Container can't start due to missing ConfigMap or Secret.

```bash
# 1. Check which configmap/secret is missing
kubectl describe pod <pod> -n <ns> | grep -A5 "Events"

# 2. List available configmaps and secrets
kubectl get cm -n <ns>
kubectl get secret -n <ns>

# 3. Check if env vars reference missing keys
kubectl get pod <pod> -n <ns> -o yaml | grep -A3 "configMapKeyRef\|secretKeyRef"
```

### Pod Stuck Terminating

```bash
# 1. Check if there are finalizers blocking deletion
kubectl get pod <pod> -n <ns> -o jsonpath='{.metadata.finalizers}'

# 2. Force delete (use with caution)
kubectl delete pod <pod> -n <ns> --grace-period=0 --force
```

### Liveness/Readiness Probe Failures

```bash
# 1. Check probe configuration
kubectl get pod <pod> -n <ns> -o jsonpath='{.spec.containers[*].livenessProbe}'
kubectl get pod <pod> -n <ns> -o jsonpath='{.spec.containers[*].readinessProbe}'

# 2. Test the probe endpoint manually
kubectl exec <pod> -n <ns> -- curl -s localhost:<port>/<path>

# 3. Check events for probe failure messages
kubectl get events -n <ns> --field-selector involvedObject.name=<pod> | grep -i unhealthy
```

## Resource Inspection

### Pod Resource Usage

```bash
# Current CPU/memory usage per pod
kubectl top pods -n <namespace>

# Sort by CPU
kubectl top pods -n <namespace> --sort-by=cpu

# Sort by memory
kubectl top pods -n <namespace> --sort-by=memory

# Specific pod's containers
kubectl top pod <pod-name> -n <namespace> --containers
```

### Node Resource Usage

```bash
# Node-level resource usage
kubectl top nodes

# Detailed node allocation
kubectl describe node <node-name> | grep -A20 "Allocated resources"

# List nodes with labels (useful for understanding node pools)
kubectl get nodes --show-labels
kubectl get nodes -L node.kubernetes.io/instance-type
```

### Resource Requests & Limits

```bash
# Show requests/limits for all pods in namespace
kubectl get pods -n <namespace> -o custom-columns=\
"NAME:.metadata.name,\
CPU_REQ:.spec.containers[*].resources.requests.cpu,\
CPU_LIM:.spec.containers[*].resources.limits.cpu,\
MEM_REQ:.spec.containers[*].resources.requests.memory,\
MEM_LIM:.spec.containers[*].resources.limits.memory"

# Check if ScaleOps is managing a deployment
kubectl get deploy <name> -n <namespace> -o jsonpath='{.metadata.annotations}' | grep -i scaleops

# Check actual vs requested (find over/under-provisioned pods)
kubectl top pods -n <namespace>
# Compare with:
kubectl get pods -n <namespace> -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[*].resources.requests.cpu}{"\t"}{.spec.containers[*].resources.requests.memory}{"\n"}{end}'
```

### HPA (Horizontal Pod Autoscaler)

```bash
# List HPAs
kubectl get hpa -n <namespace>

# Detailed HPA status (current vs target metrics)
kubectl describe hpa <hpa-name> -n <namespace>

# Watch HPA scaling in real-time
kubectl get hpa -n <namespace> -w
```

### Namespace Quotas

```bash
# Check resource quotas
kubectl describe resourcequota -n <namespace>

# Check limit ranges
kubectl describe limitrange -n <namespace>

# Check current usage vs quota
kubectl get resourcequota -n <namespace> -o yaml
```

### PersistentVolumes

```bash
# List PVCs in namespace
kubectl get pvc -n <namespace>

# Check PV status and binding
kubectl describe pvc <pvc-name> -n <namespace>

# List all PVs (cluster-wide)
kubectl get pv
```

### Network / Services

```bash
# List services and their endpoints
kubectl get svc -n <namespace>
kubectl get endpoints -n <namespace>

# Check ingress rules
kubectl get ing -n <namespace>
kubectl describe ing <ingress-name> -n <namespace>

# Test DNS resolution from inside a pod
kubectl exec <pod> -n <namespace> -- nslookup <service-name>
kubectl exec <pod> -n <namespace> -- nslookup <service-name>.<namespace>.svc.cluster.local

# Check Istio virtual services (if using service mesh)
kubectl get virtualservice -n <namespace>
kubectl get destinationrule -n <namespace>
```

## Helmfile Golden Path

Standard deployment structure for Sonic Runtime and legacy EKS.

### Directory Layout

```
helmfile.d/
├── bases/
│   ├── helmDefaults.yaml.gotmpl    # Shared helm defaults (timeout, wait, etc.)
│   └── repositories.yaml.gotmpl    # Chart repository definitions
├── helmfile.yaml.gotmpl             # Environment definitions + release specs
├── state_values/
│   ├── defaults.yaml                # Values shared across all environments
│   ├── euw1-pdv-qa-2.yaml          # QA overrides
│   ├── euw1-pdv-stg-5.yaml         # EU1 staging overrides
│   ├── euw1-pdv-prd-5.yaml         # EU1 production overrides
│   ├── euw1-pdv-stg-6.yaml         # EU2 staging overrides
│   └── euw1-pdv-prd-6.yaml         # EU2 production overrides
└── values/
    └── <RELEASE_NAME>.yaml.gotmpl   # Per-release value templates
```

### Chart Repository

```yaml
# In repositories.yaml.gotmpl
repositories:
  - name: sre
    url: https://artifactory.takeaway.com/sre-helm-prod-virtual
```

Standard chart: `sre/basic-application`

### Common Helmfile Commands

```bash
# Lint all environments
helmfile -e euw1-pdv-stg-5 lint

# Diff before applying
helmfile -e euw1-pdv-stg-5 diff

# Apply to staging
helmfile -e euw1-pdv-stg-5 apply

# Apply to production
helmfile -e euw1-pdv-prd-5 apply

# Template render (debug)
helmfile -e euw1-pdv-stg-5 template
```

### Environment Naming in helmfile.yaml.gotmpl

Environment names in helmfile match the cluster names:

```yaml
environments:
  euw1-pdv-qa-2:
    values:
      - state_values/defaults.yaml
      - state_values/euw1-pdv-qa-2.yaml
  euw1-pdv-stg-5:
    values:
      - state_values/defaults.yaml
      - state_values/euw1-pdv-stg-5.yaml
  euw1-pdv-prd-5:
    values:
      - state_values/defaults.yaml
      - state_values/euw1-pdv-prd-5.yaml
```

## DNS Patterns

### Namespaced Global (preferred)

```
<app>.<namespace>.<env_type>.jet-internal.com
```

Example: `myapp.myteam.production.jet-internal.com`

### Environment-Scoped

```
<app>.<namespace>.<env_function>-<env_partition>.<region>.<env_type>.jet-internal.com
```

Example: `myapp.myteam.pdv-5.eu-west-1.production.jet-internal.com`

### DNS Hosted Zones

Pattern: `<region>.<env_type>.jet-internal.com`

## Namespace Conventions

- Team-based namespaces (one namespace per team per cluster)
- Namespace quotas managed via `cps/projects` repository
- ScaleOps automatically rightsizes resource requests
- To increase quotas, follow the guide in OneEKS Backstage docs

## Secrets Management

### Sonic Runtime: OneSecrets (HashiCorp Vault)

- Primary method for secrets on OneEKS
- EU1 bulkhead has access to legacy Takeaway Vault secrets
- Secrets injected via Vault Agent sidecar or CSI driver

### Sonic Runtime: OneConfig (ConfigMaps + Helmfile)

- For non-sensitive configuration
- Managed via helmfile `state_values/` and `values/` directories

### Legacy: AWS Secrets Manager (deprecated)

```bash
aws secretsmanager get-secret-value --profile <profile> --secret-id <secret-name>
```

## IRSA & Workload Roles

### Sonic Runtime (Self-Service)

Workload roles provisioned via Terraform. Annotate service account in Helm values:

```yaml
serviceAccount:
  annotations:
    eks.amazonaws.com/role-arn: "arn:aws:iam::<account-id>:role/jas/wl/terraform_managed/jas-wl-role-<project>-<app>"
```

### Legacy EKS (Ticket-Based)

IRSA setup requires raising a ticket with the platform team. Role pattern varies by team.

## Deployment Methods

### 1. Helmfile (Golden Path — recommended)

Standard for both legacy and Sonic Runtime. See [Helmfile Golden Path](#helmfile-golden-path) above.

### 2. ArgoCD

Available as an alternative. Onboard via the ArgoCD team onboarding process in Backstage.

### 3. Sonic Pipeline

For eligible services (.NET, Go, Python, Java). Fully managed CI/CD — define a `sonic-spec.yaml` and the pipeline handles build, test, and deploy.

### 4. GitHub Actions

PR deploy workflows available. See OneEKS Backstage docs for GitHub Actions integration.

## Migration Paths

### SRE-EKS → Sonic Runtime

- Start with EU1 bulkhead
- Helmfile structure is similar — update environment names to OneEKS cluster names
- Update AWS profiles from `sre-eks-*` to `euw1-pdv-*`
- DNS-based weighted traffic splitting supported during migration

### CloudOps-EKS → Sonic Runtime

- Similar to SRE-EKS migration
- Update profiles from `eks-cluster-*` / `takeaway-*` to `euw1-pdv-*`

### Skip ECS → Sonic Runtime

- For Java/Quarkus apps on legacy ECS
- Requires containerisation and Helm chart setup
- See Backstage docs: `oneeks/tasks/platform-transition/skip/`

## Troubleshooting

### SSO Token Expired

```bash
# Re-authenticate
aws sso login --profile <profile>

# Then re-run the failing command
```

### Kubectl Unauthorized

```bash
# Refresh kubeconfig
aws eks update-kubeconfig --profile <profile> --name <cluster> --alias <cluster>

# Verify identity
aws sts get-caller-identity --profile <profile>
```

### Wrong Cluster Context

```bash
# List all contexts
kubectx

# Switch to correct context
kubectx <cluster-name>

# Verify
kubectl cluster-info
```

### Helm Release Stuck

```bash
# List releases in namespace
helm list -n <namespace> --kube-context <cluster>

# Check release history
helm history <release-name> -n <namespace> --kube-context <cluster>

# Rollback if needed
helm rollback <release-name> <revision> -n <namespace> --kube-context <cluster>
```
