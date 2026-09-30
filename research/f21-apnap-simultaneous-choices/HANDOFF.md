# F-21: simultaneous each-player / each-opponent choices in APNAP order (CR 101.4)

Commander Simulator Next tracker: moeendres-png/commander-playtest-lab#328.
Author: Claude Opus 5.5 (Claude Code), 2026-09-29.

## Source lock
- Base: the exact candidate pin `b19596980f2734496ea1896504253e1bdd2756dd` (head of Mage PR #16). Not master.
- Fix commit: `b0bbfce2e36fa92b7349f7121116de0df85a09b0`, tree `2d43fab37dd8e2ddb15ae2cfd91c7913ac3e676c`.
- Rule: CR 101.4. When several players make choices at the same time, the active player chooses first, then the next player in turn order, then the rest in turn order.
  - The 2026 verbatim text was not re-read in this session (egress blocked). The rule has been stable across editions.

## Defect
1. `Game.getOpponents(playerId)` streamed `state.getPlayerList()`.
   - `CircularList`'s iterator starts at the list's **current pointer**, and the priority loop moves that pointer.
   - Result: "each opponent" choices started with whoever the pointer was on, usually the last player to pass priority.
   - Example (4P, turn order A → D → C → B): A casts Liliana's Triumph on its own turn, and the choices come as B, D, C instead of D, C, B.
2. `SacrificeAllEffect` ("each player") and Grave Pact iterate `getPlayersInRange(controllerId)`, so they start with the **controller**. That matches APNAP only when the controller is the active player.

## Fix
- New `Game.getPlayersInApnapOrder()`:
  - returns all players (including players who left, like `getOpponents`), starting with the active player, then in turn order;
  - respects a reversed turn order;
  - works on a copy of the player list, so the priority pointer is not touched.
- `getOpponents` now keeps its filters (not self, in range, optionally in game) but uses this order.
- `SacrificeAllEffect` "each player" and Grave Pact use the helper, filtered by the controller's range of influence.

## Native evidence
- `Mage.Tests` `org.mage.test.commander.multiplayer.SimultaneousSacrificeApnap{3,4,5,6}PTest` uses a recording player that logs the order of the actual `TargetSacrifice` choices.
- Scenarios:
  1. Liliana's Triumph cast by the first player on its turn.
  2. Liliana's Triumph cast by the third player on its turn.
  3. Liliana's Triumph cast by a non-active player at instant speed; APNAP starts with the active player.
  4. Grave Pact triggering on another player's turn.
  5. Innocent Blood cast by the active third player (guard: already correct).
- Every chooser also sacrificed exactly one creature.
- Results:
  - red on the pin: 15/20 (scenario 5 passes, as does scenario 4 at 3P where controller-first coincides with APNAP);
  - green with the fix: 20/20.
- Full `Mage.Tests` with the fix (`-pl Mage,Mage.Sets,Mage.Tests`): 6965 run, 125 skipped, 12 failures.
  - All 12 failures are stale compiled `InitiativeLeavesGame*Test` classes left in `target/test-classes` from the F-20 branch. They run against pin behaviour, and their sources are not on this branch.
  - Everything else, 6953 tests, is green.

## Residual (not changed here)
- About 70 other card-local (list below) "each player sacrifices" loops in `Mage.Sets` still use `getPlayersInRange(controllerId)`.
- They are APNAP-correct whenever the controller is the active player (sorceries, most ETBs). They stay controller-first for triggers or instants on another player's turn.
- `getPlayersInApnapOrder()` is the drop-in replacement for them.

## Lab-lane evidence
- commander-playtest-lab#326, `XmageMultiplayerEachOpponentChoiceTest` (3–6P, Liliana's Triumph):
  - the enabled "each opponent chooses once" part is green on the pin;
  - the APNAP order expectation is disabled with F-21 and fails 4/4 on the pin (P2 asked first).

## Not done here
- No Lab repin.

### Residual site list (Mage.Sets files using `getPlayersInRange(` together with sacrifice; not all of them are simultaneous-choice loops)
    ArgothianWurm BalancingAct BellowingMauler BringerOfTheLastGift CatchRelease CracklingDoom CryptChampion 
    DanseMacabre DeadlyBrew DescentIntoMadness FadeAway FallOfTheFirstCivilization FallOfTheThran FieldOfRuin 
    FrayingOmnipotence GoblinAssassin GrimoireOfTheDead InfernalOffering InvestigatorsJournal KefkaCourtMage 
    KeldonFirebombers KillingWave LilianaDreadhordeGeneral MagusOfTheJar MartyrsBond MaximumCarnage 
    MedomaisProphecy MemoryJar MindSwords NaturalBalance NightmaresAndDaydreams OlorinsSearingLight OmenOfFire 
    OutpaceOblivion Plaguecrafter PossessedPortal Pox PoxPlague ProwlingPangolin PyxisOfPandemonium RaidingParty 
    ReignOfThePit RiseOfTheWitchKing SavraQueenOfTheGolgari SerraBestiary ShadowgrangeArchfiend 
    ShattergangBrothers Sheoldred ShivanWumpus ShredderShadowMaster SotheraTheSupervoid StraxSontaranNurse 
    StrefanMaurerProgenitor StrongholdDiscipline SummonEsperValigarmanda SyphonFlesh TaintedSigil TectonicHellion 
    TheDeathOfGwenStacy TheEternalWanderer TheHorusHeresy TheThreeSeasons TheWarGames ThoughtsOfRuin 
    Vault11VotersDilemma Vault12TheNecropolis VolatileRig WhimsOfTheFates WhirlpoolWarrior WorldQueller 
    WormsOfTheEarth ZodiarkUmbralGod 
