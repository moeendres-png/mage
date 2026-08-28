# Architecture Decision — Current Qualification State

`INITIAL_ARCHITECTURE_DECISION_FROZEN = FALSE`.

At research revision `0ea93d09…`, Forge is still the strongest Rules Core
hypothesis, not a selected architecture. The current strict patch proves a
server-side Player/Card/entity decision seam and a scoped hidden-card transport
correction. It does not prove a complete external control plane.

The current boundary has three directly externalized controller entry points.
Of 109 abstract controller callbacks and 15 blocking GUI decision paths,
106/15 remain outside a runtime-qualified typed request/response contract.
They must remain explicit fail-closed diagnostics; none may fall back to prompt
parsing, GameView inference, AI, first/default/random/pass/cancel behavior.

The first blocker remains:

```text
DECISION_EXTERNALIZATION
  -> FULL_DECISION_CENSUS_AND_TYPED_CALLBACK_COVERAGE = FAIL
```

`REMOTE_QUALIFICATION_EVIDENCE.json` contains current exact artifacts. Do not
create `moeendres-png/commander-simulator-next` from this state.
