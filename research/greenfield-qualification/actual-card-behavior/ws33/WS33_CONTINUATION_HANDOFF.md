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

Run `33863979003` / job `100994503842` is terminal `failure`.

- source HEAD `35a2a267fa70b87a4d21d5cbae98be3f7bdd27eb`
- source TREE `47ff4fdd99f63fc3489dc8a2055536de31a8165a`
- artifact `9933311779`
- artifact name `ws33-g3-svar-event-runtime-33863979003`
- digest `sha256:204cd7c057196220fdb60cd9662443a8703f20cbb7bc02f90d022fe8508353fa`
- downloaded ZIP re-hash: exact match
- record effective paths `32/32 PASS`
- source parents `33/33 PASS`
- `game_completed=true`; `path_count=32`; no observed hidden/cross-principal/phase leak
- Decision-required `22/22`; missing `0`
- RNG-required `9/10`; missing exactly one effective path
- replay NOT RUN because strict pre-replay ABI gate failed
- coverage promotion FALSE

### First material blocker

Exactly one required RNG path has no correlated RNG tape event:

`forge-behavior-v2:24a5352cfaa6ae913df6549ceed0c447d526e89d`

Source lineage:

`Descendants' Fury -> DamageDoneOnce -> TrigDig -> DigUntil`

The target script carries `RevealRandomOrder$ True`. Admission, binding, target execution, and resolution callback are all achieved; the path simply has zero RNG-tape rows.

Pinned Forge `DigUntilEffect` removes the found card from the revealed collection and then, for `RevealRandomOrder`, calls `Collections.shuffle(revealed, MyRandom.getRandom())`. The current qualification fixture does not guarantee a non-degenerate remainder. If the remainder is empty or singleton, shuffle need not consume an RNG value. Current classification is therefore a systemic qualification-fixture under-exercise of a production-reachable random-order branch, not evidence of an event-resolution rules-core failure.

The required successor is a generalized script-semantic `RevealRandomOrder` fixture that guarantees at least two nonmatching revealed objects remain after the matching object is removed, preserves the actual matcher semantics, and fails closed for unsupported matcher shapes. It must not special-case card names or effective IDs and must not alter rules, decisions, RNG implementation, coverage, or fallback behavior.

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
- latest record runtime materially green `32/32 paths`, `33/33 parents`
- Decision obligation now materially green `22/22`
- remaining strict Runtime blocker: one of ten required RNG paths lacks a non-degenerate RNG witness
- replay remains blocked behind that fail-closed prerequisite
- `G3_NON_AF_STATUS = UNKNOWN`
- `COVERAGE_PROMOTION = FALSE`

## Exact next atomic package

1. Inspect the current generic source-fixture construction and pinned zone/library ordering semantics read-only.
2. Implement one generalized script-semantic non-degenerate `RevealRandomOrder$ True` fixture for supported matcher shapes; no card/path-name conditions.
3. Persist the repair commit.
4. Trigger exactly one `ws33-g3-svar-event-runtime.yml` successor run from that repair commit.
5. Immediately persist a PENDING checkpoint with RUN/JOB/SOURCE_HEAD/SOURCE_TREE before any other runtime-affecting write.
6. Make no runtime-affecting write while that run is non-terminal.
7. On terminal result, bind artifact/digest and persist PASS/FAIL before the next step.
8. Continue until strict Runtime Record + Decision22 + RNG10 + tape-driven Replay PASS for all non-AF 32/33.
9. Freeze Runtime, then separate immutable ABI/Decision/RNG/Replay certification consuming that exact artifact, then non-AF Principal Observation Hidden31 record/replay equivalence/no leaks.
10. Only after Direct28 + AF21 + non-AF32 satisfy all contracts promote/freeze G3 and recompute live 4188 frontier.
11. Then execute serial `ABC -> D -> E -> F -> final cross-qualification`; do not use historical expected counts without fresh compatibility adjudication.

`G3_NON_AF_STATUS = UNKNOWN`

`COVERAGE_PROMOTION = FALSE`

`WS33_COMPLETE = FALSE`

`TASK_COMPLETE = NO`
