# JET Strategic Context

> **Last updated**: 2026-03-27
>
> This file provides the baseline strategic context for the feasibility panel.
> It should be periodically updated as JET's priorities and architecture evolve.
> Users can override or supplement this context at invocation time.
>
> **Data sources**: JET Confluence (SDLC/Change Management, Platform
> Consolidation, Helix AI Platform, Reliability H1 Pitches, Secure Software
> Development Policy, Architecture Decision Records), Jira (OKR project,
> Initiatives, Strategic Epics).

## Company Overview

**Just Eat Takeaway.com (JET)** is one of the world's largest online food
delivery marketplaces, operating across multiple markets in Europe, the UK,
Australia, New Zealand, and beyond. JET connects consumers with restaurants and
other food partners, providing ordering, payment, logistics (delivery), and
restaurant tooling.

**Vision**: "Empowering everyday convenience" (set on a 5+ year cadence).

**CTO**: Mert Öztekin

## Organizational Structure

### Product & Technology (P&T) Pillars

JET's P&T organization is structured into the following pillars:

| Pillar | Focus |
|---|---|
| **Customer** | Consumer-facing experiences, ordering, discovery |
| **JET Ventures** | New business lines and strategic bets |
| **Customer and Partner Care** | Support, partner experience |
| **Courier and Logistics** | Delivery operations, courier experience, routing |
| **Fintech** | Payments, financial products, invoicing |
| **Platform Consolidations** | Converging tech stacks across markets (Sonic) |
| **Information Org** | Data platform, analytics, BI |
| **Product Operations** | Cross-cutting product processes and tooling |

### Planning Cadence

- **Long Term Group Strategy** → **Priorities** (annual) → **Initiatives**
  (quarterly)
- P&T prioritisation is aligned with JET's business cycle
- Agile methodology: 2-week sprints, Jira-driven tracking
- Work hierarchy: **Initiatives → Epics → Tasks**

### SDLC Process

JET follows a two-phase SDLC:

1. **Discovery**: Value, Usability, Feasibility, Viability assessment
2. **Delivery**: Plan → Build → Test → Release → Maintain

### Decision-Making Patterns

- Major technical decisions: **Architecture Decision Records (ADRs)** published
  on Confluence (e.g., ADR-037 Checkout/GBO consolidation, ADR-0002 Assignment
  Planning Service)
- Architecture governance: Principal Architects and architecture guilds
- Resource allocation: Quarterly planning cycles aligned to OKRs
- Cross-cutting concerns: Architecture guild, security review board
- Vendor/buy decisions: Procurement process + architecture review

### Team Capacity Considerations

- Teams are generally fully allocated to their domain roadmaps
- New initiatives require either new headcount or reprioritization
- Hiring timelines: 3-6 months from approval to productive engineer
- Cross-team projects require explicit coordination overhead
- Platform teams have long backlogs of platform work

## Current Strategic Priorities

### Tier 1: Critical Priorities

1. **Platform Consolidation (Sonic)**
   Platform consolidation is an explicitly stated key strategic objective for
   JET. The target is to converge ALL services onto **Sonic Runtime (OneEKS)**
   and **Sonic Pipeline** (standardised CI/CD).

   - Multiple migration paths exist from: SRE-EKS, RefArch EKS, Marathon,
     CloudOps, Lambda (early adopter), SKIP ECS
   - AI-powered migration tooling has been built: Sonic Migration Analyser,
     SRE-EKS Migrator, CloudOps Migrator, Pipeline Migration Skill
   - Migration complexity scoring: 0-25 Easy, 26-50 Moderate, 51-75
     Challenging, 76-100 Complex
   - JetConnect pending SmartGateway/Istio migrations
   - Active OKR: **OKR-443** — Sonic Runtime (OneEKS) RefArch & Marathon
     Migrations

2. **Profitability & Unit Economics**
   Reducing missed orders and operational costs. The key metric is **Missed
   Orders** with a budget of 0.04%. In 2025, missed order incidents cost
   approximately **$20.5M**. Active OKRs include:
   - **OKR-127**: Automate Missed Order attribution to funnel/pillar/team
   - **OKR-174**: Rejection cost awareness in courier pay
   - **OKR-177**: Optimize Unassigned Deliveries (HAL)
   - **OKR-139**: Real-time incentives

