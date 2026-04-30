# Phase 1: Gather Input

**Goal**: Identify the service, validate it in PlatformMetadata, clone its source code, confirm the Sonic Runtime project, and collect Jira context.

> **Tooling**: PlatformMetadata lookups and `gh repo clone` in this phase use patterns from
> **`jet-company-standards`**. Refer to that skill for auth setup and troubleshooting.

---

## Step 1: Service Name

Ask: **"What is the name of the service you want to migrate?"**

Store as `SERVICE_NAME`.

---

## Step 2: GitHub Repository

Ask: **"What is the GitHub repository for this service?"**

- If only a component name is provided (or the user says "find it"), look it up in PlatformMetadata (Step 3 will do this).
- If the user gives `{org}/{repo}`, store it and proceed.

---

## Step 3: Validate APP_NAME against PlatformMetadata

The canonical application name is the **filename** (without `.json`) in `PlatformMetadata/Data/global_features/`. This name may differ from the repo name (e.g., repo `food-tracker-status-service` → PlatformMetadata `foodtrackerstatusservice`). All generated configs, DNS records, PR branches, and file names must use this canonical name.

### 3a. Direct lookup

```bash
gh api --hostname github.je-labs.com \
  /repos/metadata/PlatformMetadata/contents/Data/global_features/{SERVICE_NAME}.json \
  --jq '.content' | base64 -d | jq .
```

### 3b. If found

Store the filename (without `.json`) as `APP_NAME`. Extract key metadata:

| Field | Source |
|-------|--------|
| `APP_NAME` | Filename without `.json` |
| `GITHUB_ORG` | `.github_repository.owner` |
| `GITHUB_REPO` | `.github_repository.name` |
| `TEAM` | `.owners` |
| `TIER` | `.tier` |

Confirm with the user:

> "Your application is registered in PlatformMetadata as **{APP_NAME}**. This name will be used for DNS records, helm config, PR branches, and all generated files."

### 3c. If NOT found (404)

Try common variations — lowercase, remove hyphens, remove underscores, combine words. Also search for close matches:

```bash
gh api --hostname github.je-labs.com \
  /repos/metadata/PlatformMetadata/contents/Data/global_features \
  --jq '.[].name' | grep -i '{partial-match}'
```

Present candidates to the user:

> "I couldn't find `{SERVICE_NAME}.json` in PlatformMetadata. Did you mean one of these?"
>
> - {candidate-1}
> - {candidate-2}

### 3d. If still not found

Warn and ask for the exact name:

> "I couldn't find your service in PlatformMetadata. The app name must match the filename in `PlatformMetadata/Data/global_features/`. Please check with your team and provide the exact name."
>
> If this is a brand-new service that hasn't been registered yet, you can proceed with a manually specified name, but be aware that some platform integrations may not work until the PlatformMetadata entry exists.

### Where APP_NAME is used

`APP_NAME` is used throughout the rest of the workflow for:
- DNS records (E-records, NG-records)
- Helm values (`app.name`)
- SmartGateway config
- PR branch names (`{JIRA}-migrate-{APP_NAME}-to-sonic`)
- PR titles
- Generated file names
- VirtualService names

It **may differ** from the repo name.

---

## Step 4: Clone the Repository

```bash
gh repo clone github.je-labs.com/{GITHUB_ORG}/{GITHUB_REPO} /tmp/migration-{APP_NAME}
```

If `GITHUB_ORG` and `GITHUB_REPO` weren't set from PlatformMetadata, ask the user for the full `{org}/{repo}` path.

---

## Step 5: Sonic Runtime Project Name

Ask: **"What is the Sonic Runtime project name for this service?"**

Context for the user if they don't know:
> "The project ID is used directly as the Kubernetes namespace (e.g., project `cu-order-reviews` → namespace `cu-order-reviews`). There is no prefix — use it as-is in DNS records and all configs."
>
> "The project was created during Sonic Runtime onboarding. It typically looks like `<process-group-prefix>-<chosen-suffix>` (e.g., `cu-order-reviews`). Check with your team lead or `#help-sonic` on Slack if unsure."

### Auto-discovery (if user doesn't know)

If the user doesn't know the project name, find it for them:

1. Look up the team name from PlatformMetadata (Step 3).
2. Search `cps/projects` for projects owned by that team:
   ```bash
   gh api --hostname github.je-labs.com /repos/cps/projects/contents/projects/pdv \
     --jq '.[].name'
   ```
3. For each candidate, fetch the file and check the `team.name` field:
   ```bash
   gh api --hostname github.je-labs.com \
     /repos/cps/projects/contents/projects/pdv/{candidate}.yml \
     --jq '.content' | base64 -d | grep -A1 "team:"
   ```
