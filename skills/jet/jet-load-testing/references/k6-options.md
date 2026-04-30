# k6 Options Reference

Configuration reference for k6 test scripts, including JET-specific cloud requirements.

## Official Documentation

- **k6 Options Reference**: https://grafana.com/docs/k6/latest/using-k6/k6-options/reference/
- **k6 Cloud Options**: https://grafana.com/docs/grafana-cloud/testing/k6/author-run/cloud-scripting-extras/cloud-options/

## Options Block Structure

```js
export const options = {
  // Execution configuration
  vus: 10,
  duration: '30s',
  iterations: 100,

  // Stages for ramping
  stages: [
    { duration: '1m', target: 10 },
    { duration: '5m', target: 10 },
    { duration: '1m', target: 0 },
  ],

  // Thresholds for pass/fail criteria
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.01'],
  },

  // Scenarios for complex execution patterns
  scenarios: {
    my_scenario: {
      executor: 'constant-vus',
      vus: 10,
      duration: '5m',
    },
  },

  // Cloud-specific options (see JET Requirements below)
  cloud: {
    projectID: 12345,
    name: 'My Load Test',
    staticIPs: true,
  },
};
```

## Common Options

| Option | Type | Description |
|--------|------|-------------|
| `vus` | integer | Number of virtual users |
| `duration` | string | Total test duration (e.g., `'30s'`, `'5m'`) |
| `iterations` | integer | Total number of script iterations |
| `stages` | array | Ramping stages for VU count |
| `thresholds` | object | Pass/fail criteria |
| `scenarios` | object | Named execution scenarios |

## Scenarios

Scenarios allow fine-grained control over test execution:

```js
export const options = {
  scenarios: {
    constant_load: {
      executor: 'constant-vus',
      vus: 10,
      duration: '5m',
    },
    ramping_load: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 20 },
        { duration: '5m', target: 20 },
        { duration: '2m', target: 0 },
      ],
    },
    spike_test: {
      executor: 'ramping-arrival-rate',
      startRate: 10,
      timeUnit: '1s',
      preAllocatedVUs: 50,
      stages: [
        { duration: '10s', target: 10 },
        { duration: '1m', target: 100 },
        { duration: '10s', target: 10 },
      ],
    },
  },
};
```

### Available Executors

Multiple executors are available and documented here: https://grafana.com/docs/k6/latest/using-k6/scenarios/executors/

If the user has a specific rate they want to hit - an arrival-rate executor SHOULD be used. If they are trying to understand upper capacity, a VU executor SHOULD be used.

Externally Controlled is not used at JET.

## [Thresholds](https://grafana.com/docs/k6/latest/using-k6/thresholds/)

Thresholds allow for pass/fail criteria to be defined. These thresholds can also abort tests in the case of excessive failures to prevent real user impact.

```js
export const options = {
  thresholds: {
    // HTTP request duration
    http_req_duration: ['p(95)<500', 'p(99)<1000'],
    
    // Error rate
    http_req_failed: ['rate<0.01'],
    
    // Custom metrics
    my_custom_metric: ['avg<100'],
    
    // Threshold with abort
    http_req_duration: [
      { threshold: 'p(99)<1500', abortOnFail: true, delayAbortEval: '10s' },
    ],
  },
};
```

---

## JET Cloud Requirements

When running tests on k6 Cloud at JET, the following requirements MUST be followed:

### 1. Project ID (REQUIRED)

All cloud tests **MUST** have `options.cloud.projectID` defined.

```js
export const options = {
  cloud: {
    projectID: 12345, // REQUIRED
  },
};
```

**If the project ID is unknown:**
- Check existing load tests in the repository for the project ID
- Ask the user to provide the project ID

**If the user states they have not created a project:**
- Follow the [k6 project creation](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/load-testing/getting-started/onboarding/#k6-project-creation) steps.
- Add the **team** project in the [jetloadtestingmgmt](https://github.je-labs.com/AssuranceServices/jetloadtestingmgmt) repository

### 2. Test Name (RECOMMENDED)

All cloud tests **SHOULD** provide `options.cloud.name` for easy identification in the dashboard.

```js
export const options = {
  cloud: {
    projectID: 12345,
    name: 'Service Name - Endpoint Load Test', // RECOMMENDED
  },
};
```

### 3. Static IPs or Private Load Zone (REQUIRED)

All cloud tests **MUST** either:

**Option A: Enable Static IPs AND define a loadZone**
```js
export const options = {
  cloud: {
    projectID: 12345,
    staticIPs: true, // Use static IPs for firewall allowlisting
    distribution: {
      "london": { loadZone: "amazon:gb:london", percent: 100 },
    },
  },
};
```

A list of available zones can be found in the [backstage documentation](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/load-testing/k6/runbook/dedicated-ips/).

**Option B: Use a Private Load Zone**
```js
export const options = {
  cloud: {
    projectID: 12345,
    distribution: {
      'euw1-plz': { loadZone: 'euw1-plt-2-prd-plz', percent: 100 },
    },
  },
};
```

Any service using a `jet-internal.com` hostname MUST use the PrivateLoadZone.

A list of load zones can be found in the [backstage documentation](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/load-testing/test-configuration/private-load-zones/).

**Why?** JET services typically require allowlisted IP addresses for external access. Without static IPs or a private load zone, tests may fail due to firewall restrictions.
