# Multi-Repository Changes Specification

## Repository Quick Reference

| Short Name                                        | Full GHE URL                                                                    | Purpose                              |
| ------------------------------------------------- | ------------------------------------------------------------------------------- | ------------------------------------ |
| `IFA/route53`                                     | `https://github.je-labs.com/IFA/route53`                                        | DNS weighted records (traffic split) |
| `cps/helm-core`                                   | `https://github.je-labs.com/cps/helm-core`                                      | Istio ingress customRules            |
| `cps/consul`                                      | `https://github.je-labs.com/cps/consul`                                         | Consul backward compatibility        |
| `IFA/domain-routing`                              | `https://github.je-labs.com/IFA/domain-routing`                                 | Brand domain routing / Cloudflare    |
| `external-api-services/smartgatewayconfiguration` | `https://github.je-labs.com/external-api-services/smartgatewayconfiguration`    | SmartGateway (Kong) routes           |
| `Architecture/api_specifications`                 | `https://github.je-labs.com/Architecture/api_specifications/api_specifications` | OpenAPI specs (BOATS format)         |
| `cps/projects`                                    | `https://github.je-labs.com/cps/projects`                                       | OneSecrets, workload roles           |
| `cps/vault`                                       | `https://github.je-labs.com/cps/vault`                                          | Vault policies, secret backends      |
| `helm-charts/basic-application`                   | `https://github.je-labs.com/helm-charts/basic-application`                      | Helm chart (fetch latest version)    |
| `justeattakeaway-com/goldenpath`                  | `https://github.je-labs.com/justeattakeaway-com/goldenpath`                     | Goldenpath templates                 |
| `metadata/PlatformMetadata`                       | `https://github.je-labs.com/metadata/PlatformMetadata`                          | Service metadata (canonical names)   |

## Overview

An SRE-EKS to Sonic Runtime migration may require changes across up to 7 repositories. For each, use the 3-tier PR creation strategy (see "PR Creation Strategy" below): try direct push → fork and PR from fork → output diffs for manual application.

## PR Conventions

- **Branch name**: `{JIRA}-migrate-{service-name}-to-sonic`
- **PR title**: `{JIRA}: Migrate {service-name} to Sonic Runtime - {repo purpose}`
- **PR body**: Include summary, link to Jira ticket, and what the change does

## Repository 1: Source Application Repository

**What**: Full goldenpath restructure of the service repository.

**Changes**:

- Create `helmfile.d/` directory structure (see `03-goldenpath-structure.md`)
- Create `.sonic/sonic.yml` OR `.github/workflows/` (see `04-cicd-eligibility.md`)
- Update/create `Dockerfile` if needed
- Replace all `.service` references with GlobalDNS addresses from `SERVICE_ADDR_MAP` (Phase 4 Q4a-2) — both infrastructure and application deps must be resolved (see Phase 5 Step 8)
- Remove SRE-EKS-specific deployment configs (old helmfile, deploy scripts)

**PR body template**:

```markdown
## Summary

- Restructure repository to Sonic Runtime goldenpath format
- Add helmfile.d/ with environment-specific configuration for {bulkhead}
- Configure {Sonic Pipeline / GitHub Actions} for CI/CD
- Replace all .service addresses with GlobalDNS equivalents (validated via IFA/route53)

## Jira

[{JIRA}](https://justeattakeaway.atlassian.net/browse/{JIRA})

## Migration Details

- Source platform: SRE-EKS
- Target: Sonic Runtime ({bulkhead})
- Environments: {env mapping}
- CI/CD: {Sonic Pipeline / GitHub Actions}
- Chart version: {fetched version}
```

## Repository 2: IFA/route53 (DNS Traffic Split)

**When**: User chose gradual traffic split via GlobalDNS, OR service uses R-records/G-records that need weighted CNAME records.

**What**: Add weighted CNAME records for DNS-based traffic splitting. **If the service uses R-records or G-records, create records for ALL environments** (QA, staging, production), not just production. See `08-traffic-split.md` for the per-environment DNS strategy.

**How**: Clone the repo, explore its structure to find the appropriate zone file for each environment, and follow existing terraform patterns for weighted records. Use the `route53-weighted-cname.tf.tmpl` template with `{{ENV_TYPE}}` set per environment.

**PR body template**:

