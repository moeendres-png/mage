# WS32 — CARD_BEHAVIOR_FAILURE PRODUCTION BINDING — HANDOFF

## Scope

Repository: `moeendres-png/mage`

Branch: `work/ws32-card-behavior-failure-production-binding-20260830`

Owner family: `FAILURE_SEMANTICS / CARD_BEHAVIOR_FAILURE`

WS32 closes exactly the WS25 blocker for production-reachable `CARD_BEHAVIOR_FAILURE`. It does not adjudicate an Architecture Freeze and does not reopen unrelated Q2/Q3 evidence.

## Immutable boundaries

- WS26 base HEAD: `206a39cbaa3eeb98b10c2ddc36d51fe5b1b2f5ef`
- WS26 base TREE: `837f445f78bb26462653c58baf1532e294151b10`
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- WS12 contract HEAD: `80743bdbc2950b00e422f3deb38f04111f30a4d4`
- WS12 contract TREE: `9a2a52932a0d69dcf06c2392cddcf40b47e810cc`

## Production binding

WS32 adds a generic, disabled-by-default simulator semantic-verifier hook to the authoritative Forge stack-resolution path:

`forge.game.zone.MagicStack#resolveStack` → `finishResolving(...)` → `Game.verifyResolvedCardBehavior(...)` → final last-state copy.

Expected card semantics remain external to the Rules Core. The production hook contains no card-name branches and does not decide legality, costs, targets, priority, trigger order or rule resolution.

A dedicated sanitized `CardBehaviorVerificationException` is mapped by the retained WS12 `UnifiedOutcomeMapper` to exactly `CARD_BEHAVIOR_FAILURE`. Unknown throwables are not coerced into this category.

## Actual-card witness

`Ws32CardBehaviorFailureQualificationTest` reuses the WS26 Mulldrifter runtime scenario:

1. real card object in Hand;
2. real zone move to Battlefield;
3. real `ChangesZone` ETB trigger collection;
4. authoritative trigger transfer to the regular stack;
5. actual `MagicStack.resolveStack()` execution;
6. post-resolution semantic verification.

The witness executes two runs:

- positive control: actual hand/library state equals the external expected state and staged publication succeeds;
- controlled mismatch: the Rules Core still completes the actual draw correctly, but one external expected value is deliberately wrong. The production verifier throws the dedicated sanitized signal after engine resolution; the external staged state is not published.

The mismatch must classify as `CARD_BEHAVIOR_FAILURE`, not `ENGINE_FAILURE`.

## Failure semantics

Required public outcome:

- category: `CARD_BEHAVIOR_FAILURE`
- public message: `card behavior verification failed`
- state committed: `false`
- fallback used: `false`

Expected/actual semantic values remain in private qualification evidence only and are structurally absent from the public outcome envelope.

## Machine gates

The workflow `.github/workflows/ws32-card-behavior-failure-production-binding.yml` must produce an immutable artifact named:

`ws32-card-behavior-failure-production-binding`

Canonical machine outputs:

- `WS32_GATE.json`
- `CARD_BEHAVIOR_FAILURE.json`
- `WS32_RUNTIME_BINDING.json`
- `WS32_HASHES.sha256`
- `workflow-evidence/WS32_RUNTIME_WITNESS.json`
- Forge/TestNG runtime log and XML evidence
- tested source HEAD/TREE and prerequisite pins

Completion requires every `WS32_GATE.json.hard_gates` value to be true and:

```text
CARD_BEHAVIOR_FAILURE = PASS
FAILURE_SEMANTICS_BLOCKER_CLOSED = true
WORKSTREAM_COMPLETE = true
state_committed = false
fallback_used = false
production_reachable = true
integration_status = Q5_PENDING_INTEGRATION
```

A green Actions run alone is not sufficient; the artifact digest and internal `WS32_HASHES.sha256` must be verified independently.

## Regression / integration status

WS32 changes only the generic production semantic-verification seam and its qualification package. It does not authorize a global Q5/Architecture Freeze claim.

Final integration status remains:

`Q5_PENDING_INTEGRATION`
