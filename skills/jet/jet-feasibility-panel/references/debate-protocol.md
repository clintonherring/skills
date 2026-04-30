# Debate Protocol

This document defines the round structure, execution rules, and scoring
mechanics for the feasibility panel debate.

## Debate Modes

The user selects a debate depth at intake. This controls how many rounds
are executed:

| Mode | Rounds | Approximate Duration | Best For |
|---|---|---|---|
| `fast` | 2 + Final | Quick gut-check, low-stakes decisions | Small features, incremental changes |
| `standard` | 3 + Final | Balanced depth and speed | Most proposals, new projects |
| `deep` | 4 + Final | Thorough adversarial analysis | Major investments, platform bets, strategic shifts |

Default: `standard`

## Round Definitions

### Round 1: Opening Statements

**Execution**: Parallel (all 8 agents simultaneously)
**Included in**: fast, standard, deep

Each agent receives:
- The Context Brief (use case + enriched JET context)
- Their persona prompt
- The common instructions

Each agent produces:
- Their initial position on the proposal's feasibility
- Key points supporting their position
- At least 1 risk or concern (even FOR agents)
- Optional: witness questions tagged with `[WITNESS QUESTION]`

**Orchestrator actions after Round 1**:
1. Compile all 8 opening statements into a Round 1 Summary
2. Check for `[WITNESS QUESTION]` tags across all statements
3. If witness questions exist:
   - Batch all questions into a single, organized prompt
   - Present to the user and wait for responses
   - Include user responses in the context for subsequent rounds
4. Identify key points of contention (where FOR and AGAINST agents disagree)
5. Assign cross-examination targets for Round 2

### Round 2: Cross-Examination

**Execution**: Sequential (agents respond to specific points)
**Included in**: fast, standard, deep

The orchestrator selects 4-6 agents for cross-examination based on where
the strongest disagreements emerged in Round 1. Not all agents need to
participate in every round.

**Targeting rules**:
- Each selected agent receives 1-2 specific points from opposing agents
  to address
- FOR agents are asked to respond to AGAINST concerns
- AGAINST agents are asked to challenge FOR claims
- NEUTRAL agents are asked to weigh in on the most contested points

Each agent receives:
- The Context Brief
- The Round 1 Summary (all 8 statements)
- User's witness answers (if any)
- Their specific cross-examination targets: "Agent X claimed Y. Respond
  to this from your perspective."

Each agent produces:
- Direct responses to their assigned cross-examination targets
- New points that emerged from reading other agents' positions
- Updated risk assessment (if applicable)

**Orchestrator actions after Round 2**:
1. Compile cross-examination responses into a Round 2 Summary
2. Identify any remaining unresolved disagreements
3. Check for new `[WITNESS QUESTION]` tags (handle same as Round 1)

### Round 3: Rebuttals

**Execution**: Sequential (targeted agents)
**Included in**: standard, deep

The orchestrator selects 3-4 agents who had the strongest disagreements
during cross-examination.

Each agent receives:
- The Context Brief
- Round 1 + Round 2 Summaries
- Specific rebuttal targets: "Agent X countered your point about Y with Z.
  Defend or revise your position."

