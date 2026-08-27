# Final Architecture Decision — NOT FROZEN

Date: 2026-08-27

`INITIAL_ARCHITECTURE_DECISION_FROZEN = FALSE`

No Production Rules Core is selected.

## New directly verified closure

The first Forge Strict External Pilot qualification step has now been closed, not left as generic insufficient evidence.

- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- prior strict runtime reused: run `33095241142`, artifact `9656740763`
- strict-boundary closure: run `33112928078`, artifact `9663315184`
- dedicated gate evidence: `STRICT_EXTERNAL_PILOT_BOUNDARY_GATE.json/.md`
- decision registry: `DECISION_CAPABILITY_REGISTRY.json`

The evidence-producing workflow itself passed, while the **qualification gate machine-readably returned FAIL**.

## Exact reason

`FIRST_BLOCKING_GATE = DECISION_EXTERNALIZATION`

`FIRST_BLOCKING_SUBGATE = ENTITY_PLAYER_SELECTION_LEGAL_CHOICE_EXPORT`

At the exact Forge pin, authoritative `InputSelectEntitiesFromList<T extends GameEntity>.validChoices` can include Player entities. Only Card choices are exported over the current remote GUI boundary via `setSelectables(CardView,min,max)`. Player choices remain authoritative server-side and are only validated after `selectPlayer(PlayerView,ITriggerEvent)` returns from the client.

The remote protocol has no typed DecisionRequest and no monotonic request/decision token. `showPromptMessage` does not carry the exact legal Player set.

This is production-reachable: Kaervek the Merciless is a verified relevant opponent and its pinned Forge card semantics contain `ValidTgts$ Any`.

Therefore a **client-only strict adapter is rejected**: it cannot expose exact legal Player options without guessing from `GameView` / prompt text or reimplementing targeting rules. Both violate the architecture contract.

Forge Rules Core itself is **not rejected**. The failure is in the current human/remote decision boundary.

Current hard state:

```text
PRODUCTION_REACHABLE_UNSUPPORTED_DECISIONS = 1  # minimum proven count
EXACT_LEGAL_CHOICES_EXPORTED = FALSE
COMPLETE_TYPED_DECISION_REQUEST_RESPONSE = FALSE
STALE_RESPONSE_REJECTION_AT_BACKEND_PROTOCOL = FALSE
SILENT_FALLBACKS = NOT_ESTABLISHED_ZERO
```

XMage, phase.rs and Manabrew remain non-admissible for the already documented independent reasons; no candidate is promoted merely because the Forge client boundary failed.

Because this earliest boundary still fails, production-scoped hidden-information, explicit action/RNG tape replay, and per-card decision/visibility/replay safety cannot yet be fully qualified.

## Minimal next gate

Build a **research-only server-side typed Decision Export hook** at the authoritative Forge `Input` / `PlayerControllerHuman` boundary.

It must:

1. export exact authoritative choices, including Player entities;
2. export actor/principal, visibility scope, min/max and input-specific constraints;
3. attach a monotonic request token;
4. send a typed Decision Request to the trusted external-pilot adapter;
5. validate request token, actor, schema and selected options against the CURRENT authoritative Input before applying the response;
6. reject missing/null, stale, wrong-actor, malformed, illegal and timeout responses;
7. mark unknown Input kinds `UNSUPPORTED_DECISION_PATH`;
8. contain no prompt parsing, full-GameView legality inference, AI/default/first/random/pass/cancel fallback, or MTG rules reimplementation.

Only after this server-side subgate passes should the exact same boundary be used for pilot-visible hidden-information and fresh-process action/RNG tape replay qualification.

No production repository may be created from this state.
