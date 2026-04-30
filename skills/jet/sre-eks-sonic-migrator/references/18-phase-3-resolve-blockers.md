# Phase 3: Resolve Blockers

**Goal**: Address blocking issues before proceeding. Skip if none found.

**Load**: [07-mex-and-messaging.md](07-mex-and-messaging.md) (if messaging detected)

For each BLOCKING item, present in plain language:

## JustSayingStack

> "Your service uses **JustSayingStack** for messaging. This conflicts with Message Exchange (MeX) which is required in Sonic Runtime. You need to migrate to JustSaying v7 first."
>
> - Pause migration and fix first
> - Continue anyway (messaging won't work)

## Monorepo

> "Your repository contains multiple services. Check current Sonic Pipeline docs for monorepo support status."
>
> - Proceed with GitHub Actions instead
> - Pause and restructure repo first
> - Ask in #help-sonic for guidance

For WARNING items, inform and note extra work. Do not block.

## Legacy Domains (`.tkwy.cloud`, `internal.takeaway.local`)

If `LEGACY_DOMAIN_REFS` is populated from Phase 2.3a:

> "Your service references **legacy domains** that are not supported in Sonic Runtime:"
>
> | File | Reference |
> |------|-----------|
> | {file1} | `{matched-reference1}` |
> | {file2} | `{matched-reference2}` |
>
> "These domains (`*.tkwy.cloud`, `internal.takeaway.local`) are not available in Sonic Runtime environments. They must be replaced with GlobalDNS equivalents (`jet-internal.com` / `jet-external.com`)."
>
> **Resolution options:**
>
> - **Replace now** — Update references to GlobalDNS addresses as part of this migration. Map each legacy domain to its `jet-internal.com` equivalent (e.g., `servicename.int.staging.tkwy.cloud` → `servicename.{project-id}.staging.jet-internal.com`).
> - **Replace before migration** — Pause the Sonic Runtime migration, update the legacy domain references in the SRE-EKS deployment first, verify they work, then resume migration.
> - **Ask for guidance** — Post in `#help-core-platform-services` or `#help-sonic` for advice on your specific domain usage.
>
> "Would you like me to attempt automatic mapping of the legacy domain references to their GlobalDNS equivalents?"

If the user agrees to automatic mapping, replace detected references in the generated source repo changes (Phase 5). If the domains are used for service-to-service communication, map to NG-records. If for external access, map to `jet-external.com` records.

If the user specifies that they want to resolve these references themselves before migration, note `LEGACY_DOMAINS_PENDING = true` and add a reminder in Phase 5.5 review.

If the user asks for help in Slack, provide details to include in the ask:

> "I'm migrating `{service-name}` from SRE-EKS to Sonic Runtime. The service references the following legacy domains: `{domain-list}`. What are the correct GlobalDNS (`jet-internal.com`) equivalents for these endpoints?"

If the user specifies that they want

If user chooses 'Ask for #help-sonic for guidance', provide the relevant details to include in the ask (e.g., "I have a monorepo with services A, B, C. I want to migrate to Sonic Runtime but I'm not sure how to handle the monorepo structure. Can I get guidance on best practices for migrating a monorepo to Sonic Runtime?").
