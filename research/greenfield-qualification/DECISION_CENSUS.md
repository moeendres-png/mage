# Decision Census — Current Qualification State

Date: 2026-08-28

Status: **PARTIAL / FAIL-CLOSED**.

Current qualification revision: `0ea93d09d80e5c126eccb3323b17f14542e5559a` /
`64c97a207ad270fa398682c84d8dd238811a8b79`.

The exact Forge research pin is `8c7e9afb8e6caee88644b94e25da5852e36f8928`
(unpatched head tree `c634b817e037c4531051859f7d00805ffd74931e`). The
typed server-side patch SHA-256 is
`d783c20c3e43947a84edc4ee2743ac959a5867e71e51b52bd9936f7c85a4cd9b`.

## Materialized census

- `PlayerControllerHuman` callback declarations: **109**.
- Blocking server GUI decisions: **15**.
- Directly routed through the new typed seam: **3** —
  `chooseCardsForEffect`, `chooseSingleEntityForEffect`, and
  `chooseEntitiesForEffect`.
- Remaining controller declarations outside the typed request/response path:
  **106**.
- Remote current census run: **33124530367**, artifact **9667812533**,
  SHA-256 `a8f5458fffb06f4630d3a9b9cf6967497cc90be889c61f11ff733bddd656420f`.
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

`REMOTE_QUALIFICATION_EVIDENCE.json` binds the remote evidence to the current
research revision. Historical workflow IDs remain provenance context only and
are not current-head proof.
