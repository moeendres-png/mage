# WS33-D D4c target/choice survey — 21 paths, native-mechanism classification

Date: 2026-09-10. Branch: `work/ws33-d-high-throughput-20260907`.
Source lock reverified (DIRECTLY_VERIFIED): HEAD
`b456c37201ddb76cded207383cfaba5723489afd` == origin, TREE
`12122e5fc4963a8a416da78cda42150a3b157f34`, clean.
`TASK_COMPLETE=NO`. `TURN_STATUS=RUNNING`. No run registered; no D4c
machinery built yet. Retained D4a/D4b evidence rechecked and valid (no
rerun): PASS checkpoints `ABC_D4_RUN_34411858516_PASS.md` and
`ABC_D4B_RUN_34419391829_PASS.md` present; live GitHub run 34419391829
conclusion success; D-local partition EVIDENCED=36 / REMAINING_UNKNOWN=884.
D4b is terminal and is not rerun.

## 1. Frontier (DIRECTLY_VERIFIED against queue + ledger + pin scripts)

The 21 D4c paths are the template-049 members deferred from D4a/D4b with a
target/choice gate on the path to the ledger `Effect` SVar. All 21 scripts
read in full at Forge pin `8c7e9afb8e6caee88644b94e25da5852e36f8928`;
(card, Effect-line) verified against `WS33_INTEGRATED_CLOSURE_LEDGER.jsonl`
source_provenance; all 21 `current_status=UNKNOWN`, none partition-evidenced.

## 2. Per-path classification (engine-trace evidence at pin)

Shared finding: every ledger `DB$ Effect` resolves via
`EffectEffect.resolve` with zero controller calls — all 21 Effect lines are
themselves decision-free; every decision sits strictly before the Effect
line. Bridge kinds below refer to the retained WS01 strict-decision-boundary
patch (`research/greenfield-qualification/forge-patches/strict-decision-boundary.patch`)
plus the retained `apply-ws33-target-selection.py` overlay (G-proven,
externalizes `TARGET_SELECTION` via `TargetSelection.chooseExternalTargets`).

