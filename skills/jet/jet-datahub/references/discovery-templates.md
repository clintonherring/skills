# Discovery Templates

Verbatim output templates used during the Prioritized Discovery Strategy. The agent MUST output these blocks at the specified points during discovery.

## Pre-Flight Block

Output this **before** your first DataHub command:

```
PRE-FLIGHT CHECK
- Request type: [DISCOVERY | SPECIFIC_OPERATION | TARGETED_METADATA]
- User intent: <one-sentence summary>
- Classification reason: <why this classification>
- Strategy: [PRIORITIZED_DISCOVERY_LAYERS_1-6 | DIRECT_WORKFLOW | TARGETED_LOOKUP]
```

## TodoWrite Items

Create all of these at once **before** your first search call, and mark each as you go:

```
TodoWrite items:
1. "Layer 1: Semantic Layer (Looker) — search datasets, dashboards, charts; check governance"  [pending]
2. "Layer 2: Business Glossary — always check for context enrichment"                          [pending]
3. "Layer 3: Data Products — search for curated bundles"                                       [pending]
4. "Layer 4: Tagged Tables — filter by domain/team tags"                                       [pending]
5. "Layer 5: Tier Labels — gold > silver > bronze"                                             [pending]
6. "Layer 6: Full Catalog — fallback broad search"                                             [pending]
7. "Rank results and present discovery output"                                                  [pending]
```

## Layer Gate Block

Output this **after completing each layer**, before proceeding to the next:

```
LAYER <N> GATE
- Layer: <layer name>
- Tool calls made: <count>
- Results found: <count> relevant / <count> total
- Decision: [STOP — sufficient results | PROCEED — insufficient results | ALWAYS CHECK — Layer 2]
- Reason: <one-sentence justification for stopping or proceeding>
```

**Gate rules:**
- If a layer returns relevant results AND it is not Layer 2, you MAY stop. Output `STOP` in the decision.
- Layer 2 (Business Glossary) MUST always be checked regardless of Layer 1 results. Output `ALWAYS CHECK` in the decision when entering Layer 2.
- If you output `PROCEED`, you MUST execute the next layer — do not skip it.
- If you reach Layer 6, you MUST output the gate block and note that results are uncurated.
