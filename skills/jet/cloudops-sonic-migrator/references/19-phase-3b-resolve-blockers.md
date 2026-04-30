# Phase 3b: Resolve Blockers

**Goal**: Address blocking issues identified in Phase 3 before proceeding. Skip if none found.

**Load**: [20-mex-and-messaging.md](20-mex-and-messaging.md) (if messaging detected)

This phase only handles blockers that require **external action or user decisions** — warnings
that Phases 4-6 handle automatically are NOT addressed here.

---

## Auto-Resolution

Before presenting blockers to the user, **attempt automatic resolution** where possible:

### Platform-specific domain dependencies

Services must not use platform-specific domains (e.g., `*.eks.tkwy-*.io`, `*.service` mesh
addresses) to reach dependencies — these are not resolvable from Sonic Runtime.

For each platform-specific domain found in the repo:

1. Extract the service name from the domain (e.g., `jetms-user-api` from `jetms-user-api.jetms.p.eks.tkwy-prod.io`)
2. Search the `IFA/route53` repo for an existing Global DNS record:
   ```bash
   gh repo clone github.je-labs.com/IFA/route53 /tmp/route53 -- --depth 1
   grep -r "{service-name}" /tmp/route53/ --include="*.yml"
   ```
3. Search Backstage for the dependency:
   ```bash
   curl -s -H "Authorization: Bearer $BACKSTAGE_API_KEY" \
     "$BACKSTAGE_BACKEND_URL/api/search/query?term={service-name}&types%5B0%5D=techdocs" \
     | jq '.results[:3]'
   ```
4. Check PlatformMetadata for the dependency:
   ```bash
   gh api --hostname github.je-labs.com \
     /repos/metadata/PlatformMetadata/contents/Data/global_features/{service-name-no-hyphens}.json \
     --jq '.content' | base64 -d | jq '{ id, owners, tier }'
   ```

See [07-traffic-split.md — Active Resolution Procedure](07-traffic-split.md) for the full
lookup procedure and infrastructure service DNS patterns (`tk-<service>`).

**If `*.jet-internal.com` record found in Route53**: Auto-resolve — note the endpoint as the
replacement. Remove the blocker.

**If NOT found**: Present to the user (see below).

### Other auto-checks

Apply the same pattern to any blocker where automated verification is possible (e.g., check
if a Sonic Runtime project exists, check if a messaging library version is compatible).

---

## User-Facing Blocker Resolution

For each blocker that was NOT auto-resolved, present options in plain language:

### Dependency on platform-specific DNS

> "The service depends on **{dependency-name}** via a platform-specific domain
> (`{platform-domain}`). This domain won't be resolvable from Sonic Runtime."
>
> 1. **Ask the owning team ({team}) to expose via Global DNS** — proceed with placeholder
> 2. **Wait for that dependency to migrate first** — pause this migration
> 3. **Proceed with placeholder** — use `{service-name}.{env}.jet-internal.com`, resolve before go-live

If user chooses option 1 or 3, store as `DEFERRED_BLOCKERS[]` with:
- `service`: upstream service name
- `placeholder_url`: `{service-name}.{env}.jet-internal.com`
- `original_url`: the `*.eks.tkwy-*.io` URL
- `status`: deferred

These deferred blockers will be:
- Used as placeholder URLs in Phase 5 generation
- Highlighted in Phase 5.5 review
- Listed as pre-go-live requirements in Phase 7 summary

### JustSayingStack

> "Your service uses **JustSayingStack** for messaging. This conflicts with Message Exchange (MeX) which is required in Sonic Runtime. You need to migrate to JustSaying v7 first."
>
> - Pause migration and fix first
> - Continue anyway (messaging won't work)

### Monorepo

> "Your repository contains multiple services. Check current Sonic Pipeline docs for monorepo support status."
>
> - Proceed with GitHub Actions instead
> - Pause and restructure repo first
> - Ask in #help-sonic for guidance

### Other blockers

For any blocker not listed above, present the issue clearly with:
- What was detected
- Why it blocks migration
- Available options (fix first, defer, proceed with workaround)

---

## Outcome

If user chooses "Ask in #help-sonic for guidance", provide the relevant details to include
in the ask.

**Gate**: All blockers must be resolved or explicitly deferred before proceeding to Phase 4.