# CI/CD: Sonic Pipeline Configuration

> **Note**: Sonic Pipeline eligibility detection (runtime detection, monorepo detection, eligibility
> criteria) is handled by the **`sonic-migration-analyzer`** skill during Phase 2. This file
> contains only the Sonic Pipeline **configuration guidance** used during Phase 5 (code generation).
> **Canonical Source**: For the full sonic.yml schema, field reference, supported runtimes, and
> runtime-specific workload configuration (test setup, flags, env vars, workflowInputs), load the
> **`sonic-pipeline`** skill. This file contains only **migration-specific** guidance: how to detect
> existing test patterns in SRE-EKS repositories and map them to Sonic Pipeline configuration.
---

## If Eligible: Sonic Pipeline Configuration

### Onboarding an Existing Component

For migrating services, follow the "Onboard an Existing Component" guide. The **`sonic-pipeline`**
skill documents the full onboarding steps. Key migration-specific considerations:

1. Verify prerequisites (runtime, single repo, GitHub, project exists)
2. Create `.sonic/sonic.yml` in repository root (under `.sonic/` directory) — use `sonic-pipeline`
   skill for the schema reference and `assets/templates/sonic.yml.tmpl` as the generation template
3. Configure metadata, environments, workloads — field definitions and discovery commands
   (PlatformMetadata, Vault, project lookup) are documented in `sonic-pipeline`
4. Old CI/CD workflows should be kept during migration.

### The `.sonic/sonic.yml` File

The sonic.yml lives at `/.sonic/sonic.yml` from repository root. The **`sonic-pipeline`** skill
is the authoritative source for the full spec schema, including:

- Root and workloads `apiVersion` values (two independent apiVersions)
- `metadata` fields (metadataId, project, team, vaultRole, vaultSecretPath, deployNotifications)
- `environments` cluster identifiers (pattern: `<region>-<platform>-<stage>-<number>`)
- `workloads` structure (resources, artifacts, deployments)
- Runtime-specific references for all supported runtimes (dotnet, Go, Java Maven/Gradle, Python, Redpanda Connect)
- Shared logic / `skip_deploy` and `skip_build` patterns

Load `sonic-pipeline` during Phase 5 for the complete schema reference and runtime-specific
configuration guidance.

**Critical rule** (from sonic-pipeline): The keys in `resources`, `artifacts`, and `deployment`
must use the **same workload name**.

#### Resources, Artifacts, and Deployment Configuration

See the **`sonic-pipeline`** skill for the full field reference for `resources`, `artifacts`,
and `deployment` sections. The migration-specific considerations are:

- **Deployment method detection**: Check the existing SRE-EKS repo for ArgoCD vs helmfile patterns.
  If ArgoCD app manifests are found, use `deploymentMethod: argocd`. Otherwise default to `helmfile`.
- **For helmfile deployments** (the default), resource specs like CPU/memory/ports are configured
  in `helmfile.d/`, not in sonic.yml.
- **For ArgoCD deployments**, additional `spec` fields become available (resources, ports, replicas,
  helmOverrides, etc.) — consult `sonic-pipeline` for the full ArgoCD spec.

---

### Workload Tests Configuration (Migration-Specific)

The **`sonic-pipeline`** skill documents the test configuration schema and runtime-specific
test setup (including flags, env vars, workflowInputs, and which test types each runtime supports).
This section covers how to **detect existing tests** in an SRE-EKS repository and **map them**
to the Sonic Pipeline configuration format.

#### Test Types and Locations

| Test Type     | Phase  | Config Location                     | Description                             |
| ------------- | ------ | ----------------------------------- | --------------------------------------- |
| `unit`        | Build  | `workloads.artifacts.{name}.tests`  | Tests individual components             |
| `integration` | Build  | `workloads.artifacts.{name}.tests`  | Tests component interactions            |
| `e2e`         | Deploy | `workloads.deployment.{name}.tests` | Tests full user journeys post-deploy    |
| `acceptance`  | Deploy | `workloads.deployment.{name}.tests` | Tests business requirements post-deploy |

Tests run in the order they are defined in the `tests` array.

#### Build-time Test Fields

| Field            | Required | Description                                                                    |
| ---------------- | -------- | ------------------------------------------------------------------------------ |
| `type`           | Yes      | `unit` or `integration`                                                        |
| `env`            | No       | Environment variables (for .NET/Go). Array of `{name, value}` maps             |
| `flags`          | No       | CLI flags for test script (.NET only). Array of strings (e.g., `-SkipPublish`) |
| `workflowInputs` | No       | Workflow-specific inputs (for Java/RedPanda/Python). Array of maps             |

