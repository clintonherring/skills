# Platform Overview & Detection

## Table of Contents

- [Migration Overview](#migration-overview)
- [RefArch EKS](#refarch-eks)
- [L-JE EC2](#l-je-ec2)
- [Marathon](#marathon)
- [CloudOps EKS](#cloudops-eks)
- [SRE EKS](#sre-eks)
- [Kafka at JET](#kafka-at-jet)

## Migration Overview

| Platform     | Priority | Timeline | AWS Account                   |
| ------------ | -------- | -------- | ----------------------------- |
| RefArch EKS  | High     | 2025     | Legacy RefArch                |
| Marathon     | High     | 2025     | Legacy Marathon               |
| L-JE EC2     | High     | 2025     | Legacy L-JE                   |
| SRE EKS      | Medium   | 2026     | Legacy SRE                    |
| CloudOps EKS | Medium   | 2026     | **SAME as Sonic Runtime EU1** |

## RefArch EKS

### Detection Indicators
- `.deploy/` directory with Helm charts
- `helmrelease-*.yaml` files
- Environment naming: `{region}-{function}-{env-type}-{number}` (e.g., `eu-west-1-pdv-qa-1`)
- IAM roles via Ansible (iam role)
- Service accounts with `eks.amazonaws.com/role-arn` annotations

### Platform Characteristics
**Environment Types**: sandbox, qa, staging, prod, dr
**Functions**: pdv (product dev), plt (platform), ing (ingress), tgw (transit gateway), dns, idm (identity), inf (infosec), sec, ver
**App-Groups**: Logical boundaries with dedicated subnets and network ACLs
**Compute**: EKS

### Key Components
- **JE Vault** → OneSecrets
- **Consul** → OneConfig (ConfigMaps)
- **Prometheus/Grafana** → Datadog
- **IRSA**: Ansible role → cps/projects Terraform
- **Cross-Account Access**: Required (different AWS account from Sonic Runtime)

### Environment Mapping
| RefArch                      | Sonic Runtime    |
| ---------------------------- | ---------------- |
| `eu-west-1-pdv-qa-1`         | `euw1-pdv-qa-3`  |
| `eu-west-1-pdv-staging-1`    | `euw1-pdv-stg-5` |
| `eu-west-1-pdv-prod-1`       | `euw1-pdv-prd-6` |
| `eu-central-1-pdv-qa-1`      | `euw1-pdv-qa-2`  |
| `eu-central-1-pdv-staging-2` | `euw1-pdv-stg-5` |
| `eu-central-1-pdv-prod-2`    | `euw1-pdv-prd-5` |

## L-JE EC2

### Detection Indicators
- Ansible playbooks (`.yml`, `.yaml` files in root or ansible/)
- VM-based deployments
- EC2 instance configurations
- Legacy L-JE account resources
- JustSaying/SNS/SQS usage common

### Platform Characteristics
**Compute**: EC2 instances (VMs)
**Configuration**: Consul
**Secrets**: JE Vault
**Deployment**: Ansible-based
**Messaging**: Often uses JustSaying (SNS/SQS)

### Key Components
- **Consul** → OneConfig
- **JE Vault** → OneSecrets
- **Containerization**: Required (create Dockerfile)
- **Traffic Split**: Mandatory gradual cutover
- **Cross-Account Access**: Required
- **MeX Migration**: Often required (if JustSaying used)

## Marathon

### Detection Indicators
- `marathon.json` deployment files
- `.service` DNS resolution (Consul-based)
- Marathon-specific base Docker images
- Mesos/Marathon orchestration

### Platform Characteristics
**Compute**: Docker containers on Mesos
**Service Discovery**: Consul (`.service` DNS)
**Configuration**: Consul
**Base Images**: Marathon-specific

### Key Components
- **Marathon base images** → Verified Publisher/Official Docker images
- **`.service` DNS** → Global DNS (via `igw-marathon` initially)
- **Consul service discovery** → Kubernetes DNS
- **Health checks** → K8s liveness/readiness probes
- **Dependencies**: Update to use `tk-<service>` prefix for DB/RabbitMQ

## CloudOps EKS

### Detection Indicators
- Free-form Kubernetes manifests
- CloudOps EU1 deployments
- DNS patterns:
  - Dev: `{service}.{namespace}.d.eks.tkwy-infra.io`
  - Staging: `{service}.{namespace}.x.eks.tkwy-staging.io`
  - Prod: `{service}.{namespace}.p.eks.tkwy-prod.io`
- IRSA role pattern: `irsa_{namespace}_{app}`
- Namespace-per-team model
- Service Account constraint: namespace + SA name ≤ 58 characters

### Platform Characteristics
**Clusters**: `eks-cluster-dev`, `eks-cluster-staging-2`, `eks-cluster-prod`, `eks-cluster-prod-ap`
**Monitoring**: Grafana, Prometheus, Alertmanager per cluster
**Secrets**: AWS Secrets Manager
**IRSA**: Via ticket (manual process)
**Kafka**: TKWY Kafka (accessible from Sonic Runtime)
**AWS Account**: **SAME as Sonic Runtime EU1** ✅

### Key Components
- **AWS Secrets Manager** → OneSecrets (Vault)
- **IRSA ticket-based** → Self-service cps/projects
- **Namespace-per-team** → Project-per-team (one project all envs)
- **Free-form K8s** → basic-application chart
- **Cross-Account Access**: NOT needed (same AWS account) ✅
- **Kafka**: Continue using TKWY Kafka

## SRE EKS

### Detection Indicators
- Cluster naming: `sre-eks-{env}-{number}` (e.g., `sre-eks-production-1`)
- DNS pattern: `{service}.{namespace}.svc.cluster.local` or via VirtualService
- Repository structure: `cps/helm-core-xsre`, `cps/namespaces-xsre`, `cps/helm-services-xsre`
- Namespace-based isolation
- Helm v3 + helmfile deployment

### Platform Characteristics
**Clusters**: sre-eks-dev-1, sre-eks-staging-1, sre-eks-production-1, sre-eks-migration-1, sre-eks-intsvc-1, sre-eks-gitlab-1
**Monitoring**: Prometheus, Grafana, Alertmanager
**Secrets**: Vault
**Tooling**: helm, helmfile, kubens, kubectx, stern, lens
**Architecture**: Single bulkhead (vs Sonic Runtime's multi-bulkhead)

### Key Components
- **Single bulkhead** → Multi-bulkhead (EU1, EU2, OC1, NA1)
- **Vault** → OneSecrets
- **Prometheus/Grafana** → Datadog
- **SRE helm charts** → basic-application chart
- **`.tkwy.cloud` DNS** → `.jet-internal.com`
- **Namespace-per-team** → Project-per-team
- **Recommendation**: Migrate to EU1 first (functional equivalent of SRE-EKS)

## Kafka at JET

### Two Kafka Services

**JET (RefArch) Kafka**:
- Used by: RefArch applications
- Accessible from: Sonic Runtime ✅
- Migration: Not needed (continue using)

**TKWY (TA SRE) Kafka**:
- Used by: CloudOps, SRE-EKS applications
- Accessible from: Sonic Runtime ✅
- Migration: Not needed (continue using)

### Key Features
- **Cluster Linking**: Available for topic mirroring between clusters
- **Access**: No special migration needed
- **Support**: #help-messaging-integrations

### Migration Note
If already using JET or TKWY Kafka, continue using the same cluster from Sonic Runtime. No migration required.
