# WS33 CONTINUATION HANDOFF

## Authority / completion contract

Active branch: `work/ws33-g3-final-closure-20260902`.

The operative WS33 state is artifact-driven. Repository-root WS33 JSON files are tooling/reference inputs and are **not** the current 4188-path operational successor.

`TASK_COMPLETE = NO`

`WS33_COMPLETE = FALSE`

Only the final serial G3 -> ABC -> D -> E -> F successor with all 4188 paths PASS, zero UNKNOWN/FAIL/UNSUPPORTED, A-H UNKNOWN zero, and all replay/hidden/RNG/decision/failure/evidence/hash/lineage gates may change these flags.

## Stable operational predecessor

- effective 4188; PASS 285; UNKNOWN 3903; FAIL 0; UNSUPPORTED 0; G UNKNOWN 81; H UNKNOWN 0.
- Forge pin `8c7e9afb8e6caee88644b94e25da5852e36f8928`.
- model SHA256 `cd48f4279d682ab944e2534bf937d87e5311e83989e97179ae73c5c7d1bb6224`.
- predecessor artifact `9823383539`, digest `sha256:aab73ba2ede151bbd0b803c2164d3067ddd65f17d49cf655c34eef67d903595d`.

Immutable Direct-G behavior: run `33516084949`, HEAD `d8af15cb879bdfc3c40ce4cba3462da24ee3f272`, TREE `857dc01e04f58ca59437e08710bcb194bf030ea4`, artifact `9803814288`, digest `sha256:493f3549b6483d4fea9644f3a0216deb108a9ac581b651ff3e083499bcb14b5a`; Record/Replay 28/28 PASS, semantic replay PASS, stack PASS, hidden/cross-principal leak 0.

Principal Observation v4: run `33552816460`, artifact `9818304005`, 28 paths, hidden-required 24, record/replay observations 1496/1496, unauthorized/private and cross-principal leak delta 0.

G requirement migration: run `33564749471`, artifact `9822685407`, digest `sha256:81e1e24551403453e4dd32e9ed65951cbaca2776cc993eddf475b4214a67a424`; Hidden 74, RNG 21, Replay 57, Decision 50; ABI V2.1 PASS; 17 negatives rejected; verifier PASS.

## G3 items already closed — do not repeat

- principal-scoped DecisionEvent repair/hardening: run `33690697036`, artifact `9870061705`, digest `sha256:21bfde999292f5d3a3d1cc5f27e5236ab352972cedde7b32691ea5ad31fbe0cd` PASS.
- 53-SVar topology: run `33681121017`, artifact `9866293827`, digest `sha256:6a41f66937b4bf1bcf782045d869ece183c0be49b345eac654dc3588cb98b96b` PASS; G81=Direct28+SVar53; unresolved parents 0.
- topology hash-space mismatch fixed; AF parent actual-card binding fixed; target-SVar observer is observation-only; 19-field case ABI aligned.
- compile-scope defect from `33742586083` closed by `3ca8c330287ef1f140b5be9e0c46187c762a7c7b`.
- Kindred Summons ChooseType reachability closed in `33743144684`.
- raw Charm `Choices$` ordinal policy removed by commit `1cff246a32df32788736576b4bd5e21ad73cdfec`; external pilot now chooses the desired opaque `ability_sub:<id>` only by exact membership in Forge's authoritative `MODE_SELECTION` request.

## Current G3 checkpoint — 2026-09-03

`LAST_CONFIRMED_CHECKPOINT = G3_SVAR_AF_CHARM_CLONE_OBSERVER_NORMALIZATION_ROOT_CAUSE`

### Previous AF diagnostic

Run `33743144684`, artifact `9888664547`, digest `sha256:ded468207a7d4b61d95d3a87967a7eb923d083b10b1c45157f7408bd9b2040be`: behavior 21/21 PASS, stack 21/21, target reachability 18/21. Three remaining paths were Ao, Atsushi, Prismari Charm.

### Authoritative Charm-mode identity validation

Behavior-bearing commit:
- HEAD `1cff246a32df32788736576b4bd5e21ad73cdfec`
- TREE `2ac534258f68ef20d5d8843902a488a4fbccfa9d`
- run `33745157361`
- job `100615821377`
- artifact `9889418452`
- digest `sha256:0c2d2a22d1ed931b9738bc7097af5f9f062485665d2e1af2e7476f55dbe39896`
- downloaded ZIP SHA256 exactly matches digest.

Artifact adjudication:
- Maven/Forge behavior execution succeeds; case rows `21/21 PASS`.
- stack admission/resolution `21/21`.
- no `UNSUPPORTED_DECISION_PATH`, no runtime failure, no outer failure.
- target observer reports `18/21`; exactly the same three Charm targets remain at observer count 0.
- therefore authoritative target-mode selection is operational; raw ordinal was eliminated successfully.
- diagnostic remains non-promotable.

Three rows still observer-zero:
1. `forge-behavior-v2:95726bbbfdb31ba1e8fe7146f4a7971d93f97bc5` — Ao — DigEffect.
2. `forge-behavior-v2:a1fe7a20bc3ddb26ed8642a7a8b5025697bd0d83` — Atsushi — DigEffect.
3. `forge-behavior-v2:ee17650cc69e7d571ba8a6d602227eb4c8ba6154` — Prismari Charm — SurveilEffect.

### New root cause

`CODE_DERIVED` from pinned `CharmEffect.chainAbilities`:

- Forge clones each chosen `AbilitySub` before appending it to the resolving parent.
- On the clone, Forge productively adds `StackDescription=SpellDescription` when the chosen mode did not already define `StackDescription`.
- The WS33 observer currently defines target identity as exact API plus exact equality of `AbilityFactory.getMapParams(targetScript)` and the resolving clone's `getMapParams()`.
- Therefore the actual target mode can execute but fail observation solely because of this documented runtime-added presentation parameter.
- This is an observer identity-normalization defect, not a rules/reachability failure.

Diagnostic hidden note remains: the coarse record-only process counter reports one pilot-visible leak on `forge-behavior-v2:17f853...` (`RevealHandEffect`), cross-principal 0. This must be adjudicated by Principal Observation v4 before promotion.

### Exactly next atomic work package

1. Normalize target observer matching only for the documented Charm clone transformation: require API equality and exact target-map equality after removing **only** runtime-added `StackDescription=SpellDescription` when the source target script did not contain `StackDescription` and parent dispatch is Charm.
2. Preserve exact map equality for all non-Charm targets and reject any other extra/missing parameter.
3. Add a static fail-closed regression in the harness generator proving broad subset matching is not used.
4. Rerun focused 21-path AF behavior gate. Acceptance: 21/21 PASS, stack 21/21, target reachability 21/21.
5. Persist run/job/artifact/digest.
6. Then run separate AF request/RNG replay evidence (requirements: Decision 9, RNG 4, Replay 12) and AF Principal Observation v4 (Hidden 19). The focused gate alone is not promotion-complete.

## Non-AF G queue already materialized, not yet qualified

`ws33_prepare_g_svar_event_cases.py`: exactly 32 effective paths / 33 source-proven event parents; true two-parent Kang Prime preserved; direct target-SVar entry forbidden. Modes: ChangesZone12, Phase6, Attacks5, DamageDone4, SpellCast2, AttackersDeclared2, DamageDoneOnce1, Sacrificed1.

## Subsequent serial queue

After G3 reaches 81/81 PASS with all obligations and a frozen successor: ABC -> D -> E -> F. Control expectations only: post-G3 366/3822; post-ABC 1920/2268; post-D 2840/1348; post-E 3869/319; post-F 4188/0.
