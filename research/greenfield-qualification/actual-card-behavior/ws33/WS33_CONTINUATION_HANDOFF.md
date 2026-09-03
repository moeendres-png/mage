# WS33 CONTINUATION HANDOFF

## Completion contract

Active branch: `work/ws33-g3-final-closure-20260902`.

The operative state is artifact/checkpoint-driven. Historical root/current JSON names are not automatically current closure truth.

`TASK_COMPLETE = NO`

`WS33_COMPLETE = FALSE`

Only the final serial `G3 -> ABC -> D -> E -> F` successor with all 4188 effective paths PASS, zero UNKNOWN/FAIL/UNSUPPORTED, A-H UNKNOWN zero, exact pin/model/lineage, and all replay/hidden/RNG/decision/failure/evidence/hash gates may change these flags.

## Stable predecessor

- effective `4188`; PASS `285`; UNKNOWN `3903`; FAIL `0`; UNSUPPORTED `0`; G UNKNOWN `81`; H UNKNOWN `0`.
- Forge pin `8c7e9afb8e6caee88644b94e25da5852e36f8928`.
- effective-manifest file SHA256 `cd48f4279d682ab944e2534bf937d87e5311e83989e97179ae73c5c7d1bb6224`.
- predecessor artifact `9823383539`, digest `sha256:aab73ba2ede151bbd0b803c2164d3067ddd65f17d49cf655c34eef67d903595d`.

## Current confirmed checkpoint

`LAST_CONFIRMED_CHECKPOINT = G3_NON_AF_EVENT_RUNTIME_RUN_33798608932_FAILURE`

Checkpoint:
`research/greenfield-qualification/actual-card-behavior/ws33/checkpoints/G3_NON_AF_EVENT_RUNTIME_RUN_33798608932_FAILURE.md`

Run `33798608932` / job `100792262743` is terminal `failure` and fully adjudicated through its first material Step-15 failure. No further retry may be started until the narrow confirmed event-fixture repair is committed.

## G3 immutable evidence — do not rerun for reassurance

### Topology

- run `33681121017` SUCCESS
- job `100417671589` SUCCESS
- source HEAD `4032d9c14dc7840e2518a92273037aaba443ada9`
- source TREE `d86b141171397d8a3d59c556f45b27f8cc6268d9`
- artifact `9866293827`
- digest `sha256:6a41f66937b4bf1bcf782045d869ece183c0be49b345eac654dc3588cb98b96b`
- schema `commander-simulator-next.ws33-g-svar-consumer-topology.v2`
- topology consumer-model SHA256 `82638e6b3e4408cc5bddedc49372b6357d3c2bdce6fba7bfab7ed119678f9a48`
- partition: `G81 = Direct28 + SVar53`, unresolved parents `0`; SVar = `AF21 + non-AF32`; non-AF = `33` real source-proven production parent entrypoints.

Important hash distinction: topology v2's `effective_model_sha256` is the effective manifest's `consumer_model_sha256`; it is not the SHA256 of `WS33_EFFECTIVE_BEHAVIOR_PATH_MANIFEST.json`. Do not equate `82638e...` with the manifest-file SHA `cd48f427...`.

### Direct-G 28

Behavior run `33516084949` / artifact `9803814288` / digest `sha256:493f3549b6483d4fea9644f3a0216deb108a9ac581b651ff3e083499bcb14b5a`: `28/28` Record/Replay PASS.

Principal Observation v4 run `33552816460` / artifact `9818304005` / digest `sha256:7b39edd3cd67f1e0b398db90fbb592b7786372fe5b398b1a0bed39e79d24bbfc`: principal-scoped observation/hidden gates PASS.

Requirement artifact `9822685407`, digest `sha256:81e1e24551403453e4dd32e9ed65951cbaca2776cc993eddf475b4214a67a424`, remains the successfully generated-and-strictly-verified requirement evidence. Its parent workflow later failed during branch materialization and is not reclassified as a workflow PASS.

### AF21

AF is qualification-complete through focused immutable gates:

- Runtime v2 run `33773548765` PASS.
- ABI/Decision/RNG/Replay v2 run `33773805031` PASS.
- Principal Observation v5 run `33774853355` PASS; job `100713875152`; artifact `9901438964`; digest `sha256:2e60f7c79ad642f3f3942db4b3e84a9392cde5662126c0eb84153a3f0469cb5d`.

