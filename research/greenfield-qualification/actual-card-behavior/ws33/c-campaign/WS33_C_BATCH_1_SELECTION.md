# WS33-C Batch 1 selection (8 new paths + 1 intended re-witness)

Batch digest: `9d85efc6082449d4526ed4e7388e91c0326b3ca127c6cc69f771559e2cc0f855`
Scope: template-113 / AbilitySub only (cap honored; 105/119 excluded).
All 8 new paths verified UNKNOWN, STATE_ONLY, provenance-bound; pilot path
declared re-witness (upgrades its order evidence under the v2 contract).

## Selected executions (6) / new paths (8)

1. `cloudblazer-etb-rewitness` — Cloudblazer TrigGainLife->DBDraw
   (`b42b594f…`, already evidenced). INTENDED RE-WITNESS: same production
   shape now with observed parent-effect event, exact chain IDs, and zero
   tripwire hits. No new path count.
2. `rager-etb` — Phyrexian Rager TrigDraw->DBLoseLife (`ed6d9d36…`).
   Fixed Draw-1 + Lose-1; assertions hand-net 0 / life -1.
3. `shimmercreep-etb` — Shimmercreep TrigDrain->DBGainLife (`067886a9…`).
   X = colors among own permanents; fixture holds only Shimmercreep (black)
   so X=1; assertions life +1/-1 and hand-net -1.
4. `bane-etb` — Bane of Progress TrigDestroy->DBPutCounter (`2f542f51…`)
   + DBPutCounter->DBCleanup (`c01749f7…`). Fixture holds 2 own Sol Rings;
   assertions Sol Ring count 0 / Bane P1P1 2 / hand-net -1.
5. `chopper-etb` — Foot Chopper TrigToken->DBAttach (`8d18d77c…`) +
   DBAttach->DBCleanup (`746c658d…`). Assertions own token count +1 and
   token equipped by source / hand-net -1.
6. `cap-hero-etb` — Captain America TrigPump->DBPutCounter (`494de427…`).
   Fixture: Cap pre-placed, Shang-Chi (Hero, no ETB trigger, Drawn/Counter
   triggers dormant: no draws, 1 counter != 10) enters. Assertions Shang
   P1P1 1 / Cap P1P1 1 / Shang VIGILANCE+HASTE / hand-net -1.
7. `gnarlbark-eot` — Sinister Gnarlbark TrigDraw->DBBlight (`2c49adc7…`).
   Fixture reaches our EOT by real phase progression (no opponent turn, no
   upkeep travel); Blight Defined You with Gnarlbark sole own creature.
   Assertions hand-net 0 / Gnarlbark M1M1 1.

Effect diversity: Draw, LoseLife, GainLife, DestroyAll, PutCounter, Token,
Attach, Cleanup, Blight. Fixtures: ETB_SELF x4, ETB_OTHER x1, PHASE_EOT x1.

## Excluded (representative rationale; full survey in `ws33_survey_t113_fixtures.py`)

- Targeted chains (Kor Hookmaster, Puppeteer Clique, Soul-Shackled Zombie,
  Glimmerpoint Stag, Aerial Extortionist, Reaper, Hraesvelgr, Pizzasaur):
  ValidTgts/TargetMin/Max need a decision protocol (out of scope).
- Choice/charm/optional (Tataru Taru, Black Market, Ajani's Chosen,
  Highland Berserker, Akoum, Soul Seizer, Breena, Desecration Demon,
  Strongbox Raider, T'Chaka, Transpose): Optional/Choices/UnlessCost.
- Hidden/reveal (Keen Duelist, Singe-Mind Ogre, Covenant paths).
- Search/shuffle (Cabaretti/Riveteers/Maestros, Claim Jumper, T'Chaka,
  Everything Pizza): library selection + RNG shuffle.
- Cast-cost fixtures (Papalymo, Uthros, Serra Paragon, Graha): mana/cost
  payment touches the WS33B surface.
- Combat fixtures (Archnemesis, Coercive Impetus, Falcon, Baxter attacks,
  Soul Seizer, Laelia): attack/block declarations.
- Upkeep/turn-travel fixtures (Midnight Banshee, Mechanized Production,
  village-ironsmith): require opponent turns (empty-library loss risk).
- Terminal roots without C link (Coveted Jewel, Avenger ETB, Biogenic ETB,
  Thunder Dragon, Soul Snuffers, Cyberdrive, Electric Seaweed, Jubilation,
  Doomwake/Massacre ETB): no SubAbility pointer, nothing to witness.
- Vacuous semantics via moveTo (Champions from Beyond X=0).
- Conditional cast (King Solomon's Frogs wasCastByYou fails under moveTo).
- Complex multi-phase fixtures (Animate Dead aura+graveyard, Village
  Pillagers wither-then-die, Bastion/Grave dies-links duplicate the
  Shimmercreep path without new count).
- Kappa Cannoneer {SubAbility:DBUnblockable}: RESERVED as
  WITNESS_ASSERTION_INFRASTRUCTURE_PENDING — Effect-static unblockability
  has no assertion vocabulary yet; reachability alone is not semantic
  qualification.
- ws33-template-105 (74) / ws33-template-119 (55): scope-capped, separate
  witness contracts required.

## Pre-run gate status

Checker PASS (6 Dec 2026 numbering: executions=7 incl. re-witness,
paths=9 slots / 8 new). Digest above. PENDING checkpoint follows after
push-triggered run registration.
