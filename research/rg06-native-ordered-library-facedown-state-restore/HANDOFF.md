# RG-06A — Native Ordered-Library and Face-Down State-Load Support

## Final Handoff — 2026-09-25

**Disposition:** `RG06A = ENGINE_REMEDIATED_AND_RUNTIME_VERIFIED`

**Architecture Freeze:** `NOT CLAIMED`

**Production Provider:** `NOT SELECTED`

**WORKTREE:** `NOT_AVAILABLE_IN_CONNECTOR_EXECUTION`

## Source Lock

- Repository: `moeendres-png/mage`
- Exact RG-08 source base: `266b3f41391f33ecf39716fc2d8a083663368f38`
- RG-08 base tree: `efa2436b13cd30398a53890b4c531a454eeac481`
- Workstream branch: `sol/rg06-hidden-state-restore-20260924`
- Runtime-verified source head: `82d886c7a32ff3405cdd79856d2fb55141c9a7db`
- Runtime-verified source tree: `5d49f478b50422c646404c81fadc6ed017a04deb`
- Exact runtime workflow: GitHub Actions run `36082229558`, job `107906528721`
- Draft PR: #16. CI/review vehicle only; DO NOT MERGE TO Mage master from this workstream.
- Branch ancestry at runtime head: 11 commits ahead / 0 behind RG-08, merge base exactly `266b3f41391f33ecf39716fc2d8a083663368f38`.

The final handoff commit is a documentation-only descendant of the runtime-verified head. The terminal branch SHA/tree are recorded in current GitHub branch/PR metadata and in the coordinator handoff.

## Reuse Classification

### Ordered library

`NEW_IMPLEMENTATION_REQUIRED` — bounded engine-native extension.

Existing library operations are gameplay/movement operations (put on top/bottom, draw, search, shuffle). No existing atomic state-load primitive could replace the entire order while proving exact membership, ownership, zone correctness, uniqueness and no synthetic gameplay event. RG-06A therefore adds one narrow API:

`Library.restoreOrderForGameLoad(List<UUID>, Game)`

It accepts only a complete permutation of the cards already in that player's library and validates the entire payload before mutation.

### Face-down state

`ENGINE_NATIVE_REUSE` + narrow `WRAP`.

RG-06A does not implement a second face-down rules model. It adds a state-load entry point that reuses XMage's existing `BecomesFaceDownCreatureEffect`, native Morph/Megamorph/Disguise blueprints, Manifest/Cloak construction, existing turn-face-up abilities, continuous effects and normal zone-change semantics:

`BecomesFaceDownCreatureEffect.restoreFaceDownStateForGameLoad(UUID, FaceDownType, Game)`

## Rules Authority

Current official Magic Comprehensive Rules were rechecked during qualification. Relevant current mechanisms are the rules for face-down permanents (CR 708), Manifest (current CR 701.40), Cloak (current CR 701.58), Morph/Megamorph, and Disguise (current CR 702.168). The official rules require that a manifested/cloaked card with Morph or Disguise can use the applicable alternate turn-face-up procedure.

The current XMage `ManifestEffect` source still documents those mixed Manifest+Morph / Manifest+Disguise turn-up paths as TODO/unsupported and also retains stale historical rule-number comments. RG-06A therefore fails closed for restoring a Manifest/Cloak state onto an underlying card that also needs those unsupported alternate turn-up semantics rather than claiming a partially correct state.

Engine behavior is evidence, not Rules authority.

## Production Changes

Exactly two production files differ from RG-08:

1. `Mage/src/main/java/mage/players/Library.java`
   - adds the narrow ordered-library game-load seam;
   - rejects null game/payload, incomplete membership, duplicate/null/unknown IDs, wrong-zone cards and foreign ownership;
   - validates completely before mutation;
   - does not create/move cards, draw, search, shuffle, reveal or emit synthetic historical events.

2. `Mage/src/main/java/mage/abilities/effects/common/continuous/BecomesFaceDownCreatureEffect.java`
   - adds the narrow existing-permanent face-down game-load seam;
   - requires an existing battlefield card permanent and matching ownership;
   - refuses already-face-down objects, MANUAL state and invalid/native-incompatible requested types;
   - reuses native Morph/Megamorph/Disguise blueprints;
   - constructs Manifest/Cloak using existing XMage face-down machinery;
   - rejects unsupported mixed Manifest/Cloak + Morph/Disguise restore states;
   - performs all validation/construction before live mutation.

No generic snapshot serializer, Lab observation policy, second hidden-information permission model or card-name production special case was added.

## Test Changes

Added:

`Mage.Tests/src/test/java/org/mage/test/serverside/rg06/RG06HiddenStateRestoreTest.java`

The final test class contains 10 runtime-qualified methods:

