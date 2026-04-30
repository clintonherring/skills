# Python in Sonic CI

Here are the specifics required to be understood in order to define Python workloads.

## Dependencies Managers

By default, Sonic Pipeline will use the `poetry` dependency manager, however you can configure each workload artifact to utilize `pip` instead:

``` yaml
name_of_workload:
  appType: api
  runtime: python
  runtimeVersion: 3 # This MUST only reflect the major version of the runtime, do not include the minor or patch part of the version.
  tests:
    - type: unit
      workflowInputs:
        - use-poetry: false
```

## Unit Tests

The unit tests are ran, using `pytest`, by running this command in the workload source directory:

``` bash
pytest {pytest-args} --cov --cov-report=xml:coverage.xml --cov-report=html:htmlcov --cov-report=term --junitxml=junit.xml
```

By default the arguments passes to `pytest` is `tests/ -v`, which means the unit tests expected to be placed in the `tests` directory in the workload source directory. You can provide some **alternative** arguments to `pytest` by configuring the workload test, like so:

``` yaml
tests:
  - type: unit
    workflowInputs:
      - args: "specs/ -v"
```

**Important Note:** It is not possible to override the code coverage arguments passed to `pytest`.

## Integration Tests

The integration tests are ran exactly the same as unit tests, including with the same default `tests` directory configuration. This means it is important that you configure different `pytest` args:

``` yaml
tests:
  - type: integration
    workflowInputs:
      - args: "intregration-tests/ -v"
```

## E2E Tests

E2E tests for Python applications are executed by running the `run_e2e_tests.sh` script in the workload source directory:

``` bash
./run_e2e_tests.sh {flags}
```

The script receives any configured flags and environment variables from the deployment test configuration.

By default, Poetry is used for dependency management during E2E test execution. You can switch to pip by configuring the `workflowInputs`:

``` yaml
deployment:
  name_of_workload:
    tests:
      - type: e2e
        env:
          - name: ExampleEnvironmentVariable
            value: value
        flags:
          - "--example-flag"
        workflowInputs:
          - use-poetry: false
          - requirements-file: "requirements-e2e.txt"
```

The `requirements-file` input allows specifying a custom requirements file when using pip (defaults to `requirements.txt`).

## Acceptance Tests

Sonic Pipeline does not support running Acceptance tests for Python applications.

## Linting

You can enable an optional code linting process, powered by `ruff`, by configuring a test entry like so:

``` yaml
tests:
  - type: unit
    workflowInputs:
      - run-ruff: true
```

**Important Note:** It is not possible to configure how `ruff` is run. It will run against the entire workload source directory so it only needs to be enabled for one of the test entries.

## Type Checking

You can enable an optional type checking process, powered by `mypy`, by configuring a test entry like so:

``` yaml
tests:
  - type: unit
    workflowInputs:
      - run-mypy: true
```

**Important Note:** It is not possible to configure how `mypy` is run. It will run against the entire workload source directory so it only needs to be enabled for one of the test entries.
