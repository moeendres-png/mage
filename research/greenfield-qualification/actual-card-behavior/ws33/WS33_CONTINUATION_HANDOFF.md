# WS33 CONTINUATION HANDOFF

## Completion contract

Active branch: `work/ws33-g3-final-closure-20260902`.

`TASK_COMPLETE = NO`

`WS33_COMPLETE = FALSE`

Only the final serial `G3 -> ABC -> D -> E -> F -> final cross-qualification` successor with all 4188 effective paths PASS, zero UNKNOWN/FAIL/UNSUPPORTED, A-H UNKNOWN zero, exact pin/model/lineage, and all replay/hidden/RNG/decision/failure/evidence/hash gates may change these flags.

## Stable global predecessor

- effective `4188`; PASS `285`; UNKNOWN `3903`; FAIL `0`; UNSUPPORTED `0`; G UNKNOWN `81`; H UNKNOWN `0`.
- Forge pin `8c7e9afb8e6caee88644b94e25da5852e36f8928`.
- effective-manifest file SHA256 `cd48f4279d682ab944e2534bf937d87e5311e83989e97179ae73c5c7d1bb6224`.
- topology consumer-model SHA256 `82638e6b3e4408cc5bddedc49372b6357d3c2bdce6fba7bfab7ed119678f9a48`.

## Current confirmed terminal checkpoint

`LAST_CONFIRMED_CHECKPOINT = G3_NON_AF_RUNTIME_FREEZE_RUN_33928315020_PASS`

Checkpoint:
`research/greenfield-qualification/actual-card-behavior/ws33/checkpoints/G3_NON_AF_RUNTIME_FREEZE_RUN_33928315020_PASS.md`

Checkpoint persistence commit: `214f4b4313e364cff4bc87768d31b89f752e8b0f`.

### Frozen runtime tuple

```text
SOURCE_HEAD 2896cca14dcc0d43a92957b3ddb4e8e11f1f28c7
SOURCE_TREE fbb9565d4583db655872cfd378831711b0989b7a
RUN         33928315020
JOB         101201530278
ARTIFACT    9957712911
NAME        ws33-g3-svar-event-runtime-33928315020
DIGEST      sha256:2241adad950188fc0f0adb0d0a1395a399251470dc8d8e75ded96d68d61aea0b
ZIP_SHA256  2241adad950188fc0f0adb0d0a1395a399251470dc8d8e75ded96d68d61aea0b
```

Exact-source workflow run cardinality: `1`.

GitHub Actions:

- Steps 1–13 PASS;
- Step 14 Record Campaign PASS;
- Step 15 Record Behavior + Decision/RNG obligations PASS;
- Step 16 tape-driven Replay PASS;
- Step 17 source chain / immutable hashes PASS;
- Step 18 artifact upload PASS;
- overall job/run `success`.

Evidence classification: run/job/source/artifact/digest/independent ZIP rehash and step conclusions `DIRECTLY_VERIFIED`.

## G3 non-AF Runtime Record / Replay result

Artifact-independent recomputation and retained artifact evidence establish:

- effective non-AF paths `32/32 PASS`;
- source parents `33/33 PASS`;
- Decision-required paths `22/22` present;
- RNG-required paths `10/10` present;
- record `game_completed=true`;
- replay `game_completed=true`;
- record/replay path count `32`;
- `pilot_visible_hidden_info_leaks=0` in both process records;
- `cross_principal_decision_leaks=0` in both process records;
- `phase_mismatches=0` in both process records;
- `outer_failure=null` in both process records;
- Record/Replay case-summary, parent-summary, decision tape/events/requests, RNG tape/events byte-equal under the workflow gate;
- artifact `SHA256SUMS` independently verifies all retained evidence files;
- `coverage_mutated=false`;
- `principal_observation_promoted=false`.

The artifact source chain binds the same required pins:

- Forge `8c7e9afb8e6caee88644b94e25da5852e36f8928`;
- topology artifact `9866293827` / digest `sha256:6a41f66937b4bf1bcf782045d869ece183c0be49b345eac654dc3588cb98b96b`;
- consumer model `82638e6b3e4408cc5bddedc49372b6357d3c2bdce6fba7bfab7ed119678f9a48`;
- effective manifest file `cd48f4279d682ab944e2534bf937d87e5311e83989e97179ae73c5c7d1bb6224`.

`G3.1 Runtime Record = PASS`

`G3.2 Tape-driven Replay = PASS`

`G3.3 Runtime Freeze = PASS`

Evidence classification: `DIRECTLY_VERIFIED`.

## Former blocker — closed at runtime

Root-cause checkpoint:
`research/greenfield-qualification/actual-card-behavior/ws33/checkpoints/G3_NON_AF_ENTITY_LIST_SELECTION_ROOT_CAUSE_20260905.md`

Root-cause persistence commit: `1d7c0ae79ea26c8e6773fdc491fe36284860c449`.

