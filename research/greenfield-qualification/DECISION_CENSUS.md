# Decision Census — Closeout v2

Status: **FAIL; production decision gate not passed**.

## Forge

Forge remains the strongest broad Rules/Card backend candidate, but the previously uncertain Strict External Pilot question is now narrowed to a directly proven structural failure at the current remote GUI boundary.

Closure evidence:

- exact Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`;
- prior strict runtime run: `33095241142`, artifact `9656740763` — reused, not rerun;
- final boundary-closure run: `33112928078`, artifact `9663315184`;
- dedicated evidence: `STRICT_EXTERNAL_PILOT_BOUNDARY_GATE.json/.md`;
- machine-readable registry: `DECISION_CAPABILITY_REGISTRY.json`.

### Proven failure

`InputSelectEntitiesFromList<T extends GameEntity>` holds exact authoritative `validChoices` on the server. It exports only Card choices through `setSelectables(CardView,min,max)`. Player choices are not exported to the remote GUI. The remote client can send `selectPlayer(PlayerView,ITriggerEvent)`, but the protocol has no typed DecisionRequest and no monotonic request token.

Therefore a **client-only** strict adapter cannot provide an external pilot with exact legal Player options without guessing from `GameView` / prompt text or reproducing targeting rules. Both are prohibited.

This path is production-reachable: Kaervek the Merciless is a verified relevant opponent and its pinned Forge semantics use `ValidTgts$ Any`.

Current minimum hard-gate result:

```text
PRODUCTION_REACHABLE_UNSUPPORTED_DECISIONS = 1
EXACT_LEGAL_CHOICES_EXPORTED = FALSE
COMPLETE_TYPED_DECISION_REQUEST_RESPONSE = FALSE
STALE_RESPONSE_REJECTION_AT_BACKEND_PROTOCOL = FALSE
SILENT_FALLBACKS = NOT_ESTABLISHED_ZERO
```

The count `1` is a proven minimum, not a claim that only one unsupported decision kind remains.

Forge Rules Core itself is **not disqualified**. The failure is in the current human/remote decision boundary.

## Other candidates

- **XMage:** targeted run `33089884301` remains useful Rules evidence, but its own census records `complete_external_pilot_runtime_gate=false` and `principal_scoped_external_observation_runtime_gate=false`.
- **phase.rs:** interaction surface is source-externalizable, but all required decisions are explicitly not externalized-and-tested.
- **Manabrew:** run `33090536113` found current exact-pin silent/default/first-choice fallbacks; production decision gate FAIL.

## Exact next technical subgate

`FIRST_BLOCKING_GATE = DECISION_EXTERNALIZATION`

`FIRST_BLOCKING_SUBGATE = ENTITY_PLAYER_SELECTION_LEGAL_CHOICE_EXPORT`

The smallest admissible change is a server-side typed Decision Export hook at the authoritative Forge `Input` / `PlayerControllerHuman` boundary. It must export exact choices including Player entities, actor, visibility/min/max/constraints and a monotonic request token; the trusted adapter must validate token, actor and selected options before applying the response to the current Input object.

No prompt parsing, full-GameView inference, Forge AI, first/default/random fallback, or MTG rules reimplementation is acceptable.
