---
name: jet-migrate-justsayingstack-to-justsaying
description: "Migrate .NET 8+ services from JustSayingStack (the old fluent SNS/SQS wrapper library) to plain JustSaying with explicit DI configuration, as required by the Event Driven Architecture Guild for OneEKS / Sonic Runtime services. Use when a service has a JustSayingStack package reference, the user mentions JustSayingStack migration or SNS/SQS EDA guild requirements, or needs to replace JustSayingStackFluently with AddJustSaying. Also triggers on: migrating messaging configuration for OneEKS, rewriting MessagingExtensions, removing HandlerResolver boilerplate, or switching to JustSaying built-in DI handler resolution."
metadata:
  owner: ai-platform
---

# JustSayingStack → JustSaying Migration

The Event Driven Architecture Guild requires services on OneEKS / Sonic Runtime to use plain `JustSaying` with explicit DI configuration rather than the older `JustSayingStack` fluent wrapper. This skill walks through the migration end-to-end.

**What changes:** The IoC wiring — `JustSayingStackRegistration`, `JustSayingStackBackgroundService`, `HandlerResolver`, and the `AddMessaging()` extension method.

**What does NOT change:** Handler classes (`IHandlerAsync<T>`), message model classes, publisher call sites (`IMessagePublisher.PublishAsync`), and the `StatsDMessageMonitor` package.

**Related skills:**
- After migration, verify your MeX spec covers the messaging topology → use `messageexchange-asyncapi`
- For IAM canned policy gaps (SNS/SQS CreateTopic/CreateQueue permissions) → use `create-oneeks-service-account`

---

## Reference Files

| File | When to read |
|------|-------------|
| [publisher-subscriber-mapping.md](references/publisher-subscriber-mapping.md) | Step 2 — translating old fluent calls to new `config.Publications` / `config.Subscriptions` |
| [api-reference.md](references/api-reference.md) | Build errors or uncertainty about builder method signatures — documents the API surface for the version used in the reference migration |
| [pitfalls.md](references/pitfalls.md) | Unexpected errors, Brighter coexistence, StatsDMonitor, Tenant property issues |
| [real-world-example.md](references/real-world-example.md) | Complete before/after for `checkout/orderplacementapi` PR #1964 — publisher-only, per-tenant topics, custom serializer removal, simplified factory pattern |

---

## Step 0: Discovery Phase

Before touching any code, understand the service's complete messaging topology. This understanding drives every subsequent step — rushing past it leads to missed subscriptions and build failures.

### 0a. Confirm JustSayingStack is in use and record the JustSaying version

```bash
grep -r "JustSayingStack" src/ --include="*.csproj"
grep -r "JustSayingStackFluently" src/ --include="*.cs"
grep -r "IFluentStackPublisherRegistration\|IFluentStackSubscriberRegistration" src/ --include="*.cs"
```

Then record the transitive JustSaying versions that JustSayingStack is currently pulling in — you will need these exact versions in Step 4:

```bash
dotnet list src/{ServiceName}/{ServiceName}.csproj package --include-transitive | grep -i "JustSaying"
```

Expected output (versions will vary by project):

```
> JustSayingStack          8.x.x
  > JustSaying             7.x.x      (transitive)
  > JustSaying.Extensions.DependencyInjection.Microsoft  7.x.x  (transitive)
```

Note these versions down. JustSayingStack and JustSaying use **independent versioning schemes** — a JustSayingStack v8.x project may depend on JustSaying v7.x; an older JustSayingStack v6.x project may depend on JustSaying v5.x or v6.x with a different builder API surface.

### 0b. Find the registration file

Look for the file calling `JustSayingStackFluently.Configure(...)` — this is the single source of truth for messaging topology. It contains all publisher and subscriber registrations.

```bash
grep -r "JustSayingStackFluently" src/ --include="*.cs" -l
```

### 0c. Find the DI extension, background service, and HandlerResolver

```bash
# DI extension — the AddMessaging() method you'll rewrite
grep -r "JustSayingStackRegistration\|JustSayingStackBackgroundService" src/ --include="*.cs" -l

# HandlerResolver — implements IHandlerResolver, will be deleted
grep -r "IHandlerResolver" src/ --include="*.cs" -l
```

### 0d. Extract the messaging topology

From the registration file, build a complete picture of:

**Publishers:** Each `AddTopicPublisherForAllTenant<T>()` or `AddTopicPublisherForTenants<T>(tenants)` call.
- Note the message type and whether it's "all-tenant" or per-tenant.

**Subscribers:** Each `AddTopicSubscriberForTenants` or `AddQueueSubscriberForTenants` call.
- Note the message type, tenant list, and `SqsReadConfiguration` values (VisibilityTimeout, MessageRetention, DeliveryDelay).
- Distinguish `AddTopicSubscriberForTenants` (SNS fan-out → SQS) from `AddQueueSubscriberForTenants` (direct queue, no SNS).

