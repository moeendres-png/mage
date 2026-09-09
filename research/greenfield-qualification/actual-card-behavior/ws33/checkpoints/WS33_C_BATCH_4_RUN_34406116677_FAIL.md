# WS33-C Batch 4 R9-fix run 34406116677 terminal FAIL (independently adjudicated)

RUN = 34406116677
JOB = 102649380734 (completed/failure)
WORKFLOW = WS33-C AbilitySub batch witness (production-parent)
WORKFLOW_SOURCE_HEAD = d26be3b06c57e0d5a28ea5ef003621c3fc1639f1
WORKFLOW_SOURCE_TREE = 26378e0a25d684dc0babd7732ab71e18622dd2e3
FORGE_PIN = 8c7e9afb8e6caee88644b94e25da5852e36f8928
ARTIFACT = 10125467422 (ws33-c-abilitysub-batch-34406116677)
BATCH_ID = WS33_C_BATCH_4
BATCH_DIGEST = b9aa07cec3b284ea75bada8b75f1a33b98c286daa7fc9717f64d0e76f39cacd0
GATE = generated/evidence/WS33_C_BATCH_GATE.json NOT PRODUCED (2/3 markers)
COVERAGE_PROMOTION = FALSE
COVERAGE_MUTATED = FALSE

## Independent verification (immutable artifact bytes, local 2026-09-09)

- Plan digest matches PENDING (b9aa07ce...); diagnostics exactly 1 row.
- kappa-etb-other: 7/7 record assertions PASS, TECHNICALLY_CONFORMANT.
- gateway-etb-other: 4/4 record assertions PASS, TECHNICALLY_CONFORMANT.
- hildibrand-dies: NEW signature vs R7/R8 (R9 drain WORKED):
  observations now include Child{seq=3 id=71 api=Effect host=Hildibrand
  parent=-1 root=71} + Parent{seq=4 id=71 ... sub=null} + Parent{seq=5
  id=72 ...} (envelope, no child, stays unattributed per standing rule).
  The (71,71) pair meets every terminal condition EXCEPT host reference:
  both ends [FOREIGN] (host != sourceRef[0]).

## Root cause (CODE_DERIVED at FORGE_PIN; HARNESS_DEFECT, mechanism proven)

- GameAction.changeZone copies cards LEAVING the battlefield
  (`copied = new CardCopyService(c).copyCard(false)`); cards entering
  keep identity (`copied = c`). The graveyard Hildibrand hosting the
  fired dies trigger is therefore a different Java object than the
  battlefield-placed sourceRef[0]. Reference equality cannot bridge a
  leaves-battlefield trigger path. No engine defect: copy-on-leave,
  trigger fire, drain, and resolution are all correct engine behavior.
- Stable bridge exists at pin: CardCopyService.copyCard(false) preserves
  the engine Card ID (`getCard(paper, owner, copyFrom.getId())`);
  Game.nextCardId() is per-game unique monotonic; GameEntity.getId() is
  public and construction-set. The resolving host copy carries the
  placed card's ID. EffectEffect RememberObjects$ Self likewise
  remembers the resolving (copy) host, so the assertion linkage needs
  the same bridge. Numeric IDs are engine-issued piece identity, never
  mutable names (name gating stays forbidden).
- Path 2dd428f9 verdict: UNKNOWN + HARNESS_DEFECT (identity rule
  too narrow for cross-zone copies).

## Per-execution verdicts

1. kappa-etb-other: EVIDENCED-CANDIDATE (promotion withheld, unsealed).
2. gateway-etb-other: EVIDENCED-CANDIDATE shared (promotion withheld).
3. hildibrand-dies: UNKNOWN + HARNESS_DEFECT (above).

## Partition (unchanged)

- 11 EVIDENCED / 689 UNKNOWN retained. No promotion from an unsealed
  batch (batch-2 precedent).

## Evidence classification

- Run/job/artifact/diagnostic/record bytes: DIRECTLY_VERIFIED.
- Copy-on-leave + id preservation + trigger-host chain: CODE_DERIVED
  (pin GameAction.changeZone, CardCopyService, Game.nextCardId,
  GameEntity.getId, TriggerHandler.runSingleTriggerInternal,
  EffectEffect RememberObjects).
- No new promotions from this run.

## Exact next action (R10, generic harness-only)

Piece-identity bridge: hostIsSource and remembered-linkage accept
reference equality OR equal engine Card IDs (helper isSamePiece;
same-object implies same-ID so all passing executions are unaffected).
No names, no definitions/workflow/digest/consultation changes
(digest-neutral). Then gates -> commit/push -> PENDING -> replacement run.

TURN_STATUS = INTERRUPTED
TASK_COMPLETE = NO
