# F-20: the initiative when its holder leaves the game (CR 726.4, inferred)

Commander Simulator Next tracker: moeendres-png/commander-playtest-lab#327.
Author: Claude Opus 5.5 (Claude Code), 2026-09-29.

## Source lock
- Base: the exact candidate pin `b19596980f2734496ea1896504253e1bdd2756dd` (head of Mage PR #16). Not master; `magefree` code at `798b75e5` has the same gap.
- Fix commit: `71b4e9317faed5de2443f8e4d2c99286948030a5`, tree `dce25c9a4d5a0df7460d29a4f78fd67a662df494`.
- Rule: the initiative's leave-the-game rule. If the player who has the initiative leaves the game, the active player takes the initiative at the same time. If the active player is the one leaving, the next player in turn order takes it.
  - **Rule number and verbatim text NOT verified in this session.** Egress to the CR and Scryfall is blocked.
  - The number is inferred: the initiative section follows the monarch section. The Lab's 2026-09-25 CR citation numbers the monarch CR 725 (`XmageMultiplayerMonarchTest`), so this is probably **CR 726.4**. In 2022 editions it was 725.4 (monarch 724.4).
  - The fix commit message says "CR 725.4" (older numbering). This handoff supersedes it.
  - The paraphrase mirrors the monarch's leave rule, which the pin already implements in `GameImpl.leave()`.
  - Taking the initiative this way triggers "whenever you take the initiative, venture into Undercity".

## Defects (two, both needed for the rule to work)
1. `GameImpl.leave()` moved the monarch but never the initiative. `GameState.initiativeId` kept pointing at the player who left, so nobody held the initiative for the rest of the game.
2. The initiative's triggered abilities (the venture trigger and the combat-damage transfer) are added once, when the initiative first enters the game, and keep the **first** holder as their controller.
   - When that player left, `checkTriggered` never put them on the stack, because it only processes players still in the game.
   - Result: no venture on take or upkeep, and no transfer by combat damage.
   - In normal play (no leave) the same stale controller made the first holder control the new holder's venture trigger.

## Fix
- `GameImpl.leave()`: if the leaving player has the initiative, the active player takes it. If the leaver is the active player (or there is none), the next player in turn order takes it, found on a **copy** of the player list so the game's turn pointer is not moved. This goes through `takeInitiative`, so `TOOK_INITIATIVE` fires.
- `Initiative`: like `Monarch`'s abilities, both triggers now set their controller to the player who has the initiative.

## Native evidence
`Mage.Tests` `org.mage.test.commander.multiplayer.InitiativeLeavesGame{3,4,5,6}PTest`:
- Setup:
  - White Plume Adventurer, which takes the initiative on ETB.
  - Commander free-for-all at 40 life; turn order is A, then the seats in reverse creation order.
  - At 5P and 6P the holder is the third player in turn order, not seat A.
- Scenarios:
  1. The holder leaves on another player's turn: the active player has the initiative and is in Secret Entrance.
  2. The holder leaves on its own turn: the next player in turn order has it and is the active player next turn. Its take plus upkeep ventures reach a second Undercity room (Forge or Lost Well). Nobody else ventured.
  3. A non-holder leaves: the initiative stays with the holder, and the active player did not venture.
  4. After the first holder left, a third player's Grizzly Bears deal combat damage to the new holder. The attacker takes the initiative and ventures.
- Results:

| Run | Result | Log |
|---|---|---|
| Pin | red, 12/16 (scenario 3 passes everywhere) | `f20-red-pin.log` |
| `leave()` part alone | still red, 12/16: holder correct, but no venture and no damage transfer, so defect 2 is independent | `f20-step1.log` |
| Both parts | green, 16/16 | |
| Related suite | green, 283/283 | |

The related suite covers:
- `org.mage.test.multiplayer.**` and `org.mage.test.commander.**`;
- Dungeon, DungeonGeists, UndercityReaches, Monarch, PalaceJailer, PlayerLeavesGame, PlayerLeft, WS211 concession;
- the Court cycle, EndOfTurnMultiOpponents, ContinuousEffectsLastingAfterCreatorsDeath, AngelOfSerenity, Hezrou, BolassCitadel, Six, Expend, Plot, CommandersCast, Saheeli, WorldEnchantmentsRule.

## Not done here
- No Lab repin. The Lab XMage pin stays at `b19596980f`, and a repin is a separate step.
