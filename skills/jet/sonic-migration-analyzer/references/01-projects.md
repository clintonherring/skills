# Projects in Sonic Runtime

## Critical Concepts for Migration Analysis

### ONE Project for ALL Environments
- **Key Rule**: A single project serves QA, Staging, and Production
- **Project ID Format**: `{process-group-prefix}-{suffix}` (e.g., `cu-order-reviews`)
- **Namespace**: Project ID becomes the Kubernetes namespace name
- **Same namespace across all bulkheads**: `cu-order-reviews` namespace exists in both QA and Production bulkheads

### **NEVER** Create Separate Projects Per Environment
- ❌ WRONG: `myapp-qa`, `myapp-stg`, `myapp-prd` (three projects)
- ✅ CORRECT: `myapp` (one project deployed to different bulkheads)

### Project ID Structure

**Process Group**:
- Selected from PeopleProcessTech (PPT)
- Examples: `Operate Order Selection`, `Manage Delivery`, `Customer Experience`
- Determines prefix (e.g., `cu-order` for Customer Order Selection)

**Suffix**:
- User-defined component
- Guidelines:
  - Reflect broad purpose (not service-specific)
  - 3-7 characters recommended
  - Lowercase only
  - Alphanumeric only (a-z, 0-9)
  - Examples: `reviews`, `search`, `delivery`, `payroll`

**Example**:
- Process Group: "Operate Order Selection"
- Suffix: "reviews"
- Project ID: `cu-order-reviews`

### Key Features

**Resource Grouping**: All resources (pods, services, configmaps, secrets) within a project can interact seamlessly

**Isolation**: Projects are isolated from each other by default. Cross-project access requires Integration Services.

**Dedicated Namespace**: Project ID = Kubernetes namespace name

**Per-Project Components**: Each project gets dedicated:
- Ingress Gateway (IGW)
- Resource quotas
- Cost allocation

### Implications for Migration

1. **Environment Mapping**: Map legacy environments (QA, Staging, Production) to single project across bulkheads
2. **Namespace Naming**: Don't append environment suffixes to project names
3. **Bulkhead Selection**: Environments differentiated by bulkhead (euw1-pdv-qa-3 vs euw1-pdv-prd-5), not project name

## Onboarding Process

### Before Onboarding
1. Onboard a Team
2. Onboard a Project (ONE project for all environments)
3. Request tool access
4. Setup local tooling

### After Onboarding - Received Resources
- Team Okta Group: `AWS (JET) - <team-name>`
- SSO Roles per environment:
  - `jas-q-<team-short-name>` - QA
  - `jas-s-<team-short-name>` - Staging
  - `jas-p-<team-short-name>` - Production
- Project Details:
  - Project Name: `<project-name>` (same for all environments)
  - Namespace Name: `<project-name>` (same as project)
- Artifactory Repositories:
  - `<team-name>-docker-dev-local`
  - `<team-name>-docker-prod-local`
- Vault-Associated Parameters:
  - vault-role: `github-<team-name>`
  - secret-path: `secret/data/gitlab-ci/artifactory/gitlab_ci_<team-name>`

## Documentation URL
https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/oneeks/getting-started/