1. `orderedLibraryRestoreIsExactAndEmitsNoSyntheticEvents`
2. `genuineLaterDrawUsesRestoredTopCard`
3. `genuineLibrarySearchUsesRestoredLibraryAndNormalShuffle`
4. `genuineShuffleOperatesOnRestoredLibraryWithoutChangingMembership`
5. `invalidLibraryRestorePayloadsFailClosedWithoutPartialMutation`
6. `restoredMorphHasNativeCharacteristicsAndTurnsFaceUpNormally`
7. `restoredManifestAndCloakRemainDistinctNativeStates`
8. `restoredDisguiseReusesNativeWardTurnUpAndTriggerBehavior`
9. `faceDownZoneChangeUsesNormalNewObjectSemantics`
10. `invalidFaceDownRestoreFailsBeforeMutation`

## Semantic Gate Results

### Ordered library

PASS.

- Exact full-library top-to-bottom permutation is restored.
- Authoritative top and bottom identities read back correctly.
- Restore produces no draw/shuffle/reveal/zone-change event from the qualification watcher.
- Hand size and authoritative revealed-state size remain unchanged.
- Duplicate, incomplete, null-ID, unknown-ID, wrong-zone, foreign-owner, null-payload and null-game cases fail closed with the original order unchanged.
- A genuine later turn draw consumes the restored top card.
- Actual `Demonic Tutor` finds a restored card through native library search and then invokes the engine's normal shuffle path.
- A genuine native shuffle preserves exact library membership and size.

### Face-down state

PASS for the bounded states currently modeled safely by XMage.

- Restored Morph is a native 2/2 face-down object and turns face up through its normal Sagu Mauler Morph procedure.
- Restore does not alter the authoritative revealed-state set.
- Manifest and Cloak remain distinct native states.
- Cloak retains its native Ward behavior while Manifest does not invent Ward.
- Restored Disguise reuses native Ward and native turn-up behavior; Dog Walker's real turned-face-up trigger creates the expected tokens.
- Cloudshift after restored Manifest uses normal zone-change/new-object semantics; the returned object is face up with old face-down flags cleared.
- Unsupported/incompatible face-down payloads fail before mutation.
- Mixed Manifest/Cloak + underlying Morph/Disguise remains explicitly rejected because current native XMage does not yet fully implement the required alternate turn-up semantics.

## Initial Failure and Remediation

The first RG-06A runtime attempt at `498876eaf8b6fedd9db522d6f7b55c24ae7f3bf3` failed four of nine tests inside `Mage Tests`.

Root causes were qualification fixture/harness defects, not failures of the new production APIs:

1. ordered-library fixtures supplied only three UUIDs while the test player still had a complete normal test library; the production API correctly rejected the incomplete permutation;
2. the custom qualification watcher did not implement native copy semantics required by game-state copying.

The workstream repaired the fixtures to construct full-library permutations, implemented a proper watcher copy, added a genuine search-after-restore case, added explicit no-reveal assertions, made duplicate/incomplete/null-ID cases non-vacuous, and removed harness `UUID.randomUUID()` use in favor of a deterministic absent ID.

No production change was made merely to satisfy those failed fixtures.

## Exact Runtime / Build Evidence

GitHub Actions run: `36082229558`

Job: `107906528721`

Exact tested source:
- HEAD `82d886c7a32ff3405cdd79856d2fb55141c9a7db`
- TREE `5d49f478b50422c646404c81fadc6ed017a04deb`

The branch inherits the qualification workflow's exact-PR-head checkout binding:

`ref: ${{ github.event.pull_request.head.sha || github.sha }}`

The repository command executed:

`mvn test -B -Dxmage.dataCollectors.printGameLogs=false -Dlog4j.configuration=file:${GITHUB_WORKSPACE}/.travis/log4j.properties`

`Mage Tests 1.4.61`:
- tests run: **6929**
- failures: **0**
- errors: **0**
- skipped: **125**
- module result: **SUCCESS**

All 10 RG-06A methods were individually reported `[OK]`.

The same cumulative run also re-executed the inherited RG-02 Commander-damage classes, RG-07 Hex class, RG-08 replacement class and WS83/WS85 replacement/future-state classes.

### Whole-Reactor Result

The top-level reactor is still not globally green:

`FULL_MAVEN_REACTOR = FAIL_AMBIENT_MAGE_VERIFY`

After successful `Mage Tests`, the independent `Mage Verify 1.4.61` module fails with:
- `test_verifyCards`: 15 current card-data subtype mismatches in 91,085 verified cards;
- `test_checkMissingSetData`: one missing set implementation, `SLZ - The Zeta Set`.

These are outside all RG-06A changed files and reproduce the same ambient repository-maintenance class already retained by M1-M3. They are not relabeled as green CI.

## Evidence Classification

