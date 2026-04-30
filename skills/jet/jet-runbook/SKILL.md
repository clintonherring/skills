---
name: jet-runbook
description: Generate comprehensive runbooks for JET (Just Eat Takeaway.com) applications and services. Use when creating documentation that describes service purpose, dependencies, operational procedures, monitoring, alerting, and troubleshooting guides. Triggers on requests to create, write, or generate runbooks for JET services provided the service name, tier, and desired repository path.
metadata:
  owner: platform-assurance
---

# JET Runbook Generator

Generate comprehensive runbooks for JET applications and services following the official JET runbook standards. Runbooks are essential operational documents that help engineers understand, operate, and troubleshoot services in production.

## Overview

This skill helps create runbooks that document:
- Service purpose and business impact
- Internal and external dependencies
- Monitoring and alerting configurations
- Troubleshooting procedures
- Disaster recovery processes
- Security and compliance information

All runbooks created with this skill follow the JET runbook template and must be linked in Backstage. This skill is only used for creating static documents. It does not investigate or assess the service's production readiness or reliability.

## Prerequisites

Before creating a runbook, verify you have:

1. **Service/Application name** - what is this runbook for?
2. **Output location** - where should the runbook be saved? (repository path)
3. **Service information** - gather details about the service's purpose, tier, markets, dependencies

**Do not assume defaults.** Ask the user for these details if not provided.

## Runbook Requirements

According to JET standards, all runbooks **MUST include**:

### 1. Service Overview
- **Purpose** - what does the application/service do?
- **Business impact** - what happens if it fails?
- **Tier** - 1, 2, or 3 (criticality level)
- **Markets** - UK, NL, DE, i18N, etc.
- **Support channel** - Slack channel for the team

### 2. Dependencies Documentation

**Internal Dependencies (JET-hosted services):**
- Name of the dependency
- Communication method (HTTP, Async Messaging, gRPC)
- Timeouts for synchronous operations
- Justification for timeout values

**External Dependencies (AWS, Aiven, 3rd parties):**
- Provider name and service used
- Communication method
- Timeouts for synchronous operations  
- Justification for timeout values

### 3. Required Links
- Monitoring dashboards (Datadog)
- Logging queries for significant events
- Alert configurations
- Health check endpoints and retry policies
- Backstage entry
- Code repositories
- Deployment pipelines

### 4. Data Stores
- Name and type of each data store
- Description of how it's used
- Whether data is authoritative
- Backup status

### 5. Monitoring & Alerts
- Links to monitoring dashboards per environment
- Alert configurations with links
- Alert response procedures

## Workflow

Follow these steps when creating a runbook:

### Step 1: Gather Service Information

Before writing anything, collect the following from the user or available sources:

**Required information:**
- Service/feature name
- Service purpose and functionality
- Tier (1, 2, or 3)
- Markets served
- Team responsible (for support channel)

**Information to research (if possible):**
- Check Backstage for existing service metadata
- Search for deployment configurations (GitHub Actions, Sonic)
- Look for existing monitoring dashboards (Datadog)
- Check for alert configurations
- Find health check endpoints

Ask the user: "I need some information to create a complete runbook. Can you provide:
1. The service name and its purpose
2. What tier is this service? (1=critical, 2=important, 3=standard)
3. Which markets does it serve? (UK, NL, DE, i18N, etc.)
4. What's the team's Slack support channel?"

### Step 2: Determine Runbook Location

Ask the user where the runbook should be saved:
- **Code repository** (recommended) - creates versioned markdown file in the repo
- **Confluence** - requires manual creation, provide formatted content

Recommended path in repository: `docs/RUNBOOK.md` or `RUNBOOK.md` at root level.

### Step 3: Research Dependencies

Before asking the user for all dependency details, try to gather information from the repository:

**For HTTP APIs:** Run `./scripts/research_http_dependencies.sh` to find HTTP clients and timeout configurations

**For message-based systems:** Run `./scripts/research_messaging_dependencies.sh` to find Kafka/SNS/SQS configurations

