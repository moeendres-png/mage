# WS33-C R4 diagnostic run 34298583103 terminal FAIL (adjudicated)

RUN = 34298583103
JOB_CONCLUSION = failure (step "Execute batch Record")
SOURCE_HEAD = d8fea35c4c
FORGE_PIN = 8c7e9afb8e6caee88644b94e25da5852e36f8928
ARTIFACT = ws33-c-abilitysub-batch-34298583103 (diagnostics + logs)
COVERAGE_PROMOTION = FALSE

## Decisive event dumps obtained (purpose achieved)

Cloudblazer re-witness (representative; all ETB executions share the shape):
- Child seq0 id14 GainLife parent=-1 root=14 (trigger root is itself an
  AbilitySub); Parent seq1 id14 sub=DBDraw; Child seq2 id15 Draw parent=14;
  Parent seq3 id15 sub=null; Parent seq4 **id16 GainLife sub=DBDraw** with NO
  child event parented to 16.
- So a second GainLife ability object resolved its effect without any
  observed sub-resolution. Engine self-resolution by effects excluded by pin
  source inspection (no effect calls AbilityUtils.resolve/resolveSubAbilities).
- Pilot life was exactly +2 with the identical flow, so at most one of the
  two resolutions executed GainLife-for-actor-2. Open hypotheses: (a)
  second resolution credited the opponent (+2, never asserted); (b) second
  resolution ran to +4 total (contradicts pilot, unlikely); (c) second
  resolution effect-inert (e.g. activating player not in game).
- Gnarlbark EOT: phase=END_OF_TURN turn=p2(=actor) game_over=false
  stack_empty=true children=0 — EOT reached on actor's turn with empty
  stack and the trigger never resolved nor waited. Cause still open.

Both direct-child negatives PASSED again.

## Classification

- DUPLICATE_PARENT_RESOLUTION (engine-behavior question, outcome impact
  unknown until semantic snapshot read).
- GNARLBARK_SILENT_EOT (fixture/trigger question, open).
- No engine defect demonstrated yet (no incorrect production behavior
  proven). No Sol escalation until R5 data lands.

EVIDENCED_PATH_COUNT = 1 / REMAINING_UNKNOWN_COUNT = 699 (unchanged)

## Exact next action (R5, diagnostics-only, digest unchanged)

Parent events carry activating player; matching failures include semantic
snapshots (both lives + hand deltas). Rerun, read outcome impact, then
targeted R6 (pair-matching by object relation if inert; Sol escalation
with pristine evidence if outcome-affecting).

TURN_STATUS = INTERRUPTED
TASK_COMPLETE = NO
