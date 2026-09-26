# RG-06B — Validation (exact source binding)

Validation commands (all from the branch worktree):

- `mvn test -B -pl Mage.Tests
  -Dtest='RG06HiddenStateRestoreTest'
  -Dsurefire.failIfNoSpecifiedTests=false
  -Dxmage.dataCollectors.printGameLogs=false`
  → 13/13 PASS (10 inherited RG-06A + 3 RG-06B).
- Face-down suites `MorphTest,MegamorphTest,ManifestTest` → 72/72 PASS;
  `DisguiseTest` → 3/3 PASS.
- Lineage suites (RG-02 ×3 classes, RG-07, RG-08) → 29/29 PASS.
- `git diff b1959698...HEAD -- Mage/src/main` → empty (no production change).
- `git merge-base HEAD b1959698...` → `b1959698...` (direct descendant).

Full-reactor CI observed on terminal HEAD `d87f0f4005` (PR #17, run
36225815241, retargeted base): `Mage Tests 1.4.61 SUCCESS` — 6932 run,
0 failures, 0 errors, 125 skipped — including all three RG-06B tests
individually `[OK]` (`restoredMorphDoesNotOfferFaceUpActivatedAbility`,
`naturalMorphDoesNotOfferFaceUpActivatedAbility`,
`restoredMorphTurnFaceUpRestoresAbilityNormally`).
`Mage Verify 1.4.61 FAILURE` is solely the ambient card-data drift
(`test_verifyCards`: 15 subtype errors in 91,085 cards;
`test_checkMissingSetData`: 1 missing set) — classified
`FAIL_AMBIENT_MAGE_VERIFY` per M1–M4 precedent; it does not touch the
`Mage Tests` module result that carries RG-06B semantics.