```markdown
## Summary

- Add weighted CNAME records for {service-name} traffic split (SRE-EKS → Sonic Runtime)
- Environments: {list of environments with Route53 records}
- Initial weights: SRE-EKS=100, Sonic Runtime=0 (no traffic shift yet)

## Jira

[{JIRA}](https://justeattakeaway.atlassian.net/browse/{JIRA})

## Next Steps

After merging, gradually adjust weights to shift traffic to Sonic Runtime.
```

## Repository 3: cps/helm-core (Istio Ingress customRules)

**When**: Service uses any DNS record beyond E-record and NG-record on the Istio ingress. This includes:

- Regional records (R-record)
- Global records (G-record)
- Brand domains (e.g., `api.takeaway.com`) — brand domain traffic hits the ingress directly via Cloudflare

`jet-external.com` does NOT require customRules — external API traffic is proxied through SmartGateway to the internal NG-record, so the Istio ingress only sees `jet-internal.com` host headers.

Only E-records and NG-records are auto-provisioned via the `igw-<project>` gateway wildcard. All other hostnames on the ingress require explicit `customRules`.

**What**: Add `customRules` to the Istio ingress gateway configuration for `igw-<project>` so it accepts traffic for the additional hostname(s).

**How**: Clone the repo, explore `clusters/` directory to find the istio-gateways config files, and follow existing customRules patterns.

> **Critical — Same Ingress Requirement**: customRules MUST be added to the **same ingress** entry as the project's wildcard rules (the `igw-{project}` gateway). Each ingress in `istio-gateways.yaml.gotmpl` creates a separate AWS ALB. R-records and G-records CNAME to the E-record, which resolves to the ALB of the igw wildcard's ingress. If customRules are placed on a different ingress, the CNAME chain delivers traffic to the wrong ALB and routing fails silently.

> **Critical**: The hostnames in `customRules` must exactly match the DNS record names and VirtualService `hosts`. Run Section 5.8 consistency validation (DNS ↔ helm-core ↔ VirtualService) before creating this PR. See `05-dns-and-networking.md` for the Host Header Routing Chain reference.

**PR body template**:

```markdown
## Summary

- Add Istio ingress customRules for {APP_NAME} on igw-{project-id}
- Hostnames: {list of hostnames added to customRules}

## Jira

[{JIRA}](https://justeattakeaway.atlassian.net/browse/{JIRA})

## Environments

{list of clusters updated}
```

## Repository 4: Consul Repository (Backward Compatibility)

**When**: User wants SRE-EKS services to continue reaching the migrated service at its `.service` address.

**What**: Add entries to the `oneeks_migrated_services` configuration map.

**How**: Fetch current format from Backstage (see `06-consul-bridge.md`). Apply to both staging and production configs.

**PR body template**:

```markdown
## Summary

- Register {service-name} in oneeks_migrated_services for Consul backward compatibility
- Enables SRE-EKS services to reach {service-name} at its .service address after migration

## Jira

[{JIRA}](https://justeattakeaway.atlassian.net/browse/{JIRA})

## Configuration

- Port: {port}
- Health check: {health-check-path}
- Namespace: {namespace}
```

## Repository 5: Domain-Routing Repository (Brand Domains)

**When**: Service is accessible on a brand domain (e.g., `takeaway.com`).

**What**: Add weighted endpoint entries for traffic splitting on brand domains, update Cloudflare DNS records, and verify/update WAF rules.

**How**: Clone the `IFA/domain-routing` repo, explore its structure for the current schemas. Generate:

- Weighted endpoints in the appropriate config file
- Cloudflare DNS record update in `vars/records/cloudflare/{domain}.yaml` (if Cloudflare is used)
- WAF rule additions/updates in `vars/domains/waf.yml` (if needed)

**PR body template**:

```markdown
## Summary

- Add weighted endpoint for {service-name} brand domain traffic split
- Brand domain: {brand-domain}
- Initial weights: SRE-EKS=100, Sonic Runtime=0
- Update Cloudflare DNS origin endpoint (if applicable)
- Add/update WAF allow rules (if applicable)

## Jira

[{JIRA}](https://justeattakeaway.atlassian.net/browse/{JIRA})

## Changes

- Weighted endpoint: `{brand-domain}` → SRE-EKS (100) / Sonic Runtime (0)
- Cloudflare: {Updated origin / No change needed}
- WAF: {New allow rule / Updated existing rule / No change needed}
```

## Repository 6: SmartGateway Configuration (External Services)

**When**: DNS Path Discovery (Phase 4) confirmed that the service has **external internet-facing endpoints** routed through SmartGateway (Kong). This is NOT triggered by brand domains alone — brand domains used internally (direct Cloudflare → Istio, no SmartGateway in the path) do not need SmartGateway configuration.

