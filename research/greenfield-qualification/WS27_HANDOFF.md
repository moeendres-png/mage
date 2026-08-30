# WS27 — ACTION / COST / MANA / TARGET / DECISION CLOSURE

## Canonical boundary

- Repository: `moeendres-png/mage`
- Branch: `work/ws27-v2-action-cost-decision-20260830`
- WS26 base HEAD: `206a39cbaa3eeb98b10c2ddc36d51fe5b1b2f5ef`
- WS26 base TREE: `837f445f78bb26462653c58baf1532e294151b10`
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- Owner family: `ACTION_COST_DECISION`
- Assigned V2 paths: `2697`

## Qualification policy

WS27 consumes the committed WS26 V2 model and immutable WS26 artifact as authoritative. No WS15 primitive status, global Q1 result, parser/source presence, or card loadability is promoted to actual-card behavior PASS.

A V2 path is PASS only when an actual-card execution through exact pinned Forge retains semantic state evidence and all decision/RNG/hidden-information/replay evidence required by the WS26 path descriptor. Equivalent source occurrences may share a witness only where the exact WS26 V2 path ID already encodes that equivalence.

The first positive control is the exact V2 path:

`forge-behavior-v2:ede58d662fddba65852ba12b8bb699c33eb8e708`

bound by WS26 to `forge.game.ability.effects.LifeGainEffect` with `LifeAmount=NUM`. The actual card is **Swiftwater Cliffs**, Oracle identity `2f4ad084-2062-44c0-9975-15f100204531`. The qualification fixture uses normal Forge zone movement, replacement processing, trigger collection, regular stack transfer, and resolution; it does not construct or directly resolve an effect and this exact path requires no discretionary decision.

## Required machine outputs

The workflow materializes into the immutable WS27 artifact:

- `WS27_WITNESSES.jsonl`
- `WS27_PATH_COVERAGE.json`
- `WS27_DECISION_INVENTORY.json`
- `WS27_RULES_ADJUDICATION.json`
- `WS27_GATE.json`
- `WS27_HASHES.sha256`

## Hard-gate semantics

A successful GitHub Actions run means only that WS27 evidence was generated and adjudicated reproducibly. It does **not** imply `WS27_FAMILY_GATE=PASS`.

`WS27_FAMILY_GATE=PASS` and `WORKSTREAM_COMPLETE=true` are permitted only when all 2697 production-required paths are accounted, UNKNOWN/UNSUPPORTED/FAIL are zero, all PASS paths have state evidence, all decision paths use authoritative options, no test-side legality or silent fallback exists, the exact Forge pin is proven, all trace hashes are present, and no PASS is stdout-only.

Until that condition is achieved the gate must remain `FAIL_CLOSED` and `WORKSTREAM_COMPLETE=false`, with an exact unresolved blocker.

## Workflow evidence

Pending first canonical WS27 workflow execution. This section will be updated only from directly verified GitHub run/job/artifact metadata.
