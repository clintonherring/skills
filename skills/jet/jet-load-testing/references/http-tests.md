# HTTP Tests Reference

HTTP tests target REST APIs, web endpoints, and other HTTP-based services. This is the most common type of load test at JET.

## Official Documentation

- **k6 HTTP Module**: https://grafana.com/docs/k6/latest/javascript-api/k6-http/
- **JET Load Testing Backstage Docs**: https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/load-testing

## Templates

- **[k6-http-test.js](../templates/k6-http-test.js)**: Basic HTTP test template
- **[k6-http-inline-profile.js](../templates/k6-http-inline-profile.js)**: HTTP test with inline profile configuration
- **[k6-http-file-profile.js](../templates/k6-http-file-profile.js)**: HTTP test with file-based profile configuration

## Thresholds

HTTP tests should use these built-in metrics for thresholds:

```js
export const options = {
  thresholds: {
    // Response time thresholds
    http_req_duration: ['p(95)<500', 'p(99)<1000'],
    
    // Error rate threshold
    http_req_failed: ['rate<0.01'],
    
    // Threshold with abort on failure
    http_req_duration: [
      { threshold: 'p(99)<1500', abortOnFail: true, delayAbortEval: '10s' },
    ],
  },
};
```

[k6 thresholds reference](https://grafana.com/docs/k6/latest/using-k6/thresholds).

## Checks

HTTP tests should validate response status codes and body content where possible:

```js
import http from 'k6/http';
import { check } from 'k6';

export default function () {
  const res = http.get('https://api.example.com/orders');
  
  check(res, {
    'status is 200': (r) => r.status === 200,
    'response has orders': (r) => r.json().orders !== undefined,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });
}
```

[k6 checks reference](https://grafana.com/docs/k6/latest/using-k6/checks/).

## Request Tagging

Tag requests to reduce high cardinality and ensure meaningful metrics: https://grafana.com/docs/k6/latest/using-k6/tags-and-groups/#tags

```js
import http from 'k6/http';

export default function () {
  // Tag with a static name to avoid high cardinality from dynamic URLs
  const res = http.get('https://api.example.com/orders/12345', {
    tags: { name: 'GetOrder' },
  });
}
```

For dynamic URLs, use the `name` tag to group metrics:

```js
import http from 'k6/http';

export default function () {
  const orderId = Math.floor(Math.random() * 10000);
  
  // Without tagging, each unique URL creates separate metrics
  // With tagging, all requests are grouped under 'GetOrder'
  const res = http.get(`https://api.example.com/orders/${orderId}`, {
    tags: { name: 'GetOrder' },
  });
}
```

## Grouping Requests

Use `group()` to logically organise related requests within a test: https://grafana.com/docs/k6/latest/using-k6/tags-and-groups/#groups
---

## Best Practices

### MUST

- **Define thresholds**: Every HTTP test MUST have explicit pass/fail criteria defined using thresholds.
- **Include checks**: Tests MUST validate response status codes and body content where possible, not just throughput.
- **Use profiles for parameterisation**: Multi-environment tests MUST use [profiles](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/load-testing/test-configuration/profiles/) for configuration.
- **Tag requests**: Use the `name` tag to reduce high cardinality in test results and ensure meaningful metrics.
- **Utilise GitHub Actions**: All tests outside of development must be triggered through [GitHub Actions](./github-actions.md).
- **Utilise [PrivateLoadZones](./k6-options.md#3-static-ips-or-private-load-zone-required)**: For tests targeting internal-only endpoints.
- **Only test appropriate endpoints**: Health and readiness probes do not need testing.

### SHOULD

- **Use scenarios**: For complex test profiles (ramp-up, steady state, spike, soak).
- **Validate response bodies**: Check that response content matches expected values, not just status codes.
- **Follow [Cloud test requirements](./k6-options.md#jet-cloud-requirements)**: When running via `cloud` execution mode.

### COULD

- **Use `group()`**: To logically organise related requests within a test for better reporting.
- **Use `http.batch()`**: To send multiple requests in parallel when simulating concurrent API calls.
