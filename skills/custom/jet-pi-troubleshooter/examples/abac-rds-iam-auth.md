# ABAC / Session Tag Investigation Pattern

## Date
2026-04 (extracted from PI investigation experience)

## Symptom Type
IAM / Authentication Failures, RDS IAM Authentication Failures

## Triggers
- "Access denied" when connecting to RDS with IAM auth
- `generate-db-auth-token` succeeds but connection fails
- Works with one SSO profile but not another
- IAM policies using `${aws:PrincipalTag/*}` silently failing

## Investigation Steps

### Step 1: Confirm the tag is the problem using IAM Policy Simulator

```bash
# Simulate WITHOUT the tag -- expect implicitDeny with the tag in MissingContextValues
aws iam simulate-principal-policy \
  --policy-source-arn "arn:aws:iam::<account-id>:role/aws-reserved/sso.amazonaws.com/eu-west-1/AWSReservedSSO_<profile>_<suffix>" \
  --action-names "rds-db:connect" \
  --resource-arns "arn:aws:rds-db:<region>:<account-id>:dbuser:<cluster-resource-id>/<username>" \
  --output json

# Simulate WITH the tag -- expect allowed
aws iam simulate-principal-policy \
  --policy-source-arn "arn:aws:iam::<account-id>:role/aws-reserved/sso.amazonaws.com/eu-west-1/AWSReservedSSO_<profile>_<suffix>" \
  --action-names "rds-db:connect" \
  --resource-arns "arn:aws:rds-db:<region>:<account-id>:dbuser:<cluster-resource-id>/<username>" \
  --context-entries "ContextKeyName=aws:PrincipalTag/<tagName>,ContextKeyValues=<value>,ContextKeyType=string" \
  --output json
```

If the first returns `implicitDeny` with `MissingContextValues` listing the tag, and the second returns `allowed`, the policy is correct but the tag is not being passed at runtime.

### Step 2: Check if ABAC is enabled on the Identity Center instance

```bash
# From the Identity Center management account (778305418618)
aws sso-admin describe-instance-access-control-attribute-configuration \
  --instance-arn "arn:aws:sso:::instance/ssoins-6804c347891d1cb4" \
  --region eu-west-1 --output json
```

If this returns `ResourceNotFoundException`, ABAC is **not enabled at all** -- no attributes from Okta are being passed as session tags. This means every policy using `${aws:PrincipalTag/*}` is silently broken.

### Step 3: Find the permission set ARN from the IAM role name

The IAM role suffix (e.g., `38023bda058903de` in `AWSReservedSSO_dips-admin_38023bda058903de`) does NOT directly map to the permission set ID. To find the permission set:
```bash
# From the mgmt account -- list permission sets provisioned to the target account
aws sso-admin list-permission-sets-provisioned-to-account \
  --instance-arn "arn:aws:sso:::instance/ssoins-6804c347891d1cb4" \
  --account-id <target-account-id> \
  --region eu-west-1 --output json

# Then describe each to find the one matching the role name
aws sso-admin describe-permission-set \
  --instance-arn "arn:aws:sso:::instance/ssoins-6804c347891d1cb4" \
  --permission-set-arn <arn> \
  --region eu-west-1 --query "PermissionSet.Name" --output text
```

### Step 4: Compare working vs broken profiles

When one SSO profile works and another doesn't, compare their managed policies and inline policies:
```bash
# List managed policies attached to the role
aws iam list-attached-role-policies --role-name AWSReservedSSO_<profile>_<suffix> --output json

# Get inline policy
aws iam get-role-policy --role-name AWSReservedSSO_<profile>_<suffix> --policy-name AwsSSOInlinePolicy --output json
```

A profile with `AdministratorAccess` (or any broad `*:*` policy) will bypass tag-based restrictions entirely, masking the ABAC misconfiguration.

### Step 5: Check the SSO policy repos for the policy source of truth

The SSO permission set policies are managed as code in these repos:
- `IFA/aws-sso-legacy-takeaway` -- legacy Takeaway SSO (policies in `policies/cloudops/<role>/default.json`, assignments in `permissions.yml`)
- `IFA/jet-aws-sso` -- JET SSO (policies in `policies/JET/cloudops/<role>/default.json`, group configs in `groups/JET/aws-legacy-takeaway-*.yml`)

Check git history on the policy files to trace when tag-dependent statements were added and by whom.

## Key Insight

The ABAC attribute configuration on the Identity Center instance is **not managed as code** in any known repo. It can only be configured via the AWS console or CLI in the management account. If it was never set up, or was accidentally deleted, all `PrincipalTag`-based policies across all permission sets are broken -- but profiles with broad managed policies will appear to work fine, masking the issue.

## Resolution Pattern
1. Confirm ABAC is missing via `describe-instance-access-control-attribute-configuration`
2. Check CloudTrail for `DeleteInstanceAccessControlAttributeConfiguration` to determine if it was deleted vs never created
3. Re-enable ABAC with the correct attribute mappings in the management account
4. Verify with IAM Policy Simulator that tags now resolve

## Learnings
- IAM Policy Simulator is your best friend for auth issues -- it shows `MissingContextValues`
- "Works with one profile, broken with another" = compare managed policies immediately
- `AdministratorAccess` masks all ABAC issues
- Always check CloudTrail for deletion before assuming "never configured"
- The management account for Identity Center is `778305418618`