3. **Domain Consolidation**
   Active consolidation of business domains. Example: Checkout API (CAPI)
   being consolidated into the **Global Basket Orchestrator (GBO)** for unified
   purchase management (ADR-037). This pattern — consolidating fragmented
   domain services into unified orchestrators — is a recurring strategic theme.

### Tier 2: Important Priorities

4. **AI & Automation (Helix Platform)**
   JET is investing heavily in AI through the **Helix Agentic AI Platform** —
   a centralized platform providing every engineering team with infrastructure
   to build, deploy, observe, and evaluate AI agents at scale.

   Helix capabilities roadmap:
   - LLM Gateway
   - Prompt Management
   - Evals Framework
   - Tracing & Observability
   - Short-Term Memory
   - Human-in-the-Loop
   - Agent-to-Agent Orchestration
   - SDK
   - Self-Serve Onboarding
   - Auth/ABAC (Attribute-Based Access Control)

   Helix uses a **capability scoring model** for prioritisation:
   - Demand (25) + Business Impact (25) + Confidence (15) + Strategic
     Alignment (20) + Feasibility (15) = max 100
   - Priority bands: **80-100 NOW**, 65-79 NEXT, 50-64 LATER, <50 PARKED

   Related AI initiatives:
   - **Merlin**: AI conversational analyst (data Q&A)
   - **ML Platform Workbench**: Built on Vertex AI for traditional ML
   - **OKR-121**: Developer AI toolset rollout
   - **OKR-119**: Data and analytics integrations — BQ & Merlin integration
     pilots

5. **Reliability & Operational Excellence**
   Major reliability initiatives:
   - **Aegis**: AI-powered reliability orchestrator (projected €2-5.1M savings)
   - **AuRA**: Autonomous reliability assistant
   - **Wargames**: Chaos engineering / gameday exercises
   - **AI-powered performance testing**
   - **Anomaly Detection** systems

   Observability stack:
   - **Datadog** is the primary observability platform
   - Migration in progress toward a **Platform Observability Pipeline**
   - **ODL (Operational Data Lake)** for long-term operational data
   - **MCP Server** infrastructure being built for agentic data access

   Cost optimisation efforts:
   - AWS Managed Prometheus adoption
   - Logstash → Vector migration
   - CloudWatch cost reduction

   Active OKR: **OKR-89** — Improve Platform stability

6. **Data-Driven Decision Making**
   - **BigQuery** data warehouse with **dbt** transformations
   - **Airflow** for orchestration, **Looker** for BI
   - **OKR-252**: Personalised Product Recommendations

### Tier 3: Strategic Bets

7. **New Verticals & Revenue Streams**: Exploring grocery delivery, advertising
   platforms, B2B logistics services, and other adjacencies. JET Ventures
   pillar is dedicated to new business lines.

8. **Mesh Foundations** (**OKR-287**): Service mesh and networking
   infrastructure modernisation.

9. **Enhanced Authentication Experience** (**OKR-251**): Improving auth flows
   across consumer touchpoints.

10. **Logistics Optimisation**: Multiple active OKRs around courier delivery
    optimisation, 3PL integration, and delivery efficiency.

## Active OKRs (from Jira — In Progress)

| OKR | Description |
|---|---|
| OKR-443 | Sonic Runtime (OneEKS) — RefArch & Marathon Migrations |
| OKR-121 | Developer AI toolset rollout |
| OKR-119 | Data & analytics integrations — BQ & Merlin pilots |
| OKR-127 | Automate Missed Order attribution to funnel/pillar/team |
| OKR-252 | Personalised Product Recommendations |
| OKR-174 | Rejection cost awareness in courier pay |
| OKR-177 | Optimize Unassigned Deliveries (HAL) |
| OKR-139 | Real-time incentives |
| OKR-89  | Improve Platform stability |
| OKR-287 | Mesh Foundations |
| OKR-251 | Enhance Authentication Experience |

## Architecture Landscape Overview

### Core Architecture Principles

- **Event-driven architecture**: Services communicate via events (Kafka/SNS/SQS).
  Prefer async messaging over synchronous REST calls where possible. Consent
  propagation uses event-based patterns (RFC documented on Confluence).
- **Domain ownership**: Teams own their domain services end-to-end (build,
  deploy, operate). Bounded contexts aligned with business domains.
- **Platform-first**: Shared platforms and capabilities over point solutions.
  If multiple teams need it, build it as a platform.
