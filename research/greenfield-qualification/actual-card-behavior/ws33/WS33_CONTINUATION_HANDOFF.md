# WS33 CONTINUATION HANDOFF

## Authority / completion contract

Branch lineage under active work: `work/ws33-g3-final-closure-20260902`.

The operative WS33 state is artifact-driven. Repository-root WS33 JSON files are tooling/reference inputs and are **not** the current 4188-path operational successor. Do not copy artifact contents into root state to simulate promotion.

`TASK_COMPLETE = NO`

`WS33_COMPLETE = FALSE`

These flags may become true only after the final serial G3 -> ABC -> D -> E -> F successor proves all 4188 effective paths PASS, UNKNOWN/FAIL/UNSUPPORTED all zero, A-H UNKNOWN all zero, and the required replay/hidden/RNG/decision/failure/evidence/hash/lineage gates pass.

## Stable operational predecessor

- effective paths: `4188`
- PASS: `285`
- UNKNOWN: `3903`
- FAIL: `0`
- UNSUPPORTED: `0`
- G UNKNOWN: `81`
- H UNKNOWN: `0`
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- effective model SHA256: `cd48f4279d682ab944e2534bf937d87e5311e83989e97179ae73c5c7d1bb6224`
- operational predecessor artifact: `9823383539`
- predecessor digest: `sha256:aab73ba2ede151bbd0b803c2164d3067ddd65f17d49cf655c34eef67d903595d`

### Immutable Direct-G evidence — do not rerun for reassurance

Behavior:
- run `33516084949`
- HEAD `d8af15cb879bdfc3c40ce4cba3462da24ee3f272`
- TREE `857dc01e04f58ca59437e08710bcb194bf030ea4`
- artifact `9803814288`
- digest `sha256:493f3549b6483d4fea9644f3a0216deb108a9ac581b651ff3e083499bcb14b5a`
- Record `28/28 PASS`, Replay `28/28 PASS`, semantic replay PASS, stack admission/resolution PASS, hidden leak `0`, cross-principal leak `0`.

Principal Observation v4:
- run `33552816460`
- artifact `9818304005`
- 28 paths, hidden-required 24, record/replay observation events 1496/1496, unauthorized/private leak delta 0, cross-principal leak delta 0.

G requirement migration:
- run `33564749471`
- artifact `9822685407`
- digest `sha256:81e1e24551403453e4dd32e9ed65951cbaca2776cc993eddf475b4214a67a424`
- requirements: Hidden 74, RNG 21, Replay 57, Decision 50
- ABI V2.1 PASS, 17 negative fixtures rejected for intended reason, `ws33_verify.py` PASS.

## G3 items already closed — do not repeat

- DecisionEvent identity repaired to principal scope and hardened; ABI run `33690697036`, artifact `9870061705`, digest `sha256:21bfde999292f5d3a3d1cc5f27e5236ab352972cedde7b32691ea5ad31fbe0cd` PASS.
- 53-SVar topology run `33681121017`, artifact `9866293827`, digest `sha256:6a41f66937b4bf1bcf782045d869ece183c0be49b345eac654dc3588cb98b96b` PASS; `G81 = Direct28 + SVar53`; unresolved parents `0`.
- topology hash-space mismatch fixed (`MODEL_FILE_SHA=cd48...`, embedded consumer-model SHA `82638e6b3e4408cc5bddedc49372b6357d3c2bdce6fba7bfab7ed119678f9a48`).
- AF parent construction binds actual Card root ability / named parent SVar, not detached script.
- target-SVar observation hook at `AbilitySub.resolve()` is observation-only.
- AF case ABI is 19 fields.
- prior compile-scope defect from run `33742586083` was repaired by commit `3ca8c330287ef1f140b5be9e0c46187c762a7c7b`; do not revisit.

## Current G3 checkpoint — 2026-09-03

`LAST_CONFIRMED_CHECKPOINT = G3_SVAR_AF_THREE_CHARM_MODE_GAPS_ADJUDICATED`

Current branch before this checkpoint commit:
- HEAD `01edee49b91ee3f0159ba7d10d10901f62fc8854`
- TREE `d571d26cb9c4042170e8753806ebda816751ad10`

### Focused AF validation after path-spec scope fix

Exact behavior-bearing commit:
- HEAD `3ca8c330287ef1f140b5be9e0c46187c762a7c7b`
- TREE `0fa6dd43fff0176037f97a5d5f79789b61e029ac`
- run `33743144684`
- job `100609469759`
- artifact `9888664547`
- artifact digest `sha256:ded468207a7d4b61d95d3a87967a7eb923d083b10b1c45157f7408bd9b2040be`
- downloaded ZIP SHA256 exactly matches artifact digest.

