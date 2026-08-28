# Forge Strict Typed Decision Export Gate

Date: 2026-08-28

Status: **FAIL — no architecture freeze**.

## Current qualification revision

- Research revision: `5897a196405e6fc1743f41b4d5f9bf6367884930`
- Research tree: `7d2ed2c97fc3579561c9166110f61a757cd88ca9`
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- Forge unpatched head tree: `c634b817e037c4531051859f7d00805ffd74931e`
- Patch SHA-256: `190e2fdacfc24903589164d031072daf87573111b0f8a738e31a6005a71ce476`

The current remote strict-boundary qualification is run `33155888019`,
artifact `9679614525`, SHA-256
`7e7158b43da45691faeefd13547e7113e268642d11a2fe27d8af61685e2ac96b`.
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
