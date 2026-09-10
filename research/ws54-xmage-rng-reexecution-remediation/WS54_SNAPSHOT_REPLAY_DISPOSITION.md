# WS54 Snapshot / Replay Disposition

## Source facts (CODE_DERIVED)

- `Game.copy()` (`GameImpl` copy constructor) duplicates live `GameRandom` state for
  simulation isolation (`createSimulationForAI`, `createSimulationForPlayableCalc`).
  It is a fork for search, not a restore point: sim RNG is never written back.
- Rollback/bookmark facilities (`GameImpl.savedStates`, `gameStates`,
  `gameStatesRollBack`, `GameState.copy`) persist and restore GAME STATE only. No RNG
  offset is stored or restored: after a rollback the Rules stream continues
  forward-only from its live position.
- No facility rewinds, re-seeds, or replays RNG consumption. Post-rollback
  determinism is therefore NOT claimed.

## Terminal disposition

- `ARBITRARY_SNAPSHOT_RESTORE_REPLAY = NOT_QUALIFIED`
- `START_TO_FINISH_SEEDED_SEMANTIC_REEXECUTION = PASS` (bounded contract: same engine
  build + same semantic input + same explicit seed + same journaled decisions ->
  same Rules-random choices -> same event sequence -> same terminal semantic state)

These are different capabilities and must not be conflated. Replay = fresh start
with the recorded seed + decision log, never mid-decision snapshot resume.

## Capability ledger (this workstream)

- `ENGINE_DETERMINISM`: PASS (P1/P2 unit + game).
- `CONTROLLED_RULES_RNG`: PASS (game-scoped authority, closed call-site gate).
- `RNG_ISOLATION`: PASS (P3/P4 unit + game).
- `REPRODUCIBLE_REEXECUTION`: PASS (P5 fresh-process unit + game).
- `SEMANTIC_REPLAY_SUPPORTABILITY`: PASS for start-to-finish journaled reexecution
  (explicit seed + decision log + forward-only consumption).
- `ARBITRARY_SNAPSHOT_RESTORE_REPLAY`: NOT_QUALIFIED (honest scope; no rewind
  semantics invented).
