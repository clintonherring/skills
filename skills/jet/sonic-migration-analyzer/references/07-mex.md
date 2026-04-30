# Message Exchange (MeX)

## Overview

**Message Exchange (MeX)** is the centralized platform for managing SNS/SQS/Kafka messaging infrastructure at JET. All SNS/SQS resources **MUST** be configured and managed through MeX when migrating to Sonic Runtime.

**Repository:** `git@github.je-labs.com:messaging-integrations/MessageExchange.git`

## Why MeX is Required

1. **Centralized Management** - Single source of truth for messaging infrastructure
2. **Cross-Account Policies** - Automatically manages IAM trust policies
3. **AsyncAPI Specs** - Infrastructure as code with versioning
4. **Policy Protection** - Prevents overwrites from application code
5. **Governance** - Standardized messaging patterns across platforms

## Two-Phase Migration Process

MeX uses a two-phase approach to enable safe migrations:

### Phase 1: Importing Status

**Purpose:** Import existing resources WITHOUT modifying policies

**Characteristics:**
- MeX imports resource configuration
- NO policy changes applied
- Resources continue working as before
- Validation and testing phase

**AsyncAPI Configuration:**
```yaml
bindings:
  messageexchange:
    status: importing  # Phase 1: No policy changes
    environments:
      - euw1-pdv-qa-3
```

**Use When:**
- Initial MeX onboarding
- Testing AsyncAPI configuration
- Validating resource imports
- No service disruption risk

### Phase 2: Live Status

**Purpose:** Enable full MeX features and apply policies

**Characteristics:**
- MeX applies resource-based policies
- Cross-account trusts configured
- Full MeX capabilities enabled
- Policies may overwrite existing configuration

**AsyncAPI Configuration:**
```yaml
bindings:
  messageexchange:
    status: live  # Phase 2: MeX manages policies
    environments:
      - euw1-pdv-qa-3
```

**Use After:**
- Successfully validated `importing` status
- Coordinated with all producers/consumers
- Verified no `JustSayingStack` usage (would overwrite)

## Critical: JustSayingStack Conflict

**Problem:** `JustSayingStack` overwrites MeX-managed policies.

**Indicators:**
- `.CreatePublishers()` calls in code
- `.AddQueueSubscriberForTenants()` or `.AddQueuePublisherForAllTenant()` calls
- Direct SNS/SQS resource creation in application

**Required Migration:**
1. Migrate from `JustSayingStack` to `JustSaying` v7
2. Configure JustSaying in infraless mode
3. Remove all SNS/SQS modification calls
4. Replace with `.WithTopicArn()` and `.WithQueueArn()` (read-only)

**Example - Before (JustSayingStack):**
```csharp
builder.Services.AddJustSaying(config => {
    config.CreatePublishers("OrderCreated");  // ❌ Modifies SNS
});
```

**Example - After (JustSaying v7 Infraless):**
```csharp
builder.Services.AddJustSaying(config => {
    config.WithTopicArn("arn:aws:sns:...:OrderCreated");  // ✅ Read-only
});
```

## MeX Migration Steps

### 1. Identify Dependencies

