# G3 NON-AF EVENT RUNTIME — RUN 33818428322 FAILURE

```ini
EVIDENCE=DIRECTLY_VERIFIED
RUN=33818428322
JOB=100855531128
SOURCE_HEAD=3e2260fe7b8a1a7a1d9fea932301b6fac3b3b3c6
SOURCE_TREE=5f757dc8bc0c85fdea10d6e0cc8da762865e23a7
ARTIFACT=9917438334
ARTIFACT_DIGEST=sha256:696556a4e4163308ec00ef123b691a9eaa73e6742058220ac1041d73cef7fa6f
RECORD_CAMPAIGN=PASS
RECORD_ADJUDICATION=FAIL
REPLAY=NOT_RUN
COVERAGE_PROMOTION=FALSE
G3_NON_AF_STATUS=UNKNOWN
```

## Immutable artifact adjudication

The terminal GitHub Actions run is `failure`. Steps 1–14 passed; Step 15 (`Adjudicate record behavior and minimum Decision/RNG obligations`) is the first material failure. Replay and source-chain materialization did not run. Evidence upload succeeded.

A fresh post-terminal artifact listing is authoritative for this checkpoint: artifact `9917438334`, name `ws33-g3-svar-event-runtime-33818428322`, digest `sha256:696556a4e4163308ec00ef123b691a9eaa73e6742058220ac1041d73cef7fa6f`. The downloaded ZIP was re-hashed locally and matched this digest exactly. An earlier transient artifact listing observed while finalization was still changing is superseded and is not source truth.

The record artifact contains exactly 33 `parent-summary.tsv` rows and 33 `resolution-lineage.tsv` rows. Parent status is 1 PASS / 32 FAIL. Twenty-four rows are `triggerAdmissions=1,targetBindings=1,targetExecutions=0`; eight later rows fail before admission; one row (`Descendants' Fury`) is `1/1/1` PASS. Resolution-lineage reports zero callbacks for 30/33 parent rows, one callback for 3/33, and only one target execution.

## First material Step-15 failure

The first failing parent in authoritative artifact order is:

```text
parent=forge-behavior-v2:172ab06795f99590ca9d96f85995f6cf9e083ee8#1
card=Ingenious Smith
mode=ChangesZone
target_svar=TrigDig
dispatch=Dig
triggerAdmissions=1
targetBindings=1
targetExecutions=0
resolutionCallbacks=0
admittedAbilityId=225
admittedSourceTrigger=50001
admittedHostId=96
admittedApi=Dig
admittedOriginalMapHash=d20cf9e4e17d170305eac986758ee85d82941e4250d665529a0ed942a2bdd323
admittedCurrentMapHash=d20cf9e4e17d170305eac986758ee85d82941e4250d665529a0ed942a2bdd323
resolutionTrace=<empty>
```

Exact parent failure payload decodes to:

```text
java.lang.IllegalStateException
target SVar did not reach non-fizzled root resolution parent=forge-behavior-v2:172ab06795f99590ca9d96f85995f6cf9e083ee8#1
```

## Root-cause boundary

Classification remains **UNKNOWN**, but the prior ambiguity is materially narrowed.

`resolutionCallbacks=0` directly rules out the previously considered false-negative `matchesTarget` explanation at the post-fizzle resolution observer: there was no resolution callback for the matcher to reject. Admission and exact target binding both occurred (`1/1`), and admitted original/current map fingerprints are identical.

Pinned Forge source inspection establishes that `WrappedAbility.getApi()` delegates to the wrapped ability API, while the qualification observer is installed in `MagicStack.resolveStack()` after `hasFizzled(sa)` and immediately before `AbilityUtils.resolve(sa)`. Therefore the first parent's remaining common pre-observer boundary is one of:

1. the admitted simultaneous trigger never becomes a real MagicStack entry through production `PlayerControllerHuman.orderAndPlaySimultaneousSa -> PlaySpellAbility.playSpellAbility`; or
2. it becomes a real stack entry but `MagicStack.hasFizzled(sa)` returns true before the post-fizzle observer.

Current immutable evidence does not distinguish these two cases. This is not sufficient evidence for a Rules-Core repair, a matcher repair, or coverage promotion.

## Why later symptoms are not repaired yet

The eight zero-admission event-specific failures and the other `1/1/0` rows are downstream/supporting observations. The first parent already proves a shared unresolved stack/fizzle boundary. Repairing later event fixtures first would violate first-failure discipline and could mask the systemic cause.

## Narrow next atomic scope

Before any semantic repair, add observation-only telemetry at exactly the two remaining production boundaries while preserving the existing qualification gate unchanged:

- record whether the admitted parent ability is successfully inserted from the simultaneous-trigger queue onto the real MagicStack, including stable ability/source-trigger/host/API identity;
- record the pre-resolution `hasFizzled` outcome for that same real stack entry before the existing post-fizzle observer.

The instrumentation must not decide legality, choose targets, alter stack ordering, mutate targets, alter fizzle semantics, change `matchesTarget`, change `targetExecutions`, synthesize Decision/RNG evidence, or mutate coverage.

Commit diagnostic instrumentation separately. Trigger exactly one `ws33-g3-svar-event-runtime.yml` run, persist its run/job/source HEAD/TREE immediately, and do not start another run until it is terminal and checkpointed.

Resume at: inspect/persist the exact simultaneous-to-stack and `hasFizzled` observations for first parent `forge-behavior-v2:172ab06795f99590ca9d96f85995f6cf9e083ee8#1`; repair only the directly confirmed systemic defect afterward.
