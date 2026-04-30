---
name: jet-datadog
description: Interact with Datadog's observability platform using the pup CLI (https://github.com/datadog-labs/pup). Use when the user needs to query logs, metrics, or traces; manage monitors, dashboards, or SLOs; investigate incidents or errors; check APM services and dependencies; manage security rules and signals; view CI/CD pipelines and test results; manage infrastructure hosts and tags; handle cases and on-call teams; check cost and usage data; manage cloud integrations (AWS, GCP, Azure); work with synthetics tests; or perform any other Datadog API operation. Requires the pup binary to be installed and authenticated via `pup auth login` or DD_API_KEY/DD_APP_KEY environment variables. This skill targets JET's environment — EU Datadog site (datadoghq.eu) with logs stored in Flex Logs rather than indexed logs.
metadata:
  owner: ai-platform
---

# Datadog via Pup CLI

Pup is a CLI with 320+ commands across 56 Datadog product domains. Use it to query, investigate, and manage Datadog resources.

## Prerequisites

- `pup` binary installed and on PATH — **version 0.25+ required** for `--storage=flex` support
- Always use `DD_SITE=datadoghq.eu` for all `pup` commands
- Authenticated via `pup auth login` (OAuth2, preferred) or `DD_API_KEY` + `DD_APP_KEY` + `DD_SITE` env vars
- Verify installation: `pup --version` (must be ≥ 0.25)
- Verify authentication: `pup auth status`

## Installation

### Homebrew (macOS/Linux)

```bash
brew tap datadog-labs/pack
brew install datadog-labs/pack/pup
```

### Windows

For Copilot/OpenCode-style agent workflows, use `pup` inside an interactive WSL2 terminal. Starting the assistant from PowerShell while relying on WSL for auth may not work correctly.

Install `pup` inside your WSL distro using the Linux instructions above, then verify with:

```bash
pup --version
```

If the user needs to run `pup` natively from PowerShell, set file-based token storage first because the default Windows credential-store integration may fail to persist tokens:

```powershell
[System.Environment]::SetEnvironmentVariable("DD_SITE", "datadoghq.eu", "User")
[System.Environment]::SetEnvironmentVariable("DD_TOKEN_STORAGE", "file", "User")
```

Then open a new PowerShell session and run `pup auth login` once. Tokens should then persist under `%APPDATA%\pup\`.

### Build from Source (macOS/Linux/WSL)

Requires `rustup` from https://rustup.rs/ and the latest stable Rust toolchain.

Build with:

```bash
git clone https://github.com/datadog-labs/pup.git && cd pup
rustup toolchain install stable
rustup default stable
cargo build --release
cp target/release/pup /usr/local/bin/pup
```

## Key Principles

- **Agent mode** is auto-detected in AI coding assistants — output defaults to JSON, confirmations are auto-approved
- On Windows, prefer `pup` from an interactive WSL terminal for agent workflows; native PowerShell may work only when `DD_TOKEN_STORAGE=file` is configured first
- Always use `--output=json` for structured parsing (default in agent mode)
- Always pass `--yes` for destructive operations to prevent stdin hangs
- Always specify `--from` for time-scoped queries (logs, metrics, traces, events)
- **Always pass `--storage=flex` for all log commands** — JET stores the majority of logs in Flex Logs (a cost-efficient Datadog tier that retains logs without indexing them; unlike indexed logs, Flex Logs are not searchable without the `--storage=flex` flag). Omitting this flag queries only indexed logs and will miss most data
- **Always use `DD_SITE=datadoghq.eu`** — JET uses the EU Datadog site. Set `export DD_SITE=datadoghq.eu` in your shell before running pup commands, or pass `--site=datadoghq.eu` on each invocation
- Use `pup <domain> --help` to discover subcommands and flags for any domain
- For full command reference with all flags, read `references/command-reference.md`

## Authentication

```bash
# OAuth2 (preferred) — opens browser, tokens stored in the OS credential store
pup auth login

# Check status
pup auth status

# Refresh token
pup auth refresh

# API key fallback — bash/zsh
export DD_API_KEY="..." DD_APP_KEY="..." DD_SITE="datadoghq.eu"
```

On Windows, prefer authentication from an interactive WSL terminal for agent workflows. If the user needs native PowerShell, first set `DD_TOKEN_STORAGE=file` so tokens persist outside the broken default credential-store path.

Authentication priority: OAuth2 tokens > API keys. Some endpoints (e.g., logs search) may require API keys even with OAuth2.

## Command Pattern

```bash
pup <domain> <action> [--flags]              # Simple: pup monitors list
pup <domain> <subgroup> <action> [--flags]   # Nested: pup apm services list --env=prod
```

## Common Investigation Workflows

### Error Investigation

```bash
# 1. Find which services have errors
pup logs aggregate --query="status:error" --from=1h --compute="count" --group-by="service" --storage=flex

