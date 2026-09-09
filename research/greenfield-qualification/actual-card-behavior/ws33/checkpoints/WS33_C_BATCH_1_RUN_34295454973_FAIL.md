# WS33-C Batch 1 replacement run 34295454973 terminal FAIL (adjudicated)

RUN = 34295454973
JOB_CONCLUSION = failure (step "Execute batch Record"; Tests 3, 1 failure)
SOURCE_HEAD = fbdb82a560
SOURCE_TREE = 00c93603b859f08c7284f2b926bbe05d1c3b1f56
FORGE_PIN = 8c7e9afb8e6caee88644b94e25da5852e36f8928
ARTIFACT = ws33-c-abilitysub-batch-34295454973 (diagnostics + logs)
COVERAGE_PROMOTION = FALSE

## Per-execution results (DIRECTLY_VERIFIED from run log)

Tests run 3 (campaign + 2 negatives); both direct-child negatives PASSED.
Campaign: 0/7 executions recorded; diagnostics:

- cloudblazer/rager/shimmercreep/bane: UNEXPECTED_DECISION_REQUIREMENT
  sites=[chooseSpellAbilityToPlay x2] (uniform 2x, all ETB cases incl. pilot).
- chopper: same 2x plus chooseSingleEntityForEffect x1.
- cap-hero-etb: "actual trigger fixture did not reach the stack".
- gnarlbark-eot: "actual end-of-turn trigger did not reach the stack".

## Classification (all fail-closed, no false PASS)

1. TRIPWIRE_FUNCTIONAL (not a defect): the new tripwire caught real AI
   controller invocations. Uniform 2x chooseSpellAbilityToPlay across all
   ETB executions suggests incidental game-flow queries, but the CALLER is
   not yet evidenced. Class: UNEXPECTED_DECISION_REQUIREMENT pending
   caller attribution (UNKNOWN, not FAIL).
2. CHOPPER_SINGLE_ENTITY (needs caller evidence): one
   chooseSingleEntityForEffect inside the chopper window. Could be Attach
   machinery or incidental flow. UNKNOWN pending caller attribution.
3. CAP_FIXTURE (harness/diagnosability gap): trigger never waited or never
   stacked; current message does not distinguish the leg. UNKNOWN pending
   split diagnostics.
4. GNARLBARK_EOT_RACE (fixture-flow gap): EOT trigger likely auto-resolved
   during playUntilPhase travel (observers armed, evidence possibly already
   recorded) while the fixture still demands post-travel waiting. Harness
   must tolerate travel-resolution; link matching remains the real gate.

NOT engine defects (no production behavior demonstrated incorrect). No Sol
escalation. Pilot evidence (runs 34289134780/34289612464) stands uninvalidated.

## Repair plan (diagnostic revision R2, then targeted R3)

R2 (this turn): capture caller frames test-side in tripwire events; split
fixture legs with distinct messages + zone/stack snapshot; EOT fixture
tolerates travel-resolution (matching decides); diagnostics enriched with
parent/child counts and hits-with-callers; tripwire stays fail-closed.
R3 (next): classify sites from caller evidence (scope arming to resolution
segments if incidental; investigate chopper site; fix cap leg).

EVIDENCED_PATH_COUNT = 1 (unchanged)
REMAINING_UNKNOWN_COUNT = 699 (unchanged)

## Exact next action

Commit FAIL + R2 harness revision, push, register replacement PENDING,
read caller evidence from diagnostics, then R3.

TURN_STATUS = INTERRUPTED
TASK_COMPLETE = NO
