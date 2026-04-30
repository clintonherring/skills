# CI/CD: Sonic Pipeline vs GitHub Actions

## Table of Contents

- [Decision Framework](#decision-framework)
- [Sonic Pipeline](#sonic-pipeline)
- [GitHub Actions](#github-actions)
- [Comparison Matrix](#comparison-matrix)
- [Migration Scenarios](#migration-scenarios)
- [Decision Tree](#decision-tree)
- [Getting Started](#getting-started)
- [Common Patterns](#common-patterns)
- [Key Concepts](#key-concepts)

## Decision Framework

Choose CI/CD approach based on repository structure and technology stack.

## Sonic Pipeline

**Use When:**
- Single application per repository
- Supported language: .NET, Go, Python, or Java
- Standard CI/CD needs (build, test, deploy)
- Team prefers managed solution

**Characteristics:**
- **Managed** - Platform team maintains pipeline
- **Standardized** - Consistent patterns across teams
- **Limited Customization** - Configuration via `.sonic/sonic.yml`
- **Replaces GitHub Actions** - No coexistence, fully replaces workflows
- **GitOps-based** - Helmfile sync via Flux

### Configuration

**File:** `.sonic/sonic.yml`

**Example:**
```yaml
version: 1.0
language: go
build:
  dockerfile: Dockerfile
test:
  enabled: true
  command: go test ./...
deploy:
  environments:
    - euw1-pdv-qa-3
    - euw1-pdv-stg-5
    - euw1-pdv-prd-5
```

**Key Features:**
- Automatic Docker image builds
- Integrated security scanning (Wiz)
- Helmfile deployment automation
- Built-in PR environment deployments

### Limitations

**Repository Structure:**
- ❌ Monorepos (multiple applications)
- ❌ Multi-service repositories
- ✅ Single application only

**Language Support:**
- ✅ .NET (all versions)
- ✅ Go
- ✅ Python
- ✅ Java
- ❌ Node.js (use GitHub Actions)
- ❌ Ruby (use GitHub Actions)
- ❌ Other languages (use GitHub Actions)

**Customization:**
- Limited to `.sonic/sonic.yml` options
- Cannot add custom workflow steps
- Cannot integrate third-party tools not in pipeline

## GitHub Actions

**Use When:**
- Multiple applications per repository (monorepo)
- Unsupported language (Node.js, Ruby, etc.)
- Complex CI/CD requirements
- Need custom workflow steps
- Integration with third-party tools

**Characteristics:**
- **User-Controlled** - Full flexibility in workflows
- **Customizable** - Define any workflow steps
- **Self-Managed** - Team maintains workflows
- **Integration-Friendly** - Any GitHub Actions marketplace tool

### goldenpath Workflows

**Standard workflows** from [goldenpath](https://github.je-labs.com/justeattakeaway-com/goldenpath):

```
.github/workflows/
├── build-deploy-main.yml   # Main branch: build + deploy all envs
├── build-pr.yml            # PR: lint, test, build image
├── deploy-adhoc.yml        # On-demand: /sync <ENV_NAME>
├── diff-production.yml     # PR: show helmfile diff
└── rollback.yml            # Manual: rollback to version
```

### Workflow Customization

**Flexibility:**
- Add linting, test coverage, static analysis
- Integrate Wiz image scanner
- Add manual approval gates (GitHub environments)
- Run tests at any stage (pre-build, post-build, post-deploy)
- Custom notification logic

**Example Customization:**
```yaml
# .github/workflows/build-pr.yml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run linter
        run: npm run lint
  
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Wiz scan
        uses: wiz/actions/scan@v1
  
  build:
    needs: [lint, security-scan]
    # ... existing build steps
```

### Ad-Hoc Deployments

**PR Comment Trigger:**
```
/sync euw1-pdv-qa-2
```

Deploys PR branch to specified environment.

### Production Approvals

**GitHub Environments:**
```yaml
# .github/workflows/build-deploy-main.yml
jobs:
  deploy-production:
    environment: production  # Requires approval
    steps:
      - name: Deploy to production
        # ... deployment steps
```

Configure approvals in repository settings → Environments.

## Comparison Matrix

| Feature | Sonic Pipeline | GitHub Actions |
|---------|---------------|----------------|
| **Repository Structure** | Single app only | Monorepo supported |
| **Language Support** | .NET, Go, Python, Java | Any language |
| **Customization** | Limited (sonic.yml) | Full (YAML workflows) |
| **Maintenance** | Platform team | Application team |
| **Learning Curve** | Low | Medium |
| **Flexibility** | Low | High |
| **Integration** | Built-in tools only | Any GitHub Action |
| **Deployment** | GitOps (Flux) | Direct (helm/helmfile) |
| **Security Scanning** | Built-in (Wiz) | Manual integration |
| **Rollback** | Manual | Workflow-based |

## Migration Scenarios

### RefArch → Sonic Runtime

**Recommended:** GitHub Actions

**Rationale:**
- RefArch uses `.deploy/` with custom Helm charts
- Likely complex CI/CD requirements
- Helmfile adoption requires flexibility

### L-JE EC2 → Sonic Runtime

**Recommended:** Start with GitHub Actions, evaluate Sonic Pipeline

**Rationale:**
- Containerization is new (no existing Docker workflows)
- May need iterative CI/CD adjustments
- GitHub Actions provides flexibility during migration

**Future:** Consider Sonic Pipeline after stabilization (if single app + supported language).

### Marathon → Sonic Runtime

**Recommended:** Evaluate based on language and repo structure

**Rationale:**
- Check language support (Sonic Pipeline vs GitHub Actions)
- Assess repository structure (single app vs multiple)
- Consider existing Marathon CI/CD complexity

### CloudOps EKS → Sonic Runtime

**Recommended:** Maintain GitHub Actions (if already using)

**Rationale:**
- CloudOps likely uses GitHub Actions already
- Switching to Sonic Pipeline adds migration complexity
- Stick with known CI/CD approach

### SRE EKS → Sonic Runtime

**Recommended:** Evaluate based on current CI/CD

**Rationale:**
- SRE teams likely have custom CI/CD
- GitHub Actions provides compatibility with existing patterns

## Decision Tree

```
Is repository a monorepo (multiple apps)?
├─ YES → GitHub Actions (required)
└─ NO → Continue

Is language supported by Sonic Pipeline?
(.NET, Go, Python, Java)
├─ NO → GitHub Actions (required)
└─ YES → Continue

Does team need custom CI/CD steps?
(third-party integrations, complex testing)
├─ YES → GitHub Actions (recommended)
└─ NO → Continue

Does team prefer managed solution?
├─ YES → Sonic Pipeline (recommended)
└─ NO → GitHub Actions (recommended)
```

## Hybrid Approach (NOT Supported)

**❌ Cannot Coexist:** Sonic Pipeline and GitHub Actions cannot run in the same repository for deployment.

**Reason:** Sonic Pipeline replaces all GitHub Actions workflows for build/deploy.

**Alternative:** Use GitHub Actions exclusively if any hybrid need exists.

## Getting Started

### Sonic Pipeline

1. Add `.sonic/sonic.yml` to repository
2. Remove existing GitHub Actions workflows
3. Configure environments and build settings
4. Platform team reviews and enables pipeline

**Documentation:** [Sonic Pipeline Guide](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/sonic-pipeline/)

### GitHub Actions

1. Copy workflows from [goldenpath](https://github.je-labs.com/justeattakeaway-com/goldenpath)
2. Customize workflows per requirements
3. Test in non-production environment
4. Add approvals for production deployments

**Documentation:** [Deploy with Helmfile](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/oneeks/tutorials/deploy-with-helmfile/)

## Common Patterns

### Helmfile Deployment (GitHub Actions)

**Standard Pattern:**
```yaml
- name: Deploy with Helmfile
  run: |
    helmfile -e ${{ env.ENVIRONMENT }} sync
  env:
    ENVIRONMENT: euw1-pdv-qa-3
```

### Environment-Specific Secrets (GitHub Actions)

**GitHub Secrets:**
```yaml
- name: Deploy to production
  env:
    WORKLOAD_ROLE_ARN: ${{ secrets.PROD_WORKLOAD_ROLE_ARN }}
  run: |
    helmfile -e euw1-pdv-prd-5 sync
```

### PR Environment Cleanup (GitHub Actions)

**Automatic Cleanup:**
```yaml
on:
  pull_request:
    types: [closed]

jobs:
  cleanup:
    runs-on: ubuntu-latest
    steps:
      - name: Destroy PR environment
        run: |
          helmfile -e euw1-pdv-qa-2 destroy
```

## Key Concepts

**Projects**: Core organizational unit in Sonic Runtime. One project = one Kubernetes namespace used across ALL environments (QA, Staging, Production in different bulkheads). Project ID format: `{process-group-prefix}-{suffix}` (e.g., `cu-order-reviews`). The same project/namespace is used whether deploying to QA or Production - environments are differentiated by bulkhead, not project name. **NEVER** create separate projects per environment (no `-qa`, `-stg`, `-prd` suffixes).

**Bulkheads**: Cluster groupings - Critical/Tier 1, Standard/Tier 2-3, Non-Production

**Workload Roles**: IAM roles for K8s workloads via IRSA. Configure with `serviceAccount.annotations.eks.amazonaws.com/role-arn`

**Cross-Account Access (Critical Two-Sided Setup)**:
- **Side 1**: Create Workload Role in cps/projects (Terraform) with IAM policies for needed actions
- **Side 2**: Update resource-based policies in legacy account (DynamoDB tables, S3 buckets, SQS queues) to trust the Workload Role ARN
- **Common mistake**: Teams configure only one side and access fails
- **Example**: DynamoDB access requires both the Workload Role with dynamodb:GetItem permission AND the DynamoDB table resource policy allowing that role ARN

**OneSecrets**: Vault deployed in OneEKS for secrets. Replaces JE Vault and AWS Secrets Manager. Each environment has separate Vault instance.

**OneConfig**: ConfigMaps for configuration. Replaces Consul, AWS App Config, and AWS Secrets Manager. Injected as environment variables or mounted files. For shared configs or non-EKS, use Parameter Store.

**Sonic Runtime Onboarding Process**:
- **Step 1**: Onboard a Team (follow Getting Started documentation)
- **Step 2**: Onboard a Project - ONE project for all environments (QA, Staging, Production)
  - Project ID format: `{process-group-prefix}-{suffix}` based on PeopleProcessTech (PPT) Process Group
  - Example: `cu-order-reviews` (prefix from "Customer Order Selection" process group + "reviews" suffix)
  - Same project/namespace used across all bulkheads (QA, Staging, Production)
  - Kubernetes namespace = project ID (e.g., `cu-order-reviews` namespace in both QA and Prod bulkheads)
- **Step 3**: Request tool access (monitoring, support tools)
- **Step 4**: Setup local tooling (kubectl, helmfile, etc.)
- **Result**: Team Okta Group, SSO roles per environment, single project/namespace, Artifactory repos
- **Documentation**: See Getting Started guide in Sonic Runtime documentation

**Goldenpath**: Standard repo structure with helmfile.d/, state_values/, values/, cosign.pub

**basic-application chart**: Standard Helm chart providing Deployment, Service, HPA, VirtualService. **REQUIRES v1.1.2+ for Sonic Runtime deployment**.

**Datadog**: Primary monitoring (APM, logs, dashboards, monitors). Replaces Prometheus, CloudWatch, Kibana, Logz.io, Tempo, Alertmanager. Grafana/Prometheus/Sentry available as backup only.

## Documentation References

- [Sonic Pipeline Documentation](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/sonic-pipeline/)
- [goldenpath Repository](https://github.je-labs.com/justeattakeaway-com/goldenpath)
- [Deploy with Helmfile Tutorial](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/oneeks/tutorials/deploy-with-helmfile/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
