# Learnings

Accumulated patterns and insights from real-world PI investigations.

## ABAC / IAM Auth Patterns
- IAM Policy Simulator shows `MissingContextValues` -- fastest way to confirm tag issues
- "Works with one profile, broken with another" = compare managed policies immediately
- `AdministratorAccess` masks all ABAC/tag-based issues
- Always check CloudTrail for deletion before assuming "never configured"
- Identity Center management account: `778305418618`
- ABAC attribute config is NOT managed as code -- only exists in console/CLI

## RDS IAM Auth
- Check Terraform DB user provisioning (`308_rds_*_db/terragrunt.hcl`) before debugging IAM policies
- Cross-reference ABAC pattern -- these two issues often co-occur

## DNS / Weighted Routing Migrations
- Errors often appear in **downstream consumers**, not the service being changed -- always trace the `Uri` field in HTTP error logs to find the actual affected service
- Route53 weight changes take effect immediately (modulo DNS TTL) -- not gradual like pod rollouts
- **Host header mismatch is a common Istio 404 cause** -- check `cps/helm-core` istio-gateways AND the app's helmfile state values for the full list of hosts; bare hostname vs `-production` variant can differ
- Use Datadog IIS logs grouped by `@cs-host` to find all host headers hitting a service before shifting traffic
- Other services may send incorrect host headers (e.g., `ordermanagementapi` sending its own name instead of `consumerorderqueriesapi`)
- Permission model on `IFA/route53` can slow reverts -- PR author may lack Atlantis write access, requiring someone else to trigger plan/apply
- SOC notifications about route53 changes are a strong correlation signal when errors appear shortly after
- Multiple consumers affected simultaneously across different order IDs = infrastructure/routing issue, not data/logic
- `set_identifier` values `l-je` = legacy ELB, `oneeks` = Istio/OneEKS -- check which direction the weight shift went
- **Post-revert DNS caching**: even after reverting weights, application instances cache old DNS -- scale up/down to force new instances; CS agents need to clear browser cache
- **PI raise can lag 60-90 minutes behind the causal change** -- always look back further than the PI creation time (PI-33757: change at 08:37, PI raised at 10:19)

## General Investigation Patterns
- Terraform apply time != PR merge time -- check CI run timestamps
- Negative DNS caching extends outages far beyond the actual record gap
- `v-kubernetes-*` usernames = Vault-issued credentials, issue is usually ProxySQL
- IaC gaps are a root cause category -- some configs only exist in console
- Always check CloudTrail for manual console changes that bypass IaC

## S3 Replication Tracing
- Destination bucket policy reveals the source: look for `AllowS3Replication*` statements -- the `Principal.AWS` ARN contains the source account ID and replication role name
- Replication role name hints at source bucket name (e.g., `replication-role-jetconnect-sftp-fonoa-production` → bucket contains `jetconnect-sftp-fonoa-production`)
- **Wiz is the bridge between accounts** -- when you have an ARN/name but don't know which account, Wiz `graphSearch` finds it and gives `subscriptionExternalId` (account ID), region, tags
- S3 replication events (PutObject by replication role) are **data events**, NOT management events -- `cloudtrail lookup-events` won't find them
- Check `get-event-selectors` on each trail to see if S3 data events are logged for the bucket
- Fall back to `s3 ls` timestamps on the destination -- `LastModified` IS the replication completion time
- Source buckets with aggressive lifecycle expiration (e.g., 7-day) will appear empty even though they actively replicate
- Wiz GraphQL on Windows: use PowerShell `Invoke-RestMethod` directly with the token from `$env:LOCALAPPDATA\Wiz\auth.json` -- `wiz_api.sh` is bash-only and Git Bash may have auth file path issues

## Cross-Tool & Cross-Account Patterns
- **Wiz is the bridge between tools** -- when you have a name/ARN/IP but don't know the account, Wiz `graphSearch` finds it and gives `subscriptionExternalId` (account ID), region, tags, and dependency graph
- Many JET accounts are NOT in `~/.aws/config` -- check first, then **ask the user for temporary credentials** from the SSO portal
- Set temp creds as env vars (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`), verify with `sts get-caller-identity`
- Temp credentials expire (~1 hour); Wiz auth also expires -- re-auth with `wizcli auth --use-device-code` if `UNAUTHORIZED`
- Wiz auth file on Windows: `C:\Users\ClintonHerring\AppData\Local\Wiz\auth.json` (NOT `~/.wiz/auth.json`)
- **Pass identifiers between tools**: Jira gives component names → PlatformMetadata/Wiz gives account/repo → AWS CLI confirms state → Datadog correlates errors → GitHub finds the change
- Resource policies (S3 bucket policy, IAM trust policy, KMS key policy) reveal cross-account relationships -- always read the resource policy when tracing who-accesses-what
- S3 data events (PutObject, replication) are NOT in CloudTrail management event lookup -- need data event trails or fall back to object timestamps
- Datadog EU site: always set `DD_SITE=datadoghq.eu` before using `pup`
