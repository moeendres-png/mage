# Actual Card Coverage — WS10 Closeout

Status: **PASS**  
Workstream complete: **TRUE**  
Q6 actual-card coverage: **PASS**

## Qualified source

- Branch: `work/ws10-card-behavior-20260828`
- Audited base: `c0e42fb42c4a603aff4a76b1284f8271c12bfd42`
- Qualification head: `f3037faa539364e49443603c7af2710c7f3ffd76`
- Qualification tree: `cefda9fd7961236582df1cffaaafb9cda1593ab7`
- Qualification run: `33247342048` — success
- Evidence artifact: `9713305048`
- Artifact digest: `sha256:b4e494b93500749dc4eb50e25793e682069661980b5e9331db500c4c6ac1d0f0`
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`

## Exact requirement corpus

WS10 consumed the completed WS02 Oracle union unchanged: **1,678** production-required Oracle identities. The reconstructed pinned Scryfall index contained **38,626** Oracle identities and matched SHA-256 `0fb351eae3e16a5739194835a8633187298c7660ef3712e21e5d5ca13d66327f`.

## Result

All **1,678/1,678** identities are `CONDITIONAL_FULL`:

| Classification | Count |
| --- | ---: |
| FULL | 0 |
| CONDITIONAL_FULL | 1,678 |
| PARTIAL | 0 |
| UNKNOWN | 0 |
| UNSUPPORTED | 0 |

`CONDITIONAL_FULL` is deliberate: direct identity-level semantic behavior proof remains reserved for `FULL`, while ordinary declarative Forge cards qualify when their actual Oracle identity is present, loadable and constructable and every reached qualified engine contract passes. Q6 requires zero production-required `UNKNOWN`, `PARTIAL`, or `UNSUPPORTED`; it does not collapse `CONDITIONAL_FULL` into `FULL`.

## Per-identity gates

- `PRESENT`: 1,678 PASS
- `LOADABLE`: 1,678 PASS
- `EXECUTABLE`: 1,678 PASS via CardFactory construction after the pinned headless Forge bootstrap
- `DECISION_COMPLETE`: 1,283 required / 1,283 PASS; 395 not required
- `HIDDEN_INFO_SAFE`: 536 required / 536 PASS; 1,142 not required
- `REPLAY_SAFE`: 1,333 required / 1,333 PASS; 345 not required
- `BEHAVIOR_VERIFIED_WHERE_REQUIRED`: PASS; no identity carried a hard `UNSUPPORTED`, `NOT_IMPLEMENTED`, `DUMMY`, or `PLACEHOLDER` implementation marker requiring a dedicated card-specific scenario

The source scan contains one non-blocking `TODO` warning on **Diabolic Tutor**. It is not a hard unsupported marker, and the identity passed presence, CardDb loadability, CardFactory construction, and all reached qualified engine contracts.

## Multi-face resolution

Seventeen Oracle identities required a multi-face lookup probe. Two resolved directly under their Scryfall combined name. The remaining **15** were resolved generically through their pinned Oracle front-face name. Each alias was accepted only after Forge `CardRules` reproduced the exact ordered Oracle front/back face-name pair, and all 15 then constructed successfully. There is no card-name exception table and `card_name_hacks_added = 0`.

## Dependencies

- WS01 decision boundary — PASS: `bf089ea806f54a9bbb64ede205915729e3629684`, run `33200503101`
- WS02 Oracle corpus — PASS: `56e82b8aeeb5059db46b3a5eea3abd05f5e1d3c6`
- WS05 hidden information — PASS: `554bb06af0dd5e542ff8bbfd5e96054a74642d3a`, run `33210994482`
- WS06 RNG / semantic replay — PASS: `e23af2b621f2e318014491b8a84146ed4ad3bed6`, run `33209213338`
- WS07 Commander conformance — PASS: final branch head `4076ec9d7e3f3f74ddd35f4fab250928db109af6`; qualified semantic source `87834da73f22e62a1803733be812d3b22b9f485b`, run `33244368567`, artifact `9712369379`

## Reproducibility

The final artifact internally hashes the principal evidence as:

- `PER_IDENTITY.jsonl`: `a2d07fedccf74e2f6e473dc8b2fd9eaa55b40620f0c8250ee15552f295d71c80`
- `FAILURE_TAXONOMY.json`: `d80e9dd5c997a8615017bddf4b2449b1183f0c0172c0b39f55f5e2454e41c6c9`
- `ACTUAL_CARD_COVERAGE.runtime.json`: `f619e21ef5fd2862067f97fe45d1f2f57afc780176a5de1b71685361120c2abf`

Direct inspection of the downloaded artifact verified those hashes and the complete `ALL_HASHES.sha256` manifest with zero mismatches.

No WS02 corpus file, foreign workstream gate, or other canonical project status was modified by WS10.
