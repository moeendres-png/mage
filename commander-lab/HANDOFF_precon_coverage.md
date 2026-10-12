# Handoff: precon card coverage in the fork (branch cards/precon-coverage-port)

Owner decision 2026-10-12 13:44 (Moritz, "Ja, alle"): rebuild the precon cards missing
from the pinned XMage in this fork, test each card, then repin the lab and requalify.

## Base
- Fork pin used by the lab: 3cbf7741 (this branch starts there).
- Missing list: `missing49.txt` (49 precon names from the smoke run 2026-10-12).
  - 4 diacritic names (Grishnákh, Gríma, Lord of the Nazgûl, Troll of Khazad-dûm) already work
    in real decks; only the smoke harness lacked diacritic folding.
  - 2 were in the SecretsOfStrixhavenCommander `unfinished` list (Defacing Duskmage,
    Eiganjo Dynastorian): enabled, Eiganjo updated from upstream.
  - 9 ported from upstream magefree/mage afab346e (commit c6954ac5efe).
  - 34 Marvel Super Heroes Commander (MSC) cards written new; oracle text in `oracle34.md`,
    collector numbers in `meta34.json`. All 34 compile and are registered in
    MarvelSuperHeroesCommander.java (commit 7e97fb28c5c).

## Engine changes (need an independent review before repin)
- `GameEvent.EventType.CONNIVED`, fired by `ConniveSourceEffect.connive`.
- New `ConnivesCreatureYouControlTriggeredAbility`.
- `RequirementEffect.mustAttackDefenders(Ability, Game)` (default: singleton of
  mustAttackDefender) + `Combat.checkAttackRequirements` handles a multi-defender set
  (Galactus: "an opponent with the most life").
- `MageIdentifier.DragonManReformedRobotAlternateCast`.

## Status
- DONE: all card classes compile (`compile_check.sh` = javac of changed files against the
  pinned jars; empty output = OK; needs a cp.txt classpath of the 1.4.61 jars).
- WRITTEN, NOT YET RUN: 32 test classes in
  `Mage.Tests/src/test/java/org/mage/test/cards/single/msc/`. Expect to iterate on
  strict-mode choices. Some use non-strict mode where trigger order / AI mana choice is
  irrelevant. Glorious Purpose 6th plan counter and Silver Surfer's attack clause are not
  yet covered by a test.
- Known modelling choices to review:
  - Molecule Man: modelled as its own optional "first draw this turn, nonland" trigger that
    casts for {0}, not by granting MiracleAbility (granted abilities were not reliably present
    at DREW_CARD time).
  - Lady Loki: damage = absolute difference of mana values.
  - Typhoid Mary / Power Pack / Negative Zone Portal randomness uses `game.getRulesRandom()`.
  - Kang Dynasty goads via a continuous `GoadTargetEffect` (direct addGoadingPlayer is
    cleared on reset).

## Next steps
1. Build + run tests (do NOT `mvn install`: it overwrites the ~/.m2 1.4.61 jars the bridge uses):
   `mvn -o -q -pl Mage,Mage.Sets,Mage.Tests test -Dmaven.test.skip=false -Dtest='org.mage.test.cards.single.msc.*Test' -Dsurefire.failIfNoSpecifiedTests=false`
2. Fix failing cards/tests; report PARTIAL cards honestly (never count as PASS).
3. Card smoke test against the new jar (card DB must be regenerated); harness + previous results in `commander-lab/smoke/`.
4. Review of the engine hooks, then PR in moeendres-png/mage.
5. Lab repin PR (pattern #522): XMAGE_COMMIT in external-engine-integration,
   xmage-full-game-conformance, xmage-real-4p-smoke, meta-qualification workflows +
   config/rules_engines.json; then requalify (PB-03 on main -> seal.py ->
   assemble_freeze_record -> current_qualification). Bundle with the other thread's
   efficiency PR (getManaAvailable) if it has merged.

## Related work already merged in the lab (no action needed)
- #757 (issue #755): bridge advances hybrid / colorless-hybrid costs from the pool.
- #758 (issue #756): bridge handles mana abilities that need their own source tapped.
