# Available Actions Catalog

## First-Party Actions (GitHub Built-in)

Available at: `https://github.je-labs.com/actions`

These are GitHub's own actions, baked into the GHES instance. Check tags at each repo for available versions.

**Common first-party actions** (versions queried from GHES March 2026):

| Action | Latest on GHES | Recommended | Notes |
|--------|---------------|-------------|-------|
| `actions/checkout` | v4.2.2 | `@v4` | |
| `actions/setup-node` | v4.2.0 | `@v4` | Add `token` param for non-docker-runner |
| `actions/setup-go` | v5.3.0 | `@v5` | Add `token` param for non-docker-runner |
| `actions/setup-python` | v5.4.0 | `@v5` | Add `token` param for non-docker-runner |
| `actions/setup-dotnet` | v4.3.1 | `@v4` | |
| `actions/setup-java` | v4.7.0 | `@v4` | |
| `actions/upload-artifact` | v4.6.1 | **`@v3`** | **v4 tags exist but v4 is NOT supported on GHES** |
| `actions/download-artifact` | v4.1.9 | **`@v3`** | **v4 tags exist but v4 is NOT supported on GHES** |
| `actions/cache` | v4.2.2 | `@v4` | |

### Pre-baked SDKs

The `docker-runner` (a.k.a. `ubuntu-latest`) has pre-baked SDKs to speed up `setup-*` actions. Installed versions are defined in [toolset.json](https://github.je-labs.com/github-actions/runner-images/blob/main/images/docker-runner/files/toolset.json).

## Imported Third-Party Actions

Available at: `https://github.je-labs.com/github-actions/` (with topics `github-action` + `public-mirror`)

Search: `https://github.je-labs.com/search?q=topic%3Agithub-action&topic%3Apublic-mirror&type=Repositories`

> **NOTE**: Some imported actions may fail with `@v1` style refs if the original used a branch (not a tag) for versioning. If you hit a version resolution error, try an explicit tag like `@v1.0.0`. See [ghes-constraints.md](./ghes-constraints.md) for details.

To request a new action import or update: [github-actions/manage-public-actions](https://github.je-labs.com/github-actions/manage-public-actions/issues/new/choose)

## In-House Custom Actions

Developed internally and stored in the `github-actions` organisation.

| Action | Purpose |
|--------|---------|
| [artifactory-upload](https://github.je-labs.com/github-actions/artifactory-upload) | Upload build artifacts to Artifactory |
| [generate-version](https://github.je-labs.com/github-actions/generate-version) | Determine next version number from repository tags |
| [run-sonarqube-scan](https://github.je-labs.com/github-actions/run-sonarqube-scan) | Run SonarQube scans (.NET & Node.js only) |
| [slack-github-action](https://github.je-labs.com/github-actions/slackapi-slack-github-action) | Send notifications to Slack |
| [npm-package-publish](https://github.je-labs.com/github-actions/npm-package-publish) | Test and publish NPM packages to Artifactory |
| [configure-aws-creds](https://github.je-labs.com/github-actions/configure-aws-creds) | Assume IAM roles in AWS accounts |
| [hashicorp-vault-action](https://github.je-labs.com/github-actions/hashicorp-vault-action) | Load secrets from HashiCorp Vault |
| [publish-nuget-packages](https://github.je-labs.com/github-actions/publish-nuget-packages) | Publish NuGet packages to Artifactory |

## Reusable Workflows

Stored in the [pipelines repository](https://github.je-labs.com/github-actions/pipelines).

### Build Workflows

| Workflow | Purpose |
|----------|---------|
| `github-actions/pipelines/.github/workflows/publish-docker.yml@v1` | Build and push Docker image to Artifactory |
| `github-actions/pipelines/.github/workflows/publish-docker-with-kaniko.yml@v1` | Build and push Docker using Kaniko (faster) |
| `github-actions/pipelines/.github/workflows/publish-helm.yml@v1` | Publish Helm chart to Artifactory |
| `github-actions/pipelines/.github/workflows/publish-version.yml@v1` | Tag a new Git release on a repository |
| `github-actions/pipelines/.github/workflows/build-ami.yml@v1` | Build AMI with Packer |
| `github-actions/pipelines/.github/workflows/publish-ami.yml@v1` | Copy and share AMI across AWS regions |

### Deploy Workflows

| Workflow | Purpose |
|----------|---------|
| `github-actions/pipelines/.github/workflows/run-helmfile.yml` | Run Helmfile commands (diff/sync/destroy) |
| `github-actions/pipelines/.github/workflows/setup-secrets.yml@v1` | Provision Vault secret paths |

### Newer Pipeline Workflows (under development)

More flexible and user-friendly alternatives:

- [pipelines-generic](https://github.je-labs.com/github-actions/pipelines-generic)
- [pipelines-docker](https://github.je-labs.com/github-actions/pipelines-docker)
- [pipelines-k8s](https://github.je-labs.com/github-actions/pipelines-k8s)

## Example Build Workflows by Language

### .NET
- [EKS Docker build](https://github.je-labs.com/github-actions/test-dotnet-ec2-app/blob/main/.github/workflows/build.yml)
- [NuGet package (LambdaWorker)](https://github.je-labs.com/dotnet-shared/LambdaWorker/blob/main/.github/workflows/build.yml)
- [Serverless Lambda](https://github.je-labs.com/codeflow/codeflowbot/blob/main/.github/workflows/build.yml)
- [.NET Framework on Windows](https://github.je-labs.com/ContinuousDeliveryEngineering/JE.Worker.Example/blob/1.0.0.169/.github/workflows/build.yml)
- [Workflow templates](https://github.je-labs.com/dotnet-shared/.github/tree/main/workflow-templates)

### Node.js
- [npm package build](https://github.je-labs.com/dotnet-shared/generator-dotnet-app/blob/main/.github/workflows/build.yml)
- [Serverless Lambda](https://github.je-labs.com/PlatformEngineering/awslogslambdas/blob/master/.github/workflows/build.yml)

### Python
- [Serverless Lambda](https://github.je-labs.com/ContinuousDeliveryEngineering/onboarderbot/blob/master/.github/workflows/build-deploy.yml)
- [Poetry build and publish](https://github.je-labs.com/backstage/backstage-python-client/blob/master/.github/workflows/build-publish.yml)

### Java/Maven
- [Maven build](https://github.je-labs.com/Restaurant-Demolition/order-transmission-result-analyzer/blob/main/.github/workflows/run-on-push-pr.yml)

### Android
- [Gradle build](https://github.je-labs.com/experimentation-platform/jetfm/blob/main/.github/workflows/android.yml)
