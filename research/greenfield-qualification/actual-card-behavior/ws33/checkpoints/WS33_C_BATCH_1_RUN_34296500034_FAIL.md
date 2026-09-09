# WS33-C diagnostic run 34296500034 terminal FAIL (adjudicated; expected)

RUN = 34296500034
JOB_CONCLUSION = failure (step "Execute batch Record")
SOURCE_HEAD = 3f7e27eded
FORGE_PIN = 8c7e9afb8e6caee88644b94e25da5852e36f8928
ARTIFACT = ws33-c-abilitysub-batch-34296500034 (diagnostics + logs)
COVERAGE_PROMOTION = FALSE

## Caller evidence obtained (purpose of this diagnostic run achieved)

- `chooseSpellAbilityToPlay` x N @ `PhaseHandler.mainLoopStep` in every
  execution (2x per stack-clear, 10x over EOT travel): incidental AI
  play-consideration during priority passing, outcome-neutral (empty hands,
  no mana, no payable actions). Classification: INCIDENTAL_FLOW, recorded.
- chopper `chooseSingleEntityForEffect` @ `PlayerController.
  chooseSingleEntityForEffect < AttachEffect.resolve < AbilitySub.resolve`:
  effect-driven attach-target reaffirmation. AttachEffect.java pin shows the
  consultation is unconditional over the defined set; fixture set is a
  singleton (Remembered token). Classification: DECLARED singleton
  consultation (options must equal 1 at runtime).
- cap: `runWaitingTriggers true` but `addAllTriggeredAbilitiesToStack false`:
  runWaiting true is partly the battlefield-entry side effect
  (TriggerHandler returns checkStatics which entry sets); Cap placed via
  addCardToZone never got engine trigger registration (registration happens
  on entry via moveTo). Fixture defect, not engine defect. Fix: enter Cap
  via production moveTo.
- gnarlbark: EOT tolerance worked (no fixture error); only incidental hits
  failed it. Proceeds to matching under R3 rules.

Both direct-child negatives PASSED again (Tests 3, 1 campaign failure).

## Root-cause classes

- TRIPWIRE_UNCLASSIFIED_SITES (methodology gap, now R3-ruled).
- CAP_FIXTURE_REGISTRATION (harness fixture defect, fixed via-move).
- GNARLBARK_EOT_RACE (fixture tolerance, fixed).

No engine defect demonstrated. Pilot evidence stands.

EVIDENCED_PATH_COUNT = 1 / REMAINING_UNKNOWN_COUNT = 699 (unchanged)
