# WS33-C R5 run 34299361792 terminal FAIL (adjudicated)

RUN = 34299361792
JOB = 102302796309 (c-abilitysub-pilot, completed/failure)
RUN_SOURCE_HEAD = b85c6ac50498c1001d4329c949e0a7d1141a64e3 (matches PENDING seal)
EVENT = push, BRANCH = work/ws33-c-high-throughput-20260907
FORGE_PIN = 8c7e9afb8e6caee88644b94e25da5852e36f8928
ARTIFACT = 10084393859 (ws33-c-abilitysub-batch-34299361792)
ARTIFACT_DIGEST = sha256:2a8f4bfa57fe11fb8d38d94dbd864faed89a348c2a7bc3b10caa2d449c6d1182
FAILING_STEP = Execute batch Record (production-parent witnesses)
CERTIFICATION_SKIPPED = TRUE (fail-fast after runtime failure, as designed)
COVERAGE_PROMOTION = FALSE

## Run result (DIRECTLY_VERIFIED from live log)

Tests run 3, Failures 1, Errors 0. Both direct-child negatives PASSED.
Campaign 0/7 records; diagnostics non-empty (workflow gate correctly red).

## What R5 instrumentation proved (diagnostic purpose achieved)

1. DUPLICATE_PARENT_RESOLUTION, 6/6 ETB executions, uniform shape.
   Representative (Cloudblazer): Child seq0 id14 GainLife parent=-1 root=14;
   Parent seq1 id14 sub=DBDraw; Child seq2 id15 Draw parent=14 root=14;
   Parent seq3 id15 sub=null; Parent seq4 id16 GainLife sub=DBDraw by=p2,
   with NO child event parented to 16. All activators p2 (=actor, in game).
2. Outcome-neutrality proven per execution by exact semantic snapshots:
   cloud life+2/opp+0, rager life-1, shimmer +1/-1, bane/chopper/cap all d0.
   A second effective GainLife/Draw/LoseLife resolution would break at
   least one delta; none broke. Hand deltas reflect the OLD snapshot order
   (pre-hand-placement; fixed separately in R6).
3. Mechanism identified at FORGE_PIN source (CODE_DERIVED, no behavior change):
   the stacked trigger ability is a WrappedAbility (own runtime id,
   delegated api/host/params); its resolve() delegates to the inner
   executing ability via playSpellAbilityNoStack, and resolveSubAbilities
   skips wrappers via the isWrapper guard, so no double application.
   The seq-last same-api parent event is the stack-level envelope frame,
   not a second firing. Engine self-resolution by effects excluded by
   source inspection (no effect calls AbilityUtils.resolve/resolveSubAbilities).
   NOT a Forge engine defect; no Sol escalation required for this item.
4. GNARLBARK_SILENT_EOT: phase=END_OF_TURN turn=p2(=actor) game_over=false
   stack_empty=true children=0. EOT reached on actor's turn in a live game
   with zero parent/child events. devModeSet sets turn player (verified at
   pin), so turn mismatch is excluded. Phase-trigger silence mechanism
   still open; no engine defect demonstrated (no incorrect behavior proven).

## Root-cause classification

- R5a DUPLICATE_PARENT_UNMATCHED: harness uniqueness rule (exactly-1
  parent per api/host) too strict vs production wrapper/inner nesting.
  C-local repair: pair-matching by exact object relation
  (child.parentId == parent.id), already in progress uncommitted.
- R5b SILENT_EOT_UNEXPLAINED: fixture/trigger question, mechanism open.
  Repair path: defer gnarlbark execution (FIXTURE_INFRASTRUCTURE_PENDING),
  keep path UNKNOWN with cause; investigate phase family separately.
- R5c HAND_SNAPSHOT_ORDER: snapshot precedes fixture hand placement,
  shifting hand deltas by the fixture card. C-local repair: snapshot after
  hand placement (in progress uncommitted).

No production behavior demonstrated incorrect. Pilot evidence (runs
34289134780/34289612464) stands uninvalidated. No rerun of R5: its
diagnostic purpose is fulfilled; the replacement run carries R6.

EVIDENCED_PATH_COUNT = 1 / REMAINING_UNKNOWN_COUNT = 699 (unchanged)

## Exact next action

Finish R6 (pair-matching, snapshot rule, screen gate, armor diversity,
gnarlbark deferral, digest), pre-run gate, PENDING, push, run, per-path
adjudication, repartition.

TURN_STATUS = INTERRUPTED
TASK_COMPLETE = NO
