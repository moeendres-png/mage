# WS83 Implementation (systemic Rules-Core, no card-name hacks)

Production files modified (2):

1. `Mage/src/main/java/mage/abilities/effects/ContinuousEffects.java`
   - `getApplicableReplacementEffects`: both replacement and prevention loops now consult
     `isSelfEnteringReplacementWithoutFutureAbility` before `effect.applies` and skip the
     (effect, ability) pair when true. All other events, non-self effects, and other-source
     effects are untouched.
   - New `in61412FutureCheck` transient reentrancy guard (fail-closed: nested checks allow).
   - New `isSelfEnteringReplacementWithoutFutureAbility`: true only for ETB event types
     (SELF/CONTROL/COPY/OTHER), `hasSelfScope`, `event.target == ability.source`,
     entering object present via `game.getPermanentEntering`. Otherwise false. All
     exceptions fail closed to false (existing behavior).
   - New `wouldLoseEnteringAbilityViaPreexistingLayer6`: saves entering abilities (shallow),
     temporarily exposes entering to battlefield queries via `addPermanent`, collects active
     layer-6 `Outcome.LoseAbility` removers in timestamp order (no timestamp mutation; direct
     `layeredEffects` snapshot sorted by `getOrder`), checks each source ability usability
     (`StaticAbility.isInUseableZone(game,null,null)`), reuses each remover's own `apply`
     filter logic, then tests `entering.hasAbility(enteringAbility, game)`. Restores entering
     abilities and removes the temporary battlefield exposure in `finally`.
   - Rationale: reuses existing continuous-effect/layer authority instead of duplicating it;
     Humility custom effect, generic `LoseAllAbilitiesAllEffect` (Dress Down), targeted and
     fixed-set removals, graveyard removers (Yixlid Jailer), and gains/becomes effects all
     behave per their own code. No strings "Clone"/"Humility", no H01 branches, no blanket
     copy suppression, no prompt injection, no second engine.

2. `Mage/src/main/java/mage/abilities/effects/ReplacementEffectImpl.java`
   - Comment only: updated the quoted 614.12 text from the outdated "ignoring ... any other
     source" phrasing to the current "continuous effects that already exist and would apply"
     wording, noting that ContinuousEffects establishes self-scope entering applicability.

Tests added (1 file, actual cards, no production bypass):

- `Mage.Tests/src/test/java/org/mage/test/serverside/ws83/WS83CR61412SystemicTest.java`
  - `testPhantasmalImageHumilityFirst_NoCopyDecision_DiesAfterHumilityLeaves`: same machinery
    (EntersBattlefieldAbility + CopyPermanentEffect, printed 0/0) with a different card;
    strict mode, zero decisions, 1/1 under Humility, 0/0 -&gt; SBA after Disenchant.
  - `testVesuvaHumilityFirst_CopyPreserved`: land copy under creature-only Humility still
    offers Yes + land choice (strict consumption proves occurrence); filter precision,
    anti-blanket control.
  - `testCloneDressDownFirst_NoCopyDecision`: generic engine remover class
    (`LoseAllAbilitiesAllEffect` via Dress Down) also suppresses Clone; 0/0 -&gt; SBA.

Preserved history: `Mage.Tests/.../serverside/ws81/WS81H01CorrectedTest.java` unmodified
(historical red preserved; post-fix green is fresh behavior, not edited expectations).
