# WS211 ARCHITECTURE_ADJUDICATION (XHIGH read-first)

Verified against HEAD a9b9a4075f6f92b2ec1ba03557674b2bbd33d9fc.
Classification: DIRECTLY_VERIFIED where a native test proves it, else
CODE_DERIVED (static call-chain). Nothing below is assumed.

## 1. Normal client entry point

`GameController.sendPlayerAction(PlayerAction.CONCEDE, userId)` (Mage.Server)
maps `userId -> playerId` through `userPlayerMap` and calls
`Game.setConcedingPlayer(ownPlayerId)`. The concede button is therefore an
anytime async command bound to the sender's OWN player id. Test-harness
equivalent: `Game.concede(id)` + `GameImpl.checkConcede()` (TestPlayer).

## 2. Callable without priority — YES (DIRECTLY_VERIFIED)

`setConcedingPlayer` queues the id, dedups, and only nudges the current
priority player's dialog. Processing happens at the next `checkConcede`
(`checkStateAndTriggered`, post-`resolve`, direct game-thread call).
Tests: non-priority 2-player concede, 4-player B-concedes-on-D's-turn,
combat-step concede — all green.

## 3. Callable while controlled — YES for self (DIRECTLY_VERIFIED)

`setConcedingPlayer` explicitly branches on
`currentPriorityPlayer.getTurnControlledBy().equals(playerId)` as self-concede
with immediate dialog stop, as CR 723.6 requires. Test: controlled B
concedes self; green in 2-player and 4-player.

## 4. Identity distinction

- Core distinguishes PLAYER_ID vs TURN_CONTROLLER_ID
  (`getTurnControlledBy` / `turnController` / `isGameUnderControl`).
- Core does NOT know GUI/controller or match owner/user identity. That
  binding lives in the server layer (`GameController.userPlayerMap`).
- `Game.concede(UUID)` / `setConcedingPlayer(UUID)` carry the actor id only.
  Consequence: the CALLER (bridge/server) must bind actor == principal and
  never substitute the turn-controller id. Core offers no seat for
  substitution: every path removes exactly the passed id.

## 5. Game.concede(UUID) to multiplayer cleanup (CODE_DERIVED + tests)

`Game.concede` -> `Player.concede` -> `setConcedingPlayer` (queue/dedup/
signal) + `lost()` (synchronous loss mark) -> game-thread `checkConcede` ->
`leave(playerId)` (800.4a cleanup: owned permanents out, control effects
end, leaver's stack objects cease, remaining controlled permanents exiled,
exile/command-zone sweep, priority/turn advance) -> `checkIfGameIsOver`
(one player left ends the game, winner declared).

## 6. Sync model — MIXED by design (CODE_DERIVED)

Loss marking is synchronous; leave cleanup is marshalled to the game thread.
Semantically immediate within the serialized engine; no cross-thread
mutation. No evidence of queue delay past meaningful Rules actions
(checkConcede runs inside state/trigger processing and post-resolve).

## 7. Duplicates — cannot queue (DIRECTLY_VERIFIED)

`setConcedingPlayer` contains-guard dedups; `leave()` re-guards `hasLeft`.
Test `testDuplicateConcedeSingleCleanup` + 4-player duplicate test: single
leave, winner declared once, second drain is a no-op.

## 8/9. Lost/left/unknown — PRE-FIX: stale winner corrupted (DIRECTLY_VERIFIED)

Pre-change `Game.concede` accepted `!hasLost`, so a stale post-game request
for the WINNER set `loses=true` on the winner (`hasWon()` flipped false).
Left/lost/unknown were already harmless (early returns / null ignore).
Remediation: narrow guard on the external seam only (see below).

## 10. Core change necessary? — YES, narrow (decision)

Execution seam sufficient; availability query missing (no `canConcede`
anywhere in core). Classification: CORE_AVAILABILITY_SURFACE_REQUIRED plus
one evidenced seam guard => CORE_CONCESSION_SEMANTICS_REMEDIATION_REQUIRED
scoped to `Game.concede` stale acceptance.

## 11. Narrow predicate vs broad surface — NARROW (decision)

`Game.canConcede(UUID)->boolean`. The `PlayerAction` enum is
priority-dialog scoped and no generic anytime-action surface exists; building
a full legal-action framework for one boolean would violate smallest-design.
Documented in code javadoc on `Game.canConcede`.

## 12. Action model — PLAYER_INITIATED_ACTION (decision)

CONCESSION_ACTION_MODEL = PLAYER_INITIATED_ACTION. No blocking Yes/No
callback exists or is added. WS204's proposed
`decision_class=concede` hook is SUPERSEDED (see WS204_IMPACT_ADJUDICATION).

## Production change (minimal, final)

1. `Game.canConcede(UUID)` + `GameImpl` impl: `playerId != null &&
   !hasEnded() && player != null && player.isInGame()`. No RNG, no priority/
   step/stack/control requirements.
2. `GameImpl.concede` guard: reject when `!canConcede(playerId)` (stale/
   unknown/post-game fail closed; fixes the evidenced winner corruption).
   Internal flows (`Player.concede`, `setConcedingPlayer`, quit/timeout/
   forced-loss) untouched.
3. All `Game` implementors extend `GameImpl`: no other implementor updates.
