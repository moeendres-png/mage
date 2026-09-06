# WS33 ABC — A-rest SVar production-root route refinement — recovered PENDING checkpoint

Status: PENDING_RECOVERED

This checkpoint reconstructs the required run-registration checkpoint after the prior worker was technically interrupted immediately after run registration. No qualification PASS is asserted here. The source remained frozen from registration through this recovery.

## Frozen source

- repository: `moeendres-png/mage`
- branch: `work/ws33-g3-final-closure-20260902`
- source HEAD: `48cb9a018f606f1209d14ee587a6ff3f14d263a1`
- source TREE: `cc719e021ba4e1319ce10eb157c976f1df0226c9`
- workflow: `.github/workflows/ws33-abc-a-rest-svar-route-refinement.yml`
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`

## Run identity

- run: `34063748962`
- job: `101568792257`
- expected artifact: `ws33-abc-a-rest-svar-routes-34063748962`
- immutable predecessor case artifact: `9996808331`
- predecessor digest: `sha256:ea34615a1ee8735b9f97fd1ee3e6e9ff2fa925569792339a90b15fd4f03e99ec`
- predecessor source HEAD: `6dc8a3fb37f91026fb8b75a9614d528f4b88996d`

## Expected gate

The run is allowed to prove only the already-derived execution-route refinement for the existing 26 A-rest SVar effective paths:

- AF direct production-root effective paths: 8
- nested-trigger effective paths: 1
- nested-trigger production parent entrypoints: 2
- direct-trigger effective paths: 17
- total production runtime parent entrypoints: 27
- effective-path overlap: 0
- Magic legality inference: FALSE
- coverage mutation: FALSE
- coverage promotion: FALSE

`COVERAGE_PROMOTION=FALSE`

At the time of recovery the GitHub job had already reached terminal success, but that fact is intentionally not adjudicated by this checkpoint. Artifact/digest/internal-hash verification and PASS/FAIL classification must occur in a separate terminal checkpoint.
