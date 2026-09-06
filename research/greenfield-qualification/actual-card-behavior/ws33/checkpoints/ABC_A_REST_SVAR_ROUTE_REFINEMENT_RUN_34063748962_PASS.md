# WS33 ABC — A-rest SVar production-root route refinement — PASS

Status: PASS
Evidence class: DIRECTLY_VERIFIED + CODE_DERIVED
Coverage promotion: FALSE

## Frozen source

- source HEAD: `48cb9a018f606f1209d14ee587a6ff3f14d263a1`
- source TREE: `cc719e021ba4e1319ce10eb157c976f1df0226c9`
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- run: `34063748962`
- job: `101568792257`

## Immutable artifact

- artifact ID: `9998291348`
- artifact name: `ws33-abc-a-rest-svar-routes-34063748962`
- GitHub digest: `sha256:646594434eb987009561127f012bd0d974dcec97e67bef0bf478294f1fd9d0e9`
- independently computed ZIP sha256: `646594434eb987009561127f012bd0d974dcec97e67bef0bf478294f1fd9d0e9`
- every entry listed by artifact `SHA256SUMS`: PASS

## Verified route gate

`A_REST_SVAR_EXECUTION_ROUTE_GATE.json` was independently read from the downloaded artifact and proves:

- status: PASS
- effective paths: 26
- AF direct-root effective paths: 8
- nested-trigger effective paths: 1
- nested-trigger production parent entrypoints: 2
- nested-trigger modes: `ChangesZone`, `Attacks`
- direct-trigger effective paths: 17
- direct-trigger parent entrypoints: 17
- total runtime parent entrypoints: 27
- effective-path overlap: 0
- runtime-root refinement performed: true
- Magic legality inference: false
- coverage mutated: false
- coverage promotion: false

The nested route is the Avengers Quinjet path `forge-behavior-v2:998c818f96396b9d032dd327a137c613226e93d9`; its exact card source exposes two real trigger roots, both consuming `TrigCharm`, whose selected target mode is `DBReturn`. This path is therefore not qualified by standalone `DB$ Charm` execution.

## Scope

This PASS qualifies only the source-derived production-root routing partition. It does not qualify behavior execution, hidden-information semantics, RNG, replay, or coverage for the 26 effective paths.

`COVERAGE_PROMOTION=FALSE`
