# S3 Replication Tracing: Fonoa Reports Bucket

## Question
"When were the last files replicated to `enterprise-infrastructure-fonoa-reports-prod`?"

## Investigation Steps

### 1. Find the destination bucket in Wiz
**Tool**: Wiz GraphQL API (PowerShell — `wiz_api.sh` doesn't work natively in PowerShell, use direct REST)

```powershell
# Auth first
wizcli.exe auth --use-device-code

# Query Wiz for the bucket
$authJson = Get-Content "$env:LOCALAPPDATA\Wiz\auth.json" | ConvertFrom-Json
$token = $authJson.access_token
$dc = $authJson.data_center
$apiUrl = "https://api.$dc.app.wiz.io/graphql"

$query = 'query($q:GraphEntityQueryInput){graphSearch(first:5,query:$q){nodes{entities{id name type properties}}}}'
$variables = '{"q":{"type":["BUCKET"],"where":{"cloudPlatform":{"EQUALS":["AWS"]},"name":{"CONTAINS":["fonoa-reports-prod"]}}}}'

$body = @{query=$query;variables=($variables | ConvertFrom-Json)} | ConvertTo-Json -Depth 10 -Compress
$headers = @{Authorization="Bearer $token";"Content-Type"="application/json"}
$result = Invoke-RestMethod -Uri $apiUrl -Method POST -Headers $headers -Body $body
```

**Result**: Found `enterprise-infrastructure-fonoa-reports-prod` in account **868502343283**, region `eu-west-1`, owned by `enterprise-infrastructure`.

### 2. Get the bucket policy to find replication source
**Tool**: AWS CLI (needed temp credentials for account 868502343283 — no SSO profile existed)

Asked user for temporary credentials, set as env vars:
```powershell
$env:AWS_ACCESS_KEY_ID="<from user>"
$env:AWS_SECRET_ACCESS_KEY="<from user>"
$env:AWS_SESSION_TOKEN="<from user>"
$env:AWS_DEFAULT_REGION="eu-west-1"
```

Checked CloudTrail for bucket events:
```bash
aws cloudtrail lookup-events \
  --lookup-attributes "AttributeKey=ResourceName,AttributeValue=enterprise-infrastructure-fonoa-reports-prod" \
  --max-results 5
```

**Result**: Found `PutBucketPolicy` events showing the replication statement:
```json
{
  "Sid": "AllowS3ReplicationProd",
  "Principal": {"AWS": "arn:aws:iam::851725368028:role/replication-role-jetconnect-sftp-fonoa-production"},
  "Action": ["s3:ReplicateObject", "s3:ReplicateDelete", "s3:ReplicateTags", "s3:ObjectOwnerOverrideToBucketOwner"],
  "Resource": "arn:aws:s3:::enterprise-infrastructure-fonoa-reports-prod/*"
}
```

**Key finding**: Source account is **851725368028**, replication role name hints at source bucket: `jetconnect-sftp-fonoa-production`.

### 3. Find the source bucket in Wiz
**Tool**: Wiz GraphQL API

```powershell
$variables = '{"q":{"type":["BUCKET"],"where":{"cloudPlatform":{"EQUALS":["AWS"]},"subscriptionExternalId":{"EQUALS":["851725368028"]},"name":{"CONTAINS":["fonoa"]}}}}'
```

**Result**: Found `jetconnect-sftp-fonoa-production-d13aa70d` in account 851725368028.

### 4. Confirm replication config on source bucket
**Tool**: AWS CLI (needed temp credentials for account 851725368028 — also no SSO profile)

```bash
aws s3api get-bucket-replication --bucket jetconnect-sftp-fonoa-production-d13aa70d
```

**Result**: Replication is **Enabled**, replicating entire bucket to `enterprise-infrastructure-fonoa-reports-prod` with `DeleteMarkerReplication: Enabled`.

### 5. Check for recent replication events
**Tool**: AWS CloudTrail (source account)

CloudTrail `lookup-events` only returned management events (PutBucketReplication, PutBucketPolicy, PutBucketLifecycle). Actual PutObject/replication events are **S3 data events** and were NOT logged on any trail for this bucket.

Checked trail event selectors:
```bash
aws cloudtrail get-event-selectors --trail-name trail-s3
```
The `trail-s3` trail only logged data events for `scoober-assets-private-prod` — not the fonoa bucket.

### 6. Fall back to object timestamps
**Tool**: AWS CLI (destination account)

```bash
aws s3 ls s3://enterprise-infrastructure-fonoa-reports-prod/ --recursive
```

Sorted by date, the most recent files were uploaded on **2025-04-16 at 14:32:06 UTC**.

### 7. Check source bucket lifecycle
The source bucket has a **7-day expiration** lifecycle rule, meaning files are deleted 7 days after upload. This explains why listing the source bucket would show no/few files — they expire quickly after being replicated.

## Tool Switching Summary

| Step | Tool | Account | Auth Method |
|------|------|---------|-------------|
| Find bucket metadata | Wiz GraphQL | N/A (cross-account) | `wizcli auth --use-device-code` |
| Get bucket policy | AWS CLI | 868502343283 (dest) | Temp creds from user |
| Find source bucket | Wiz GraphQL | N/A (cross-account) | Same Wiz session |
| Confirm replication | AWS CLI | 851725368028 (source) | Temp creds from user |
| Check CloudTrail | AWS CLI | Both accounts | Temp creds from user |
| List objects | AWS CLI | 868502343283 (dest) | Temp creds from user |

## Key Takeaways

1. **Wiz is the bridge** — when you have a resource but don't know the account, Wiz's graph search finds it and gives you the account ID, region, and tags
2. **Bucket policy reveals the replication chain** — the `AllowS3Replication*` statement contains the source account and role ARN
3. **Role name hints at source bucket name** — `replication-role-jetconnect-sftp-fonoa-production` → source bucket contains `jetconnect-sftp-fonoa-production`
4. **S3 replication events are data events** — CloudTrail management event lookup won't find them; need S3 data event trails or fall back to object timestamps
5. **Object LastModified = replication time** — on the destination, the modification timestamp is when replication completed
6. **Ask for temp creds** — when no SSO profile exists for an account, ask the user to paste temporary credentials from the AWS SSO portal
7. **Check lifecycle rules** — source buckets with aggressive expiration explain "empty" buckets that actively replicate