| # | path prefix | card Effect line | entry | decision sequence to Effect (engine method -> bridge kind) | discretionary? | hidden/RNG | setup | cluster |
|---|---|---|---|---|---|---|---|---|
| 1 | 2cfa2277 | surge_to_victory L7 | SP cast (sorcery) | 1x `chooseTargetsFor` (root ChangeZone ValidTgts own-GY instant/sorcery) -> TARGET_SELECTION. PumpAll X automatic (`calculateAmount`); Effect automatic. | yes (GY choice) | none | GY instant/sorcery + mana | T1 |
| 2 | 8d38c2a7 | heroic_return L5 | SP cast (instant) | 1x `chooseTargetsFor` (SUBABILITY DBReturn ValidTgts own-GY creature; `setupTargets` walks root+sub, SpellAbility.java:2135). ETBCreat replacement inert for non-Hero fixture (`getReplacementList` empty -> `NotReplaced` before any controller call). ReduceCost static. | yes | none | GY creature + mana | T1 |
| 3 | 914cf7d8 | makeshift_mannequin L5 | SP cast (instant) | 1x `chooseTargetsFor` (root ChangeZone ValidTgts own-GY creature) -> TARGET_SELECTION. WithCountersType MANNEQUIN + Effect automatic. | yes | none | GY creature + mana | T1 |
| 4 | cac6cb0a | intimidation_bolt L5 | SP cast (instant) | 1x `chooseTargetsFor` (root DealDamage ValidTgts Creature) -> TARGET_SELECTION. Fixed NumDmg 3 (no division params); Effect/ForbidAttack automatic. | yes | none | BF creature + mana | T1 |
| 5 | 05d5031c | strongbox_raider L8 | ETB trigger | `confirmTrigger` (OptionalDecider raid) -> CONFIRM_TRIGGER; Dig ChangeNum All (no choice); `chooseCardsForEffect` (ChooseCard Mandatory 1-of-2 remembered) -> ENTITY_CARD_SELECTION; Effect decision-free. | yes/yes | none | raid (attackers declared) | E-conf |
| 6 | 0e81ef03 | atsushi_the_blazing_sky L10 | dies trigger | `chooseModeForAbility` (Charm ExileTwo vs CreateTreasure, CharmEffect.java:270) -> MODE_SELECTION; Dig All (no choice); Effect decision-free. Mandatory trigger (no OptionalDecider). | yes | none | own creature dies | M-modal |
| 7 | 2a2bef86 | conduit_of_worlds L6 | AB activation | `chooseTargetsFor` (AB ValidTgts own-GY nonland) -> TARGET_SELECTION; `chooseSingleEntityForEffect` (PlayEffect resolve, forced 1-option) -> ENTITY_SINGLE_SELECTION; `confirmAction` (may-cast) -> CONFIRM_ACTION; then casts chosen card. ConditionCheckSVar X + SorcerySpeed are legality gates. | yes | none | GY nonland + main phase + zero casts | A-multi |
| 8 | 2f59baa7 | solar_array L5 | AB mana (no stack) | `chooseColor` (Produced Any, ManaEffect.java:161) -> COLOR_SELECTION. Effect (SpellCast trigger) decision-free. | yes (1-of-5) | none | untapped Array | C-color |
| 9 | 3a82c008 | promise_of_loyalty L7 | SP cast (sorcery) | Per-player `chooseCardsForEffect` (PutCounter Choices + Chooser Player.IsRemembered, CountersPutEffect.java:195-240) -> ENTITY_CARD_SELECTION x N players; choosing actor INCLUDES the opponent (second principal required). RepeatEach serial (no order decision). SacAllOthers/Effect automatic. | yes | none | every player controls a creature | P-multi |
| 10 | 4b162fa8 | superior_foes_of_spider_man L12 | cast trigger | `confirmTrigger` (OptionalDecider SpellCast cmcGE4) -> CONFIRM_TRIGGER; ChangeZone Defined (automatic); Dig All (no choice); Effect (MayPlay, Permanent) decision-free. | yes | none | host BF + cast cmc4+ spell | E-conf |
| 11 | 58e9c0ef | gideon_jura L6 | loyalty AB activation | Zero target prompts in 1-opponent games: card-candidate list empty -> pristine auto-target of the single non-card candidate (TargetSelection.java:156-168), no TARGET_SELECTION issued. Loyalty payment automatic. DelayedTrigger Effect/MustAttack automatic at activation (fires on opponent next upkeep, beyond the line). | no (forced) | none | production planeswalker BF (D4b doubling reusable) | A-auto |
| 12 | 5ece6263 | spark_double L7 | ETB replacement | BLOCKED under strict WS01: `ReplacementHandler.run` -> `chooseSingleReplacementEffect` -> reject REPLACEMENT_ORDER (fires even for a single replacer). Conditionally: `confirmReplacementEffect` (may-copy) + `chooseSingleEntityForEffect` (copy target, CloneEffect.java:94). | yes | none | another controlled creature/planeswalker | X-blocked |
| 13 | 75a3affd | quintorius_loremaster L10 | end-step trigger + AB | Turn-phase passage to own end step required (no turn passing under frozen D boundary); trigger target -> TARGET_SELECTION; Spirit token; AB cost `Sac<1/Spirit>` -> `HumanCostDecision` `showAndWait` REJECT (no single-short-circuit); exiled-with-source target -> TARGET_SELECTION. >=3 decisions, one hard reject. | yes | none | multi-phase setup | H-heavy |
| 14 | 79d60932 | kang_dynasty L7 | saga chapter trigger | Lore progression automatic (ETB LORE:1 + MAIN1 tick); TargetMin 0: zero candidates -> silent complete, no request; one candidate -> exactly one TARGET_SELECTION, loop exits via isMaxTargetChosen (no DONE request). Goad/Effect automatic. | optional-target | none | saga lore phases | T2-trig |
| 15 | 7f28d6c8 | conspiracy_theorist L8 | discard trigger | Discard outlet: attack (`DECLARE_ATTACKERS` reject) or other outlet; discard cost -> `InputSelectCardsFromList.showAndWait` REJECT; ExileFromGrave cost -> `chooseEntitiesForEffect` ENTITY_MULTI_SELECTION (bridged) but unreachable past the REJECT. | yes | none | discard outlet + combat | H-heavy |
| 16 | ad075f18 | circle_of_protection_blue L5 | AB activation | `chooseSingleEntityForEffect` 4-arg (ChooseSource candidates incl. divider pseudo-cards, ChooseSourceEffect.java:128-136) -> ENTITY_SINGLE_SELECTION; Effect ConditionDefined ChosenCard (check only). Forced if exactly 1 blue source. | conditional | none | CoP BF + {1} + blue source | E-single |
| 17 | cbd4a37a | urianger_augurelt L9 | AB activation (Effect itself decision-free) | Setup kills it: Draw Arcanum Dig Optional (no PromptToSkip -> min 0, ENTITY_MULTI_SELECTION extra decision); ExileFaceDown -> hidden-info requirement; second T activation (untap/turn pass). | yes (setup) | hidden (face-down exile) | exile setup + untap | H-heavy |
| 18 | d0e3415b | expressive_iteration L7 | SP cast (sorcery) | 2x `chooseEntitiesForEffect` (Dig 3->1, Dig 2->1, DigEffect.java:346) -> ENTITY_MULTI_SELECTION x2; Dig 1 All (no choice); Effect decision-free. Library look principal-scoped (`NoReveal`/`NoLooking`, engine show/restore). | yes/yes | hidden (library look) | UR mana + 3-card library | E-dig |
| 19 | d436ca3c | progenitors_icon L7 | AB activation (Effect decision-free) | Setup BLOCKED: ETB replacement routing -> reject REPLACEMENT_ORDER (even single replacer). Conditionally: `chooseSomeType` has NO WS01 hunk -> generic GUI_ONE bridge (untyped). | yes | none | host BF + chosen type | X-blocked |
| 20 | e20bced1 | containment_construct L7 | discard trigger | `confirmTrigger` (OptionalDecider Discarded) -> CONFIRM_TRIGGER; ChangeZone Defined TriggeredCard (automatic, ChangeZoneEffect.java:1199-1200); Effect decision-free. | yes | none | discard outlet (fixture supplies; discard decisions outside this path) | E-conf |
| 21 | ec4b7ecd | palace_jailer L9 | ETB triggers (x2) | TrigMonarch BecomeMonarch decision-free; TrigExile target -> TARGET_SELECTION on stack admission; two simultaneous same-controller triggers -> `getGui().order` -> GUI_ORDER (bridged, not rejected). Mandatory (no Optional). | yes | none | host ETB + opponent BF creature | T2-trig |

