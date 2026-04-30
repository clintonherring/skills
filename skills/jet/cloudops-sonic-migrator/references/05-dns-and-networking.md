# DNS Path Discovery Procedure

## Overview

Before configuring the migration, discover how traffic currently reaches the service by tracing
DNS paths from the existing CloudOps-EKS configuration. This replaces guessing with automated
discovery followed by user confirmation.

## Step 1: Extract Hostnames from Existing Config

From the K8s manifests / ingress / helmfile config discovered in Phase 2, extract all hostnames:

- `*.eks.tkwy-*.io` hosts (CloudOps private domains — must be migrated)
- `.jet-internal.com` hosts (E-records, NG-records, R-records, G-records)
- `.jet-external.com` hosts
- Brand domain hosts (e.g., `*.takeaway.com`, `*.lieferando.de`)

## Step 2: Trace DNS Path for Each Hostname

For each discovered hostname, trace how traffic reaches the service:

### 2a. Check `IFA/route53`

```bash
gh repo clone github.je-labs.com/IFA/route53 /tmp/route53 -- --depth 1
grep -rn "{hostname}" /tmp/route53/
```

Note: record type (CNAME, weighted, alias), where it points, which zone (private/public).

### 2b. Check `IFA/domain-routing`

```bash
gh repo clone github.je-labs.com/IFA/domain-routing /tmp/domain-routing -- --depth 1
grep -rn "{hostname}" /tmp/domain-routing/vars/records/
```

Also search by **service name** and **parent domain** (brand domains may not appear in K8s manifests):
```bash
grep -rn "{service-name}" /tmp/domain-routing/vars/records/
# Also search for the parent domain — subdomain may not be listed yet
grep -rn "{parent-domain}" /tmp/route53/ --include="*.yml"
find /tmp/domain-routing/vars/records/ -name "{parent-domain}.yaml"
```

Check if Cloudflare proxy is involved (look in `vars/records/cloudflare/` and `vars/records/route53/`).

### 2c. If Cloudflare Detected (Progressive Discovery)

Only clone these repos if Step 2b detected Cloudflare involvement:

```bash
gh repo clone github.je-labs.com/IFA/cloudflareplatformproduction /tmp/cloudflareplatformproduction -- --depth 1
gh repo clone github.je-labs.com/IFA/cloudflareplatformstaging /tmp/cloudflareplatformstaging -- --depth 1
```

Check for WAF rules, page rules, origin overrides.

### 2d. Brand Domain Lookup

When searching for a brand domain hostname, always search for **both the subdomain AND
the parent domain** in both repos:

```bash
# Search for specific subdomain
grep -rn "{subdomain}" /tmp/route53/ --include="*.yml"
grep -rn "{subdomain}" /tmp/domain-routing/vars/records/

# Search for parent domain (the zone it belongs to)
grep -rn "{parent-domain}" /tmp/route53/ --include="*.yml"
find /tmp/domain-routing/vars/records/ -name "{parent-domain}.yaml"
```

The subdomain itself may not be listed yet — that's normal. What matters is finding
which repo manages the parent domain's zone (e.g., `production/records/scoober.com.yml`
in route53, or `vars/records/cloudflare/scoober.com.yaml` in domain-routing, or both).
Note the repo and file path for Phase 4.

## Step 3: Present Discovery Findings

Present the DNS path analysis as a table:

> **DNS Discovery for {service-name}**
>
> | Hostname | Source | DNS Path | Exposure |
> |----------|--------|----------|----------|
> | `app.ns.p.eks.tkwy-prod.io` | K8s ingress | CloudOps private (unreachable from Sonic) | Internal — must migrate |
> | `app.eu-west-1.production.jet-internal.com` | Route53 | R-record → existing CNAME | Internal (regional) |
> | `app.takeaway.com` | domain-routing | Cloudflare CDN → origin CNAME | External (Cloudflare proxied) |
> | `app.scoober.com` | route53 / domain-routing | Brand domain — parent zone found in `{repo}` | External (brand) |
>
> Based on this analysis, your service appears to be **{internal / external / both}**.

## Step 4: Ask User to Confirm

> "Does this match your understanding? Should the service be **internal-only** or **external**
> (internet-facing) in Sonic Runtime?"
>
> - **Internal only** — No internet-facing traffic. No SmartGateway needed.
> - **External** — Service receives internet traffic via SmartGateway/Cloudflare.
> - **Both** — Internal service-to-service AND external internet traffic.

Store the result as `EXPOSURE_TYPE`. Subsequent decisions branch based on this value.

## SmartGateway Determination Rule

SmartGateway is needed **only** when the service has external internet-facing endpoints (traffic
routed through SmartGateway/Kong). Brand domains used for **internal** purposes (not proxied
through Cloudflare/SmartGateway) do NOT need SmartGateway. The DNS discovery findings determine
this — always trace the actual DNS path rather than assuming from the domain name alone.
