# WS33 ABC-A1 — run 33999460235 PENDING

Date: 2026-09-06

## Frozen qualification source

- workflow: `WS33 ABC A1 TargetRestrictions fresh closure v2`
- run: `33999460235`
- job: `101395608713`
- source HEAD: `5f81b489541d1638758b201916b8dc9f9544987f`
- source TREE: `6b61eb6662f3348b0a5b1ea3824a0913df487b9c`
- expected artifact: `ws33-abc-a1-targetrestrictions-v2-33999460235`
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- model artifact: `9823383539`
- model artifact digest: `sha256:aab73ba2ede151bbd0b803c2164d3067ddd65f17d49cf655c34eef67d903595d`
- authoritative manifest sha256: `cd48f4279d682ab944e2534bf937d87e5311e83989e97179ae73c5c7d1bb6224`
- consumer model sha256: `82638e6b3e4408cc5bddedc49372b6357d3c2bdce6fba7bfab7ed119678f9a48`

## Repair under qualification

This source composes the previously proven 64-shape materialization layer, the Forge-authoritative dynamic-cardinality layer, and a new systemic runtime-state layer that:

1. executes Forge `SpellAbility.clearTargets()` before target selection so pinned Forge initializes `DividedAsYouChoose` through its production lifecycle;
2. derives `TriggeredDefendingPlayer` / `TriggeredCardController` fixture context from actual ability parameters;
3. derives TriggeredCardController fixture ownership from the real defined-controller context rather than a card-name branch;
4. for A1 target-restriction cases whose target/division parameter depends on `Count$xPaid`, establishes a bounded already-paid `X=1` prerequisite only if Forge `AbilityUtils.getAnnouncementBounds` admits 1, then leaves all target cardinality/legal-option computation to Forge.

This A1 run does **not** claim to requalify CostPayment; its paid-X setup is a target-witness prerequisite and must not be reused as cost evidence.

## Required gates

- exact A1 queue/model binding: `122` unique paths
- exact materialization: `122/122`
- actual pinned-Forge Record execution: `122/122`
- Record diagnostics: empty
- actual Rules-Core target path for every path
- selected response IDs contained in Forge-authoritative option IDs
- no fallback
- no direct effect resolution
- tape-driven Replay: `122/122`
- Replay diagnostics: empty
- semantic divergence: `0`
- exact per-path certification: `122/122`
- immutable evidence hashes verified

`COVERAGE_PROMOTION=FALSE`
`SOURCE_FROZEN=TRUE`
`ABC_A1_COMPLETE=FALSE`
