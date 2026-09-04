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

`LAST_CONFIRMED_CHECKPOINT = G3_NON_AF_EVENT_RUNTIME_RUN_33863979003_FAILURE`

Checkpoint:
`research/greenfield-qualification/actual-card-behavior/ws33/checkpoints/G3_NON_AF_EVENT_RUNTIME_RUN_33863979003_FAILURE.md`

Corrected checkpoint commit: `349e58b79a87c82afd20a7466c8e3e7edbad73a6`.

Run `33863979003` / job `100994503842` is terminal `failure`.

- source HEAD `35a2a267fa70b87a4d21d5cbae98be3f7bdd27eb`
- source TREE `85c1d4fe2df0f980d1e4fe43c4bca11b2eeb5108`
- artifact `9933311779`
- artifact name `ws33-g3-svar-event-runtime-33863979003`
- digest `sha256:204cd7c057196220fdb60cd9662443a8703f20cbb7bc02f90d022fe8508353fa`
- independently downloaded ZIP re-hash: exact match
- record effective paths `32/32 PASS`
- source parents `33/33 PASS`
- `game_completed=true`; `path_count=32`; no observed pilot-hidden/cross-principal/phase leak
- Decision-required `22/22`; missing `0`
- RNG-required `9/10`; missing exactly one effective path
- replay NOT RUN because strict pre-replay gate failed
- coverage promotion FALSE

### Exact first material blocker

Missing RNG-required effective path:

`forge-behavior-v2:24a5352cfaa6ae913df6549ceed0c447d526e89d`

Source lineage:

`Descendants' Fury -> DamageDoneOnce -> TrigDigUntil -> DigUntil`

The target script contains `Cost$ Sac<1/Card.TriggeredSources>` and `RevealRandomOrder$ True`.

The source-proven parent is admitted, bound, enters MagicStack, does not fizzle, and reaches the observation-only resolution callback. However the exact underlying target ability trace is:

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

Therefore the `DigUntilEffect` random-order body is not reached. The prior hypothesis that the failure was only a degenerate `Collections.shuffle` witness is invalidated and has been removed from the canonical checkpoint.

Pinned `TriggerDamageDoneOnce` writes the actual damage-source collection to triggering object `AbilityKey.Sources`; the harness creates a controlled `Runeclaw Bear` in the battlefield `DamageMap`. Trigger admission succeeds. The unresolved boundary is now authoritative sacrifice-cost materialization/payment for `Card.TriggeredSources` on the target ability.

Current root-cause status: `UNKNOWN`. Do not repair Forge or the fixture until a generic observation-only cost trace distinguishes fixture omission, triggering-object propagation, authoritative selection/payment integration, or another cost prerequisite.

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
- latest record behavior materially green `32/32 paths`, `33/33 parents`
- Decision obligation materially green `22/22`
- RNG obligation `9/10`, but the one missing path is blocked before its RNG-bearing effect by failed sacrifice cost
- replay remains blocked behind the fail-closed pre-replay gate
- `G3_NON_AF_STATUS = UNKNOWN`
- `COVERAGE_PROMOTION = FALSE`

## Exact next atomic package

1. Inspect pinned sacrifice-cost and `TriggeredSources` resolution/payment source read-only.
2. Add a single generic observation-only cost-boundary diagnostic. It must expose for the affected ability shape: triggering `Sources` visibility, computed sacrifice candidate set, authoritative selected entity/option, and cost-part result. No card-name/path-ID branching.
3. Persist that diagnostic commit.
4. Trigger exactly one `ws33-g3-svar-event-runtime.yml` successor run from that commit.
5. Immediately persist a PENDING checkpoint with RUN/JOB/SOURCE_HEAD/SOURCE_TREE before any other runtime-affecting write.
6. Make no runtime-affecting write while the run is non-terminal.
7. On terminal result, bind artifact/digest and persist PASS/FAIL before any repair.
8. Repair only the root cause directly established by that artifact. If production Forge behavior is implicated, adjudicate against current official Magic rules/card wording before changing rules code.
9. Continue until strict Runtime Record + Decision22 + RNG10 + tape-driven Replay PASS for all non-AF 32/33.
10. Freeze Runtime; then perform separate immutable ABI/Decision/RNG/Replay certification consuming that exact runtime artifact; then non-AF Principal Observation Hidden31 record/replay equivalence/no leaks.
11. Only after Direct28 + AF21 + non-AF32 satisfy all contracts promote/freeze G3 and recompute the live 4188 frontier.
12. Then execute serial `ABC -> D -> E -> F -> final cross-qualification`; do not use historical expected counts without fresh compatibility adjudication.

`G3_NON_AF_STATUS = UNKNOWN`

`COVERAGE_PROMOTION = FALSE`

`WS33_COMPLETE = FALSE`

`TASK_COMPLETE = NO`
