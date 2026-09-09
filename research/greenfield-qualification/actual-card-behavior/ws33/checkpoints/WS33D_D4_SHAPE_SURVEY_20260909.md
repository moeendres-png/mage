# WS33-D D4 shape survey — template-049 EffectEffect STATE_ONLY (49 paths)

Date: 2026-09-09. Branch: `work/ws33-d-high-throughput-20260907`.
`TASK_COMPLETE=NO`. `TURN_STATUS=RUNNING`. `COVERAGE_MUTATED=FALSE`.
`COVERAGE_PROMOTED=FALSE`. No run registered; no witness machinery built.

## 1. Source reverification (DIRECTLY_VERIFIED)

- Local HEAD `ac1006848490b47a00faec386975acb3a9b7705f` == remote
  `origin/work/ws33-d-high-throughput-20260907` == mandated remote source
  lock. TREE `b97490e02159ef3647a100288a58a12c56cf5d10`. Clean except two
  untracked D4 scratch files (inventoried below, untouched).
- Retained evidence rechecked: `WS33D_PARTITION.json` EVIDENCED=25,
  REMAINING_UNKNOWN=895, BLOCKED_TEMPLATE_MISSING=1; D3 run 34380960438
  PASS checkpoint present; all 49 D4 queue ids are UNKNOWN in
  `WS33_INTEGRATED_CLOSURE_LEDGER.jsonl` (49/49).
- Forge pin `8c7e9afb8e6caee88644b94e25da5852e36f8928` reverified live:
  sparse checkout at the pin (`Fix Nori, Teller of Tales (#11713)`),
  all 48 unique D4 card scripts read at pin (49 paths; gideon_jura x2).
  Fixture cards verified at pin: Seismic Rupture (2R, 2 to each nonflying),
  Suntail Hawk (1/1 flying), Runeclaw Bear (2/2), Memnite (0-cost 1/1
  artifact nonflying), Wrath of God (2WW destroy-all).

## 2. Untracked scratch adjudication (retained, NOT trusted as-is)

Two untracked files from the interrupted session; neither deleted nor
staged. Verdict: RETAIN BOTH as drafts, repair before use.

- `ws33_prepare_d4_staticeffect_campaign.py`: per-card survey table
  (7 provable + 42 deferred) is broadly sound but has three binding
  errors found by ground-truth recheck: (a) `invisible_woman` recipe
  `BEGIN_COMBAT_TOKEN` exercises the Wall-token SVar, NOT the ledger
  Effect SVar (line 10 `DBUnblockable`, attack trigger, cost RGWU +
  target) — invalid binding, must be deferred, recipe deleted;
  (b) `electric_seaweed` deferred for the wrong path (its AB DealDamage
  line belongs to another template; the D4 Effect line 8 is ETB,
  decision-free, cascade-observable) — repromote to D4a;
  (c) single per-card `gideon_jura` entry conflates two ledger paths:
  line 6 (+2 delayed trigger, opponent target → D6) vs line 11
  (0-loyalty animate + self-prevention Effect, no targets/decisions →
  D4a). Dispositions must be per-PATH, not per-card. Deferred reasons
  for `conspiracy_theorist`, `urianger_augurelt`, `progenitors_icon`
  are imprecise (see full mapping below) but the deferrals stand.
- `runtime-tests/Ws33D4StaticeffectCampaignTest.java` (1156 lines):
  NOT executable as-is. Blocking defects: (a) `assertRecipePostconditions`
  contains dead D3 branches (SPELL_DAMAGE_ALL, ETB_DAMAGE_OPP,
  CAST_TRIGGER_SOURCE, Seismic/Chain/Volcanic/Pillagers/Crystal/Y'shtola
  card checks) and ZERO branches for its own six recipes — no
  command-zone Effect assertion, no per-card zone assertions, so cases
  could pass vacuously; (b) `driveRecipe BEGIN_COMBAT_TOKEN` implements
  the invalid invisible_woman binding — delete; (c) `record.json`
  hardcodes `trace_event_ids` `LIFEGAIN_RESOLVED` (wrong taxonomy);
  (d) `canonicalFinalState` lacks planeswalker loyalty (needed for the
  gideon-L11 consequence assertion) and command-zone Effect-object
  extraction; (e) `addCards`/`createCard`/`placeCard` helpers must be
  rechecked against `AITest` API before build. Repair list is exact and
  bounded; no A/C/serial/shared decision-contract change is involved
  (provider pattern is D1/D3-identical: NONE/ENTITY/CONFIRM_TRUE only,
  fail-closed on any other request).

