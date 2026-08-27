# Final Architecture Decision — NOT FROZEN

Date: 2026-08-28

```text
INITIAL_ARCHITECTURE_DECISION_FROZEN = FALSE
READY_FOR_GREENFIELD_BUILD          = FALSE
READY_FOR_TRUSTED_REAL_DECK_SIMULATION = FALSE
```

## Decision

No production Rules Core, control plane, observation boundary, RNG/replay
format, interop strategy, or license/distribution model is selected.

Forge remains the current Rules Core hypothesis because its broad Commander
runtime evidence is strongest. The current client-only remote boundary is not
accepted. A research-only server-side typed Decision Export patch now proves a
narrow entity-selection seam at static/compile level:

- exact authoritative options, including Player entities;
- type-qualified option IDs;
- actor, principal, principal-only visibility, min/max, constraints, schema,
  and semantic context;
- monotonic decision/token values;
- strict token/actor/principal/schema/membership/count/cancel/timeout checks;
- atomic application to the current Input;
- explicit failure for GUI/legacy/unsupported paths.

## Why this is not a freeze

The complete census is 109 controller declarations and 15 blocking GUI
decisions, while only 3 controller entry points are directly routed. The
remaining 106 paths have no runtime-qualified typed request/response contract.
No real gameplay Decision-Tape, RNG-Tape, canonical-state replay, hidden-info
zero-leak result, complete actual-card union, or final differential campaign is
available at the same current provenance.

The first blocking gate is therefore:

```text
DECISION_EXTERNALIZATION
  -> FULL_DECISION_CENSUS_AND_TYPED_CALLBACK_COVERAGE = FAIL
```

The exact input head/tree, Forge pin/tree, and patch hash are recorded in
`DECISION_EXPORT_IMPLEMENTATION.json` and
`STRICT_EXTERNAL_PILOT_BOUNDARY_GATE.json`. Historical workflow results are
not substituted for current-head runtime evidence.

No private `moeendres-png/commander-simulator-next` repository is created.
