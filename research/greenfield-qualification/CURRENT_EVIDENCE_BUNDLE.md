# Current Evidence Bundle

Date: 2026-08-28

This index closes the current research-only qualification increment. It binds
all current remote evidence to source revision
`0ea93d09d80e5c126eccb3323b17f14542e5559a` and tree
`64c97a207ad270fa398682c84d8dd238811a8b79`; the starting research input is
retained only for traceability in `REMOTE_QUALIFICATION_EVIDENCE.json`.

| Boundary | Current run / artifact | SHA-256 | Outcome |
|---|---:|---|---|
| Strict typed decision boundary | `33124530375` / `9667836800` | `66f4dc3acf7a745fa7b84075142ef70e73664b8869970f267a4807bef98e9977` | FAIL: 3/109 callbacks externalized; 106 and 15 blocking GUI paths remain |
| Hidden-information decoded transport | `33124530500` / `9667841078` | `4bffb8c461acafd9437f1f722487aa830102c98bd1aca900504a79024d7836f5` | scoped PASS: 2P raw identity leak count 0 |
| Decision census / RNG inventory | `33124530367` / `9667812533` | `a8f5458fffb06f4630d3a9b9cf6967497cc90be889c61f11ff733bddd656420f` | FAIL: census incomplete and uninstrumented RNG remains |
| 2P–5P CLI / three-process replay | `33124530414` / `9667883597` | `a1c7fe5020c36a5f07324bd15370d057f50dc3de493f8b9d7a9a0efe99fcb9b3` | NOT_RUN: no state, RNG, or decision stream |

The qualification bundle also contains versioned schemas, the strict patch,
the full decision census, A–T and C01–C22 requirement matrices, Scryfall and
actual-card boundary records, replay/isolation/differential/third-party
adjudications, `CURRENT_STATUS.md`, and `NEXT_HANDOFF.md`.

The evidence supports neither architecture freeze nor production repository
creation. The first hard gate remains
`FULL_DECISION_CENSUS_NOT_EXTERNALIZED`.
