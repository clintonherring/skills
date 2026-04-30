# Backstage TechDocs Search Reference

## Overview

Use Backstage TechDocs search to fetch current platform documentation at runtime. Do NOT rely
solely on hardcoded content in reference files — always verify against Backstage for the latest
information.

## Query Template

```bash
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "$BACKSTAGE_BACKEND_URL/api/search/query?term={SEARCH_TERM}&types%5B0%5D=techdocs" \
  | jq '.results[:5][] | {title: .document.title, text: .document.text[:500]}'
```

For results with clickable URLs:

```bash
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "$BACKSTAGE_BACKEND_URL/api/search/query?term={SEARCH_TERM}&types%5B0%5D=techdocs" \
  | jq '.results[:3][] | {title: .document.title, url: "'"$BACKSTAGE_UI_URL"'\(.document.location)", text: .document.text[:500]}'
```

Software catalog lookup (components, APIs):

```bash
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "$BACKSTAGE_BACKEND_URL/api/search/query?term={service-name}" | \
  jq '.results[]?.document | select(.kind == "Component")'
```

---

## Migration-Related Search Terms

| Search Term | What to Fetch |
|---|---|
| `cloudops sonic runtime migration` | Migration steps, DNS, ingress |
| `cloudops sonic runtime traffic split` | Traffic split, Route53, weighted routing |
| `sonic pipeline prerequisites` | Eligibility criteria, supported runtimes |
| `sonic.yml configuration` | sonic.yml spec per runtime |
| `configure workload spec sonic` | Full sonic.yml structure, apiVersion, metadata, environments, workloads |
| `configure workload tests sonic` | Test types (unit/integration/e2e/acceptance), runtime-specific examples |
| `onboard existing component sonic` | Migration guide for onboarding existing services to Sonic Pipeline |
| `sonic spec reference` | Available apiVersion values and their status |
| `sonic environments and accounts` | Valid cluster identifiers for environments |
| `deploy with argocd sonic` | ArgoCD deployment method, helmOverrides, feature branches |
| `euw1-pdv bulkhead eu2 environments` | All Sonic Runtime environments with bulkhead assignments and AWS account IDs |
| `CloudOps sonic runtime environment mapping` | CloudOps-EKS → Sonic Runtime environment mapping |

## DNS & Networking Search Terms

| Search Term | What to Fetch |
|---|---|
| `expose service internally oneeks` | VirtualService config, gateway patterns, E/NG-records |
| `expose service externally oneeks` | SmartGateway setup, external ingress |
| `dns service discovery specification` | DNS record type formats (E/R/G/NG) |
| `cloudflare expose endpoint` | Cloudflare proxied CNAME, WAF rules, page rules |
| `helm-core customRules istio gateway` | Istio gateway customRules configuration |

## Vault & OneSecrets Search Terms

| Search Term | What to Fetch |
|---|---|
| `onesecrets vault oneeks` | OneSecrets setup, Vault sidecar injection |
| `use onesecrets` | OneSecrets usage guide, KV v2 paths |
| `vault migration oneeks sonic` | Vault migration patterns, legacy to OneSecrets |
| `extra_policy_ro vault` | Extra read policies for legacy secret access |
| `vault sidecar injection kubernetes` | Vault agent injector annotations |

## External Services Search Terms

| Search Term | What to Fetch |
|---|---|
| `smartgateway configuration kong` | SmartGateway JSON config schema, environments |
| `expose service externally oneeks` | External exposure, SmartGateway setup |

## Messaging & MeX Search Terms

| Search Term | What to Fetch |
|---|---|
| `messaging applications migration sonic` | MeX process, AsyncAPI spec |

## Phase 5.5 Interactive Q&A Search Terms

When the user asks a question during the review phase, use these search terms:

| Question Topic | Backstage Search Term |
|---|---|
| E-records, NG-records, internal DNS | `expose service internally oneeks` |
| External exposure, SmartGateway | `expose service externally oneeks` |
| Traffic splitting | `cloudops sonic runtime traffic split` |
| Sonic Pipeline setup | `sonic pipeline prerequisites` |
| helm-core / Istio gateway | `helm-core customRules istio gateway` |
| Cloudflare / brand domains | `cloudflare expose endpoint` |
| DNS record formats | `dns service discovery specification` |
| Vault / secrets | `onesecrets vault oneeks` |
| Legacy secret access | `use onesecrets` |

Present a summary of the relevant documentation and include the Backstage URL for further reading.

---

## Backstage Documentation Links

Direct links to Backstage TechDocs pages. If a link returns 404, search Backstage with the
topic name — pages may have been reorganized.

