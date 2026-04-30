# Real-World Example: OrderPlacement API

Source: `checkout/orderplacementapi` PR #1964 — publisher-only migration (no subscribers).

This service publishes `OrderPlaced`, `OrderReserved`, and `CustomerConsentGiven` messages to per-tenant SNS topics. It had a custom `IMessagePublisherFactory` that built a per-tenant `JustSayingStackFluently` stack on first use.

---

## Before (JustSayingStack)

**`JustSayingExtensions.cs` (old registration)**
```csharp
public static IServiceCollection AddJustSayingPublisher(this IServiceCollection services)
{
    services.AddSingleton<IMessageSerializationFactory, SystemTextJsonSerializationFactory>();
    services.AddSingleton<IMessageMonitor, StatsDMessageMonitor>();
    services.AddSingleton<IMessagePublisherFactory, MessagePublisherFactory>();
    services.AddSingleton<IAwsClientFactory, AwsClientFactory>();
    services.AddSingleton<IAwsClientFactoryProxy, Messaging.AwsClientFactoryProxy>();
    return services;
}
```

**`MessagePublisherFactory.cs` (old — built a stack per tenant on first use)**
```csharp
public class MessagePublisherFactory(
    IAwsClientFactoryProxy awsClientFactoryProxy,
    ILoggerFactory loggerFactory,
    IMessageMonitor messageMonitor,
    IMessageSerializationFactory serializationFactory,
    IOrderPlacementApiConfigurationFactory configurationFactory) : IMessagePublisherFactory
{
    private readonly Dictionary<string, IMessagePublisher> _cache = new();

    public async Task<IMessagePublisher> GetOrSet(string tenant)
    {
        var region = AppSettings.GetRegion(tenant);
        if (!_cache.TryGetValue(region, out var cache))
        {
            var settings = configurationFactory.GetAppSettings(tenant);
            var stack = GetJustSayingStack(settings, region);

            stack.CreatePublishers();
            stack.WithMessageSerialisationFactory(serializationFactory);

            var supportedTenants = settings.SupportedTenants;
            var result = stack
                .AddTopicPublisherForTenants<OrderPlaced>(supportedTenants)
                .AddTopicPublisherForTenants<OrderReserved>(supportedTenants)
                .AddTopicPublisherForTenants<CustomerConsentGiven>(supportedTenants);

            _cache.Add(region, result);
            await result.StartAsync(CancellationToken.None);
            return result;
        }
        return cache;
    }

    private JustSayingStackFluently GetJustSayingStack(AppSettings settings, string region) =>
        (JustSayingStackFluently)JustSayingStackFluently.Configure(stack => { ... });
}
```

**Custom serializer classes (old — `SystemTextJsonSerializationFactory` + `SystemTextJsonSerializer`)**

Implemented `IMessageSerializationFactory` / `IMessageSerializer` from JustSayingStack to use `System.Text.Json` instead of Newtonsoft. Both are redundant in v7.4.0 — delete them.

---

## After (JustSaying v7.4.0)

**`Startup.cs` — `ConfigureServices` (new `AddJustSaying` block)**
```csharp
services.AddJustSaying(config =>
{
    var appConfig = Configuration.GetSection("AppSettings").Get<AppSettings>();

    config.Client(client =>
    {
        if (Environment.GetEnvironmentVariable("AWS_ENDPOINT_URL") is not null)
        {
            client.WithServiceUri(new Uri(Environment.GetEnvironmentVariable("AWS_ENDPOINT_URL")));
        }
    });

    config.Messaging(x =>
    {
        x.WithPublishFailureReattempts(appConfig.GetJustSayingOptions().PublishFailureReAttempts);
        x.WithPublishFailureBackoff(new TimeSpan(10 * 1000 * appConfig.GetJustSayingOptions().PublishFailureBackoffMilliseconds));
        x.WithRegion(appConfig.GetRegion());
        x.WithTopicNamingConvention(new DefaultNamingConventions());
    });

    config.Publications(x =>
    {
        x.WithTopic<OrderPlaced>(topic =>
            topic.WithTopicName(msg => $"{msg.Tenant}-{appConfig.Environment}-orderplaced"));
        x.WithTopic<OrderReserved>(topic =>
            topic.WithTopicName(msg => $"{msg.Tenant}-{appConfig.Environment}-orderreserved"));
        x.WithTopic<CustomerConsentGiven>(topic =>
            topic.WithTopicName(msg => $"{msg.Tenant}-{appConfig.Environment}-customerconsentgiven"));
    });
});

services.AddHostedService<JustSayingBackgroundService>();
```