**For data stores:** Run `./scripts/research_datastore_dependencies.sh` to find database connection configurations

After research, compile what you found and ask the user to fill in gaps:
"I found these potential dependencies: [list]. Can you confirm and provide:
- Any missing internal/external dependencies?
- Timeout values for synchronous calls?
- Justification for these timeouts?"

### Step 4: Research Monitoring & Alerting

**For Datadog dashboards and alerts:**
Use the jet-datadog skill if available to search for existing dashboards and monitors.

If jet-datadog skill is not available, ask the user:
"Can you provide links to:
1. Datadog dashboards for this service?
2. Alert/monitor configurations?
3. Health check endpoints?"

If the user cannot provide these links, proceed with placeholders in the runbook (e.g., `{PLACEHOLDER: Add Datadog dashboard link}`) and note which sections need to be completed manually.

### Step 5: Generate the Runbook

Use the template structure from `runbook-template.md` as your guide. Create a complete runbook with all sections filled in based on gathered information.

**Critical sections to complete:**
1. **Summary** - clear description with business impact
2. **Monitoring** - links to logs and metrics by environment
3. **Alerts** - table of alerts with links to configurations
4. **Useful Links** - all required links (Backstage, repos, dashboards, pipelines)
5. **Dependencies** - complete tables for data stores, APIs, and events
6. **Interface** - document exposed APIs and emitted events (if applicable)
7. **Known Scenarios** - troubleshooting guides for common issues
8. **Troubleshooting Guides** - alert response procedures
9. **Disaster Recovery** - backup and restoration procedures

### Step 6: Remove Inapplicable Sections

After creating the runbook, remove sections that don't apply:
- If no events are consumed/published, remove the Events sections
- If no APIs are exposed, remove the APIs/Endpoints section
- If no data stores are used, remove the Data Stores section
- If no feature flags exist, remove that subsection

**Always keep:** Summary, Monitoring, Alerts, Useful Links, Dependencies (even if some subsections are empty)

### Step 7: Validate Completeness

Before presenting the final runbook, verify:

1. All required MUST-HAVE items are documented:
- Service purpose and business impact
- All dependencies with timeout values
- All required links (monitoring, alerts, health checks, Backstage)

2. Tables are properly formatted and filled in
3. Placeholder text like `{Feature Name}` is replaced
4. Links use proper markdown format `[Link Text](URL)`
5. Badge links are properly formatted (see template for examples)

### Step 8: Link to Backstage

Remind the user: "This runbook must be linked via Backstage. Please update your service's Platform Metadata to include a link to this runbook."

## Template Structure Reference

The runbook should follow this structure (based on `runbook-template.md`):

1. **Title** - Service/Feature name
2. **Summary** - Purpose, impact, tier, markets, scorecard/CI/CD badges
3. **Monitoring** - Environment-specific links to logs and metrics
4. **Alerts** - Alert configurations by environment
5. **Useful Links** - All essential links (code, infra, Backstage, Datadog, pipelines, docs)
6. **PagerDuty** - Escalation policy and schedule (if applicable)
7. **Scalability** - Auto-scaling configuration and behavior
8. **Dependencies**
   - Data Stores - table with name, type, description, authoritative, backed up
   - APIs - table with service, scope, description, retries, timeout
   - Events - table with message bus, type, event name, description, queue usage, replayability
9. **Interface**
   - Events - table of emitted events (if applicable)
   - APIs - base URIs and endpoint table (if service exposes APIs)
10. **Handlers** - Description of message handlers (if applicable)
11. **Known Scenarios**
    - Possible Issues
    - Feature Flags
    - Running it manually
    - Other scenarios
12. **Troubleshooting Guides** - Alert response table
13. **Testing** - Feature testing and load testing details
14. **Health Checks** - Health check endpoints table
15. **Security** - Security configurations and compliance
16. **Disaster Recovery**
    - Feature Recovery
    - Data Backup
    - Authoritative Data Recovery
    - Projection Rebuilding
17. **Rollout/Rollback Requirements** - Special deployment considerations

