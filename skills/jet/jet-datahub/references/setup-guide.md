# Setup Guide

## Skill Installation

```bash
npx skills add git@github.je-labs.com:ai-platform/skills.git --skill jet-datahub
```

Or copy the skill directory manually to `~/.agents/skills/jet-datahub/`.

## Prerequisites

| Tool | Purpose | Tested Version |
|------|---------|----------------|
| `datahub` CLI | Entity lookups, existence checks, timeline | `acryl-datahub==1.0.0` |
| `curl` | Search and lineage via GMS REST API | Pre-installed on macOS/Linux |
| `jq` (optional) | JSON slicing and extraction | any |

## CLI Installation

Install the `datahub` CLI using one of the methods below.

### Method 1: uv (recommended)

```bash
uv tool install --python 3.11 "acryl-datahub==1.0.0"
```

### Method 2: pipx

```bash
pipx install --python python3.11 "acryl-datahub==1.0.0"
```

### Method 3: pip (fallback)

```bash
pip install "acryl-datahub==1.0.0"
```

> If system `pip` is permission-restricted, use Method 1 or 2 instead.

### Verify installation

```bash
datahub version
```

Expected output should show `DataHub CLI version: 1.0.0`.

## Authentication

Use one of the following methods.

### Method 1: `datahub init` (recommended)

```bash
# Interactive
datahub init

# Non-interactive
datahub init --host https://datahub.just-data.io/api/gms --token <your-token>
```

This stores configuration in `~/.datahubenv`.

### Method 2: Environment variables

```bash
export DATAHUB_GMS_URL="https://datahub.just-data.io/api/gms"
export DATAHUB_GMS_TOKEN="<your-personal-access-token>"
```

Environment variables override `~/.datahubenv`.

## Loading Auth for curl Commands

The CLI commands (`datahub get urn`, `datahub exists urn`, etc.) read auth from `~/.datahubenv` automatically. For `curl` commands (search and lineage), load the credentials:

```bash
DATAHUB_GMS_URL=$(grep server ~/.datahubenv | awk '{print $2}')
DATAHUB_GMS_TOKEN=$(grep token ~/.datahubenv | awk '{print $2}')
```

## Connectivity Check

Run both checks before using discovery workflows:

```bash
# Check client + server version
datahub version --include-server

# Check entity read access
datahub exists urn --urn "urn:li:dataset:(urn:li:dataPlatform:bigquery,just-data-warehouse.core_dwh.fact_order,PROD)"
```

If both commands return successfully, auth and connectivity are confirmed.

## Self-Test

After setup, run the following health checks to verify all capabilities:

```bash
# 1. Check version + server connectivity
datahub version --include-server

# 2. Test REST search
DATAHUB_GMS_URL=$(grep server ~/.datahubenv | awk '{print $2}')
DATAHUB_GMS_TOKEN=$(grep token ~/.datahubenv | awk '{print $2}')
curl -s -X POST "$DATAHUB_GMS_URL/entities?action=search" \
  -H "Authorization: Bearer $DATAHUB_GMS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"input": "*", "entity": "dataset", "start": 0, "count": 1}' | jq '.value.numEntities'

# 3. Test entity existence
datahub exists urn --urn "urn:li:dataset:(urn:li:dataPlatform:bigquery,just-data-warehouse.core_dwh.fact_order,PROD)"

# 4. Test entity metadata retrieval
datahub get urn --urn "urn:li:dataset:(urn:li:dataPlatform:bigquery,just-data-warehouse.core_dwh.fact_order,PROD)" --aspect globalTags
```

| Step | Pass criteria | If it fails |
|------|--------------|-------------|
| 1 | Shows client + server versions | CLI not installed or auth not configured |
| 2 | Returns a positive integer (total datasets) | Check token, GMS URL, or network/VPN |
| 3 | Returns `true` | Dataset URN may be wrong, or auth issue |
| 4 | Returns JSON with `globalTags` | Check auth token has read permissions |

## Default JET Endpoint

- GMS URL: `https://datahub.just-data.io/api/gms`

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATAHUB_GMS_URL` | DataHub GMS endpoint | `https://datahub.just-data.io/api/gms` |
| `DATAHUB_GMS_TOKEN` | DataHub access token | None |

## CLI v1.0.0 — Available Commands

The following commands are available in `datahub` CLI v1.0.0:

| Command | Purpose |
|---------|---------|
| `datahub get urn` | Get entity metadata by URN (all aspects or specific) |
| `datahub exists urn` | Check if entity exists |
| `datahub dataset get` | Dataset-focused metadata (may be slow — prefer `datahub get urn`) |
| `datahub timeline` | Metadata change history |
| `datahub version` | Client/server version info |
| `datahub init` | Configure auth |

The following commands do **NOT** exist in v1.0.0:

| Command | Alternative |
|---------|-------------|
| `datahub search` | Use `curl POST $DATAHUB_GMS_URL/entities?action=search` |
| `datahub graphql` | Not needed — use CLI commands for entity lookups, `curl` REST API for search/lineage |

## Troubleshooting

### Installation Issues

| Error | Meaning | Action |
|-------|---------|--------|
| `pip: permission denied` | System pip is restricted | Use `uv tool install` or `pipx install` instead |
| `No such command 'search'` | Expected — CLI v1.0.0 does not have search | Use `curl` to the GMS REST API for search |
| `No such command 'graphql'` | Expected — CLI v1.0.0 does not have graphql | Use CLI for entity lookups, `curl` REST API for search/lineage |

### Runtime Issues

| Error | Meaning | Action |
|-------|---------|--------|
| `datahub: command not found` | CLI not installed or not on PATH | Install with one of the methods above, then restart shell |
| `401 Unauthorized` (curl) | Token invalid/expired | Re-run `datahub init` with a valid token or update `DATAHUB_GMS_TOKEN` |
| `403 Forbidden` | Token lacks permissions | Request required scopes/access from DataHub admins |
| `Could not connect` / timeout | Wrong URL or network issue | Verify `DATAHUB_GMS_URL`, VPN, and corporate network access |
| `Expecting value: line 1` | CLI output parse error | Check `~/.datahubenv` has correct `server` and `token` values |
| Empty `{}` from `--aspect ownership` | Normal — ownership aspect is often empty | Use `--aspect globalTags` and look for `team:` prefixed tags instead |
| `datahub dataset get` hangs | Known issue — can be slow | Use `datahub get urn --urn <urn>` instead |
