# Final Architecture Decision — NOT FROZEN

Date: 2026-08-27

`INITIAL_ARCHITECTURE_DECISION_FROZEN = FALSE`

No Production Rules Core is selected.

## Reason

The mandatory `DECISION_EXTERNALIZATION` gate is not satisfied by any current finalist:

- Forge stock path contains forbidden fallback behavior and the strict research qualification did not prove all production-reachable decision paths through a non-auto external pilot.
- XMage targeted evidence explicitly reports the complete external-pilot runtime gate as false.
- phase.rs reports that all required decisions are not externalized-and-tested.
- Manabrew exact-pin audit reports concrete silent/default/first-choice fallbacks and production decision gate FAIL.

Because this earliest boundary is unqualified, production-scoped hidden-information, explicit action/RNG tape replay, and per-card decision/visibility/replay safety cannot be fully qualified either.

## Minimal next gate

Build a **research-only Forge Strict External Pilot Qualification Adapter** at exact pin `8c7e9afb8e6caee88644b94e25da5852e36f8928` that:

1. uses no Headless auto-click/default/AI fallback;
2. exposes exact legal choices plus actor and visibility scope;
3. requires typed responses and rejects missing/null, stale, wrong-actor, malformed, illegal and timeout responses;
4. emits a machine-readable Decision Capability Registry;
5. runtime-covers every decision kind reachable from the actual-card requirement population;
6. marks any unhandled path `UNSUPPORTED_DECISION_PATH` and invalidates the game;
7. demonstrates `SILENT_FALLBACKS = 0` and `PRODUCTION_REACHABLE_UNSUPPORTED_DECISIONS = 0`.

Only after this passes should the same boundary be used for pilot-visible hidden-information and fresh-process action/RNG tape replay qualification.

No production repository may be created from this state.
