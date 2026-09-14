# WS211 PLAYER_CONTROL_AUTHORITY (DIRECTLY_VERIFIED)

Rules: CR 723.6 — controller cannot concede for the controlled player; the
controlled player may concede themself at any time.

Engine facts (CODE_DERIVED):

- Control state: `turnController` / `turnControllers` / `isGameUnderControl`
  on PlayerImpl; established natively by `controlPlayersTurn`
  (e.g. Mindslaver-class effects). Tests establish the identical fields
  directly because `controlPlayersTurn` refuses AI controllers (product
  limitation "not supported yet", not Rules authority).
- Authorization boundary: `GameController` binds network user -> own player
  id (`userPlayerMap`); the CONCEDE command can only ever submit the
  sender's own id. No network authentication is duplicated in Rules Core.
- Core invariant: concession takes exactly one actor id and removes exactly
  that actor. There is no core API shaped "X concedes Y".

Native proofs (2-player + 4-player, green):

- Controlled B concedes self (actor B) => B leaves, controller unaffected.
- Controller A concedes (actor A) while controlling B => exactly A leaves;
  B remains in game (2-player: B wins; 4-player: B/C/D continue, no game end).
- `canConcede` is true for both controller and controlled player
  independently; availability never authorizes cross-actor submission.

Bridge obligation (recorded for the Lab successor): bind CONCEDE to the
principal's own player id; never substitute `getTurnControlledBy()`.