## 3. Survey verdict: NOT one executable family — repartition required

Entry-point mix at pin: SP-root 4, AB-root 6, AB-nested SVAR 2,
DB-nested SVAR 37. Effect payloads span emblems, MayPlay permissions,
replacement preventions, CantBeCast/CantPrevent statics, MustAttack,
trigger-carrying Effects, target/choice/X/combat/hidden-gated Effects.
One harness cannot execute them. Repartition (per-PATH):

- D4a STATE_ONLY-provable now (8 paths, bounded attempt set, §4).
- D4b planeswalker-emblem setup → D5 batch (3: tezzeret L11, elspeth L7,
  chandra L11 ultimates; loyalty setup machinery).
- D4c target/choice-gated → D6 batches (21, incl. gideon L6, surge,
  promise, heroic_return, makeshift, palace_jailer, quintorius,
  conduit, kang, spark_double, circle_of_protection, solar_array,
  strongbox_raider, atsushi, expressive_iteration, progenitors_icon
  (ChooseType → D7-adjacent), superior_foes, containment_construct,
  urianger_L9 (exiled-with-source setup, no decision in the Effect
  itself but unreachable without Draw-Arcanum setup), conspiracy (also
  needs attack+discard chain), intimidation_bolt).
- D4d X-gated → D7 (2: finale_of_revelation, disintegrate).
- D4e combat/hidden-gated → D8 (14: aerial_extortionist (note: ETB
  TargetMin 0 zero-target variant recorded as future stretch),
  invisible_woman, love_on_the_battlefield, gateway_sneak, okoye,
  winter_soldier, arbalest_elite, klaw, willie_lumpkin, taunt_from_the_
  rampart, inkshield, extract_power, summon_good_king_mog_xii,
  human_torch; full list in §5).
- D4f unclear → needs-review, never blocks siblings (1: furygale_flocking
  RepeatEach tokenverse + MustAttack attachment).
- 8 + 3 + 19 + 2 + 15 + 1 = 48 dispositions over 48 cards / 49 paths
  (gideon counted twice: L6→D4c, L11→D4a). Deferred buckets stay
  UNKNOWN; no sibling inference.

## 4. D4a frozen attempt set (8 path ids, fail-closed)

Each candidate is decision-free on its exercised line at pin; any
decision request fails the case closed and defers the path with exact
evidence. Consequence-tier assertions (TIER-1) except where noted.

1. `forge-behavior-v2:236a197c184149bb9d038b2dd88479c106c13376`
   silence SP$ Effect (CantBeCast). Recipe SPELL_STATIC_PRESENCE, pool
   W1. TIER-1: opponent production Memnite-cast attempt rejected
   (automatic), Effect in command, zones unchanged.
2. `forge-behavior-v2:7a54c6e56acee350879801e528ddf5420c4cca64`
   unstable_footing SP$ Effect (CantPreventDamage) + kicker-gated
   DBDamage (Condition$ Kicked). Pool R1 (kicker 3R unaffordable).
   TIER-2 presence (chained prevention-suppression consequence is a
   follow-up). Fail-closed on any kicker/target prompt.
3. `forge-behavior-v2:48c858c0c0537b06e88b866cec40dc68adaf142f`
   ethersworn_shieldmage ETB trigger → Effect (PreventArtifact).
   TIER-1: ETB via stack transfer, fixture Seismic Rupture (exact 2R
   pool, D3-proven NONE-intent) leaves Memnite (1/1 artifact nonflying)
   on BF — survival proves prevention.
4. `forge-behavior-v2:71482ff8159f5fc0b7805336a484e957cc20e4ba`
   hildibrand_manderville dies trigger (no OptionalDecider) → Effect
   (MayPlay self-as-Adventure). TIER-1: fixture Wrath (exact W2C2
   pool), host in GY, Effect in command with STPlay permission.
