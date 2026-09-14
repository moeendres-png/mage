# WS212 Source Lock

- Repository: `moeendres-png/mage`
- Branch: `ws212/xmage-rules-rng-seed-authority-20260914`
- Audit base (WS211 terminal, immutable): `2b3f0f767b69192f90a921a9ece40abb0b8149d0`
- Audit-base tree: `38a1bcada4d694959fce68bcd4908fa07e7702c9`
- WS211 source branch (no mutation in WS212).
- Read-only root-cause reference (Commander-Lab WS208):
  commit `086589721dea69c38069ab5223e39a4b602bfcad`,
  tree `e1a1c096bf725867c68e735e50e31ffeb8412348`
  (declared `FOUNDRY_REFERENCE_ROOTS`, never written).
- `ARCHITECTURE_FREEZE = NOT_CLAIMED`
- `PRODUCTION_PROVIDER = NOT_SELECTED`

Verification (this worktree, before material edits):

- `git rev-parse HEAD` = `2b3f0f767b69192f90a921a9ece40abb0b8149d0`
- `git rev-parse HEAD^{tree}` = `38a1bcada4d694959fce68bcd4908fa07e7702c9`
- `git status --short` = clean.
