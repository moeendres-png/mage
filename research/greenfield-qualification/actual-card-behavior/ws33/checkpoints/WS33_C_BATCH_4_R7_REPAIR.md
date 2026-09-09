# WS33-C Batch 4 R7 repair (generic, C-local; source-verified timing)

REPAIR_BASE_HEAD = d7934168d6336d1090178bf279870ef258354399
REPAIR_BASE_TREE = 4c2ea4ea458d34e1e30aa884492395ac1bc12228
FORGE_PIN = 8c7e9afb8e6caee88644b94e25da5852e36f8928
PRIOR_RUN = 34385344654 (terminal FAIL, checkpoint
WS33_C_BATCH_4_RUN_34385344654_FAIL.md persisted BEFORE this repair)
BATCH_DIGEST_OLD = a294312c2015696e8e22131e3071368951be5c07e4fdc43757543116055983de
BATCH_DIGEST_NEW = b9aa07cec3b284ea75bada8b75f1a33b98c286daa7fc9717f64d0e76f39cacd0
COVERAGE_PROMOTION = FALSE
COVERAGE_MUTATED = FALSE
PARTITION_RETAINED = 11 EVIDENCED / 689 UNKNOWN (branch-owned)

## Timing semantics (source-verified at FORGE_PIN 2026-09-09, re-fetched)

- Kappa DBUnblockable / Gateway TrigUnblockable: DB$ Effect with NO
  Duration (card texts at pin) -> EffectEffect.resolve:319 addUntilCommand
  with null duration -> SpellAbilityEffect:925 else-branch
  game.getEndOfTurn().addUntil (player-independent until list).
- That list fires only on Phase.executeUntil() no-arg (Phase:101), which
  PhaseHandler runs in CLEANUP onPhaseBegin (discard/damage-reset block),
  NOT on entering END_OF_TURN (which runs only player-mapped
  executeUntil(playerTurn)).
- playUntilPhase stops on phase ENTRY (AITest:208-212), so an END_OF_TURN
  stop precedes expiry; a CLEANUP stop includes EndOfTurn.executeUntil()
  in the same mainLoopStep. Travel target END_OF_TURN -> CLEANUP is
  therefore required, not optional.
- Hildibrand MayPlay Duration UntilTheEndOfYourNextTurn ->
  EndOfTurn.registerUntilEnd/addUntilEnd (next turn): correctly beyond the
  window; no after-phase claimed (unchanged).

## Edits (all C-local; no shared Decision/overlay/checker/certifier changes)

1. ws33_c_batch_4_definitions.json: kappa-static expected 1->2 (setup
   via-move firing + fixture firing = 2 Command-zone effects remembering
   the same witness; artifact-proven actual=2). No card-name logic.
2. Ws33AbilitySubWitnessTest.java after-EOT block: playUntilPhase CLEANUP.
3. Same file: generic setup verification (every placed card in declared
   zone pre-fixture; fail-closed message) + graveyard side in
   rosterSnapshot (diagnostics-only; distinguishes SBA-destroyed from
   exiled/LKI/missing for the hildibrand silence branch).
4. Batch-4 needs no forced-singleton consultation: all
   expected_consultations [] unchanged (Blight singleton pattern was
   batch-2 scope; checker PASS confirms declaration shape).
5. Workflow BATCH_DIGEST -> b9aa07ce...; selection doc digest + kappa
   linked-count filled (was TBD / linked/1).

## Focused local gates (2026-09-09, this worktree)

- python py_compile c-campaign + 8 workflow overlay scripts: PASS.
- pilot certifier self-test: PASS; batch certifier self-test: PASS
  (26 cases incl. effect-static-accept + 20 fail-closed negatives).
- checker+preparer dry run vs /tmp/opencode/forge-pin (pin object
  present): CHECK=PASS PREPARE=PASS digest b9aa07ce rows=4 slots=4.
- workflow YAML parse: PASS (digest binds new value).
- javac syntax scan: 0 syntax-class errors (only missing-forge-deps
  resolution errors, expected without engine checkout): PASS.
- Full engine execution NOT run locally (replacement qualification runs
  in CI on frozen source).

## Next

Commit + push (triggers replacement run via c-campaign/workflow paths)
-> persist PENDING with resulting HEAD/TREE + RUN id -> poll ->
independent adjudication -> repartition on PASS.

TURN_STATUS = INTERRUPTED
TASK_COMPLETE = NO
