# Worker Tests Reference

Worker tests target message-based systems such as Kafka and SQS. These tests measure message publishing throughput rather than end-to-end processing latency.

## Official Documentation

- **JET Worker Testing Backstage Docs**: https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/load-testing/getting-started/worker-testing/
- **JET k6 Templates Repository**: https://github.je-labs.com/AssuranceServices/k6-templates/tree/main/templates/messaging

## Important Limitation

When using k6 to test workers, you can only measure **message publishing throughput**. k6 publishes messages to Kafka or SQS but cannot observe how long the downstream worker takes to process those messages. End-to-end processing latency must be measured via application metrics or tracing.

## Templates


- **[k6-kafka-test.js](https://github.je-labs.com/AssuranceServices/k6-templates/blob/main/templates/messaging/kafka/kafka_example.js)** - Kafka test
- **[k6-sqs-test.js](https://github.je-labs.com/AssuranceServices/k6-templates/blob/main/templates/messaging/SQS/sqs_example.js)** - SQS test

---

## Kafka Testing

Kafka tests use the [xk6-kafka](https://github.com/mostafa/xk6-kafka) extension to produce and consume messages. This is already installed in our [PrivateLoadZone](./k6-options.md#3-static-ips-or-private-load-zone-required).

### Prerequisites

- **Kafka Cluster**: Ensure your Kafka cluster is running with an existing topic.
- **Secrets**: `KAFKA_USER` and `KAFAKA_PASS` must be stored as Secrets as per [this guidance](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/load-testing/test-configuration/secrets/). The user MUST be prompted to add this themselves.
- **Private Load Zone**: Tests MUST be run from a [Private Load Zone](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/load-testing/test-configuration/private-load-zones/) to ensure connectivity.

### Configuration

Update the following in the test script. If values can be inferred use these, otherwise you MUST ask the user.

```js
const KAFKA_BROKERS = ['broker1:9092', 'broker2:9092'];
const KAFKA_TOPIC = 'your_kafka_topic';
```

### Teardown

Always close the producer in the teardown function:

```js
export function teardown() {
  producer.close();
}
```

---

## SQS Testing

SQS tests use the [k6 SQSClient](https://grafana.com/docs/k6/latest/javascript-api/jslib/aws/sqsclient/) from the AWS jslib.

### Prerequisites

- **AWS SQS Queue**: Ensure you have an existing queue with `sqs:SendMessage` permission for the workload role.
- **Private Load Zone**: Tests MUST be run from a [Private Load Zone](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/load-testing/test-configuration/private-load-zones/) to ensure connectivity.

### AWS Authentication

The Private Load Zone (PLZ) provides a workload IAM role for AWS connectivity:

```
arn:aws:iam::058264529639:role/jas/wl/terraform_managed/jas-wl-role-pl-soft-change-platass-jet-k6-operator
```

This role is assumed automatically via the `getTemporaryCredentials()` helper installed on the PLZ:

```js
import getTemporaryCredentials from '../load-testing/lib/get-aws-creds.js';

export function setup() {
  const creds = getTemporaryCredentials();
  if (!creds) {
    throw new Error('Failed to get temporary AWS credentials');
  }
  return creds;
}
```

### SQS Queue Policy

To grant access to the SQS queue, the user MUST add the PLZ role to the queue's resource policy. This is explained [here](https://github.je-labs.com/AssuranceServices/k6-templates/blob/main/templates/messaging/SQS/README.md#aws-authentication).

### KMS-Encrypted Queues

When an SQS queue uses SSE-KMS with a customer-managed KMS key, the workload role must also be allowed to use the KMS key. This is explained [here](https://github.je-labs.com/AssuranceServices/k6-templates/blob/main/templates/messaging/SQS/README.md#using-a-kms-encrypted-sqs-queue-additional-steps).

### FIFO Queues

For FIFO queues (`*.fifo`), you must include `MessageGroupId` in `sendMessage()`:

```js
sqs.sendMessage(queueUrl, messageBody, { messageGroupId: 'my-group' });
```

---

## Best Practices

### MUST

- **Use profiles for parameterisation**: Multi-environment tests MUST use [profiles](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/load-testing/test-configuration/profiles/) for configuration.
- **Use Private Load Zones**: Worker tests MUST run from a [Private Load Zone](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/load-testing/test-configuration/private-load-zones/) to ensure connectivity to internal messaging systems.
- **Implement teardown**: Kafka tests MUST close producers in the `teardown()` function to release resources.
- **Utilise GitHub Actions**: All tests outside of development must be triggered through [GitHub Actions](./github-actions.md).

### SHOULD

- **Use scenarios**: For complex test profiles (ramp-up, steady state, spike, soak).
- **Utilise secrets**: For storing of any Kafaka credentials.
- **Update IAM policies**: Ensure the PLZ workload role has appropriate permissions for SQS and KMS.

### COULD

- **Add message metadata**: Include timestamps, correlation IDs, or other metadata for debugging.
- **Vary message payloads**: Use realistic message sizes and content for accurate throughput testing.
