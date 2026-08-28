# Current Evidence Bundle

Date: 2026-08-28

This index closes the current research-only qualification increment. It binds
all affected remote evidence to source revision
`34036a2d6704c0b70c0a59d071bc938870db0c2b` and tree
`33e3968b35fc5cd2967f12d8f57c4b7ebab2d21f`; the starting research input is
retained only for traceability in `REMOTE_QUALIFICATION_EVIDENCE.json`.

| Boundary | Current run / artifact | SHA-256 | Outcome |
|---|---:|---|---|
| Strict typed decision boundary | `33152614647` / `9678342430` | `1cf3fb821bae89ebc4761c412a7609862179698c1de2d862ad2219c9d49fbe67` | FAIL: entity seam/discrete facade compile, but full census and runtime remain unqualified |
| Hidden-information decoded transport | `33152614611` / `9678348191` | `126f4062334510582b7fc9eaace074e3568b3805397334a1d8fc88f0d1ca23c8` | scoped PASS: 2P raw identity leak count 0 |
| Decision census / RNG inventory | `33152614624` / `9678318483` | `bf9be7008c4f14764ec04c624d5451d7147b61296fe7f27a02f863ed7b630f2f` | FAIL: 109/15 census incomplete, 10 fallback and 8 direct-RNG findings remain |
| 2P–5P CLI / three-process replay | `33152614679` / `9678412031` | `6798a2841e45e8b9aada2411d1739280dba507ad769d075a84598cf3e189a8de` | NOT_RUN: no state, RNG, or decision stream |

The qualification bundle also contains versioned schemas, the strict patch,
the full decision census, A–T and C01–C22 requirement matrices, Scryfall and
actual-card boundary records, replay/isolation/differential/third-party
adjudications, `CURRENT_STATUS.md`, and `NEXT_HANDOFF.md`.

The evidence supports neither architecture freeze nor production repository
creation. The first hard gate remains
`FULL_DECISION_CENSUS_NOT_EXTERNALIZED`.
