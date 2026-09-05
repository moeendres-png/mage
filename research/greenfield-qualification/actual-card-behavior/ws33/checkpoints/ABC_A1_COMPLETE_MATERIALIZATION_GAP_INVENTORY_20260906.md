# WS33 ABC-A1 — complete remaining materialization-gap inventory

Date: 2026-09-06

## Evidence boundary

Run `33996373469` prepared 328 conservative TargetRestrictions cases and then failed because the A1 filter reports only the first five missing IDs (`missing[:5]`). The immutable run artifact `9978200670` (digest `sha256:a1c6ef13263dd6f47baf3ce6302ced8922eacd41adffb3f001c7f3bf63652ea9`) was independently compared against the exact 122-ID A1 queue from `WS33_INTEGRATED_WORK_QUEUE.json`.

Result:

- A1 queue IDs: 122 / 122 unique
- present in prepared 328-case campaign: 72
- absent from prepared campaign: **50**
- every absent path is `ACTION_COST_DECISION / forge.game.spellability.TargetRestrictions / DECISION+REPLAY`
- Record/Replay has not executed for these paths

This proves the previous five-at-a-time sequence was caused by diagnostic truncation, not by sequential discovery of only five defects at a time.

## Complete missing selector inventory

The 50 absent authoritative `ValidTgts` shapes are:

1. `Permanent.Black,Permanent.Red`
2. `Creature.White,Creature.Blue`
3. `Creature.ControlledBy TriggeredDefendingPlayer`
4. `Creature.YouOwn+ThisTurnEnteredFrom_Battlefield`
5. `Creature.nonVampire+nonWerewolf+nonZombie`
6. `Creature.nonLegendary+YouOwn`
7. `Card.ExiledWithSource`
8. `Creature.YouCtrl+cmcLE3`
9. `Creature.Legendary+YouCtrl`
10. `Permanent.YouCtrl+cmcLE4`
11. `Artifact.YouCtrl+cmcEQX+!token`
12. `Aura.YouOwn,Equipment.YouOwn`
13. `Permanent.OppCtrl+cmcGE3`
14. `Creature.tapped`
15. `Creature.nonLegendary+YouCtrl`
16. `Creature.MultiColor`
17. `Creature.powerGE4`
18. `Creature.HasCounters`
19. `Creature.cmcLEX+YouCtrl`
20. `Creature.cmcLEX`
21. `Creature.attacking+YouCtrl,Creature.blocking+YouCtrl`
22. `Creature.ControlledBy ParentTargetedController,Creature.ControlledBy ParentTarget`
23. `Instant.YouCtrl+cmcLEX,Sorcery.YouCtrl+cmcLEX`
24. `Creature.OppOwn`
25. `Creature.OppCtrl,Enchantment.OppCtrl`
26. `Creature.ControlledBy TriggeredTarget`
27. `Permanent.nonLand+cmcLEX+YouOwn`
28. `Creature.Green,Creature.White`
29. `Creature.Assembly-Worker`
30. `Artifact.YouOwn+cmcLE3,Creature.YouOwn+cmcLE3,Enchantment.nonAura+YouOwn+cmcLE3`
31. `Creature.cmcLE2`
32. `Permanent.nonLand+tapped+ControlledBy TriggeredDefendingPlayer`
33. `Card.nonCreature+nonLand+YouOwn`
34. `Creature.cmcLEX`
35. `Permanent.nonLand+!token+YouDontCtrl+cmcLE4`
36. `Vampire.YouCtrl`
37. `Creature.nonWhite`
38. `Permanent.nonLand+nonCreature+ControlledBy TriggeredTarget`
39. `Permanent.MonoColor`
40. `Ninja,Turtle`
41. `Card.Red,Card.Green`
42. `Creature.OppCtrl,Planeswalker.OppCtrl`
43. `Creature.attacking+withoutFlying`
44. `Enchantment,Instant,Sorcery`
45. `Card.cmcLE3`
46. `Any.NotDefinedParentTarget,Player`
47. `Creature.YouOwn+cmcLEX`
48. `Creature.Legendary`
49. `Creature.counters_GE1_M1M1`
50. `Artifact.YouOwn,Creature.YouOwn`

(`Creature.cmcLEX` occurs in two distinct actual-card paths and therefore appears twice in the path inventory.)

## Systemic repair families

These shapes reduce to reusable qualification fixture families; Forge remains the sole legality authority:

- ordinary type/color/controller/owner/CMC/power filters -> real typed cards in the authoritative target zone;
- tapped/counter filters -> real `Card` state via Forge `setTapped(true)` / `addCounterInternal(...)`;
- attacking/blocking filters -> real `Combat` state;
- `TriggeredDefendingPlayer` / `TriggeredTarget` -> authoritative `AbilityKey` triggering objects;
- `ThisTurnEnteredFrom_Battlefield` -> actual `GameAction.moveTo(Battlefield -> Graveyard)` history;
- `ExiledWithSource` -> actual exile-zone card with Forge `setExiledWith(source)` relation;
- subtype filters (Vampire, Assembly-Worker, Ninja/Turtle) -> actual pinned Forge card scripts;
- X-dependent `cmcLEX` forms -> zero-CMC real card where the source semantics allow Forge to determine legality; no X value is invented in the pilot;
- stack-target color/CMC filters -> real stack spell produced through the existing stack fixture.

No production Rules code, card script, effective manifest, queue, coverage registry, or global identity registry is to be changed by this repair.

Evidence classes:

- 122-ID queue / 328 prepared IDs / 50-set difference: `DIRECTLY_VERIFIED`
- path-to-selector resolution from immutable successor manifest: `DIRECTLY_VERIFIED`
- repair-family grouping: `CODE_DERIVED`
- concrete fixture choices: `MODELED` until fresh runtime execution

`ABC_A1_MISSING_PATHS=50`
`ABC_A1_MISSING_SELECTOR_OCCURRENCES=50`
`ABC_A1_RULES_CORE_DEFECT=FALSE`
`ABC_A1_COVERAGE_PROMOTION=FALSE`
