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

`LAST_CONFIRMED_CHECKPOINT = G3_NON_AF_EVENT_RUNTIME_TOPOLOGY_ASSERT_FAIL_33797779388`

Checkpoint:
`research/greenfield-qualification/actual-card-behavior/ws33/checkpoints/G3_NON_AF_EVENT_RUNTIME_TOPOLOGY_ASSERT_FAIL_33797779388.md`

The failed run is fully adjudicated. It is a pre-runtime qualification-infrastructure failure; the non-AF frontier remains UNKNOWN and no behavior failure or coverage promotion is established.

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

Important hash distinction: topology v2 writes `effective_model_sha256` from the effective manifest's `consumer_model_sha256`; it is not the SHA256 of `WS33_EFFECTIVE_BEHAVIOR_PATH_MANIFEST.json`. Do not equate `82638e...` with the predecessor manifest-file SHA `cd48f427...`.

### Direct-G 28

Behavior:
- run `33516084949` SUCCESS
- HEAD `d8af15cb879bdfc3c40ce4cba3462da24ee3f272`
- TREE `857dc01e04f58ca59437e08710bcb194bf030ea4`
- artifact `9803814288`
- digest `sha256:493f3549b6483d4fea9644f3a0216deb108a9ac581b651ff3e083499bcb14b5a`
- Record/Replay `28/28 PASS`; stack/semantic replay PASS.

Principal Observation v4:
- run `33552816460` SUCCESS
- HEAD `3be666cc268456274204d39b2bd3c208f0d8c41e`
- TREE `e9979879f1eb9082c45d52f87744f5bb4f7407fb`
- artifact `9818304005`
- digest `sha256:7b39edd3cd67f1e0b398db90fbb592b7786372fe5b398b1a0bed39e79d24bbfc`
- 28 paths; principal-scoped hidden/observation gates PASS.

Requirement evidence:
- run `33564749471` overall FAILURE and is not reclassified as a workflow PASS.
- requirement generation, strict verification, and immutable artifact upload steps PASS.
- later branch-materialization step failed.
- artifact `9822685407`, digest `sha256:81e1e24551403453e4dd32e9ed65951cbaca2776cc993eddf475b4214a67a424` remains the successfully generated-and-verified requirement evidence.

### AF21

AF is qualification-complete through focused immutable gates:
- AF Runtime v2 certified run `33773548765` PASS.
- AF ABI/Decision/RNG/Replay v2 run `33773805031` PASS.
- AF Principal Observation v5 run `33774853355` PASS; job `100713875152`; artifact `9901438964`; digest `sha256:2e60f7c79ad642f3f3942db4b3e84a9392cde5662126c0eb84153a3f0469cb5d`.

The v5 gate proves Record, tape-driven Replay, observation-only nonperturbation, shape-aware principal lifecycle adjudication, source-chain hashing, and artifact upload for AF21.

## Current G3 frontier

- total G3: `81`
- immutable Direct-G qualified: `28`
- immutable AF qualified: `21`
- remaining effective paths: `32`
- remaining production parent entrypoints: `33`
- global G3 coverage promotion: `FALSE`

Event-case ABI v2 is persisted. Observation-only trigger-admission and non-fizzled stack-resolution hooks are persisted. The event harness is persisted and keeps Forge `TriggerHandler` authoritative; target SVars are never entered directly. Request tracing and ABI adjudication now support the exact Event-v21 parent ABI while preserving Direct-v15 / AF-v19 fail-closed discrimination.

Remaining production-parent modes:
- ChangesZone 12
- Phase 6
- Attacks 5
- DamageDone 4
- SpellCast 2
- AttackersDeclared 2
- DamageDoneOnce 1
- Sacrificed 1

Invariant: the Kang Prime effective path retains both real equivalent production parents.

## First non-AF runtime attempt — adjudicated

Workflow source commit: `0b1afc7be70f5a74b38516e3848f526f3693eac4`

- source TREE `e9d39da970809555e3246cb2b156ac7156cc3ae5`
- run `33797779388`
- job `100789526018`
- conclusion `failure`
- artifact: none
- first material failure: Step 3 topology assertion before Forge checkout/build/runtime
- cause: workflow compared topology's consumer-model hash `82638e...` with effective-manifest-file hash `cd48f...`
- secondary failure: always-upload required a late-created `generated/SHA256SUMS`, so no partial-failure artifact was emitted
- Maven/runtime Record/Replay did not execute
- non-AF32 remains UNKNOWN

## Exact next atomic package

1. Repair `.github/workflows/ws33-g3-svar-event-runtime.yml` only for the adjudicated infrastructure defects:
   - explicitly retain both hash semantics;
   - assert topology v2 against consumer-model SHA `82638e...` plus immutable artifact run/head/digest;
   - reduce current-tooling checkout to `fetch-depth: 1`;
   - upload the existing `generated/` tree on early failure instead of requiring a not-yet-created hash file.
2. Persist the repair commit before execution.
3. The workflow push may create exactly one corrective run; persist its run/job/source identity immediately.
4. Adjudicate that run before any additional retry.
5. When non-AF Runtime Record/Replay is strict PASS, verify artifact digest/content and checkpoint it immutable.
6. Run separate immutable ABI/Decision/RNG/Replay certification consuming the actual Runtime artifact.
7. Run separate Principal Observation/Hidden qualification for the 31 hidden-required non-AF paths.
8. Only after all non-AF gates are green may G3 be materialized/promoted and frozen.
9. Only then continue serial `ABC -> D -> E -> F`.

Control expectations after fresh successor computation only: post-G3 PASS366/UNKNOWN3822; post-ABC 1920/2268; post-D 2840/1348; post-E 3869/319; post-F 4188/0.