**What**: Add SmartGateway (Kong Gateway) route configuration to enable external internet traffic to reach the service.

**How**: Clone `external-api-services/smartgatewayconfiguration`, explore `Data/Global/` for existing config files and schema patterns. Generate a `.json.hbs` config file that routes external traffic to the service's internal NG-record.

**Important**: SmartGateway `host` must use the **NG-record** (not E-record), `port` must be `443`, and `protocol` must be `"https"`.

**PR body template**:

```markdown
## Summary

- Add SmartGateway route configuration for {service-name}
- Routes external traffic to internal NG-record: {ng-record}
- SmartGateway environments: {environment-list}

## Jira

[{JIRA}](https://justeattakeaway.atlassian.net/browse/{JIRA})

## Testing

Please deploy to QA first (ad-hoc deploy) and test via SmartGateway regional endpoints.

## Configuration

- Host: {ng-record}
- Port: 443
- Protocol: https
- Routes: {route-paths}
```

**Review**: Request review in `#help-http-integrations` on Slack.

## Repository 7: API Specifications (External Services, No Existing Spec)

**When**: Service is externally exposed AND the user doesn't have an existing BOATS OpenAPI spec.

**What**: Add a placeholder OpenAPI v3 specification in BOATS format for the service's external API.

**How**: Clone `api_specifications`, explore `src/paths/` for existing spec examples and the current BOATS format. Generate a spec based on the service's detected routes.

**Important**: This is a **placeholder** — the user must review, refine, and get approval from the API Design Guild before the external endpoint goes live.

**PR body template**:

```markdown
## Summary

- Add placeholder OpenAPI v3 spec for {service-name} in BOATS format
- This is a draft spec for review by the API Design Guild

## Jira

[{JIRA}](https://justeattakeaway.atlassian.net/browse/{JIRA})

## Note

This is a placeholder specification generated during the SRE-EKS to Sonic Runtime migration.
Please review and refine the request/response schemas before approving.

## Endpoints

{list-of-external-endpoints}
```

**Review**: Request review from the API Design Guild in `#api-guild-design` on Slack.

## PR Creation Strategy (3-Tier Fallback)

For each repository, attempt the following tiers in order:

### Tier 1: Direct Push (preferred)

```
1. Clone: gh repo clone github.je-labs.com/{org}/{repo} /tmp/{repo}
2. Branch: git checkout -b {JIRA}-migrate-{service}-to-sonic
3. Explore repo structure to find correct files and existing patterns
4. Apply changes following the repo's conventions
5. Commit: git add . && git commit -m "{JIRA}: Migrate {service} to Sonic Runtime"
6. Push: git push -u origin {JIRA}-migrate-{service}-to-sonic
7. PR: gh pr create --title "..." --body "..."
```

### Tier 2: Fork and PR from Fork (if Tier 1 push fails)

If step 6 (push) fails with a permissions error:

```
1. Fork: gh repo fork github.je-labs.com/{org}/{repo} --clone --remote
2. Branch: git checkout -b {JIRA}-migrate-{service}-to-sonic
3. Apply the same changes as Tier 1
4. Commit and push to fork: git push -u origin {JIRA}-migrate-{service}-to-sonic
5. PR from fork: gh pr create --title "..." --body "..." --head {your-username}:{branch}
```

Tell the user: "I created a PR from a fork of `{org}/{repo}`. The repo owners will need to approve the fork PR."

### Tier 3: Manual Diffs (if Tier 2 also fails)

If forking also fails (e.g., org policy disallows forks):

- Output the **full diff/patch** that the user can apply manually
- Provide the exact file paths and content to add/modify
- Include the PR title and body template for the user to create the PR themselves
- Tell the user which Slack channel to request review in (see table below)

### Review Channels per Repository

| Repository                                        | Slack Channel                  |
| ------------------------------------------------- | ------------------------------ |
| `cps/helm-core`                                   | `#help-core-platform-services` |
| `IFA/route53`                                     | `#help-infra-foundations-aws`  |
| `IFA/domain-routing`                              | `#help-infra-foundations-aws`  |
| `IFA/cloudflareplatformproduction`                | `#help-infra-foundations-aws`  |
| `IFA/cloudflareplatformstaging`                   | `#help-infra-foundations-aws`  |
| `external-api-services/smartgatewayconfiguration` | `#help-http-integrations`      |
| `api_specifications`                              | `#api-guild-design`            |
| Source app repo                                   | Team's own review process      |
