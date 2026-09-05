# WS33 ABC-A1 TargetRestrictions v2 — terminal failure checkpoint

Date: 2026-09-05

## Transaction identity

- workflow source SHA: `e0b21d90bc7fae5c40780b448a017e361c4c52e0`
- workflow source tree: `921e1ac6d6303ccf87c1795203763dc5474db781`
- run: `33938471426`
- job: `101230974216`
- terminal conclusion: `failure`
- artifact: `9961000389`
- artifact digest: `sha256:cf00923211a5c78f1f5c8c3e83ba85bd2800996a1ccf7cd23479ac82cc4510bc`

## Passed boundaries

- immutable authoritative model artifact/digest: PASS
- 4188 model / exact 122 A1 UNKNOWN queue binding: PASS
- exact Forge / WS01 / WS12 / WS32 pins: PASS
- retained Decision, Hidden, RNG, stack-target and failure-semantics overlays: PASS
- generic five-selector fixture extension: PASS
- rules mutation by fixture extension: FALSE
- card-name production branches added: 0

The target preparer increased from the previous 306 cases to 318 and now included the first five omitted selector families (`Villain.YouCtrl`, `Creature.withHaste`, `Creature.attacking`, `Creature.attacking,Creature.blocking`, `Creature.powerGE4,Artifact,Enchantment`).

## Terminal failure boundary

The exact 122-ID A1 filter then failed closed on a second set of five not-yet-materialized paths:

- `forge-behavior-v2:12c6c4325fb92fcd0f5d2bbe07c2679152c89f9c`
- `forge-behavior-v2:16ac36d0e2b4715a787864d587400f91e314e801`
- `forge-behavior-v2:2085b827a5d49d535a3d2b5ca17d4cc9c66c25c0`
- `forge-behavior-v2:236471fd27480662959ef51e07f1fb84c21f4795`
- `forge-behavior-v2:27cf9487a495125599341a3c8b3d6a0f6aaa29ce`

Record, tape-driven Replay and per-path certification were skipped. No behavior PASS was produced.

## Classification

- run/artifact facts: `DIRECTLY_VERIFIED`
- first five-selector repair: `CODE_DERIVED` and mechanically executed successfully
- second omission set root cause: `UNKNOWN` pending exact manifest/source adjudication
- Forge Rules Core defect: `NOT ESTABLISHED`
- coverage promotion: `FALSE`

## Frontier invariant

- TOTAL=4188
- PASS=366
- UNKNOWN=3822
- FAIL=0
- UNSUPPORTED=0
- ABC_UNKNOWN=1554
- WS33_COMPLETE=FALSE

`ABC_A1_RUN_33938471426=FAIL_CLOSED`
`ABC_A1_COVERAGE_PROMOTION=FALSE`
