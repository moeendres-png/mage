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

Full-reactor CI is owned by the PR #17 Actions runs (master-based vehicle);
whole-reactor `Mage.Verify` ambient drift, if observed there, is classified
`FAIL_AMBIENT_MAGE_VERIFY` per lineage precedent and does not touch the
`Mage Tests` module result that carries RG-06B semantics.
