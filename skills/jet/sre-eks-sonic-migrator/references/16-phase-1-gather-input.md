# Phase 1: Gather Input

**Goal**: Identify the service and access its source code.

> **Tooling**: PlatformMetadata lookups and `gh repo clone` in this phase use patterns from
> **`jet-company-standards`**. Refer to that skill for auth setup and troubleshooting.

1. Ask: **"What is the name of the service you want to migrate?"**

2. Ask: **"What is the GitHub repository for this service?"**
   - If only a component name is provided, look up in PlatformMetadata:

     ```bash
     gh api --hostname github.je-labs.com /repos/metadata/PlatformMetadata/contents/Data/global_features/{COMPONENT}.json | jq -r '.content' | base64 -d
     ```

3. **Validate app name against PlatformMetadata**:

   The canonical application name is the filename (without `.json`) in `PlatformMetadata/Data/global_features/`. This name may differ from the repo name (e.g., repo `food-tracker-status-service` → PlatformMetadata `foodtrackerstatusservice`). All generated configs, DNS records, PR branches, and file names must use this canonical name.

   ```bash
   gh api --hostname github.je-labs.com /repos/metadata/PlatformMetadata/contents/Data/global_features/{service-name}.json | jq -r '.content' | base64 -d
   ```

   - **If found**: Store the filename (without `.json`) as `APP_NAME`. Confirm with the user:

     > "Your application is registered in PlatformMetadata as **{APP_NAME}**. This name will be used for DNS records, helm config, PR branches, and all generated files."

   - **If NOT found** (404): Try common variations — lowercase, remove hyphens, remove underscores, combine words. Also search for close matches:

     ```bash
     gh api --hostname github.je-labs.com /repos/metadata/PlatformMetadata/contents/Data/global_features | jq -r '.[].name' | grep -i '{partial-match}'
     ```

     Present candidates to the user:

     > "I couldn't find `{service-name}.json` in PlatformMetadata. Did you mean one of these?"
     >
     > - {candidate-1}
     > - {candidate-2}

   - **If still not found**: Warn and ask for the exact name:
     > "I couldn't find your service in PlatformMetadata. The app name must match the filename in `PlatformMetadata/Data/global_features/`. Please check with your team and provide the exact name."
     >
     > If this is a brand-new service that hasn't been registered in PlatformMetadata yet, you can proceed with a manually specified name, but be aware that some platform integrations may not work until the PlatformMetadata entry exists.

   `APP_NAME` is used throughout the rest of the workflow for: DNS records, helm/helmfile values (`app.name`), SmartGateway config, Consul bridge entries, PR branch names (`{JIRA}-migrate-{APP_NAME}-to-sonic`), PR titles, and generated file names. It may differ from the repo name.

4. Clone the repository:

   ```bash
   gh repo clone github.je-labs.com/{org}/{repo} /tmp/{repo}
   ```

5. Ask: **"What is the Sonic Runtime project name for this service?"**
   - The project ID is used directly as the Kubernetes namespace (e.g., project `cu-order-reviews` → namespace `cu-order-reviews`). There is no prefix — use it as-is in DNS records and all configs.
   - If unknown: "The project was created during Sonic Runtime onboarding. It typically looks like `<process-group-prefix>-<chosen-suffix>` (e.g., `cu-order-reviews`). Check with your team lead or `#help-sonic` on Slack if unsure."

6. **Validate project exists** by checking `cps/projects`:

   ```bash
   gh repo clone github.je-labs.com/cps/projects /tmp/cps-projects -- --depth 1
   ```

   Then check for the project definition. **Important**: Projects in `cps/projects` are organized in nested directory structures (e.g., `projects/{env-function}/{project-id}.yml` or `workloads/env-function/{project-id}.yml`). Do NOT only check the top-level `projects/` directory. Use `find` to search recursively:

   ```bash
   find /tmp/cps-projects -name "{project-id}*" 2>/dev/null
   ```

   This will find matches like `projects/pdv/or-fulfill-rd.yml` or `workloads/pdv/or-fulfill-rd.yml` that a simple `ls projects/{project-id}/` would miss.
   - **If found** (as a file or directory at any depth): The project is onboarded. Confirm to the user:
     > "Verified: project **{project-id}** exists in `cps/projects`."
   - **If NOT found** anywhere in the repo: The project hasn't completed Sonic Runtime onboarding. Warn the user:
     > "I couldn't find project **{project-id}** in `cps/projects`. This means Sonic Runtime onboarding may not be complete. You need to complete onboarding before migrating. See the [Getting Started guide](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/oneeks/getting-started/)."
     >
     > "Would you like to proceed anyway (if onboarding is in progress), or pause until onboarding is complete?"

   Store `PROJECT_ID` for use throughout the workflow.

7. Ask for the **Jira ticket** for this migration (for PR descriptions and commits).
