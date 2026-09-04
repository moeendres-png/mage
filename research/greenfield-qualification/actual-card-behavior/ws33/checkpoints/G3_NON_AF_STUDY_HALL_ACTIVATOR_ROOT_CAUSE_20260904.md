# WS33 G3 Study Hall spawning-activator root cause — 2026-09-04

Classification: `DIRECTLY_VERIFIED + CODE_DERIVED / SYSTEMIC FIXTURE DEFECT`

Pinned Forge: `8c7e9afb8e6caee88644b94e25da5852e36f8928`.

## Direct runtime evidence

Run `33857483472` / artifact `9930890226` isolates the sole non-AF parent failure to `TriggerSpellAbilityCastOrCopy.performTest(...)` stage `VALID_ACTIVATING_PLAYER=false`.

For the intended Study Hall commander-spell check, same-run telemetry records:

- trigger mode: `SpellCast`
- host/spawning host: `Study Hall`
- cast: `Serra Angel`
- `castCommander=true`
- cast owner id: `1`
- SpellCast activator id: `1`
- remembered count: `1`
- remembered identity matches: `1`
- remembered contains current SpellAbility: `true`

Thus Commander identity, ownership, SpellCast activator, and TriggersWhenSpent remembered-spell identity are all correct. The first failing predicate is specifically `ValidActivatingPlayer$ You`.

## Pinned Forge explanation

`CardTraitBase.matchesValid(o, valids, srcCard)` normally derives the source player from `srcCard.getController()`, but for a `Trigger` with a non-null `spawningAbility`, Forge replaces that source player with `trigger.getSpawningAbility().getActivatingPlayer()` before evaluating `You`/`Opponent` validity.

`AbilityManaPart.addTriggersWhenSpent(saBeingPaid)` creates the delayed trigger and assigns its spawning ability from the mana part's source SpellAbility.

The WS33 event fixture locates the source-proven mana producer and directly invokes its production `addTriggersWhenSpent(spell)` path, but it never establishes the producer SpellAbility's activating player. In a real mana-ability activation, that field is already the player who activated the mana ability. Therefore the fixture supplies an incomplete production precondition: the SpellCast activator is actor 1, while the dynamically spawned trigger's source-player context comes from an unactivated producer SpellAbility.

This is not a Study Hall card-name defect and not a Forge rules-core defect.

## Authorized repair scope

Repair the generic `SVAR / TriggersWhenSpent` fixture setup only: when the harness has source-proven exactly one `TriggersWhenSpent` mana producer, bind that producer SpellAbility's `activatingPlayer` to the fixture actor before calling `addTriggersWhenSpent(spell)`. Fail closed if the binding does not hold.

Do not alter `TriggerSpellAbilityCastOrCopy`, `matchesValid`, Study Hall script data, Commander validity, trigger legality, or remembered identity semantics.

One repair commit -> exactly one event-runtime successor -> immediate pending checkpoint -> terminal adjudication.

`COVERAGE_PROMOTION = FALSE`
`WS33_COMPLETE = FALSE`
`TASK_COMPLETE = NO`
