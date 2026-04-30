# Sonic Runtime Migration Analyzer

A GitHub Copilot CLI [Agent Skill](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills) that analyzes git repositories to assess migration difficulty to Sonic Runtime (OneEKS). Provides comprehensive scoring (0-100), timelines, effort estimates, and actionable recommendations.

## What It Does

- **Platform Detection**: Identifies current platform (Marathon, L-JE EC2, RefArch EKS, SRE-EKS, CloudOps, Lambda)
- **Migration Scoring**: Rates complexity from EASY (0-25) to COMPLEX (76-100)
- **Effort Estimation**: Provides realistic timelines and team size recommendations
- **Actionable Roadmap**: Phase-by-phase migration guidance
- **Critical Blockers**: Highlights MUST-RESOLVE items (e.g., MeX for L-JE EC2)

## Difficulty Levels

- 🟢 **EASY** (0-25): 1-2 weeks, 1-2 developers
- 🟡 **MODERATE** (26-50): 2-4 weeks, 2-3 developers
- 🟠 **CHALLENGING** (51-75): 1-2 months, 3-4 developers + support
- 🔴 **COMPLEX** (76-100): 2-4 months, full team + significant support

## Requirements

- GitHub Copilot Pro, Pro+, Business, or Enterprise subscription
- [GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/set-up/install-copilot-cli) installed

## Installation

This skill is part of the [JET AI Platform skills collection](https://github.je-labs.com/ai-platform/skills). Install the full collection using the Copilot Skills CLI:

```bash
npx skills add git@github.je-labs.com:ai-platform/skills.git
```

To update to the latest version, re-run the same command.

## Usage

Navigate to any repository and start Copilot CLI in interactive mode:

```bash
# Navigate to any repository
cd /path/to/your/repository

# Start Copilot CLI
copilot
```

Copilot will automatically load the skill when you ask questions about Sonic Runtime migration. Just ask naturally:

- "Analyze this repository for Sonic Runtime migration"
- "What's the migration difficulty to OneEKS?"
- "What are the critical blockers for migrating to Sonic Runtime?"
- "Show me a migration timeline to Sonic Runtime"
- "Is MeX migration required for this app?"

The skill is automatically activated based on keywords like "Sonic Runtime", "OneEKS", "migration difficulty", "platform modernization", etc.

## What Gets Analyzed

The skill examines:

### Platform Indicators

- **Deployment configs**: Dockerfile, helmfile.d/, .deploy/, marathon.json, serverless.yml
- **CI/CD**: .github/workflows/, .gitlab-ci.yml
- **Language files**: package.json, go.mod, pom.xml, *.csproj, requirements.txt
- **Platform markers**: Consul, Vault, JustSaying, systemd

### Key Patterns

- **JustSaying/SNS/SQS** → Requires MeX migration (CRITICAL for L-JE EC2)
- **Consul** → OneConfig migration needed
- **JE Vault/AWS Secrets** → OneSecrets migration needed
- **.service DNS** → Global DNS migration needed
- **Marathon JSON** → Full containerization required

### Migration Complexity Factors

- Containerization status
- Messaging patterns (JustSaying → MeX)
- Configuration management (Consul → OneConfig)
- Secrets management (Vault → OneSecrets)
- AWS IAM/cross-account access
- Monitoring setup (→ Datadog)
- Traffic split requirements

## Example Output

```markdown
# Sonic Runtime Migration Analysis

🟠 Migration Difficulty: CHALLENGING (Score: 58/100)

**Current Platform:** L-JE EC2
**Detection Confidence:** high

**✅ Positive Factors:**
- Application is containerized with Dockerfile
- Uses multi-stage Docker build

**⚠️ Key Challenges:**
- VM-based deployment requires full K8s migration
- JustSaying usage requires MeX migration (BLOCKING)
- Consul config needs OneConfig migration
- Traffic split required for zero-downtime cutover

**Estimated Effort:** 6-8 weeks
**Team Size:** 3-4 developers + platform support

## 🚫 Critical Blockers

⚠️ **MeX Migration (MANDATORY)**: Application uses JustSaying for SNS/SQS. 
Must migrate to MeX before Sonic deployment (contact #help-messaging-integrations)

## 📋 Recommendations

### Phase 1: MeX Migration (Weeks 1-2) - BLOCKING
- Work with #help-messaging-integrations team
- Configure MeX cross-account trust policies
- Update application code from JustSaying to MeX client
- Test messaging in dev environment

### Phase 2: Configuration & Secrets (Weeks 3-4)
- Migrate Consul configs to OneConfig (Helmfile values)
- Migrate JE Vault secrets to OneSecrets
- Create Workload Roles for AWS access

### Phase 3: Goldenpath & Deployment (Weeks 5-6)
- Adopt helmfile.d/ structure
- Configure basic-application chart
- Set up Datadog monitoring

### Phase 4: Testing & Cutover (Weeks 7-8)
- Deploy to dev/staging
- Implement traffic split (10% → 50% → 100%)
- Monitor and validate

...
```

## Troubleshooting

### Skill Not Loading

1. **Verify installation**:

   ```bash
   ls ~/.copilot/skills/sonic-migration-analyzer/SKILL.md
   ```

2. **Check SKILL.md format**:
   - Must be named exactly `SKILL.md` (case-sensitive)
   - Must have valid YAML frontmatter

3. **Restart Copilot**: Exit and restart `copilot` after installation

## Resources

- [GitHub Copilot CLI Documentation](https://docs.github.com/en/copilot/concepts/agents/about-copilot-cli)
- [Agent Skills Specification](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills)
- [Sonic Runtime Documentation](https://oneeksdocs.internal/)

## License

Proprietary - JET Platform Engineering

---

**Maintained by:** Core Platform Services EU  
**Repo:** [github.je-labs.com/ai-platform/skills](https://github.je-labs.com/ai-platform/skills)  
**Platform:** Sonic Runtime (OneEKS)
