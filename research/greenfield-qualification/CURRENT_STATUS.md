# Commander Simulator Next — Qualification Current Status

Date: 2026-08-27

## Source

- Research branch: `research/greenfield-engine-shootout-20260827`
- Original pre-closeout evidence head: `de0720380afa640a85b65011a525498cb6d76267`
- Forge exact pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- Strict-boundary closure run: `33112928078`
- Strict-boundary closure artifact: `9663315184` (`sha256:36446570c77c040b7a722d9a5cda5238fce3c0b00d689eb11c24c803f43c1a1c`)
- Prior strict runtime evidence reused without gameplay rerun: run `33095241142`, artifact `9656740763`.

## Freeze

`INITIAL_ARCHITECTURE_DECISION_FROZEN = FALSE`

`READY_FOR_GREENFIELD_BUILD = FALSE`

`READY_FOR_TRUSTED_REAL_DECK_SIMULATION = FALSE`

## Decision externalization — first step closed

The previously broad uncertainty around a client-only Forge Strict External Pilot Adapter is now **closed as FAIL**.

Dedicated evidence:

- `STRICT_EXTERNAL_PILOT_BOUNDARY_GATE.json`
- `STRICT_EXTERNAL_PILOT_BOUNDARY_GATE.md`
- `DECISION_CAPABILITY_REGISTRY.json`

### Exact proven blocker

`FIRST_BLOCKING_GATE = DECISION_EXTERNALIZATION`

`FIRST_BLOCKING_SUBGATE = ENTITY_PLAYER_SELECTION_LEGAL_CHOICE_EXPORT`

At the pinned Forge source, `InputSelectEntitiesFromList<T extends GameEntity>` retains authoritative `validChoices` server-side. It exports only Card choices through `setSelectables(CardView,min,max)`. Valid Player choices are not exported to the current remote GUI boundary, while the client response `selectPlayer(PlayerView,ITriggerEvent)` has no typed request/decision token.

This is production-reachable: the verified relevant opponent Kaervek the Merciless has pinned Forge semantics `ValidTgts$ Any`.

Therefore a client-only adapter cannot present exact legal Player choices to an external pilot without guessing from full `GameView` / prompt text or reimplementing targeting rules. Both violate the contract.

Current hard values:

```text
PRODUCTION_REACHABLE_UNSUPPORTED_DECISIONS = 1   # proven minimum
EXACT_LEGAL_CHOICES_EXPORTED = FALSE
COMPLETE_TYPED_DECISION_REQUEST_RESPONSE = FALSE
STALE_RESPONSE_REJECTION_AT_BACKEND_PROTOCOL = FALSE
SILENT_FALLBACKS = NOT_ESTABLISHED_ZERO
```

Forge Rules Core is **not disqualified**. The failure is the current human/remote decision boundary.

### Candidate adjudication

- Forge: broad mature rules/card runtime evidence remains strongest; current client-only remote boundary FAIL as above.
- XMage: run `33089884301` passes targeted Commander tests but explicitly records complete external-pilot runtime gate=false and principal-scoped external observation gate=false.
- phase.rs: strong targeted conformance; interaction source is externalizable but all required decisions are explicitly not externalized/tested.
- Manabrew: run `33090536113` passes concurrent 4P process isolation but exact-pin audit finds multiple first/default/pass fallbacks; production decision gate FAIL.

## Other mandatory gates

- Forge 2P–5P Commander runtime and exact RogShai runtime: previous PASS evidence retained, not rerun.
- Hidden information: NOT PASS. Forge raw transport run `33095565820` completed the game but exposed 74 hidden identities; pilot filtering cannot be promoted before the new server-side decision boundary exists.
- Semantic replay: NOT RUN to required action-tape + RNG-tape fresh-process A/B/C standard. Forge census explicitly says event-tape runtime unqualified.
- Process isolation: Manabrew candidate-specific concurrent 4P PASS; overall production gate cannot be promoted before a core/boundary is admissible.
- Actual-card manifest: INCOMPLETE merged Oracle-identity union; source control counts verified.
- Actual-card behavior coverage: INSUFFICIENT_EVIDENCE; source index/presence is not behavior support.
- Precon extraction: 11/11 exact 100-slot lists extracted successfully in run `33089467077`, artifact `9653672924`; Wizards remains content authority.
- Rules matrices A–T and C01–C22: INCOMPLETE as complete production-boundary matrices; prior passing targeted tests retained.
- Differential: INCOMPLETE under a common explicit action/RNG contract.
- License final decision: DEFERRED until technical architecture is admissible.

## Key domain controls

- Physically held unique identities: 1338.
- Operational own unique identities: 1007.
- RogShai exact 100, normalized hash `2b6258ae1c778784ed252bb46ff828343055177146634c77847506d33f4a4362`.
- Kaervek exact 100, deck hash `aa7a90a4e5cf32f40b1c9832d329aa03f6f7bf130f2d2e9c1e80d10e97c53c7a`.
- Dargo/Tymna theorycraft identities: 743.
- Unknown real opponent slots: at least 142; no synthetic promotion.

## Next action

The next qualification task is no longer another client-side RemoteClientGuiGame patch.

Implement a **research-only server-side typed Decision Export hook** at the authoritative Forge `Input` / `PlayerControllerHuman` boundary. It must export exact choices including Player entities, actor/principal, visibility/min/max/constraints and a monotonic request token, and validate token + actor + option membership before applying a response to the current Input object.

Do not parse prompts, infer legality from full `GameView`, use Forge AI/default/first/random fallbacks, or implement MTG targeting rules in the adapter.

Do not create `commander-simulator-next` before this and all downstream mandatory gates pass.
