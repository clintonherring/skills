# Phase 5.5: Review & Confirm

**Goal**: Present all generated changes to the user for review before creating any PRs. This is the gate between generating code and creating PRs.

## 5.5.1 Summary Table

Present a summary of all repos that will receive PRs:

> **Migration Changes Summary for {service-name}**
>
> | #   | Repository                              | Files                                                    | Description                                   |
> | --- | --------------------------------------- | -------------------------------------------------------- | --------------------------------------------- |
> | 1   | `{org}/{app-repo}`                      | `helmfile.d/`, `.sonic/sonic.yml`, ...                   | Goldenpath restructure, Sonic Pipeline config |
> | 2   | `IFA/route53`                           | `{zone-file}.tf`                                         | R-record DNS records for QA, STG, PRD         |
> | 3   | `cps/helm-core`                         | `clusters/{cluster}/releases/istio-gateways.yaml.gotmpl` | customRules for R-record on igw-{project}     |
> | 4   | `cps/projects` (if NEEDS_WORKLOAD_ROLE) | `workloads/pdv/{PROJECT_ID}.yaml`                        | Workload Role for cross-account AWS access    |
> | ... | ...                                     | ...                                                      | ...                                           |
>
> **DNS Consistency**: All hosts validated (see table above).

## 5.5.2 User Options

> "Here is a summary of all changes I will create PRs for. You can:"
>
> - **Approve all** — I'll create PRs now
> - **Review a specific file** — Tell me which file to show in full detail
> - **Request changes** — Describe what to adjust; I'll regenerate
> - **Ask a question** — I can explain any config choice and look up Backstage documentation
> - **Cancel** — Abort PR creation

## 5.5.3 Interactive Q&A

If the user asks a question about the generated configuration, dynamically search Backstage TechDocs:

```bash
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "$BACKSTAGE_BACKEND_URL/api/search/query?term={RELEVANT_SEARCH_TERM}&types%5B0%5D=techdocs" \
  | jq '.results[:3][] | {title: .document.title, url: "'"$BACKSTAGE_UI_URL"'\(.document.location)", text: .document.text[:500]}'
```

For suggested search terms by topic, see [13-backstage-queries.md](13-backstage-queries.md).

Present a summary of the relevant documentation and include the Backstage URL for further reading. Continue answering questions and applying requested changes until the user explicitly approves.

**Only after explicit user approval does Phase 6 execute.**