5. `forge-behavior-v2:ffe5f7ee06f0c2a7901475dc5168aad88a715c8d`
   leitmotif_composer sole AB$ Effect (Unblockable named-composer),
   cost 2U, pool U1C2. TIER-2 presence (consequence needs combat → D8
   upgrade path, never a blocker).
6. `forge-behavior-v2:6621cb87836967d18a6e79d35391618523aa4f54`
   burning_curiosity SP$ Dig X → Effect (MayPlay exiled). Blight
   additional cost unpaid (no creatures). Hypothesis H0: unpaid → exile
   exactly 2 (library_fill=2 → library 0, exile 2, Effect live).
   Fail-closed on any optional-cost prompt; if zones show 0 exiled,
   path defers to D6 (blight-paid variant needs creature + payment).
7. `forge-behavior-v2:a907c974dedcaebf3d1adb958ff8cdcc5666c2d3`
   electric_seaweed ETB → Effect (nested DieTrigger). Host is 0/4 Wall
   (survives Seismic). TIER-1 cascade: ETB, BF seaweed + bear + hawk,
   fixture Seismic kills bear → trigger kills hawk (1/1 flier, Seismic-
   immune — death proves trigger damage), seaweed BF, Effect command.
8. `forge-behavior-v2:4a791d62238e20dba66b255ae6176ad804f50db1`
   gideon_jura L11 AB$ Animate (cost +0 loyalty) → DBPrevent Effect.
   TIER-1: loyalty 6 unchanged after fixture Seismic (requires loyalty
   in canonical state + command-zone Effect assertion in repaired
   harness), Gideon BF as 6/6.

Target digest over these 8 ids must be frozen by the repaired preparer
at run time; no other D4 path may be exercised by D4a machinery.

## 5. Full 49-path disposition (path-prefix | card line | Effect shape | disposition)