Do not rerun these without a concrete invalidating code/pin/contract change.

## Current G3 frontier

- total G3: `81`
- immutable Direct-G qualified: `28`
- immutable AF qualified: `21`
- remaining effective paths: `32`
- remaining production parent entrypoints: `33`
- global G3 coverage promotion: `FALSE`

Remaining production-parent modes: ChangesZone `12`, Phase `6`, Attacks `5`, DamageDone `4`, SpellCast `2`, AttackersDeclared `2`, DamageDoneOnce `1`, Sacrificed `1`.

Invariant: Kang Prime retains both real source-proven parent entrypoints.

## Non-AF runtime attempts

### Attempt 1 — adjudicated

- source `0b1afc7be70f5a74b38516e3848f526f3693eac4`
- run `33797779388`, job `100789526018`, failure before runtime
- cause: topology consumer-model hash `82638e...` was incorrectly compared to manifest-file hash `cd48f...`.

### Attempt 2 — adjudicated

- source `935da1abf48b84f85e4265a26ba65fb546e8cb07`
- run `33798342466`, job `100791376533`, partial artifact `9910100377`
- digest `sha256:ced3f9f26efe6f0540b4d8b661f5afad0fea2adc5071762866864658d1fb846a`
- cause: observation-only MagicStack overlay used a class-declaration anchor that omitted pinned Forge's literal `/* extends MyObservable */` comment.

### Attempt 3 — terminal and adjudicated

- source HEAD `26ec46d852a731054e8719e5bf1ea37bef3f6ea6`
- source TREE `793c1e3c10cf07f4d0b432a56aa0f90e73eb7fe0`
- run `33798608932`
- job `100792262743`
- artifact `9910414457`
- digest `sha256:796d734fe0f3074319d4471e691ce356f4fe16d7661f8aee5223d48f1cf521c1`
- artifact ZIP re-hash matched exactly
- Step 14 record campaign: PASS
- Step 15 record adjudication: FAIL
- replay: NOT RUN
- coverage promotion: FALSE
- non-AF32: UNKNOWN

First Step-15 predicate failure: parent runtime. The first bad parent in artifact order is `forge-behavior-v2:172ab06795f99590ca9d96f85995f6cf9e083ee8#1` (`Ingenious Smith`, `ChangesZone`) with `triggerAdmissions=0`, `targetBindings=0`, `targetExecutions=0`.

Root cause classification: **event-fixture defect**. The harness synthesizes `AbilityKey.Origin` / `AbilityKey.Destination` as `ZoneType` enums. Pinned Forge production `GameAction.changeZone` writes the zone `.name()` strings, and pinned `TriggerChangesZone.performTest` compares against the trigger's string values. The enum-valued fixture is therefore rejected before legal trigger admission. This is not evidence of a Rules-Core defect.

Exact failure details and the first-eight-row adjudicator output are frozen in `G3_NON_AF_EVENT_RUNTIME_RUN_33798608932_FAILURE.md`.

## Exact next atomic package

1. Repair only the common `ChangesZone` fixture shape in `ws33_prepare_g_svar_event_harness.py`: emit production-equivalent String zone names for `AbilityKey.Origin` and `AbilityKey.Destination`.
2. No card-name/path-ID branches, no direct target-SVar entry, no TriggerHandler bypass, no fabricated Decision/RNG evidence, no silent fallback.
3. Commit the repair separately.
4. Let exactly one `ws33-g3-svar-event-runtime.yml` run start from that repair commit.
5. Immediately persist new run/job/source HEAD/TREE in a pending-run checkpoint before any other repair.
6. Adjudicate that run to terminal. If it fails, freeze its first material failure before another repair.
7. If Runtime becomes strict PASS, perform separate ABI/Decision/RNG/Replay certification consuming its exact artifact, then separate Principal Observation/Hidden qualification for Hidden31.
8. Only then materialize/promote/freeze G3 and continue serial `ABC -> D -> E -> F`.

Control expectations are non-authoritative until fresh successor computation: post-G3 PASS366/UNKNOWN3822; post-ABC 1920/2268; post-D 2840/1348; post-E 3869/319; post-F 4188/0.
