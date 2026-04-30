# DNS Path Discovery Procedure

## Overview

Before configuring the migration, discover how traffic currently reaches the service by tracing
DNS paths from the existing SRE-EKS configuration. This replaces manual user input with automated
discovery followed by user confirmation.

## Step 1: Extract Hostnames from Existing Config

From the VirtualService / ingress / helmfile config discovered in Phase 2, extract all hostnames:

- `.jet-internal.com` hosts (E-records, NG-records, R-records, G-records)
- `.jet-external.com` hosts
- Brand domain hosts (e.g., `*.takeaway.com`, `*.lieferando.de`)
- `.service` references

## Step 2: Trace DNS Path for Each Hostname

For each discovered hostname, trace how traffic reaches the service:

### 2a. Check `IFA/route53`

```bash
gh repo clone github.je-labs.com/IFA/route53 /tmp/route53
```

Search for the hostname in terraform files. Note record type (CNAME, weighted, alias), where it
points, and which zone (private/public).

### 2b. Check `IFA/domain-routing`

```bash
gh repo clone github.je-labs.com/IFA/domain-routing /tmp/domain-routing
```

Search for the hostname in `vars/records/`. Check if Cloudflare proxy is involved (look in
`vars/records/cloudflare/` and `vars/records/route53/`).

### 2c. If Cloudflare Detected (Progressive Discovery)

Check `IFA/cloudflareplatformproduction` and `IFA/cloudflareplatformstaging` for Cloudflare-specific
config (WAF rules, page rules, origin overrides):

```bash
gh repo clone github.je-labs.com/IFA/cloudflareplatformproduction /tmp/cloudflareplatformproduction
gh repo clone github.je-labs.com/IFA/cloudflareplatformstaging /tmp/cloudflareplatformstaging
```

Only clone these repos if Step 2b detected Cloudflare involvement. This avoids unnecessary clones.

## Step 3: Present Discovery Findings

Present the DNS path analysis as a table:

> **DNS Discovery for {service-name}**
>
> | Hostname                                                           | Source         | DNS Path                            | Exposure Classification       |
> | ------------------------------------------------------------------ | -------------- | ----------------------------------- | ----------------------------- |
> | `app.cu-order-reviews.pdv-5.eu-west-1.production.jet-internal.com` | VirtualService | E-record (auto-provisioned)         | Internal                      |
> | `app.eu-west-1.production.jet-internal.com`                        | VirtualService | Route53 R-record → E-record         | Internal (regional)           |
> | `app.takeaway.com`                                                 | VirtualService | Cloudflare CDN → origin CNAME → ... | External (Cloudflare proxied) |
> | `app.service`                                                      | Config refs    | Consul                              | Internal (SRE-EKS legacy)     |
>
> Based on this analysis, your service appears to be **{internal / external / both}**.

## Step 4: Ask User to Confirm

> "Does this match your understanding? Should the service be **internal-only** or **external**
> (internet-facing) in Sonic Runtime?"
>
> - **Internal only** — No internet-facing traffic. No SmartGateway or Cloudflare needed.
> - **External** — Service receives internet traffic. Must be proxied through Cloudflare and
>   directed to SmartGateway, which routes requests to internal clusters via their environment
>   DNS record.
> - **Both** — Internal service-to-service AND external internet traffic.

Store the result as `EXPOSURE_TYPE`. The subsequent questions in Phase 4 branch based on this value.

## SmartGateway Determination Rule

SmartGateway is needed **only** when the service has external internet-facing endpoints (traffic
routed through SmartGateway/Kong). Brand domains used for **internal** purposes (not proxied
through Cloudflare/SmartGateway) do NOT need SmartGateway. The DNS discovery findings determine
this — always trace the actual DNS path rather than assuming from the domain name alone.
