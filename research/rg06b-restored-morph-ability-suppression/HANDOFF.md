# RG-06B — Final Handoff — 2026-09-26

**Disposition:** `RG06B = PREMISE_FALSIFIED_NO_ENGINE_CHANGE`
(terminal; test-hardened, fully evidenced, nothing fabricated)

**Architecture Freeze:** `NOT CLAIMED`

**Production Provider:** `NOT SELECTED`

## Source Lock

- Repository: `moeendres-png/mage`
- Base: `b19596980f2734496ea1896504253e1bdd2756dd` (direct ancestor, verified
  via merge-base; no master/upstream merge in this branch).
- Branch: `sol/rg06b-restored-morph-ability-suppression-20260926`
- Runtime-tested implementation HEAD: `2d4ae7496d`
  (tree `85faeb9a`); docs persisted at `f51d8aef00` (tree `20129bac`).
  Terminal HEAD/TREE (this handoff commit): recorded by coordinator from
  branch metadata after push; documentation-only descendant.
- Production delta vs base: EMPTY (`git diff base..HEAD -- Mage/src/main`
  is zero bytes).
- Draft PR #17: retarget base `master` → `sol/rg06-hidden-state-restore-20260924`
  after push; stays Draft; DO NOT MERGE (to master or elsewhere).

## Pre-Fix Reproducer

Coordinator checkpoint accepted: tip-RED was fixture-invalid
(`Permanent not found`, name lookup post-rename), not semantic. Repaired to
native-UUID observation with all 8 non-vacuity gates (existence, face-down,
morphed, 2/2, placeholder name, authoritative `getPlayable` scan,
no-harness-identity-leak, semantic-specificity). Outcome on UNMODIFIED
baseline: GREEN — the specified leak does not reproduce pre-start (duel),
post-start (duel), or post-start+revalidate (commander 4P, both hidden
flags). Full record: PRE_FIX_REPRODUCER.md.

## Root Cause

No engine divergence exists. `makeFaceDownObject` removal is ID-based
(`AbilitiesImpl.contains` compares `getId()`/`getOriginalId()`; copies
preserve IDs), so own face-up abilities are stripped while genuinely gained
ones are kept — exactly the Rules shape (CR 707). Restored and natural morphs
converge (2/2, placeholder, morphed, 3 abilities, silent playable surface,
normal turn-up). The vacuous RED is explained (post-rename name lookup).
Probable Lab-side artifact noted for Lab re-pin follow-up (label-substring
offer matching without source binding, or refused-restore face-up offer
misread). Full trace: ROOT_CAUSE.md.

## Work Completed

1. Repaired the reproducer to non-vacuous, ID-bound form (no production touch).
2. Added natural-morph negative control + genuine turn-up positive control.
3. Added hidden-info negatives (revealed-zero, no identity-naming offers).
4. Diagnosed via throwaway scratch probes (removed): pre/post ability dumps,
   `contains()` semantics, commander-game + revalidate variant.
5. Ran full matrix (§TEST_MATRIX): 13/13 RG-06A class, 72+3 face-down engine,
   29/29 lineage (RG-02/07/08).
6. Persisted 9 research docs; no historical evidence rewritten.

## Production Changes

NONE.

## Test Changes

`Mage.Tests/.../rg06/RG06HiddenStateRestoreTest.java` only (+159 lines):
fixture repair, 2 new tests, hidden-info negatives. No production file, no
card implementation, no harness semantics changed.

## Runtime Evidence

- `RG06HiddenStateRestoreTest`: 13/13 PASS (10 inherited + 3 new).
- `MorphTest,MegamorphTest,ManifestTest`: 72/72; `DisguiseTest`: 3/3.
- RG-02 (13) + RG-07 (9) + RG-08 (7): 29/29 PASS.
- All on exact baseline production bytes; `Mage Tests` module result SUCCESS.
- Whole-reactor `Mage.Verify` ambient drift (if any on PR CI) is
  `FAIL_AMBIENT_MAGE_VERIFY` per precedent, not an RG-06B failure.

## Hidden-Information Evidence

Revealed-size-zero + no identity-naming offers while face-down (restored
test); RG-06A no-reveal regression green; no test harness prints hidden
identity (scratch probes removed; surefire output contains no card names
beyond public Akroma setup).

## Regression Evidence

See TEST_MATRIX.md + IMPACT_ADJUDICATION.md (no-impact proof by empty
production delta).

## PASS / FAIL / UNKNOWN

- Specified-defect PASS: NOT CLAIMED (no RED obtainable — engine correct).
- `RG06B_SUPPRESSION_CORRECTNESS`: PASS (restored/natural/turn-up/hidden-info
  matrix green on baseline).
- `FULL_MAVEN_REACTOR`: determined by PR #17 CI; ambient Verify drift, if
  any, classified separately.
- No required RG-06B cell remains UNKNOWN except the Lab-side provenance of
  the original "3/2 pump" observation (EXTERNAL to this stream; follow-up
  below). No PARTIAL passed as FULL.

## RG06B_MAGE_CANDIDATE_HEAD / TREE

No new engine candidate is minted: production bytes are identical to
`b1959698...`, so the standing residual candidate REMAINS authoritative.
For reference, the fully-tested branch tip is documented above; a later Lab
re-pin needs NO engine repin from RG-06B.

- `RG06B_MAGE_CANDIDATE_HEAD = b19596980f2734496ea1896504253e1bdd2756dd`
  (unchanged; reaffirmed)
- `RG06B_MAGE_CANDIDATE_TREE = 04c00f25bb456227b3c6d2996357b6d6d794a956`
  (tree of `b1959698...`, unchanged; reaffirmed)

## Remaining Blockers

None inside RG-06B. Follow-ups (other surfaces):
1. Lab re-pin workstream: re-examine original "3/2 pump" observation as
   harness artifact; adjudicate removal of the now-proven-unnecessary Lab
   `ACTIVATED_ABILITY_PRESENT` guard (relaxes morph restores of
   ability-bearing cards); do NOT touch Lab from this stream.
2. PR #17 retarget + CI observation (mechanical, below).

## Dependencies Unblocked

- B1 (RG-closure handoff) is CLOSED (as non-defect with proof); no engine
  repin required before Lab consumption of hidden-state seams.
- Lab may proceed to consume `b1959698...` for library/face-down features
  with the guard question now evidence-backed.

## Exact Next Action

Push this branch, retarget PR #17 base to
`sol/rg06-hidden-state-restore-20260924` (keep Draft), observe CI, then hand
to coordinator. No merge to master. No Architecture/Provider claims change.