- M3 -> M4 ancestry and changed-file boundary: `DIRECTLY_VERIFIED`
- Exact runtime checkout/head/tree and Actions result: `DIRECTLY_VERIFIED`
- 10 RG-06A runtime tests: `DIRECTLY_VERIFIED` + `TECHNICALLY_CONFORMANT`
- Ordered-library implementation atomicity: `CODE_DERIVED` + runtime negative tests
- No synthetic restore events / no revealed-state mutation: `DIRECTLY_VERIFIED`
- No immediate restore-path game-log disclosure: `CODE_DERIVED`; native `PermanentImpl.setFaceDown` only changes the internal flag and the new restore methods contain no player log operation
- Wolfram finite permutation check: `MODELED`, supplemental only
- Current face-down semantics checked against official CR: `EXTERNALLY_RULE_VALIDATED`
- Mixed Manifest/Cloak + Morph/Disguise restore support: deliberately unsupported/fail-closed, not PASS

## PASS / FAIL / UNKNOWN

### PASS

`RG06A_ORDERED_LIBRARY_STATE_LOAD = PASS`

`RG06A_BOUNDED_FACE_DOWN_STATE_LOAD = PASS`

`RG06A = ENGINE_REMEDIATED_AND_RUNTIME_VERIFIED`

### FAIL

`FULL_MAVEN_REACTOR = FAIL_AMBIENT_MAGE_VERIFY`

This is not an RG-06A semantic failure.

### UNKNOWN / Unsupported

Full restoration of an underlying Morph/Megamorph/Disguise card specifically in a Manifested/Cloaked state remains unsupported because the existing native engine does not yet implement all alternate turn-up semantics required for that mixed state. The new API rejects it before mutation.

No required bounded RG-06A test cell remains UNKNOWN.

## Production Engine Semantics Changed

`YES — NARROW STATE-LOAD API SURFACE ONLY`

Ordinary gameplay draw/search/shuffle, Morph/Disguise/Manifest/Cloak resolution, hidden-information projection, Rules RNG and zone-change semantics were not replaced. RG-06A adds only engine-native load seams used to establish authoritative state and then hands subsequent play back to normal XMage procedures.

## Cross-Workstream Impact

- **Commander damage:** no RG-02 production surface changed; inherited RG-02 tests re-executed inside the successful 6929-test Mage Tests run.
- **Exact-N target offering:** no target/legal-action production surface changed; inherited RG-07 tests re-executed.
- **Replacement effects:** no replacement engine production surface changed; inherited RG-08 plus WS83/WS85 classes re-executed.
- **Hidden state:** two bounded authoritative Mage state-load APIs added; no Lab/redaction policy added.
- **RNG:** restoration itself consumes no Rules RNG. Genuine post-restore shuffle uses the existing native engine RNG path. No harness-side Rules RNG was introduced.
- **Replay:** replay/qualification can now bind exact full library order and bounded face-down state without fabricating historical draw/shuffle/reveal events.
- **Multiplayer:** no player-count branch or fixed-size assumption was added. APIs are player/object scoped; the cumulative suite includes inherited RG-02 3P/4P/5P Commander cases.

## New Findings

1. The initial library failures validated the API's fail-closed full-permutation contract rather than demonstrating an engine defect.
2. Native game-state copying requires qualification watchers to implement valid copy semantics; this was a harness defect and was corrected.
3. The existing Manifest implementation still contains explicit TODOs for Manifest+Morph/Disguise alternate turn-up semantics and stale historical CR numbering.
4. The safe closure boundary is therefore exact ordered-library restoration plus native single face-down state types, with mixed unsupported states rejected.
5. Principal-scoped observation/redaction remains a separate Commander Lab concern; the Mage API does not introduce such policy.
6. There is no `PIN_MATERIALIZATION_MISMATCH` on the cumulative residual lineage.

## Remaining Blockers

None for the bounded RG-06A objective.

The mixed Manifest/Cloak + Morph/Disguise engine capability remains a separately identifiable native Rules gap if future qualification requires loading that exact mixed state. The ambient Mage.Verify card-data drift also remains separate repository maintenance.

## Dependencies Unblocked

- The Mage residual closure campaign M1 -> M2 -> M3 -> M4 is cumulatively runtime-qualified on one direct descendant lineage.
- A later Commander Lab repin/integration workstream may consume **only the terminal residual candidate head** recorded by the coordinator after this docs-only handoff commit.
- The later Lab workstream must still perform pin/contract/bridge/evidence impact adjudication and its own required requalification.
- No Mage master merge is authorized by this handoff.

## Exact Next Action

Coordinator records the docs-only terminal branch HEAD as `MAGE_RESIDUAL_CANDIDATE_HEAD`.

Then a separate Commander Lab repin workstream may consume that exact commit, update only the authoritative pin/integration surfaces, and requalify impacted Lab runtime/evidence. Do not merge this Mage branch to master as part of RG-06A.
