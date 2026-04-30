# Istio Debugging

Debugging Istio service mesh issues in JET OneEKS clusters. The `basic-application` Helm chart generates Istio resources (VirtualService, DestinationRule, AuthorizationPolicy, ServiceEntry, RequestAuthentication, Telemetry) based on chart values.

## Prerequisites

```bash
# Verify istioctl is installed
istioctl version

# If not installed:
brew install istioctl
```

If `istioctl` is not available, most debugging can still be done with `kubectl` by inspecting Istio CRDs directly.

## Istio Analysis (Best First Step)

```bash
# Analyze all Istio config in a namespace
istioctl --context=<ctx> -n <ns> analyze

# Analyze the whole cluster
istioctl --context=<ctx> analyze --all-namespaces

# Example output:
# Warning [IST0101] (VirtualService myapp.mynamespace) Referenced host not found: "myapp.mynamespace.svc.cluster.local"
# Error [IST0134] (DestinationRule myapp.mynamespace) Port name "http" not found in service
```

Common analysis messages:

| Code | Meaning | Fix |
|------|---------|-----|
| `IST0101` | VirtualService references unknown host | Verify Service exists and host matches `<svc>.<ns>.svc.cluster.local` |
| `IST0104` | Gateway references unknown port | Check Service port definition |
| `IST0106` | Schema validation error | Fix the YAML syntax of the Istio resource |
| `IST0134` | Port not found in service | Ensure Service port name matches DestinationRule port |

## VirtualService Debugging

The `basic-application` chart creates VirtualService resources for traffic routing.

### Check Current VirtualService

```bash
# View VirtualService configuration
kubectl --context=<ctx> -n <ns> get vs <app> -o yaml

# JSON: extract routing rules
kubectl --context=<ctx> -n <ns> get vs <app> -o json | \
  jq '{hosts: .spec.hosts, http: .spec.http}'
```

### Common VirtualService Issues

**Issue: 404 Not Found**
- The VirtualService host doesn't match the incoming request's Host header
- Check `.spec.hosts` — must match the hostname clients use

```bash
kubectl --context=<ctx> -n <ns> get vs <app> -o jsonpath='{.spec.hosts[*]}'
```

**Issue: Traffic not reaching canary during rollout**
- The canary VirtualService should have weight-based routing
- Check route weights:

```bash
kubectl --context=<ctx> -n <ns> get vs <app> -o json | \
  jq '.spec.http[0].route[] | {host: .destination.host, weight: .weight}'
```

Expected during canary: stable service gets (100 - canary_weight)%, preview service gets canary_weight%.

**Issue: Preview VirtualService not created**
- Canary requires: `deployment.strategy.canary` + `virtualservices[].hosts` defined + no custom `http` routes
- If any condition is missing, the preview VirtualService is not rendered

### Fault Injection (Testing)

The chart supports fault injection via VirtualService:

```bash
# Check if fault injection is configured
kubectl --context=<ctx> -n <ns> get vs <app> -o json | \
  jq '.spec.http[]?.fault'

# Faults and custom http routes are mutually exclusive in basic-application
```

## DestinationRule Debugging

DestinationRules control traffic policies (TLS, load balancing, circuit breaking).

```bash
# View DestinationRule
kubectl --context=<ctx> -n <ns> get dr <app> -o yaml

# JSON: check TLS mode
kubectl --context=<ctx> -n <ns> get dr <app> -o json | \
  jq '{host: .spec.host, trafficPolicy: .spec.trafficPolicy}'
```

### Common DestinationRule Issues

**Issue: 503 Upstream Connection Error**
- TLS mode mismatch between client and server
- JET uses Istio mTLS (ISTIO_MUTUAL) by default

```bash
# Check TLS mode
kubectl --context=<ctx> -n <ns> get dr <app> -o jsonpath='{.spec.trafficPolicy.tls.mode}'
# Expected: ISTIO_MUTUAL

# Check PeerAuthentication (namespace or mesh-wide)
kubectl --context=<ctx> -n <ns> get peerauthentication -o yaml
kubectl --context=<ctx> -n istio-system get peerauthentication -o yaml
```

