# Kafka Platform at JET

## Overview

JET operates two Kafka services, both accessible from Sonic Runtime:

| Service        | Provider | Usage                     | Accessibility from Sonic Runtime |
| -------------- | -------- | ------------------------- | -------------------------------- |
| **JET Kafka**  | RefArch  | Legacy platform           | ✅ Accessible                     |
| **TKWY Kafka** | TA SRE   | Modern, CloudOps standard | ✅ Accessible                     |

## Migration Considerations

### No Migration Needed (Common Case)
- If using **TKWY Kafka**: Already accessible from Sonic Runtime
- CloudOps applications typically use TKWY Kafka
- No topic migration or cluster change required

### Migration Scenarios

**RefArch → Sonic Runtime:**
- JET Kafka accessible from Sonic Runtime
- May require network connectivity verification
- Cluster linking available for topic mirroring

**CloudOps → Sonic Runtime:**
- TKWY Kafka already accessible (no changes needed)
- Same network connectivity as CloudOps EU1

## Kafka Scaling with KEDA

Sonic Runtime supports automatic scaling based on Kafka consumer lag using KEDA.

### Quick Configuration

```yaml
# values.yaml
horizontalPodAutoscaler:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  kafka:
    - consumerGroup: "my-consumer-group"
      topic: "user-events"
      lagThreshold: "10"
      activationLagThreshold: "5"
      authenticationRef:
        name: "your-cluster-name"  # Must match Kafka cluster name
```

### Key Parameters

| Parameter                | Description                                    | Default    | Required |
| ------------------------ | ---------------------------------------------- | ---------- | -------- |
| `consumerGroup`          | Consumer group name                            | -          | ✅        |
| `authenticationRef.name` | Cluster name (e.g., "default-euw1-production") | -          | ✅        |
| `topic`                  | Topic to monitor                               | All topics | ❌        |
| `lagThreshold`           | Target lag per pod                             | "10"       | ❌        |
| `activationLagThreshold` | Minimum lag to activate                        | "0"        | ❌        |

### Bootstrap Servers

**Automatic Detection:** The basic-application Helm chart automatically configures `bootstrapServers` based on the cluster name specified in `authenticationRef.name`.

**Manual Override (rare):**
```yaml
kafka:
  - consumerGroup: "my-group"
    bootstrapServers: "custom-kafka.company.com:9092"
```

## Confluent Kafka Clusters

Available clusters are documented in the [Confluent Kafka Clusters](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/kafka/getting-started/platform-overview/#confluent-kafka-clusters) list.

Example cluster names:
- `default-euw1-production`
- `default-euw1-staging`
- `default-euw1-qa`

## Common Scaling Use Cases

### Single Topic Consumer

Scale based on lag for one topic:

```yaml
horizontalPodAutoscaler:
  enabled: true
  minReplicas: 2
  maxReplicas: 15
  kafka:
    - consumerGroup: "user-events-consumer"
      topic: "user-events"
      lagThreshold: "10"
      activationLagThreshold: "5"
      authenticationRef:
        name: "default-euw1-production"
```

### Multi-Topic Consumer (All Topics in Group)

Scale based on all topics without specifying individual topics:

```yaml
horizontalPodAutoscaler:
  enabled: true
  minReplicas: 3
  maxReplicas: 15
  kafka:
    - consumerGroup: "multi-topic-consumer-group"
      # No topic specified = monitor all topics in consumer group
      lagThreshold: "50"
      activationLagThreshold: "10"
      authenticationRef:
        name: "default-euw1-production"
```

### Multiple Topics with Different Priorities

```yaml
horizontalPodAutoscaler:
  enabled: true
  minReplicas: 2
  maxReplicas: 20
  kafka:
    # High-priority events - aggressive scaling
    - consumerGroup: "priority-consumer-group"
      topic: "priority-events"
      lagThreshold: "5"
      activationLagThreshold: "1"
      authenticationRef:
        name: "default-euw1-production"
    
    # Batch processing - relaxed scaling
    - consumerGroup: "batch-consumer-group"
      topic: "batch-events"
      lagThreshold: "100"
      activationLagThreshold: "50"
      authenticationRef:
        name: "default-euw1-production"
```

## Advanced Configuration

### Partition-Aware Scaling

Ensure even distribution across consumers:

```yaml
horizontalPodAutoscaler:
  kafka:
    - consumerGroup: "balanced-consumer-group"
      topic: "events"
      lagThreshold: "20"
      ensureEvenDistributionOfPartitions: "true"
      limitToPartitionsWithLag: "true"
      authenticationRef:
        name: "default-euw1-production"
```

### Advanced Parameters

| Parameter                            | Description                       | Example      | Default  |
| ------------------------------------ | --------------------------------- | ------------ | -------- |
| `allowIdleConsumers`                 | Allow replicas > partition count  | "true"       | "false"  |
| `limitToPartitionsWithLag`           | Scale only on partitions with lag | "true"       | "false"  |
| `ensureEvenDistributionOfPartitions` | Even partition distribution       | "true"       | "false"  |
| `partitionLimitation`                | Specific partitions to monitor    | "0,1,2,5-10" | All      |
| `offsetResetPolicy`                  | Offset reset for new consumers    | "latest"     | "latest" |

## Prerequisites for Kafka Scaling

Before implementing Kafka-based scaling:

1. Application is a Kafka consumer with proper consumer group configuration
2. Topics have measurable message lag
3. Consumer group actively commits offsets

## Documentation References

- [KEDA Apache Kafka Scaler](https://keda.sh/docs/latest/scalers/apache-kafka/)
- [Kafka Platform Overview](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/kafka/getting-started/platform-overview/)
- [Scale with Kafka](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/oneeks/tasks/run-applications/advanced-scaling/kafka/)