Actor analysis: paths 1-4, 6, 8, 10, 11, 16, 18 use the single actor only.
Path 9 (promise) requires opponent-principal choices. All others are
actor-scoped. State-restoration: none beyond engine-owned show/restore for
path 18 (hidden) — out of T1 scope. RNG: zero across all 21 Effect paths
(no shuffle/random on any path to the ledger line).

## 3. Capability clusters (shared native mechanism only)

- T1 SPELL_SINGLE_TARGET (4): 1-4. Production SP cast from hand; exactly
  one mandatory cast-time `chooseTargetsFor` -> TARGET_SELECTION; zero other
  prompts; no hidden/RNG/combat/turn-pass. ONE mechanism (proven: G target
  campaigns; engine walk `setupTargets` covers root+sub, so heroic_return's
  subability-level target joins genuinely).
- T2 TRIGGER_TARGET (2): 14, 21. Trigger-entry targets (+ GUI_ORDER for 21,
  lore phases for 14). Shares TARGET_SELECTION transport with T1 but differs
  in entry (ETB/chapter, not cast) and second decisions. Ordered second.
- E-conf OPTIONAL_CONFIRM (3): 5, 10, 20. Shared `confirmTrigger` only;
  setups diverge (raid+combat / cmc4+ cast / discard outlet) and path 5 adds
  ENTITY_CARD_SELECTION. Ordered third (needs per-path setup drivers).
