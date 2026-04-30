# Redpanda Connect in Sonic CI

Here are the specifics required to be understood in order to define Redpanda Connect workloads.

## Workload Artifact Definition

Redpanda Connect workload artifacts will always look like this:

``` bash
name_of_workload:
  appType: worker
  runtime: redpandaconnector
  runtimeVersion: 0
  tests: []
```

The application type will always be a `worker`, the runtime version will always be `0` and no tests are currently supported.

## The Dockerfile

Most Redpanda Connect workloads will be using the official Redpanda Connect image that is available from the JET Artifactory: `artifacts.takeaway.com/docker-virtual/redpandadata/connect`.

However there are some Redpanda Connect powered workloads that have a more complex setup, usually using streams mode, where configuration needs to be baked into the image, which would mean building the image using a `Dockerfile` found in the workload source directory.

## Unit Tests

Sonic Pipeline does not support running unit tests for Redpanda Connect workloads.

## Integration Tests

Sonic Pipeline does not support running integration tests for Redpanda Connect workloads.

## E2E Tests

Sonic Pipeline does not support running E2E tests for Redpanda Connect workloads.

## Acceptance Tests

Sonic Pipeline does not support running Acceptance tests for Redpanda Connect workloads.

## References

- [Redpanda Connect Documentation](https://docs.redpanda.com/)
