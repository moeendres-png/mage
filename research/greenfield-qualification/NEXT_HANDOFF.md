# Commander Simulator Next — Next Handoff

Date: 2026-08-27

## Entry state

`INITIAL_ARCHITECTURE_DECISION_FROZEN = FALSE`

Do not start the production repository and do not inspect Commander-Lab as an architecture prior.

Read first:

1. `CURRENT_STATUS.md`
2. `STRICT_EXTERNAL_PILOT_BOUNDARY_GATE.md` / `.json`
3. `DECISION_CAPABILITY_REGISTRY.json`
4. `DECISION_CENSUS.md` / `.json`
5. `EXISTING_RUN_RECONCILIATION.md`
6. `HIDDEN_INFORMATION_ASSAY.md` / `.json`
7. `RNG_INVENTORY.md`
8. `ACTUAL_CARD_REQUIREMENT_MANIFEST.md` / `.json`
9. `ACTUAL_CARD_COVERAGE.md` / `.json`
10. `FINAL_ENGINE_SCORECARD.md`
11. `FINAL_ARCHITECTURE_DECISION.md`

## Closed step

The client-only Forge Strict External Pilot Boundary question is no longer `INSUFFICIENT_EVIDENCE`.

Closure run `33112928078`, artifact `9663315184` (`sha256:36446570c77c040b7a722d9a5cda5238fce3c0b00d689eb11c24c803f43c1a1c`) completed successfully as an evidence-producing workflow and machine-readably adjudicated the qualification gate as **FAIL**.

It reused prior strict runtime run `33095241142` / artifact `9656740763`; no 2P–5P gameplay baseline was rerun.

## Exact first blocking subgate

`FIRST_BLOCKING_GATE = DECISION_EXTERNALIZATION`

`FIRST_BLOCKING_SUBGATE = ENTITY_PLAYER_SELECTION_LEGAL_CHOICE_EXPORT`

At Forge pin `8c7e9afb8e6caee88644b94e25da5852e36f8928`:

- authoritative `InputSelectEntitiesFromList<T extends GameEntity>.validChoices` can contain Player entities;
- only Card members are exported through `setSelectables(CardView,min,max)`;
- `showPromptMessage` does not carry a legal Player collection;
- client `selectPlayer(PlayerView,ITriggerEvent)` carries no request/decision token;
- `ProtocolMethod` contains no typed `DecisionRequest` and no monotonic request/decision token;
- server-side `selectEntity` correctly validates against authoritative `validChoices`, but the external pilot cannot see that exact legal Player set at the current remote boundary.

Production reachability is proven by the relevant exact Kaervek profile: pinned Forge semantics for `Kaervek the Merciless` use `ValidTgts$ Any`.

Hard state:

```text
PRODUCTION_REACHABLE_UNSUPPORTED_DECISIONS = 1  # proven minimum
EXACT_LEGAL_CHOICES_EXPORTED = FALSE
COMPLETE_TYPED_DECISION_REQUEST_RESPONSE = FALSE
STALE_RESPONSE_REJECTION_AT_BACKEND_PROTOCOL = FALSE
SILENT_FALLBACKS = NOT_ESTABLISHED_ZERO
```

Forge Rules Core is not rejected. A **client-only** adapter is rejected.

## Exact next qualification task

Build a research-only **server-side typed Decision Export hook** at the authoritative Forge `Input` / `PlayerControllerHuman` boundary.

Minimum contract:

```text
Authoritative current Input
-> actor/principal
-> exact legal choices
-> min/max + input-specific constraints
-> visibility scope
-> monotonic request token
-> trusted adapter
-> external pilot
-> typed response
-> validate token + actor + schema + option membership against CURRENT Input
-> apply through existing Forge Input/controller path
```

Required fail-closed tests before this subgate can pass:

- valid Player choice round-trip from authoritative `validChoices`;
- invalid Player not in `validChoices` rejected;
- wrong actor rejected;
- stale request token rejected after Input changes;
- malformed/missing response rejected;
- timeout invalidates the game/qualification path;
- exact same mechanism for Card/entity selections without relying on prompt parsing;
- no AI/default/first/random/pass/cancel fallback;
- unknown Input decision kind -> `UNSUPPORTED_DECISION_PATH`.

Do not derive legal options from prompt text or the complete `GameView`. Do not copy MTG targeting legality into the adapter; Forge's authoritative current Input remains the source of legality.

Existing evidence not to rerun:

- Forge broad 2P–5P and RogShai baseline PASS.
- Forge census/RNG run `33095873712`, artifact `9656344793`.
- Forge raw hidden transport run `33095565820`, artifact `9656277015`, 74 hidden identities.
- Forge old strict runtime run `33095241142`, artifact `9656740763`.
- Forge strict boundary closure run `33112928078`, artifact `9663315184`.
- XMage targeted-v2 run `33089884301`, artifact `9655841512`.
- phase.rs targeted run `33078715204`, artifact `9649312620`.
- Manabrew isolation-only run `33090536113`, artifact `9654315901`.
- Precon extraction run `33089467077`, artifact `9653672924`.
- Forge neutral card index run `33090672334`, artifact `9654200891`.

Only after the server-side Decision Export subgate passes should hidden-information testing be rerun through that exact boundary, followed by action+RNG tape replay and actual-card behavior admission.
