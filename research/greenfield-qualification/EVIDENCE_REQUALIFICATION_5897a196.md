# Evidence Requalification — 5897a196

Date: 2026-08-28

This increment is bound to source `5897a196405e6fc1743f41b4d5f9bf6367884930`,
tree `7d2ed2c97fc3579561c9166110f61a757cd88ca9`, Forge pin
`8c7e9afb8e6caee88644b94e25da5852e36f8928`, Forge tree
`c634b817e037c4531051859f7d00805ffd74931e`, and strict patch SHA-256
`190e2fdacfc24903589164d031072daf87573111b0f8a738e31a6005a71ce476`.

## Current remote evidence

| Boundary | Run | Artifact | Artifact SHA-256 | Result |
|---|---:|---:|---|---|
| strict decision boundary | `33155888019` | `9679614525` | `7e7158b43da45691faeefd13547e7113e268642d11a2fe27d8af61685e2ac96b` | workflow PASS, gate FAIL |
| static decision census/RNG inventory | `33155888005` | `9679578243` | `cf9f8f0db9edd85926990e07a5f89646ef006656cff32a9e2a87885faf20296d` | static census PASS, runtime FAIL |
| scoped raw hidden-information assay | `33155887970` | `9679616053` | `161dd60187f5135580a18117a25585c22bc7af3fea7b550ab398bd176c9b9180` | scoped PASS, leak count 0 |
| 2P–5P runtime/fresh-process replay | `33155888017` | `9679680835` | `f4f39d4855b62d3c5378f98333989d8991b297d056cf1744deb7f1c083e44b83` | workflow FAIL by gate design, replay NOT_RUN |

The Java contract emitted `JAVA_EXTERNAL_DECISION_CONTRACT=PASS`. It directly
exercised successful validation and explicit rejection of missing, null,
malformed, stale, wrong-actor, wrong-principal, illegal-option, invalid-count,
illegal-cancel, consumed-token, timeout, and unsupported-path responses. The
metadata-only tape records accepted, rejected, timeout, and unsupported events
without request labels, option payloads, semantic context, or hidden views.

The static census is now complete as a source classification: 109/109
controller callbacks and 15/15 blocking GUI methods are represented. This is
not runtime decision completeness. The strict gate remains `FAIL` because 106
controller paths are not fully externalized and a full-game Decision-Tape has
not been emitted.

The three fresh 4P processes again produced identical probe envelopes but no
canonical state, RNG-event, or full-game decision streams. The semantic replay
validator therefore returned `NOT_RUN` with three `E_STREAM_MISSING` failures;
stdout, stderr, and timestamps were not accepted as replay evidence.

No architecture freeze or production repository creation is authorized.
