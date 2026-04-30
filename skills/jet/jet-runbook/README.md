# JET Runbook Generator

Generate comprehensive runbooks for JET (Just Eat Takeaway.com) applications and services. This skill helps create operational documentation that describes service purpose, dependencies, monitoring, alerting, and troubleshooting guides following the official JET runbook standards. Runbooks are a requirement for every JET service that are being deployed into production.

## Installation

```bash
npx skills add git@github.je-labs.com:ai-platform/skills.git
```

## Prerequisites

### Agent Skills

| Skill | Purpose |
|-------|---------|
| `jet-datadog` | (Optional) Query existing dashboards, monitors, and service metrics |
| `jet-company-standards` | (Optional) Check Backstage for existing service metadata |

## Usage

Once installed, the skill is automatically triggered when you:

- Create, write, or generate runbooks
- Create operational documentation for services
- Document service dependencies and architecture
- Set up production readiness documentation
- Create troubleshooting guides for JET services

## What Gets Generated

The skill creates complete runbooks that include:

- **Service Overview** - Purpose, business impact, tier, and markets
- **Dependencies** - Internal/external dependencies with timeout configurations
- **Monitoring & Alerts** - Dashboard links and alert configurations
- **Troubleshooting** - Alert response procedures and known issues
- **Disaster Recovery** - Backup and restoration procedures
- **Security & Compliance** - PCI-DSS, GDPR, and access control documentation

All runbooks follow the official JET template and are ready to be linked via Backstage.

## Integration

This skill works seamlessly with:

- **jet-company-standards** - Checks Backstage for service metadata
- **jet-datadog** - Checks existing dashboards, logs, and monitoring

## Support

For questions or issues with this skill, please reach out to the Platform Assurance Team
