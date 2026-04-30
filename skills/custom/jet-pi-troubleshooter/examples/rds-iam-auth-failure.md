# RDS IAM Authentication Failures

## Date
2026-04 (extracted from PI investigation experience)

## Symptom Type
RDS IAM Authentication Failures

## Triggers
- "Access denied" when connecting to RDS with IAM auth
- `generate-db-auth-token` succeeds but connection fails
- Works with one SSO profile but not another

## Check First
1. IAM Policy Simulator against the failing role (see `abac-rds-iam-auth.md`)
2. Identity Center ABAC configuration in mgmt account `778305418618`
3. Terraform DB user provisioning (is the username in the IAM DB user list?)
4. SSO policy repos for `AllowRDSLogin` statement history

## Common Causes
- **ABAC not enabled on Identity Center** -- `${aws:PrincipalTag/shortUserName}` resolves to empty, resource ARN matches nothing
- **User not provisioned as IAM DB user** -- the Terraform config for the RDS cluster (typically `308_rds_*_db/terragrunt.hcl` in `Data-Infrastructure-Platform-Services/tkwy-aws-datastores`) must include the username with `AWSAuthenticationPlugin`
- **Broad policy masking the real issue** -- `dba` profile has `AdministratorAccess` which bypasses `shortUserName` tag requirement; `dips` and other least-privilege profiles do not

## Key Repos
- `Data-Infrastructure-Platform-Services/tkwy-aws-datastores` -- RDS cluster definitions and DB user provisioning
- `IFA/aws-sso-legacy-takeaway` / `IFA/jet-aws-sso` -- SSO permission set policies containing `AllowRDSLogin`

## Key Datadog Query
```
*rds-db:connect* OR *Access denied* OR *authentication* AND service:<db-related-service>
```

## Learnings
- Always check if the DB user is provisioned in Terraform before debugging IAM policies
- The `308_rds_*_db/terragrunt.hcl` pattern is where IAM DB users are defined
- Cross-reference with ABAC pattern -- these two issues often co-occur