### 0e. Understand naming

The `JustEatNamingStrategyFactory` generates names as:
- Topics: `{tenant}-{env}-{messageType.Name.ToLower()}`
- Queues: `{tenant}-{env}-{component}-{messageType.Name.ToLower()}`
- "all-tenant" topics: `all-{env}-{messageType.Name.ToLower()}`

Where `component` = `config.Component` (usually `AppSettings.Feature`).

Look for `config.NamingStrategyFactory = new JustEatNamingStrategyFactory()` to confirm this is the naming strategy in use. If the service uses a custom naming factory, extract its logic carefully — you'll need to replicate it inline.

### 0f. Find AppSettings bindings

```bash
grep -r "GetSection(\"AppSettings\")" src/ --include="*.cs" -l
```

Extract: `Environment`, `Region`, `SupportedTenants`, and the component/feature name. Also note any tenant-filtering extension methods (e.g. `FilterTakeawayTenants()`).

### 0g. Check for StatsDMessageMonitor

```bash
grep -r "StatsDMessageMonitor" src/ --include="*.cs"
```

If present, keep the `JustSayingStack.Monitoring.StatsD` NuGet package — it does NOT depend on JustSayingStack itself and provides the monitoring integration.

### 0h. Check for custom serializer classes

```bash
grep -r "IMessageSerializationFactory\|IMessageSerializer\|IMessageSerialisationFactory" src/ --include="*.cs" -l
```

Classes implementing these interfaces (typically `SystemTextJsonSerializationFactory` + `SystemTextJsonSerializer`) can be deleted — JustSaying v7+ uses System.Text.Json by default.

### 0i. Locate HandlerResolver tests

```bash
grep -r "HandlerResolver" tests/ --include="*.cs" -l
```

These will need to be deleted (they import JustSayingStack and cause build failures after migration).

### 0j. Cross-reference MeX spec (validates topic/queue names)

The MessageExchange spec is the source of truth for deployed SNS topics and SQS queues. Fetch it to validate the names you inferred from code in Step 0d/0e.

The spec lives in the `messaging-integrations/messageexchange` repository on GHE (`github.je-labs.com`):

```bash
# Search for the service's MeX spec
gh api --hostname github.je-labs.com \
  repos/messaging-integrations/messageexchange/contents/spec/services \
  --jq '.[].name' | grep -i {servicename}

# Fetch the spec (replace {filename} with the match)
gh api --hostname github.je-labs.com \
  repos/messaging-integrations/messageexchange/contents/spec/services/{filename} \
  --jq '.content' | base64 -d
```

**What to validate:**
1. Every publisher's SNS topic name matches a `channels.*.bindings.sns.name` entry with `action: send`
2. Every subscriber's SQS queue name matches a `operations.*.bindings.sqs.queues[].name` entry with `action: receive`
3. For queue subscribers where MeX manages the SNS→SQS subscription (look for `sns.consumers` in the operation), confirm `ForQueue<T>` is correct — JustSaying polls the queue; MeX manages the subscription

**Flag gaps:**
- Subscriptions/publishers in code but missing from MeX → spec update needed (use `messageexchange-asyncapi` skill)
- If no spec exists → the service needs one created before OneEKS deployment

### 0k. Check cps/projects workload for IAM permissions

The `cps/projects` repository on GHE defines IRSA (IAM Roles for Service Accounts) workloads. Verify the service has adequate SNS/SQS permissions for the new JustSaying configuration.

```bash
# Search for the service in cps/projects
gh api --hostname github.je-labs.com \
  '/search/code?q={servicename}+repo:cps/projects' \
  --jq '.items[].path'

# Fetch the workload file
gh api --hostname github.je-labs.com \
  repos/cps/projects/contents/workloads/pdv/{project-name}.yml \
  --jq '.content' | base64 -d
```

**What to validate:**
1. `canned_policy_resources` or `permission_template` includes ARNs for **all** SNS topics the service publishes to
2. `canned_policy_resources` or `permission_template` includes ARNs for **all** SQS queues the service subscribes to
3. If any subscriber uses `DeliveryDelay`, verify the SQS canned policy includes `sqs:SetQueueAttributes` (canned policies include this by default, but confirm)
4. Cross-account access: both `${AccountId}` and `${RefArchAccountId}` ARNs are present for every resource

**If no workload exists:** The service needs a workload created before OneEKS deployment → use the `create-oneeks-service-account` skill.

---

## Step 1: Create `JustSayingBackgroundService.cs`

Create this in a `Services/` folder or alongside the old background service file.

