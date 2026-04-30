# Phase 7: Post-Migration Guidance

Present next steps (adapt based on EXPOSURE_TYPE):

> **After Merging PRs:**
>
> 1. **Verify**: Check QA deployment in Sonic Runtime. Monitor in Datadog.
>    - _The **`jet-datadog`** skill provides `pup` CLI commands for querying logs, checking APM
>      service stats, and verifying monitors. Load it if the user wants to verify the migration
>      through Datadog._
>      1b. **Vault verification** (if `VAULT_STRATEGY != none`): After deploying to QA, verify secrets are injected:
>    - Check pod annotations are applied: `kubectl get pod -n {PROJECT_ID} -o yaml | grep vault`
>    - Check sidecar logs: `kubectl logs -n {PROJECT_ID} {pod} -c vault-agent`
>    - If using `extra_policy_ro`, verify legacy paths are accessible (no permission denied errors in sidecar logs)
> 2. **Test**: Run smoke/integration tests against QA.
> 3. **Promote**: Deploy to staging, then production.
> 4. **Traffic split** (if configured):
>    - 0→10%: Update Route53 / domain-routing weights. Monitor 24h.
>    - 10→50%: Monitor 1-2 days.
>    - 50→100%: Monitor 1 week.
>    - Convert to direct CNAME after 1 week at 100%.
> 5. **Decommission SRE-EKS**: Remove Consul bridge, scale down deployment, clean up DNS, clean up code repo.

If EXPOSURE_TYPE is external or both, also present:

> **External Service Steps:**
>
> 6. **SmartGateway testing**: After SmartGateway PR is deployed to QA, test via SmartGateway regional endpoints (not directly via internal DNS). This validates the full external traffic path.
> 7. **API spec approval**: If you created a new BOATS spec, get approval from the API Design Guild before production. Join `#api-guild-design` on Slack.
> 8. **Cloudflare verification** (brand domains): After updating the Cloudflare origin, verify the brand domain resolves correctly. Check Cloudflare dashboard for any WAF blocks or cache issues.
> 9. **Origin restriction**: Ensure your service only accepts traffic from Cloudflare IP ranges (if using Cloudflare). This prevents direct access bypassing WAF.
>
> **Need help?**
>
> - Platform: `#help-sonic`
> - External routing: `#help-edge`/`#help-sonic`
> - API governance: `#help-edge`
> - DNS / Cloudflare: `#help-infra-foundations-aws`
