# Java (Maven) in Sonic CI

Here are the specifics required to be understood in order to define Java workloads that use Maven.

## Unit Tests

The unit tests are ran by running this `mvn` command at the root of the repository:

``` bash
mvn org.jacoco:jacoco-maven-plugin:prepare-agent test org.jacoco:jacoco-maven-plugin:report
```

You are able to configure workflow inputs for unit tests, like so:

``` yaml
- type: unit
  workflowInputs:
    # This allows you to change the Maven goal to run instead of the default `test`.
    - maven-goals: "clean test"
```

## Integration Tests

The integration tests are ran by running this `mvn` command at the root of the repository:

``` bash
mvn org.jacoco:jacoco-maven-plugin:prepare-agent verify org.jacoco:jacoco-maven-plugin:report
```

**Important:** For integration tests the `DskipUnitTests` is set to `true`.

In addition, you are able to configure workflow inputs for integration tests, like so:

``` yaml
- type: integration
  workflowInputs:
    # This allows you to change the Maven goal to run instead of the default `verify`.
    - maven-goals: "integration"
```

## E2E Tests

Sonic Pipeline does not support running E2E tests for Java applications using Maven.

## Acceptance Tests

Sonic Pipeline does not support running Acceptance tests for Java applications using Maven.
