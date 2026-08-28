# Forge Strict Typed Decision Export Gate

Date: 2026-08-28

Status: **FAIL — no architecture freeze**.

## Current qualification revision

- Research revision: `0ea93d09d80e5c126eccb3323b17f14542e5559a`
- Research tree: `64c97a207ad270fa398682c84d8dd238811a8b79`
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- Forge unpatched head tree: `c634b817e037c4531051859f7d00805ffd74931e`
- Patch SHA-256: `d783c20c3e43947a84edc4ee2743ac959a5867e71e51b52bd9936f7c85a4cd9b`

The current remote strict-boundary qualification is run `33124530375`,
artifact `9667836800`, SHA-256
`66f4dc3acf7a745fa7b84075142ef70e73664b8869970f267a4807bef98e9977`.
Its workflow completed successfully while the qualification gate correctly
reported `FAIL`.

## What is implemented

The research-only patch adds a server-side typed seam at the authoritative
`InputSelectEntitiesFromList` / `PlayerControllerHuman` boundary. It exports
exact `Player`, `Card`, and other `GameEntity` options, actor, principal,
principal-only visibility, min/max, constraints, semantic context, response
schema, and a monotonic decision token. Responses are validated against the
current request and input before atomic application.

Missing/null, malformed, stale, wrong-actor, wrong-principal, illegal,
out-of-range, illegal-cancel, consumed, timeout, and unsupported paths do not
fall back to AI, first-choice, random, pass, prompt parsing, or GUI behavior.
The exact Forge checkout compiles successfully; the engine-neutral strict
contract suite passes.

## Why the production gate still fails

The static census contains 109 `PlayerControllerHuman` callback declarations
and 15 blocking server GUI decisions. Only these three controller entry points
are directly routed through the new seam:

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
