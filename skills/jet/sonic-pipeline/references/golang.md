# Go in Sonic CI

Here are the specifics required to be understood in order to define Go workloads.

## Unit Tests

The unit tests are ran by running the following command in the `app` directory (where the `go.mod` file is found) in the workload source directory:

``` bash
go test -json
```

The command will have any configured flags appended to it.

## Integration Tests

Sonic Pipeline does not support running integration tests for Go applications.

## E2E Tests

The E2E tests are ran by running the `run-tests.sh` script in the workload source directory:

``` bash
bash run-tests.sh --type {type} --env {env} --json --output some/path/to/output.json
```

The script must support the following parameters:

- `--type {type}`\
  The type of tests being ran, this will have value `e2e` for E2E tests.
- `--env {env}`\
  The environment that the E2E tests will be testing.
- `--output {path}`\
  The path to a JSON file where the test output will be written.
- `--json`\
  A flag indicating that the test output should be JSON. The script only needs to support this if it supports other output types.

**Important Note:** You can't configure any flags to pass to the `/run-tests.sh` script.

If the E2E tests are written in Go, and they are placed in the `/tests/e2e` directory, then that test module will be initialized.

## Acceptance Tests

The Acceptance tests are ran by running the `run-tests.sh` script in the workload source directory:

``` bash
bash run-tests.sh --type {type} --env {env} --json --output some/path/to/output/provided/by/sonic/pipeline.json
```

The script must support the following parameters:

- `--type {type}`\
  The type of tests being ran, this will have value `acceptance` for Acceptance tests.
- `--env {env}`\
  The environment that the Acceptance tests will be testing.
- `--output {path}`\
  The path to a JSON file where the test output will be written.
- `--json`\
  A flag indicating that the test output should be JSON. The script only needs to support this if it supports other output types.

**Important Note:** You can't configure any flags to pass to the `run-tests.sh` script.

If the Acceptance tests are placed in the `tests/acceptance` directory, then that test module will be automatically initialized by Sonic Pipeline.
