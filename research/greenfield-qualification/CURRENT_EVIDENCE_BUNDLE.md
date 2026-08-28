# Current Evidence Bundle

Date: 2026-08-28

This index closes the current research-only qualification increment. It binds
all affected remote evidence to source revision
`5897a196405e6fc1743f41b4d5f9bf6367884930` and tree
`7d2ed2c97fc3579561c9166110f61a757cd88ca9`; the starting research input is
retained only for traceability in `REMOTE_QUALIFICATION_EVIDENCE.json`.

| Boundary | Current run / artifact | SHA-256 | Outcome |
|---|---:|---|---|
| Strict typed decision boundary | `33155888019` / `9679614525` | `7e7158b43da45691faeefd13547e7113e268642d11a2fe27d8af61685e2ac96b` | FAIL: Java validator and metadata-only Decision-Tape PASS; 106 runtime callback paths remain unqualified |
| Hidden-information decoded transport | `33155887970` / `9679616053` | `161dd60187f5135580a18117a25585c22bc7af3fea7b550ab398bd176c9b9180` | scoped PASS: 2P raw identity leak count 0 |
| Decision census / RNG inventory | `33155888005` / `9679578243` | `cf9f8f0db9edd85926990e07a5f89646ef006656cff32a9e2a87885faf20296d` | static PASS: 109/109 controller and 15/15 GUI paths classified; runtime FAIL |
| 2P–5P CLI / three-process replay | `33155888017` / `9679680835` | `f4f39d4855b62d3c5378f98333989d8991b297d056cf1744deb7f1c083e44b83` | NOT_RUN: no state, RNG, or full-game decision stream |

The qualification bundle also contains versioned schemas, the strict patch,
the full decision census, A–T and C01–C22 requirement matrices, Scryfall and
actual-card boundary records, replay/isolation/differential/third-party
adjudications, `CURRENT_STATUS.md`, and `NEXT_HANDOFF.md`.

The evidence supports neither architecture freeze nor production repository
creation. The first hard gate remains
`FULL_DECISION_CENSUS_NOT_EXTERNALIZED`.