```csharp
using System.Threading;
using System.Threading.Tasks;
using JustSaying;
using JustSaying.Messaging;
using Microsoft.Extensions.Hosting;

namespace {Service.Namespace}.Services;

public class JustSayingBackgroundService(
    IMessagingBus bus,
    IMessagePublisher publisher) : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        await publisher.StartAsync(stoppingToken);
        await bus.StartAsync(stoppingToken);
    }
}
```

Start both `publisher` and `bus` even if the service is publish-only — `bus.StartAsync()` is a no-op when there are no subscriptions.

---

## Step 2: Rewrite the Messaging DI Extension

Replace the body of `AddMessaging()` with `services.AddJustSaying(config => {...})`. Add an `IConfiguration configuration` parameter — `IOptions<AppSettings>` is not resolvable at container construction time, so read config directly.

```csharp
public static IServiceCollection AddMessaging(
    this IServiceCollection services,
    IConfiguration configuration)
{
    services.AddSingleton<IMessageMonitor, StatsDMessageMonitor>(); // keep if present

    var appSettings = configuration.GetSection("AppSettings").Get<AppSettings>();
    var env = appSettings.Environment;
    var component = appSettings.Feature; // or whatever the component name field is

    services.AddJustSaying(config =>
    {
        config.Client(client =>
        {
            // LocalStack support for local development
            var endpointUrl = Environment.GetEnvironmentVariable("AWS_ENDPOINT_URL");
            if (endpointUrl is not null)
                client.WithServiceUri(new Uri(endpointUrl));
        });

        config.Messaging(x =>
        {
            x.WithPublishFailureReattempts(3);   // use original value
            x.WithPublishFailureBackoff(TimeSpan.FromSeconds(1));  // use original value
            x.WithRegion(appSettings.Region);
            // Do NOT call WithTopicNamingConvention — use explicit names instead
        });

        config.Publications(x =>
        {
            // See references/publisher-subscriber-mapping.md for patterns
        });

        config.Subscriptions(x =>
        {
            // See references/publisher-subscriber-mapping.md for patterns
        });
    });

    return services;
}
```

For the exact translation of each `AddTopicPublisherForAllTenant`, `AddTopicPublisherForTenants`, `AddTopicSubscriberForTenants`, and `AddQueueSubscriberForTenants` call, read **[publisher-subscriber-mapping.md](references/publisher-subscriber-mapping.md)**.

---

## Step 3: Update `Startup.cs`

```diff
-services.AddMessaging();
-services.AddSingleton<IHandlerResolver, HandlerResolver>();
+services.AddMessaging(_configuration);
 services.AddTransient<IHandlerAsync<OrderCreatedV2>, OrderCreatedV2Handler>();
 // ... keep all IHandlerAsync<T> registrations unchanged ...
+services.AddHostedService<JustSayingBackgroundService>();
-services.AddHostedService<JustSayingStackBackgroundService>(); // if registered here
```

JustSaying's DI extension resolves `IHandlerAsync<T>` handlers automatically — no custom `IHandlerResolver` needed.

Also remove any `using` statements that import `JustSayingStack` namespaces.

---

## Step 4: Update the `.csproj`

```xml
<!-- REMOVE -->
<PackageReference Include="JustSayingStack" Version="..." />

<!-- KEEP (does not depend on JustSayingStack) -->
<PackageReference Include="JustSayingStack.Monitoring.StatsD" Version="..." />

<!-- ADD if not already a direct reference — use the versions recorded in Step 0a -->
<PackageReference Include="JustSaying" Version="{version from Step 0a}" />
<PackageReference Include="JustSaying.Extensions.DependencyInjection.Microsoft" Version="{version from Step 0a}" />
```

**Do not change the JustSaying version as part of this migration.** Promote the exact transitive versions to direct dependencies — nothing more. If the project already has `JustSaying` or `JustSaying.Extensions.DependencyInjection.Microsoft` as direct references, verify they match the transitive versions and leave them unchanged.

Upgrading to a newer JustSaying major version is a separate concern: the builder API surface (`ForTopic<T>`, `ForQueue<T>`, `WithTopicName` overloads, etc.) differs between major versions. If you do need to upgrade, read **[api-reference.md](references/api-reference.md)** first — it documents the confirmed API surface for the version used in the reference migration.

> **If the discovered major version is not v7**, stop before writing any `AddJustSaying` configuration and read **[api-reference.md](references/api-reference.md)** — the builder API in this skill (Steps 2–4) was written for v7.x. Proceeding without checking will produce build errors on a different major version.

---

## Step 5: Delete Old JustSayingStack Files

Delete all three from the JustSayingStack IoC directory:
- The registration file (`JustSayingStackRegistration.cs` or equivalent)
- The background service file (`JustSayingStackBackgroundService.cs` or equivalent)
- The `HandlerResolver.cs`

If deleting these empties the directory, delete the directory too.

Then delete the HandlerResolver test file from the test project (found in Step 0i). If that empties its parent directory, delete it too.

