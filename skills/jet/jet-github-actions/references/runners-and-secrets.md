# Runners & Secrets

## Runner Infrastructure

Runners are deployed as containers on EKS within PLT environments.

- **Hosting**: [eu-west-1-plt-prod-1](https://backstage.eu-west-1.production.jet-internal.com/catalog/default/environment/eu-west-1-plt-prod-1)
- **Base OS**: Ubuntu 22.04
- **Only EKS runners have autoscaling** (via Actions Runner Controller)
- **IP range**: `10.201.160.0/19`

## Runner Groups

Runners are organised into groups with different capabilities:

| Group | Type | Purpose | Access |
|-------|------|---------|--------|
| **CI** | EKS (Linux) | Default build/test runners | All orgs |
| **CI-EC2** | EC2 (Windows) | Windows builds (.NET Framework) | All orgs |
| **CI-Medium** | EKS (Linux) | Medium-sized with more memory/disk | Specific orgs only |
| **CI-Large** | EKS (Linux) | Large runners for Android/Mobile | Mobile/Orderpad teams only |
| **CI-MobileTeams** | Bare Metal (macOS) | iOS builds | Mobile teams only |
| **CD** | EKS (Linux) | Ansible/Terraform deployments | All orgs |

### Using Runners in Workflows

```yaml
jobs:
  build:
    runs-on: [self-hosted, ubuntu-latest]  # CI group (default)

  windows-build:
    runs-on: [self-hosted, windows-latest]  # CI-EC2 group
```

### Requesting Access to Restricted Groups

- **Non-restricted groups** (e.g., CI, CI-EC2): Automatically shared via [github-mgmt automation](https://github.je-labs.com/DevOps/github-mgmt)
- **Restricted groups** (e.g., CI-Large): Requires manual configuration at enterprise and org level

## Runner Images

- Dockerfiles: [github-actions/runner-images](https://github.je-labs.com/github-actions/runner-images)
- Deployment config: [runner-deployments](https://github.je-labs.com/github-actions/runner-deployments/blob/main/vars/eu-west-1-plt-prod-1.yml)
- Pre-baked SDK versions: [toolset.json](https://github.je-labs.com/github-actions/runner-images/blob/main/images/docker-runner/files/toolset.json)
- EC2 AMI update schedule: **1st week of every month**

### Requesting Changes to Runner Images

If a tool is widely useful and measurably speeds up builds, raise a PR to [runner-images](https://github.je-labs.com/github-actions/runner-images). Otherwise, install tools in your workflow steps.

## Deploy Runners

| Runner | Pre-installed Tools |
|--------|-------------------|
| [ansible-runner](https://github.je-labs.com/github-actions/runner-images/blob/main/images/ansible-runner-2.12/Dockerfile) | Ansible, kubectl, Helm |
| [terraform-runner](https://github.je-labs.com/github-actions/runner-images/blob/main/images/terraform-runner/Dockerfile) | Various Terraform versions |

---

## Secrets Management

### Vault (Recommended for Sensitive Data)

Store sensitive data in **Vault**, not GitHub Secrets. Vault offers enhanced protection and reusability.

#### Loading Secrets from Vault

```yaml
- name: Load secrets from vault
  id: secrets
  uses: github-actions/hashicorp-vault-action@v2
  with:
    url: "https://secretsmanagement-eu-west-1-plt-prod-1.eu-west-1.production.jet-internal.com"
    role: pipeline-ci-access
    method: jwt
    path: github-jwt
    exportEnv: false
    secrets: |
      secret/data/eu-west-1-plt-prod-1/githubrunners/all/ci/Secrets ARTIFACTORY_TOKEN
```

Access secrets: `${{ steps.secrets.outputs.ARTIFACTORY_TOKEN }}`

#### Vault Access Setup

- Configuration: [cps/vault](https://github.je-labs.com/cps/vault)
- Request access: Submit a [CDE ticket](https://justeattakeaway.atlassian.net/servicedesk/customer/portal/499)
- Vault role config goes in `vars/apps/k8s-intsvc/github-<your-app-or-org>.yaml`
- Copy the [golden path example](https://github.je-labs.com/cps/vault/blob/b560e263cbb957ed3ffaf68709d50c3a70e8ff69/vars/apps/plt-prod/github-cde-goldenpath.yaml)

### GitHub Secrets (Non-sensitive Data Only)

Use GitHub Secrets for project-specific, non-critical tokens.

```yaml
${{ secrets.FOO }}
```

### Default Organisation Secrets

Available to all organisations:

| Secret | Purpose |
|--------|---------|
| `ARTIFACTORY_NPM_TOKEN` | Publish npm packages (prefix: `npm-ci:xyz`) |
| `ARTIFACTORY_NUGET_TOKEN` | Publish NuGet packages (prefix: `nuget-ci:xyz`) |
| `ARTIFACTORY_PYPI_TOKEN` | Publish Python packages |
| `ARTIFACTORY_TOKEN` | Publish ZIP/Docker to Artifactory (JWT for JFrog CLI) |
| `CORE_GITHUB_TOKEN` | GitHub API token for `pipeline-user` (e.g., tagging) |
| `GH_DOTCOM_READ_TOKEN` | Read-only token for github.com (avoids API rate limits) |
| `GITHUB_TOKEN` | Default GitHub Actions token ([docs](https://docs.github.com/actions/security-guides/automatic-token-authentication)) |

### GitHub Variables (Non-sensitive Config)

```yaml
${{ vars.<variable-name> }}
```

Use for environment names, configuration values, and other non-secret data.

## Kubernetes Permissions

Managed via the [namespaces-xsre repository](https://github.je-labs.com/cps/namespaces-xsre).

Grant repository access:
```yaml
git_project_paths:
  - <org-name>/<repository-name>
```

Grant organisation access:
```yaml
git_namespaces:
  - <org-name>
```

## AWS Access

Use the [configure-aws-creds action](https://github.je-labs.com/github-actions/configure-aws-creds):

```yaml
- name: Set up AWS variables
  uses: github-actions/pipelines/actions/setup-ci@v1
  with:
    app: my-app-name
    aws-env: my-aws-environment-name

- name: Configure AWS IAM credentials
  uses: github-actions/configure-aws-creds@v1
  with:
    role-to-assume: arn:aws:iam::${{ env.AWS_ACCOUNT_ID }}:role/pipeline-ci
    role-session-name: github-session
```

### IAM Roles for Runners

- Source roles: Defined in [runner-deployments config](https://github.je-labs.com/github-actions/runner-deployments/blob/ee356a4ef29a1fd1d7ebc1c4d82294ac6eb990e7/vars/eu-west-1-plt-prod-1.yml#L32-L33)
- Target roles: Provisioned via [pipelineiams Ansible role](https://github.je-labs.com/ansible-roles/pipelineiams)

## Secrets Setup Workflow (L-JE)

Provisions Vault secret paths for applications:

```yaml
name: secrets
on:
  push:
    branches: [main]
    paths-ignore:
      - "**/*.gitattributes"
      - "**/*.gitignore"
      - "**/*.md"
  workflow_dispatch:

jobs:
  secrets:
    uses: github-actions/pipelines/.github/workflows/setup-secrets.yml@v1
    secrets: inherit
    with:
      app: myapplication
```
