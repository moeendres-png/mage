# G3 NON-AF EVENT RUNTIME — RUN 33851809027 FAILURE

Classification: `DIRECTLY_VERIFIED` runtime evidence plus `CODE_DERIVED` boundary attribution.

## Immutable run identity

- source HEAD: `6fbb0150acf5b9d7c865ac90f0b485d97b482d30`
- source TREE: `73cc2fde2b9ff22a474b3f1460b67257a1d9231a`
- workflow: `WS33 G3 SVar non-AF event runtime`
- run: `33851809027`
- job: `100956085252`
- artifact: `9928708015`
- artifact digest: `sha256:65dfc40f374e63bd67150a2bf77285358c38e9d25026102f11a9eef5909077e0`
- downloaded ZIP SHA256 independently re-hashed: exact match

## Workflow adjudication

- Steps 1–14: PASS
- Step 15 `Adjudicate record behavior and minimum Decision/RNG obligations`: FAIL
- Step 16 replay: SKIPPED
- Step 17 source-chain/hash materialization: SKIPPED
- Step 18 immutable evidence upload: PASS
- coverage promotion: `FALSE`

## Confirmed effect of singleton repair

The previously frozen first parent now reaches the target root:

- path: `forge-behavior-v2:172ab06795f99590ca9d96f85995f6cf9e083ee8`
- parent: `#1`
- card: `Ingenious Smith`
- mode: `ChangesZone`
- source SVar: `TrigDig`
- target API: `Dig`
- admission / binding / execution: `1 / 1 / 1`

Therefore the adjudicated `abilities.size()==1` repair successfully removes the prior `OPTIONAL_COST_SELECTION_NULL` blocker and does not merely change measurement.

## New first material failure

The first parent fails only after the Dig root is executing, with:

- exception: `forge.gamemodes.match.input.ExternalDecisionValidationException`
- code: `UNSUPPORTED_DECISION_PATH`
- message: `hidden authoritative Card choices require RemoteClient principal observation`

This message is emitted by the WS33 hidden-card observation bridge in `apply-ws33-input-confirm.py` when `beginWs33ExternalCardObservation(...)` detects hidden Card choices but the underlying `PlayerControllerHuman.gui` is not a `RemoteClientGuiGame`.

The same bridge deliberately refuses to expose hidden Card choices through a non-principal-scoped local GUI path. This is fail-closed behavior, not a legal-action failure and not a reason to relax hidden-information checks.

## Boundary attribution

Runtime source path now reaches:

`TriggerHandler admission`
-> `PlaySpellAbility` singleton variant selection
-> normal pre-cost prerequisites
-> `MagicStack.add / push / non-fizzled resolution`
-> target `Dig` execution
-> authoritative hidden Card choice construction
-> WS33 principal observation bridge
-> `gui instanceof RemoteClientGuiGame` check
-> `UNSUPPORTED_DECISION_PATH`

The current non-AF event runtime harness therefore lacks the RemoteClient principal-observation transport required by the already-established strict hidden-card decision contract.

## Repair constraints

No relaxation is authorized. Specifically forbidden:

- exposing hidden Card identities directly to the external decision provider;
- bypassing `beginWs33ExternalCardObservation`;
- treating the local authoritative backend view as the pilot observation;
- auto-selecting hidden options;
- changing hidden/reveal semantics or the Rules Core.

Next investigation must determine the already-qualified RemoteClient/principal-observation setup used by the stable Direct-G / AF observation workflows and bind the event runtime harness to that same transport semantics, or prove another existing compatible transport path. Reuse qualified infrastructure rather than inventing a parallel observation model.

## Status

`G3_NON_AF_STATUS = UNKNOWN`
`COVERAGE_PROMOTION = FALSE`
`WS33_COMPLETE = FALSE`
`TASK_COMPLETE = NO`
