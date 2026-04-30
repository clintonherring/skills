# Consul Bridge: Backward Compatibility for SRE-EKS

## Purpose

After migrating to Sonic Runtime, other services **still running on SRE-EKS** may need to reach the migrated service at its old `.service` address. The Consul bridge provides this backward compatibility through a one-way sync.

> **Note**: This section covers backward compatibility for **callers** reaching _this_ service via
> its `.service` address after migration (i.e., making the migrated service still discoverable
> in Consul for SRE-EKS consumers). For replacing `.service` addresses that _this service uses_
> to reach its own dependencies (databases, message brokers, other services), see "Migrating from
> Consul .service Addresses" in [05-dns-and-networking.md](05-dns-and-networking.md) and Phase 4
> Q4a-2 in [19-phase-4-configure.md](19-phase-4-configure.md).

## User-Friendly Prompt

> "Do you want other services still running on SRE-EKS to be able to reach your service at its current `.service` address (e.g., `myapi.service`)? This keeps backward compatibility during the transition period so dependent services don't need to update their configuration immediately."
>
> - **Yes** (recommended if other services depend on you) → Configure Consul advertising
> - **No** (safe if no other SRE-EKS services call you) → Skip

## How It Works (Conceptual)

1. The migrated service runs in Sonic Runtime behind the `igw-marathon` Istio ingress gateway
2. A Consul config map (`oneeks_migrated_services`) tells the SRE-EKS Consul cluster to route `.service` lookups to the Sonic Runtime ingress
3. SRE-EKS services calling the `.service` address get routed transparently to Sonic Runtime

## Configuration: Two Changes Required

### 1. VirtualService for igw-marathon

Add an `igw-marathon` VirtualService entry in the application's helm values. Fetch the exact format from:

- The **basic-application chart** `values.yaml` → `virtualservices` schema
- Backstage: search `advertising in consul oneeks` for current documentation

The entry exposes the service on the `igw-marathon` gateway in addition to the standard `igw-<project>` gateway.

### 2. Consul Repository: oneeks_migrated_services Map

Fetch the current configuration format and file locations from Backstage:

```bash
curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
  "$BACKSTAGE_BACKEND_URL/api/search/query?term=advertising+in+consul+oneeks+migrated&types%5B0%5D=techdocs" \
  | jq '.results[:3][] | {title: .document.title, text: .document.text[:500]}'
```

The general pattern is to add an entry for the migrated service in the `oneeks_migrated_services` map with the service name, port, health check path, and namespace. Apply to both staging and production configs.

## When to Remove

The Consul bridge should be removed after:

1. All dependent services in SRE-EKS have migrated or updated their config to use GlobalDNS
2. No traffic is flowing through the `igw-marathon` gateway for this service
3. The SRE-EKS deployment has been fully decommissioned