| Topic | URL |
|-------|-----|
| CloudOps Migration Guide | https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/oneeks/tasks/platform-transition/cloudops/ |
| Traffic Split Guide | https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/oneeks/tasks/platform-transition/cloudops/cloudops-sonic-runtime-traffic-split/ |
| Getting Started | https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/oneeks/getting-started/ |
| Expose Service Internally | https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/oneeks/tasks/networking/expose-service-internally/ |
| Expose Service Externally | https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/oneeks/tasks/networking/expose-service-externally/ |
| OneSecrets | https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/oneeks/tasks/manage-secrets/ |
| Read Secrets from CloudOps | https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/oneeks/tasks/manage-secrets/read-secrets-from-oneeks-vault-in-cloudops/ |
| OneConfig Tutorial | https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/oneeks/tutorials/manage-config-with-helmfile/ |
| Workload Roles | https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/oneeks/tasks/use-cloud-resources/ |
| Bulkheads | https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/oneeks/concepts/bulkheads/ |
| Onboard Application | https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/oneeks/getting-started/ |
| Helm Chart Setup | https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/oneeks/getting-started/onboard-an-application/helm-chart-setup/ |
| Slack Support | #help-sonic |

---

## GitHub Enterprise Repositories

Authoritative sources for current schemas, versions, and patterns:

| Repo | Command | What to Fetch |
|---|---|---|
| **basic-application chart** | `gh api --hostname github.je-labs.com /repos/helm-charts/basic-application/releases/latest \| jq '.tag_name'` | Current chart version |
| **basic-application schema** | Clone `helm-charts/basic-application`, read `values.yaml`, `CHANGELOG.md` | Config schema, breaking changes |
| **Goldenpath template** | Clone `justeattakeaway-com/goldenpath` | Current directory structure, workflow patterns, environment names |
| **helm-core** | Clone `cps/helm-core` (when customRules needed) | Current igw config file structure |
| **Route53** | Clone `IFA/route53` (when traffic split needed) | Current terraform patterns |
| **Domain-Routing** | Clone `IFA/domain-routing` (when brand domain) | Cloudflare DNS, WAF rules, weighted endpoints |
| **Cloudflare Platform** | Clone `IFA/cloudflareplatformproduction` / `IFA/cloudflareplatformstaging` | Cloudflare WAF/page rules |
| **SmartGateway** | Clone `external-api-services/smartgatewayconfiguration` (when external) | SmartGateway JSON config schema |
| **API Specifications** | Clone `Architecture/api_specifications` (when external, no BOATS spec) | BOATS format, existing spec examples |
| **Vault infra** | Clone `cps/vault` | App Vault configs (`vars/apps/{env}/{app}.yml`), auth/secret backends |
| **Projects** | Clone `cps/projects` | Project definitions, `onesecrets.extra_policy_ro`, workload roles |

---

## Key Rule

Reference files contain **procedural logic** (detection patterns, scoring, decision trees,
interactive prompts) and **structural hints** (directory layouts, conceptual explanations).
For any specific versions, formats, schemas, or configuration patterns — **fetch from source**.

---

## Gotchas & Edge Cases

> Accumulated wisdom from migrations. These are NOT duplicated in other reference files.

1. **QA environments matter too** — Route53 records are needed for QA and staging, not just production
2. **DNS ↔ Helm-Core sync** — Every Route53 entry must have a matching `customRules` in helm-core, and vice versa (see `09-consistency-validation.md`)
3. **Permission denied on repos** — Fork and create PR from fork when direct push not allowed
4. **Sonic Pipeline eliminates GHA** — If eligible, do NOT create GitHub Actions workflows (maybe backup copy only)
5. **SmartGateway scope** — Only for external-facing APIs; internal services don't need it (see `05b-dns-reference.md`)
6. **Same AWS account advantage** — CloudOps EU1 and Sonic Runtime EU1 share an account, simplifying IAM
7. **EU2 is in eu-west-1** — Same AWS region as EU1, NOT eu-west-2. The bulkhead number differentiates them.
8. **Brand domain DNS: always search parent domain too** — When looking for brand domain records, search for both the subdomain AND the parent domain in `IFA/route53` and `IFA/domain-routing`. Brand domains can be in either or both repos. Searching only for the subdomain will miss the records file.
9. **Brand domain traffic split happens on the brand domain** — When keeping a brand domain, traffic split must happen on the brand domain itself (weighted records in route53 or domain-routing). Only add NG-records if the service actually needs a `jet-internal.com` address. Keep runtime migration focused on the runtime, keep client hosts the same.

---

