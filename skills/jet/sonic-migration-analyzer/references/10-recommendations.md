# Recommendations Framework

Provide guidance on these areas (tailor to detected patterns):

1. **Sonic Pipeline Eligibility Check FIRST** (if .NET/Go/Python/Java single repo - consider Sonic Pipeline instead of manual GitHub Actions)
   - If eligible: Suggest .sonic/sonic.yml approach, note that manual workflows aren't needed
   - If not eligible: Suggest manual goldenpath with GitHub Actions
2. **Platform onboarding** (follow Getting Started guide - onboard team, onboard project with ONE project for all environments, request tool access, setup local tooling)
3. **Environment Mapping Strategy** (current envs → target bulkheads, market-based selection)
4. **Suggested timeline with phases** (QA → Staging → Prod, per-bulkhead validation)
5. **Potential training needs** (Helmfile, K8s, basic-application chart)

## For L-JE EC2 with JustSaying

1. **Phase 1 (Likely Required - Evaluate Applicability)**: MeX migration (2-3 weeks)
   - Identify ALL producers, co-publishers, consumers using same SNS/SQS
   - Check MessageExchange repo (`git@github.je-labs.com:messaging-integrations/MessageExchange.git` spec/services/) for existing specs
   - Use Marmot documentation platform to find existing MeX migrations
   - Coordinate with other teams sharing resources to avoid blockers
   - Check for JustSayingStack usage - if present, migrate to JustSaying v7 first
   - **Sub-phase 1a**: Create AsyncAPI spec with status `importing`
     - Define environments, tenants, interopStrategy, naming patterns
     - For consumers: Ensure producer is already in MeX (`draft` or `live` status)
     - Merge PR → auto-deploy non-prod → request prod deployment
     - Test import success (NO policy changes at this stage)
   - **Sub-phase 1b**: Set status to `live`
     - Enables MeX policies & cross-account networking
     - Policies WILL change - monitor components carefully
     - Can be done phased by environment (QA → Staging → Prod)
2. **Phase 2**: Config/secrets migration (1-2 weeks)
3. **Phase 3**: Goldenpath + Workload Roles (1-2 weeks)
4. **Phase 4**: Testing + traffic split (2-3 weeks)

## For RefArch Eligible for Sonic Pipeline

1. **Use Sonic Pipeline** (replaces manual workflows entirely)
   - Create .sonic/sonic.yml config file
   - Install Sonic GitHub App in org
   - Add sonic-pipeline tag to Platform Metadata
   - NO GitHub Actions workflows needed
2. Migrate secrets → OneSecrets
3. Update alerts → Datadog
4. Deploy with Sonic orchestration

## For Any Platform with Traffic Split

1. **CRITICAL**: Verify zero traffic to legacy platform before decommissioning (check DataDog metrics)
2. Document rollback procedures
3. Monitor health/latency/errors at each split percentage
4. Test in non-prod first
