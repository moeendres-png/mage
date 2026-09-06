# WS33 ABC A-REST TOPOLOGY RUN 34002894410 — PASS

Date: 2026-09-06

Evidence classification: workflow/run/artifact tuple `DIRECTLY_VERIFIED`; topology reconciliation `TECHNICALLY_CONFORMANT` from source-proven pinned-Forge inputs.

## Frozen source and run

- source HEAD `60fa4ff1b224ede4983087a9c28bb6bbc89c728c`
- source TREE `88f5d5460f10364a20d03e8c37854a7793eb00c0`
- run `34002894410`
- job `101404821057`
- conclusion `SUCCESS`
- artifact `9980023181`
- artifact digest `sha256:053ca7036eec2e13dd66022975a7f766e9c8c9ebc3cc30576ab03eaab99cb995`
- exact Forge pin `8c7e9afb8e6caee88644b94e25da5852e36f8928`

## Independently verified artifact

Downloaded artifact ZIP SHA256 equals GitHub digest exactly.
All 7 entries in `SHA256SUMS` verify.
`A_REST_TOPOLOGY.json` reports:

- `status=PASS`
- `a_rest_path_count=57`
- `direct_ability_path_count=31`
- `svar_path_count=26`
- `svar_parent_entrypoint_count=26`
- `unresolved_svar_paths=[]`
- `coverage_mutated=false`

Source-proven selected SVar parent shapes:

- `TRIGGER:Execute:NON_AF` = 17
- `ABILITY:Choices:AF` = 7
- `SVAR:Choices:AF` = 1
- `ABILITY:SubAbility:AF` = 1

There are no multi-parent A-rest SVar paths and no ambiguous selected parent set.

## Adjudication

This closes only the provenance/topology prerequisite for A57. It does not qualify behavior and does not promote coverage.

The expensive behavior qualification must now execute:

1. the 31 direct source-bound abilities/spells through Forge-owned target setup and, where applicable, `PlaySpellAbility`/`CostPayment`;
2. the 26 SVar paths through the exact selected source parent entrypoint, never by entering the target SVar directly;
3. required Decision/Hidden/RNG evidence plus fresh tape-driven Replay;
4. exact 57-path union certification before any coverage promotion.

`RUN_STATUS = PASS`
`A_REST_TOPOLOGY_COMPLETE = TRUE`
`A_REST_BEHAVIOR_COMPLETE = FALSE`
`COVERAGE_PROMOTION = FALSE`
