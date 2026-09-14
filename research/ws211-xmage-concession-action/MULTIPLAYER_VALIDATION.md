# WS211 MULTIPLAYER_VALIDATION (DIRECTLY_VERIFIED)

Harness: native `FreeForAll` (RangeOfInfluence.ALL), 4 players
(order A -> D -> C -> B), real running games, no mocks.

- testFourPlayerConcedeContinuesWithThree: B concedes turn 2 (no priority).
  B out at END_TURN; A/C/D in-game turn 3; game NOT ended at turn 4.
  FOUR_PLAYER_CONTINUATION = PASS.
- testFourPlayerControlledSelfConcede: D controlled by A concedes self.
  Exactly D leaves; A/B/C continue; game NOT ended. PASS.
- testFourPlayerControllerConcedeRemovesOnlySelf: A (controlling B) concedes.
  Exactly A leaves; B/C/D continue; game NOT ended. PASS.
- testFourPlayerDuplicateAndStaleRequests: duplicate queue + repeat + unknown
  actor. Exactly C leaves; A/B/D continue; game NOT ended. PASS.
- testFourPlayerConcedeClearsLeaversStackObjects: C's spell on stack at
  concede time; stack empty after `checkConcede`; C out; game continues. PASS.
  (2-player skips object cleanup once the game ends — pre-existing intended
  early return in `leave()`, unchanged.)

2-player (DIRECTLY_VERIFIED): priority concede, non-priority concede,
combat (declare-blockers) concede, nonempty-stack concede — conceder leaves,
survivor wins, game ends. NON_PRIORITY_CONCESSION,
STACK_NONEMPTY_CONCESSION, COMBAT_CONCESSION = PASS.

3/5-player: native harness 2P/4P coverage used; FFA engine paths are
player-count generic (leave/cleanup iterate state, no count-specific
branches), so no proportionate 3/5 infrastructure was built. 3/5 = UNKNOWN
(explicitly not claimed).
