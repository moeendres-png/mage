# WS33-C Batch 4 run 34385344654 terminal FAIL (independently adjudicated)

RUN = 34385344654
JOB = 102580086778 (completed/failure)
WORKFLOW = WS33-C AbilitySub batch witness (production-parent)
WORKFLOW_FILE_SOURCE_HEAD = 29fbd77fb052e03af2c01329dd5097d2fa78f551
WORKFLOW_FILE_SOURCE_TREE = 489500301292c8faeadfb1c574f4e94d065e3490
FORGE_PIN = 8c7e9afb8e6caee88644b94e25da5852e36f8928
ARTIFACT = 10117578494 (ws33-c-abilitysub-batch-34385344654, expired=false)
BATCH_ID = WS33_C_BATCH_4
BATCH_DIGEST = a294312c2015696e8e22131e3071368951be5c07e4fdc43757543116055983de
GATE = generated/evidence/WS33_C_BATCH_GATE.json NOT PRODUCED (Record step failed; no seal)
COVERAGE_PROMOTION = FALSE
COVERAGE_MUTATED = FALSE

## Independent verification (from immutable artifact bytes, local download 2026-09-09)

- Plan digest matches PENDING: a294312c...; case_rows=4, path_slots=4.
- abilitysub-record-diagnostics.jsonl has exactly 3 rows, 0 record-success markers.
  No records/ directory, no evidence seal. Workflow failure is real, not infra.
- Materialization succeeded (plan digest match, 3 executions ran, assertions
  evaluated). No ModuleNotFoundError. Prior coordinator-import concern stays
  superseded.

## Per-execution verdicts (all 3 batch-4 paths remain UNKNOWN; 0 new EVIDENCED)

1. kappa-etb-other (634a4b2d sub-link + 998516b9 terminal, same execution):
   `semantic postcondition failed: kappa-static expected=1 actual=2`.
   Pair matching REACHED (failure is post-match assertion value only).
   Root cause class: FIXTURE_DEFECT (expected count wrong; setup via-move
   trigger drained by settleSetup creates effect 1, fixture Sol Ring entry
   creates effect 2; both remember same witness object). Engine behaved
   correctly. Repair: expected 1->2 (generic count semantics, no card hack).
   Path verdicts: UNKNOWN + FIXTURE_DEFECT.
2. gateway-etb-other (998516b9 shared terminal):
   `lifecycle rollback failed: gateway-static-after-eot expected=0 actual=1`.
   Active-phase assertion PASSED (effect created, count==1); absence check
   after playUntilPhase(END_OF_TURN) still sees 1.
   Root cause class: HARNESS_DEFECT (travel target).
   Source-verified at FORGE_PIN this session: DB$ Effect with no Duration
   (kappa/gateway card texts) -> EffectEffect.resolve:319 addUntilCommand
   with null duration -> SpellAbilityEffect:925 else-branch
   game.getEndOfTurn().addUntil (player-independent until list) ->
   fires only on Phase.executeUntil() no-arg, which PhaseHandler runs in
   CLEANUP onPhaseBegin (discard/damage-reset block), NOT on entering
   END_OF_TURN (which runs only player-mapped executeUntil(playerTurn)).
   playUntilPhase stops on phase ENTRY (AITest:208-212), so END_OF_TURN
   entry precedes expiry. Repair: travel target END_OF_TURN -> CLEANUP
   (CLEANUP entry already includes the EndOfTurn.executeUntil() in the
   same mainLoopStep; PhaseType.CLEANUP verified at pin).
   Path verdict: UNKNOWN + HARNESS_DEFECT (shared path; no new count).
3. hildibrand-dies (2dd428f9 terminal MayPlay):
   `terminal root resolution not observed ... parents=[DamageAll x2 FOREIGN]
   children=[DamageAll FOREIGN] roster=[p2:Thunder Dragon;p1:]`.
   Thunder DamageAll observably resolved (foreign, correctly unattributed;
   thunder's own path already evidenced, not claimed). Hildibrand absent
   from battlefield roster; graveyard state NOT recorded (roster is
   battlefield-only) so exile-vs-graveyard-vs-LKI is unproven.
   Root cause class: UNKNOWN (pending setup-verification + graveyard
   roster diagnostics; R7-3). No engine defect evidenced. No Rules-Core
   defect claimed.
   Path verdict: UNKNOWN + UNKNOWN (cause pending R7-3 diagnostics).

## Preserved prior evidence (immutable, unaffected)

- Batch-2 PASS run 34353935136 (artifact 10105006299): 11 EVIDENCED /
  689 UNKNOWN partition stands. This FAIL adds nothing and removes nothing.
- 2 shared diversity slots (banshee/snuffers on thunder path) unaffected.

## Evidence classification

- Run/job/artifact/diagnostic bytes: DIRECTLY_VERIFIED.
- addUntilCommand default + Phase expiry + playUntilPhase entry semantics:
  CODE_DERIVED from pin source (files re-fetched 2026-09-09:
  EffectEffect_pin.java:319, SpellAbilityEffect_pin.java:919-925/925-...,
  Phase_pin.java:92-104, PhaseHandler_pin onPhaseBegin CLEANUP block +
  mainLoopStep:1039+, AITest_pin2.java:208-212, PhaseType_pin CLEANUP,
  kappa/gateway card texts at pin).
- No new TECHNICALLY_CONFORMANT paths from this run.

## Exact next action

Apply generic R7 repairs only (no card-name hacks, no shared Decision
changes): (1) kappa-static expected 1->2; (2) after-EOT travel target
END_OF_TURN->CLEANUP; (3) hildibrand setup verification + graveyard
roster diagnostics; (4) confirm batch-4 needs no forced-singleton
consultation (all expected_consultations [] stay; Blight pattern was
batch-2 scope). Then focused local gates -> commit/push -> PENDING ->
replacement run.

TURN_STATUS = INTERRUPTED
TASK_COMPLETE = NO
