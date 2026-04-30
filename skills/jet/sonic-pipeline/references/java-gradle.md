# Java (Gradle) in Sonic CI

Here are the specifics required to be understood in order to define Java workloads that use Gradle.

**Important:** Sonic Pipeline expects a `build.gradle` file or a `build.gradle.kts` to be at the root of the repository.

## Unit Tests

The unit tests are ran by running the `gradlew` wrapper script at the root of the repository:

``` bash
./gradlew test
```

You are able to configure workflow inputs for unit tests, like so:

``` yaml
- type: unit
  workflowInputs:
    # This allows you to change the Gradle goal to run instead of the default `test`.
    - goals: "clean test"
    # The Java distribution to use, Sonic Pipeline will default to `temurin`.
    - distribution: "corretto"
```

## Integration Tests

The integration are ran by running the `gradlew` wrapper script at the root of the repository:

``` bash
./gradlew test
```

You are able to configure workflow inputs for integrations tests, like so:

``` yaml
- type: integration
  workflowInputs:
    # This allows you to change the Gradle goal to run instead of the default `test`.
    - goals: "clean test"
    # The Java distribution to use, Sonic Pipeline will default to `temurin`.
    - distribution: "corretto"
```

**Important:** Due to Sonic Pipeline using the same default `test` goal for both unit and integration tests, then it is important that the `goals` workflow input is configured.

## E2E Tests

Sonic Pipeline does not support running E2E tests for Java applications using Gradle.

## Acceptance Tests

Sonic Pipeline does not support running Acceptance tests for Java applications using Gradle.
