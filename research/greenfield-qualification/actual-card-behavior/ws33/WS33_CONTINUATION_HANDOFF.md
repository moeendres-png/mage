# WS33 CONTINUATION HANDOFF

## Completion contract

Active branch: `work/ws33-g3-final-closure-20260902`.

`TASK_COMPLETE = NO`

`WS33_COMPLETE = FALSE`

Only the final serial `G3 -> ABC -> D -> E -> F -> final cross-qualification` successor with all 4188 effective paths PASS, zero UNKNOWN/FAIL/UNSUPPORTED, A-H UNKNOWN zero, exact pin/model/lineage, and all replay/hidden/RNG/decision/failure/evidence/hash gates may change these flags.

## Stable predecessor

- effective `4188`; PASS `285`; UNKNOWN `3903`; FAIL `0`; UNSUPPORTED `0`; G UNKNOWN `81`; H UNKNOWN `0`.
- Forge pin `8c7e9afb8e6caee88644b94e25da5852e36f8928`.
- effective-manifest file SHA256 `cd48f4279d682ab944e2534bf937d87e5311e83989e97179ae73c5c7d1bb6224`.
- topology consumer-model SHA256 `82638e6b3e4408cc5bddedc49372b6357d3c2bdce6fba7bfab7ed119678f9a48`.

## Current confirmed terminal checkpoint

`LAST_CONFIRMED_CHECKPOINT = G3_NON_AF_COST_TRACE_RUN_33919282114_FAILURE`

Checkpoint:
`research/greenfield-qualification/actual-card-behavior/ws33/checkpoints/G3_NON_AF_COST_TRACE_RUN_33919282114_FAILURE.md`

Checkpoint commit: `c3e5abad69f8017b4af5d484d1152de904bb026c`.

- source HEAD `505c242b3c193f31e59fda7a0e34a678ebc06067`
- source TREE `59e7923685899af413bf8a25563da0814f176dec`
- RUN `33919282114`
- JOB `101173616625`
- terminal `failure`
- artifact `9954643672`
- artifact name `ws33-g3-svar-event-runtime-33919282114`
- digest `sha256:13322c3ddae4670049e13192303c945e76940cbef4b20c2cd1b417e0468e0d1f`
- independently downloaded ZIP re-hash: exact match
- Steps 1–14 PASS; Step 15 FAIL; replay Step 16 skipped fail-closed; upload Step 18 PASS.

Record evidence from this exact artifact:

- effective non-AF paths `32/32 PASS`
- source parents `33/33 PASS`
- Decision-required `22/22`
- RNG-required `9/10`
- coverage promotion `FALSE`

Missing RNG-required effective path:
`forge-behavior-v2:24a5352cfaa6ae913df6549ceed0c447d526e89d`

Lineage:
`Descendants' Fury -> DamageDoneOnce -> TrigDigUntil -> DigUntil`

### Directly localized remaining runtime blocker

The repaired generic TriggeredSources cost trace reaches production `CostSacrifice` and records for target `DigUntil` ability `712` / source trigger `50010` / host `385`:

```text
CANDIDATES required=1 mandatory=false sources=388 candidates=388 candidateCount=1
SELECTION cancelled=true selectedCount=-1 selected=
DECISION decisionNull=true
RESULT result=false reason=DECISION_NULL
PAY_COST=false
PREREQUISITES_MET=false
```

Thus `Card.TriggeredSources` resolution and sacrifice validity filtering succeed with exactly one legal candidate, but the external cost-time entity-list selection resolves to cancel/null. The same effective path has accepted `CONFIRM_TRIGGER` and `ENTITY_LIST_SELECTION` decision events. Its request advertises two generic choice tokens while the production sacrifice-cost candidate set is the single legal card ID `388`.

This localizes the remaining blocker to the generic external Decision binding at cost-time `ENTITY_LIST_SELECTION`, before the required `DigUntil` RNG operation. RNG generation itself is not implicated by this artifact.

Evidence classification: run/artifact/digest/table counts `DIRECTLY_VERIFIED`; trace boundary interpretation `CODE_DERIVED`; repaired semantic result remains `UNKNOWN` until rerun.

## Confirmed generic Decision root cause

`ROOT_CAUSE_CHECKPOINT = research/greenfield-qualification/actual-card-behavior/ws33/checkpoints/G3_NON_AF_ENTITY_LIST_SELECTION_ROOT_CAUSE_20260905.md`

Checkpoint persistence commit: `1d7c0ae79ea26c8e6773fdc491fe36284860c449`.

The exact WS01 synchronized-input bridge used by this workflow patches `InputSelectEntitiesFromList.driveExternal()` to build UI action strings in this order: `DONE` when the Forge input already satisfies minimum selection, `CANCEL` when `allowCancel`, then `ENTITY:<ExternalDecisionRequest.optionIdFor(entity)>` for each authoritative `validChoices` entity. It sends those action strings through `PlayerControllerHuman.chooseExternalUiOptions(..., "ENTITY_LIST_SELECTION", value -> value)`.

For the failing sacrifice state, minimum is not yet satisfied, `allowCancel=true`, and Forge has exactly one legal Card `388`. Therefore the bridge produces exactly two actions: `CANCEL` and the authoritative Card-388 entity transition. `chooseExternalUiOptions` erases that entity identity at the external ABI surface into generic `choice:0` / `choice:1`. The record tape selected `choice:0`, which decodes back to `CANCEL`; `onCancel()` clears the legacy input, `HumanCostDecision` returns `null`, and cost payment stops before RNG.

