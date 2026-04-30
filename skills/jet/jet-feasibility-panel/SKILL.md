---
name: jet-feasibility-panel
description: >-
  Assembles a structured panel of 8 expert agents to debate and evaluate the
  feasibility of a proposed project or use case at JET. The panel includes
  advocates, skeptics, and neutral domain experts who conduct a multi-round
  debate covering technical architecture, business value, strategic alignment,
  security, and delivery feasibility. Produces a scored verdict (Go / Conditional
  Go / No-Go) with a full debate transcript and structured feasibility report.
  Use when evaluating whether JET should pursue a new project, feature, platform
  initiative, or architectural change. Triggers on phrases like "is this
  feasible", "should we build", "evaluate this use case", "feasibility study",
  "feasibility analysis", "should JET invest in", "pros and cons of building",
  or "debate this proposal".
metadata:
  owner: ai-platform
---

# JET Feasibility Panel

A structured adversarial debate panel that evaluates the feasibility of a
proposed project or use case at Just Eat Takeaway. Eight expert agents with
distinct perspectives -- advocates, skeptics, and neutral assessors -- conduct a
multi-round debate and produce a scored feasibility verdict.

## Model Recommendations

- **Recommended**: Run this skill with **Claude Opus** for best results. The
  debate quality, cross-examination depth, and synthesis accuracy scale directly
  with model reasoning capability.
- **Acceptable**: Claude Sonnet in `fast` mode (2 rounds) only.
- **Minimum**: Any model capable of structured role-playing and multi-step
  reasoning. Weaker models will produce shallow debate and unreliable scoring.

## When to Use

- Evaluating whether JET should pursue a new project, product, or platform initiative
- Assessing technical feasibility of an architectural change or migration
- Weighing build-vs-buy decisions
- Stress-testing a proposal before presenting it to leadership
- Getting a structured, multi-perspective analysis before committing resources

## When NOT to Use

- For simple technical questions (use `jet-company-standards` or ask directly)
- For pure architecture design (use an architect, not a debate panel)
- For operational issues or incidents (use `jet-datadog`, `jet-pagerduty`)
- When the decision has already been made and you just need implementation help

## Prerequisites

### Dependency Skills

| Skill | Purpose | When Loaded |
|---|---|---|
| `jet-company-standards` | PlatformMetadata, Backstage, team/service lookups | Phase 1 |

### Required Context

The skill uses a baked-in strategic context reference file that should be
periodically updated. See [references/jet-strategic-context.md](references/jet-strategic-context.md).

## The Panel

Eight expert agents with defined stances and domain focus areas:

| # | Role | Stance | Focus Area |
|---|---|---|---|
| 1 | **Product Champion** | FOR | Business value, market opportunity, user impact, ROI |
| 2 | **Solution Architect** | FOR | Technical approach, architecture fit, implementation path |
| 3 | **Devil's Advocate PM** | AGAINST | Business risks, opportunity cost, market assumptions |
| 4 | **Skeptical Architect** | AGAINST | Technical debt, complexity, integration risks, scale concerns |
| 5 | **Principal Architect** | NEUTRAL | Current JET landscape fit, platform alignment, reuse opportunities |
| 6 | **VP of Strategy** | NEUTRAL | Strategic alignment, priority ranking, resource allocation, timing |
| 7 | **Security & Compliance Officer** | NEUTRAL-CAUTIOUS | Data privacy, regulatory, security posture, compliance burden |
| 8 | **Engineering Manager** | NEUTRAL | Delivery feasibility, team capacity, timeline realism, operational cost |

Detailed persona prompts for each agent are in
[references/agent-personas.md](references/agent-personas.md).

## IMPORTANT: User Consent Required Before Starting

**This skill is resource-intensive. NEVER start automatically.** Even if you
detect that the user's request would benefit from a feasibility panel, you MUST
first ask for explicit permission. Present the following briefing:

