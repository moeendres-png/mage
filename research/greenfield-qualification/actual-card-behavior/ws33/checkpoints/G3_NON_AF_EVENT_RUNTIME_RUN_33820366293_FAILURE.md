# G3 NON-AF EVENT RUNTIME — RUN 33820366293 FAILURE

```ini
EVIDENCE=DIRECTLY_VERIFIED
RUN=33820366293
JOB=100861534555
SOURCE_HEAD=a6980d1763237c185a41456c0da81b706e285902
SOURCE_TREE=46945f1682b4d5ab8a30474459ff0c9217c4f3eb
ARTIFACT=9918110105
ARTIFACT_DIGEST=sha256:dd3e0b2e194654bc8fbca2acdff5c0a4411faba13b14b6d652fbf391832900df
RECORD_CAMPAIGN=PASS
RECORD_ADJUDICATION=FAIL
REPLAY=NOT_RUN
COVERAGE_PROMOTION=FALSE
G3_NON_AF_STATUS=UNKNOWN
```

The artifact ZIP was downloaded and locally re-hashed; SHA256 matched the terminal GitHub artifact digest exactly.

Steps 1–14 passed. Step 15 is the first material failure. The first parent remains:

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
```

## Parent-correlated stack lifecycle

`record/stack-lifecycle.tsv` is present and contains 11 rows. It contains **zero rows** for the first `Ingenious Smith` parent. In particular there is no `ADD_ENTER`, `ADD_TARGET_REJECT`, `FROZEN_QUEUE`, `STACK_PUSH`, or `FIZZLE_RESULT` callback for its admitted/bound `TrigDig` ability.

A positive control in the same artifact (`Descendants' Fury`) records the expected production sequence for its admitted target:

```text
ADD_ENTER
FROZEN_QUEUE
ADD_ENTER
STACK_PUSH
FIZZLE_RESULT=false
```

and then reaches the existing post-fizzle resolution callback / target execution.

Therefore the lifecycle observer is functioning and the absence for Ingenious Smith is meaningful.

## Root-cause boundary

The prior `MagicStack.hasFizzled` alternative is now ruled out for the first parent. The admitted/bound triggered Dig never enters `MagicStack.add`; therefore it cannot be rejected by `MagicStack.hasLegalTargeting`, queued frozen, pushed, or fizzled there.

Pinned Forge `PlayerControllerHuman.orderAndPlaySimultaneousSa` routes non-copied triggered abilities through `PlaySpellAbility.playSpellAbility(this, player, next)`. The first unresolved production boundary is now inside that play path before `MagicStack.addAndUnfreeze/add`.

Current evidence is still insufficient to name the exact rejected prerequisite. No Rules-Core, card, target, or fizzle repair is authorized yet.

## Narrow next atomic scope

Add observation-only prerequisite telemetry to the production `PlaySpellAbility` path used by simultaneous triggers. It must distinguish, without changing evaluation order or return values, at least:

- optional/additional-cost selection returning null;
- extra `sa.canPlay()` rejection where applicable;
- `announceType()`;
- `announceValuesLikeX()`;
- `ability.checkRestrictions(player)`;
- `ability.setupTargets()`;
- `ability.canCastTiming(player)`;
- `ability.isLegalAfterStack()`;
- cost payment/prerequisite completion;
- successful transition into `MagicStack.addAndUnfreeze`.

Record stable parent/ability/source-trigger/host/API identity and the first false stage. Existing qualification predicates remain unchanged. The observer must not choose options, alter costs/targets, bypass restrictions, change timing, or change stack semantics.

Commit diagnostic instrumentation separately; trigger exactly one successor run; immediately persist run/job/source HEAD/TREE; do not start another run before terminal adjudication.
