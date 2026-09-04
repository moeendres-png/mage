# WS33 G3 non-AF TriggeredSources cost-trace successor — PENDING

Status: `PENDING`

This checkpoint is intentionally written before terminal adjudication so the active successor is resumable if execution is interrupted.

## Exact active run boundary

- branch: `work/ws33-g3-final-closure-20260902`
- source repair HEAD: `505c242b3c193f31e59fda7a0e34a678ebc06067`
- source TREE: `59e7923685899af413bf8a25563da0814f176dec`
- commit: `ws33 g3: repair generic TriggeredSources cost trace anchors`
- workflow: `.github/workflows/ws33-g3-svar-event-runtime.yml`
- RUN: `33919282114`
- JOB: `101173616625`
- trigger event: `push`
- observed run cardinality for exact source HEAD at checkpoint time: `1`
- observed job status at checkpoint time: `queued`
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- effective-manifest file SHA256: `cd48f4279d682ab944e2534bf937d87e5311e83989e97179ae73c5c7d1bb6224`
- topology consumer-model SHA256: `82638e6b3e4408cc5bddedc49372b6357d3c2bdce6fba7bfab7ed119678f9a48`

## Repair scope

The source commit repairs only the generic observation-only TriggeredSources sacrifice-cost diagnostic:

- anchors candidate instrumentation structurally inside `HumanCostDecision.visit(CostSacrifice)` instead of the previously ambiguous short `int c` block;
- reads `AbilityKey.Sources` from `ability.getRootAbility()`, matching pinned Forge `AbilityUtils` semantics;
- records validity-filtered sacrifice candidate IDs and authoritative HumanCostDecision selection IDs;
- records the CostPayment boundary distinguishing `PaymentDecision == null` from `payAsDecided == false`;
- contains no card-name or effective-path-ID branch;
- does not intentionally modify Forge rules semantics, fixture semantics, targets, costs, decisions, RNG, coverage, or replay behavior.

## Predecessor evidence remains authoritative while PENDING

Until this run is terminal and its artifact is bound, the latest valid runtime evidence remains run `33863979003`:

- record effective paths `32/32 PASS`
- parent entrypoints `33/33 PASS`
- Decision obligation `22/22`
- RNG obligation `9/10`
- replay blocked fail-closed
- missing RNG path `forge-behavior-v2:24a5352cfaa6ae913df6549ceed0c447d526e89d`
- lineage `Descendants' Fury -> DamageDoneOnce -> TrigDigUntil -> DigUntil`
- prior target trace reaches `PAY_COST=false`, `PREREQUISITES_MET=false`

## Execution discipline

While RUN `33919282114` is non-terminal:

- READ-ONLY inspection only;
- no runtime-affecting write;
- no rerun/manual dispatch;
- if a second run for source HEAD `505c242...` appears, record it as a protocol incident and do not create a third;
- once terminal, bind RUN/JOB/SOURCE_HEAD/SOURCE_TREE/ARTIFACT/DIGEST, independently re-hash the ZIP, inspect `WS33_SACRIFICE_COST` evidence, and persist PASS/FAIL before any further repair.

`G3_NON_AF_STATUS = UNKNOWN`

`COVERAGE_PROMOTION = FALSE`

`WS33_COMPLETE = FALSE`

`TASK_COMPLETE = NO`
