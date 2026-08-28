# Decision Census — Current Qualification State

Date: 2026-08-28

Status: **PARTIAL / FAIL-CLOSED**.

Current qualification revision: `34036a2d6704c0b70c0a59d071bc938870db0c2b` /
`33e3968b35fc5cd2967f12d8f57c4b7ebab2d21f`.

The exact Forge research pin is `8c7e9afb8e6caee88644b94e25da5852e36f8928`
(unpatched head tree `c634b817e037c4531051859f7d00805ffd74931e`). The
typed server-side patch SHA-256 is
`42ff6d7301287af90b3c5b1ba9d809d78f19018d80f4a8ba5b0eeacad0d1e581`.

## Materialized census

- `PlayerControllerHuman` callback declarations: **109**.
- Blocking server GUI decisions: **15**.
- Directly routed through the new typed seam: **3** —
  `chooseCardsForEffect`, `chooseSingleEntityForEffect`, and
  `chooseEntitiesForEffect`.
- Remaining controller declarations outside the typed request/response path:
  **106**.
- Remote current census run: **33152614624**, artifact **9678318483**,
  SHA-256 `bf9be7008c4f14764ec04c624d5451d7147b61296fe7f27a02f863ed7b630f2f`.
- Runtime decision-tape qualification: **NOT_RUN**.

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