**Issue: Connection pooling / circuit breaking**
- If a service is overwhelmed, Istio may be dropping connections

```bash
kubectl --context=<ctx> -n <ns> get dr <app> -o json | \
  jq '.spec.trafficPolicy.connectionPool'
```

## AuthorizationPolicy Debugging

AuthorizationPolicies control which services can communicate with each other.

```bash
# List all AuthorizationPolicies in namespace
kubectl --context=<ctx> -n <ns> get authorizationpolicy

# View policy details
kubectl --context=<ctx> -n <ns> get authorizationpolicy <name> -o yaml
```

### Common AuthorizationPolicy Issues

**Issue: RBAC access denied (403)**

```bash
# Check which policies apply to the workload
kubectl --context=<ctx> -n <ns> get authorizationpolicy -o json | \
  jq '.items[] | {name: .metadata.name, action: .spec.action, rules: .spec.rules}'

# Look for:
# 1. DENY policies that match the caller
# 2. Missing ALLOW rules for the calling service's principal
# 3. Wrong namespace in the source principal
```

**Istio RBAC principal format:**
```
cluster.local/ns/<source-namespace>/sa/<source-service-account>
```

**Debug authorization decisions:**
```bash
# Check Envoy proxy access logs for RBAC decisions
kubectl --context=<ctx> -n <ns> logs <pod> -c istio-proxy --tail=50 | grep "rbac"

# ⚠ MUTATION — Enable Envoy debug logging temporarily (changes proxy log level).
# Confirm with user. Reset to info when done.
istioctl --context=<ctx> -n <ns> proxy-config log <pod> --level rbac:debug
# After debugging: reset to info
# ⚠ MUTATION — resets proxy log level
istioctl --context=<ctx> -n <ns> proxy-config log <pod> --level rbac:info
```

## RequestAuthentication Debugging

The `basic-application` chart can configure JWT validation via RequestAuthentication.

```bash
# Check RequestAuthentication resources
kubectl --context=<ctx> -n <ns> get requestauthentication -o yaml

# Common issue: JWT validation fails because:
# 1. JWKS URI is unreachable from the pod
# 2. Token issuer doesn't match the RequestAuthentication issuer field
# 3. Token audience doesn't match
```

## ServiceEntry Debugging

ServiceEntries allow access to external services from within the Istio mesh.

```bash
# List ServiceEntries
kubectl --context=<ctx> -n <ns> get serviceentry

# View details
kubectl --context=<ctx> -n <ns> get serviceentry <name> -o yaml
```

**Issue: External service unreachable (connection timeout)**
- If Istio's outbound traffic policy is `REGISTRY_ONLY`, a ServiceEntry is required
- Check if the external host has a ServiceEntry:

```bash
kubectl --context=<ctx> -n <ns> get serviceentry -o json | \
  jq '.items[] | {name: .metadata.name, hosts: .spec.hosts, ports: .spec.ports}'
```

## Envoy Proxy Debugging

The Istio sidecar (Envoy) is responsible for all traffic routing. When other debugging steps fail:

```bash
# Check proxy status (is the sidecar synced with Istiod?)
istioctl --context=<ctx> -n <ns> proxy-status

# Check proxy config for a specific pod
istioctl --context=<ctx> -n <ns> proxy-config route <pod>
istioctl --context=<ctx> -n <ns> proxy-config cluster <pod>
istioctl --context=<ctx> -n <ns> proxy-config endpoints <pod>

# Check if the destination is in the proxy's endpoint list
istioctl --context=<ctx> -n <ns> proxy-config endpoints <pod> | grep <destination-svc>

# Envoy access logs
kubectl --context=<ctx> -n <ns> logs <pod> -c istio-proxy --tail=100
```

## Telemetry Configuration

The `basic-application` chart can configure Istio Telemetry (metrics, tracing, access logging).

```bash
# Check Telemetry resources
kubectl --context=<ctx> -n <ns> get telemetry -o yaml

# Check if access logging is enabled
kubectl --context=<ctx> -n <ns> get telemetry -o json | \
  jq '.items[]?.spec.accessLogging'
```
