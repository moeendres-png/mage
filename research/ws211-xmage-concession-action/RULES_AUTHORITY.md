# WS211 RULES_AUTHORITY

Source: official Wizards Comprehensive Rules, fetched live 2026-09-14 from
https://magic.wizards.com/en/rules.

- Document: "Magic: The Gathering Comprehensive Rules", effective **2026-08-07**
  (TXT build 20260819; DOCX/PDF builds 20260807).
- CURRENT_OFFICIAL_RULES_VERSION = CR-20260807 (effective 2026-08-07).
- Fresh official rules outrank the task summary; the material rules below were
  read verbatim from the fetched document.

## CR 104.3a (EXTERNALLY_RULE_VALIDATED)

> "A player can concede the game at any time. A player who concedes leaves the
> game immediately. That player loses the game."

CR104_3A_CONCEDE_ANY_TIME = CONFIRMED. No priority, step, stack, or
turn-control precondition. Immediacy is a game-rule property; the engine
marshals the state mutation to the serialized game thread (see
ARCHITECTURE_ADJUDICATION q06), which is the thread-safe realization of
"immediately" inside XMage's architecture.

## CR 723.6 (EXTERNALLY_RULE_VALIDATED)

> "The controller of another player can't make that player concede. A player
> may concede the game at any time, even if they are controlled by another
> player. See rule 104.3a."

- TURN_CONTROLLER_CAN_CONCEDE_FOR_CONTROLLED_PLAYER = FALSE (prohibited).
- CONTROLLED_PLAYER_SELF_CONCESSION = TRUE (retained under control).

## CR 101.1 (CODE_DERIVED context)

Concession is the single exception to the Golden Rules ("The only exception
is that a player can concede the game at any time (see rule 104.3a)").
No card or effect may remove the concession action.

## CR 800.4 family (CODE_DERIVED context, engine-owned)

Leave-the-game cleanup (owned objects leave, control-changing effects end,
stack objects not represented by cards cease, remaining controlled objects
exiled, priority passes) stays entirely inside existing `GameImpl.leave`;
WS211 reimplements nothing there.