Direct artifact adjudication:
- Maven / Forge: `BUILD SUCCESS`; test failures/errors `0/0`.
- case rows `21/21`, each with 21 fields.
- behavior status `21/21 PASS`.
- stack admission `21/21`.
- stack resolution `21/21`.
- exact target-SVar reachability `18/21`.
- Kindred Summons `ChooseType -> DBDigUntil` is now reached: prior generic type-selection defect CLOSED.
- workflow is correctly red because three Charm paths still have `targetExecutions=0`.
- diagnostic only; no coverage mutation or promotion authorized.

Three remaining exact gaps:
1. `forge-behavior-v2:95726bbbfdb31ba1e8fe7146f4a7971d93f97bc5a` — Ao, the Dawn Sky — `Charm -> TrigDig -> DigEffect`.
2. `forge-behavior-v2:a1fe7a20bc3ddb26ed8642a7a8b5025697bd0d83` — Atsushi, the Blazing Sky — `Charm -> ExileTwo -> DigEffect`.
3. `forge-behavior-v2:ee17650cc69e7d571ba8a6d602227eb4c8ba6154` — Prismari Charm — `Charm -> DBSurveil -> SurveilEffect`.

Additional diagnostic only: `record/process.json` reports `pilot_visible_hidden_info_leaks=1`, `cross_principal_decision_leaks=0`, `outer_failure=null`. The focused record-only AF gate does not adjudicate all source-required hidden/RNG/replay obligations; this leak counter must be separately resolved/adjudicated before AF promotion.

### Root cause for the three Charm gaps

`CODE_DERIVED` against pinned Forge:

- `CharmEffect.makeChoices(sa)` now correctly runs and produces real authoritative `MODE_SELECTION` requests.
- Current qualification policy maps the modeled target SVar to the **ordinal in the raw `Choices$` script** and selects the option at that ordinal.
- Forge `CharmEffect.makePossibleOptions` filters illegal modes before the authoritative request. Therefore raw-script ordinal is not a stable identity after filtering; a preceding filtered mode shifts indices and the pilot can legally choose a different mode.
- This is a qualification pilot reachability defect, not a Dig/Surveil/Charm rules-core failure.

### Exactly next atomic work package

1. Replace raw-ordinal Charm selection with exact desired mode identity. From the actual parsed parent `SpellAbility`, locate exactly one raw `Choices` `AbilitySub` whose API/map matches `CaseSpec.targetDispatch/targetScript`; record desired semantic identity `ability_sub:<id>` for the current path.
2. Call production `CharmEffect.makeChoices(sa)` unchanged. In `MODE_SELECTION`, select the desired semantic identity **only if it is present in Forge's authoritative request options**. If absent or ambiguous, fail closed with `UNSUPPORTED_DECISION_PATH`. Do not synthesize options and do not infer legality outside Forge.
3. Keep card-name independence, no direct target-SVar entry, no direct `sa.resolve()`, no manual target injection.
4. Run the focused 21-path AF gate. Acceptance: `21/21 PASS`, stack admission/resolution `21/21`, target-SVar reachability `21/21`.
5. Persist run/job/artifact/digest and adjudication here before any broader evidence gate.
6. Then close source-required Hidden/RNG/Replay/Decision obligations for the 21 AF paths before promotion.
7. Only after AF closure begin the 32-path / 33-entrypoint non-AF event campaign.

## Non-AF G queue already materialized, not yet qualified

`ws33_prepare_g_svar_event_cases.py` materializes exactly 32 effective paths / 33 source-proven event parents, preserving the true two-parent Kang Prime path and forbidding direct target-SVar entry. Event modes: ChangesZone 12, Phase 6, Attacks 5, DamageDone 4, SpellCast 2, AttackersDeclared 2, DamageDoneOnce 1, Sacrificed 1.

## Subsequent serial queue

Only after G3 reaches `81/81 PASS` with all evidence obligations and an exact frozen successor may serial campaigns proceed `ABC -> D -> E -> F`.

Control expectations only, never source truth until freshly computed:
- post-G3 PASS 366 / UNKNOWN 3822
- post-ABC PASS 1920 / UNKNOWN 2268
- post-D PASS 2840 / UNKNOWN 1348
- post-E PASS 3869 / UNKNOWN 319
- post-F PASS 4188 / UNKNOWN 0
