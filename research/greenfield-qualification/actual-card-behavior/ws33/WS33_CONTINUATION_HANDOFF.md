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

`LAST_CONFIRMED_CHECKPOINT = G3_NON_AF_EVENT_RUNTIME_RUN_33820366293_FAILURE`

Checkpoint:
`research/greenfield-qualification/actual-card-behavior/ws33/checkpoints/G3_NON_AF_EVENT_RUNTIME_RUN_33820366293_FAILURE.md`

Run `33820366293` / job `100861534555` is terminal `failure`. Parent-correlated lifecycle evidence now rules out both a post-fizzle matcher false-negative and `MagicStack.hasFizzled` for the first `Ingenious Smith` parent: its admitted/bound `TrigDig` produces zero `MagicStack.add` lifecycle callbacks. The first unresolved production boundary is therefore inside `PlayerControllerHuman.orderAndPlaySimultaneousSa -> PlaySpellAbility.playSpellAbility` before `MagicStack.addAndUnfreeze/add`. No semantic repair is authorized until the exact first rejected play prerequisite is directly observed.

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

## Non-AF runtime attempt chain

### Attempts 1–3 — pre-runtime/hash/anchor/ChangesZone fixture

- `33797779388`: pre-runtime consumer-model hash vs manifest-file hash confusion; repaired.
- `33798342466`: pinned MagicStack declaration anchor mismatch; repaired.
- `33798608932` / artifact `9910414457` / digest `sha256:796d734fe0f3074319d4471e691ce356f4fe16d7661f8aee5223d48f1cf521c1`: Step14 PASS, Step15 FAIL, first Ingenious parent `0/0/0`; confirmed event-fixture defect (`ZoneType` vs production zone-name Strings); repair commit `3bf09bc325ee5094d2a4874bbc133520f5f759dc`.

### Attempt 4 — first admitted/bound runtime boundary

- run `33816948410`, job `100851076967`
- artifact `9916940071`, digest `sha256:4e1ed01602e46b796bdcd257964e9fc56d32aa370112c94cc57c64d8ef8b0871`
- first Ingenious parent becomes `1/1/0`; 1/33 parent PASS, 24 rows `1/1/0`, eight later event-specific failures.

### Attempts 5–6 — diagnostic infrastructure defects

- `33817799382` / artifact `9917183980`: request-trace ABI lacked lineage Event write shape; repaired by `8446cfc72060156db63237cb7c4b00045ef72fbb`.
- `33818067742` / artifact `9917297622`: diagnostic `TreeMap` compile failure; repaired by `3e2260fe7b8a1a7a1d9fea932301b6fac3b3b3c6`.

### Attempt 7 — post-fizzle lineage runtime evidence

- run `33818428322`, job `100855531128`
- source `3e2260fe7b8a1a7a1d9fea932301b6fac3b3b3c6`, tree `5f757dc8bc0c85fdea10d6e0cc8da762865e23a7`
- artifact `9917438334`, digest `sha256:696556a4e4163308ec00ef123b691a9eaa73e6742058220ac1041d73cef7fa6f`
- Step14 PASS, Step15 FAIL.
- first parent admissions/bindings/executions `1/1/0`, resolutionCallbacks `0`, admitted ability `225`, sourceTrigger `50001`, host `96`, API `Dig`, equal original/current map fingerprints.
- directly rejects post-fizzle matcher false-negative; boundary narrowed to real-stack placement vs fizzle.

### Attempt 8 — lifecycle overlay-only reproduction

- run `33819960784`, job `100860290828`
- source `8cc9085267174fa08ec44998dba75384638f70a0`, tree `46cd9b9d4f06fc1b485ae1d137e44cb5de5c85d7`
- artifact `9917974166`, digest `sha256:88dbd82d6db6318517176497ade0713fd53454e236f7e381e76d79a5f4bfe97e`
- lifecycle-enhanced MagicStack overlay applies/builds; harness did not yet consume observer; first result remains `1/1/0`, zero post-fizzle callbacks.

### Attempt 9 — parent-correlated stack lifecycle evidence

- run `33820366293`, job `100861534555`
- source `a6980d1763237c185a41456c0da81b706e285902`, tree `46945f1682b4d5ab8a30474459ff0c9217c4f3eb`
- artifact `9918110105`, digest `sha256:dd3e0b2e194654bc8fbca2acdff5c0a4411faba13b14b6d652fbf391832900df`
- artifact ZIP re-hash matched exactly.
- Steps 1–14 PASS; Step15 FAIL; replay/source-chain NOT RUN; evidence upload PASS.
- `stack-lifecycle.tsv` exists with 11 rows.
- first `Ingenious Smith` parent has **zero lifecycle rows**, therefore no `ADD_ENTER` and no possible MagicStack target reject/frozen/push/fizzle stage.
- positive control `Descendants' Fury` records `ADD_ENTER -> FROZEN_QUEUE -> ADD_ENTER -> STACK_PUSH -> FIZZLE_RESULT=false` and then resolves.
- conclusion: lifecycle observer functions; first admitted/bound target fails before `MagicStack.add`.

## Exact next atomic package

1. Add observation-only prerequisite telemetry to the exact production `PlaySpellAbility` path used by `PlayerControllerHuman.orderAndPlaySimultaneousSa` for non-copied triggers.
2. Preserve evaluation order and return values while recording the first false/rejection stage among the applicable path, including optional/additional-cost selection, extra `sa.canPlay()` where applicable, `announceType`, `announceValuesLikeX`, `checkRestrictions`, target setup, cast timing, `isLegalAfterStack`, payment/prerequisite completion, and successful transition to `MagicStack.addAndUnfreeze`.
3. Correlate stable parent key plus effective ability/source-trigger/host/API identity. Output an immutable play-prerequisite trace.
4. Do not choose options, pay costs, mutate targets, bypass restrictions/timing, change trigger legality, change stack semantics, change `matchesTarget`/`targetExecutions`, fabricate Decision/RNG evidence, or mutate coverage.
5. Commit diagnostic instrumentation separately; trigger exactly one successor run; persist run/job/source HEAD/TREE immediately.
6. Terminally adjudicate the first Ingenious parent and repair only the directly confirmed systemic defect.
7. Freeze every failure before repair/retry.
8. Continue until Runtime strict PASS; then freeze Runtime before separate ABI/Decision/RNG/Replay certification and Principal Observation/Hidden31 qualification.
9. Only after Direct28 + AF21 + non-AF32 satisfy all behavior/decision/RNG/replay/hidden/provenance/fail-closed contracts may G3 be promoted/frozen and serial closure proceed to `ABC -> D -> E -> F`.

Control expectations remain non-authoritative until fresh successor computation: post-G3 PASS366/UNKNOWN3822; post-ABC 1920/2268; post-D 2840/1348; post-E 3869/319; post-F 4188/0.
