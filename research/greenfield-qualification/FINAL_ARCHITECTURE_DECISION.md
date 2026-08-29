# Architecture Decision — NOT FROZEN after WS90

Date: 2026-08-29

```text
INITIAL_ARCHITECTURE_DECISION_FROZEN   = FALSE
READY_FOR_GREENFIELD_BUILD             = FALSE
READY_FOR_TRUSTED_REAL_DECK_SIMULATION = FALSE
PRODUCTION_REPOSITORY_CREATED           = FALSE
```

## Decision

No production architecture is frozen. WS90 materially strengthens the Forge
candidate but also identifies three mandatory non-PASS areas that prohibit a
freeze: Q6 actual-card behavior, the integrated failure model, and Q8's
architecture-specific license boundary.

## Technically qualified candidate constraints

These are evidence-backed constraints on the current strongest hypothesis; they
are **not** a Frozen ADR:

- `PRODUCTION_RULES_CORE_CANDIDATE`: Forge at
  `8c7e9afb8e6caee88644b94e25da5852e36f8928` plus the qualified WS01/WS05/WS06
  research overlays.
- `CONTROL_PLANE_CANDIDATE`: external pilots choose only from server-generated
  typed legal decision options; production-reachable untyped/fallback paths are
  zero in the qualified 4P run.
- `OBSERVATION_MODEL_CANDIDATE`: principal-scoped observations and transport;
  the qualified 4P hidden-info campaign reports zero pilot-visible leaks and
  zero cross-principal decision leaks.
- `RNG_MODEL_CANDIDATE`: explicit game-scoped named RNG streams with an event
  tape and deterministic fresh-process replay.
- `REPLAY_MODEL_CANDIDATE`: canonical semantic state + RNG + decision tapes;
  A/B/C fresh-process replay is zero-divergence.
- `PROCESS_ISOLATION_MODEL_CANDIDATE`: one game per OS process. Same-JVM
  multi-game isolation is not qualified and must not be silently assumed.
- `MULTIPLAYER_MODEL_CANDIDATE`: 4P Commander is primary; 2P–5P required
  conformance subsets pass.
- `REFERENCE_ENGINES`: XMage for the currently qualified shared differential
  scenarios; phase.rs and Manabrew remain reference-only where adapters are
  unsupported.

## Why Freeze remains prohibited

### Q6 — actual-card behavior

WS10 verified the exact 1,678-identity requirement corpus, Forge presence,
loadability and CardFactory construction. It then classified all 1,678 as
`CONDITIONAL_FULL`, with 0 `FULL`. WS90 rejects the resulting Q6 PASS claim:
per-card decision/hidden/replay flags are derived from global WS01/WS05/WS06
PASS values after source regex reachability, and dedicated behavior is required
only when hard suspicious source markers are found. Successful construction and
global contract prerequisites do not prove each card's rules behavior.

### Failure model

The integrated evidence distinguishes many negative response paths and proves
no decision fallback, but it does not expose one verified outcome taxonomy that
covers all required categories from `SUCCESS` through response failures,
unsupported decision/rules paths, engine/transport/process failures, replay
and hidden-info violations, and card-behavior failure.

### Q8 — license / third-party

WS03's exact-pin license inventory and third-party boundary are accepted. Its
own final status is nevertheless
`DEFERRED_PENDING_ARCHITECTURE_SELECTION` with
`LICENSE_DECISION_COMPLETE = FALSE`. Linkage/distribution/interop obligations
cannot be promoted to PASS before the concrete production topology exists.

## Current integrated proof anchor

- runtime-qualified integration source: `55820618e7243bd5ba8cfa33c3148cea8c166c73`
- tree: `3706900d49c6ef61690c227bb7b4c0067fbcfb44`
- WS90 integrated rerun: `33250119165`
- artifact: `9714119110`
- artifact SHA-256:
  `d5bdb8b59045c78c5c3774bac1f9091c7b32327834eea9abf106412452cdcb4c`

No `moeendres-png/commander-simulator-next` repository is authorized from this
state. The next dependency wave is defined in `NEXT_HANDOFF.md`.