4. **Present matching projects WITH their validation status** (run Step 6 checks inline):

   For each matching project, check project definition, workloads, and bulkheads — then present a summary table:

   > "I found the following Sonic Runtime projects owned by team **{TEAM}**:"
   >
   > | Project | Onboarded | Workloads | Bulkheads | EU1? |
   > |---------|-----------|-----------|-----------|------|
   > | `cu-payment-paycore` | ✅ Yes | ❌ None | eu1, eu2, na1, oc1 | ✅ |
   > | `cu-fintech-par` | ✅ Yes | ❌ None | eu1, eu2, na1, oc1 | ✅ |
   >
   > **"Which project should consumer-email-dispatcher be deployed to?"**

5. If **no matching projects found**, the service may not be onboarded yet:
   > "I couldn't find any Sonic Runtime projects owned by team **{TEAM}** in `cps/projects`. This means Sonic Runtime onboarding may not be complete. You need to complete onboarding before migrating. See the [Getting Started guide](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/oneeks/getting-started/)."
   >
   > "Would you like to proceed anyway (if onboarding is in progress), or pause until onboarding is complete?"

Once the user picks a project (or provides one directly), proceed to Step 6 for full validation.

---

## Step 6: Validate Project in cps/projects

Run all three checks and present results together. **Always end with a clear verdict.**

### 6a. Check project definition exists

```bash
gh api --hostname github.je-labs.com \
  /repos/cps/projects/contents/projects/pdv/{PROJECT_ID}.yml \
  --jq '.content' | base64 -d
```

### 6b. Check workload definition exists

```bash
gh api --hostname github.je-labs.com \
  /repos/cps/projects/contents/workloads/pdv/{PROJECT_ID}.yml \
  --jq '.content' | base64 -d
```

### 6c. Check bulkheads include eu1

From the project YAML, extract the `bulkheads` list. Verify it includes `eu1` (required for CloudOps EU migrations).

### Present validation result

Always present a clear summary:

> **Project Validation: {PROJECT_ID}**
>
> | Check | Status | Detail |
> |-------|--------|--------|
> | Project definition (`projects/pdv/`) | ✅ Found | Onboarded to Sonic Runtime |
> | Workload roles (`workloads/pdv/`) | ❌ Not found | Will create in Phase 5 |
> | EU1 bulkhead | ✅ Included | Required for CloudOps migration |
>
> "Verified: project **{PROJECT_ID}** exists in `cps/projects` and is configured for EU1."

**If project definition NOT found (404)**:
> "I couldn't find project **{PROJECT_ID}** in `cps/projects`. This means Sonic Runtime onboarding may not be complete. You need to complete onboarding before migrating. See the [Getting Started guide](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/oneeks/getting-started/)."
>
> "Would you like to proceed anyway (if onboarding is in progress), or pause until onboarding is complete?"

**If EU1 bulkhead missing**:
> "Project **{PROJECT_ID}** does not include the `eu1` bulkhead. CloudOps services run in EU1, so the project must be configured for `eu1`. This needs to be added to `cps/projects` before proceeding."

**If workloads not found**: Note this for Phase 5 — a workload role will need to be created if the service requires AWS access (Vault secrets, SQS, S3, etc.).

Store `PROJECT_ID` and `PROJECT_BULKHEADS` for use throughout the workflow.

---

## Step 7: Jira Ticket

Ask: **"What is the Jira ticket for this migration?"** (e.g., `CPS-1234`)

- This is used for PR descriptions, commit messages, and branch naming (`{JIRA}-migrate-{APP_NAME}-to-sonic`).
- If none provided, use default branch naming: `migrate/{APP_NAME}-to-sonic-runtime`.

Store as `JIRA_TICKET`.

---

## Output Summary

At the end of this phase, confirm all collected inputs:

| Variable | Value | Source |
|----------|-------|--------|
| `SERVICE_NAME` | {value} | User input |
| `APP_NAME` | {value} | PlatformMetadata filename |
| `GITHUB_ORG` | {value} | PlatformMetadata |
| `GITHUB_REPO` | {value} | PlatformMetadata or user input |
| `TEAM` | {value} | PlatformMetadata |
| `TIER` | {value} | PlatformMetadata |
| `PROJECT_ID` | {value} | User input, validated in cps/projects |
| `PROJECT_BULKHEADS` | {value} | cps/projects |
| `JIRA_TICKET` | {value} | User input |
| `CLONE_PATH` | `/tmp/migration-{APP_NAME}` | Derived |

> "All inputs collected and validated. Ready to proceed to Phase 2 (Discover)."
