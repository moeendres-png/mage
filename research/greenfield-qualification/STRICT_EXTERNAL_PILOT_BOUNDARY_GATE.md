# Forge Strict Typed Decision Export Gate

Date: 2026-08-28

Status: **FAIL — no architecture freeze**.

## Current qualification revision

- Research revision: `34036a2d6704c0b70c0a59d071bc938870db0c2b`
- Research tree: `33e3968b35fc5cd2967f12d8f57c4b7ebab2d21f`
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- Forge unpatched head tree: `c634b817e037c4531051859f7d00805ffd74931e`
- Patch SHA-256: `42ff6d7301287af90b3c5b1ba9d809d78f19018d80f4a8ba5b0eeacad0d1e581`

The current remote strict-boundary qualification is run `33152614647`,
artifact `9678342430`, SHA-256
`1cf3fb821bae89ebc4761c412a7609862179698c1de2d862ad2219c9d49fbe67`.
Its workflow completed successfully while the qualification gate correctly
reported `FAIL`.

## What is implemented

The research-only patch adds a server-side typed seam at the authoritative
`InputSelectEntitiesFromList` / `PlayerControllerHuman` boundary and a
server-mapped discrete-choice facade for exact, bounded controller/UI choices.
It exports exact `Player`, `Card`, and other `GameEntity` options or opaque
server-mapped discrete option IDs, actor, principal, principal-only visibility,
min/max, constraints, semantic context, response schema, and a monotonic
decision token. Responses are validated against the current request and input
before atomic application.

Missing/null, malformed, stale, wrong-actor, wrong-principal, illegal,
out-of-range, illegal-cancel, consumed, timeout, and unsupported paths do not
fall back to AI, first-choice, random, pass, prompt parsing, or GUI behavior.
The exact Forge checkout compiles successfully; the engine-neutral strict
contract suite passes.

## Why the production gate still fails

The static census contains 109 `PlayerControllerHuman` callback declarations
and 15 blocking server GUI decisions. The new discrete facade is static and
compile-proven only; only these three controller entry points are directly
routed through the authoritative entity seam:

1. `chooseCardsForEffect`
2. `chooseSingleEntityForEffect`
3. `chooseEntitiesForEffect`

Thus 106 controller declarations remain outside a typed runtime request/response
contract. The decision tape has not been emitted by a real gameplay run, so the
boundary is `PASS_STATIC_AND_COMPILE_ONLY`, not production-qualified.

The next blocker is therefore:

```text
FIRST_BLOCKING_GATE    = DECISION_EXTERNALIZATION
FIRST_BLOCKING_SUBGATE = FULL_DECISION_CENSUS_AND_TYPED_CALLBACK_COVERAGE
```

No production repository is created from this state.
