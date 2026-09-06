# WS33 ABC A-rest Direct31 — run 34044389860 PENDING

Status: `PENDING`

## Frozen run identity

- branch: `work/ws33-g3-final-closure-20260902`
- workflow: `.github/workflows/ws33-abc-a-rest-direct31-runtime.yml`
- source HEAD: `665f40e286b58912db27ba1734c0c9d92f52ae4b`
- source TREE: `06404df91656e8798a1e5cb3e9bdac853ca54e0d`
- run: `34044389860`
- job: `101516725121`
- run attempt: `1`
- topology input run: `34002894410`
- topology artifact: `9980023181`
- topology digest: `sha256:053ca7036eec2e13dd66022975a7f766e9c8c9ebc3cc30576ab03eaab99cb995`
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`

## Qualification scope

Exactly 31 remaining direct A paths from the immutable A-rest topology:

- 24 source-bound spells
- 7 source-bound activated abilities
- 31 Decision-required
- 2 RNG-required
- 31 Hidden-required
- 31 replay-required

The run must execute actual source-bound Forge abilities through `PlaySpellAbility`, Forge target setup/cost/timing/restriction checks, and `MagicStack`; no direct resolve or manual target injection is admissible.

## Run invariants

- `COVERAGE_MUTATED=FALSE`
- `COVERAGE_PROMOTION=FALSE`
- `A_REST_UNKNOWN=57`
- `DIRECT31_RUNTIME_RESULT=PENDING`

The run source is frozen. No repair or promotion may be made against this run until a terminal result and artifact state are persisted.