- 0006052e tezzeret_betrayer_of_flesh L11 AB$ Effect emblem (loyalty 6) → D4b/D5
- 056d2d73 finale_of_revelation L7 X-spell GY-shuffle conditional Effect → D4d/D7
- 05d5031c strongbox_raider L8 raid+optional+ChooseCard remembered Effect → D4c/D6
- 0e81ef03 atsushi_the_blazing_sky L10 dies Charm-modal remembered Effect → D4c/D6
- 1c8c4168 aerial_extortionist L9 up-to-one-target (min 0) remembered Effect + combat → D4e/D8 (zero-target ETB stretch noted)
- 236a197c silence L4 SP static CantBeCast → D4a(1)
- 23c5728b furygale_flocking L7 RepeatEach token MustAttack Effect → D4f review
- 2a2bef86 conduit_of_worlds L6 GY-target optional conditional CantBeCast Effect → D4c/D6
- 2cfa2277 surge_to_victory L7 GY-target pump + damage-trigger Effect → D4c/D6
- 2d5a6d01 elspeth_knight_errant L7 emblem (loyalty 8) → D4b/D5
- 2f59baa7 solar_array L5 mana-ability nested SpellCast-trigger Effect (color choice) → D4c/D6
- 3a82c008 promise_of_loyalty L7 RepeatEach vow-choice sacrifice Effect → D4c/D6
- 3f49079f inkshield L4 combat-prevention replacement Effect → D4e/D8
- 44592e9c invisible_woman L10 attack-trigger costed targeted Unblockable Effect → D4e/D8 (scratch token recipe deleted)
- 46b2bb04 love_on_the_battlefield L7 exactly-two-attackers combat-trigger Effect → D4e/D8
- 48c858c0 ethersworn_shieldmage L7 ETB prevention Effect → D4a(3)
- 4a791d62 gideon_jura L11 0-loyalty animate self-prevention Effect → D4a(8)
- 4b162fa8 superior_foes_of_spider_man L12 cast-trigger may-exile MayPlay Effect → D4c/D6
- 5225d6d7 taunt_from_the_rampart L5 goad + can't-block Effect → D4e/D8
- 58e9c0ef gideon_jura L6 +2 delayed MustAttack Effect (opponent target) → D4c/D6
- 5ece6263 spark_double L7 clone-choice replacement Effect → D4c/D6
- 6151ed75 extract_power L5 face-down both-library exile MayPlay Effect → D4e/D8
- 6621cb87 burning_curiosity L6 optional-cost Dig MayPlay Effect → D4a(6) H0
- 69c9b5cf arbalest_elite L6 damage-AB subability self-untap Effect → D4e/D8
- 6db284ae summon_good_king_mog_xii L7 saga cast-trigger token-copy Effect → D4e/D8
- 71482ff8 hildibrand_manderville L7 dies MayPlay-self Effect → D4a(4)
- 75a3affd quintorius_loremaster L10 GY-target + AB-target MayPlay/replacement Effect → D4c/D6
- 783e2d9b human_torch L8 attack-trigger costed damage-trigger Effect → D4e/D8
- 79d60932 kang_dynasty L7 saga targeted goad/damage-draw Effect → D4c/D6
- 7a0360f5 gateway_sneak L6 Gate-ETB self-Unblockable Effect → D4e/D8
- 7a54c6e5 unstable_footing L5 kicker-gated static+damage Effect → D4a(2)
- 7f28d6c8 conspiracy_theorist L8 attack+discard-chain costed MayCast Effect → D4c/D6
- 8d38c2a7 heroic_return L5 GY-target + attacker-cost-reduction Effect → D4c/D6
- 9073ab21 winter_soldier_reborn_avenger L6 attack-trigger GY-target Effect → D4e/D8
- 914cf7d8 makeshift_mannequin L5 GY-target mannequin-counter Effect → D4c/D6
- 9175dd12 klaw_master_of_sound L11 combat-damage face-down-exile MayPlay Effect → D4e/D8
- 96a93b32 chandra_torch_of_defiance L11 emblem (loyalty 7) damage-trigger Effect → D4b/D5
- a907c974 electric_seaweed L8 ETB nested-die-trigger Effect → D4a(7)
- ad075f18 circle_of_protection_blue L5 ChooseSource prevention Effect → D4c/D6
- b777e433 willie_lumpkin_postman L8 combat-damage opponent-may-draw Effect → D4e/D8
- cac6cb0a intimidation_bolt L5 targeted-damage CantAttack Effect → D4c/D6
- cbd4a37a urianger_augurelt L9 AB cost-T MayPlay/reduce-cost Effect (needs exiled-with-source setup) → D4c/D6
- d0e3415b expressive_iteration L7 sort-choose remembered MayPlay Effect → D4c/D6
- d436ca3c progenitors_icon L7 ETB-ChooseType-gated flash-grant Effect → D4c/D6 (ChooseType D7-adjacent)
- db1baf87 okoye_mighty_and_adored L9 begin-combat targeted monarch-attack Effect → D4e/D8
- de8304a5 disintegrate L5 X-target NoRegen curse Effect → D4d/D7
- e20bced1 containment_construct L7 discard may-exile MayPlay Effect → D4c/D6
- ec4b7ecd palace_jailer L9 ETB opponent-target monarch-return Effect → D4c/D6
- ffe5f7ee leitmotif_composer L9 sole-AB Unblockable Effect → D4a(5)

Counts: D4a 8 + D4b 3 + D4c 21 + D4d 2 + D4e 14 + D4f 1 = 49 paths
(48 cards; gideon counted twice: L6→D4c, L11→D4a). Deferred buckets stay
UNKNOWN; no sibling inference.

## 6. Forbidden / boundary notes

No card-name production hacks (exact Name: lines only), no manual
outcome injection (zone/effect assertions evaluated, never written),
no shotgun qualification (8-path bounded set), no A/C/serial/shared
decision-contract change, no coverage promotion (stays FALSE), no run
registered yet. `UNKNOWN` remains `UNKNOWN` for all 49 until an
adjudicated run says otherwise.

## Exact next action

Repair D4a machinery (preparer per-path table with §4 freeze list +
harness postconditions/command-zone/loyalty/taxonomy fixes), run local
`py_compile` + focused gates, then persist source lock/PENDING and
execute the bounded 8-path D4a qualification.
