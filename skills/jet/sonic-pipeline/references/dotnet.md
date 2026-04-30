# .NET in Sonic CI

Here are the specifics required to be understood in order to define .NET workloads.

**Important:** Sonic Pipeline sets up .NET SDK using the `global.json` in the workload's source directory.

## Unit Tests

The unit tests are ran by running the `build.ps1` script in the workload source directory:

``` bash
./build.ps1 {flags}
```

The command will have any configured flags appended to it.

### Determining Required Flags

Unlike other runtimes (Go, Java, Python) where the pipeline test command runs tests by default, the .NET pipeline delegates entirely to the repository's `build.ps1` script. This means `build.ps1` controls whether tests actually execute, and **the pipeline will succeed (exit 0) even if no tests run**.

You **must** inspect the `build.ps1` script in the workload source directory to determine which flags are required to actually run tests. Look for:

- **Switch parameters** that gate test execution (e.g. `-RunTests`, `-Test`, `-ExecuteTests`).
- **Conditional blocks** like `if ($RunTests) { ... } else { Write-Host "tests skipped" }`.
- **Flags that skip non-test steps** to speed up the pipeline (e.g. `-SkipPublish`, `-SkipPack`).

A common pattern in JET .NET repositories is:

``` powershell
param(
    [switch]$RunTests,
    [switch]$SkipPublish
)

if ($RunTests -eq $true) {
    # ... runs tests
}
else {
    Write-Host "Unit tests are set to skip"
}
```

In this case, the `sonic.yml` test entry **must** include `-RunTests` as a flag, otherwise the pipeline will report success without running any tests:

``` yaml
tests:
  - type: unit
    flags:
      - "-RunTests"
      - "-SkipPublish"  # Optional: skip publish step during test-only runs.
```

**If `build.ps1` does not have any switch parameters that gate test execution** (i.e. it always runs tests), then no flags are required and the test entry can omit `flags`.

## Integration Tests

Sonic Pipeline does support integration tests for .NET workloads, however they are expected to run together alongside the unit tests.

When you configure tests, like so:

``` yaml
- type: unit
- type: integration
```

This configuration only results in execution of the `build.ps1` script in the workload source directory. Defining integration tests just tells Sonic Pipeline to spin up supporting dependencies using a `docker-compose.yml` file found in the workload source directory before running that `build.ps1` script.

This also means that unit tests and integration tests can't have different flags and environment variables, and both `sonic.yml` test entries need to be configured with the exact same flags and environment variables.

For example, if the `build.ps1` requires `-RunTests` to execute tests:

``` yaml
tests:
  - type: unit
    flags:
      - "-RunTests"
      - "-SkipPublish"
  - type: integration
    flags:
      - "-RunTests"
      - "-SkipPublish"
```

## E2E Tests

The E2E tests are ran by running the `build.ps1` script in the workloads' source directory:

``` bash
./build.ps1 -EndToEndTestEnvironment {env}
```

The `build.ps1` script must support the following parameters:

- `EndToEndTestEnvironment {env}`
  The environment that the E2E tests will be testing. This should be used to indicate that the script should be running E2E tests.

The command will have any configured flags appended to it.

## Acceptance Tests

The Acceptance tests are ran by running the `/run-acceptance-tests.ps1` script in the workloads' source directory:

``` bash
./run-acceptance-tests.ps1 -AcceptanceTestEnvironment {env}
```

The `run-acceptance-tests.ps1` script must support the following parameters:

- `-AcceptanceTestEnvironment {env}`
  The environment that the Acceptance tests will be testing.

The command will have any configured flags appended to it.

## External Repository for E2E and Acceptance Tests

For .NET applications, E2E tests and Acceptance tests can be in a completely different repository, this can be configured in the deployment test configuration, for example:

``` yaml
- type: acceptance
  location:
    # The repository that contains the E2E and/or Acceptance tests.
    repository: owner/repo
    # The path where the `build.ps1` or `run-acceptance-tests.ps1` script lives in the repository.
    path: ./path-to-test-scripts
    # The path to the `global.json` file in the repository.
    global-json-file: global.json
```

## AWS IAM Role Assumption for E2E Tests

For .NET E2E tests that require AWS access, you can configure OIDC-based IAM role assumption. This allows the E2E test runner to assume a team-specific AWS role during execution:

``` yaml
deployment:
  name_of_workload:
    tests:
      - type: e2e
        assumeTeamRole: true
        teamSid: "your-team-sid"
```

The `teamSid` is used to look up the correct IAM role ARN for the team via OIDC. When `assumeTeamRole` is set to `true`, the pipeline will configure AWS credentials before running the E2E tests.