# 2. Drill into the affected service
pup logs search --query="status:error AND service:<name>" --from=1h --limit=20 --storage=flex

# 3. Check monitors for that service
pup monitors list --tags="service:<name>"

# 4. Check recent events (deploys, config changes)
pup events list --from=4h
```

### Performance Investigation

```bash
# 1. Check service latency
pup metrics query --query="avg:trace.servlet.request.duration{service:<name>} by {resource_name}" --from=1h

# 2. Find slow traces (>5s) — CRITICAL: APM durations are in NANOSECONDS
pup apm services stats --env=prod

# 3. Check resource utilization
pup metrics query --query="avg:system.cpu.user{service:<name>} by {host}" --from=1h
```

### Incident Triage

```bash
# 1. List active incidents
pup incidents list

# 2. Get incident details
pup incidents get <incident-id>

# 3. Check related error tracking issues
pup error-tracking issues search --query="service:<name>" --from=1d

# 4. Check SLO status
pup slos list
```

## Query Syntax

### Logs

```
status:error                    # By status
service:web-app                 # By service
@user.id:12345                  # Custom attribute
host:i-*                        # Wildcard
"exact error message"           # Exact phrase
status:error AND service:web    # Boolean AND
status:error OR status:warn     # Boolean OR
NOT status:info                 # Negation
-status:info                    # Shorthand negation
```

Storage tiers: `indexes`, `online-archives`, `flex`. **Always use `--storage=flex`** — JET stores logs in Flex Logs by default.

### Metrics

```
<aggregation>:<metric_name>{<filter>} by {<group>}

avg:system.cpu.user{*}                          # All hosts
avg:system.cpu.user{env:prod} by {host}         # By host, prod only
sum:trace.servlet.request.hits{service:web}     # Request count
```

Aggregations: `avg`, `sum`, `min`, `max`, `count`. Always include `{...}` filter, use `{*}` for all.

### APM

```
service:<name>                  # By service
resource_name:<path>            # By endpoint
@duration:>5000000000           # Duration > 5s (NANOSECONDS!)
status:error                    # Errors only
env:production                  # By environment
```

**CRITICAL**: APM durations are in **nanoseconds**. 1ms = 1,000,000ns. 1s = 1,000,000,000ns.

### RUM

```
@type:error                     # Error events
@session.type:user              # User sessions (not synthetic)
@view.url_path:/checkout        # Specific page
@action.type:click              # Click actions
```

## Time Ranges

All `--from` and `--to` flags accept:

| Format | Example | Description |
|--------|---------|-------------|
| Relative short | `1h`, `30m`, `7d`, `5s` | Ago from now |
| Relative long | `5min`, `2hours`, `3days` | Ago from now |
| RFC3339 | `2024-01-01T00:00:00Z` | Absolute |
| Unix ms | `1704067200000` | Milliseconds since epoch |
| Keyword | `now` | Current time |

## Output Formats

```bash
pup monitors list --output=json   # Default in agent mode, structured
pup monitors list --output=table  # Human-readable
pup monitors list --output=yaml   # YAML format
```

## Error Handling

| Status | Meaning | Action |
|--------|---------|--------|
| 401 | Auth failed | Run `pup auth login` or check API keys |
| 403 | Insufficient permissions | Verify API/App key scopes |
| 404 | Resource not found | Check the ID or resource name |
| 429 | Rate limited | Wait and retry with backoff |
| 5xx | Server error | Retry after a short delay |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DD_API_KEY` | Datadog API key (fallback auth) | - |
| `DD_APP_KEY` | Datadog Application key (fallback auth) | - |
| `DD_SITE` | Datadog site (must be `datadoghq.eu` for JET) | `datadoghq.eu` |
| `DD_AUTO_APPROVE` | Auto-approve destructive ops | `false` |
| `DD_TOKEN_STORAGE` | Token storage backend | auto-detect |

## Full Command Reference

For complete details on all 56 command domains, every subcommand, and every flag, read [references/command-reference.md](references/command-reference.md).

Search patterns for the reference file:
- Search `## <domain>` to find a specific domain (e.g., `## logs`, `## monitors`)
- Search `### <domain> <subcommand>` for nested commands (e.g., `### apm services`)
