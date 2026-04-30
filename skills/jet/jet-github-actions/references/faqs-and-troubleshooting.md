# FAQs & Troubleshooting

## Common Issues

### "No runners available" for my repository

Ensure runner groups in your GitHub organisation allow access to public repositories. Check: Organisation Settings → Actions → Runner Groups → allow public repository access.

### New workflows aren't running in my PR

New workflows added via **fork PRs are ignored** (GitHub security model). You must add/update workflows in a branch of the **target repository**, not a fork. You need write access to the repo.

### Imported action version can't be resolved

```
Unable to resolve action `github-actions/dorny-test-reporter@v1`, unable to find version `v1`
```

This happens when the original public action uses a long-lived **branch** (e.g., `v1`) for versioning, but only tags were imported to GHES. **Fix**: Use an explicit tag that exists:
```diff
- github-actions/dorny-test-reporter@v1
+ github-actions/dorny-test-reporter@v1.0.0
```

Check available tags at `https://github.je-labs.com/github-actions/<action-name>/tags`.

### Can't upload to Artifactory from a PR

Is your PR from a **fork**? Fork PRs don't have access to secrets. Close the fork PR, push the branch to the upstream repo, and open a new PR from there.

### Pipeline stuck in pending/waiting state

Could be:
1. **Waiting for approval** — check if you can see and approve the request
2. **Waiting on a concurrency group** — another job in the same group is running
3. **Suspected GitHub bug** — the job gets stuck in a generic pending state

**Fix for concurrency locks**: Set `cancel-in-progress: true` on the concurrency group, or use a [break-lock workflow](https://github.je-labs.com/Account-Vertical/AuthenticationProxy/blob/49fd70177bb25ae70030653c95a822c1b3384fdc/.github/workflows/break-lock.yml).

More on concurrency: [GHA concurrency learnings](https://justeattakeaway.atlassian.net/wiki/spaces/techcomms/blog/2023/09/22/6463555219/GHA+concurrency+learnings)

### Individual job rerun unavailable

Individual jobs can only be restarted once the **overall workflow has completed** (all jobs finished or failed). Wait for remaining jobs to complete.

### Rate limited when installing Go/Node/Python

Use the `GH_DOTCOM_READ_TOKEN` secret with setup actions:
```yaml
- uses: actions/setup-node@v3
  with:
    token: ${{ secrets.GH_DOTCOM_READ_TOKEN }}
```

Not needed when using the `docker-runner` (`ubuntu-latest`) which has SDKs pre-baked.

### Workflow changes not taking effect for ad-hoc deploys

Ad-hoc deployments triggered by PR comments (`/sync`, `/diff`) **always run from the default branch** (e.g., `main`), not the PR branch. This is a GitHub Actions constraint for comment-triggered workflows.

### Can't authenticate with AWS/Vault in tests

The AWS credential setup in GitHub Actions differs from TeamCity/Zuul. You need:

1. Add `setup-ci` and `configure-aws-creds` steps before any AWS-dependent steps
2. For .NET apps, update the `FallbackCredentialsFactory`:
   ```csharp
   FallbackCredentialsFactory.CredentialsGenerators = new()
   {
       () => new EnvironmentVariablesAWSCredentials(),
   };
   ```

### AWS resources blocked by Security Groups

GitHub Actions runners use IP range `10.201.160.0/19`. Add the [`ci_eu-west-1-plt-prod-1`](https://github.je-labs.com/ContinuousDeliveryEngineering/PlatformMetadata/blob/master/Data/named_ip_ranges/ci_eu-west-1-plt-prod-1.json) named IP range to your security groups.

### SonarQube status check not showing on PRs

Install the [SonarQube GitHub app](https://github.je-labs.com/github-apps/sonarqubeprchecks) into your organisation with access to all repos. This is a one-time setup per org.

### Grafana release annotations stopped appearing

Update the annotation tag from `smart-pipeline` to `github-actions` in your Grafana JSON config.

### Backstage still shows old CI/CD tab

Update your application type to `GitHubActions` in [Platform Metadata](https://github.je-labs.com/ContinuousDeliveryEngineering/PlatformMetadata/tree/master/Data/global_features).

## General Questions

### What application types are supported?

**For CI (builds)**:
- ✅ EKS, Serverless, EC2

**For CD (deployments)**:
- ✅ EKS, Serverless
- ❌ EC2 (must use Concourse for deployments)

### What OS/runners are available?

- **Linux** (EKS) — default, autoscaling
- **Windows** (EC2) — for legacy .NET Framework builds
- **macOS** — iOS team only (case-by-case for others)

### Base runner image

Ubuntu 22.04 — see [runner-images Dockerfile](https://github.je-labs.com/github-actions/runner-images/blob/d7653da0154f770d160d76ff14098cf7642687ad/images/base-image/Dockerfile#L1)

### Can I add tools to the base runner image?

Maybe — only if widely adopted and measurably impacts builds. Otherwise, install in your workflow. PRs go to [runner-images](https://github.je-labs.com/github-actions/runner-images).

### How to add a new action from GitHub.com?

Open an issue at [manage-public-actions](https://github.je-labs.com/github-actions/manage-public-actions/issues/new/choose).

### How to write a custom GitHub Action?

Ask in [#community-pipelines](https://justeat.slack.com/archives/C03325HDYMP). If there's a case for it, a repo can be created in the `github-actions` org.

### How to extend shared workflows?

Raise a PR to [github-actions/pipelines](https://github.je-labs.com/github-actions/pipelines).

### How to redeploy or rollback?

Use the `redeploy` or `rollback` workflow in your repo (run manually via Actions tab). Specify version and environment.

### How to update the default branch?

1. Follow [GitHub's guide](https://docs.github.com/repositories/configuring-branches-and-merges-in-your-repository/managing-branches-in-your-repository/changing-the-default-branch)
2. Update all old branch references in `.github/workflows/`

## Getting Help

- Slack: [#help-cde](https://justeattakeaway.enterprise.slack.com/archives/C04T7SF9C00)
- Slack: [#help-cicd-pipeline-community](https://justeat.slack.com/archives/C03325HDYMP)
- Internal docs: [TechDocs](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/github-actions/)
- Public docs: [GitHub Actions documentation](https://docs.github.com/actions)
