# WS33-D ranked qualification plan (2026-09-09)

D denominator: 920 UNKNOWN (actionable) + 1 retained PASS (excluded) +
1 template-missing blocked (`55bd7d1a...`, template-011, stays UNKNOWN).
All `owner_family=ACTION_COST_DECISION`. Partition: `WS33D_PARTITION.json`.

## Ranked families (yield order)

1. D1 — template-059 LifeGain STATE_ONLY, 22 paths. Proven
   Swiftwater-Cliffs idiom; 3 invocation shapes (triggered/activated/
   spell); zero decisions; CR 119 basis. EFFORT=low. NEXT.
2. D2 — template-061 LifeLose STATE_ONLY, 18 paths. Same harness
   shape as D1 (life-total sign flip). EFFORT=low.
3. D3 — template-039 DamageAll STATE_ONLY, 17 paths + template-042
   DamageResolve STATE_ONLY 2. Same life-total/state idiom. EFFORT=low.
4. D4 — template-049 EffectEffect STATE_ONLY, 49 paths. Largest
   STATE_ONLY group; per-path shape survey required first (emblem/
   continuous wrappers may need Sol adjudication for some members;
   escalate per-path, never block siblings). EFFORT=medium.
5. D5 — remaining STATE_ONLY tail, 140 paths across ~45 small groups
   (DelayedTrigger 044/18, SimpleKeyword 099/15, AbilityApiBased
   009/10, CountersPutAll 036/10, CleanUp 028/9, ImmediateTrigger
   054/9, BecomeMonarch 015/5, Proliferate 034/5, + singletons).
   Group into 2-3 harness batches by fixture shape. EFFORT=medium.
6. D6 — DECISION+REPLAY 225 (ManaEffect 063/105 first: B2 Cost-campaign
   precedent for mana-adjacent fixtures; then TapEffect 081/19,
   CounterEffect 030/15, RepeatEach 071/12, EffectEffect 048/13,
   Investigate 056/7, + tail). Requires WS01 decision tapes, all
   responses ACCEPTED in-option. EFFORT=medium-high.
7. D7 — DECISION+RNG+REPLAY 271 (DamageDeal 040/103, CountersPut
   037/92, Charm 020/46, ChooseType 027/8, ChooseColor 023/6, + tail).
   Requires WS01 + WS06 RNG tapes replay-served. EFFORT=high.
8. D8 — DECISION+HIDDEN+REPLAY 134 (Draw 047/110, Play 067/20, + tail)
   + HIDDEN 3 + DECISION+RNG+HIDDEN+REPLAY 39 (Discard 046/26,
   ChooseCard 021/11, + tail incl. template-011 siblings but NOT the
   template-missing id). Requires WS05 hidden observation 0-leak +
   full tapes. EFFORT=high. Draw-047 is the hard tail anchor.
9. Terminal dispositions: SOL_RULES_ADJUDICATION_REQUIRED (layer/LKI/
   replacement-order ambiguity) and *_INFRASTRUCTURE_PENDING are
   per-path terminal classifications, never batch blockers.

## Batch sizing rule

One queue item per batch while machinery is new (D1=22); combine only
sibling items sharing an exact harness shape after the harness is
proven (D2+D3 candidate). Every batch: frozen ids, PENDING checkpoint,
run, independent adjudication, repartition, counts, next batch.

## D1 selection freeze (this plan)

D1 = the 22 queue ids of (WS33D, template-059, STATE_ONLY,
LifeGainEffect), each proven UNKNOWN in queue + D ledger + Serial
ledger-arithmetic (Serial D unknown=920). Rationale: highest
evidence-yield per effort; reuses the only D-family idiom already
witnessed once (ede58d66, excluded). Expected assertions: exact life
delta + zone/tap/stack postconditions per invocation shape; replay
byte-equal; diagnostics empty; CR 119.1/119.3 citation for
EXTERNALLY_RULE_VALIDATED.
