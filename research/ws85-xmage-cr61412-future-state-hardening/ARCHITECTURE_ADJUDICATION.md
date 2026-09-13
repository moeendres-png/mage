# WS85 Architecture Adjudication (XHIGH, read/test-first, no production edits)

Source: Foundry adjudicator at XHIGH on branch
ws85/xmage-cr61412-future-state-hardening-20260913 at ffefc19536 (CODE_DERIVED;
no files edited by the adjudicator; runtime behavior taken from WS81/WS83
evidence, not re-verified by the adjudicator).

## The 10 Phase-1 answers (condensed; full citations in workstream record)

1. Can the current WS83 helper mutate any object other than the entering
   permanent? YES (proven). Live-reference fetch (GameImpl.java:845-847) into
   live field (ContinuousEffects.java:491-493 + Battlefield.java:137-139), then
   real-Game mutating apply (ContinuousEffects.java:521 via
   ContinuousEffect.java:36 + ContinuousEffectImpl.java:116-121) into global
   bodies: Humility.java:67-72 (all creatures removeAllAbilities),
   LoseAllAbilitiesAllEffect.java:38-43, LoseAbilityAllEffect.java:80-98
   (affectedObjectList prune + discard), YixlidJailer graveyard loop
   (CardImpl.java:294-298 persists lostAllAbilities), LoseAbilityTargetEffect
   (other permanents). finally (ContinuousEffects.java:532-544) restores only
   entering abilities + removes the insertion. Incomplete by construction.

2. Can any invoked apply have non-idempotent/externally observable side effects?
   YES. Transient battlefield membership window (LinkedHashMap iteration/order),
   persistent ability stripping of others (PermanentImpl.java:487-490, no
   inverse), effect-lifetime discard, graveyard flag persistence, stripped-window
   reads via MageObjectImpl.java:170-176.

3. Existing pure applicability/filter API avoiding apply()? NO. ContinuousEffect
   exposes only apply/hasLayer/isInactive/init/dependency accessors; layer-6
   filters are encapsulated without a wouldApply predicate.

4. Existing safe snapshot facility for hypothetical projection? NO lightweight
   facility. Only heavyweight deep copies (GameState.java:288-290,
   Battlefield.java:35-37, GameImpl.java:206-281) and AI-simulation full copies
   (Game.java:336-343) — architecture-sized per-probe, none wired as a probe.

5. Can a copy of entering be evaluated without live membership? NO with current
   removers: getActivePermanents reads only field (Battlefield.java:258-270),
   ignoring permanentsEntering (Battlefield.java:21,167-169); a detached copy is
   invisible to Humility-style loops. Requires a new pure path calling each
   effect's own filter.match directly.

6. Smallest non-mutating systemic design: add one pure probe method to the
   effect hierarchy (default false), overridden per layer-6 Lose family to reuse
   its OWN filter/target state; helper evaluates entering.copy() through it with
   existing hasLayer/Outcome.LoseAbility/getOrder/isInUseableZone gating. No
   battlefield insertion, no apply() in probe, no second engine, no copied card
   logic. (This is the implemented WS85 design.)

7. Bounded claim implementable now: self-scope entering replacement for
   ENTERS_THE_BATTLEFIELD* suppressed iff a pre-existing, usable layer-6
   LoseAbility remover pure-matches the entering object; otherwise allow.
   Fixed-set/targeted/graveyard-unknown, missing entering, or probe error are
   defined non-suppression inputs. Timestamp/dependency ordering beyond getOrder,
   own-statics interplay, already-applied replacement interplay, copy/PT layers
   are explicitly out of scope. No card-name/H01 branches; Vesuva-style filter
   precision required (creature-only removers must not match lands).

8. On uncompletable evaluation: never silent, never suppress-on-uncertainty
   (suppressing would break normal Clones), never mutate-to-complete. Required:
   zero live mutation + allow + loud warn for defined-unknown inputs; explicit
   propagation (engine failure) for evaluation errors. Suppression requires
   positive pure-match evidence only.

9. Prevention-branch helper use: vacuously dead today (PreventionEffectImpl
   checksEventType is damage-only), asymmetric gating; disposition: remove or
   gate identically with pure path. (WS85 kept the call with the pure helper +
   documented rationale: harmless future-proofing.)

10. Tests proving no live-state leakage: NONE in WS81/WS83 corpus (functional
    outcomes only). Required new corpus: other-permanent ability inventories,
    graveyard stability, targeted fixed-set stability, membership hygiene,
    UNKNOWN-warn behavior. (WS85 landed P0/P1/P2/F1 to this specification.)

## Verdict on WS83 helper

Non-mutating contract: FAIL. Silent fail-open: FAIL (debug-only allow).
Functional green does not cure live-state leakage.

Root-cause class: ENGINE_DEFECT (shared, provider/harness-agnostic).
First failing boundary:
ContinuousEffects.wouldLoseEnteringAbilityViaPreexistingLayer6
(addPermanent + remover.apply(Layer6) + partial restore), invoked from
getApplicableReplacementEffects during replaceEvent for ENTERS_THE_BATTLEFIELD*.
Minimal repair surface: ContinuousEffects helper + guard, pure probe overrides
in the layer-6 LoseAbility families + Humility, prevention-branch disposition,
ReplacementEffectImpl comment. No authority gate (no Rules-policy ambiguity).

Gate: READ_FIRST_XHIGH_ADJUDICATION = PASS (persisted before any production edit).