- E-single ENTITY_SINGLE (1): 16. ChooseSource single-pick (+ divider
  re-prompt quirk). Ordered with E-dig.
- E-dig ENTITY_MULTI_DIG (1): 18. Two dig picks + hidden library look.
  Needs hidden-observation machinery (WS05) on top of entity transport.
- M-modal MODE_SELECTION (1): 6. Charm modal + dies setup. Alone.
- C-color COLOR_SELECTION (1): 8. Mana color pick on a non-stack ability.
  Alone.
- A-multi ACTIVATION_MULTI (1): 7. AB entry + 3 bridged decisions incl.
  playing the chosen card. Alone.
- A-auto ACTIVATION_FORCED (1): 11. No decision at all in 1-opponent games;
  needs D4b-style planeswalker entry. Smallest alone; candidate stretch only
  after T1-T2.
- P-multi MULTI_ACTOR (1): 9. Opponent-principal choices; second-principal
  decision plumbing. Alone, last among bridged.
- H-heavy SETUP_HEAVY (3): 13, 15, 17. Each blocked by REJECT-grade cost
  paths (sac/discard selection `showAndWait`), turn passing, combat, or
  hidden setup. No implementation without AUTHORITY_GATE decisions.
- X-blocked REPLACEMENT_ORDER (2): 12, 19. Strict WS01 rejects
  `chooseSingleReplacementEffect` before any size shortcut, so both ETB
  setups are unreachable. Terminally blocked pending Sol/rules adjudication
  of replacement-order scope; never blocks siblings. Recorded as
  SOL_RULES_ADJUDICATION_REQUIRED candidates, not UNKNOWN-in-progress.

21 = 4 + 2 + 3 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 3 + 2. No grouping by fixture
name or desired outcome; clusters share native controller paths.

## 4. Family decision

T1 (surge_to_victory, heroic_return, makeshift_mannequin, intimidation_bolt)
is the highest-leverage coherent subfamily: 4 paths, one entry (production
spell cast, D1/D3/D4a-proven), one decision kind (TARGET_SELECTION,
G-proven transport + retained overlay), presence-tier assertions, no
hidden/RNG/combat/turn-pass, per-case fixture divergence limited to zone of
a directly-placed fixture card. Machinery: D4c preparer/filter/harness/
certifier/workflow cloned from retained D4b (semantically appropriate:
same record/replay/tape/RNG/hidden/evidence skeleton) with the drive
replaced by single-target production casts and the provider extended by one
TARGET_SELECTION branch (unique authoritative match of the case-designated
ENTITY intent; zero/multiple matches fail closed; any other kind fails
closed). The retained target-selection overlay is added to the D4c workflow
runtime (same application point as G/A-rest runs); no new shared-surface
change. Remaining 17 stay UNKNOWN with the ordered plan above; X-blocked (2)
go to AUTHORITY_GATE, never retried experimentally.

## 5. Exact next action

Build D4c-T1 machinery (preparer/filter/harness/certifier/workflow),
run py_compile + preparer dry-run + digest stability + certifier/filter
negative self-tests + pin-derived stub-compile + overlay anchor dry-run,
then freeze source and register the single 4-path D4c qualification run.

## 6. Research addendum — native decision-surface record (2026-09-10)

