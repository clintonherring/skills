# SmartGateway Configuration

## When SmartGateway Is Needed

SmartGateway (Kong Gateway) routes **external internet traffic** to services deployed in Sonic
Runtime. It is needed **only** when DNS Path Discovery (Phase 4 Q3) confirms
`*.jet-external.com` endpoints — i.e., traffic from the public internet routed through
SmartGateway (Kong) to the service.

SmartGateway is **NOT needed** for:
- **Brand domains** (`*.takeaway.com`, `*.lieferando.de`, `*.thuisbezorgd.nl`, etc.) that route
  through Cloudflare CDN directly to the Istio ingress gateway — no SmartGateway in the path
- Internal-only services (even those with brand domains used for internal routing)
- Services accessed only via `*.jet-internal.com` records

**Key distinction**: `jet-external.com` APIs go through SmartGateway → NG-record → Istio.
Brand domains go through Cloudflare → Istio directly (with the brand domain as the Host
header). These are two completely different traffic paths. Only the first requires
SmartGateway configuration.

Always determine SmartGateway need from the actual DNS path trace, not from the domain name
or exposure type alone.

---

## Config Repository

**Repo**: `external-api-services/smartgatewayconfiguration`

```bash
gh repo clone github.je-labs.com/external-api-services/smartgatewayconfiguration /tmp/smartgatewayconfiguration -- --depth 1
```

**Config file path**: `Data/Global/{service-name}.json.hbs`

Explore the repo structure to confirm current conventions:
```bash
ls /tmp/smartgatewayconfiguration/Data/Global/ | head -20
cat /tmp/smartgatewayconfiguration/Data/Global/<existing-service>.json.hbs  # study pattern
```

---

## Config JSON Schema

Use `assets/templates/smartgateway-config.json.hbs.tmpl` as the starting point.

```json
{
  "name": "{SERVICE_DISPLAY_NAME}",
  "host": "{NG_RECORD}",
  "port": 443,
  "protocol": "https",
  "paths": [
    {
      "incoming": "/api/v1/{service}",
      "outgoing": "/api/v1/{service}"
    }
  ]
}
```

### Critical Rules

| Field | Value | Why |
|-------|-------|-----|
| `host` | **NG-record** (NOT E-record) | SmartGateway resolves to the regional endpoint |
| `port` | `443` | Always HTTPS |
| `protocol` | `"https"` | Always HTTPS |

**NG-record format**: `{APP_NAME}.{PROJECT_ID}.{env-type}.jet-internal.com`

Example: `partner-management-api.pa-partner-access.production.jet-internal.com`

### Paths

- `incoming`: The URL path as seen by external clients
- `outgoing`: The URL path forwarded to the service (usually identical)
- If the service handles multiple paths, add multiple entries to the `paths` array
- Detect paths from existing CloudOps ingress rules, VirtualService config, or by asking the user

### Plugins

At minimum, include `rate-limiting`. Check existing configs in the repo for the current plugin
format. Common plugins:

| Plugin | Purpose |
|--------|---------|
| `rate-limiting` | Protect against traffic spikes (required) |
| `correlation-id` | Request tracing |
| `request-transformer` | Header manipulation |

---

## SmartGateway Environment Mapping

SmartGateway environments are named by region and stage. Use the bulkhead selection from
Phase 4 Q1 to determine which environments to configure:

| Bulkhead | QA Environment             | Staging Environment              | Production Environment        |
| -------- | -------------------------- | -------------------------------- | ----------------------------- |
| EU1      | `eu-central-1-ing-qa-1`    | `eu-central-1-ing-staging-1`     | `eu-central-1-ing-prod-1`     |
| EU2      | `eu-west-1-ing-qa-1`       | `eu-west-1-ing-staging-1`        | `eu-west-1-ing-prod-1`        |
| OC1      | `ap-southeast-2-ing-qa-1`  | `ap-southeast-2-ing-staging-1`   | `ap-southeast-2-ing-prod-1`   |
| NA1      | `us-east-1-ing-qa-1`       | `us-east-1-ing-staging-1`        | `us-west-2-ing-prod-1`        |

> **Note**: Always fetch the current environment mapping from the
> `external-api-services/smartgatewayconfiguration` repo at runtime — the values above are
> reference points only.

### NG-Record per Environment

The `host` field in the SmartGateway config must use the **NG-record** which varies by
environment:

| Environment | NG-Record Pattern |
|-------------|------------------|
| QA | `{APP_NAME}.{PROJECT_ID}.qa.jet-internal.com` |
| Staging | `{APP_NAME}.{PROJECT_ID}.staging.jet-internal.com` |
| Production | `{APP_NAME}.{PROJECT_ID}.production.jet-internal.com` |

---

## API Governance (OpenAPI / BOATS)

All externally-exposed APIs require an **OpenAPI specification** registered with the API Design
Guild using the **BOATS** format in the `api_specifications` repo.

```bash
gh repo clone github.je-labs.com/Architecture/api_specifications /tmp/api_specifications -- --depth 1
ls /tmp/api_specifications/src/paths/  # explore existing specs
```

Ask the user:
> "All externally-exposed APIs require an OpenAPI specification registered with the API Design
> Guild (BOATS format). Do you already have one?"
>
> - **Yes** — already in `api_specifications` repo
> - **No** — need to create one
> - **Not sure**

If **No** or **Not sure**:
- Generate a placeholder OpenAPI v3 spec based on detected routes
- Inform user it must be refined and approved by API Design Guild (`#api-guild-design` on Slack)
- Add `api_specifications` PR to the repo list

---

## Testing

After SmartGateway PR is merged and deployed:

1. Test via SmartGateway regional endpoints (not internal DNS) to validate the full external path
2. Verify the NG-record resolves correctly
3. Check rate-limiting is applied

> "Request review in `#help-http-integrations` on Slack."

---

## PR Template

See [08-multi-repo-changes.md](08-multi-repo-changes.md) Repository 6 for the SmartGateway PR
body template and review channel.
