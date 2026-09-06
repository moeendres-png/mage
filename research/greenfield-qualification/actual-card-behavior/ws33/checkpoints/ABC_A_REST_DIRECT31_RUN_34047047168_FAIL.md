# WS33 ABC — A-rest Direct31 Runtime v3 — TERMINAL FAIL

Evidence class: DIRECTLY_VERIFIED / CODE_DERIVED root-cause classification.

## Frozen run

- RUN: `34047047168`
- JOB: `101523857155`
- SOURCE_HEAD: `44d55813e1803bdfd833f1e76f0b2c4b4e6c0a19`
- SOURCE_TREE: `cb13c4105446644ecf8f2fb70da888cf94efe147`
- CONCLUSION: `failure`
- ARTIFACT_ID: `9993464063`
- ARTIFACT_DIGEST: `sha256:45abb498c2096c3b2ff3a40dd9afac3d41aa8a54903372c7ed4e1d2b9392ba4e`
- downloaded ZIP SHA256 independently verified: `45abb498c2096c3b2ff3a40dd9afac3d41aa8a54903372c7ed4e1d2b9392ba4e`

## Record outcome

- exact cases: `31`
- runtime PASS: `27`
- runtime FAIL: `4`
- pilot-visible hidden leak delta: `0` on all paths
- cross-principal leak delta: `0` on all paths
- remote actor binding succeeded
- principal observation instrumentation active
- play-stage observation active
- coverage mutation/promotion: `FALSE/FALSE`

Failing exact paths:

1. `forge-behavior-v2:728d346f8c02e5ba4c32cb442b31e65ee8d6ef30` — Dead Reckoning (`ManaCost:1 B B`)
2. `forge-behavior-v2:7ddf701e9ef53522a4a087a6be55fb793712057c` — Path to Exile (`ManaCost:W`)
3. `forge-behavior-v2:c8e8876ce834a56072b7b64f058ee01b0ebf4ddc` — Condemn (`ManaCost:W`)
4. `forge-behavior-v2:e9cb61631a22f2c7ab960b22fe074ad8a6f0fb37` — Banishment Decree (`ManaCost:3 W W`)

Pinned Forge source confirms those mana costs at the exact pin.

## Stage evidence

For all four failures, observation-only `PlaySpellAbility` telemetry reports:

- `ANNOUNCE_TYPE=true`
- `ANNOUNCE_X=true`
- `CHECK_RESTRICTIONS=true`
- `SETUP_TARGETS=true`
- `CAST_TIMING=true`
- `LEGAL_AFTER_STACK=true`
- `PRECOST_REQUISITES=true`
- `PAY_COST=false`
- `PREREQUISITES_MET=false`

Therefore target legality, timing, restrictions, and post-stack legality are not the rejection point.

The harness seeds the shared mana fixture once before the 31-case loop and does not untap/reseed it between cases. Path-attributed stage evidence shows cumulative successful Mana ability activations before each failing case:

- before Dead Reckoning: `24`
- before Path to Exile: `35`
- before Condemn: `52`
- before Banishment Decree: `65`

Classification: `HARNESS_FIXTURE_LIFECYCLE` — cumulative mana resource depletion between otherwise independent exact cases.

Required repair: refresh/reseed real Forge-payable mana resources per case while keeping `PlaySpellAbility` + `CostPayment.payCost(...)` authoritative. Do not inject mana into the pool and do not bypass cost payment.

No Forge Rules Core defect is proven. No PASS promotion is permitted from this run.

- PASS remains `488`
- UNKNOWN remains `3700`
- A_UNKNOWN remains `57`
