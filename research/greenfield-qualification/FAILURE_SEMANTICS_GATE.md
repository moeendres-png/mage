# WS12 unified failure-semantics gate

- Source HEAD: `9566758b0d7b7cd5b1cf9847f0e438b67025c403`
- Source tree: `e7a71586ab52bd24ebe5b6b7b51bf8f6099729a1`
- Authoritative contract SHA-256: `f96cd8b941fce54e3fc2be58d3b62516fee6a33af26b8fbdd67d99704f258d21`
- Required typed categories: **16/16**
- Production-reachable untyped failure outcomes: **UNKNOWN (UNKNOWN)**
- Production-reachable fallback failure handling: **UNKNOWN (UNKNOWN)**
- FAILURE_SEMANTICS: **FAIL_INCOMPLETE**

## Category matrix

| Category | Construction witness | Production binding | Classification | Trace SHA-256 |
|---|---:|---|---:|---|
| `SUCCESS` | PASS | `EXACT_PIN_DECISION_TAPE_AND_MAPPER` | PASS | `de024e51ca41ec26c8b2c2fa59973da0fb891d37d979c090e4ba4ac4ef8e3d50` |
| `PLAYER_CANCELLED` | PASS | `EXACT_PIN_DECISION_TAPE_AND_MAPPER` | PASS | `35893c0bfb54a7a9376f90feed4f3822e3d7bf63e4c09c37175a067a61e2f994` |
| `ACTION_NOT_COMPLETABLE` | PASS | `UNBOUND_GENERIC_CONSTRUCTION_ONLY` | PARTIAL | `1f45ac6298e66c63645db65830a7f655cc95a72f8296ee24a0ffdbc3050c5400` |
| `ILLEGAL_RESPONSE` | PASS | `EXACT_PIN_DECISION_TAPE_AND_MAPPER` | PASS | `ba6eb3af5c8bc49bb42c910042f5b4f7a6a44755a8da082124a6c79a2b525400` |
| `MALFORMED_RESPONSE` | PASS | `EXACT_PIN_DECISION_TAPE_AND_MAPPER` | PASS | `64837db1e15091870d33cf8b6d59b3d5438579d42faa9d05490b82e5c114d714` |
| `STALE_RESPONSE` | PASS | `EXACT_PIN_DECISION_TAPE_AND_MAPPER` | PASS | `8bb8eb8150f1e45a4e0b0ce1712b7dfc349dbefbf4c2acf23dc6966ff971e9b3` |
| `WRONG_ACTOR` | PASS | `EXACT_PIN_DECISION_TAPE_AND_MAPPER` | PASS | `62cf35ffa6a846d55703dca125a515acb8e99b3340ac27034ecab98f85f1150a` |
| `TIMEOUT` | PASS | `EXACT_PIN_DECISION_TAPE_AND_MAPPER` | PASS | `e2865d667751429d45c9aca934daa92a70e3224adc8c98e6333f7b4557120913` |
| `UNSUPPORTED_DECISION_PATH` | PASS | `EXACT_PIN_DECISION_TAPE_AND_MAPPER` | PASS | `e7ea37302556386090b2a05d7e300e9ab765548fbb1b7816f2999a24f4812835` |
| `UNSUPPORTED_RULES_PATH` | PASS | `UNBOUND_GENERIC_CONSTRUCTION_ONLY` | PARTIAL | `ea8f1b21bf3dcb9564bd6c58a28a65065ca4a9e9d21bc74be69406f7d67fd996` |
| `ENGINE_FAILURE` | PASS | `UNBOUND_GENERIC_CONSTRUCTION_ONLY` | PARTIAL | `097ba63abfaf91560a4e6f1c1d4eafe809cefbddec2f425be9cbae5a8cecf2bd` |
| `TRANSPORT_FAILURE` | PASS | `UNBOUND_GENERIC_CONSTRUCTION_ONLY` | PARTIAL | `a0d1c5999025cdf12f91b185317a8efa836fbc2368bc059f3878053662142472` |
| `PROCESS_FAILURE` | PASS | `OS_PROCESS_SUPERVISOR_WITNESS` | CONDITIONAL_PASS | `2ad2a596a744b268c0391a540e19afc800a362f313ad1105d6ed88efaa7539f0` |
| `REPLAY_DIVERGENCE` | PASS | `UNBOUND_GENERIC_CONSTRUCTION_ONLY` | PARTIAL | `1127f8ce3c11213af79662ac3dbb1f2f4f6006350adc97c878cebd8d9236508c` |
| `HIDDEN_INFO_VIOLATION` | PASS | `UNBOUND_GENERIC_CONSTRUCTION_ONLY` | PARTIAL | `61301895fc2821ab539e246fd74902a10813556eafede23295d178b46b75a7f2` |
| `CARD_BEHAVIOR_FAILURE` | PASS | `UNBOUND_GENERIC_CONSTRUCTION_ONLY` | PARTIAL | `bfaa370bff4bf7e1c6c60af18d4435fcdd32d99df4d0831d2d1a15213d9dbc26` |

## Regression decisions

- `Q1_STRICT_DECISION_BOUNDARY`: **NO_RERUN** — The additive tape classification does not change legality or response validation. The exact-pin validator probe passed; this was not a full Q1 predecessor rerun.
- `Q2_PRINCIPAL_HIDDEN_INFORMATION`: **AUDIT_NEEDS_RERUN** — Fixed public envelopes excluded private markers, but the seven unbound adapters have no actual failure payload to assay. The full Q2 predecessor gate was not rerun.
- `Q3_SEMANTIC_REPLAY`: **AUDIT_NEEDS_RERUN** — Only enum construction/non-mutation was exercised; no replay divergence detector is bound. The full Q3 semantic replay gate was not rerun.
- `Q4_PROCESS_ISOLATION`: **NO_RERUN** — Two OS children demonstrated fault isolation, but this was a focused contract probe rather than a full Q4 predecessor rerun; no process isolation implementation changed.
- `Q5_COMMANDER_MULTIPLAYER`: **NO_RERUN** — WS12 changes no Commander or multiplayer rules path.
