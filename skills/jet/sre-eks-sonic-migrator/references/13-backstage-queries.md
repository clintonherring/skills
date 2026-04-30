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

## Migration-Related Search Terms

| Search Term                           | What to Fetch                                                           |
| ------------------------------------- | ----------------------------------------------------------------------- |
| `sre-eks sonic runtime migration`     | Migration steps, DNS, ingress, Consul bridge                            |
| `sre-eks sonic runtime traffic split` | Traffic split, Route53, Consul advertising                              |
| `sonic pipeline prerequisites`        | Eligibility criteria, supported runtimes                                |
| `sonic.yml configuration`             | sonic.yml spec per runtime                                              |
| `configure workload spec sonic`       | Full sonic.yml structure, apiVersion, metadata, environments, workloads |
| `configure workload tests sonic`      | Test types (unit/integration/e2e/acceptance), runtime-specific examples |
| `onboard existing component sonic`    | Migration guide for onboarding existing services to Sonic Pipeline      |
| `sonic spec reference`                | Available apiVersion values and their status                            |
| `sonic environments and accounts`     | Valid cluster identifiers for environments                              |
| `deploy with argocd sonic`            | ArgoCD deployment method, helmOverrides, feature branches               |

## DNS & Networking Search Terms

| Search Term                           | What to Fetch                                         |
| ------------------------------------- | ----------------------------------------------------- |
| `expose service internally oneeks`    | VirtualService config, gateway patterns, E/NG-records |
| `expose service externally oneeks`    | SmartGateway setup, external ingress                  |
| `dns service discovery specification` | DNS record type formats (E/R/G/NG)                    |
| `cloudflare expose endpoint`          | Cloudflare proxied CNAME, WAF rules, page rules       |
| `helm-core customRules istio gateway` | Istio gateway customRules configuration               |

## Consul & Messaging Search Terms

| Search Term                              | What to Fetch                   |
| ---------------------------------------- | ------------------------------- |
| `advertising in consul oneeks`           | oneeks_migrated_services format |
| `messaging applications migration sonic` | MeX process, AsyncAPI spec      |

## Vault & OneSecrets Search Terms

| Search Term                          | What to Fetch                                  |
| ------------------------------------ | ---------------------------------------------- |
| `onesecrets vault oneeks`            | OneSecrets setup, Vault sidecar injection      |
| `use onesecrets`                     | OneSecrets usage guide, KV v2 paths            |
| `vault migration oneeks sonic`       | Vault migration patterns, legacy to OneSecrets |
| `extra_policy_ro vault`              | Extra read policies for legacy secret access   |
| `vault sidecar injection kubernetes` | Vault agent injector annotations               |

## External Services Search Terms

| Search Term                        | What to Fetch                                 |
| ---------------------------------- | --------------------------------------------- |
| `smartgateway configuration kong`  | SmartGateway JSON config schema, environments |
| `expose service externally oneeks` | External exposure, SmartGateway setup         |

## Phase 5.5 Interactive Q&A Search Terms

When the user asks a question during the review phase, use these search terms:

| Question Topic                      | Backstage Search Term                 |
| ----------------------------------- | ------------------------------------- |
| E-records, NG-records, internal DNS | `expose service internally oneeks`    |
| External exposure, SmartGateway     | `expose service externally oneeks`    |
| Traffic splitting                   | `sre-eks sonic runtime traffic split` |
| Sonic Pipeline setup                | `sonic pipeline prerequisites`        |
| helm-core / Istio gateway           | `helm-core customRules istio gateway` |
| Cloudflare / brand domains          | `cloudflare expose endpoint`          |
| Consul bridge                       | `advertising in consul oneeks`        |
| DNS record formats                  | `dns service discovery specification` |
| Vault / secrets                     | `onesecrets vault oneeks`             |
| Legacy secret access                | `use onesecrets`                      |

Present a summary of the relevant documentation and include the Backstage URL for further reading.

## GitHub Enterprise Repositories

These repositories are authoritative sources for current schemas, versions, and patterns:

| Repo                         | Command                                                                                                       | What to Fetch                                                                   |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| **basic-application chart**  | `gh api --hostname github.je-labs.com /repos/helm-charts/basic-application/releases/latest \| jq '.tag_name'` | Current chart version                                                           |
| **basic-application schema** | Clone `helm-charts/basic-application`, read `values.yaml`, `CHANGELOG.md`, `MIGRATION*.md`                    | Config schema, breaking changes                                                 |
| **Goldenpath template**      | Clone `justeattakeaway-com/goldenpath`                                                                        | Current directory structure, workflow patterns, environment names               |
| **GHA Pipelines**            | Explore `github-actions/pipelines` repo                                                                       | Current reusable workflow versions                                              |
| **helm-core**                | Clone `cps/helm-core` (when customRules needed — R-record or brand domain)                                    | Current igw config file structure                                               |
| **Route53**                  | Clone `IFA/route53` (when traffic split needed)                                                               | Current terraform patterns                                                      |
| **Domain-Routing**           | Clone `IFA/domain-routing` (when brand domain)                                                                | Cloudflare DNS, WAF rules, weighted endpoints                                   |
| **Cloudflare Platform**      | Clone `IFA/cloudflareplatformproduction` and `IFA/cloudflareplatformstaging` (when Cloudflare detected)       | Cloudflare WAF rules, page rules, origin overrides                              |
| **SmartGateway**             | Clone `external-api-services/smartgatewayconfiguration` (when external)                                       | Current SmartGateway JSON config schema                                         |
| **API Specifications**       | Clone `Architecture/api_specifications` (when external, no BOATS spec)                                        | BOATS format, existing spec examples                                            |
| **Vault infra**              | Clone `cps/vault`                                                                                             | App Vault configs (`vars/apps/{env}/{app}.yml`), auth backends, secret backends |
| **Projects (Vault)**         | Clone `cps/projects`                                                                                          | Project definitions with `onesecrets.extra_policy_ro`, workload roles           |

## Key Rule

Reference files contain **procedural logic** (detection patterns, scoring, decision trees,
interactive prompts) and **structural hints** (directory layouts, conceptual explanations).
For any specific versions, formats, schemas, or configuration patterns — **fetch from source**.
