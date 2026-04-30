---
name: jet-load-testing
description: Load and performance testing at Just Eat Takeaway.com using k6. Use this skill when writing, managing, or maintaining load tests, performance tests, stress tests, spike tests, or soak tests. Triggers include creating new k6 test scripts, debugging test failures, configuring test thresholds, setting up test scenarios, creating a load testing Github Actions Workflow, or integrating within CI/CD pipelines.
metadata:
  owner: platform-assurance
---

# JET Load Testing

Write, manage, and maintain load and performance tests at Just Eat Takeaway.com.

## When to use

- Writing new load or performance test scripts
- Modifying or debugging existing load tests
- Configuring test thresholds, scenarios, or options
- Setting up CI/CD pipelines for performance testing

## Prerequisites

- [jet-company-standards](https://github.je-labs.com/ai-platform/skills/tree/master/skills/jet-company-standards) skill installed. This MUST be used for referencing backstage documentation.
- k6 installed locally

### k6 Installation

macOS/Linux: `brew install k6`
Windows (PowerShell): `winget install GrafanaLabs.k6`

Refer to the official installation guide if needed: https://grafana.com/docs/k6/latest/set-up/install-k6/

### Documentation

Additional context on load testing practices at JET can be found in the Backstage documentation:
- https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/load-testing

## Instructions

### Tool

**k6** is the global load testing service at JET and MUST be used for all load and performance tests. Do not use other tools (e.g. JMeter, Locust, Gatling).

### Test Types

JET supports testing of both HTTP APIs and Workers. You MUST determine which type applies before proceeding:

- **HTTP Tests**: Tests that target HTTP endpoints (REST APIs, web services). These tests measure response times and error rates of HTTP requests. Refer to the [HTTP Tests Reference](./references/http-tests.md) for more details. If you believe an endpoint should be excluded, you MUST ask the user for claification.
- **Worker Tests**: Tests that target message-based systems (Kafka or SNS/SQS). These tests measure message publishing throughput. Refer to the [Worker Tests Reference](./references/worker-tests.md) for more details.

You MUST try to determine if the application is a Worker or an HTTP API (or both). If this cannot be determined, ask the user for clarification. This will determine the type of test script template to use and the relevant SLOs to ask for. If the application is both an HTTP API and a Worker, you should create separate test scripts for each aspect.

**If the only HTTP endpoint is a healthcheck, and it is clear the application handles messages - consider it a worker NOT both.**

### Running Tests

**WARNING: Tests targeting production environments MUST NOT be run from a local machine.**

Production load tests MUST only be executed via:
- GitHub Actions Workflows

Local execution is only permitted for:
- Development and debugging against non-production environments

### Required User Input

#### HTTP Tests

Before writing any new HTTP load test OR modifying thresholds/throughput of an existing HTTP test, you MUST ask the user for their Service Level Objectives (SLOs) AND throughput information including load profile. Do not proceed without this information.

Ask the user:
1. **Service/Application name** — e.g., "What service are you testing?" (e.g., order-service, menu-api, reliabilityinsightsapi)
2. **Response time SLOs** — e.g., "What is your p95/p99 latency target?" (e.g., p95 < 500ms)
3. **Error rate SLOs** — e.g., "What is your acceptable error rate?" (e.g., < 0.1%)
4. **Throughput requirements** — e.g., "What RPS (requests per second) must the service handle?"
5. **Load Profile** - e.g., "What does your expected traffic pattern look like? (steady, ramp-up to known peak, ramp-up to stress, spike, soak)" - Refer to [k6 execution options](./references/k6-options.md#available-executors).

Use these SLOs directly as k6 thresholds:

```js
export const options = {
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'], // Replace with user's latency SLOs
    http_req_failed: ['rate<0.001'], // Replace with user's error rate SLO
  },
};
```

If the user doesn't know their SLOs or throughput, use these defaults:
- **p95 latency**: < 500ms
- **p99 latency**: < 1000ms
- **Error rate**: < 0.1%
- **Throughput**: 5 RPS

Inform the user these defaults are being applied and recommend they refine them based on product requirements.

#### Worker Tests

For non-HTTP tests (e.g., worker performance tests), you MUST ask the user for throughput requirements AND load profile. Use this information to configure the test.

Ask the user:
1. **Service/Application name** — e.g., "What service/worker are you testing?" (e.g., order-processor, menu-indexer)
2. **Throughput requirements** — e.g., "How many messages must the worker process per second?"
3. **Load Profile** - e.g., "What does your expected traffic pattern look like? (steady, ramp-up to known peak, ramp-up to stress, spike, soak)" - Refer to [k6 execution options](./references/k6-options.md#available-executors).

If the user doesn't know their throughput requirements, use a default of 5 messages per second. Inform the user this default is being applied and recommend they refine it based on product requirements.

### k6 Test Script Structure

New test scripts should follow the standard structure based on test type:

**HTTP Tests:**
- Base template: [templates/k6-http-test.js](templates/k6-http-test.js)

**Worker Tests:**
- Kafka template: [templates/k6-kafka-test.js](https://github.je-labs.com/AssuranceServices/k6-templates/blob/main/templates/messaging/kafka/kafka_example.js)
- SQS template: [templates/k6-sqs-test.js](https://github.je-labs.com/AssuranceServices/k6-templates/blob/main/templates/messaging/SQS/sqs_example.js)

### Test Naming & Directory Convention

Tests should have a simple yet descriptive name. If only a single endpoint or topic is being tested, that should be in the name.

By default, load tests should be placed in a `.load-tests` directory at the project root.

**Simple tests** (inline profiles):
```
project-root/
├── .load-tests/
│   ├── smoke.js
│   ├── load.js
│   └── stress.js
```

**Complex tests** (file-based profiles):
```
project-root/
├── .load-tests/
│   └── my-service/
│       ├── script.js
│       └── profiles/
│           ├── staging-uk.json
│           ├── uk-production.json
│           └── i18n-production.json
```

If the user requests a different location, follow their preference.

### Test Display Names (Cloud Options)

All tests MUST set a descriptive `name` in the k6 cloud options. This name appears in the Grafana Cloud UI and Slack notifications, making it easy to identify what test is running. For full guidance on test naming, see the load-testing [best practices](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/load-testing/getting-started/best-practices/#best-practices).

**Naming Convention:**

The test name should include:
- **Service/application name** (e.g., `reliabilityinsightsapi`, `partnerlistingapi`, `order-service`)
- **Test type** (e.g., `load`, `smoke`, `stress`, `spike`, `soak`)
- **Optional identifiers**: environment, market, scenario, or load profile (e.g., `UK`, `staging`, `peak-load`, `i18n`)

**Good Examples:**
```js
export const options = {
  cloud: {
    name: 'UK: stress test - SampleApi',
  },
};
```
```js
export const options = {
  cloud: {
    name: 'SampleAPI - smoke test',
  },
};
```
```js
export const options = {
  cloud: {
    name: 'order-service - load test - peak traffic',
  },
};
```

**Avoid:**
- Generic names: `load test`, `smoke`, `test1`
- Non-descriptive names: `my-test`, `api-test`
- Missing service identification

**When creating new tests, construct the cloud name using:**
1. The service/application name (from user input)
2. The test type (smoke/load/stress/spike/soak)
3. Any environment or market specifics mentioned by the user

### k6 Options Configuration

For detailed options configuration including test naming requirements and JET-specific cloud requirements, see [references/k6-options.md](references/k6-options.md).

### Profiles

Profiles are the JET-recommended way to parameterise load tests for different **environments**. They allow environment-specific configurations (base URLs, VU counts, thresholds) to be passed via the GitHub Actions Workflow `profile` input.

Full documentation: https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/load-testing/test-configuration/profiles/

#### Inline Profiles (Simple Tests)

Simple tests can have profiles defined directly within the script. See [templates/k6-http-inline-profile.js](templates/k6-http-inline-profile.js) for an HTTP example.

Run locally with: `k6 run -e PROFILE=staging-uk script.js`

#### File-Based Profiles (Complex Tests)

Complex tests with many configuration options can use separate JSON profile files. See [test naming and directory convention](#test-naming--directory-convention) for the structure.

**profiles/staging-uk.json:**
```json
{
  "baseUrl": "https://api.uk.example.com",
  "vus": 10,
  "duration": "5m",
  "thresholds": {
    "http_req_duration": ["p(95)<500", "p(99)<1000"],
    "http_req_failed": ["rate<0.01"]
  }
}
```

**script.js:** See [templates/k6-http-file-profile.js](templates/k6-http-file-profile.js) for an HTTP test template utilising file-based profiles.

Run with: `k6 run -e PROFILE=staging-uk script.js`

### Secrets Management

Any secure data for use within tests **MUST** be stored as GitHub Secrets and accessed via environment variables in the test script. Refer to [this guidance](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/load-testing/test-configuration/secrets/) for how to set up secrets.

### Test Data

Ensure all the required parameters for each endpoint or message are included. Where possible, generate realistic test data (e.g., names, emails). In complex cases, you MUST ask the user for sample data or data generation rules.

### GitHub Actions

All tests outside of development must be triggered through [GitHub Actions](./references/github-actions.md). You MUST ensure all required inputs are present.

### Private Load Zones

Tests targeting internal-only endpoints (including all worker tests) MUST use [Private Load Zones](./references/k6-options.md#3-static-ips-or-private-load-zone-required).

## References

- [k6 Documentation](https://k6.io/docs/)
- [JET Load Testing Backstage Docs](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/load-testing)
- [HTTP Tests Reference](./references/http-tests.md)
- [Worker Tests Reference](./references/worker-tests.md)
- [k6 Options Reference](./references/k6-options.md)
- [GitHub Actions Workflow Reference](./references/github-actions.md)