# GitHub Search Patterns for Event-Driven Discovery

A comprehensive catalog of code patterns to search for when identifying message producers and consumers across different platforms and languages.

## MessageExchange (JET Internal)

**MessageExchange** is a dedicated repository on JET GitHub Enterprise where message specifications (event contracts, schemas, topic definitions) should be registered. In theory, this repo is the canonical place to discover which events exist, who produces them, and who consumes them. In practice, **MessageExchange is not fully reliable as a discovery source** -- not all teams register their events there, registrations may be outdated, and some events exist only in service code without a corresponding entry in MessageExchange. Use it as a supplementary signal alongside the platform-specific code search patterns below, not as the sole source of truth.

```bash
# Search within the MessageExchange repo for an event name
gh search code "EVENT_NAME" --hostname github.je-labs.com -R OWNER/MessageExchange -L 30
```

## Case Sensitivity

GitHub code search is **case-insensitive by default** for keyword queries. A search for `kafkatemplate` will match `KafkaTemplate`, `KAFKATEMPLATE`, and `kafkaTemplate`. This means:

- You do NOT need to search for multiple case variants of the same keyword.
- However, when searching for **topic/queue names** that may appear in different formats (PascalCase, kebab-case, snake_case), search for each variant separately since they are different strings (e.g., `order-created`, `order_created`, `OrderCreated`).
- When using `gh api /search/code` with query strings, the same case-insensitivity applies.
- When using local `grep`/`rg` on cloned repos, always use the `-i` flag for case-insensitive matching.

