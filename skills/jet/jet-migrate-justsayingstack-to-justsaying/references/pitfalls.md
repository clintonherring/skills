# Common Pitfalls and Troubleshooting

---

## Pitfall 1: Missing `Tenant` property on published messages

When using `WithTopicName(msg => $"{msg.Tenant}-{env}-topicname")`, the `Tenant` property must be set on the message before calling `PublishAsync`. It comes from `JustSaying.Models.Message`.

```csharp
// Correct
message.Tenant = tenantValue;
await _publisher.PublishAsync(message);

// Wrong — Tenant will be null/empty, producing a malformed topic name
await _publisher.PublishAsync(message);
```

**Check:** Search all `PublishAsync` call sites and verify `Tenant` is set for per-tenant publishers:
```bash
grep -r "PublishAsync" src/ --include="*.cs"
```

---

## Pitfall 2: Multiple `ForTopic<T>` calls for the same message type

When subscribing per tenant (one call per tenant for the same `T`), JustSaying creates multiple SQS polling loops — one per queue. This is intentional and correct. All use the same `IHandlerAsync<T>` handler.

If the handler has request-scoped dependencies (e.g. `DbContext`), register it with `AddTransient` not `AddSingleton`, otherwise dependencies won't be fresh per message.

---

## Pitfall 3: DeliveryDelay on SQS queues needs IAM `SetQueueAttributes`

`DeliveryDelay` is a queue attribute set when the queue is created (by MeX). If JustSaying attempts to set it at startup via `SetQueueAttributes`, the IRSA role needs the `sqs:SetQueueAttributes` permission.

If the queue is already provisioned with the correct delay, the call is idempotent. If your IAM canned templates (`sns-crud.tftpl`, `sqs-crud.tftpl`) don't include `sqs:SetQueueAttributes`, either add it or use explicit ARNs to bypass queue creation/attribute calls at startup.

For self-referencing retry loops (publish to a topic, subscribe from a delayed queue), verify the MeX spec declares both the publication and the queue subscription.

---

## Pitfall 4: `StatsDMessageMonitor` comes from `JustSayingStack.Monitoring.StatsD`

Despite the name, `JustSayingStack.Monitoring.StatsD` does NOT depend on JustSayingStack. It only depends on `JustSaying` (for `IMessageMonitor`) and `JustEat.StatsD`. Always keep this package — do not confuse it with JustSayingStack.

```xml
<!-- KEEP this -->
<PackageReference Include="JustSayingStack.Monitoring.StatsD" Version="..." />

<!-- REMOVE this -->
<PackageReference Include="JustSayingStack" Version="..." />
```

---

## Pitfall 5: `HandlerResolver` implements `JustSaying.Fluent.IHandlerResolver`, not a JustSayingStack type

The custom `HandlerResolver` in JustSayingStack-based services implements `JustSaying.Fluent.IHandlerResolver` (from the plain JustSaying package). It is a JustSayingStack usage pattern but the interface itself comes from JustSaying.

Do not try to keep it — it is deleted entirely. JustSaying's DI extension resolves handlers automatically from the registered `IHandlerAsync<T>` services.

---

## Pitfall 6: Brighter/Kafka `IMessagePublisher` injection conflict

If the service uses both JustSaying (SNS/SQS) and Brighter (Kafka), there is no DI conflict:
- Brighter uses `IAmAMessagePublisher` (Paramore.Brighter)
- JustSaying uses `JustSaying.Messaging.IMessagePublisher`

These are different interfaces. If a Brighter handler injects `JustSaying.Messaging.IMessagePublisher` to re-publish messages on failure, it will resolve correctly — `AddJustSaying()` registers it.

---

## What Does NOT Change

| Component | Why unchanged |
|-----------|---------------|
| Message model classes (extending `JustSaying.Models.Message`) | Same base class in both libraries |
| Handler classes implementing `IHandlerAsync<T>` | Same interface in both libraries (`JustSaying.Messaging.MessageHandling`) |
| `IMessagePublisher.PublishAsync(message)` call sites | Same interface — `JustSaying.Messaging.IMessagePublisher` |
| `PublishAsync` extension methods | Built on `IMessagePublisher` — unchanged |
| `IMessageMonitor` / `StatsDMessageMonitor` usage | Same interface |
| `services.AddTransient<IHandlerAsync<T>, THandler>()` registrations | JustSaying resolves these automatically |

---

## Pitfall 7: Integration test DI setup missing `AddLogging()`

`AddJustSaying` registers services that resolve `ILogger<ServiceProviderResolver>` at container build time. In production, the ASP.NET Core host calls `services.AddLogging()` automatically before `Startup.ConfigureServices`. Integration tests that build their own bare `ServiceCollection` and call `startup.ConfigureServices(services)` directly will not have `ILogger<T>` registered.

**Symptom:**
```
System.InvalidOperationException: No service for type 'ILogger`1[JustSaying.ServiceProviderResolver]' has been registered.
```

**Fix:** Add `services.AddLogging()` to the test DI setup before calling `startup.ConfigureServices`:

```csharp
public IServiceProvider BuildServices()
{
    var services = new ServiceCollection();
    services.AddLogging();  // add this
    services.AddSingleton<IConfiguration>(_configuration);

    var startup = new Startup(new TestHostingEnvironment(), _configuration);
    startup.ConfigureServices(services);

    return services.BuildServiceProvider();
}
```

**How to find affected test setups:**
```bash
grep -r "new ServiceCollection\(\)" tests/ --include="*.cs" -l
```

Any file that builds a `ServiceCollection` and calls `startup.ConfigureServices` should have `AddLogging()` added.

---

## Build Error Reference

| Error message | Fix |
|---------------|-----|
| `'IServiceCollection' does not contain a definition for 'AddJustSaying'` | Add `JustSaying.Extensions.DependencyInjection.Microsoft` NuGet package |
| `The type or namespace 'JustSayingStack' could not be found` | Check .csproj; also search for remaining `using` statements importing JustSayingStack namespaces |
| `'IHandlerResolver' is defined in assembly 'JustSayingStack'` | Remove `IHandlerResolver`/`HandlerResolver` registration from `Startup.cs` |
| `cannot convert from 'lambda' to 'Action<...>'` | `WithTopicName` on `TopicSubscriptionBuilder` takes a `string`, not a lambda. Capture the tenant variable before calling |
| `ForQueue<T>` or `ForTopic<T>` not found | Wrong NuGet version or missing `using JustSaying.Fluent;` — check api-reference.md |
| `Ambiguous reference 'IHandlerAsync'` | Check for remaining `using` statements that import both JustSayingStack and JustSaying namespaces |
