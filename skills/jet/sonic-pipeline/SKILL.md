---
name: sonic-pipeline
description: "Use this skill when asked to configure or modify Sonic Pipeline for an application — defining workloads, artifacts, deployments, and sonic.yml. Covers dotnet, Go, Java (Maven/Gradle), Python and Redpanda Connect runtimes. Does not cover platform migrations from SRE-EKS, Marathon, EC2, or other source platforms — use the dedicated migrator skills for those. Not needed separately during platform migrations — migrator skills load this skill as a dependency for schema reference."
metadata:
  owner: continuous-delivery-engineering
---

# Sonic Pipeline

Sonic Pipeline is a CI/CD pipeline that is used to build, test and deploy applications to Sonic Runtime.

## Prerequisites

- Have `jq` installed locally, you can check this by running `jq --version`.
- Have `gh` installed locally and authenticated with access to `github.je-labs.com`, you can check this by running `gh auth status --hostname github.je-labs.com`.
- Have `base64` installed locally, you can check this by running `base64 --version`.

## The `sonic.yml` file

Sonic Pipeline requires a `.sonic/sonic.yml` file at the root of the application repository. The `.sonic/sonic.yml` file should look like this:

``` yaml
apiVersion: justeattakeaway.com/sonic-spec/0.0.2

# Defines general metadata for the component and how it
# should be used.
metadata:
  metadataId: "component name"
  project: "project name"
  team: "owning team name"
  vaultRole: "vault secret role"
  vaultSecretPath: secret/data/gitlab-ci/artifactory/gitlab_ci_{team_name}
  deployNotifications:
    default: "C01ABCDEF" # if the Slack Channel ID is used for all environment types, this is all that is needed.
    qa: "Q01ABCDEF" # This is optional.
    stg: "S01ABCDEF" # This is optional.
    prd: "P01ABCDEF" # This is optional.

# The environments, broken down by environment type, that
# will be deployed.
environments:
  qa: # QA.
    - "environment_for_qa"
    - "another_environment_for_qa"
  stg: # Staging.
    - "environment_for_staging"
    - "another_environment_for_staging"
  prd: # Production.
    - "environment_for_production"
    - "another_environment_for_production"
```

### Component Metadata

You may need access to a components platform metadata (a.k.a. PMD), this can be retrieved by running this command:

``` sh
gh api --hostname github.je-labs.com /repos/metadata/PlatformMetadata/contents/Data/global_features/COMPONENT_NAME.json | jq -r '.content' | base64 -d
```

### Team Metadata

You may need access to team's platform metadata:

``` sh
gh api --hostname github.je-labs.com /repos/metadata/PlatformMetadata/contents/Data/teams/TEAM_NAME.json | jq -r '.content' | base64 -d
```

### Project Metadata

The project that the application belongs is the same as the namespace it is being deployed to, therefore, if not provided then you can discover this by looking at the existing deployments defined in the Helm configuration.

### Vault Metadata

Sonic Pipeline requires a vault role and a secret path for the application. You should be able to find this in the GitHub Workflows, specifically when building and publishing a Docker image using the `github-actions/pipelines-docker/.github/workflows/publish-docker-artifactory.yml` action:

``` yaml
build-image:
  uses: github-actions/pipelines-docker/.github/workflows/publish-docker-artifactory.yml@v1
  with:
    vault-role: github-partner-acquisition # This is the vault role.
    secret-path: secret/data/github-actions/artifactory/github_actions_team-name # This is the vault secret path.
  secrets: inherit
```

### Pipeline Environments

Sonic Pipeline needs to know the environments defined, broken down by environment type. You should be able to find this in the GitHub Workflows, specifically when building and publishing a Docker image using the `github-actions/pipelines/.github/workflows/deploy-helmfile.yml` action:

``` yaml
deploy-qa:
  uses: github-actions/pipelines/.github/workflows/deploy-helmfile.yml@v1
  strategy:
    matrix:
      env_name:
        - euw1-pdv-qa-2
        - euw1-pdv-qa-3
        - apse2-pdv-qa-2
    with:
      environment: ${{ matrix.env_name }}
      slack-channel-id-for-stage: slack-channel-for-qa
    secrets: inherit
```

If you find a list of slack channels for an environment (a comma seperated list), then only take note of the first one.

## The `workloads` Sonic Module

There is an additional section of the `.sonic/sonic.yml` file that defines the runtime workloads that need to be built and deployed. This section will look something like this:

``` yaml
workloads:
  apiVersion: justeattakeaway.com/workloads/0.0.2
  resources:
    name_of_workload: # For monorepos, the workload name disambiguates Docker image names.
      type: service
      # This is the path for the workload source code, this is optional and is only needed for monorepos, if this is not
      # provided then the workload source directory is the root of the repository.
      source_directory: ./path/to/workload/source

  # There will be an artifact for each workload
  # resource.
  artifacts:
    name_of_workload:
      appType: api # `api` or `worker`
      runtime: dotnet # can be `java-gradle`, `java-maven`, `dotnet`, `go`, `python` or `redpandaconnector`
      runtimeVersion: 9.0
      tests:
        - type: unit # can be `unit` and `integration`
          flags:
            - "-example-flag"
        - type: integration
          flags:
            - "-example-flag"
            - "-another-flexible-flag"
          env:
            - name: ExampleEnvironmentVariable
              value: value

  # This an optional section, you only need this if
  # we have Acceptance or E2E tests.
  #
  # There will be a deployment for each workload.
  deployment:
    name_of_workload:
      tests:
        - type: e2e # can only be `e2e` and `acceptance`
          env:
            - name: ExampleEnvironmentVariable
              value: value
          flags:
            - "-example-flag"
        - type: acceptance
          env:
            - name: ExampleEnvironmentVariable
              value: value
          flags:
            - "-example-flag"
```

### Docker And Helm

It is expected that a `Dockerfile` file and `helmfile.d` directory is available in each workload source directory.

### Shared Logic

If there is a workload in your application that you still want to test, but is not deployed to Sonic Runtime (e.g. a shared library), then you can define the workload that is configured to skip deployment like this:

``` yaml
my_shared_library:
  type: service
  source_directory: ./src/domain
  skip_deploy: true # <-- This flag is used to skip deployment for this workload.
```

In addition, the artifact for such workloads should also be configured to skip building:

``` yaml
my_shared_library:
  runtime: dotnet
  skip_build: true # <-- This flag is used to skip building for this workload.
  tests:
    - type: unit
```

### Test Types

- **Unit Tests**\
  These are tests that run at build time, therefore they are only applicable to workload artifacts.
- **Integration Tests**\
  These are tests that run at build time, therefore they are only applicable to workload artifacts.
- **E2E Tests**\
  These are tests that run at deployment time, therefore they are only applicable to workload deployments.\
  Supported runtimes: `dotnet`, `go`, `python`.
- **Acceptance Tests**\
  These are tests that run at deployment time, therefore they are only applicable to workload deployments.\
  Supported runtimes: `dotnet`, `go`.

### Deployment Test Pipeline Flow

Deployment tests (E2E and acceptance) are gated between environment tiers. The pipeline follows this promotion flow:

1. **Deploy to QA** environments
2. Run E2E and/or acceptance tests against QA
3. **Deploy to Staging** environments (only if QA tests pass or are skipped)
4. Run E2E and/or acceptance tests against Staging
5. **Deploy to Production** environments (only if Staging tests pass or are skipped)

Both E2E and acceptance tests must pass (or be skipped) before promotion to the next environment tier.

### Custom E2E Workflows

Instead of using the built-in runtime-specific E2E test runners, you can dispatch to a custom workflow file. This is configured in the deployment test entry:

``` yaml
deployment:
  name_of_workload:
    tests:
      - type: e2e
        e2e_custom_workflow_org: "YourOrg"
        e2e_custom_workflow_repo: "your-repo"
        e2e_custom_workflow_file: "custom-e2e.yml"
```

When a custom workflow is configured, the pipeline will dispatch to the specified workflow file instead of the default runtime-specific E2E workflow.

### Language Runtimes / Technology Stacks

Defining workloads will vary based on the runtime / technology being used in the repository. Please reference based on the runtime you have determined:

| Runtime               | Reference                       |
| --------------------- | ------------------------------- |
| `dotnet`              | ./references/dotnet.md          |
| `go`                  | ./references/golang.md          |
| `java` (using Maven)  | ./references/java-maven.md      |
| `java` (using Gradle) | ./references/java-gradle.md     |
| `python`              | ./references/python.md          |
| `redpandaconnect`     | ./references/redpandaconnect.md |

If your runtime is not listed here, then it is not supported by Sonic Pipeline at the moment.

## Indicator of Sonic Pipeline in Platform Metadata

A component's platform metadata (a.k.a. PMD) should have `sonic-pipeline` added to its tags. Therefore if the component is already onboarded onto Sonic Pipeline, this field will look like this:

``` json
"tags": [
  "sonic-pipeline"
]
```

## Onboarding to Sonic Pipeline

When onboarding an application to Sonic Pipeline, you should follow these steps:

1. Create the `.sonic/sonic.yml` file with the required metadata and environment information.
2. Define the workloads and configure their artifacts and deployments based on their runtimes.
3. You should update the GitHub Workflows by removing any event triggers (e.g. `push` and `pull_request`) from workflows that build, test and deploy; examples of such workflows are `ad-hoc.yml` and `build-deploy.yml`, but they will be different for each application repository.
