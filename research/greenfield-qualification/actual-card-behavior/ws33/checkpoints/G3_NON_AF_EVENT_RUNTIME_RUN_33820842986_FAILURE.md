# G3 NON-AF EVENT RUNTIME — RUN 33820842986 FAILURE

Classification: `DIRECTLY_VERIFIED`

## Immutable run identity

- branch: `work/ws33-g3-final-closure-20260902`
- source HEAD: `71a64f9cd483daf5fbbd1ada5bbde157a73e142e`
- source TREE: `300edfc71b11041069885c03978ee14590999b52`
- workflow: `WS33 G3 SVar non-AF event runtime`
- run: `33820842986`
- job: `100862957388`
- artifact: `9918266289`
- artifact digest: `sha256:693c5b2767e3758668dc38183aa21f543ca0fe08faf3d1e2d8d3c3c98154dfa6`
- downloaded ZIP SHA256 independently re-hashed: exact match

## Workflow adjudication

- Steps 1–13: PASS
- Step 14 `Execute 33-parent record campaign`: PASS
- Step 15 `Adjudicate record behavior and minimum Decision/RNG obligations`: FAIL
- Step 16 replay: SKIPPED
- Step 17 source-chain/hash materialization: SKIPPED
- Step 18 immutable evidence upload: PASS
- coverage promotion: `FALSE`

## First material failure

First source-proven production parent remains:

- path: `forge-behavior-v2:172ab06795f99590ca9d96f85995f6cf9e083ee8`
- parent key: `forge-behavior-v2:172ab06795f99590ca9d96f85995f6cf9e083ee8#1`
- card: `Ingenious Smith`
- mode: `ChangesZone`
- parent: `TrigDig`
- target SVar API: `Dig`
- admission / binding / execution: `1 / 1 / 0`
- resolution callbacks: `0`
- correlated `stack-lifecycle.tsv` events for this parent: `0`

Thus the target root does not reach `MagicStack.add`; target rejection, frozen queueing, stack push and `hasFizzled` are downstream and cannot explain this first failure.

## Trigger-play production telemetry

The source HEAD includes observation-only `PlaySpellAbility` stage telemetry. For the first parent, `record/runtime.log` records:

1. `WS33_TRIGGER_PLAY PLAY_SPELL_ENTRY`
2. `WS33_TRIGGER_PLAY OPTIONAL_COST_SELECTION_NULL`

No `ANNOUNCE_TYPE`, `ANNOUNCE_X`, `CHECK_RESTRICTIONS`, `SETUP_TARGETS`, `CAST_TIMING`, `LEGAL_AFTER_STACK`, `PAY_COST`, `ADD_AND_UNFREEZE`, or `MagicStack.ADD_ENTER` occurs for this parent.

Pinned Forge therefore returns `false` from `PlaySpellAbility.playSpellAbility(...)` because `chooseOptionalAdditionalCosts(p, sa)` returns `null`, before `playAbility(...)` begins.

The same `OPTIONAL_COST_SELECTION_NULL` boundary is present for many other 1/1/0 source-proven parents. A passing control parent proceeds through `OPTIONAL_COST_SELECTION_OK`, all pre-cost stages, payment, `ADD_AND_UNFREEZE`, and normal stack lifecycle. This establishes a common pre-MagicStack boundary rather than a card-specific failure.

## Root-cause boundary

Current first systemically relevant boundary:

`PlayerControllerHuman.orderAndPlaySimultaneousSa`
-> `PlaySpellAbility.playSpellAbility`
-> `chooseOptionalAdditionalCosts`
-> `controller.getAbilityToPlay(original.getHostCard(), abilities)`
-> returns `null`

No repair is authorized from this checkpoint alone. Before changing behavior, inspect:

1. the actual cardinality/content produced by `GameActionUtil.getAdditionalCostSpell(original)` for failing and passing triggers;
2. the connected/external `PlayerControllerHuman.getAbilityToPlay` decision adapter;
3. whether singleton authoritative variants are non-discretionary and should bypass an external pilot decision, versus whether multiple genuine legal variants require an explicit authoritative-option decision.

Do not repair later `SETUP_TARGETS=false` cases until this earlier common boundary is resolved.

## Status

- `G3_NON_AF_STATUS = UNKNOWN`
- `COVERAGE_PROMOTION = FALSE`
- `WS33_COMPLETE = FALSE`
- `TASK_COMPLETE = NO`
