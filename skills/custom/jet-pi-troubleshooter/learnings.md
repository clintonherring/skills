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

## General Investigation Patterns
- Terraform apply time != PR merge time -- check CI run timestamps
- Negative DNS caching extends outages far beyond the actual record gap
- `v-kubernetes-*` usernames = Vault-issued credentials, issue is usually ProxySQL
- IaC gaps are a root cause category -- some configs only exist in console
- Always check CloudTrail for manual console changes that bypass IaC
