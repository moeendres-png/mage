# WS33 CONTINUATION HANDOFF

## Authority / completion contract

Active branch: `work/ws33-g3-final-closure-20260902`.

The operative WS33 state is artifact-driven. Repository-root WS33 JSON files are tooling/reference inputs and are **not** the current 4188-path operational successor. Do not copy artifact contents into root state to simulate promotion.

`TASK_COMPLETE = NO`

`WS33_COMPLETE = FALSE`

These flags may become true only after the serial G3 -> ABC -> D -> E -> F successor proves all 4188 effective paths PASS, UNKNOWN/FAIL/UNSUPPORTED all zero, A-H UNKNOWN all zero, plus all required replay/hidden/RNG/decision/failure/evidence/hash/lineage gates.

## Stable operational predecessor

- effective `4188`; PASS `285`; UNKNOWN `3903`; FAIL `0`; UNSUPPORTED `0`; G UNKNOWN `81`; H UNKNOWN `0`.
- Forge pin `8c7e9afb8e6caee88644b94e25da5852e36f8928`.
- effective model SHA256 `cd48f4279d682ab944e2534bf937d87e5311e83989e97179ae73c5c7d1bb6224`.
- predecessor artifact `9823383539`, digest `sha256:aab73ba2ede151bbd0b803c2164d3067ddd65f17d49cf655c34eef67d903595d`.

### Immutable Direct-G evidence — do not rerun for reassurance

Behavior run `33516084949`, HEAD `d8af15cb879bdfc3c40ce4cba3462da24ee3f272`, TREE `857dc01e04f58ca59437e08710bcb194bf030ea4`, artifact `9803814288`, digest `sha256:493f3549b6483d4fea9644f3a0216deb108a9ac581b651ff3e083499bcb14b5a`: Record `28/28 PASS`, Replay `28/28 PASS`, semantic replay PASS, stack admission/resolution PASS, hidden leak 0, cross-principal leak 0.

Principal Observation v4 run `33552816460`, artifact `9818304005`: 28 paths, hidden-required 24, record/replay observation events 1496/1496, unauthorized/private leak delta 0, cross-principal leak delta 0.

G requirement migration run `33564749471`, artifact `9822685407`, digest `sha256:81e1e24551403453e4dd32e9ed65951cbaca2776cc993eddf475b4214a67a424`: Hidden 74, RNG 21, Replay 57, Decision 50; ABI V2.1 PASS; 17 negative fixtures rejected; `ws33_verify.py` PASS.

## G3 items already closed — do not repeat

- principal-scoped DecisionEvent repair/hardening: run `33690697036`, artifact `9870061705`, digest `sha256:21bfde999292f5d3a3d1cc5f27e5236ab352972cedde7b32691ea5ad31fbe0cd` PASS.
- 53-SVar topology: run `33681121017`, artifact `9866293827`, digest `sha256:6a41f66937b4bf1bcf782045d869ece183c0be49b345eac654dc3588cb98b96b` PASS; `G81=Direct28+SVar53`; unresolved parents 0.
- topology hash-space mismatch fixed (`MODEL_FILE_SHA=cd48...`, embedded consumer-model SHA `82638e6b3e4408cc5bddedc49372b6357d3c2bdce6fba7bfab7ed119678f9a48`).
- AF parents bind actual Card root ability / named parent SVar; no detached script reconstruction.
- target-SVar observer at `AbilitySub.resolve()` is observation-only.
- AF case ABI is 19 fields.
- compile-scope defect from run `33742586083` closed by commit `3ca8c330287ef1f140b5be9e0c46187c762a7c7b`.
- Kindred Summons generic ChooseType reachability defect closed in run `33743144684`.

## Current G3 checkpoint — 2026-09-03

`LAST_CONFIRMED_CHECKPOINT = G3_SVAR_AF_AUTHORITATIVE_CHARM_MODE_FIX_VALIDATION_RUNNING`

### Last fully adjudicated AF run

Commit `3ca8c330287ef1f140b5be9e0c46187c762a7c7b`, TREE `0fa6dd43fff0176037f97a5d5f79789b61e029ac`.

