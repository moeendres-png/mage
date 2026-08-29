# WS12 unified failure-semantics gate

- Source HEAD: `259d6d68b59fe0cdca3d8d495371b84a226c67fa`
- Source tree: `991817a776ae1b50e95b3969a7e6ed891294780b`
- Authoritative contract SHA-256: `f96cd8b941fce54e3fc2be58d3b62516fee6a33af26b8fbdd67d99704f258d21`
- Required typed categories: **16/16**
- Production-reachable untyped failure outcomes: **0**
- Production-reachable fallback failure handling: **0**
- FAILURE_SEMANTICS: **PASS**

## Category matrix

| Category | Witness | State policy | No fallback | Hidden-safe payload | Trace SHA-256 |
|---|---:|---:|---:|---:|---|
| `SUCCESS` | PASS | PASS | PASS | PASS | `485123e599cb56c0745a454610bfa8a814832da638d7286a2d8b7e71119821ef` |
| `PLAYER_CANCELLED` | PASS | PASS | PASS | PASS | `5781558e7bb6f09efd11dd23eedd38fb1856d82ff0b9cf63baf281ececf9647d` |
| `ACTION_NOT_COMPLETABLE` | PASS | PASS | PASS | PASS | `25a0c10d90de415655a9723538e59636693df8ba49969000bb6775a318b9cc24` |
| `ILLEGAL_RESPONSE` | PASS | PASS | PASS | PASS | `e6e43973f57a25c5f3fe370fcb12083370198685f4477ef7fd34eb1a3b4c866e` |
| `MALFORMED_RESPONSE` | PASS | PASS | PASS | PASS | `d4788d6f8713153c056affa6fb710d1e44084694606333472a7ce4fb42f21891` |
| `STALE_RESPONSE` | PASS | PASS | PASS | PASS | `135d3af30fd1e472539cabae1fd2c318773cd22a3b4baa109b4a97a229559fb2` |
| `WRONG_ACTOR` | PASS | PASS | PASS | PASS | `aac0450cd2eec61bd96d406fe96dfc8452dd2cbe927b323ddfc36bc515f20ce6` |
| `TIMEOUT` | PASS | PASS | PASS | PASS | `9a792d99f1190b67b5d54bb22e77eee536c05c029066ab4f10c6cf7e58bc85d6` |
| `UNSUPPORTED_DECISION_PATH` | PASS | PASS | PASS | PASS | `80b5e8f736fa9da30a5485f0e9d8f956c62967e76954f00702f4baad4820fe9c` |
| `UNSUPPORTED_RULES_PATH` | PASS | PASS | PASS | PASS | `5c1ff45e69cce66a556144381f986a5b3fc7b5dbd576522b305a4c8650d11508` |
| `ENGINE_FAILURE` | PASS | PASS | PASS | PASS | `967ac49f30916c323e4a7cfb6ff7c9db2c24ad9e18d818906a17649dd6ece03d` |
| `TRANSPORT_FAILURE` | PASS | PASS | PASS | PASS | `60f346c3c0f81ccef6bb1b2abdb3d62e19a477544a8fea2152c95a07c4baf174` |
| `PROCESS_FAILURE` | PASS | PASS | PASS | PASS | `fad4500f62c7f854c4cb9200a2e6a7efbef7bc4be776f059a62ce9203664c0a4` |
| `REPLAY_DIVERGENCE` | PASS | PASS | PASS | PASS | `ca2b6d1a7b110e122772efdb804eac5ec0f3dd76ec03064f3500d8e0c9f9225e` |
| `HIDDEN_INFO_VIOLATION` | PASS | PASS | PASS | PASS | `fd7fc3fe23cb08f082915494a6f1195284c9a06d772711ea7341650f4cb9dd33` |
| `CARD_BEHAVIOR_FAILURE` | PASS | PASS | PASS | PASS | `18b5706eb30007183a33e2103e172d1ad459538eb569e09a1c47ad8343f33a92` |

## Regression decisions

- `Q1_STRICT_DECISION_BOUNDARY`: **RERUN_NOW** — WS12 maps the existing exact-pin decision validation errors into the unified outcome contract; compile and runtime contract probes are affected.
- `Q2_PRINCIPAL_HIDDEN_INFORMATION`: **RERUN_NOW** — The new public failure envelope is a principal-facing surface; every category is checked against private markers.
- `Q3_SEMANTIC_REPLAY`: **RERUN_NOW** — REPLAY_DIVERGENCE is newly authoritative and is checked as distinct from execution failure without mutating state.
- `Q4_PROCESS_ISOLATION`: **RERUN_NOW** — PROCESS_FAILURE is newly authoritative; two OS child games prove one failed process cannot alter the independent game.
- `Q5_COMMANDER_MULTIPLAYER`: **NO_RERUN** — WS12 changes no Commander or multiplayer rules path.