No scope change, no restart, no additional run authorized by the note. T1
compliance verified against each constraint: (1) T1 uses exactly one native
callback, `chooseTargetsFor` (taxonomy: chooseTarget/chooseTargetsFor); no
chooseNumber/chooseMode/chooseUse/combat-declare/order/mana-payment callback
on any T1 path (surveyed per-path; the record run fails closed on any other
request, with decision-requests.jsonl as empirical proof). (2) Legal options
come from Forge itself (`Target.getAllCandidates` + validity filtering in
the retained overlay); the provider only unique-matches the designated
ENTITY semantic — no fixture/card-name/outcome legality reconstruction.
(3) No yield/auto-pass/interrupt/macro/GUI-preference machinery used as
priority proof: single actor MAIN1, no priority passing, no turn passing.
(4) No macros. (5) No GameState combat restoration touched. (6) No new RNG
plumbing: retained WS06 MyRandom seam (beginGameScope/replay-served), 0 RNG
events expected. (7) Contract preserved verbatim in the D4c provider.

Per-cluster surface classification:

| cluster | paths | classification | native callback(s) / gap |
|---|---|---|---|
| T1 SPELL_SINGLE_TARGET | 4 | NATIVE_FORGE_DECISION_SURFACE | `chooseTargetsFor` -> TARGET_SELECTION; options `Target.getAllCandidates`; transport = unique match only |
| T2 TRIGGER_TARGET | 2 | NATIVE_FORGE_DECISION_SURFACE | same target surface; trigger entry; `getGui().order` via bridged GUI_ORDER adapter (14 silent Min0, 21 order+target) |
| E-conf OPTIONAL_CONFIRM | 3 | NATIVE_FORGE_DECISION_SURFACE | `confirmTrigger` (CONFIRM_TRIGGER); strongbox adds `chooseCardsForEffect` (ENTITY_CARD_SELECTION) |
| E-single ENTITY_SINGLE | 1 | NATIVE_FORGE_DECISION_SURFACE | `chooseSingleEntityForEffect` (ENTITY_SINGLE_SELECTION); divider re-prompt is engine-internal |
| E-dig ENTITY_MULTI_DIG | 1 | NATIVE_FORGE_DECISION_SURFACE | `chooseEntitiesForEffect` x2 (ENTITY_MULTI_SELECTION); hidden look via engine show/restore |
| M-modal MODE_SELECTION | 1 | NATIVE_FORGE_DECISION_SURFACE | `chooseModeForAbility` (MODE_SELECTION); candidates `CharmEffect.makePossibleOptions` |
| C-color COLOR_SELECTION | 1 | NATIVE_FORGE_DECISION_SURFACE | `chooseColor` (COLOR_SELECTION) on non-stack mana ability |
| A-multi ACTIVATION_MULTI | 1 | NATIVE_FORGE_DECISION_SURFACE | `chooseTargetsFor` + `chooseSingleEntityForEffect` + `confirmAction`; all bridged |
| A-auto ACTIVATION_FORCED | 1 | NATIVE_FORGE_DECISION_SURFACE | no prompt (pristine single-non-card auto-target); no transport needed |
| P-multi MULTI_ACTOR | 1 | NATIVE_FORGE_DECISION_SURFACE | `chooseCardsForEffect` per player incl. opponent principal; needs second-principal plumbing |
| H-heavy quintorius | 1 | ENGINE_GAP | `HumanCostDecision` sac-cost `showAndWait` REJECT + turn-phase passage |
| H-heavy conspiracy | 1 | ENGINE_GAP | discard-cost `showAndWait` REJECT + combat entry |
| H-heavy urianger setup | 1 | NATIVE_FORGE_DECISION_SURFACE | setup Dig choice bridged (ENTITY_MULTI_SELECTION); cluster deferred only by hidden face-down + second-activation dependency, not by gap |
| X-blocked (2) | 2 | ENGINE_GAP | `chooseSingleReplacementEffect` rejected before any option surfaces; SOL adjudication candidates |

No CUSTOM_TRANSPORT_ONLY and no UNKNOWN clusters remain: every bridged path
is keyed to a named native callback with patch-hunk evidence; every gap is
a named engine rejection or boundary, never an inference.
