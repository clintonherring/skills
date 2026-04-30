# SmartGateway Configuration

## Overview

SmartGateway (Kong Gateway) routes **external internet traffic** to services deployed in Sonic
Runtime. It is needed **only** when DNS Path Discovery (Phase 4 Q3) confirms external
internet-facing endpoints routed through SmartGateway. Brand domains used internally (direct
Cloudflare → Istio, no SmartGateway in the path) do NOT need SmartGateway configuration.

## SmartGateway Environment Mapping

SmartGateway environments are named by region and stage. Use the bulkhead selection from Phase 4 Q1
to determine which environments to configure:

| Bulkhead | QA Environment            | Staging Environment            | Production Environment      |
| -------- | ------------------------- | ------------------------------ | --------------------------- |
| EU1      | `eu-central-1-ing-qa-1`   | `eu-central-1-ing-staging-1`   | `eu-central-1-ing-prod-1`   |
| EU2      | `eu-west-1-ing-qa-1`      | `eu-west-1-ing-staging-1`      | `eu-west-1-ing-prod-1`      |
| OC1      | `ap-southeast-2-ing-qa-1` | `ap-southeast-2-ing-staging-1` | `ap-southeast-2-ing-prod-1` |
| NA1      | `us-east-1-ing-qa-1`      | `us-east-1-ing-staging-1`      | `us-west-2-ing-prod-1`      |

**Note**: Always fetch the current environment mapping from the
`external-api-services/smartgatewayconfiguration` repo at runtime — the values above are reference
points only.

## API Governance (BOATS Spec)

All externally-exposed APIs require an **OpenAPI specification** registered with the API Design
Guild (using the BOATS format). During Phase 4 Q4c, ask the user:

> "All externally-exposed APIs also require an **OpenAPI specification** registered with the API
> Design Guild (using the BOATS format). Do you already have one?"
>
> - **Yes** — I already have a BOATS spec in the `api_specifications` repository
> - **No** — I need to create one
> - **Not sure**

If **No** or **Not sure**: inform the user that this is a prerequisite and provide guidance:

> "You'll need to create an OpenAPI v3 spec in the `api_specifications` repo (BOATS format) and
> get it approved by the API Design Guild (`#api-guild-design` on Slack). I'll generate a
> placeholder spec based on your service's routes, but you'll need to refine and submit it for
> approval before going live externally."

## Generating SmartGateway Config (Phase 5)

Clone `external-api-services/smartgatewayconfiguration`. Explore `Data/Global/` directory for
existing config files and current schema patterns.

Use `assets/templates/smartgateway-config.json.hbs.tmpl` as the base template. Key rules:

1. **Service host**: Must use the **NG-record** (e.g.,
   `{APP_NAME}.{project-id}.{env-type}.jet-internal.com`). SmartGateway proxies to the internal
   endpoint — never use the E-record.
2. **Port**: Must be `443` — SmartGateway connects via HTTPS to the internal endpoint.
3. **Protocol**: Must be `"https"` — prevents 301 redirects from the Istio ingress.
4. **Environments**: Use SmartGateway env names based on bulkhead selection (see mapping table
   above).
5. **Routes**: Map from the service's external URL paths (collected in Q4d for brand domains, or
   inferred from service routes for external APIs).
6. **Plugins**: At minimum, include `rate-limiting` plugin. Fetch current plugin patterns from
   existing configs in the repo.

Place the config file under `Data/Global/{service-name}.json.hbs` in the SmartGateway repo.

> Inform user: "After the SmartGateway PR is merged, you can test via SmartGateway regional
> endpoints before going fully live. Request review in `#help-http-integrations` on Slack."

## API Specifications (Phase 5)

If the user indicated in Q4c that they don't have a BOATS spec:

1. Clone `api_specifications` repo. Explore `src/paths/` for existing examples.
2. Generate a **placeholder OpenAPI v3 spec** based on the service's detected routes and endpoints.
3. Inform the user:
   > "I've generated a placeholder API spec. You'll need to review it, refine the
   > request/response schemas, and get approval from the API Design Guild
   > (`#api-guild-design` on Slack) before your external endpoint goes live."

If the user already has a BOATS spec: skip this step, but note that the existing spec may need
updating if URLs or paths change during migration.
