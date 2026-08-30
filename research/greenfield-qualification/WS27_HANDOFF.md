# WS27 — ACTION / COST / MANA / TARGET / DECISION CLOSURE

## Final adjudication

```text
WS27_FAMILY_GATE = FAIL_CLOSED
WORKSTREAM_COMPLETE = FALSE
WORKSTREAM_CLOSED_FAIL_CLOSED = TRUE
SHARED_CORE_FIX_REQUIRED = FALSE
Q6_ACTUAL_CARD_BEHAVIOR = NOT_ADJUDICATED_BY_WS27
```

WS27 is closed **fail-closed**, not qualified PASS. The hard gate cannot honestly be promoted because production-required V2 paths remain without actual-card runtime evidence.

## Canonical boundary

- Repository: `moeendres-png/mage`
- Branch: `work/ws27-v2-action-cost-decision-20260830`
- WS26 base HEAD: `206a39cbaa3eeb98b10c2ddc36d51fe5b1b2f5ef`
- WS26 base TREE: `837f445f78bb26462653c58baf1532e294151b10`
- Tested WS27 source HEAD: `93440c26e946934ae9257c16bca0760b02f0c554`
- Tested WS27 source TREE: `dfc086170097d0dffbfae1da2f956709570bac9e`
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- Owner family: `ACTION_COST_DECISION`
- Assigned V2 paths: `2697`

The tested source is exactly one commit ahead of WS26 and changes only the WS27 workflow, this handoff, the WS27 materializer, and the qualification-only Swiftwater Cliffs fixture.

## Directly verified workflow evidence

- Run: `33304817385` — `success`
- Job: `99239367842` — `success`
- Immutable artifact: `9730143001`
- Artifact name: `ws27-v2-action-cost-decision`
- Artifact digest: `sha256:e8b8a690161c464599269cbd7caed0680291f35428163c6e43c5fe3f71d592be`
- Artifact tested HEAD: `93440c26e946934ae9257c16bca0760b02f0c554`

The downloaded artifact ZIP independently hashes to the same SHA-256 digest. Every entry listed in the artifact's `WS27_HASHES.sha256` was independently recomputed and matched.

## Machine outputs

The immutable artifact contains under `research/greenfield-qualification/actual-card-behavior/ws27/`:

- `WS27_WITNESSES.jsonl`
- `WS27_PATH_COVERAGE.json`
- `WS27_DECISION_INVENTORY.json`
- `WS27_RULES_ADJUDICATION.json`
- `WS27_GATE.json`
- `WS27_HASHES.sha256`
- `ws27-swiftwater-cliffs.trace.json`

It also retains the Surefire XML, Maven log, tested source HEAD/TREE, exact Forge pin, and WS26 artifact identity/digest under `workflow-evidence/`.

## Path coverage

Direct artifact adjudication:

```text
assigned = 2697
accounted = 2697
PASS = 1
UNKNOWN = 2696
UNSUPPORTED = 0
FAIL = 0
```

The single PASS path is:

`forge-behavior-v2:ede58d662fddba65852ba12b8bb699c33eb8e708`

- parent: `forge-primitive-v1:336f092f6f84a1ba3f916857091b3734`
- implementation target: `forge.game.ability.effects.LifeGainEffect`
- selector: `LifeAmount=NUM`
- actual card: **Swiftwater Cliffs**
- Oracle identity: `2f4ad084-2062-44c0-9975-15f100204531`

The exact pinned-Forge test executed normal zone movement, ETB replacement handling, trigger collection, simultaneous-trigger transfer, regular stack resolution, and retained semantic state. The trace shows:

```text
initial:    Hand, life=20
move:       Battlefield, tapped=true, life=20
final:      Battlefield, tapped=true, life=21
stack:      empty
fallbacks:  0
stdout_only:false
```

Surefire reports `tests=1`, `failures=0`, `errors=0`, `skipped=0`.

## Decision inventory

```text
decision_required_paths = 1812
decision_paths_with_PASS_authoritative_option_evidence = 0
decision_paths_without_PASS_authoritative_option_evidence = 1812
```

This is intentional fail-closed accounting. Global Q1 / strict-decision-boundary qualification and the historical WS15 materialization are supporting architecture evidence only; neither is path-specific actual-card behavior proof for these WS27 V2 paths.

The WS27 decision contract therefore remains:

- Rules Core generates authoritative options;
- pilot may not infer legality;
- typed response required;
- no silent fallback;
- no test-side legality reconstruction.

No unexecuted decision path was promoted to PASS.

## Hard gate

Directly read from `WS27_GATE.json`:

```text
assigned_paths_accounted = true
production_required_UNKNOWN = 2696
production_required_UNSUPPORTED = 0
production_required_FAIL = 0
all_PASS_have_state_evidence = true
all_decision_paths_use_authoritative_options = false
illegal_test_side_legality_logic = 0
silent_fallback_count = 0
card_name_production_hacks = 0
exact_forge_pin = true
trace_hashes_complete = true
stdout_only_PASS_count = 0
```

Because `production_required_UNKNOWN != 0` and `all_decision_paths_use_authoritative_options != true`, the requested PASS gate is not satisfied.

## Exact unresolved blocker

```text
class = ACTUAL_CARD_RUNTIME_COVERAGE_INCOMPLETE
unproved_v2_path_count = 2696
decision_required_unproved_path_count = 1812
```

Those paths have no WS27 actual-card pinned-Forge execution and therefore no admissible state/decision/RNG/observation trace. Source presence, WS26 model equivalence, Q1, historical WS15 status, or a green workflow cannot replace that evidence.

This is not presently classified as a shared-core defect, so `SHARED_CORE_FIX_REQUIRED = FALSE`. If later executions reach a systemic shared-engine defect, it must be escalated with the exact affected paths/files/rules/reproducer rather than patched across another owner's subsystem.

## Rules authority

`WS27_RULES_ADJUDICATION.json` records the current official Magic Comprehensive Rules effective `2026-08-07`, including the WS27-relevant sections for mana, targets, priority, costs, life, casting, activation, and resolution (`106`, `115`, `117`, `118`, `119`, `601`, `602`, `608`). Rules references do not promote unexecuted paths.

## Integration consequence

Do **not** consume WS27 as a family PASS. Integration may consume the one exact PASS witness and the complete fail-closed inventory, but the remaining 2696 V2 paths must stay UNKNOWN until independently exercised or covered by an equivalence explicitly authorized by the WS26 model with complete required evidence.