The WS01 synchronized `InputSelectEntitiesFromList` bridge had represented legal cancel + Card 388 as generic `choice:0` / `choice:1`; the record pilot's accepted `choice:0` decoded to legacy `CANCEL`, so `HumanCostDecision.visit(CostSacrifice)` returned null before `DigUntil` RNG.

Systemic repair commit `2896cca14dcc0d43a92957b3ddb4e8e11f1f28c7` preserves Forge legality but exposes typed entity identity and the ABI cancellation channel. No card-name/path-ID branch, singleton autopick, first/default/random/pass/cancel fallback, rules mutation, RNG mutation or coverage mutation was introduced.

For effective path `forge-behavior-v2:24a5352cfaa6ae913df6549ceed0c447d526e89d` (`Descendants' Fury -> DamageDoneOnce -> TrigDigUntil -> DigUntil`) the successful record now exposes:

- `ENTITY_LIST_SELECTION` min/max `1/1`;
- `cancelAllowed=true`;
- entity schema `commander-simulator-next.entity-selection.v1`;
- sole authoritative option `card:388`;
- Decision event `ACCEPTED`;
- sacrifice `cancelled=false selectedCount=1 selected=388`;
- `decisionNull=false`;
- `result=true reason=PAY_AS_DECIDED`;
- required DigUntil RNG event present on operation `rules.forge.game.ability.effects.DigUntilEffect.collections_shuffle.1`.

Evidence classification: runtime facts `DIRECTLY_VERIFIED`; systemic adapter diagnosis `CODE_DERIVED`.

## Active PENDING successor

`ACTIVE_PENDING_CHECKPOINT = NONE`

There is no non-terminal qualification run at this handoff point.

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

### non-AF32
- Runtime Record / Replay / runtime Decision+RNG obligations run `33928315020`; job `101201530278`; artifact `9957712911`; digest `sha256:2241adad950188fc0f0adb0d0a1395a399251470dc8d8e75ded96d68d61aea0b`; PASS and frozen.
- Separate certification consuming this exact runtime artifact: **NOT YET RUN**.
- Principal Observation Hidden31 qualification: **NOT YET RUN**.

## Current G3 frontier

- total G3 `81`;
- immutable Direct-G `28` fully qualified;
- immutable AF `21` fully qualified;
- non-AF `32` Runtime Record/Replay PASS;
- non-AF Decision obligation `22/22` PASS at runtime;
- non-AF RNG obligation `10/10` PASS at runtime;
- non-AF separate certification still required;
- non-AF Hidden31 Principal Observation still required;
- `G3_NON_AF_STATUS = UNKNOWN` until both remaining gates PASS;
- `G_PASS` is **not** promoted;
- `G_UNKNOWN` remains `81` at the stable global coverage boundary;
- `COVERAGE_PROMOTION = FALSE`.

## Retry-protocol incident retained for provenance

Source commit `2bb3a56a3edcefdd18d0a26bba5755e393ee28e7` unexpectedly produced two diagnostic runs `33907775080` and `33907795947`, both Step-12 tooling failures from an ambiguous anchor. No third run may be created from that source commit. Their immutable artifacts/digests were already independently checked and they do not supersede the frozen runtime evidence above.

## Exact resume action

1. Read-only inspect existing G3 non-AF ABI / Decision / RNG / Replay certification tooling.
2. Ensure the certification consumes exact frozen runtime artifact `9957712911` and verifies its digest `sha256:2241adad950188fc0f0adb0d0a1395a399251470dc8d8e75ded96d68d61aea0b`; do not reconstruct the runtime record from another run.
3. Execute/persist G3.4 under the same transactional retry protocol.
4. Then execute/persist G3.5 Principal Observation for the non-AF Hidden31 set: principal-scoped observations, record/replay equivalence, visibility grant/revoke lifetime, no cross-principal or hidden-card-ID leak, stable Actor/Principal identity.
5. Only after Direct28 + AF21 + non-AF32 satisfy all contracts materialize G3.6 with `G_PASS=81`, `G_UNKNOWN=0` and an immutable G3-complete checkpoint.
6. Recompute the live 4188 frontier from current canonical source.
7. Continue strictly serial `ABC -> D -> E -> F -> final cross-qualification`; historical WS27–WS32/WS29/Post-Gen2 evidence may be reused only after exact compatibility adjudication.
8. Do not mark WS33 COMPLETE until `TOTAL=4188 PASS=4188 UNKNOWN=0 FAIL=0 UNSUPPORTED=0 A-H_UNKNOWN=0 WS33_COMPLETE=TRUE TASK_COMPLETE=YES` with all cross-cutting gates valid.

`G3_NON_AF_STATUS = UNKNOWN`

`COVERAGE_PROMOTION = FALSE`

`WS33_COMPLETE = FALSE`

`TASK_COMPLETE = NO`