The bridge additionally encodes cancellation as an ordinary discrete option while its external request sets `cancelAllowed=false`; this confirms the adapter shape is inconsistent with the project Decision ABI. This is not a Forge sacrifice-legality defect and not an RNG defect.

Evidence classification: pinned Forge + exact WS01 bridge + exact run response mapping `CODE_DERIVED`; run request/tape/cost trace `DIRECTLY_VERIFIED`.

Required repair: preserve Forge's `validChoices`, min/max and cancellation legality, expose authoritative entity option IDs directly, use the Decision cancellation channel rather than a fake `choice:N`, map responses only to current authoritative entities, and fail closed on stale/illegal responses. No card-name/path-ID branch, singleton autopick, first/default/random/pass/cancel fallback, rules mutation, RNG mutation or coverage mutation.

No official Magic rules adjudication is required for this adapter repair because it preserves the Rules Core's already-computed legal choices and current cancellation/min/max semantics.

## Active PENDING successor

`ACTIVE_PENDING_CHECKPOINT = NONE`

There is currently no non-terminal successor. The concrete source defect is confirmed, so one runtime-affecting repair commit is now permitted after re-verifying live HEAD/TREE. That source commit must produce exactly one intended qualification run; immediately after run creation its RUN/JOB/SOURCE_HEAD/SOURCE_TREE/workflow/cardinality must be persisted and writes frozen until terminal.

## Retry-protocol incident retained for provenance

Diagnostic source commit `2bb3a56a3edcefdd18d0a26bba5755e393ee28e7` / tree `2046196b514ad0bb4e64297fc8de024b0b216170` unexpectedly produced two push-triggered workflow runs with the same source HEAD. This is a recorded retry-protocol incident; no third run may be created from that source commit.

- Run `33907775080`; job `101136703588`; artifact `9950185061`; digest `sha256:defe92ec72912fc455496d037f9cb04ceb01c56356b6423fd469947ce2973d73`; failed Step 12 with ambiguous diagnostic anchor.
- Run `33907795947`; job `101136772850`; artifact `9950194328`; digest `sha256:92fc6c1f951ceff8b3e962db3dcadd9d04e03cc95bd47c3cc72f0f6ab2a85544`; same Step-12 diagnostic-tooling failure.
- Both immutable ZIPs were independently re-hashed and matched GitHub digests.
- First failure in both: `WS33_G_COST_TRACE=FAIL TriggeredSources sacrifice candidates: expected exactly one anchor, got 2`.

These two runs are diagnostic-tooling failures and do not supersede runtime evidence from `33919282114`.

## G3 immutable evidence — do not rerun without invalidation

### Topology
- run `33681121017`; job `100417671589`; artifact `9866293827`; digest `sha256:6a41f66937b4bf1bcf782045d869ece183c0be49b345eac654dc3588cb98b96b`; PASS.
- partition `G81 = Direct28 + SVar53`; SVar = `AF21 + non-AF32`; non-AF production parents `33`; unresolved `0`.

### Direct-G 28
- behavior run `33516084949`; artifact `9803814288`; digest `sha256:493f3549b6483d4fea9644f3a0216deb108a9ac581b651ff3e083499bcb14b5a`; 28/28 Record/Replay PASS.
- Principal Observation run `33552816460`; artifact `9818304005`; hidden/observation gates PASS.

### AF21
- Runtime run `33773548765` PASS.
- ABI/Decision/RNG/Replay run `33773805031` PASS.
- Principal Observation run `33774853355`; artifact `9901438964`; digest `sha256:2e60f7c79ad642f3f3942db4b3e84a9392cde5662126c0eb84153a3f0469cb5d`; PASS.

## Current G3 frontier

- total G3 `81`
- immutable Direct-G `28`
- immutable AF `21`
- remaining non-AF effective paths `32`
- remaining production parents `33`
- latest valid record behavior `32/32 paths`, `33/33 parents`
- Decision obligation `22/22`
- RNG obligation `9/10`
- replay blocked behind fail-closed pre-replay gate
- `G3_NON_AF_STATUS = UNKNOWN`
- `COVERAGE_PROMOTION = FALSE`

## Exact resume action

1. Re-verify the live branch after root-cause persistence/handoff commits.
2. Apply exactly one systemic runtime-affecting repair to the synchronized `InputSelectEntitiesFromList` external binding so entity identities/cancel semantics are authoritative at the external ABI surface.
3. Verify exactly one successor workflow run for that source commit.
4. Immediately bind RUN/JOB/SOURCE_HEAD/SOURCE_TREE and exact-source run cardinality in a PENDING checkpoint before further runtime-affecting writes.
5. On terminal result, bind artifact ID/name/GitHub digest, independently re-hash ZIP, and persist terminal PASS/FAIL + handoff before any next repair.
6. Continue until strict Runtime Record + Decision22 + RNG10 + tape-driven Replay PASS for all non-AF 32/33.
7. Freeze Runtime; separately certify immutable ABI/Decision/RNG/Replay consuming the exact runtime artifact; then non-AF Principal Observation Hidden31 record/replay equivalence/no leaks.
8. Only after Direct28 + AF21 + non-AF32 satisfy all contracts promote/freeze G3 and recompute the live 4188 frontier.
9. Then execute serial `ABC -> D -> E -> F -> final cross-qualification`; do not use historical expected counts without fresh compatibility adjudication.

`G3_NON_AF_STATUS = UNKNOWN`

`COVERAGE_PROMOTION = FALSE`

`WS33_COMPLETE = FALSE`

`TASK_COMPLETE = NO`
