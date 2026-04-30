# Phase 7: Post-Migration

**Goal**: Generate migration summary, provide verification guidance, update knowledge base.

## 7.1 Generate Migration Report

Save to `/tmp/migration-summary-{APP_NAME}.md`:

```markdown
# Migration Summary: {APP_NAME}

## Service Details
- **Component**: {APP_NAME}  |  **Team**: {TEAM}  |  **Tier**: {TIER}
- **Source**: CloudOps-EKS  →  **Target**: Sonic Runtime (OneEKS)
- **Difficulty**: {score}/100  |  **CI/CD**: Sonic Pipeline / GHA

## PRs Created
| Repository | PR | Description |
|---|---|---|
| {source-repo} | #N | Goldenpath restructure |
| IFA/route53 | #N | DNS weighted records |
| cps/helm-core | #N | Istio gateway rules |
| cps/projects | #N | Workload Role / Vault access |

## Next Steps
1. Get PRs reviewed and merged (see merge order below)
2. Deploy to QA, verify connections and functionality
3. Deploy to staging, verify
4. Start traffic split: Sonic weight 1 (1%), monitor in Datadog
5. Gradually increase (10% → 50% → 100%)
6. After 30+ days stable at 100%, decommission CloudOps

## Secrets Status

{Generate from SECRETS_INVENTORY grouped by day1_status — see 06-vault-secrets-migration.md → "Secrets Migration Checklist Format"}

### ✅ Works Immediately (no action needed)
| Secret | Source | What Was Generated |
|--------|--------|--------------------|  
| {ready secrets} | {source} | {annotation/policy description} |

### ⚠️ Before First Deploy
{Only include this section if any secrets have day1_status = blocked}
| Secret | Source | OneSecrets Path | Action Required |
|--------|--------|----------------|----------------|
| {blocked secrets} | {source} | `{PROJECT_ID}/data/{secret-name}` | Create in Vault UI: copy values from current source (K8s Secret / AWS SM) |

### ⚠️ Migrate to OneSecrets Before First Deploy
{Only include this section if any secrets come from AWS Secrets Manager}

Secrets currently in AWS Secrets Manager must be migrated to **OneSecrets** (Vault KV v2) before your first Sonic deploy:
1. Create the secret values in Vault UI at `{PROJECT_ID}/data/{secret-name}`
2. Remove the AWS Secrets Manager SDK dependency from the app

See [Backstage: Migrating Secrets](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/oneeks/tasks/manage-secrets/migrating-secrets/).

**Note**: The runtime migration PRs include all Vault annotations, policies, and
`extra_policy_ro` config. Only the "⚠️ Before First Deploy" items block deployment.
```

## 7.2 Post-Merge Verification

Provide verification commands:

```bash
# Check pod status
kubectl get pods -n {PROJECT_ID} | grep {APP_NAME}

# Check Vault sidecar (if VAULT_STRATEGY != none)
kubectl logs -n {PROJECT_ID} {pod} -c vault-agent
# Look for: no permission denied errors, secrets successfully injected

# Check VirtualService
kubectl get virtualservice -n {PROJECT_ID} {APP_NAME} -o yaml

# Check pod annotations (Vault)
kubectl get pod -n {PROJECT_ID} -o yaml | grep vault
```

**Vault verification** (if `VAULT_STRATEGY != none`):
- Verify secrets are injected at `/vault/secrets/` in the pod
- Check sidecar logs for permission denied errors
- If using `extra_policy_ro`, verify cross-project secret paths are accessible
- For non-EU1 environments, verify OneSecrets paths resolve correctly

Suggest using `jet-datadog` skill for monitoring verification if available. The **`jet-datadog`**
skill provides `pup` CLI commands for querying logs, checking APM service stats, and verifying
monitors. Load it if the user wants to verify the migration through Datadog.

## 7.3 Traffic Split Progression

Remind the user of the gradual increase schedule:

| Stage | Sonic Weight | CloudOps Weight | Duration |
|-------|-------------|-----------------|----------|
| Start | 0 | 100 | Deploy + verify |
| Canary | 1 | 99 | 1-2 days |
| 10% | 10 | 90 | 3-5 days |
| 50% | 50 | 50 | 1 week |
| Full | 100 | 0 | 30+ days before decommission |

After 1 week stable at 100%, convert weighted records to direct CNAMEs (remove the CloudOps
endpoint entry, keep only the Sonic entry, remove weights/identifiers).

## 7.4 CloudOps-EKS Decommissioning

After 30+ days stable at 100% Sonic traffic, decommission CloudOps resources.
See the [official decommissioning guide](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/oneeks/tasks/platform-transition/cloudops/#9-cloudops-eks-decommissioning).

> **Decommissioning Checklist:**
>
> 1. Verify zero traffic reaching CloudOps endpoints
> 2. Archive CloudOps K8s manifests and configurations
> 3. Update runbooks and documentation
> 4. Remove CloudOps-specific DataDog monitors and dashboards
> 5. Clean up secrets from AWS Secrets Manager (after verifying OneSecrets has copies)
> 6. Scale down CloudOps deployments to zero replicas
> 7. Remove old CI/CD workflows (re-enable or delete the disabled push trigger)

## 7.5 External Service Post-Migration (if external endpoints detected)

Present additional steps for services with `jet-external.com` endpoints (SmartGateway):

> **External Service Steps:**
>
> 5. **SmartGateway testing**: After SmartGateway PR is deployed to QA, test via SmartGateway
>    regional endpoints (not directly via internal DNS). This validates the full external path.
> 6. **API spec approval**: If you created a new BOATS spec, get approval from the API Design
>    Guild before production. Join `#api-guild-design` on Slack.
> 7. **Cloudflare verification** (brand domains): After updating the Cloudflare origin, verify
>    the brand domain resolves correctly. Check Cloudflare dashboard for WAF blocks or cache issues.
>
> **Need help?**
>
> - Platform: `#help-sonic`
> - External routing: `#help-http-integrations`
> - API governance: `#api-guild-design`
> - DNS / Cloudflare: `#help-infra-foundations-aws`

## 7.6 Update Knowledge Base

Add a learning entry to `references/01-knowledge-base.md` under `## Learnings from Past Migrations`:

```markdown
### {APP_NAME} (YYYY-MM-DD)
- **Difficulty**: {score}/100
- **Key findings**: {what was unique about this migration}
- **Gotchas encountered**: {anything unexpected}
- **New patterns**: {reusable patterns discovered}
```

Update any KB sections where new patterns or edge cases were found.
