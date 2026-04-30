# Platform-Specific Migration Patterns

## L-JE EC2 → Sonic Runtime (Most Complex)

**CRITICAL:** If using JustSaying/SNS/SQS, MeX migration is **MANDATORY** before Sonic deployment.

**Note:** RefArch applications may also use JustSaying/JustSayingStack - see RefArch section for specific guidance.

1. **Messaging (BLOCKING if applicable)**:
   - **Phase 1**: Create AsyncAPI spec in MessageExchange repo (spec/services/)
   - Set status to `importing` (imports existing infra, NO policy changes)
   - Define environments, tenants, interopStrategy, naming patterns
   - Merge PR → auto-deploy to non-prod, request prod deployment
   - **Phase 2**: Set status to `live` (enables MeX policies & cross-account access)
   - Test thoroughly - policies WILL change
   - Contact #help-messaging-integrations for support
   - Update application code from JustSaying to MeX client (if needed)

2. **Configuration**: Consul → OneConfig (ConfigMaps via Helmfile state_values)

3. **Secrets**: JE Vault → OneSecrets (Vault in OneEKS, separate per environment)

4. **Containerization**: Create Dockerfile if needed (multi-stage build)

5. **AWS Access**: Configure cross-account access (BIDIRECTIONAL)
   - **Side 1 (Sonic Runtime)**: Create Workload Role via cps/projects Terraform
   - **Side 2 (Legacy Account)**: Update resource-based policies (DynamoDB, S3, etc.) to allow Workload Role ARN
   - Both sides required - common mistake to only configure one side

6. **Traffic Management**: Traffic split is **MANDATORY** (gradual 10% → 100%)

7. **Monitoring**: Set up Datadog APM, logs, dashboards

## RefArch EKS → Sonic Runtime

**Check Sonic Pipeline Eligibility First** (.NET/Go/Python/Java single repo)

### CRITICAL: If using JustSaying/JustSayingStack, MeX migration is MANDATORY

1. **Messaging (if applicable - BLOCKING)**:
   - **If using JustSayingStack**: Migrate to pure JustSaying v7 FIRST
     - Remove `.CreatePublishers()` calls (use `.WithTopicArn()` instead)
     - Remove `.AddQueueSubscriberForTenants()` and `.AddQueuePublisherForAllTenant()` calls
     - JustSayingStack overwrites MeX policies - MUST migrate JSS before MeX
   - **MeX Migration Phase 1**: Create AsyncAPI spec with status `importing`
     - For consumers: Producer MUST already be in MeX (status `draft` or `live`)
     - Define environments, tenants, interopStrategy, naming
     - Merge PR → test in non-prod environments
   - **MeX Migration Phase 2**: Set status to `live`
     - Enables MeX policies & cross-account networking
     - Test thoroughly as policies change
   - Contact #help-messaging-integrations for support

2. Adopt goldenpath structure (helmfile.d/)
3. Migrate Vault → OneSecrets
4. Convert Prometheus alerts → Datadog monitors
5. Replace .deploy/iam.yml IAM policies → Workload Roles
6. Map .deploy/inventory environments → helmfile.d/state_values/

## Marathon → Sonic Runtime

1. Replace .service DNS → Global DNS (route via igw-marathon initially)
2. Remove Consul service discovery (update Consul config to route .service to Sonic Runtime)
3. Replace Marathon base images with Verified Publisher/Official Docker images
4. Convert health checks → K8s probes
5. Update dependencies to use Global DNS (`tk-<service>` prefix for DB/RabbitMQ)

## CloudOps-EKS → Sonic Runtime

**Note:** CloudOps typically uses TKWY (TA SRE) Kafka, which is accessible from Sonic Runtime - no migration needed.

**Important:** CloudOps and Sonic Runtime EU1 bulkhead are in the **same AWS account** - no cross-account access setup needed for AWS resources (RDS, S3, DynamoDB, etc.).

1. Adopt goldenpath structure (helmfile.d/)
2. Migrate AWS Secrets Manager → OneSecrets (Vault)
3. Convert IRSA (manual/ticket-based) → Workload Roles (self-service Terraform)
4. Update namespace references → Projects
5. Convert free-form K8s/Helm → basic-application chart
6. **AWS Resources**: Same account as EU1 - Workload Role can access directly (no cross-account trust policies needed)
7. **Kafka**: Continue using existing TKWY brokers (accessible from Sonic Runtime)

## SRE-EKS → Sonic Runtime

**Key Consideration**: SRE-EKS is single bulkhead, Sonic Runtime is multi-bulkhead (EU1, EU2, OC1, NA1)

**Recommendation**: Migrate to EU1 first - functional equivalent of SRE-EKS, only bulkhead with legacy Takeaway Vault access

**Check Sonic Pipeline Eligibility**: .NET/Go/Python/Java single repo may qualify for automated goldenpath

1. Adopt goldenpath structure (helmfile.d/)
2. Route .service DNS via igw-marathon initially
3. Update to Global DNS over time
4. Validate deployments across ALL bulkheads independently
5. Convert to basic-application chart