- **Consolidation-driven**: Actively consolidating fragmented services into
  unified domain orchestrators (e.g., Checkout API → GBO). New proposals
  that add fragmentation face heavy scrutiny.
- **Cloud-native**: AWS is the primary cloud. Kubernetes (**OneEKS / Sonic
  Runtime**) is the standard compute platform. All services are expected to
  migrate to Sonic.
- **Observability**: Datadog for monitoring, logging, and tracing. SLO-driven
  reliability with missed-order budget (0.04%).

### Key Technology Stack

| Layer | Technology |
|---|---|
| Cloud | AWS (primary), GCP (BigQuery, Vertex AI) |
| Compute | Kubernetes (OneEKS / Sonic Runtime) |
| CI/CD | Sonic Pipeline, GitHub Actions |
| Messaging | Kafka, SNS/SQS, JustSaying |
| Observability | Datadog (primary), Platform Observability Pipeline, ODL |
| Data Platform | BigQuery, dbt, Airflow, Looker |
| AI/ML Platform | Helix (agentic AI), Vertex AI (ML Workbench), Merlin |
| Service Mesh | In evolution (Mesh Foundations OKR-287) |
| API Gateway | JetConnect (pending SmartGateway/Istio migration) |
| Helm Charts | `basic-application` (standard deployment chart) |
| Source Control | GitHub Enterprise (github.je-labs.com) |
| Service Registry | PlatformMetadata, Backstage |

### Shared Platforms & Services

> Use PlatformMetadata and Backstage (via `jet-company-standards` skill) to
> look up specific services at runtime.

- **Identity & Access**: Authentication, authorization, user management
- **Payments (Fintech)**: Payment processing, wallet, invoicing
- **Order Management / GBO**: Order lifecycle, basket orchestration, checkout
- **Delivery / Logistics**: Courier assignment (HAL), route optimization,
  tracking, 3PL integration
- **Restaurant Platform**: Menu management, onboarding, analytics
- **Consumer Platform**: Discovery, search, recommendations, ordering UX
- **Data Platform**: BigQuery warehouse, dbt transformations, Airflow DAGs,
  Looker dashboards, Merlin AI analyst
- **AI Platform (Helix)**: LLM Gateway, prompt management, evals, tracing,
  agent orchestration
- **Notification Platform**: Push, email, SMS notifications
- **Experimentation**: A/B testing, feature flags
- **Reliability**: Aegis orchestrator, AuRA assistant, anomaly detection

### Architecture Debt & Known Challenges

- Multiple legacy systems from acquisitions still in operation — Sonic
  migration is actively addressing this (complexity-scored migration paths)
- Varying levels of Sonic adoption across services (SRE-EKS, RefArch, Marathon,
  CloudOps, Lambda, SKIP ECS still in use)
- Ongoing domain consolidation (e.g., CAPI → GBO) creating temporary
  dual-running systems
- JetConnect gateway pending SmartGateway/Istio migration
- Data consistency challenges across distributed services
- Cross-market feature parity gaps
- Observability stack in transition (Datadog primary, but pipeline and ODL
  being built out)

## Security & Compliance Context

### Security Governance

JET maintains a **Secure Software Development Policy** (v5.0, August 2025),
approved by:
- CTO: Mert Öztekin
- Director of InfoSec: Sherif Mansour
- Director InfoSec R&C: Mark Poen

### Security Programs

- **Security Champions**: Embedded across all P&T pillars — designated
  engineers with security training who act as first-line security advisors
- **AppSec Program**: Threat modeling, penetration testing, secure-by-design
  assessments
- **CI/CD Security**: Segregation of duties enforced, automated vulnerability
  scanning in pipelines, bug bar enforcement (vulnerabilities must meet
  severity thresholds before release)
- **Wiz**: Cloud security scanning for all infrastructure and container images

### AI & Open Source Policies

- **AI coding assistants** (GitHub Copilot): Encouraged for official JET
  projects, **forbidden for personal/non-JET use** on company devices
- **Open source usage**: Must be approved by the **Platforms Strategy and
  Architecture Team** and scanned via Wiz before adoption
- **Open source contribution**: Requires explicit approval process

### Regulatory Requirements

- **GDPR**: JET operates across EU markets. All personal data handling must
  comply with GDPR (consent, right to deletion, data minimization, DPIAs).
  Event-based consent propagation patterns are defined.
