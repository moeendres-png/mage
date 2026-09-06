# WS33 ABC A-rest Direct31 — run 34044823779 PENDING

Status: `PENDING`

## Frozen run identity

- branch: `work/ws33-g3-final-closure-20260902`
- workflow: `.github/workflows/ws33-abc-a-rest-direct31-runtime.yml`
- source HEAD: `ccfabf7517334f5ee166e5f80f76971e44603818`
- source TREE: `0d5c1ab6b130143b20d44218dcc1a5e13ed06584`
- run: `34044823779`
- job: `101517903398`
- run attempt: `1`
- topology input run: `34002894410`
- topology artifact: `9980023181`
- topology digest: `sha256:053ca7036eec2e13dd66022975a7f766e9c8c9ebc3cc30576ab03eaab99cb995`
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`

## Repair relative to failed run 34044389860

The only intended repair is the inherited evidence-only `CaseSpec.implementation` ABI:

- repair tool: `ws33_repair_a_rest_direct_case_abi.py`
- implementation evidence value: `forge.game.spellability.TargetRestrictions`
- rules mutation: `0`
- target/cost/decision/RNG/stack semantics: unchanged

## Qualification scope and invariants

Exactly 31 remaining direct A paths: 24 spells, 7 activated abilities, all Decision+Hidden+Replay, with 2 RNG-required.

- `COVERAGE_MUTATED=FALSE`
- `COVERAGE_PROMOTION=FALSE`
- `A_REST_UNKNOWN=57`
- `DIRECT31_RUNTIME_RESULT=PENDING`

The run source is frozen. No repair or coverage promotion may occur until its terminal run/artifact state is persisted.