- run `33743144684`; job `100609469759`; artifact `9888664547`; digest `sha256:ded468207a7d4b61d95d3a87967a7eb923d083b10b1c45157f7408bd9b2040be`.
- downloaded ZIP SHA256 exactly matches digest.
- Maven/Forge `BUILD SUCCESS`; tests failures/errors 0/0.
- case rows `21/21`; behavior `21/21 PASS`; stack admission/resolution `21/21`; exact target-SVar reachability `18/21`.
- workflow correctly red because exactly three Charm paths have `targetExecutions=0`.
- diagnostic only; no promotion.

Remaining gaps from that run:
1. `forge-behavior-v2:95726bbbfdb31ba1e8fe7146f4a7971d93f97bc5a` — Ao, the Dawn Sky — `Charm -> TrigDig -> DigEffect`.
2. `forge-behavior-v2:a1fe7a20bc3ddb26ed8642a7a8b5025697bd0d83` — Atsushi, the Blazing Sky — `Charm -> ExileTwo -> DigEffect`.
3. `forge-behavior-v2:ee17650cc69e7d571ba8a6d602227eb4c8ba6154` — Prismari Charm — `Charm -> DBSurveil -> SurveilEffect`.

`CODE_DERIVED` root cause: `CharmEffect.makeChoices(sa)` now executes and emits real `MODE_SELECTION`; the previous pilot selected raw `Choices$` ordinal, but Forge filters illegal modes before the authoritative request, so raw ordinal can shift. This is a qualification-pilot reachability defect, not a Forge Dig/Surveil/Charm rules failure.

Diagnostic note: `record/process.json` in run `33743144684` reports `pilot_visible_hidden_info_leaks=1`, `cross_principal_decision_leaks=0`, `outer_failure=null`. This must be separately adjudicated before AF promotion.

### Current atomic repair — persistent, validation running

Code commit:
- HEAD `1cff246a32df32788736576b4bd5e21ad73cdfec`
- TREE `2ac534258f68ef20d5d8843902a488a4fbccfa9d`
- message `ws33 g3: bind Charm choice by authoritative mode identity`.

Repair semantics:
- removes raw Choice ordinal selection completely;
- locates exactly one target `AbilitySub` from the actual parsed parent's raw `Choices` by exact target API/map identity;
- records only its opaque semantic identity `ability_sub:<id>` as desired reachability target;
- production `CharmEffect.makeChoices(sa)` remains authoritative for legal-mode filtering;
- external pilot selects the desired mode only if exactly one authoritative `MODE_SELECTION` option exposes the same semantic identity; absent/ambiguous membership fails closed with `UNSUPPORTED_DECISION_PATH`;
- no synthetic options, no card-name branch, no direct target-SVar entry, no direct `sa.resolve()`, no manual target injection.

Focused validation:
- run `33745157361`
- exact head `1cff246a32df32788736576b4bd5e21ad73cdfec`
- state at checkpoint: `IN_PROGRESS`.

If interrupted, adjudicate run `33745157361` first. Do not rerun or modify this repair before reading its exact job result and retained artifact.

### Exactly next work package

1. Adjudicate run `33745157361` and artifact.
2. Acceptance for focused AF behavior: `21/21 PASS`, stack admission/resolution `21/21`, exact target-SVar reachability `21/21`.
3. If red, isolate only its first new root cause, checkpoint, then repair systemically.
4. If green, separately close the source-required Hidden/RNG/Replay/Decision obligations for all 21 AF paths; focused record-only green is not promotion-complete.
5. Persist that evidence before beginning the 32-path non-AF event campaign.

## Non-AF G queue already materialized, not yet qualified

`ws33_prepare_g_svar_event_cases.py` materializes exactly 32 effective paths / 33 source-proven event parents, preserves the true two-parent Kang Prime path, and forbids direct target-SVar entry. Modes: ChangesZone 12, Phase 6, Attacks 5, DamageDone 4, SpellCast 2, AttackersDeclared 2, DamageDoneOnce 1, Sacrificed 1.

## Subsequent serial queue

Only after G3 reaches `81/81 PASS` with all evidence obligations and an exact frozen successor may campaigns proceed `ABC -> D -> E -> F`.

Control expectations only, never source truth until freshly computed: post-G3 PASS366/UNKNOWN3822; post-ABC 1920/2268; post-D 2840/1348; post-E 3869/319; post-F 4188/0.
