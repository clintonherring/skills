# JustSaying v7.4.0 API Reference

Confirmed API surface verified on phonemaskingapi (WLVS-462, 2026-03-09) with v7.4.0 and DI extension v7.1.2. Build succeeds, 508/508 unit tests pass.

---

## `SubscriptionsBuilder` methods

```csharp
// Subscribe to SNS-backed topic → SQS queue (one call per tenant)
x.ForTopic<T>()
x.ForTopic<T>(Action<TopicSubscriptionBuilder<T>> configure)
x.ForTopic<T>(string topicNameOverride, Action<TopicSubscriptionBuilder<T>> configure)

// Subscribe to a direct SQS queue (no SNS)
x.ForQueue<T>()
x.ForQueue<T>(Action<QueueSubscriptionBuilder<T>> configure)

// Subscribe using explicit ARN or URL (cross-account / known ARN)
x.ForQueueArn(string queueArn, Action<QueueSubscriptionBuilder<T>> configure)
x.ForQueueUrl(string queueUrl, string regionName, Action<QueueSubscriptionBuilder<T>> configure)
```

---

## `TopicSubscriptionBuilder<T>` methods

```csharp
cfg.WithTopicName(string name)           // static string only — no lambda overload
cfg.WithQueueName(string name)
cfg.WithReadConfiguration(Action<SqsReadConfiguration> configure)
```

---

## `QueueSubscriptionBuilder<T>` methods

```csharp
cfg.WithQueueName(string name)
cfg.WithReadConfiguration(Action<SqsReadConfiguration> configure)
```

---

## `SqsReadConfiguration` properties

```csharp
rc.VisibilityTimeout   // TimeSpan
rc.MessageRetention    // TimeSpan
rc.DeliveryDelay       // TimeSpan
```

---

## `PublicationsBuilder` methods

```csharp
x.WithTopic<T>()
x.WithTopic<T>(Action<TopicPublicationBuilder<T>> configure)
```

---

## `TopicPublicationBuilder<T>` methods

```csharp
topic.WithTopicName(string name)                  // static name
topic.WithTopicName(Func<T, string> nameFactory)  // dynamic name using message at publish time
```

The dynamic overload is used for per-tenant publishing — the factory receives the message and returns the topic name based on `msg.Tenant`.

---

## `MessagingConfigBuilder` methods

```csharp
config.Client(Action<ClientConfig> configure)
config.Messaging(Action<MessagingConfig> configure)
config.Publications(Action<PublicationsBuilder> configure)
config.Subscriptions(Action<SubscriptionsBuilder> configure)
```

---

## `MessagingConfig` methods

```csharp
x.WithPublishFailureReattempts(int count)
x.WithPublishFailureBackoff(TimeSpan backoff)
x.WithRegion(string region)
// Do NOT call WithTopicNamingConvention — use explicit names in WithTopicName / WithQueueName
```

---

## Cross-account ARN patterns (if required by EDA Guild)

If topics/queues are in a different AWS account, the EDA Guild may require explicit ARNs read from configuration:

```csharp
// Publication with explicit ARN
x.WithTopic<T>(topic => topic.WithTopicArn("arn:aws:sns:eu-west-1:123456789012:tenant-env-topicname"));

// Subscription with explicit topic ARN (ForTopic variant)
x.ForTopic<T>(cfg => cfg.WithTopicArn("arn:aws:sns:..."));

// Subscription with explicit queue ARN
x.ForQueueArn("arn:aws:sqs:eu-west-1:123456789012:queue-name", cfg => { ... });
```

ARNs should come from configuration (e.g. `appSettings.Messaging.TopicArns`) populated from helmfile `state_values` per environment, not hardcoded.

---

## NuGet packages

| Package | Version | Purpose |
|---------|---------|---------|
| `JustSaying` | 7.4.0 | Core messaging library |
| `JustSaying.Extensions.DependencyInjection.Microsoft` | 7.1.2 | `services.AddJustSaying(...)` extension |
| `JustSayingStack.Monitoring.StatsD` | keep existing | `StatsDMessageMonitor` — does NOT depend on JustSayingStack |