#### Deployment-time Test Fields

| Field              | Required    | Description                                                         |
| ------------------ | ----------- | ------------------------------------------------------------------- |
| `type`             | Yes         | `e2e` or `acceptance`                                               |
| `env`              | No          | Environment variables. Array of `{name, value}` maps                |
| `flags`            | No          | CLI flags (.NET only). Array of strings                             |
| `skipEnvironments` | No          | Cluster IDs where test should be skipped (e.g., skip E2E in prod)   |
| `location`         | No          | External test repo. Object: `{repository, path, global-json-file}`  |
| `assumeTeamRole`   | No          | Enable AWS IAM role assumption for tests. Default: `false`          |
| `teamSid`          | Conditional | Team identifier for OIDC role. Required when `assumeTeamRole: true` |

#### Test Detection by Runtime

When generating test config, detect patterns from the source repo:

**Detection hints for existing tests**:

- **.NET**: Look for `build.ps1`, `*Tests.csproj`, `run-acceptance-tests.ps1`. Tests use `flags` and `env`. See `sonic-pipeline` dotnet reference for exact test execution commands.
- **Go**: Look for `*_test.go` files. Tests use `env` and `flags`. See `sonic-pipeline` Go reference for exact test execution commands.
- **Java (Gradle/Maven)**: Look for `src/test/`, test tasks in `build.gradle`. Tests use `workflowInputs` with `goals` and `report-paths`. See `sonic-pipeline` Java references for exact workflowInputs format.
- **Python**: Look for `tests/`, `pytest.ini`, `pyproject.toml[tool.pytest]`. Tests use `workflowInputs` with `use-poetry`, `run-ruff`, `run-mypy`. See `sonic-pipeline` Python reference for exact workflowInputs format.
- **RedPanda**: Tests use `workflowInputs` with custom script configuration. See `sonic-pipeline` Redpanda Connect reference.

**Mapping SRE-EKS test patterns to Sonic Pipeline**:

| What to look for in source repo       | Sonic test config                               |
| ------------------------------------- | ----------------------------------------------- |
| Unit test project/directory           | `artifacts.{name}.tests: [{type: unit}]`        |
| Integration test project/directory    | `artifacts.{name}.tests: [{type: integration}]` |
| E2E test scripts, Selenium/Playwright | `deployment.{name}.tests: [{type: e2e}]`        |
| Acceptance test scripts               | `deployment.{name}.tests: [{type: acceptance}]` |
| Test env vars in CI workflows         | Copy to `env` array                             |
| Test flags in CI scripts              | Copy to `flags` array                           |
| Tests in separate repo                | Use `location` field                            |
| Tests skipped in production           | Use `skipEnvironments` with prd cluster         |

---

### How Sonic Pipeline Processes the Spec

When you push changes, Sonic:

1. **Validates** `sonic.yml` against the schema (based on `apiVersion`)
2. **Generates a Single Runfile** containing config and workflow input for all workloads
3. **Analyzes Impact**: Identifies which workloads are affected by the change
4. **Triggers** appropriate CI/CD workflows (e.g., `build-pr`, `build-deploy-main`)

Sonic automatically maps spec fields to workflow inputs (vault-role, secret-path, app-type, notification channels). You do NOT edit workflow inputs directly.

When using Sonic Pipeline, do **NOT** add `.github/workflows/` — Sonic Pipeline manages CI/CD entirely.

---

## If NOT Eligible: GitHub Actions Workflows

Use the standard goldenpath GitHub Actions workflows. Fetch current patterns from:

1. **Goldenpath repo** (cloned in Phase 2): Read `.github/workflows/` for the latest workflow files
2. **Pipelines repo**: Check `github-actions/pipelines` for current reusable workflow versions

The standard workflows are:

- `build-deploy-main.yml` — Main branch: generate-version → test → docker-build → tag → deploy QA → staging → production
- `build-pr.yml` — PRs: lint → test → docker-build
- `deploy-adhoc.yml` — Ad-hoc deployments via `/sync` comments
- `diff-production.yml` — Helmfile diff against production
- `rollback.yml` — Rollback to a previous version

Copy workflow files from goldenpath and adapt service-specific values (service name, namespace, environments, test commands).