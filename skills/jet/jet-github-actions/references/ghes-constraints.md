# GHES Constraints & Gotchas

This reference covers the critical differences between GitHub.com and the JET GitHub Enterprise Server (GHES) instance at `github.je-labs.com`.

## No GitHub Connect

JET does **not** use GitHub Connect. This means:

- **No access to the public GitHub Marketplace** — you cannot use `uses: actions/checkout@v4` referencing github.com
- **All external actions must be imported** into the `github-actions` organisation at `https://github.je-labs.com/github-actions/`
- To request an action be imported or updated, open an issue at [github-actions/manage-public-actions](https://github.je-labs.com/github-actions/manage-public-actions/issues/new/choose)

## Action Sources — Where Actions Live

There are three categories of actions available:

| Category | Location | Example |
|----------|----------|---------|
| **First-party (GitHub built-in)** | `https://github.je-labs.com/actions` | `actions/checkout@v4` |
| **Imported (third-party mirrors)** | `https://github.je-labs.com/github-actions/` | `github-actions/dorny-test-reporter@v1.0.0` |
| **In-house custom** | `https://github.je-labs.com/github-actions/` | `github-actions/artifactory-upload@v1` |

### Enforcement Policy

> As per enforcement policies, **only** shared workflows and actions stored in the `github-actions` organisation can be utilised in a workflow, along with first-party GitHub actions.

## Imported Action Version Resolution Gotcha

Some public actions use a long-lived **branch** (e.g., `v1`) to define their major version. When these actions are imported to GHES, **only tags are mirrored**, not branches. This means `@v1` may fail if `v1` is a branch, not a tag.

**Symptom:**
```
Unable to resolve action `github-actions/dorny-test-reporter@v1`, unable to find version `v1`
```

**Fix:** Use an explicit tag that exists in the GHES mirror:
```diff
- github-actions/dorny-test-reporter@v1
+ github-actions/dorny-test-reporter@v1.0.0  # Or whatever tag exists
```

Check available tags at `https://github.je-labs.com/github-actions/<action-name>/tags`.

This mainly affects less popular or newly-imported actions. Most commonly-used imported actions have proper version tags that work fine with `@v1` style refs.

See: [Slack thread](https://justeat.slack.com/archives/C03325HDYMP/p1679333291721229) and [GitHub community discussion](https://github.com/community/community/discussions/39519).

## Built-in Action Version Restrictions

Because JET runs GHES (not github.com), not all action versions work even if tags are present. Key restriction:

| Action | Tags on GHES | Usable Version | Notes |
|--------|-------------|----------------|-------|
| `actions/upload-artifact` | Up to v4.6.1 | **v3 only** | v4 tags exist but [README states](https://github.je-labs.com/actions/upload-artifact): "upload-artifact@v4+ is not currently supported on GHES yet" |
| `actions/download-artifact` | Up to v4.1.9 | **v3 only** | Same as upload-artifact |

Other built-in actions (checkout, setup-node, setup-go, etc.) work fine at their latest versions. See [available-actions.md](references/available-actions.md) for a full table queried from GHES.

## Rate Limiting When Installing SDKs

The `setup-go`, `setup-node`, and `setup-python` actions download runtimes from the public GitHub API as an anonymous user if the version isn't pre-baked in the runner image. This can cause rate limiting.

**Fix**: Include the `GH_DOTCOM_READ_TOKEN` secret:

```yaml
- uses: actions/setup-node@v3
  with:
    token: ${{ secrets.GH_DOTCOM_READ_TOKEN }}
```

This only applies if **not** using the `docker-runner` (a.k.a. `ubuntu-latest`), which has SDKs pre-baked. See [runner-images toolset.json](https://github.je-labs.com/github-actions/runner-images/blob/main/images/docker-runner/files/toolset.json) for pre-installed versions.

## Fork and Bot Limitations

- **Fork PRs cannot access repository secrets** — this is a GitHub security model restriction
- **Bots** (`dependabot[bot]`, `github-actions[bot]`) also cannot access secrets
- **Workaround**: Close the fork PR, push the branch to the upstream repo, and open a new PR from there

Condition to exclude forks and bots from secret-dependent steps:

```yaml
if: |
  (github.event_name != 'pull_request' && github.event.repository.fork == false) ||
  (github.event_name == 'pull_request' &&
  github.event.pull_request.head.repo.full_name == github.repository &&
  !contains('["dependabot[bot]", "github-actions[bot]"]', github.actor))
```

## New Workflows Won't Run in PRs From Forks

New GitHub Actions workflows added by forks are **ignored** as part of the GitHub security model. To add/update workflows and test them before merging, you must make them in a branch of the **target repository** (not a fork).

## Runner IP Range

GitHub Actions runners operate from the IP range `10.201.160.0/19`. If accessing AWS resources with Security Group restrictions, you must allow ingress from the [`ci_eu-west-1-plt-prod-1`](https://github.je-labs.com/ContinuousDeliveryEngineering/PlatformMetadata/blob/master/Data/named_ip_ranges/ci_eu-west-1-plt-prod-1.json) named IP range.

## GHES-Specific URLs

| Resource | URL |
|----------|-----|
| GHES instance | `https://github.je-labs.com` |
| Built-in actions | `https://github.je-labs.com/actions` |
| Imported/custom actions | `https://github.je-labs.com/github-actions/` |
| Request new action import | `https://github.je-labs.com/github-actions/manage-public-actions` |
| Runner images | `https://github.je-labs.com/github-actions/runner-images` |
| Reusable workflows | `https://github.je-labs.com/github-actions/pipelines` |
| Internal docs (TechDocs) | `https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/github-actions/` |