> **Feasibility Panel Assessment**
>
> I can assemble a panel of 8 expert agents to debate this proposal. Before I
> do, you should know what this involves:
>
> - **8 AI agents** with distinct roles (product, architecture, security,
>   strategy, delivery, and adversarial perspectives) will conduct a structured
>   debate
> - **Multiple rounds** of debate: opening statements, cross-examination,
>   rebuttals, and final scoring
> - **Duration**: This is a heavy, long-running process. Expect:
>   - `fast` mode (2 rounds): ~5-10 minutes, lighter analysis
>   - `standard` mode (3 rounds): ~10-20 minutes, balanced depth
>   - `deep` mode (4 rounds): ~20-30+ minutes, thorough adversarial analysis
> - **Output**: A scored Go / Conditional Go / No-Go verdict with a full debate
>   transcript saved to a markdown file
> - **Cost**: Each round launches multiple subagent calls. This will consume
>   significant token budget.
>
> Would you like to proceed? If so, which depth: `fast`, `standard`, or `deep`?

**Do NOT proceed until the user explicitly confirms.** If the user declines,
suggest lighter alternatives (e.g., a quick pros/cons list, a single-agent
assessment, or asking specific questions directly).

## Workflow

```
Phase 0: Intake & Context Gathering .......... (Interactive)
Phase 1: Context Enrichment .................. (Automatic)
Phase 2: Panel Debate ........................ (Automatic, multi-round)
Phase 3: Synthesis & Scoring ................. (Automatic)
Phase 4: Report Generation ................... (Automatic)
```

### Phase 0: Intake & Context Gathering (Interactive)

**Goal**: Understand the use case well enough to brief the panel.
**Prerequisite**: User has explicitly consented to run the panel (see above).

1. Accept the user's use case description. This can be a single prompt or a
   detailed brief.
2. If the input is sparse (fewer than 3 substantive sentences), ask the
   following structured questions before proceeding:
   - **Problem**: What problem does this solve? Who experiences this pain today?
   - **Users**: Who are the target users or consumers of this solution?
   - **Scope**: What is the rough scope? (MVP vs full platform, single market vs global)
   - **Timeline**: Any timeline expectations or deadlines?
   - **Constraints**: Known constraints (budget, team size, tech restrictions)?
   - **Depth**: How deep should the debate go? (`fast` = 2 rounds, `standard`
     = 3 rounds, `deep` = 4 rounds). Default: `standard`.
3. Ask the user if they want to state or override current JET strategic
   priorities. If not, use the defaults from
   [references/jet-strategic-context.md](references/jet-strategic-context.md).
4. Compile the raw use case brief from user input.

### Phase 1: Context Enrichment (Automatic)

**Goal**: Ground the debate in real JET context.

1. Load the `jet-company-standards` skill.
2. Use PlatformMetadata and/or Backstage to look up:
   - Existing services or components relevant to the proposed use case
   - Team ownership of related domains
   - Any existing architecture that overlaps with the proposal
3. Read [references/jet-strategic-context.md](references/jet-strategic-context.md)
   for the current strategic priorities and architecture landscape.
4. Merge any user-provided priority overrides with the reference file context.
5. Compile the **Context Brief** -- a single document that every panel agent
   will receive. It should contain:
   - The use case description (from Phase 0)
   - Relevant existing services and architecture (from lookups)
   - Current JET strategic priorities (from reference + overrides)
   - Known constraints and timeline

### Phase 2: Panel Debate (Automatic, Multi-Round)

**Goal**: Conduct a structured, multi-round debate among the 8 panel agents.

Read the full debate protocol at
[references/debate-protocol.md](references/debate-protocol.md).

Each agent is launched as a **Task tool subagent** with:
- Their persona prompt from [references/agent-personas.md](references/agent-personas.md)
- The Context Brief from Phase 1
- The round instructions and any prior round summaries

#### Round Structure

