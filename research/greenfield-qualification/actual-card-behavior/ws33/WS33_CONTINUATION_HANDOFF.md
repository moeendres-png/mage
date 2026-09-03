# WS33 CONTINUATION HANDOFF

## Completion contract

Active branch: `work/ws33-g3-final-closure-20260902`.

The operative WS33 state is artifact-driven. Repository-root WS33 JSON files are tooling/reference inputs, not the current 4188-path successor.

`TASK_COMPLETE = NO`

`WS33_COMPLETE = FALSE`

Only the final serial `G3 -> ABC -> D -> E -> F` successor with all 4188 effective paths PASS, zero UNKNOWN/FAIL/UNSUPPORTED, A-H UNKNOWN zero, exact pin/model/lineage, and all semantic-replay/hidden/RNG/decision/failure/evidence/hash gates may change these flags.

## Stable operational predecessor

- effective `4188`; PASS `285`; UNKNOWN `3903`; FAIL `0`; UNSUPPORTED `0`; G UNKNOWN `81`; H UNKNOWN `0`.
- Forge pin `8c7e9afb8e6caee88644b94e25da5852e36f8928`.
- model SHA256 `cd48f4279d682ab944e2534bf937d87e5311e83989e97179ae73c5c7d1bb6224`.
- predecessor artifact `9823383539`, digest `sha256:aab73ba2ede151bbd0b803c2164d3067ddd65f17d49cf655c34eef67d903595d`.

## Immutable Direct-G evidence — do not rerun for reassurance

Behavior: run `33516084949`, HEAD `d8af15cb879bdfc3c40ce4cba3462da24ee3f272`, TREE `857dc01e04f58ca59437e08710bcb194bf030ea4`, artifact `9803814288`, digest `sha256:493f3549b6483d4fea9644f3a0216deb108a9ac581b651ff3e083499bcb14b5a`; Record/Replay `28/28 PASS`, semantic replay PASS, stack PASS, hidden/cross-principal leak 0.

Principal Observation v4: run `33552816460`, artifact `9818304005`; 28 paths, hidden-required 24, record/replay observations 1496/1496, unauthorized/private leak delta 0, cross-principal leak delta 0.

G requirement migration: run `33564749471`, artifact `9822685407`, digest `sha256:81e1e24551403453e4dd32e9ed65951cbaca2776cc993eddf475b4214a67a424`; G requirements Hidden 74, RNG 21, Replay 57, Decision 50; ABI V2.1 PASS; 17 negative fixtures rejected; verifier PASS.

## G3 work already closed — do not repeat

- principal-scoped DecisionEvent repair/hardening: run `33690697036`, artifact `9870061705`, digest `sha256:21bfde999292f5d3a3d1cc5f27e5236ab352972cedde7b32691ea5ad31fbe0cd` PASS.
- 53-SVar topology: run `33681121017`, artifact `9866293827`, digest `sha256:6a41f66937b4bf1bcf782045d869ece183c0be49b345eac654dc3588cb98b96b` PASS; `G81 = Direct28 + SVar53`; unresolved parents 0.
- topology hash-space mismatch fixed; AF parent actual-card binding fixed; 19-field AF case ABI aligned; target-SVar observer is observation-only.
- compile-scope defect from run `33742586083` closed by commit `3ca8c330287ef1f140b5be9e0c46187c762a7c7b`.
- Kindred Summons generic ChooseType reachability closed in run `33743144684`.
- raw Charm Choices ordinal selection removed by commit `1cff246a32df32788736576b4bd5e21ad73cdfec`; desired mode is chosen only by exact membership of opaque `ability_sub:<id>` in Forge's authoritative `MODE_SELECTION` set.
- Charm clone observation normalized narrowly by commit `28f4e7cdd6a35c488d4633cf8d77163a8aa2d5d9`; only Forge's documented runtime-added `StackDescription=SpellDescription` is ignored, broad subset matching is statically forbidden.

## Current checkpoint — AF behavior fully green

`LAST_CONFIRMED_CHECKPOINT = G3_SVAR_AF_BEHAVIOR_21_OF_21_VERIFIED`

Behavior-bearing commit:
- HEAD `28f4e7cdd6a35c488d4633cf8d77163a8aa2d5d9`
- TREE `fa5cb7385b2724433cf877b11e890985adef2376`

Focused behavior evidence:
- run `33745809012`
- job `100617880661`
- artifact `9889684290`
- digest `sha256:7a9b8a4e8dd993d419d55fa31763ef8d49ffc3927408bfdb4488724dd16d68e9`
- downloaded ZIP SHA256 exactly equals artifact digest.
- workflow/job: SUCCESS.
- case-summary rows: `21/21`, each 21 fields.
- behavior status: `21/21 PASS`.
- stack admission: `21/21`.
- stack resolution: `21/21`.
- exact target-SVar reachability: `21/21` (minimum executions per path 1; zero-count paths 0; total target executions 25).
- outer failure: null; game completed true.
- this closes the focused AF source-parent behavior/reachability package.

This is **not yet AF promotion-complete**. The record-only process counter still reports `pilot_visible_hidden_info_leaks=1`, cross-principal decision leaks 0. That coarse counter must not be waived; the source-required principal-observation evidence must adjudicate it.

AF requirement cardinalities from the frozen cases:
- paths `21`
- Hidden required `19`
- RNG required `4`
- Replay required `12`
- Decision required `9`

## Exactly next atomic packages

1. Build/run an AF ABI request/RNG/tape-driven replay gate by reusing the existing Direct-G request instrumentation/adjudicator and the now-green AF harness/cases. Bind to exact behavior HEAD `28f4e7...` and immutable AF behavior artifact `9889684290`. Expected: paths 21, Decision 9, RNG 4; required replay paths 12 must have deterministic record/replay evidence. No coverage mutation.
2. Persist run/job/artifact/digest and adjudication before modifying Principal Observation tooling.
3. Parameterize the existing Principal Observation base adjudicator from hardcoded 28 to `--expected-paths` with default 28, and generalize the observation instrumenter to recognize the AF attribution anchor `currentPath.set(spec.pathId);prepareSourceParentChoices(spec,sa);bindTargets(sa);` in addition to the unchanged Direct-G anchor, fail-closed if neither/ambiguous.
4. Build/run AF Principal Observation v4 for 21 paths / Hidden-required 19. The coarse RevealHand leak is acceptable only if v4 proves correct entitled-principal visibility and zero unauthorized/private/cross-principal leakage.
5. Only after both evidence packages PASS may the 21 AF SVar paths be considered qualification-complete.
6. Then qualify the 32 non-AF G SVar paths through 33 real source-proven event parent entrypoints; preserve the true two-parent Kang Prime path and prohibit direct target-SVar/trigger entry.

## Non-AF G queue already materialized, not yet qualified

`ws33_prepare_g_svar_event_cases.py`: exactly 32 effective paths / 33 source-proven event parents; modes ChangesZone12, Phase6, Attacks5, DamageDone4, SpellCast2, AttackersDeclared2, DamageDoneOnce1, Sacrificed1; direct target-SVar entry false.

## Serial queue after G3

Only after G3 reaches `81/81 PASS` with all evidence obligations and an exact frozen successor: `ABC -> D -> E -> F`.

Control expectations only until freshly computed from each successor: post-G3 PASS366/UNKNOWN3822; post-ABC 1920/2268; post-D 2840/1348; post-E 3869/319; post-F 4188/0.