> Note: `AddJustSaying` is called directly in `Startup.ConfigureServices` here rather than in a dedicated extension method. Both approaches work — the extension method approach in the main SKILL.md is cleaner for larger services.

**`JustSayingBackgroundService.cs` (new)**
```csharp
public class JustSayingBackgroundService(IMessagingBus bus, IMessagePublisher publisher) : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        await publisher.StartAsync(stoppingToken);
        await bus.StartAsync(stoppingToken);
    }
}
```

**`MessagePublisherFactory.cs` (simplified — delegates to DI-provided `IMessagePublisher`)**

After migration, the per-tenant caching logic is no longer needed — JustSaying v7.4.0 routes to the correct topic at publish time via the `msg.Tenant` lambda. The factory simplifies to:

```csharp
public class MessagePublisherFactory(
    IAwsClientFactoryProxy awsClientFactoryProxy,
    ILoggerFactory loggerFactory,
    IMessageMonitor messageMonitor,
    IMessagePublisher messagePublisher,       // injected by JustSaying DI
    IOrderPlacementApiConfigurationFactory configurationFactory) : IMessagePublisherFactory
{
    public async Task<IMessagePublisher> GetOrSet(string tenant)
    {
        return messagePublisher;  // single publisher handles all tenants via dynamic topic name
    }
}
```

> If your service has a similar per-tenant publisher factory, you can simplify it the same way rather than refactoring all call sites immediately.

**`JustSayingExtensions.cs` (after)**
```csharp
public static IServiceCollection AddJustSayingPublisher(this IServiceCollection services)
{
    services.AddSingleton<IAwsClientFactory, AwsClientFactory>();
    services.AddSingleton<IAwsClientFactoryProxy, Messaging.AwsClientFactoryProxy>();
    services.AddSingleton<IMessageMonitor, StatsDMessageMonitor>();
    return services;
}
```

`IMessageSerializationFactory` and `IMessagePublisherFactory` registrations are removed here. `IMessagePublisherFactory` moves to `IServiceCollectionExtensions.AddDomainServices()` as a scoped registration:
```csharp
services.AddScoped<IMessagePublisherFactory, MessagePublisherFactory>();
```

**`.csproj` changes**
```xml
<!-- ADD -->
<PackageReference Include="JustSaying.Extensions.DependencyInjection.Microsoft" />
<PackageReference Include="JustSayingStack.Monitoring.StatsD" />

<!-- REMOVE (once migration complete — was kept during this transitional PR) -->
<PackageReference Include="JustSayingStack" />
```

**Custom serializer classes — delete both:**
- `SystemTextJsonSerializationFactory.cs`
- `SystemTextJsonSerializer.cs`

JustSaying v7.4.0 uses `System.Text.Json` by default. Custom `IMessageSerializationFactory` / `IMessageSerializer` implementations are no longer needed and will not compile (the interfaces were renamed in v7.x).

---

## Key Differences vs Generic Pattern

| Aspect | Generic (SKILL.md) | OrderPlacement actual |
|--------|--------------------|-----------------------|
| `AddJustSaying` location | Dedicated `AddMessaging()` extension | Inline in `Startup.ConfigureServices` |
| `IConfiguration` access | Parameter on extension method | `Configuration` field on `Startup` |
| Per-tenant factory | Not applicable | Kept `IMessagePublisherFactory`, simplified to return `IMessagePublisher` |
| Custom serializer | Not mentioned | Deleted — v7.4.0 uses STJ by default |
| `IMessagePublisherFactory` scope | N/A | Moved from singleton to scoped |