## Table of Contents
- [Kafka](#kafka)
- [AWS SNS](#aws-sns)
- [AWS SQS](#aws-sqs)
- [RabbitMQ](#rabbitmq)
- [Redpanda](#redpanda)
- [Infrastructure as Code](#infrastructure-as-code)
- [Schema Definitions](#schema-definitions)

---

## Kafka

### Java / Kotlin (Spring Kafka)

| Role | Search Pattern | Context |
|------|---------------|---------|
| Producer | `KafkaTemplate` | Spring Kafka producer injection |
| Producer | `@SendTo` | Spring annotation for sending to topic |
| Producer | `ProducerRecord` | Low-level Kafka producer API |
| Producer | `ProducerFactory` | Producer configuration |
| Consumer | `@KafkaListener` | Spring annotation for consuming |
| Consumer | `ConsumerFactory` | Consumer configuration |
| Consumer | `ConcurrentKafkaListenerContainerFactory` | Consumer container setup |
| Config | `spring.kafka.bootstrap-servers` | Spring Boot Kafka config |
| Config | `spring.kafka.producer.topic` | Topic name in config |
| Config | `spring.kafka.consumer.group-id` | Consumer group config |

```bash
# Find Spring Kafka producers
gh search code "KafkaTemplate" --hostname github.je-labs.com --filename "*.java" -L 30
gh search code "KafkaTemplate" --hostname github.je-labs.com --filename "*.kt" -L 30

# Find Spring Kafka consumers
gh search code "@KafkaListener" --hostname github.je-labs.com --filename "*.java" -L 30

# Find topic config in application.yml
gh search code "spring.kafka" --hostname github.je-labs.com --filename "application*.yml" -L 30
```

### .NET (Confluent.Kafka)

| Role | Search Pattern | Context |
|------|---------------|---------|
| Producer | `IProducer<` | Confluent producer interface |
| Producer | `ProduceAsync` | Async produce call |
| Producer | `ProducerBuilder` | Producer configuration |
| Consumer | `IConsumer<` | Confluent consumer interface |
| Consumer | `ConsumeResult` | Consume result handling |
| Consumer | `ConsumerBuilder` | Consumer configuration |
| Consumer | `Subscribe(` | Topic subscription |
| Config | `BootstrapServers` | Broker connection string |
| Config | `GroupId` | Consumer group |

```bash
# Find .NET Kafka producers
gh search code "IProducer" --hostname github.je-labs.com --filename "*.cs" -L 30
gh search code "ProduceAsync" --hostname github.je-labs.com --filename "*.cs" -L 30

# Find .NET Kafka consumers
gh search code "IConsumer" --hostname github.je-labs.com --filename "*.cs" -L 30
gh search code "ConsumeResult" --hostname github.je-labs.com --filename "*.cs" -L 30
```

### Python

| Role | Search Pattern | Context |
|------|---------------|---------|
| Producer | `confluent_kafka.Producer` | confluent-kafka-python |
| Producer | `KafkaProducer` | kafka-python |
| Producer | `AIOKafkaProducer` | aiokafka async producer |
| Producer | `produce(` | confluent-kafka produce call |
| Consumer | `confluent_kafka.Consumer` | confluent-kafka-python |
| Consumer | `KafkaConsumer` | kafka-python |
| Consumer | `AIOKafkaConsumer` | aiokafka async consumer |
| Consumer | `subscribe(` | Topic subscription |

```bash
gh search code "confluent_kafka" --hostname github.je-labs.com --filename "*.py" -L 30
gh search code "KafkaProducer" --hostname github.je-labs.com --filename "*.py" -L 30
gh search code "KafkaConsumer" --hostname github.je-labs.com --filename "*.py" -L 30
```

### Go

| Role | Search Pattern | Context |
|------|---------------|---------|
| Producer | `sarama.SyncProducer` | Sarama sync producer |
| Producer | `sarama.AsyncProducer` | Sarama async producer |
| Producer | `kafka.NewProducer` | confluent-kafka-go |
| Producer | `kafka.Writer` | segmentio/kafka-go |
| Consumer | `sarama.ConsumerGroup` | Sarama consumer group |
| Consumer | `kafka.NewConsumer` | confluent-kafka-go |
| Consumer | `kafka.NewReader` | segmentio/kafka-go |

```bash
gh search code "sarama" --hostname github.je-labs.com --filename "*.go" -L 30
gh search code "kafka.NewProducer" --hostname github.je-labs.com --filename "*.go" -L 30
gh search code "kafka.NewReader" --hostname github.je-labs.com --filename "*.go" -L 30
```

### Node.js / TypeScript

| Role | Search Pattern | Context |
|------|---------------|---------|
| Producer | `kafka.producer()` | KafkaJS producer |
| Producer | `producer.send(` | KafkaJS send |
| Consumer | `kafka.consumer(` | KafkaJS consumer |
| Consumer | `consumer.subscribe(` | KafkaJS subscribe |
| Consumer | `eachMessage` | KafkaJS message handler |
| Config | `kafkajs` | KafkaJS package |

```bash
gh search code "kafkajs" --hostname github.je-labs.com --filename "package.json" -L 30
gh search code "eachMessage" --hostname github.je-labs.com --filename "*.ts" -L 30
```

---

## AWS SNS

| Role | Search Pattern | Context |
|------|---------------|---------|
| Publisher | `sns.publish` | AWS SDK v2 publish |
| Publisher | `PublishCommand` | AWS SDK v3 publish |
| Publisher | `SNSClient` | AWS SDK v3 client |
| Publisher | `AmazonSNSClient` | Java SDK |
| Publisher | `TopicArn` | Topic ARN reference |
| Subscriber | `sns.subscribe` | Subscription creation |
| Subscriber | `SubscribeCommand` | SDK v3 subscription |
| IaC | `aws_sns_topic` | Terraform resource |
| IaC | `AWS::SNS::Topic` | CloudFormation resource |

```bash
# SNS publishers
gh search code "sns.publish" --hostname github.je-labs.com -L 30
gh search code "PublishCommand" --hostname github.je-labs.com -L 30
gh search code "AmazonSNSClient" --hostname github.je-labs.com --filename "*.java" -L 30

# SNS topic definitions
gh search code "aws_sns_topic" --hostname github.je-labs.com --filename "*.tf" -L 30
gh search code "AWS::SNS::Topic" --hostname github.je-labs.com --filename "*.yaml" -L 30
```

---

## AWS SQS

| Role | Search Pattern | Context |
|------|---------------|---------|
| Sender | `sqs.send_message` | Python SDK send |
| Sender | `SendMessageCommand` | SDK v3 send |
| Sender | `AmazonSQSClient` | Java SDK |
| Consumer | `sqs.receive_message` | Python SDK receive |
| Consumer | `ReceiveMessageCommand` | SDK v3 receive |
| Consumer | `SQSEvent` | Lambda SQS trigger |
| Consumer | `@SqsListener` | Spring Cloud AWS |
| IaC | `aws_sqs_queue` | Terraform resource |
| IaC | `AWS::SQS::Queue` | CloudFormation resource |
| DLQ | `dead_letter_queue` | Dead letter queue config |
| DLQ | `RedrivePolicy` | SQS redrive policy |

```bash
# SQS senders
gh search code "SendMessageCommand" --hostname github.je-labs.com -L 30
gh search code "sqs.send_message" --hostname github.je-labs.com -L 30

# SQS consumers
gh search code "ReceiveMessageCommand" --hostname github.je-labs.com -L 30
gh search code "SQSEvent" --hostname github.je-labs.com -L 30
gh search code "@SqsListener" --hostname github.je-labs.com --filename "*.java" -L 30

# SQS infrastructure
gh search code "aws_sqs_queue" --hostname github.je-labs.com --filename "*.tf" -L 30

# Dead letter queues
gh search code "RedrivePolicy" --hostname github.je-labs.com -L 30
gh search code "dead_letter" --hostname github.je-labs.com --filename "*.tf" -L 30
```

---

## RabbitMQ

| Role | Search Pattern | Context |
|------|---------------|---------|
| Producer | `RabbitTemplate` | Spring AMQP producer |
| Producer | `channel.basic_publish` | Python pika |
| Producer | `amqp.Publish` | Go amqp |
| Consumer | `@RabbitListener` | Spring AMQP listener |
| Consumer | `channel.basic_consume` | Python pika |
| Consumer | `channel.Consume` | Go amqp |
| Config | `amqp://` | Connection string |
| Config | `spring.rabbitmq` | Spring Boot config |
| Exchange | `ExchangeDeclare` | Exchange declaration |
| Exchange | `@Exchange` | Spring AMQP exchange annotation |
| Queue | `QueueDeclare` | Queue declaration |
| Binding | `QueueBind` | Queue to exchange binding |

```bash
# RabbitMQ producers
gh search code "RabbitTemplate" --hostname github.je-labs.com -L 30
gh search code "basic_publish" --hostname github.je-labs.com -L 30

# RabbitMQ consumers
gh search code "@RabbitListener" --hostname github.je-labs.com -L 30
gh search code "basic_consume" --hostname github.je-labs.com -L 30

# RabbitMQ config
gh search code "amqp://" --hostname github.je-labs.com --filename "*.yml" -L 30
gh search code "spring.rabbitmq" --hostname github.je-labs.com --filename "application*.yml" -L 30
```

---

## Redpanda

Redpanda is Kafka-compatible, so the same Kafka client patterns apply. Additionally search for Redpanda-specific configuration:

```bash
# Redpanda-specific config
gh search code "redpanda" --hostname github.je-labs.com --filename "*.yml" -L 30
gh search code "redpanda" --hostname github.je-labs.com --filename "*.yaml" -L 30
gh search code "rpk" --hostname github.je-labs.com --filename "Makefile" -L 20

# Redpanda Connect (Benthos)
gh search code "redpanda-connect" --hostname github.je-labs.com -L 20
gh search code "benthos" --hostname github.je-labs.com --filename "*.yml" -L 20
```

---

## Infrastructure as Code

### Terraform

```bash
# Kafka topics
gh search code "kafka_topic" --hostname github.je-labs.com --filename "*.tf" -L 30

# MSK (AWS Managed Kafka)
gh search code "aws_msk_cluster" --hostname github.je-labs.com --filename "*.tf" -L 30

# EventBridge (related to SNS/SQS)
gh search code "aws_cloudwatch_event_rule" --hostname github.je-labs.com --filename "*.tf" -L 30

# SNS + SQS subscriptions
gh search code "aws_sns_topic_subscription" --hostname github.je-labs.com --filename "*.tf" -L 30
```

### Helm Charts

```bash
# Kafka config in Helm values
gh search code "kafka" --hostname github.je-labs.com --filename "values.yaml" -L 30

# RabbitMQ config in Helm values
gh search code "rabbitmq" --hostname github.je-labs.com --filename "values.yaml" -L 30
```

---

## Schema Definitions

Search for event schemas (Avro, Protobuf, JSON Schema, AsyncAPI):

```bash
# Avro schemas
gh search code "" --hostname github.je-labs.com --filename "*.avsc" -L 30

# Protobuf message definitions
gh search code "message" --hostname github.je-labs.com --filename "*.proto" -L 30

# AsyncAPI specs (event contracts)
gh search code "asyncapi" --hostname github.je-labs.com --filename "*.yml" -L 30
gh search code "asyncapi" --hostname github.je-labs.com --filename "*.yaml" -L 30

# JSON Schema for events
gh search code "event" --hostname github.je-labs.com --filename "*.schema.json" -L 30
```

## Tips for Effective Searching

1. **Case-insensitive by default**: GitHub code search is case-insensitive for keywords, so `KafkaTemplate` and `kafkatemplate` return the same results. But topic names in different formats (e.g., `order-created` vs `OrderCreated`) are different strings -- search for each variant.
2. **Local grep must use -i**: When grepping through cloned repos locally, always use `rg -i` or `grep -i` to ensure case-insensitive matching.
3. **Start broad, then narrow**: Begin with platform-agnostic searches (e.g., topic name), then refine by language/framework.
4. **Check config files**: Topic and queue names are often in config rather than code. Search `*.yml`, `*.yaml`, `*.properties`, `*.env`.
5. **Follow the imports**: When you find a match, check the imports in the file to understand which messaging library is used.
6. **Check Terraform**: IaC definitions are the most reliable source of truth for what topics and queues actually exist in production.
7. **Rate limiting**: `gh search code` is rate-limited. If you get 403 errors, wait 30 seconds between requests. Prioritize the most likely patterns first.
