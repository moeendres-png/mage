# WS33 G3 non-AF TriggeredSources cost-trace successor — FAILURE

Status: `FAILURE`

This checkpoint terminally adjudicates the already-bound successor before any further runtime-affecting repair.

## Exact immutable run boundary

- branch: `work/ws33-g3-final-closure-20260902`
- source HEAD: `505c242b3c193f31e59fda7a0e34a678ebc06067`
- source TREE: `59e7923685899af413bf8a25563da0814f176dec`
- workflow: `.github/workflows/ws33-g3-svar-event-runtime.yml`
- RUN: `33919282114`
- JOB: `101173616625`
- terminal conclusion: `failure`
- artifact ID: `9954643672`
- artifact name: `ws33-g3-svar-event-runtime-33919282114`
- GitHub digest: `sha256:13322c3ddae4670049e13192303c945e76940cbef4b20c2cd1b417e0468e0d1f`
- independently downloaded ZIP SHA256: `13322c3ddae4670049e13192303c945e76940cbef4b20c2cd1b417e0468e0d1f` — exact match
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- effective-manifest file SHA256: `cd48f4279d682ab944e2534bf937d87e5311e83989e97179ae73c5c7d1bb6224`
- topology consumer-model SHA256: `82638e6b3e4408cc5bddedc49372b6357d3c2bdce6fba7bfab7ed119678f9a48`

## Workflow adjudication

- Steps 1–14: `PASS`
- Step 15 `Adjudicate record behavior and minimum Decision/RNG obligations`: `FAIL`
- Step 16 tape-driven replay: correctly `SKIPPED` by the fail-closed pre-replay gate
- Step 17 source-chain materialization: `SKIPPED`
- Step 18 immutable evidence upload: `PASS`

Record evidence remains:

- effective non-AF paths: `32/32 PASS`
- production parent entrypoints: `33/33 PASS`
- Decision-required paths: `22/22`
- RNG-required paths: `9/10`
- coverage promotion: `FALSE`

The sole missing RNG-required effective path is:

`forge-behavior-v2:24a5352cfaa6ae913df6549ceed0c447d526e89d`

Lineage:

`Descendants' Fury -> DamageDoneOnce -> TrigDigUntil -> DigUntil`

## First material failure and root boundary

The repaired observation-only cost trace now reaches the pinned production `CostSacrifice` decision boundary without diagnostic-tooling failure. For the target `DigUntil` ability (`abilityId=712`, `sourceTrigger=50010`, `hostId=385`) it records:

```text
WS33_SACRIFICE_COST CANDIDATES ... required=1 mandatory=false sources=388 candidates=388 candidateCount=1
WS33_SACRIFICE_COST SELECTION  ... cancelled=true selectedCount=-1 selected=
WS33_SACRIFICE_COST DECISION   ... decisionNull=true
WS33_SACRIFICE_COST RESULT     ... result=false reason=DECISION_NULL
WS33_TRIGGER_PLAY PAY_COST     false ...
WS33_TRIGGER_PLAY PREREQUISITES_MET false ...
```

Therefore:

1. `Card.TriggeredSources` is resolved to a concrete source (`388`).
2. The validity/sacrifice filter leaves exactly one legal candidate (`388`).
3. The authoritative human-cost selection nevertheless returns cancelled/null.
4. `CostPayment` receives `PaymentDecision == null`; cost payment fails.
5. The `DigUntil` continuation that carries the required RNG path never executes its RNG operation.

The same path has accepted external decision events for `CONFIRM_TRIGGER` and `ENTITY_LIST_SELECTION`, but the latter records result `null`; the request advertises two generic choice tokens while the production sacrifice cost has exactly one legal card candidate. This localizes the remaining blocker to the external Decision/fixture binding for cost-time entity-list selection, not to RNG generation or the DigUntil rules core itself.

Evidence classification:

- immutable run/artifact/digest and table counts: `DIRECTLY_VERIFIED`
- production call-boundary interpretation from the injected observation-only trace: `CODE_DERIVED`
- semantic repair target beyond this boundary: not yet PASS; remains `UNKNOWN` until repaired and rerun

## Next allowed action

Before another run, inspect the generic external Decision binding used for `ENTITY_LIST_SELECTION` during `HumanCostDecision.visit(CostSacrifice)` and repair only the directly confirmed systemic mismatch between authoritative legal card candidates and the external selection result. No card-name/effective-path branch, no random/default/pass/cancel fallback, and no intentional RNG/rules/coverage mutation is allowed.

Exactly one repair commit may then produce exactly one successor run, which must be immediately bound by a PENDING checkpoint before further writes.

`G3_NON_AF_STATUS = UNKNOWN`

`COVERAGE_PROMOTION = FALSE`

`WS33_COMPLETE = FALSE`

`TASK_COMPLETE = NO`