## Best Practices

### Badge Links

Use proper badge formatting for scorecard, CI/CD, and support channels:

**Score Card:**
```markdown
[![Score Card](https://scorekeeper.eu-west-1.production.jet-internal.com/api/features/global/{feature}/badge)](https://backstage.eu-west-1.production.jet-internal.com/catalog/default/component/{feature}/scorecard)
```

**GitHub Actions:**
```markdown
[![GHA Build](https://github.je-labs.com/{OWNER}/{REPOSITORY}/actions/workflows/{WORKFLOW_FILE}/badge.svg)](https://github.com/{OWNER}/{REPOSITORY}/actions/workflows/{WORKFLOW_FILE})
```

**Support Channel:**
```markdown
[![Support Channel](https://img.shields.io/badge/slack-<channel-name>-green?style=flat-square&logo=slack)](https://justeat.slack.com/app_redirect?channel=<channelName>)
```

### Timeout Documentation

When documenting timeouts for dependencies, always include:
1. **The timeout value** (e.g., "5 seconds", "30s", "500ms")
2. **Justification** - why this value was chosen (e.g., "Based on p99 latency + buffer", "Downstream service SLA is 3s", "Prevents cascade failures")

Example:
```markdown
| Service | Timeout | Justification |
|---------|---------|---------------|
| Payment API | 5s | Downstream SLA is 3s, +2s buffer for network/retries |
```

### Dependency Scope

When documenting APIs, specify scope clearly:
- **Internal** - JET-hosted services
- **External** - Third-party services outside JET infrastructure
- **AWS** - AWS-managed services (S3, DynamoDB, Lambda, etc.)

### Authoritative Data

Data is **authoritative** if your service is the source of truth for that data. If data can be rebuilt from another source, it's not authoritative.

Examples:
- Authoritative: Customer orders, payment transactions, user profiles
- Not authoritative: Cached data, read models, projections that can be rebuilt

### BigQuery Event Tables

When documenting events in BigQuery, use the format:
```
just-data.production_je_justsaying.[event]_[tenant]_[year]
```

Example: `just-data.production_je_justsaying.order_placed_uk_2026`

## Common Issues & Tips

### Missing Information

If critical information is not available:
1. Add a placeholder with `{PLACEHOLDER: description of what's needed}`
2. Add a comment in the Summary noting incomplete sections
3. Tell the user which information needs to be filled in manually

### Service Without External Dependencies

This is valid. Document it explicitly:
```markdown
### External Dependencies

This service has no external dependencies.
```

### Service Without Data Stores

Also valid. Document it:
```markdown
### Data Stores

This service does not persist data.
```

### Multiple Environments

Always provide environment-specific tables where applicable:
- Monitoring links per environment
- Alert configurations per environment
- API base URIs per environment

## Integration with Other Skills

This skill works well with:

- **jet-datadog** - Use to query for existing dashboards, monitors, and service metrics
- **jet-company-standards** - Use to check Backstage for existing service metadata

When these skills are available, use them to gather information automatically before asking the user.

## Validation Checklist

Before finalizing a runbook, confirm:

- [ ] Service name and purpose clearly documented
- [ ] Business impact statement included
- [ ] Tier and markets specified
- [ ] All dependencies documented with timeout values
- [ ] Monitoring dashboard links provided
- [ ] Alert configuration links provided
- [ ] Health check endpoints documented
- [ ] Backstage link included
- [ ] Code repository link included
- [ ] Deployment pipeline link included
- [ ] Support channel specified
- [ ] All placeholder text replaced
- [ ] All tables properly formatted
- [ ] Inapplicable sections removed
- [ ] User reminded to link runbook in Backstage via Platform Metadata

## Output Format

Always output the runbook as a complete markdown file. Do not create multiple files unless specifically requested. The runbook should be self-contained and ready to be saved to the specified location.

## References

- [runbook-docs.md](./references/lcc-runbook-docs.md) - Official JET runbook requirements
- [runbook-template.md](./references/runbook-template.md) - Complete runbook template with all sections