**Find All Producers:**
- Search codebase for SNS publish operations
- Check AsyncAPI specs in MeX repository
- Use [Marmot documentation platform](https://marmot.pl-data-mi.pdv-3.eu-west-1.qa.jet-internal.com/)

**Find All Consumers:**
- Search for SQS polling/subscription code
- Identify all teams sharing resources
- Map message flow diagrams

**Coordination Required:**
- If resources shared across teams, synchronize migration
- Notify co-publishers/consumers before policy changes
- Plan migration windows to avoid blockers

### 2. Check Existing MeX Status

**Search MeX Repository:**
```bash
cd MessageExchange
grep -r "OrderCreated" specs/
```

**Check Marmot:**
- Visit [Marmot](https://marmot.pl-data-mi.pdv-3.eu-west-1.qa.jet-internal.com/)
- Search for message name
- Check if marked as documentation (not migrated) or live (migrated)

### 3. Migrate JustSayingStack (if applicable)

**Steps:**
1. Upgrade to JustSaying v7
2. Remove `JustSayingStack` dependency
3. Replace `.CreatePublishers()` with `.WithTopicArn()`
4. Replace `.AddQueueSubscriber*()` with `.WithQueueArn()`
5. Test in non-production environment
6. Deploy to production before MeX `live` status

### 4. Create AsyncAPI Spec in MeX

**File Location:** `MessageExchange/specs/{team}/{service}/asyncapi.yaml`

**Example AsyncAPI Spec:**
```yaml
asyncapi: 2.6.0
info:
  title: Order Service Messages
  version: 1.0.0
  description: Messages published by Order Service

channels:
  OrderCreated:
    publish:
      message:
        name: OrderCreated
        payload:
          type: object
          properties:
            orderId:
              type: string
            customerId:
              type: string

bindings:
  messageexchange:
    status: importing  # Start with importing
    environments:
      - euw1-pdv-qa-3
      - euw1-pdv-stg-5
      - euw1-pdv-prd-5
    sns:
      OrderCreated:
        accountId: "123456789012"  # Legacy account
        region: eu-west-1
```

### 5. Configure Cross-Account Access

**For Producers (Publishing to Legacy SNS):**

**MeX Custom SNS Policy:**
```yaml
sns:
  OrderCreated:
    accountId: "123456789012"  # Legacy SNS account
    region: eu-west-1
    policy:
      statements:
        - effect: Allow
          principal:
            AWS: "arn:aws:iam::{account_id}:role/jas/wl/terraform_managed/jas-wl-role-<MY_PROJECT_NAME>-<MY_WORKLOAD_NAME>"
          action:
            - sns:Publish
            - sns:GetTopicAttributes
```

**Sonic Runtime Workload Role (cps/projects):**
```yaml
workloads:
  my-service:
    permission_template: |
      {
        "Effect": "Allow",
        "Action": ["sns:Publish", "sns:GetTopicAttributes"],
        "Resource": "arn:aws:sns:eu-west-1:123456789012:OrderCreated"
      }
```

**For Consumers (Consuming from Legacy SQS):**

**MeX Configuration with Peered Environments:**
```yaml
bindings:
  messageexchange:
    interopStrategy: custom
    peeredEnvironments:
      - source: euw1-pdv-qa-3  # Sonic Runtime
        target: eu-west-1-pdv-qa-1  # Legacy RefArch
```

**MeX creates:**
- SQS queue in Sonic Runtime account
- SNS subscription from legacy topic
- Cross-account trust policies

### 6. Update Status to Live

After validation in `importing` status:

```yaml
bindings:
  messageexchange:
    status: live  # Enable full MeX features
```

**Merge PR** → MeX applies policies

## Common Migration Scenarios

### Scenario 1: RefArch Producer → Sonic Runtime

**Steps:**
1. Create AsyncAPI spec with `status: importing`
2. Configure legacy SNS topic in MeX
3. Create Sonic Runtime workload role (cps/projects)
4. Add custom SNS policy for cross-account publish
5. Deploy application to Sonic Runtime
6. Validate publishing works
7. Update to `status: live`

### Scenario 2: Sonic Runtime Consumer ← Legacy Producer

**Steps:**
1. Create AsyncAPI spec with `status: importing`
2. Configure `peeredEnvironments` (Sonic Runtime ← Legacy)
3. MeX creates SQS in Sonic Runtime + SNS subscription
4. Create workload role for SQS access
5. Deploy consumer to Sonic Runtime
6. Validate message consumption
7. Update to `status: live`

### Scenario 3: Shared Resource (Multiple Teams)

**Coordination Required:**
1. Identify all producers and consumers
2. Check if any team uses `JustSayingStack`
3. All teams migrate to JustSaying v7 first
4. Coordinate MeX onboarding (one team creates spec)
5. Other teams reference existing MeX resources
6. Update to `status: live` after all teams ready

## AsyncAPI Extensions

### interopStrategy

**Values:**
- `custom` - Manual cross-account configuration
- `auto` - Automatic interop based on MeX patterns

**Use `custom` for:**
- Legacy platform migrations (RefArch, L-JE, Marathon)
- Non-standard cross-account scenarios

### peeredEnvironments

**Purpose:** Define source → target message flows

**Example:**
```yaml
peeredEnvironments:
  - source: euw1-pdv-qa-3  # Sonic Runtime QA
    target: eu-west-1-pdv-qa-1  # RefArch QA
  - source: euw1-pdv-prd-5  # Sonic Runtime Prod
    target: eu-west-1-pdv-prd-1  # RefArch Prod
```

**Direction:**
- Producer in target, consumer in source → Subscribe source SQS to target SNS

## Documentation and Resources

**Official Documentation:**
- [MeX Onboarding Guide](https://backstage.eu-west-1.production.jet-internal.com/docs/default/group/messaging-integrations/MessageExchange/#how-to-onboarding-docs)
- [MeX Migration Examples](https://backstage.eu-west-1.production.jet-internal.com/docs/default/group/messaging-integrations/MessageExchange/just-saying-migrations/migration-examples-justsaying-consumer)
- [MeX Migration Cheatsheet](https://backstage.eu-west-1.production.jet-internal.com/docs/default/group/messaging-integrations/MessageExchange/just-saying-migrations/migration-cheatsheet)
- [JustSaying Producer Migration](https://backstage.eu-west-1.production.jet-internal.com/docs/default/group/messaging-integrations/MessageExchange/just-saying-migrations/migrate-existing-justsaying-producer)
- [JustSaying Consumer Migration](https://backstage.eu-west-1.production.jet-internal.com/docs/default/group/messaging-integrations/MessageExchange/just-saying-migrations/migrate-existing-justsaying-consumer)

**Confluence:**
- [SNS/SQS Migration Guide](https://justeattakeaway.atlassian.net/wiki/spaces/EDAG/pages/7426408922/SNS+SQS) by `#guild-events`

**Tools:**
- [Marmot Documentation Platform](https://marmot.pl-data-mi.pdv-3.eu-west-1.qa.jet-internal.com/)

**Support:**
- Slack: [#help-messaging-integrations](https://justeattakeaway.enterprise.slack.com/archives/C02EGBEMM1C)

## Key Reminders

1. **Always start with `importing` status** - Test before applying policies
2. **Coordinate with all teams** - Shared resources require synchronization
3. **Migrate away from JustSayingStack** - Must happen before `live` status
4. **Bidirectional cross-account setup** - Configure both Sonic Runtime role AND legacy resource policies
5. **Use Marmot** - Check existing MeX configurations before creating duplicates
