# WS33 G3 non-AF event runtime — pending event-shape successor

Status: PENDING / NOT YET ADJUDICATED

- SOURCE_HEAD: `99377107cf860876bd5ee43fbc8121802ad9336e`
- SOURCE_TREE: `515c9847f54fd4eeb1a3375a36913a6cc990d274`
- RUN: `33854808213`
- JOB: `100965530844`

This is the single successor triggered by the generic event-fixture repair after run `33853539153`.

The source change is limited to:

1. Phase parents establish their script-derived target `PhaseType` before `resetActiveTriggers()`, so pinned Forge `isTriggerActive()->phasesCheck(game)` evaluates the intended event state during active-trigger registration.
2. `AttackersDeclared` writes `AbilityKey.AttackedTarget` as an aggregate singleton collection/Iterable, matching pinned production `PhaseHandler` and `TriggerAttackersDeclared.setTriggeringObjects()`.

No card-specific exception was introduced by this repair. No trigger legality method was bypassed. `Study Hall / TriggersWhenSpent` is intentionally unrepaired and remains a diagnostic frontier if it still fails.

No coverage promotion is authorized until terminal strict adjudication and replay gates pass.
