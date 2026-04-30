# Goldenpath Structure

The target repository structure for Sonic Runtime follows the **goldenpath** pattern.

## Authoritative Sources

- **Goldenpath repo** (`justeattakeaway-com/goldenpath`): Clone and use as the source of truth for directory structure, helmfile patterns, workflow files, and environment names.
- **basic-application chart** (`helm-charts/basic-application`): Clone and read `values.yaml` for the current configuration schema, `CHANGELOG.md` for breaking changes, and `MIGRATION*.md` for upgrade guides.

Always clone both repos before generating code. The chart schema determines what goes in the helm values file.

## Directory Layout (Structural Hints)

This layout is the standard goldenpath structure. Verify against the cloned goldenpath repo.

```
repo/
├── Dockerfile
├── .sonic/
│   └── sonic.yml                        # Only if using Sonic Pipeline
├── .github/
│   └── workflows/                       # Only if using GitHub Actions (not Sonic Pipeline)
│       ├── build-deploy-main.yml
│       ├── build-pr.yml
│       ├── deploy-adhoc.yml
│       ├── diff-production.yml
│       └── rollback.yml
├── helmfile.d/
│   ├── helmfile.yaml.gotmpl             # Main helmfile entry point
│   ├── bases/
│   │   ├── helmDefaults.yaml.gotmpl     # Helm defaults (kubeContext, wait, atomic)
│   │   └── repositories.yaml.gotmpl     # Chart repository definition
│   ├── state_values/
│   │   ├── defaults.yaml                # Shared defaults (port, replicas)
│   │   └── {env-name}.yaml             # Per-environment overrides (one per env)
│   └── values/
│       └── {service-name}.yaml.gotmpl   # Application helm values
├── cosign.pub                           # Optional: image signing key
└── src/                                 # Application source code (unchanged)
```

## Key Patterns (from goldenpath)

### helmfile.yaml.gotmpl

- Defines `bases` (helmDefaults + repositories)
- Lists `environments` — each loading `state_values/defaults.yaml` + `state_values/{env}.yaml`
- Defines `releases` — single release using `sre/basic-application` chart into the project namespace
- **Chart version**: Fetch from the goldenpath repo. Verify against `helm-charts/basic-application` releases for the latest compatible version.

### state_values/

- `defaults.yaml`: Shared config (port, replicas min/max) — populate from extracted SRE-EKS config
- `{env}.yaml`: Per-environment overrides — must include `domains` list for VirtualService

### values/{service}.yaml.gotmpl

- Application-specific Helm values — **must match the basic-application chart's `values.yaml` schema**
- Key sections: `app` (metadata), `deployment` (workload), `virtualservices` (ingress), scaling config
- Read `basic-application/values.yaml` to determine the correct schema for the current chart version

### bases/

- `repositories.yaml.gotmpl`: Chart repository URL — copy from goldenpath
- `helmDefaults.yaml.gotmpl`: Helm defaults — copy from goldenpath

## Chart Version: Fetch, Don't Hardcode

```bash
# Get latest chart version
gh api --hostname github.je-labs.com /repos/helm-charts/basic-application/releases/latest | jq '.tag_name'

# Clone for full details
gh repo clone github.je-labs.com/helm-charts/basic-application /tmp/basic-application
```

After fetching:

1. Read `CHANGELOG.md` for breaking changes
2. Read `MIGRATION*.md` for upgrade notes
3. Read `values.yaml` for the current configuration schema
4. Inform user: "The current basic-application chart version is **{version}**. Key implications: {summary of relevant changes}."

## PlatformMetadata Tier

The app tier is fetched in Phase 2.1 using the `APP_NAME` validated in Phase 1:

```bash
gh api --hostname github.je-labs.com /repos/metadata/PlatformMetadata/contents/Data/global_features/{APP_NAME}.json | jq -r '.content' | base64 -d | jq '.tier'
```

Use the tier value (`bronze`, `silver`, `gold`) in the `app.tier` field. `APP_NAME` is the canonical name from PlatformMetadata — it may differ from the repo name.
