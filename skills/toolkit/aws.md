# aws (AWS CLI)

## Location
Should be on PATH via standard installation.

## Verification
```powershell
aws --version
aws sts get-caller-identity
```

## SSO Login
```powershell
aws sso login --profile <profile-name>
```

## Notes
- JET uses AWS SSO via Okta
- Multiple profiles available (check `~/.aws/config`)
- For CloudTrail queries, ensure you're in the right account