- **PCI-DSS**: Payment data handling must comply with PCI-DSS standards.
  Fintech pillar owns compliance.
- **Food Safety**: Varying regulations across markets for food delivery,
  allergen information, and hygiene ratings.
- **Employment/Gig Worker**: Varying regulations across markets regarding
  courier employment status and rights.
- **Data Residency**: Some markets have data residency requirements.

## How to Use This Context

1. **Panel agents** receive this context as part of their Context Brief
2. **The VP of Strategy** should use the Strategic Priorities and Active OKRs
   sections to assess alignment — proposals that conflict with Tier 1
   priorities or active OKRs face an uphill battle
3. **The Principal Architect** should use the Architecture Landscape section
   to assess fit — proposals must align with Sonic consolidation, event-driven
   patterns, and domain ownership principles
4. **The Security Officer** should use the Security & Compliance section,
   particularly the Secure Software Development Policy requirements, AI/open
   source policies, and regulatory requirements
5. **The Engineering Manager** should use the Team Capacity section and Active
   OKRs to ground delivery estimates — teams are fully allocated and new work
   requires reprioritisation
6. **The Devil's Advocate PM** should challenge whether a proposal competes
   with active OKRs for the same resources or attention
7. **The Skeptical Architect** should evaluate whether a proposal adds
   fragmentation counter to the consolidation strategy

## Key Numbers for Calibration

| Metric | Value | Source |
|---|---|---|
| Missed order budget | 0.04% | Reliability H1 Pitches |
| 2025 missed order incident cost | ~$20.5M | Reliability H1 Pitches |
| Aegis projected savings | €2-5.1M | Reliability H1 Pitches |
| Helix capability score — NOW band | 80-100 | Helix Capability Scoring |
| Helix capability score — NEXT band | 65-79 | Helix Capability Scoring |
| Sonic complexity — Easy | 0-25 | Platform Consolidation Guide |
| Sonic complexity — Moderate | 26-50 | Platform Consolidation Guide |
| Sonic complexity — Challenging | 51-75 | Platform Consolidation Guide |
| Sonic complexity — Complex | 76-100 | Platform Consolidation Guide |

## Updating This File

This file should be updated when:
- JET announces new strategic priorities or reorganizations
- Major architecture decisions change the landscape (new ADRs)
- New regulatory requirements emerge
- Significant platform capabilities are added or deprecated
- OKR cycles change (quarterly refresh recommended)

### Recommended Update Procedure

Use a **Jira-first** strategy. Jira is structured data with status fields and
dates — it gives a fast, concrete snapshot of what's actively being worked on.
Confluence is unstructured prose that takes longer to search and synthesize.

**Step 1 — Jira quick check (fast, do this first)**

Query current In Progress OKRs and top-priority Initiatives. Compare against
the Active OKRs table above. Use the `jet-company-standards` skill (acli) to
run queries like:

```
acli jira issue list --project OKR --status "In Progress" --type Initiative
acli jira issue list --project OKR --status "In Progress" --type OKR
```

If the OKR table hasn't materially changed, the strategic context is likely
still current. Stop here.

**Step 2 — Confluence deep dive (only if Jira signals a shift)**

Triggers for a Confluence dive:
- A new OKR or Initiative that doesn't map to any existing priority in this
  file
- A major Initiative you don't recognize (new platform, new domain, reorg)
- An OKR that was Tier 1 is now closed/cancelled (priorities may have shifted)

When triggered, search Confluence for the context behind the new items:
- Strategy documents, architecture decision records (ADRs)
- Platform guides, program pitches, security policy updates
- Use the `confluence search` command via `jet-company-standards`

**Step 3 — Update and note sourcing**

- Update the relevant sections with new data
- Note whether tiering/ranking is sourced or inferred (see note below)
- Update the "Last updated" date at the top of this file

> **Sourcing note**: The priority tiering (Tier 1/2/3) in the Current Strategic
> Priorities section is **editorially inferred** from emphasis and frequency
> across source documents, not from a single authoritative ranking. Only
> Platform Consolidation (Sonic) was explicitly called "a key strategic
> objective" in its Confluence page. If a formal priority ranking document
> exists in Jira or Confluence, use it to replace the inferred tiering.

To update, submit a PR to this file with the changes and the date.
