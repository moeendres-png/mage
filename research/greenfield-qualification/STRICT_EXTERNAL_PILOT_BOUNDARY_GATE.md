# Forge Strict External-Pilot Boundary Gate — FINAL CLOSURE

Date: 2026-08-27

- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- Closure run: `33112928078`
- Closure artifact: `9663315184`
- Reconciled prior runtime run: `33095241142`
- Reconciled prior artifact: `9656740763`
- Gate: `DECISION_EXTERNALIZATION`
- Status: **FAIL**
- Evidence: CODE-DERIVED + RUNTIME-RECONCILED; no gameplay rerun.

## Exact blocker

`InputSelectEntitiesFromList<T extends GameEntity>` keeps the authoritative `validChoices` server-side. It exports only Card members through `setSelectables(CardView, min, max)`. Player members remain server-side and are validated only after a client sends `selectPlayer(PlayerView, ITriggerEvent)`.

The pinned remote protocol has neither a typed `DecisionRequest` nor a monotonic request/decision token. `showPromptMessage` carries the acting `PlayerView`, prompt text and an optional `CardView`, but no exact legal Player collection.

This is production-reachable: pinned Forge semantics for `Kaervek the Merciless` contain `ValidTgts$ Any`; project domain evidence classifies Kaervek as a verified relevant opponent.

A client-only adapter therefore cannot send **exact legal Player options** to an external pilot without guessing from `GameView` / prompt text or reimplementing targeting rules. Both are forbidden by the qualification contract.

## Prior runtime reconciliation

Existing run `33095241142` was reused, not rerun. It proves the research patch rejected null/wrong-type blocking returns, but the remote clients were still `HeadlessNetworkClient` auto-choice controllers and 2P–5P did not establish a complete external-pilot stream. In 2P the trace reached `setSelectables` followed by `tempShowZones` and the game remained incomplete.

## Adjudication

- Forge Rules Core: **not disqualified**.
- Stock remote GUI boundary: **not qualified**.
- Client-only strict adapter: **insufficient by construction**.
- `PRODUCTION_REACHABLE_UNSUPPORTED_DECISIONS = 1` — minimum proven count, not a claim that only one exists.
- `EXACT_LEGAL_CHOICES_EXPORTED = FALSE`.
- `COMPLETE_TYPED_DECISION_REQUEST_RESPONSE = FALSE`.
- `STALE_RESPONSE_REJECTION_AT_BACKEND_PROTOCOL = FALSE`.
- `SILENT_FALLBACKS = 0`: **not established**.

## Minimal required change

Add a **server-side typed Decision Export hook** at the authoritative `Input` / `PlayerControllerHuman` boundary. It must publish:

- exact `validChoices`, including Player entities;
- actor/principal;
- min/max and other choice constraints;
- visibility scope;
- monotonic request token;
- typed response schema.

Before applying a response to the existing Forge input object, the trusted adapter must validate request token, actor, schema and selected options against the authoritative current input.

No prompt parsing, no inference from full `GameView`, no Forge AI fallback, no first/default/random fallback, and no MTG rules reimplementation.

This is the next technical blocker. The previous broader `DECISION_EXTERNALIZATION` uncertainty is now closed to this exact failure.
