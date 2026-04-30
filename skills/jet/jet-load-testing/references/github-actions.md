# GitHub Actions Integration

k6 tests should only be run locally during development. Production tests MUST be executed via GitHub Actions using JET's shared reusable workflow.

## Official Documentation

- **Triggering Tests**: https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/load-testing/getting-started/triggering-tests/
- **Test Validation**: https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/load-testing/getting-started/test-validation/
- **Notifications**: https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/load-testing/test-configuration/notifications/
- **Reusable Workflow**: https://github.je-labs.com/github-actions/load-testing/blob/main/docs/run-k6.md

## Reusable Workflow

JET provides a shared reusable workflow for executing k6 tests:

```yaml
uses: github-actions/load-testing/.github/workflows/run-k6.yml@v1
secrets: inherit
```

### Workflow Inputs

| Input | Required | Description |
|-------|----------|-------------|
| `path` | **Yes** | Relative path to your test script (e.g., `.load-tests/smoke.js`) |
| `app` | **Yes** | App name as per PlatformMetadata. User should be prompted for this if it cannot be inferred from the RUNBOOK or README. |
| `environment` | **Yes** | Environment name (e.g., `euw1-pdv-qa-2`) |
| `mode` | **Yes** | Execution mode: `local`, `cloud` or `cloudresultsonly` |
| `cloud-project-id` | **Yes** | Your k6 Cloud project ID. |
| `profile` | No | Profile name for parameterised tests |
| `validation-test` | No | Set to `true` for lightweight validation (1 VU, 1 iteration) |
| `slack-channel-id` | No | Team-specific Slack channel ID for notifications |
| `is-artifact` | No | Set to `true` if the script is uploaded as an artifact |

### Execution Mode

- `local` - This will run on the Github Actions runner. No results passed to Grafana Cloud for visualisation.
- `cloudresultsonly` - This runs on the Github Actions runner, and passes the results to Grafana Cloud.
- `cloud` - Recommended mode for most tests. Runs using Grafana Cloud infrastructure. This is required for PrivateLoadZone tests.

### Secrets

The workflow uses `secrets: inherit` to automatically pass required secrets from the repository. No manual secret configuration is needed.

### Default Notifications

All tests automatically post notifications to `#alerts-k6-load-tests`. Prompt the user for a different (usually a team channel) channel, and use the `slack-channel-id` input if provided.

### Default User Agent

The workflow sets a standardised User Agent for all requests:

```
JET/k6LoadTest (GITHUB_REPO; TEST_NAME)
```

This helps identify load test traffic in application logs. Avoid overriding this in any test scripts.

---

## Triggering Tests

### Manual Trigger (workflow_dispatch)

If users want to manually trigger their tests: See [templates/github-workflow-manual.yml](../templates/github-workflow-manual.yml).

### Within Existing Pipelines (Post-Deployment)

Run load tests automatically after deploying to an environment. It is suggested that teams at least run a test following staging deployments, before deploying into production. See [templates/github-workflow-cicd.yml](../templates/github-workflow-cicd.yml) for a complete CI/CD example.

Prompt the user to ask if their CI/CD Pipelines should be updated with test runs (and explain that this is best practice). Only update them if the user requests this.

### PR Comment Trigger

Trigger tests from PR comments for ad-hoc testing during development: https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/load-testing/getting-started/triggering-tests/#pr-comments