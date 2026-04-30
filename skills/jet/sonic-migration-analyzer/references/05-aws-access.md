# AWS Resource Access and Cross-Account Setup

## Table of Contents

- [Workload Roles (IRSA)](#workload-roles-irsa)
- [Cross-Account Access](#cross-account-access)
- [Troubleshooting](#troubleshooting)
- [Documentation References](#documentation-references)

## Workload Roles (IRSA)

Sonic Runtime uses **IAM Roles for Service Accounts (IRSA)** to provide AWS credentials to workloads.

### When Do You Need a Workload Role?

- Your service accesses AWS resources (DynamoDB, S3, SQS, SNS, etc.)
- Skip this if your service doesn't interact with AWS

### Creating a Workload Role

**Required Information:**
1. AWS account IDs for target environments
2. Service Account name (auto-created by basic-application chart)
3. Specific IAM permissions (Action and Resource granularity)

**Find AWS Account IDs:** [Backstage OneEKS Environments](https://backstage.eu-west-1.production.jet-internal.com/catalog/default/environment?filters%5Bkind%5D=environment&filters%5Btags%5D=oneeks&filters%5Buser%5D=all)

**Service Account Discovery:**
```bash
# List all service accounts
kubectl get sa --namespace <MY_NAMESPACE>

# Find service account for specific pods
kubectl get pods --namespace <MY_NAMESPACE> -o=jsonpath="{range .items[*]}{.metadata.name}{'  '}{'system:serviceaccount:'}{.metadata.namespace}{':'}{.spec.serviceAccountName}{'\n'}{end}"
```

### Define Workload Role in cps/projects

Create or update `<MY_PROJECT_NAME>.yaml` in [cps/projects/workloads/pdv](https://github.je-labs.com/cps/projects/tree/main/workloads/pdv):

```yaml
workloads:
  <MY_APP_SERVICE_ACCOUNT_NAME>:
    service_account: <MY_APP_SERVICE_ACCOUNT_NAME>
    permission_template: |
      {
          "Effect": "Allow",
          "Action":  [
              "dynamodb:BatchGetItem",
              "dynamodb:Describe*",
              "dynamodb:List*",
              "dynamodb:GetItem",
              "dynamodb:Query",
              "dynamodb:Scan",
              "dynamodb:PartiQLSelect"
          ],
          "Resource": [
              "arn:aws:dynamodb:${dynamoCrossAccountRegion}:${dynamoCrossAccountId}:table/${tableName}",
              "arn:aws:dynamodb:${dynamoCrossAccountRegion}:${dynamoCrossAccountId}:table/${tableName}/*"
          ]
      }
    accounts:
      euw1-pdv-qa-3:
        variables:
          tableName: "my-table-name-euw1-pdv-qa-3"
          dynamoCrossAccountRegion: "eu-west-1"
          dynamoCrossAccountId: "123456789012"
```

**Approval Process:**
- Fork cps/projects repository
- Create PR with changes
- Link Sonic Runtime onboarding ticket
- Request approval from IFA team: `@support-ifa` in [#help-infra-foundations-aws](https://justeattakeaway.enterprise.slack.com/archives/CS6TQQG4S)

### Use Workload Role in Helmfile

**Step 1: Annotate Service Account**

In `helmfile.d/values/<MY_APP>.yaml.gotmpl`:
```yaml
serviceAccount:
  annotations:
    eks.amazonaws.com/role-arn: "{{ .Values.workloadRoleARN }}"
```

**Step 2: Set Role ARN per Environment**

In `helmfile.d/state_values/euw1-pdv-qa-3.yaml`:
```yaml
workloadRoleARN: "arn:aws:iam::891377069564:role/jas/wl/terraform_managed/jas-wl-role-<MY_PROJECT_NAME>-<MY_WORKLOAD_NAME>"
```

**ARN Pattern:**
```
arn:aws:iam::<AWS_ACCOUNT_ID>:role/jas/wl/terraform_managed/jas-wl-role-<MY_PROJECT_NAME>-<MY_WORKLOAD_NAME>
```

**Step 3: Verify Annotation**
```bash
kubectl describe sa <MY_APP_SERVICE_ACCOUNT_NAME>
```

Ensure `eks.amazonaws.com/role-arn` annotation is present.

### AWS SDK Configuration

**Supported Minimum Versions:**
- Java (v2): 2.10.11+
- Java (v1): 1.11.704+
- Go: 1.23.13+
- Python (Boto3): 1.9.220+
- Node.js: 2.525.0+ or 3.27.0+
- .NET: 3.3.659.1+ (requires AWSSDK.SecurityToken)
- PHP: 3.110.7+

**Automatic Credential Discovery:**
AWS SDKs automatically detect IRSA credentials if you don't explicitly set a credential provider.

**Environment Variables (Auto-Injected):**
- `AWS_ROLE_ARN`
- `AWS_WEB_IDENTITY_TOKEN_FILE`

**Java-Specific:** Include STS module on classpath ([WebIdentityTokenFileCredentialsProvider](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/auth/credentials/WebIdentityTokenFileCredentialsProvider.html))

### Regional STS Endpoints

**Recommendation:** Use regional STS endpoints to reduce latency and increase redundancy.

```yaml
env:
  - name: AWS_STS_REGIONAL_ENDPOINTS
    value: regional
```

**Behavior:**
- Default: Global `sts.amazonaws.com`
- Regional: `sts.{region}.amazonaws.com` (e.g., `sts.eu-west-1.amazonaws.com`)

## Cross-Account Access

### When Cross-Account Access is Needed

| Source Platform | Target            | Cross-Account Required?        |
| --------------- | ----------------- | ------------------------------ |
| RefArch EKS     | Sonic Runtime     | ✅ Yes (different AWS accounts) |
| L-JE EC2        | Sonic Runtime     | ✅ Yes (different AWS accounts) |
| Marathon        | Sonic Runtime     | ✅ Yes (different AWS accounts) |
| SRE EKS         | Sonic Runtime     | ✅ Yes (different AWS accounts) |
| CloudOps EU1    | Sonic Runtime EU1 | ❌ NO (same AWS account)        |

### Bidirectional Setup (Two-Sided Configuration)

**Critical:** True cross-account access requires configuration on BOTH sides.

**Side 1: Sonic Runtime (cps/projects)**
Create workload role with permissions to access legacy resources (see "Creating a Workload Role" above).

**Side 2: Legacy Account**
Update resource-based policies to trust Sonic Runtime workload role.

### Resource-Based Policies (Recommended)

Use resource-based policies for cross-account access instead of role assumption chains.

**Supported Services:** DynamoDB, S3, SQS, SNS, Secrets Manager, KMS, Lambda, ECR
- [AWS services supporting resource-based policies](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_aws-services-that-work-with-iam.html)

### DynamoDB Cross-Account Access

**Example:** Sonic Runtime workload in `euw1-pdv-qa-3` (account `891377069564`) accessing DynamoDB table in `eu-west-1-pdv-qa-1` (account `748583010480`).

**Resource-Based Policy on DynamoDB Table:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CrossAccountTablePolicy",
      "Effect": "Allow",
      "Principal": {
          "AWS": "arn:aws:iam::891377069564:role/jas/wl/terraform_managed/jas-wl-role-<MY_PROJECT_NAME>-<MY_WORKLOAD_NAME>"
      },
      "Action": "dynamodb:*",
      "Resource": [
        "arn:aws:dynamodb:eu-west-1:748583010480:table/<MY_DYNAMODB_TABLE>",
        "arn:aws:dynamodb:eu-west-1:748583010480:table/<MY_DYNAMODB_TABLE>/*"
      ]
    }
  ]
}
```

**Encryption Recommendation:** Use Amazon DynamoDB Managed Keys for encryption (simplifies cross-account access).

**Documentation:**
- [Cross-Account DynamoDB Access](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/oneeks/tasks/use-cloud-resources/cross-account-dynamodb-access/)
- [DynamoDB Resource Policies](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/oneeks/tasks/use-cloud-resources/dynamodb/#cross-account-access-to-dynamodb-tables-deployed-in-sonic-runtime-via-resource-policies)

### SNS/SQS Cross-Account Access

**Recommendation:** Use Message Exchange (MeX) for cross-account SNS/SQS communication.

**Consuming Messages from Non-Sonic Runtime:**
1. Create SQS queue in Sonic Runtime AWS account
2. Subscribe to original SNS topic via MeX
3. Define `peeredEnvironments` with `interopStrategy:custom` in MeX

**Publishing to Legacy SNS Topic:**
If migrating SNS producer to Sonic Runtime but topic remains in legacy account:

**Custom SNS Policy (in legacy account):**
```yaml
policy:
  statements:
    - effect: Allow
      principal:
        AWS: "arn:aws:iam::{account_id}:role/jas/wl/terraform_managed/jas-wl-role-<MY_PROJECT_NAME>-<MY_WORKLOAD_NAME>"
      action:
        - sns:Publish
        - sns:GetTopicAttributes
```

**MeX Token Replacement:** `{account_id}` automatically replaced by MeX based on environments.

**Workload Role Name Convention:**
- Default: `jas-wl-role-<MY_PROJECT_NAME>-<MY_WORKLOAD_NAME>`
- Override: `jas-wl-role-<legacy_name_override>` (if `legacy_name_override` set in cps/projects)

### CloudOps EU1 → Sonic Runtime EU1 (Same Account)

**No cross-account setup required.** Both use the same AWS account.

**Steps:**
1. Create workload role in cps/projects (as usual)
2. Update resource policies to allow workload role (if needed)
3. No Side 2 configuration needed (already in same account)

## Troubleshooting

### Verify Environment Variables
```bash
kubectl describe pod <MY_POD_NAME> -n <MY_NAMESPACE>
kubectl describe sa <MY_APP_SERVICE_ACCOUNT_NAME> -n <MY_NAMESPACE>
```

Check for:
- `AWS_ROLE_ARN`
- `AWS_WEB_IDENTITY_TOKEN_FILE`

### Common Issues

**"AccessDenied" Errors:**
- Verify IAM role has correct permissions
- Check trust relationship allows EKS OIDC provider + Service Account
- Review resource ARNs in policy statements

**"Unable to locate credentials":**
- Ensure AWS SDK version supports IRSA
- Verify no explicit credential configuration in code
- Check environment variables not overriding IRSA

**Java-Specific:**
- Include STS module on classpath

### Debug Logging

**Java:** `AWS_JAVA_SDK_LOG_LEVEL=DEBUG`
**Other SDKs:** Configure logger in code (SDK-specific)

### Get Help

[#help-sonic](https://justeattakeaway.enterprise.slack.com/archives/C06FWQRR64E)

**Provide:**
- Project, environment, application name
- Exact error message (Datadog link preferred)
- Helmfile values, Pod spec, Service Account YAML
- IAM role and policies (cps/projects PR link)
- AWS SDK version and language

## Documentation References

- [Access AWS Resources](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/oneeks/tasks/use-cloud-resources/using-aws-resources/)
- [Cross-Account DynamoDB Access](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/oneeks/tasks/use-cloud-resources/cross-account-dynamodb-access/)
- [Message Exchange (MeX)](https://backstage.eu-west-1.production.jet-internal.com/docs/default/group/messaging-integrations/architecture/)
- [AWS IRSA Documentation](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html)
