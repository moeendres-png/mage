# WS83 Architecture Adjudication (persisted)

Source: Foundry adjudicator at XHIGH, read/test-first, no production edits (CODE_DERIVED;
prior runtime A=FAIL/B,C=PASS taken from WS81 evidence, not re-verified by adjudicator).

1. Forbidden H01-A prompt call chain (CODE_DERIVED):
   - Spell resolves via controller.moveCards to BATTLEFIELD (Spell.java:418-420).
   - ZonesHandler zone-change gate + entering blueprint + entersBattlefield
     (ZonesHandler.java:402,427,449-452).
   - PermanentImpl.entersBattlefield SELF event then OTHER event + game.replaceEvent
     (PermanentImpl.java:1389,1406-1408).
   - GameImpl/GameState replaceEvent dispatch (GameImpl.java:3619-3625;
     GameState.java:1045-1053) into ContinuousEffects.replaceEvent (850-968).
   - getApplicableReplacementEffects admits Clone effect (354-391); no future-ability check.
   - EntersBattlefieldEffect.replaceEvent optional chooseUse prompt at line 101
     (EntersBattlefieldEffect.java:91-103); surfaced by TestPlayer.chooseUse strict-mode
     Missing CHOICE failure (WS81H01CorrectedTest.java:49-52,79-81).
   - Participants: Clone EntersBattlefieldAbility + CopyPermanentEffect (Clone.java:27);
     Humility SimpleStaticAbility layers 6/7b (Humility.java:31-32,62-81);
     downstream CopyPermanentEffect.apply / GameImpl.copyPermanent / CopyEffect.init/copyToPermanent
     not reached in correct H01-A.

2. Earliest authoritative applicability boundary (CODE_DERIVED):
   ContinuousEffects.getApplicableReplacementEffects (354-391) — sole systemic filter before
   616.1 ordering/chooseReplacementEffect (891-899) and before any prompt side effect.
   Current checks: event type, applied-effects dedup, useable-zone, used, scopeRelevant/selfScope,
   per-effect applies. No future-characteristics/ability-existence check.
   Contrast: preventedByRuleModification calls checkAbilityStillExists (817-821, 423-468);
   layer apply calls isAbilityStillExists (1220-1243). Replacement path omits both.
   EntersBattlefieldEffect.applies/replaceEvent is symptom, not repair location (per-effect,
   downstream, duplicates layer semantics, misses 616.1a-d ordering and consumed loop).

3. Future battlefield object (CODE_DERIVED, negative): none.
   Battlefield.field vs permanentsEntering separate (Battlefield.java:21,167-169);
   getAllActivePermanents/getActivePermanents read only field (188-270), so entering Clone
   never visible to Humility loop (Humility.java:67-68).
   AbilityImpl.isInUseableZone entering shortcut returns true unconditionally
   (AbilityImpl.java:1331-1333). GameImpl scopeRelevant + getPermanentEntering returns raw
   blueprint, not hypothetical post-Humility object. Grep 614.12/would-exist/future-state in
   Mage/src/main/java returns only ReplacementEffectImpl comment + scopeRelevant flag.
   PermanentCard copies printed abilities with no layer projection before replacement filtering.

4. Reusable machinery (CODE_DERIVED): ContinuousEffects.getLayeredEffects/apply layer pipeline
   (189-224, 971-1160); Layer CopyEffects_1/AbilityAddingRemovingEffects_6/PTChangingEffects_7;
   HumilityEffect hasLayer/applies as authoritative layer-6 remover to query, not copy;
   applyContinuousEffect/isAbilityStillExists and checkAbilityStillExists hasAbility patterns;
   AbilityImpl.hasSourceObjectAbility/isInUseableZone; GameState.addAbility/addEffect registration;
   PermanentImpl.addAbility/removeAllAbilities; CopyEffect.init entering handling;
   Battlefield.permanentsEntering + scopeRelevant infrastructure.

5. Smallest systemic repair surface (CODE_DERIVED, ranked):
   (1) ContinuousEffects.getApplicableReplacementEffects + shared 614.12 helper reusing layer-6
   machinery — one place covering all self-copy replacements.
   (2) Shared helper (e.g. wouldAbilityExistOnFutureBattlefield) evaluating layer-6 removers
   without mutating live state — acceptable, not a parallel engine.
   (3) EntersBattlefieldEffect guard — last; blanket optional-disable forbidden (breaks B/C).
   Out of surface: Clone/Humility/CopyPermanentEffect/CopyEffect/tests/adapters/providers/harness.

6. Over-broad repair regressions (CODE_DERIVED): normal clones (CloneTest Bloodgift/sacrifice/
   Vesuvan color, AdaptiveAutomaton subtype, face-down 2/2); H01-B/C discrimination;
   optional ETB replacements generally (AdaptiveAutomaton, Tribute/Sunburst/X-counters/
   ChooseColor/ETB-tapped); ETB triggers vs replacements (testCloneTriggered); copy-after-entry
   and Humility-leaves restoration; aura-retarget; MDFC/Room/prototype; 616.1 ordering, target
   legality, duplicate-prompt loops.

7. Authority gate (CODE_DERIVED): none required before implementation. Rules policy already bound
   by CPL main 79c5af1 corrected cases + adjudication; 614.12 text already in
   ReplacementEffectImpl:14-24 (outdated phrasing). Repair is ENGINE_DEFECT within existing
   ContinuousEffects/layer/scopeRelevant contract. Escalate to AUTHORITY_GATE only for
   blanket-disable, card-name branch, parallel engine, or H01/614.12 reinterpretation.

Gate: READ_FIRST_XHIGH_ADJUDICATION = PASS (inspected Clone, Humility, EntersBattlefieldAbility/
Effect, CopyPermanentEffect/CopyEffect, ContinuousEffects/ContinuousEffectImpl/layers,
ReplacementEffectImpl, GameState.replaceEvent, Permanent enters flow, ZonesHandler, Battlefield,
GameImpl copy/scope facilities, WS81 test, CloneTest, HumilityTest, 614.12 history).
H01-A contract FAIL, H01-B/C PASS (CODE_DERIVED from preserved red + static chain).
Root-cause class ENGINE_DEFECT at getApplicableReplacementEffects (admits Clone ETB replacement
under scopeRelevant without future-state check).
