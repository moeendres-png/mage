# Decision Census — Current Qualification State

Date: 2026-08-28

Status: **PARTIAL / FAIL-CLOSED**.

Current qualification revision: `5897a196405e6fc1743f41b4d5f9bf6367884930` /
`7d2ed2c97fc3579561c9166110f61a757cd88ca9`.

The exact Forge research pin is `8c7e9afb8e6caee88644b94e25da5852e36f8928`
(unpatched head tree `c634b817e037c4531051859f7d00805ffd74931e`). The
typed server-side patch SHA-256 is
`190e2fdacfc24903589164d031072daf87573111b0f8a738e31a6005a71ce476`.

## Materialized census

- `PlayerControllerHuman` callback declarations: **109**.
- Blocking server GUI decisions: **15**.
- Directly routed through the new typed seam: **3** —
  `chooseCardsForEffect`, `chooseSingleEntityForEffect`, and
  `chooseEntitiesForEffect`.
- Remaining controller declarations outside the typed request/response path:
  **106**.
- Remote current census run: **33155888005**, artifact **9679578243**,
  SHA-256 `cf9f8f0db9edd85926990e07a5f89646ef006656cff32a9e2a87885faf20296d`.
- Static classifications: **109/109** controller callbacks and **15/15**
  blocking GUI methods materialized.
- Java validator and metadata-only Decision-Tape contracts: **PASS**.
- Full-game runtime decision-tape qualification: **NOT_RUN**.

The three entity-selection paths and the new server-mapped discrete facade
pass static assertions and the exact Forge checkout compiles. This is not
equivalent to full production qualification: the remaining callbacks and
blocking GUI methods have not been converted to typed requests with runtime
evidence. Their strict mode behavior is explicit failure, never implicit
AI/default/first/random/pass/cancel substitution.

The machine-readable source is `DECISION_CENSUS.json`; the capability-level
view is `DECISION_CAPABILITY_REGISTRY.json`.

```text
DECISION_EXTERNALIZATION                 = FAIL
ENTITY_PLAYER_CARD_SELECTION_SEAM       = PASS_STATIC_AND_COMPILE_ONLY
FULL_DECISION_CENSUS_AND_TYPED_CALLBACK = FAIL
RUNTIME_DECISION_TAPE                   = NOT_RUN
ARCHITECTURE_FREEZE                     = FALSE
```

`REMOTE_QUALIFICATION_EVIDENCE.json` binds the remote evidence to the current
research revision. Historical workflow IDs remain provenance context only and
are not current-head proof.
