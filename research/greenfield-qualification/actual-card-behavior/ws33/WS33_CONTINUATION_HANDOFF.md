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

## Current confirmed checkpoint

`LAST_CONFIRMED_CHECKPOINT = G3_NON_AF_COST_TRACE_RUNS_33907775080_33907795947_FAILURE`

Checkpoint:
`research/greenfield-qualification/actual-card-behavior/ws33/checkpoints/G3_NON_AF_COST_TRACE_RUNS_33907775080_33907795947_FAILURE.md`

Checkpoint commit: `efbc37183278410d8eed51a21910bb220dd2baae`.

Diagnostic source commit `2bb3a56a3edcefdd18d0a26bba5755e393ee28e7` / tree `2046196b514ad0bb4e64297fc8de024b0b216170` unexpectedly produced two push-triggered workflow runs with the same source HEAD. This is a recorded retry-protocol incident; no third run may be created from that source commit.

### Run A

- RUN `33907775080`; JOB `101136703588`; terminal `failure`
- artifact `9950185061`
- artifact name `ws33-g3-svar-event-runtime-33907775080`
- digest `sha256:defe92ec72912fc455496d037f9cb04ceb01c56356b6423fd469947ce2973d73`
- independently downloaded ZIP re-hash: exact match
- Steps 1-11 PASS; Step 12 harness/request-trace preparation FAIL; Java/runtime Steps 13-17 skipped; artifact upload PASS

### Run B

- RUN `33907795947`; JOB `101136772850`; terminal `failure`
- artifact `9950194328`
- artifact name `ws33-g3-svar-event-runtime-33907795947`
- digest `sha256:92fc6c1f951ceff8b3e962db3dcadd9d04e03cc95bd47c3cc72f0f6ab2a85544`
- independently downloaded ZIP re-hash: exact match
- Steps 1-11 PASS; Step 12 harness/request-trace preparation FAIL; Java/runtime Steps 13-17 skipped; artifact upload PASS

Both logs fail first at the exact same strict diagnostic cardinality guard:

```text
WS33_G_COST_TRACE=FAIL TriggeredSources sacrifice candidates: expected exactly one anchor, got 2
```

The cost-trace patch therefore failed closed before Java compilation. These are diagnostic-tooling failures, not new runtime-behavior evidence. No Forge/fixture/root-cause repair is justified from them.

The last valid runtime evidence remains run `33863979003` / job `100994503842`:

- source HEAD `35a2a267fa70b87a4d21d5cbae98be3f7bdd27eb`
- source TREE `85c1d4fe2df0f980d1e4fe43c4bca11b2eeb5108`
- artifact `9933311779`
- digest `sha256:204cd7c057196220fdb60cd9662443a8703f20cbb7bc02f90d022fe8508353fa`
- record effective paths `32/32 PASS`
- source parents `33/33 PASS`
- Decision-required `22/22`
- RNG-required `9/10`
- replay NOT RUN because strict pre-replay gate failed
- coverage promotion FALSE

### Exact material blocker still under diagnosis

Missing RNG-required effective path:

`forge-behavior-v2:24a5352cfaa6ae913df6549ceed0c447d526e89d`

Source lineage:

`Descendants' Fury -> DamageDoneOnce -> TrigDigUntil -> DigUntil`

The target script contains `Cost$ Sac<1/Card.TriggeredSources>` and `RevealRandomOrder$ True`.

The source-proven parent is admitted, bound, enters MagicStack, does not fizzle, and reaches the observation-only resolution callback. The exact underlying target ability trace from valid run `33863979003` is:

```text
abilityId=712 sourceTrigger=50010 hostId=385 api=DigUntil
ANNOUNCE_TYPE=true
ANNOUNCE_X=true
CHECK_RESTRICTIONS=true
CAST_TIMING=true
LEGAL_AFTER_STACK=true
PRECOST_REQUISITES=true
PAY_COST=false
PREREQUISITES_MET=false
```

Pinned Forge source inspection confirms `Card.TriggeredSources` resolves through the root ability's `AbilityKey.Sources`, `CostSacrifice` filters battlefield candidates by that defined set plus sacrifice legality, and `CostPayment` fails when the authoritative `PaymentDecision` is null or `payAsDecided` returns false. Current semantic root cause remains `UNKNOWN` because the intended observation-only cost trace has not yet executed.

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
- RNG obligation `9/10`; the missing path remains blocked before its RNG-bearing effect by failed sacrifice cost
- replay remains blocked behind the fail-closed pre-replay gate
- latest two cost-trace successors produced no runtime evidence because their diagnostic patch failed at harness preparation
- `G3_NON_AF_STATUS = UNKNOWN`
- `COVERAGE_PROMOTION = FALSE`

## Exact next atomic package

1. Repair only the generic observation-only cost-trace patcher's ambiguous anchor selection in `ws33_instrument_g_authoritative_requests.py`. Select the intended semantic harness site structurally or with uniquely qualified surrounding context. No card-name/path-ID branching; no Forge/runtime/fixture semantics change.
2. Persist that diagnostic-repair commit.
3. Allow exactly one `ws33-g3-svar-event-runtime.yml` successor for that source commit. Do not manually dispatch an additional run.
4. Immediately enumerate runs by exact source HEAD. If more than one appears, record the protocol incident and do not create another.
5. Persist a PENDING checkpoint containing RUN/JOB/SOURCE_HEAD/SOURCE_TREE before any other runtime-affecting write.
6. Make no runtime-affecting write while the intended run is non-terminal.
7. On terminal result, bind artifact/digest, independently re-hash ZIP, inspect the cost trace, and persist PASS/FAIL before any repair.
8. Repair only the root cause directly established by that artifact. If production Forge behavior is implicated, adjudicate against current official Magic rules/card wording before changing rules code.
9. Continue until strict Runtime Record + Decision22 + RNG10 + tape-driven Replay PASS for all non-AF 32/33.
10. Freeze Runtime; then perform separate immutable ABI/Decision/RNG/Replay certification consuming that exact runtime artifact; then non-AF Principal Observation Hidden31 record/replay equivalence/no leaks.
11. Only after Direct28 + AF21 + non-AF32 satisfy all contracts promote/freeze G3 and recompute the live 4188 frontier.
12. Then execute serial `ABC -> D -> E -> F -> final cross-qualification`; do not use historical expected counts without fresh compatibility adjudication.

`G3_NON_AF_STATUS = UNKNOWN`

`COVERAGE_PROMOTION = FALSE`

`WS33_COMPLETE = FALSE`

`TASK_COMPLETE = NO`
