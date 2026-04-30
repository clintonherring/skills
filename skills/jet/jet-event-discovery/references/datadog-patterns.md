# Datadog Query Patterns for Event-Driven Discovery

Runtime-level discovery of messaging activity using the `pup` CLI against JET's EU Datadog site.

## Case Sensitivity

- **Datadog log search queries**: Unstructured text search (the `--query` parameter) is **case-insensitive by default**. A search for `myevent` will match `MyEvent` in log messages.
- **Attribute filters**: Filters on structured attributes (e.g., `service:my-service`, `@topic:my-topic`) are **case-sensitive**. When filtering by attribute values, use wildcards if unsure of casing (e.g., `@topic:*myevent*`).
- **Metrics queries**: Metric tag values are typically lowercase. Use the exact tag value as stored (check with `pup metrics search` if unsure).

## Table of Contents
- [Setup](#setup)
- [Kafka Discovery](#kafka-discovery)
- [SNS/SQS Discovery](#snssqs-discovery)
- [RabbitMQ Discovery](#rabbitmq-discovery)
- [Error Investigation](#error-investigation)
- [Consumer Health](#consumer-health)
- [Throughput & Metrics](#throughput--metrics)
- [APM Service Dependencies](#apm-service-dependencies)
- [Cross-Platform Queries](#cross-platform-queries)

---

## Setup

JET uses the EU Datadog site and stores logs in Flex Logs. These two settings are non-negotiable for every query:

```bash
export DD_SITE=datadoghq.eu
# All log commands MUST include --storage=flex
```

Verify access:

```bash
pup auth status
```

If not authenticated, run `pup auth login` or set `DD_API_KEY` + `DD_APP_KEY` + `DD_SITE` env vars.

---

## Kafka Discovery

### Find all services producing Kafka messages

```bash
# Group by service to see which services produce Kafka messages
pup logs aggregate \
  --query="(kafka OR KafkaTemplate OR KafkaProducer OR ProducerRecord) AND (produce OR send OR publish)" \
  --from=24h --compute="count" --group-by="service" --storage=flex
```

### Find all services consuming Kafka messages

```bash
pup logs aggregate \
  --query="(kafka OR KafkaListener OR KafkaConsumer) AND (consume OR receive OR poll OR listener OR commit)" \
  --from=24h --compute="count" --group-by="service" --storage=flex
```

### Find services interacting with a specific topic

```bash
# Replace TOPIC_NAME with the actual topic
pup logs aggregate \
  --query="TOPIC_NAME" \
  --from=24h --compute="count" --group-by="service" --storage=flex

# Get actual log lines to understand producer vs consumer
pup logs search \
  --query="TOPIC_NAME" \
  --from=1h --limit=20 --storage=flex
```

### Discover topic names from logs

```bash
# Search for common Kafka topic log patterns
pup logs search \
  --query="(topic OR Topic) AND kafka" \
  --from=1h --limit=30 --storage=flex

# Search for Spring Kafka topic binding logs
pup logs search \
  --query="Kafka MessageListenerContainer AND topic" \
  --from=1h --limit=20 --storage=flex
```

### Kafka consumer group activity

```bash
# Find consumer group references
pup logs search \
  --query="(consumer.group OR group.id OR ConsumerGroup) AND kafka" \
  --from=1h --limit=20 --storage=flex

# Group by consumer group
pup logs aggregate \
  --query="kafka AND consumer AND group" \
  --from=24h --compute="count" --group-by="@consumer_group" --storage=flex
```

---

## SNS/SQS Discovery

### Find SNS publishers

```bash
# Services publishing to SNS
pup logs aggregate \
  --query="(sns OR SNS) AND (publish OR PublishCommand OR PublishBatch)" \
  --from=24h --compute="count" --group-by="service" --storage=flex

# Find specific SNS topic ARNs in logs
pup logs search \
  --query="arn:aws:sns:*" \
  --from=1h --limit=20 --storage=flex
```

### Find SQS consumers

```bash
# Services consuming from SQS
pup logs aggregate \
  --query="(sqs OR SQS) AND (receive OR ReceiveMessage OR DeleteMessage OR SQSEvent)" \
  --from=24h --compute="count" --group-by="service" --storage=flex

# Find specific SQS queue URLs/ARNs
pup logs search \
  --query="arn:aws:sqs:*" \
  --from=1h --limit=20 --storage=flex
```

### Find SNS-to-SQS subscriptions (fan-out patterns)

```bash
# Subscription-related activity
pup logs search \
  --query="(sns AND sqs AND subscribe) OR SNSSubscription" \
  --from=24h --limit=20 --storage=flex
```

### Search by specific ARN

```bash
# Replace with actual ARN or partial match
pup logs search \
  --query="arn:aws:sns:eu-west-1:*:ORDER_TOPIC_NAME" \
  --from=1h --limit=20 --storage=flex

pup logs search \
  --query="arn:aws:sqs:eu-west-1:*:QUEUE_NAME" \
  --from=1h --limit=20 --storage=flex
```

---

## RabbitMQ Discovery

### Find services using RabbitMQ

```bash
pup logs aggregate \
  --query="(rabbitmq OR RabbitMQ OR amqp OR AMQP)" \
  --from=24h --compute="count" --group-by="service" --storage=flex
```

### Find exchanges and queues

```bash
# Exchange activity
pup logs search \
  --query="(rabbitmq OR amqp) AND (exchange OR Exchange)" \
  --from=1h --limit=20 --storage=flex

# Queue activity
pup logs search \
  --query="(rabbitmq OR amqp) AND (queue OR Queue)" \
  --from=1h --limit=20 --storage=flex
```

### RabbitMQ connection/channel activity

```bash
pup logs search \
  --query="(rabbitmq OR amqp) AND (connection OR channel)" \
  --from=1h --limit=20 --storage=flex
```

---

## Error Investigation

### Messaging errors across all platforms

```bash
# All messaging errors grouped by service
pup logs aggregate \
  --query="status:error AND (kafka OR sqs OR sns OR rabbitmq OR amqp)" \
  --from=1h --compute="count" --group-by="service" --storage=flex

# Get error details
pup logs search \
  --query="status:error AND (kafka OR sqs OR sns OR rabbitmq OR amqp)" \
  --from=1h --limit=20 --storage=flex
```

### Dead letter queue activity

```bash
# DLQ mentions (common indicator of failed message processing)
pup logs search \
  --query="(dead_letter OR deadletter OR dlq OR DLQ OR dead-letter)" \
  --from=1h --limit=20 --storage=flex

# DLQ activity by service
pup logs aggregate \
  --query="(dead_letter OR deadletter OR dlq OR DLQ)" \
  --from=24h --compute="count" --group-by="service" --storage=flex
```

### Serialization/deserialization errors

```bash
# Schema/serialization issues (common in event-driven systems)
pup logs search \
  --query="status:error AND (serializ OR deserializ OR schema OR avro OR protobuf)" \
  --from=1h --limit=20 --storage=flex
```

### Kafka-specific errors

```bash
# Consumer rebalance issues
pup logs search \
  --query="(rebalance OR Rebalance OR CommitFailed OR OffsetOutOfRange)" \
  --from=1h --limit=20 --storage=flex

# Producer errors
pup logs search \
  --query="status:error AND (kafka OR KafkaProducer) AND (produce OR send OR timeout OR retry)" \
  --from=1h --limit=20 --storage=flex
```

### SQS-specific errors

```bash
# SQS processing errors
pup logs search \
  --query="status:error AND (sqs OR SQS) AND (receive OR process OR visibility)" \
  --from=1h --limit=20 --storage=flex
```

---

## Consumer Health

### Consumer lag

```bash
# Kafka consumer lag (if instrumented with Datadog metrics)
pup metrics query \
  --query="avg:kafka.consumer.lag{*} by {consumer_group,topic}" --from=1h

# Kafka consumer lag by consumer group
pup metrics query \
  --query="max:kafka.consumer.lag{*} by {consumer_group}" --from=1h

# Kafka consumer lag for a specific topic
pup metrics query \
  --query="avg:kafka.consumer.lag{topic:TOPIC_NAME} by {consumer_group}" --from=1h
```

### Consumer processing time

```bash
# If services log processing duration
pup logs search \
  --query="(process OR processing) AND (duration OR time OR elapsed) AND (kafka OR message)" \
  --from=1h --limit=20 --storage=flex
```

### SQS queue depth

```bash
# Number of messages waiting in SQS queues
pup metrics query \
  --query="avg:aws.sqs.approximate_number_of_messages_visible{*} by {queuename}" --from=1h

# Messages in flight (being processed)
pup metrics query \
  --query="avg:aws.sqs.approximate_number_of_messages_not_visible{*} by {queuename}" --from=1h

# Age of oldest message (indicates stuck consumers)
pup metrics query \
  --query="max:aws.sqs.approximate_age_of_oldest_message{*} by {queuename}" --from=1h
```

---

## Throughput & Metrics

### Kafka throughput

```bash
# Producer message rate
pup metrics query \
  --query="sum:kafka.producer.record_send_total{*} by {service}" --from=1h

# Consumer message rate
pup metrics query \
  --query="sum:kafka.consumer.records_consumed_total{*} by {service,topic}" --from=1h

# Bytes in/out
pup metrics query \
  --query="sum:kafka.producer.byte_total{*} by {topic}" --from=1h
```

### SNS/SQS throughput

```bash
# SNS messages published
pup metrics query \
  --query="sum:aws.sns.number_of_messages_published{*} by {topicname}" --from=1h

# SQS messages sent
pup metrics query \
  --query="sum:aws.sqs.number_of_messages_sent{*} by {queuename}" --from=1h

# SQS messages received
pup metrics query \
  --query="sum:aws.sqs.number_of_messages_received{*} by {queuename}" --from=1h
```

---

## APM Service Dependencies

Datadog APM traces can reveal asynchronous dependencies between services that aren't visible from synchronous HTTP calls alone.

```bash
# List all services (look for messaging-related ones)
pup apm services list --env=prod

# Get service stats (throughput, errors, latency)
pup apm services stats --env=prod

# Search for error traces involving messaging
pup logs search \
  --query="status:error AND service:SERVICE_NAME AND (kafka OR sqs OR sns OR rabbitmq)" \
  --from=1h --limit=10 --storage=flex
```

---

## Cross-Platform Queries

### All messaging activity for a specific service

```bash
# Everything a service does related to messaging
pup logs search \
  --query="service:SERVICE_NAME AND (kafka OR sqs OR sns OR rabbitmq OR amqp OR topic OR queue)" \
  --from=1h --limit=30 --storage=flex

# Aggregate by message type/platform
pup logs aggregate \
  --query="service:SERVICE_NAME AND (kafka OR sqs OR sns OR rabbitmq)" \
  --from=24h --compute="count" --group-by="@messaging.system" --storage=flex
```

### All messaging errors in the last hour

```bash
pup logs aggregate \
  --query="status:error AND (kafka OR sqs OR sns OR rabbitmq OR amqp OR message OR consumer OR producer)" \
  --from=1h --compute="count" --group-by="service" --storage=flex
```

### Discover messaging patterns you didn't know about

Sometimes services use messaging without obvious keywords. Cast a wider net:

```bash
# Look for async/event patterns
pup logs search \
  --query="(event.published OR event.consumed OR message.sent OR message.received)" \
  --from=1h --limit=30 --storage=flex

# Look for common message broker ports in connection logs
pup logs search \
  --query="(9092 OR 5672 OR 61616)" \
  --from=1h --limit=20 --storage=flex
```

---

## Tips

1. **Start with aggregations**: Use `pup logs aggregate` with `--group-by="service"` to get the big picture before drilling into individual logs with `pup logs search`.
2. **Expand time ranges carefully**: Start with `--from=1h`, then `--from=24h`, then `--from=7d`. Larger ranges are slower and may hit rate limits.
3. **Combine with code search**: If Datadog shows a service actively producing to a topic but GitHub code search found nothing, the messaging may be wired via infrastructure (e.g., EventBridge rule, Lambda trigger) rather than application code.
4. **Check for custom attributes**: Services may log topic names, queue names, or consumer groups as custom attributes (e.g., `@topic`, `@queue_name`, `@consumer_group`). Try `--group-by="@topic"` or `--group-by="@queue_name"`.
5. **APM duration is in nanoseconds**: If checking trace durations, remember 1ms = 1,000,000ns and 1s = 1,000,000,000ns.
