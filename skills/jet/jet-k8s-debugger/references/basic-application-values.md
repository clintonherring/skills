# basic-application Chart Values Reference

Complete values reference for the `sre/basic-application` Helm chart used across all JET OneEKS deployments. Chart source: `artifactory.takeaway.com/sre-helm-prod-virtual`. Upstream repo: `github.je-labs.com/helm-charts/basic-application`.

## Table of Contents

- [Application Metadata](#application-metadata)
- [Deployment Configuration](#deployment-configuration)
- [Service Configuration](#service-configuration)
- [Istio Resources](#istio-resources) (VirtualService, DestinationRule, AuthorizationPolicy, ServiceEntry, RequestAuthentication)
- [KEDA Autoscaling](#keda-autoscaling)
- [ConfigMaps](#configmaps)
- [Secrets](#secrets)
- [CronJobs and Jobs](#cronjobs-and-jobs)
- [Persistent Volume Claims](#persistent-volume-claims)
- [Common Misconfigurations](#common-misconfigurations)

## Application Metadata

```yaml
application:
  name: ""          # Application name. Must match ^[a-z][a-z0-9]*$, 3-36 chars (length enforced by schema separately).
  repository: ""    # Git repository URL. Must start with "git" or be empty.
```

## Deployment Configuration

```yaml
deployment:
  # Container image
  image:
    repository: ""                    # Full image path (e.g., artifacts.takeaway.com/docker-prod-virtual/myapp)
    tag: ""                           # Image tag
    pullPolicy: IfNotPresent

  # Resource requests and limits
  resources:
    requests:
      cpu: "100m"
      memory: "128Mi"
    limits:
      cpu: "500m"
      memory: "512Mi"

  # Replica count (before KEDA takes over)
  replicaCount: 1

  # Liveness probe
  livenessProbe:
    httpGet:
      path: /health
      port: http
    initialDelaySeconds: 30
    periodSeconds: 10
    timeoutSeconds: 5
    failureThreshold: 3

  # Readiness probe
  readinessProbe:
    httpGet:
      path: /health/ready
      port: http
    initialDelaySeconds: 10
    periodSeconds: 10
    timeoutSeconds: 5
    failureThreshold: 3

  # Environment variables
  # WARNING: names cannot start with JET_ or be reserved Datadog vars
  env:
    - name: MY_VAR
      value: "my-value"
    - name: SECRET_VAR
      valueFrom:
        secretKeyRef:
          name: my-secret
          key: password

  # Rollout strategy (choose ONE)
  strategy:
    # Option A: Rolling update (default)
    rollingUpdate:
      maxSurge: 25%
      maxUnavailable: 0

    # Option B: Canary (requires Istio VirtualService)
    # canary:
    #   steps:
    #     - setWeight: 1
    #     - pause: {}
    #     - setWeight: 10
    #     - pause: {}
    #     - setWeight: 50
    #     - pause: {}

  # Node scheduling
  capacityType: ""        # "", "spot", or "on-demand"
  nodeSelector: {}
  tolerations: []
  affinity: {}

  # Pod disruption budget
  podDisruptionBudget:
    enabled: false
    minAvailable: 1
    # maxUnavailable: 1   # Alternative to minAvailable

  # Service account
  serviceAccount:
    create: true
    name: ""
    annotations: {}       # e.g., eks.amazonaws.com/role-arn for IRSA

  # Additional volumes and volume mounts
  volumes: []
  volumeMounts: []

  # Init containers
  initContainers: []

  # Additional containers (sidecars)
  extraContainers: []

  # Labels and annotations
  podLabels: {}
  podAnnotations: {}
  labels: {}
  annotations: {}
```

## Service Configuration

```yaml
service:
  type: ClusterIP          # Almost always ClusterIP in JET (Istio handles ingress)
  port: 80                 # Service port
  targetPort: http         # Container port name
  annotations: {}
```

## Istio Resources

### VirtualService

```yaml
virtualservices:
  - hosts:
      - "myapp.eu-west-1.production.jet-internal.com"
    # HTTP routing (mutually exclusive with fault)
    http:
      - match:
          - uri:
              prefix: /api/v1
        route:
          - destination:
              host: myapp
              port:
                number: 80
    # Fault injection (mutually exclusive with http)
    # fault:
    #   delay:
    #     percentage:
    #       value: 10
    #     fixedDelay: 5s
```

When canary is enabled, the chart auto-generates:
- Stable VirtualService with traffic weight split
- Preview VirtualService at `preview-<host>` for `*.jet-internal.com` hosts

### DestinationRule

```yaml
destinationRules:
  - trafficPolicy:
      tls:
        mode: ISTIO_MUTUAL     # Default for JET (mTLS between services)
      connectionPool:
        tcp:
          maxConnections: 100
        http:
          h2UpgradePolicy: DEFAULT
          http1MaxPendingRequests: 1024
          http2MaxRequests: 1024
```

### AuthorizationPolicy

```yaml
authorizationPolicies:
  - action: ALLOW
    rules:
      - from:
          - source:
              principals:
                - "cluster.local/ns/other-namespace/sa/other-service"
        to:
          - operation:
              methods: ["GET", "POST"]
              paths: ["/api/*"]
```

### ServiceEntry

```yaml
serviceEntries:
  - hosts:
      - "external-api.example.com"
    ports:
      - number: 443
        name: https
        protocol: TLS
    resolution: DNS
    location: MESH_EXTERNAL
```

### RequestAuthentication

```yaml
requestAuthentication:
  jwtRules:
    - issuer: "https://auth.example.com"
      jwksUri: "https://auth.example.com/.well-known/jwks.json"
      audiences:
        - "my-audience"
```

## KEDA Autoscaling

```yaml
keda:
  enabled: false
  minReplicaCount: 1
  maxReplicaCount: 10
  cooldownPeriod: 300
  pollingInterval: 30

  # Authentication reference (for Kafka, CloudWatch, etc.)
  authenticationRef:
    name: ""

  triggers:
    # CPU-based scaling
    - type: cpu
      metadata:
        type: Utilization
        value: "80"

    # Memory-based scaling
    - type: memory
      metadata:
        type: Utilization
        value: "80"

    # Kafka consumer lag
    - type: kafka
      metadata:
        topic: my-topic
        consumerGroup: my-group
        lagThreshold: "100"
        # bootstrapServers auto-resolved from authenticationRef.name
        # Supported clusters: default-euw1-*, default-apse2-*, default-usw2-*, stag, duck

    # CloudWatch metric
    - type: aws-cloudwatch
      metadata:
        namespace: AWS/SQS
        dimensionName: QueueName
        dimensionValue: my-queue
        metricName: ApproximateNumberOfMessagesVisible
        targetMetricValue: "5"

    # Cron-based scaling
    - type: cron
      metadata:
        timezone: Europe/London
        start: "0 8 * * *"
        end: "0 20 * * *"
        desiredReplicas: "5"
```

## ConfigMaps

```yaml
configmap:
  enabled: false
  data:
    config.yaml: |
      key: value
```

**Note:** ConfigMap names are hash-suffixed (`<app>-<sha256[:8]>`) and annotated with `helm.sh/resource-policy: keep`. Old ConfigMaps are not automatically deleted.

## Secrets

```yaml
secrets:
  - name: my-secret
    data:
      password: "base64-encoded-value"
```

**Note:** Most JET services use Vault for secrets, not Helm-managed secrets. Vault agent injects secrets via init container or annotations.

## CronJobs and Jobs

```yaml
cronjobs:
  - name: my-cronjob
    schedule: "0 */6 * * *"
    concurrencyPolicy: Forbid
    image:
      repository: artifacts.takeaway.com/docker-prod-virtual/myapp
      tag: latest
    resources:
      requests:
        cpu: "100m"
        memory: "128Mi"
    env: []

jobs:
  - name: my-job
    image:
      repository: artifacts.takeaway.com/docker-prod-virtual/myapp
      tag: latest
    command: ["./run-migration.sh"]
    resources:
      requests:
        cpu: "100m"
        memory: "128Mi"
```

## Persistent Volume Claims

```yaml
persistentVolumeClaims:
  - name: data
    accessModes:
      - ReadWriteOnce
    storageClassName: gp3
    resources:
      requests:
        storage: 10Gi
```

## Common Misconfigurations

| Issue | Symptom | Fix |
|-------|---------|-----|
| `deployment.env[].name` starts with `JET_` | Schema validation failure | Rename env var (reserved prefix) |
| Both `rollingUpdate` and `canary` in strategy | Schema validation failure | Use only one strategy |
| `virtualservices[].fault` and `http` both set | Schema validation failure | These are mutually exclusive |
| `capacityType` set to invalid value | Schema validation failure | Use `""`, `"spot"`, or `"on-demand"` |
| `application.name` with uppercase or special chars | Schema validation failure | Use `^[a-z][a-z0-9]*$`, 3-36 chars |
| Canary configured without VirtualService hosts | Canary does not create preview resources | Add `virtualservices[].hosts` |
| Wrong `image.repository` | ImagePullBackOff | Use `artifacts.takeaway.com/docker-prod-virtual/<app>` |
| Resource limits too low | OOMKilled or CPU throttling | Increase limits, check `kubectl top pods` |
| Missing `serviceAccount.annotations` for IRSA | AWS API calls fail from pod | Add `eks.amazonaws.com/role-arn` annotation |
| KEDA trigger without `authenticationRef` | ScaledObject error | Add TriggerAuthentication for Kafka/CloudWatch triggers |
