# Architecture Decision — Current Qualification State

`INITIAL_ARCHITECTURE_DECISION_FROZEN = FALSE`.

The current evidence supports a narrow hypothesis, not a final architecture:
Forge remains the strongest Rules Core candidate, provided its authoritative
`Input` / `PlayerControllerHuman` boundary can be made fully typed and
principal-scoped. The research patch now proves the Player/Card/entity
selection seam at static and compile level, but it does not qualify the full
decision surface.

Current blocker:

```text
DECISION_EXTERNALIZATION
  -> FULL_DECISION_CENSUS_AND_TYPED_CALLBACK_COVERAGE = FAIL
```

The census is 109 controller declarations and 15 blocking GUI decisions; only
3 controller entry points are directly routed. The remaining strict paths
must produce explicit typed unsupported errors until they are implemented and
runtime-qualified. No prompt parsing, GameView legality inference, AI,
first/default/random/pass/cancel fallback, or Rules reimplementation is
allowed.

Do not create `moeendres-png/commander-simulator-next` from this state.