| Round | Name | Execution | Included In |
|---|---|---|---|
| 1 | Opening Statements | **Parallel** (all 8) | fast, standard, deep |
| 2 | Cross-Examination | **Sequential** (targeted) | fast, standard, deep |
| 3 | Rebuttals | **Sequential** (targeted) | standard, deep |
| 4 | Deep Dive | **Sequential** (targeted) | deep only |
| Final | Closing Positions & Scores | **Parallel** (all 8) | fast, standard, deep |

#### Witness Mechanism

After Round 1 (Opening Statements), the orchestrator reviews all 8 statements
for questions tagged for the user. If any agent flagged a question for the
user (e.g., "I need to know if the user has considered X"), the orchestrator:

1. Batches all witness questions into a single prompt
2. Pauses the debate and presents them to the user
3. Distributes the user's answers to all agents in the next round's context

#### Between-Round Processing

After each round, the orchestrator:

1. Compiles a summary of all statements from that round
2. Identifies key points of contention
3. For sequential rounds (Cross-Examination, Rebuttals), identifies which
   agents should respond to which points
4. Passes the compiled summary + targeting instructions to each agent for
   the next round

### Phase 3: Synthesis & Scoring (Automatic)

**Goal**: Synthesize the debate into a scored verdict.

1. Collect all Final Round positions and domain scores (1-10) from each agent.
2. Compute domain scores:

   | Domain | Assessors | Calculation |
   |---|---|---|
   | Business Feasibility | Product Champion + Devil's Advocate PM | Average of their scores |
   | Technical Feasibility | Solution Architect + Skeptical Architect | Average of their scores |
   | Strategic Alignment | VP of Strategy + Principal Architect | Average of their scores |
   | Delivery Confidence | Engineering Manager | Direct score |
   | Risk Posture | Security & Compliance Officer | Direct score |

3. Compute overall score as equal-weighted average of the 5 domain scores.
4. Determine verdict:
   - **GO**: Overall score > 7.0
   - **CONDITIONAL GO**: Overall score 5.0 - 7.0
   - **NO-GO**: Overall score < 5.0
   - **NEEDS MORE INFO**: If 2 or more agents explicitly flagged insufficient
     data to make a confident assessment
5. Synthesize key arguments for and against, key risks, and recommended next
   steps.

### Phase 4: Report Generation (Automatic)

**Goal**: Produce the final deliverable.

1. Generate the feasibility report using the template at
   [references/report-template.md](references/report-template.md).
2. The report includes:
   - Executive summary with verdict and scores dashboard
   - Key arguments for and against
   - Risks and mitigations
   - Conditions (if Conditional Go)
   - Recommended next steps
   - Full panel debate transcript
3. Save the report to `feasibility-reports/<use-case-slug>-<YYYY-MM-DD>.md`
   in the current working directory. Create the `feasibility-reports/`
   directory if it does not exist.
4. Present the Executive Summary and Verdict to the user in the conversation,
   and point them to the saved file for the full report.

## Orchestrator Responsibilities

You (the main agent) act as the **moderator and orchestrator**. You do NOT
participate in the debate. Your responsibilities are:

- Ensuring each agent stays in character and addresses their domain
- Compiling between-round summaries accurately and without bias
- Identifying and routing cross-examination targets fairly
- Batching witness questions for the user
- Computing scores mathematically (no subjective adjustment)
- Synthesizing the final report from agent outputs, not from your own opinions
- Flagging if an agent's reasoning appears contradictory or unsupported

## Error Handling

- If a subagent call fails, retry once. If it fails again, note the agent as
  "unable to participate" and proceed with remaining agents. Adjust scoring
  to exclude that agent's domain contribution.
- If the `jet-company-standards` skill is unavailable, proceed with
  user-provided context only and note in the report that context enrichment
  was limited.
- If fewer than 5 agents successfully participate, abort the panel and inform
  the user that insufficient perspectives were gathered for a reliable
  assessment.
