# Final Architecture Decision — NOT FROZEN

Date: 2026-08-28

```text
INITIAL_ARCHITECTURE_DECISION_FROZEN = FALSE
READY_FOR_GREENFIELD_BUILD          = FALSE
READY_FOR_TRUSTED_REAL_DECK_SIMULATION = FALSE
PRODUCTION_REPOSITORY_CREATED       = FALSE
```

## Decision

No production Rules Core, control plane, observation boundary, RNG/replay
format, interop strategy, or license/distribution model is selected.

Forge remains the current Rules Core hypothesis. At exact pin
`8c7e9afb…`, the research patch establishes a server-side typed entity
selection boundary with authoritative Player/Card/entity options, typed
response validation, monotonic tokens, principal scope, and no GUI/AI/default
fallback. The same patch now redacts hidden CardViews per client across full
state, deltas, events, and visibility transitions; current decoded 2P transport
testing saw zero hidden card names.

## Why this is not a freeze

The exact current strict run (`33124530375`) proves only three directly routed
controller entry points. The remaining 106 of 109 callbacks and all 15
blocking GUI decision paths lack a runtime-qualified typed request/response
contract. The current runtime run (`33124530414`) also contains no canonical
state, RNG, or Decision-Tape streams, and the 1,721 actual-card requirement
union is still missing materialized Oracle IDs.

The scoped hidden transport pass does not cover the required principal-scoped
4P campaign, logs, exceptions, IDs/hashes, replay, debug output, or
reveal/look lifecycle. Differential adjudication, isolation, matrices, and
license/distribution gates remain incomplete.

```text
DECISION_EXTERNALIZATION
  -> FULL_DECISION_CENSUS_AND_TYPED_CALLBACK_COVERAGE = FAIL
```

`REMOTE_QUALIFICATION_EVIDENCE.json` contains current source/tree, artifact
hashes, and gate results. Historical workflow evidence is not substituted for
current-head proof. No private `moeendres-png/commander-simulator-next`
repository is created.
