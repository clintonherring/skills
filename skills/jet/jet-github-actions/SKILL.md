---
name: jet-github-actions
description: |
  JET GitHub Actions skill for writing, debugging, and maintaining CI/CD workflows on GitHub Enterprise Server (GHES).
  Use this skill when:
  - Writing or editing GitHub Actions workflow files (.github/workflows/*.yml)
  - Debugging workflow failures, runner issues, or action version errors
  - Asking about available actions or reusable workflows
  - Working with Artifactory, Vault secrets, Docker builds, Helm/Helmfile deployments
  - Migrating from GitLab, Jenkins, TeamCity, Concourse, or Zuul to GitHub Actions
  - Asking about runners, runner groups, runner images, or SDK versions
  - Asking about GHES-specific constraints, imported actions, or version pinning
  - Setting up GitHub Actions for a new repository or organisation
  - Working with Kubernetes deployments, AWS credentials, or SonarQube integration
metadata:
  owner: continuous-delivery-engineering
---

# JET GitHub Actions

You are an expert in GitHub Actions CI/CD for JET (Just Eat Takeaway), running on **GitHub Enterprise Server (GHES)** at `https://github.je-labs.com`.

## Applicability

This skill applies broadly to **any GitHub Actions workflow authoring** at JET. The only requirement is access to the GHES instance:

```
gh auth status --hostname github.je-labs.com
```

Depending on your workflows, you may also interact with some of these common JET CI/CD tools:

- **Vault** — secrets management (most workflows use this)
- **Artifactory** (`artifactory.justeattakeaway.com`) — package registry and Docker images
- **Helm / Helmfile** — Kubernetes deployments
- **AWS CLI** — AWS credential setup

## Critical Rules — Always Apply These

### 1. No GitHub Connect — Actions Must Be Local

JET does **not** use GitHub Connect. You cannot reference actions from github.com directly. All actions must come from:

- **First-party (built-in)**: `actions/*` at `https://github.je-labs.com/actions`
- **Imported third-party**: `github-actions/*` at `https://github.je-labs.com/github-actions/`
- **In-house custom**: also in `github-actions/*`

To request a new action: [manage-public-actions](https://github.je-labs.com/github-actions/manage-public-actions/issues/new/choose)

### 2. Imported Actions — Version Resolution Gotcha

Some imported actions use a long-lived **branch** (e.g., `v1`) on github.com to define their major version, but only **tags** are mirrored to GHES. If you see this error:

```
Unable to resolve action `github-actions/some-action@v1`, unable to find version `v1`
```

It means the `v1` branch wasn't imported. Fix by using an explicit tag instead:

```diff
- uses: github-actions/some-action@v1
+ uses: github-actions/some-action@v1.0.0  # Use a tag that exists in the GHES mirror
```

Most commonly-used imported actions have working version tags — this mainly affects less popular or newly-imported actions. Check available tags at `https://github.je-labs.com/github-actions/<action-name>/tags`.

### 3. upload-artifact / download-artifact — Pin to v3

`actions/upload-artifact@v4` and `actions/download-artifact@v4` do **NOT** support GHES. Always use **v3**:

```yaml
- uses: actions/upload-artifact@v3
- uses: actions/download-artifact@v3
```

**Verify compliance**: `grep -rn 'artifact@v4' .github/workflows/` — should return no results.

### 4. Vault for Secrets, Not GitHub Secrets

Store sensitive data in **Vault**, not GitHub Secrets. GitHub Secrets are only for non-sensitive project-specific config.

```yaml
- name: Load secrets from vault
  id: secrets
  uses: github-actions/hashicorp-vault-action@v2
  with:
    url: "https://secretsmanagement-eu-west-1-plt-prod-1.eu-west-1.production.jet-internal.com"
    role: pipeline-ci-access
    method: jwt
    path: github-jwt
    exportEnv: false
    secrets: |
      secret/data/eu-west-1-plt-prod-1/githubrunners/all/ci/Secrets ARTIFACTORY_TOKEN
```

### 5. Runners — Self-Hosted Only

Always use self-hosted runners:

```yaml
runs-on: [self-hosted, ubuntu-latest]    # Linux (default)
runs-on: [self-hosted, windows-latest]   # Windows (.NET Framework)
```

Never use `runs-on: ubuntu-latest` without `self-hosted` — there are no GitHub-hosted runners.

**Verify compliance**: `grep -rn 'runs-on:' .github/workflows/ | grep -v 'self-hosted'` — should return no results.

### 6. Prevent Unnecessary Builds

Add fork/bot guards to avoid wasted builds:

```yaml
if: ${{ github.event.repository.fork == false || github.event_name == 'pull_request' }}
```

## Workflow Authoring Guidelines

When writing or reviewing workflows:

1. **Use reusable workflows** from [github-actions/pipelines](https://github.je-labs.com/github-actions/pipelines) whenever possible
2. **Always include `secrets: inherit`** when calling reusable workflows that need secrets
3. **Add `permissions`** block when using Vault or Kubernetes auth:
   ```yaml
   permissions:
     contents: read
     id-token: write
   ```
4. **Use `paths-ignore`** to avoid triggering on doc-only changes:
   ```yaml
   on:
     push:
       branches: [main]
       paths-ignore:
         - "**/*.gitattributes"
         - "**/*.gitignore"
         - "**/*.md"
   ```
5. **Rate limit protection**: When using `setup-node`, `setup-go`, or `setup-python` on non-docker-runners, pass `token: ${{ secrets.GH_DOTCOM_READ_TOKEN }}`

## Common Patterns

### Docker Build & Release

```yaml
jobs:
  build-image:
    uses: github-actions/pipelines/.github/workflows/publish-docker.yml@v1
    with:
      docker-image: order-service/api  # format: <team-or-domain>/<service-name>
    secrets: inherit

  release:
    uses: github-actions/pipelines/.github/workflows/publish-version.yml@v1
    needs: [build-image]
    secrets: inherit
    if: github.event_name != 'pull_request'
```

### AWS Credentials

```yaml
- uses: github-actions/pipelines/actions/setup-ci@v1
  with:
    app: order-service    # Your service name as registered in PlatformMetadata
    aws-env: eu-west-1-prod  # AWS environment identifier, e.g. eu-west-1-prod, eu-west-1-staging

- uses: github-actions/configure-aws-creds@v1
  with:
    role-to-assume: arn:aws:iam::${{ env.AWS_ACCOUNT_ID }}:role/pipeline-ci
    role-session-name: github-session
```

### Slack Notifications

```yaml
- uses: github-actions/slackapi-slack-github-action@v1
  with:
    channel-id: ${{ vars.SLACK_CHANNEL_ID }}
    # ... message configuration
```

## Reference Documentation

For detailed information, consult:

- [GHES constraints and gotchas](references/ghes-constraints.md)
- [Available actions catalog](references/available-actions.md)
- [Runners and secrets](references/runners-and-secrets.md)
- [FAQs and troubleshooting](references/faqs-and-troubleshooting.md)

## Key URLs

| Resource | URL |
|----------|-----|
| GHES instance | `https://github.je-labs.com` |
| Actions org | `https://github.je-labs.com/github-actions/` |
| Pipelines (reusable workflows) | `https://github.je-labs.com/github-actions/pipelines` |
| Runner images | `https://github.je-labs.com/github-actions/runner-images` |
| Request action import | `https://github.je-labs.com/github-actions/manage-public-actions` |
| Internal docs | `https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/github-actions/` |
| Help channel | `#help-cde` / `#help-cicd-pipeline-community` |