**Also delete custom serializer classes if present:**

```bash
grep -r "IMessageSerializationFactory\|IMessageSerializer\|IMessageSerialisationFactory\|IMessageSerialiser" src/ --include="*.cs" -l
```

Any classes implementing these interfaces (typically `SystemTextJsonSerializationFactory.cs` and `SystemTextJsonSerializer.cs`) should be deleted. JustSaying v7+ uses `System.Text.Json` by default — custom serialization factories are no longer needed and the old interfaces do not exist in v7.x.

---

## Step 6: Verify Build

```bash
dotnet build src/{ServiceName}/{ServiceName}.csproj
```

**Common errors and fixes:**

| Error | Fix |
|-------|-----|
| `'IServiceCollection' does not contain a definition for 'AddJustSaying'` | Add `JustSaying.Extensions.DependencyInjection.Microsoft` NuGet package |
| `The type or namespace 'JustSayingStack' could not be found` | Check .csproj removal; search for remaining `using` statements importing JustSayingStack namespaces |
| `'IHandlerResolver' is defined in assembly 'JustSayingStack'` | Remove `HandlerResolver` registration from `Startup.cs` |
| `cannot convert from 'lambda' to 'Action<...>'` | Check `WithTopicName` / `WithQueueName` lambda signatures — see [api-reference.md](references/api-reference.md) |
| `ForQueue<T>` or `ForTopic<T>` not found | Verify the JustSaying version matches what was recorded in Step 0a; also check for missing `using JustSaying.Fluent;` — see [api-reference.md](references/api-reference.md) |

For deeper troubleshooting, read **[pitfalls.md](references/pitfalls.md)**.

Then run **all** test suites that can be executed locally:

```bash
# Unit tests — always run
dotnet test tests/{ServiceName}.Tests/{ServiceName}.Tests.csproj

# Integration tests — run if they exist and have a local/CI-only mode
# Check for test projects matching *IntegrationTests*, *Functional.Tests*, etc.
find tests/ -name "*.csproj" | grep -v "EndToEnd"
```

**Integration test DI setup — check for missing `AddLogging()`:**

If the service has integration tests that build their own `ServiceCollection` (common pattern: a `TestConfiguration` class that calls `startup.ConfigureServices(services)`), verify it calls `services.AddLogging()` before configuring the app. `AddJustSaying` resolves `ILogger<ServiceProviderResolver>` at container build time. In production the ASP.NET Core host registers this automatically, but bare `ServiceCollection` setups do not.

```csharp
public IServiceProvider BuildServices()
{
    var services = new ServiceCollection();
    services.AddLogging();  // required for AddJustSaying — add if missing
    services.AddSingleton<IConfiguration>(_configuration);

    var startup = new Startup(new TestHostingEnvironment(), _configuration);
    startup.ConfigureServices(services);

    return services.BuildServiceProvider();
}
```

The symptom of a missing `AddLogging()` call is:
```
System.InvalidOperationException: No service for type 'ILogger`1[JustSaying.ServiceProviderResolver]' has been registered.
```

---

## Completion Checklist

- [ ] `JustSayingStack` package reference removed from `.csproj`
- [ ] `JustSayingStack.Monitoring.StatsD` package reference kept
- [ ] `JustSayingBackgroundService.cs` created (starts both `IMessagingBus` and `IMessagePublisher`)
- [ ] `MessagingExtensions.cs` rewritten with `services.AddJustSaying(config => {...})`
- [ ] All publishers mapped with correct topic names
- [ ] All subscribers mapped with correct queue names and SQS config
- [ ] `IHandlerResolver` registration removed from Startup
- [ ] All `IHandlerAsync<T>` handler registrations kept
- [ ] `services.AddHostedService<JustSayingBackgroundService>()` added
- [ ] Old registration, background service, and HandlerResolver files deleted
- [ ] Custom serializer classes deleted (`SystemTextJsonSerializationFactory`, `SystemTextJsonSerializer` or equivalent)
- [ ] `HandlerResolverTests.cs` (or equivalent) deleted from test project
- [ ] Integration test `TestConfiguration` (or equivalent) checked for `services.AddLogging()`
- [ ] `dotnet build` passes
- [ ] `dotnet test` passes (unit tests)
- [ ] Integration/functional tests pass (or confirmed skipped with justification)
- [ ] MeX spec cross-referenced — all topic/queue names validated against `messaging-integrations/messageexchange`
- [ ] MeX spec gaps flagged — any subscriptions/publishers missing from spec documented for follow-up (use `messageexchange-asyncapi` skill)
- [ ] cps/projects workload verified — IAM `canned_policy_resources` covers all SNS topics and SQS queues
- [ ] IAM canned policy gaps identified (use `create-oneeks-service-account` skill if workload missing or incomplete)
