# WS33 ABC — A-rest Direct31 runtime v4 — terminal FAIL

Status: **FAIL_CLOSED**
Evidence classification: **DIRECTLY_VERIFIED runtime + artifact; root-cause classification pending source adjudication**
Coverage promotion: **FALSE**
Coverage mutated during witness: **FALSE**

## Frozen run lineage

- source HEAD: `8d7a243ef6a55dc0a12a0484d9138bdb9b11e2e1`
- source TREE: `bad2a2d8a60bddec5700ff6375a9fc6fcb586d8b`
- run: `34047683558`
- job: `101525569557`
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- topology artifact: `9980023181`
- runtime artifact: `9993650928`
- runtime artifact digest: `sha256:3a36401cab2fabe0e8154179cc356f80dae5ede959fa8a9970278355c8987a5e`
- downloaded ZIP SHA-256 independently matched the GitHub artifact digest.

## Terminal result

Exact Direct31 record set: `31` paths.

- record PASS: `28`
- record FAIL: `3`
- coverage promotion: `0`
- replay not admitted because record gate failed closed.

Failed exact paths:

1. `forge-behavior-v2:7365d5c90f364445ba2b22da9f1998aaf50fa394` — Disperse
2. `forge-behavior-v2:c20d354ac8258ea3088607c1c8bd7bbf3dab44ec` — Buried Ruin
3. `forge-behavior-v2:dd2f9dfad2fba886a0fa66300b8ab654ad501b86` — River's Rebuke

For all three failures, the observation-only PlaySpellAbility stage trace shows:

- `ANNOUNCE_TYPE=true`
- `ANNOUNCE_X=true`
- `CHECK_RESTRICTIONS=true`
- `SETUP_TARGETS=true`
- `CAST_TIMING=true`
- `LEGAL_AFTER_STACK=true`
- `PRECOST_REQUISITES=true`
- `PAY_COST=false`
- `PREREQUISITES_MET=false`
- `PLAY_ABILITY=false`

No target legality failure was observed. No manual target injection or direct effect resolution occurred.

## Authoritative decision evidence around the failures

Each failure reached authoritative target selection and then one or more `MANA_PAYMENT` requests that were accepted by the external decision boundary:

- Disperse: `TARGET_SINGLE` followed by 2 accepted `MANA_PAYMENT` requests.
- Buried Ruin: `TARGET_SINGLE` followed by 3 accepted `MANA_PAYMENT` requests.
- River's Rebuke: `TARGET_PLAYER` followed by 6 accepted `MANA_PAYMENT` requests.

Decoded selected mana-payment semantic values were opaque choice identities (`choice:<id>`), not an independently adjudicated mana plan.

The inherited qualification pilot sorts authoritative options by a deterministic SHA-derived stable key and selects the first required count. That policy is not mana-aware. Whether the authoritative `MANA_PAYMENT` request already exposes sufficient actor-scoped mana semantics, or whether the request ABI must be enriched by the Forge-owned boundary, requires source adjudication before repair.

## Failure semantics

This checkpoint does **not** classify the three failures as Forge Rules Core defects. `PAY_COST=false` is directly verified; the current likely blocker is the qualification pilot/payment-option interface. That classification remains provisional until the exact Direct-runtime `MANA_PAYMENT` externalization is inspected.

No PASS from this run is promoted independently. Direct31 remains unqualified as a complete 31-path shard.

## Required next action

Inspect the exact Direct-runtime source pin that materializes `MANA_PAYMENT` authoritative options. Repair only if the pilot can select from Forge-owned payable options using actor-scoped authoritative metadata, or enrich that Forge-owned option ABI systemically. Do not implement mana legality or payment feasibility in the pilot, do not use card-name branches, and do not add first/default/random fallback behavior.
