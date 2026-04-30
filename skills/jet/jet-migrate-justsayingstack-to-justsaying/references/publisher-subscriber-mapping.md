# Publisher and Subscriber Mapping Reference

Complete old-to-new translation patterns for `config.Publications` and `config.Subscriptions`.

All examples assume:
- `env` = `appSettings.Environment`
- `component` = `appSettings.Feature` (or whatever the component/feature name field is)

---

## Table of Contents

1. [Publisher Patterns](#publisher-patterns)
   - [All-tenant publisher](#all-tenant-publisher)
   - [Per-tenant publisher](#per-tenant-publisher)
2. [Subscriber Patterns](#subscriber-patterns)
   - [Topic subscriber (SNS fan-out → SQS)](#topic-subscriber-addtopicsubscriberfortenants)
   - [Queue subscriber (direct queue)](#queue-subscriber-addqueuesubscriberfortenants)
3. [SqsReadConfiguration Mapping](#sqsreadconfiguration-mapping)

---

## Publisher Patterns

### All-tenant publisher

**Old (`AddTopicPublisherForAllTenant<T>`):**
```csharp
_publisherRegistration.AddTopicPublisherForAllTenant<SuccessfullyConnectedToCustomer>();
```

**New (`WithTopic<T>` with static all-tenant name):**
```csharp
config.Publications(x =>
    x.WithTopic<SuccessfullyConnectedToCustomer>(topic =>
        topic.WithTopicName($"all-{env}-successfullyconnectedtocustomer")));
```

The topic name follows `JustEatNamingStrategyFactory`: `all-{env}-{typename.ToLower()}`.

---

### Per-tenant publisher

**Old (`AddTopicPublisherForTenants<T>`):**
```csharp
_publisherRegistration.AddTopicPublisherForTenants<TakeawayOrderEventError>(takeawayTenants);
```

**New (`WithTopic<T>` with dynamic name from message):**
```csharp
config.Publications(x =>
    x.WithTopic<TakeawayOrderEventError>(topic =>
        topic.WithTopicName(msg => $"{msg.Tenant}-{env}-takeawayordereventerror")));
```

The `Tenant` property comes from `JustSaying.Models.Message`. It is set by the calling code before publishing:
```csharp
message.Tenant = tenantValue;
await _publisher.PublishAsync(message);
```

The `tenants` list from the old registration is NOT needed at configuration time — the tenant is determined per-publish from the message. Verify that all `PublishAsync` call sites in the service already set `Tenant` before publishing.

---

## Subscriber Patterns

### Topic subscriber (`AddTopicSubscriberForTenants`)

This pattern subscribes to SNS topics (SNS fan-out → SQS). One `ForTopic<T>` call per tenant.

**Old:**
```csharp
_subscriberRegistration
    .AddTopicSubscriberForTenants(_appSettings.SupportedTenants, DefaultSqsReadConfiguration)
    .WithHandler<OrderCreatedV2>(_handlerResolver);
```

**New (loop over tenants):**
```csharp
config.Subscriptions(x =>
{
    foreach (var tenant in appSettings.SupportedTenants)
    {
        x.ForTopic<OrderCreatedV2>(cfg =>
        {
            cfg.WithTopicName($"{tenant}-{env}-ordercreatedv2");
            cfg.WithQueueName($"{tenant}-{env}-{component}-ordercreatedv2");
            cfg.WithReadConfiguration(rc =>
            {
                rc.VisibilityTimeout = TimeSpan.FromSeconds(30);
                rc.MessageRetention = TimeSpan.FromMinutes(30);
            });
        });
    }
});
```

JustSaying creates one SQS polling loop per tenant. All tenants share the same `IHandlerAsync<T>` handler — JustSaying resolves it automatically from DI. If the handler has request-scoped dependencies, register it with `AddTransient` (not `AddSingleton`).

**Note on `WithTopicName`:** In v7.x, `TopicSubscriptionBuilder<T>.WithTopicName` takes a static `string`, not a lambda. The tenant name must be captured from the foreach loop variable — this is safe because the lambda captures by value in the loop body. If you are on a different major version, verify this signature in `api-reference.md` before proceeding.

---

### Queue subscriber (`AddQueueSubscriberForTenants`)

This pattern subscribes directly to an SQS queue (not fed by SNS). Use `ForQueue<T>` instead of `ForTopic<T>`.

**Old:**
```csharp
_subscriberRegistration
    .AddQueueSubscriberForTenants(new[] { "all" }, $"{env}-{feature}-daasdeliveryevent", DefaultSqsReadConfiguration)
    .WithHandler<DaasDeliveryEvent>(_handlerResolver);
```

**New (`ForQueue<T>`):**
```csharp
config.Subscriptions(x =>
    x.ForQueue<DaasDeliveryEvent>(cfg =>
    {
        cfg.WithQueueName($"all-{env}-{component}-daasdeliveryevent");
        cfg.WithReadConfiguration(rc =>
        {
            rc.VisibilityTimeout = TimeSpan.FromSeconds(30);
            rc.MessageRetention = TimeSpan.FromMinutes(30);
        });
    }));
```

The key distinction: `AddQueueSubscriberForTenants` → `ForQueue<T>`, `AddTopicSubscriberForTenants` → `ForTopic<T>`.

---

## SqsReadConfiguration Mapping

| Old `SqsReadConfiguration` property | New `WithReadConfiguration` property | Notes |
|--------------------------------------|---------------------------------------|-------|
| `sqsReadConfiguration.VisibilityTimeout` | `rc.VisibilityTimeout` | `TimeSpan` |
| `sqsReadConfiguration.MessageRetention` | `rc.MessageRetention` | `TimeSpan` |
| `sqsReadConfiguration.DeliveryDelay` | `rc.DeliveryDelay` | `TimeSpan`; see pitfalls.md re: IAM |

If a service defines a `DefaultSqsReadConfiguration` shared across all subscriptions, apply the same `WithReadConfiguration` values to every `ForTopic<T>` and `ForQueue<T>` call.

---

## Multiple Handlers for the Same Message Type

If the old registration has multiple `.WithHandler<T>()` calls for the same message type (on different subscriptions), each subscription gets its own queue and each queue uses the registered `IHandlerAsync<T>`. JustSaying's DI resolves all registered implementations — if multiple `IHandlerAsync<T>` are registered, they all run for each message.

If the old code used separate subscriber registrations for the same type on different queues for different purposes, create a separate `ForTopic<T>` or `ForQueue<T>` call for each queue, each with its own `WithQueueName`.