Each agent produces:
- Defense or revision of their position based on cross-examination
- Any concessions ("I acknowledge that Agent X's point about Y changes
  my assessment of Z")
- Refined risk assessment

**Orchestrator actions after Round 3**:
1. Compile rebuttals into a Round 3 Summary
2. Note any position changes or concessions

### Round 4: Deep Dive (Deep Mode Only)

**Execution**: Sequential (targeted agents, 2-3 selected)
**Included in**: deep only

The orchestrator identifies the 1-2 most critical unresolved questions
and assigns 2-3 agents to do a deep-dive analysis.

Each agent receives:
- All prior round summaries
- A specific deep-dive prompt: "The panel has not resolved the question
  of X. Provide your deepest analysis of this specific issue."

Each agent produces:
- An in-depth analysis of their assigned topic
- Concrete evidence or reasoning not yet surfaced
- A clear position on the contested issue

### Final Round: Closing Positions & Scores

**Execution**: Parallel (all 8 agents simultaneously)
**Included in**: fast, standard, deep

Each agent receives:
- All prior round summaries
- Instruction to provide their final position and domain score

Each agent produces:
- Final position (2-3 paragraphs): Has the debate changed their view?
- Key arguments summary (top 3 points)
- Concessions (if any): "I initially thought X, but Agent Y's point
  about Z has shifted my assessment"
- **Domain Score (1-10)** with calibration rationale
- Final recommendation: Build / Don't Build / Build with conditions /
  Need more information

## Scoring Mechanics

### Domain Score Collection

After the Final Round, collect scores from all 8 agents:

| Agent | Domain Scored |
|---|---|
| Product Champion | Business Feasibility |
| Devil's Advocate PM | Business Feasibility |
| Solution Architect | Technical Feasibility |
| Skeptical Architect | Technical Feasibility |
| VP of Strategy | Strategic Alignment |
| Principal Architect | Strategic Alignment |
| Engineering Manager | Delivery Confidence |
| Security & Compliance Officer | Risk Posture |

### Domain Score Calculation

| Domain | Formula |
|---|---|
| Business Feasibility | (Product Champion score + Devil's Advocate PM score) / 2 |
| Technical Feasibility | (Solution Architect score + Skeptical Architect score) / 2 |
| Strategic Alignment | (VP of Strategy score + Principal Architect score) / 2 |
| Delivery Confidence | Engineering Manager score (direct) |
| Risk Posture | Security & Compliance Officer score (direct) |

### Overall Score

```
Overall = (Business + Technical + Strategic + Delivery + Risk) / 5
```

All domains weighted equally.

### Verdict Thresholds

| Overall Score | Verdict | Meaning |
|---|---|---|
| > 7.0 | **GO** | Strong recommendation to proceed |
| 5.0 - 7.0 | **CONDITIONAL GO** | Proceed with specific conditions that must be met |
| < 5.0 | **NO-GO** | Recommendation against proceeding |
| Any score, but 2+ agents flagged insufficient data | **NEEDS MORE INFO** | Cannot make a confident recommendation |

### Verdict Overrides

- If ANY domain scores below 3.0, add a mandatory condition related to that
  domain regardless of the overall score
- If Business Feasibility < 4.0, the verdict cannot be higher than CONDITIONAL GO
- If Risk Posture < 3.0, the verdict cannot be higher than CONDITIONAL GO
  (compliance is non-negotiable)

## Witness Question Protocol

Witness questions allow agents to request information from the user during
the debate. This ensures the debate is grounded in reality when agents
identify critical unknowns.

### How Agents Tag Witness Questions

In any round, an agent can include a section:

```markdown
### [WITNESS QUESTION]
- What is the expected data volume for this feature? (I need this to
  assess scalability requirements)
- Has the legal team been consulted on GDPR implications? (This affects
  my compliance assessment)
```

### How the Orchestrator Handles Them

1. After each parallel round (Round 1, Final Round), scan all agent
   outputs for `[WITNESS QUESTION]` sections
2. Deduplicate similar questions
3. Group by theme (technical, business, compliance, etc.)
4. Present to the user as a single organized prompt:

```markdown
## Questions from the Panel

The following questions were raised by panel members. Your answers will
be shared with all agents.

### Technical Questions
1. [From Solution Architect] What is the expected data volume?
2. [From Skeptical Architect] Are there existing APIs that handle X?

### Business Questions
3. [From Devil's Advocate PM] Has user research validated the demand?

### Compliance Questions
4. [From Security Officer] Has a DPIA been initiated?
```

5. After receiving user answers, include them in the context for the
   next round under a `## Witness Testimony` heading

### Limits

- Maximum 2 witness question pauses per debate (after Round 1 and
  optionally after Round 2)
- If a question is raised in later rounds, include it in the report's
  "Questions for Further Investigation" section instead of pausing
