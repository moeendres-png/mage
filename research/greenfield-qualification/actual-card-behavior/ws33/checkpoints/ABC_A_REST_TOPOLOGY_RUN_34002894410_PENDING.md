# WS33 ABC A-REST TOPOLOGY RUN 34002894410 — PENDING

Date: 2026-09-06

Evidence classification: `DIRECTLY_VERIFIED` GitHub Actions registration.

## Frozen source

- source HEAD `60fa4ff1b224ede4983087a9c28bb6bbc89c728c`
- source TREE `88f5d5460f10364a20d03e8c37854a7793eb00c0`
- workflow `.github/workflows/ws33-abc-a-rest-topology.yml`
- run `34002894410`
- job `101404821057`
- Forge pin `8c7e9afb8e6caee88644b94e25da5852e36f8928`

## Immutable predecessor

- artifact `9979204198`
- digest `sha256:ae75ff01604f9fcc2b2cd2320e4cec1470347bcd47665d1989c1541542e76af0`
- predecessor source HEAD `1df1db4876efeebe737aa30bda8b5f6634d2365d`
- predecessor source TREE `f99102c4a96905e9d43b8dca7ab9808d71e3250e`
- coverage `PASS=488 UNKNOWN=3700 FAIL=0 UNSUPPORTED=0`

## Purpose

Materialize the complete source-proven topology for exactly the remaining A57 TargetRestrictions paths before any expensive behavior qualification. This run is provenance/topology only; it may not mutate or promote coverage.

Expected gates:

- immutable predecessor ZIP digest verified;
- predecessor internal WS33 hashes verified;
- exact A57 integrated queue union = `53 + 2 + 2 = 57`;
- exact effective manifest SHA256 `cd48f4279d682ab944e2534bf937d87e5311e83989e97179ae73c5c7d1bb6224`;
- exact consumer-model SHA256 `82638e6b3e4408cc5bddedc49372b6357d3c2bdce6fba7bfab7ed119678f9a48`;
- exact Forge pin;
- `direct_ability_path_count=31`;
- `svar_path_count=26`;
- every SVar path has one or more source-proven selected parent entrypoints and no ambiguous/unresolved parent;
- output hashes emitted;
- `coverage_mutated=false`;
- `coverage_promotion=false`.

Expected artifact: `ws33-abc-a-rest-topology-34002894410`.

`RUN_STATUS = PENDING`
`COVERAGE_PROMOTION = FALSE`
`SOURCE_FROZEN = TRUE`
