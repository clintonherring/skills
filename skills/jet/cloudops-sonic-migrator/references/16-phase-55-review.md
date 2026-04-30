# Phase 5.5: Review & Confirm

**Goal**: Present all generated changes for user review. This is the gate before PR creation.

## Present Change Summary

Show all generated changes in a table:

> | # | Repository | Files | Description |
> |---|------------|-------|-------------|
> | 1 | `{org}/{repo}` | `helmfile.d/`, `.sonic/sonic.yml` | Goldenpath restructure |
> | 2 | `IFA/route53` | zone files | DNS weighted records |
> | 3 | `cps/helm-core` | `istio-gateways.yaml.gotmpl` | customRules |
> | 4 | `IFA/domain-routing` | endpoint config | Brand domain traffic split |
> | 5 | `cps/projects` | `workloads/pdv/{project}.yml` | Workload Role / Vault access |
> | 6 | SmartGateway | service config | External API routing |

(Only show rows for repos that have changes.)

## User Options

- **Approve all** — proceed to create PRs (Phase 6)
- **Review a specific file** — show full content of any generated file
- **Request changes** — describe modifications, regenerate affected files
- **Ask a question** — answer with explanation + Backstage doc links:
  ```bash
  curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
    "$BACKSTAGE_BACKEND_URL/api/search/query?term={RELEVANT_TERM}&types%5B0%5D=techdocs" \
    | jq '.results[:3][] | {title: .document.title, text: .document.text[:500]}'
  ```
- **Cancel** — abort, no PRs created

**Only explicit approval triggers Phase 6.**
