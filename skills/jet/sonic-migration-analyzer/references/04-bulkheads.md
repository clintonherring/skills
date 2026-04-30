# Bulkheads in Sonic Runtime

## What is a Bulkhead?

A **Bulkhead** is a pool of isolated environments designed to tolerate failures in other bulkheads. Each JET environment is assigned to a bulkhead, enabling multi-tenant, fault-tolerant applications without enforcing specific designs at the infrastructure level.

## Key Concepts

1. **Isolation**: Bulkheads prevent failures in one from affecting others
2. **Proximity**: Deploy to bulkheads close to your market for better performance
3. **Flexibility**: Teams choose how to group applications across bulkheads

## Available Bulkheads

| Bulkhead ID | Market Region | Description              | AWS Region     |
| ----------- | ------------- | ------------------------ | -------------- |
| **EU1**     | Europe        | Central Europe & Ireland | eu-west-1      |
| **EU2**     | Europe        | United Kingdom           | eu-west-2      |
| **OC1**     | Oceania       | Australia                | ap-southeast-2 |
| **NA1**     | North America | Canada                   | us-west-2      |

## Environment Naming Convention

Format: `{region}-{tenant}-{stage}-{bulkhead-number}`

Examples:
- `euw1-pdv-prd-5` - EU1 Production
- `euw1-pdv-stg-5` - EU1 Staging
- `euw1-pdv-qa-3` - EU1 QA
- `euw2-pdv-prd-2` - EU2 Production
- `apse2-pdv-prd-2` - OC1 Production
- `usw2-pdv-prd-1` - NA1 Production

### Components:
- **Region**: `euw1` (eu-west-1), `apse2` (ap-southeast-2), `usw2` (us-west-2)
- **Tenant**: `pdv` (Product)
- **Stage**: `prd` (Production), `stg` (Staging), `qa` (QA)
- **Bulkhead Number**: Sequential identifier (1, 2, 3, 5, etc.)

## Project Deployment Across Bulkheads

**Critical Rule**: One project namespace deploys to multiple bulkheads (QA, Staging, Production).

### Example:
Project ID: `cu-order-reviews`

Deployments:
- **QA**: `euw1-pdv-qa-3` (namespace: `cu-order-reviews`)
- **Staging**: `euw1-pdv-stg-5` (namespace: `cu-order-reviews`)
- **Production**: `euw1-pdv-prd-5` (namespace: `cu-order-reviews`)

**Same namespace name**, different bulkheads.

## Helmfile Configuration

Projects configure target bulkheads in `helmfile.d/helmfile.yaml`:

```yaml
environments:
  euw1-pdv-qa-3:
    values:
      - state_values/defaults.yaml
      - state_values/euw1-pdv-qa-3.yaml
  euw1-pdv-stg-5:
    values:
      - state_values/defaults.yaml
      - state_values/euw1-pdv-stg-5.yaml
  euw1-pdv-prd-5:
    values:
      - state_values/defaults.yaml
      - state_values/euw1-pdv-prd-5.yaml
```

Environment-specific configurations stored in `state_values/{environment}.yaml`.

## Market-Based Selection

Choose bulkheads based on proximity to your user base:

| Market                  | Recommended Bulkhead | Latency Benefit           |
| ----------------------- | -------------------- | ------------------------- |
| Central Europe, Ireland | EU1                  | Lowest                    |
| United Kingdom          | EU2                  | Lowest                    |
| Australia, New Zealand  | OC1                  | Lowest                    |
| Canada                  | NA1                  | Lowest                    |
| Global/Multi-region     | Multiple bulkheads   | Distribute across regions |

## High-Availability Strategies

### Single-Region Applications
Deploy to one bulkhead per environment:
- QA: `euw1-pdv-qa-3`
- Staging: `euw1-pdv-stg-5`
- Production: `euw1-pdv-prd-5`

### Multi-Region Applications
Deploy to multiple bulkheads for the same environment:
- Production EU: `euw1-pdv-prd-5`
- Production UK: `euw2-pdv-prd-2`
- Production OC: `apse2-pdv-prd-2`
- Production NA: `usw2-pdv-prd-1`

## Isolation Benefits

1. **Failure Containment**: Issues in EU1 don't affect EU2
2. **Independent Upgrades**: Upgrade one bulkhead without impacting others
3. **Resource Separation**: Quota and resource limits per bulkhead
4. **Network Isolation**: Separate VPCs and network boundaries

## Migration Mapping

### RefArch Environments → Sonic Runtime Bulkheads

Example mapping (EU region):
- RefArch QA → `euw1-pdv-qa-3` (EU1 QA)
- RefArch Staging → `euw1-pdv-stg-5` (EU1 Staging)
- RefArch Production → `euw1-pdv-prd-5` (EU1 Production)

### L-JE EC2 / Marathon → Sonic Runtime

Map based on legacy environment:
- Legacy Staging → QA or Staging bulkhead
- Legacy Production → Production bulkhead

Choose bulkhead ID based on market requirements and team preferences.

## Cost Allocation

Each bulkhead tracks costs independently, enabling:
- Per-environment cost visibility
- Project-level cost allocation within bulkheads
- Market-based cost analysis

## Documentation References

- [Bulkheads Concept](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/oneeks/concepts/bulkheads/)
- [Environment Naming Standards](https://backstage.eu-west-1.production.jet-internal.com/docs/default/concept/jet-environments/environments/naming-standards/)
