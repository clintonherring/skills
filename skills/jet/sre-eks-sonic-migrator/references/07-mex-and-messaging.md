# Message Exchange (MeX) & Messaging Migration

## When This Reference Is Needed

Load this file when the source repo analysis detects:

- SNS/SQS usage (topic ARNs, queue URLs, SQS client configuration)
- JustSaying or JustSayingStack dependencies
- Event-driven / messaging patterns (publishers, subscribers, handlers)

## Detection Patterns

### JustSaying (Manageable)

| Pattern                              | Files to Check                   |
| ------------------------------------ | -------------------------------- |
| `JustSaying` NuGet package           | `*.csproj`, `packages.config`    |
| `AddJustSaying()`                    | C# source files                  |
| `IMessagePublisher`, `IHandlerAsync` | C# source files                  |
| JustSaying v7+ configuration         | `appsettings.json`, startup code |

JustSaying v7+ is compatible with MeX. Proceed with MeX migration.

### JustSayingStack (BLOCKING)

| Pattern                                         | Files to Check               |
| ----------------------------------------------- | ---------------------------- |
| `JustSayingStack` NuGet package                 | `*.csproj`                   |
| `JustSayingStack` in code                       | C# source files              |
| CloudFormation SNS/SQS resources managed by JSS | Infrastructure-as-code files |

**JustSayingStack overwrites MeX IAM policies**, making coexistence impossible. Must migrate to JustSaying v7 first.

### Direct SNS/SQS SDK Usage

| Pattern                              | Files to Check         |
| ------------------------------------ | ---------------------- |
| `AmazonSNSClient`, `AmazonSQSClient` | Source code            |
| `AWSSDK.SNS`, `AWSSDK.SQS`           | Dependency files       |
| `boto3` SNS/SQS clients              | Python source          |
| SNS topic ARNs, SQS queue URLs       | Config files, env vars |

Direct SDK usage is compatible with MeX, but messaging resources must be declared in AsyncAPI specs.

## Blocker: JustSayingStack

Present to user:

> "Your service uses **JustSayingStack** for messaging. JustSayingStack manages SNS/SQS infrastructure in a way that conflicts with MeX (Message Exchange), which is required in Sonic Runtime. You need to migrate from JustSayingStack to JustSaying v7 before proceeding."
>
> **Options:**
>
> - **Pause migration**: Migrate to JustSaying v7 first, then resume
> - **Proceed without messaging**: Migrate the service but defer messaging (NOT recommended for production)

## MeX Migration Details

For the current MeX migration process, AsyncAPI spec format, and cross-account setup, fetch from Backstage:

```bash
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "$BACKSTAGE_BACKEND_URL/api/search/query?term=messaging+applications+migration+sonic+runtime&types%5B0%5D=techdocs" \
  | jq '.results[:3][] | {title: .document.title, text: .document.text[:500]}'
```

Key concepts (verify details from fetched docs):

- **Two phases**: Importing (low risk, observe only) → Live (full MeX management)
- **AsyncAPI specs**: Infrastructure-as-code for messaging resources
- **Cross-account**: SRE-EKS and Sonic Runtime are in different AWS accounts; MeX manages trust policies

## User-Friendly Summary

For services with messaging:

> "Your service uses messaging (SNS/SQS). In Sonic Runtime, messaging infrastructure is managed through **Message Exchange (MeX)**. This requires declaring your topics and queues in an AsyncAPI specification. MeX migration can happen in parallel with the platform migration."
