# Decision Census — Current Qualification State

Date: 2026-08-28

Status: **PARTIAL / FAIL-CLOSED**.

The exact Forge research pin is `8c7e9afb8e6caee88644b94e25da5852e36f8928`.
The typed server-side entity-selection patch produces patched Forge tree
`c634b817e037c4531051859f7d00805ffd74931e` and has SHA-256
`ef10fd59faf63b241b862d1700690bc1668421f00b72541929333f7fe4d1c7e9`.

## Materialized census

- `PlayerControllerHuman` callback declarations: **109**.
- Blocking server GUI decisions: **15**.
- Directly routed through the new typed seam: **3** —
  `chooseCardsForEffect`, `chooseSingleEntityForEffect`, and
  `chooseEntitiesForEffect`.
- Remaining controller declarations outside the typed request/response path:
  **106**.
- Runtime decision-tape qualification: **NOT_RUN**.

The three entity-selection paths pass static assertions and the exact Forge
checkout compiles. This is not equivalent to full production qualification:
the remaining callbacks and blocking GUI methods have not been converted to
typed requests with runtime evidence. Their strict mode behavior is explicit
failure, never implicit AI/default/first/random/pass/cancel substitution.

The machine-readable source is `DECISION_CENSUS.json`; the capability-level
view is `DECISION_CAPABILITY_REGISTRY.json`.

```text
DECISION_EXTERNALIZATION                 = FAIL
ENTITY_PLAYER_CARD_SELECTION_SEAM       = PASS_STATIC_AND_COMPILE_ONLY
FULL_DECISION_CENSUS_AND_TYPED_CALLBACK = FAIL
RUNTIME_DECISION_TAPE                   = NOT_RUN
ARCHITECTURE_FREEZE                     = FALSE
```

Historical workflow IDs remain provenance context only and are not current
HEAD proof.
