# WS33-C Batch-3 selection framework (analysis, no definitions yet)

SOURCE_HEAD_AT_ANALYSIS = 148023070f
PARTITION = 11 EVIDENCED / 689 UNKNOWN (STATE_ONLY remaining 294)

## Reuse rules (proven machinery, unchanged)

ETB_SELF_MOVE / ETB_OTHER_ENTER (via-move registration) / PHASE_EOT_OUR_TURN
(+post-travel addAll) / PHASE_UPKEEP_OPP_TURN / PHASE_UPKEEP_OWN_TURN
(round-trip + opp library fill); sub-link + terminal pair matching;
integer ordering (sub parent<child, terminal child<parent-same-id);
reference-identity attribution (no names); forced-choice bundles
(singleton + actor + caller + selected + covering assertion); 7-method
caller-attributed tripwire (incidental rule); SBA settle; roster/damage
diagnostics; screen gate (Mode TgtChoose + Dig rules); ApiType allowlist;
anti-double-credit; source seal; hash sealing.

## Ranked families (from regenerated WS33_C_T113_SURVEY.json, 98 families)

1. AnimateDead ETB_SELF:TrigReanimate + ChangesZone:DBCleanup (4 rows,
   CLEAN screen): aura + graveyard-reanimate fixture (pre-place creature
   in own graveyard, Aura enters via... cast targeting? Animate Dead is an
   Aura cast -> TARGETS in real play; test moveTo bypasses cast targeting
   but the aura must attach on ETB (Defined Enchanted) — needs a legal
   object. Feasibility: MEDIUM. Requires fixture design (graveyard setup +
   attach legality), no new machinery.
2. Upkeep-own round-trip reuses (proven by banshee): other own-upkeep
   triggers with assertable semantics (survey PHASE:Upkeep rows).
3. EOT-travel reuses (proven by gnarlbark/biogenic pattern): other EOT
   triggers with assertable terminal/sub links.
4. TrigDeath/TrigEffect ChangesZone triggers (CLEAN, 3 rows): need death
   outlets (Thunder-DamageAll style casualty fixture, proven pattern).
5. Kang DigUntil (3 rows): screen-CLEAN but dig reveals cards -> treat as
   HIDDEN until proven otherwise (do NOT trust screen blindly here).
6. ABILITY_ACTIVATED_OR_SPELL rows: DEFAULT EXCLUDE (cost surface = WS33B
   ownership) unless a row is provably costless.

## Explicit exclusions (standing)

- Template-105/119 (scope cap, separate contracts).
- Kappa-class Effect-statics (assertion vocabulary gap).
- Targeted first links (template-107, decision protocol = scope decision).
- Combat/cast-cost/search/reveal/RNG rows.
- Gnarlbark-class EOT silence: closed for EOT-travel pattern; new phase
  kinds need their own probe evidence.
- Vacuous/terminal-no-op semantics (insufficient muscle per item 4).

## Exact next action

Pick highest-yield family (recommend AnimateDead-4 or upkeep-own reuses),
write definitions + checker run (expect new digest), update workflow
counts, commit, push, PENDING, run, adjudicate per-path, repartition.

TURN_STATUS = INTERRUPTED
TASK_COMPLETE = NO
