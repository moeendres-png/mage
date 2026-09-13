package org.mage.test.serverside.ws85;

import mage.abilities.Ability;
import mage.abilities.common.SimpleStaticAbility;
import mage.abilities.effects.ContinuousEffectImpl;
import mage.constants.Duration;
import mage.constants.Layer;
import mage.constants.Outcome;
import mage.constants.PhaseStep;
import mage.constants.SubLayer;
import mage.constants.Zone;
import mage.game.Game;
import mage.game.permanent.Permanent;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * WS85 future-state hardening: purity + failure-semantics coverage for the CR 614.12
 * entry-applicability probe in ContinuousEffects.
 *
 * <p>Hard gates under test:
 * - FUTURE_STATE_QUERY_LIVE_MUTATION = 0: applicability analysis must not mutate live state.
 * - SILENT_EVALUATION_FALLBACK = 0: evaluation failure must surface explicitly, never
 *   silently fall back to the old forbidden Clone prompt.
 *
 * <p>Method: a test-only sentinel layer-6 LoseAbility effect (never strips anything, never
 * decides anything) observes, from inside the engine's own layer-dispatch path, whether an
 * entering object is ever simultaneously visible as a live battlefield member while still
 * tracked as entering. That dual presence can only be produced by inserting the entering
 * object into the live battlefield for hypothetical evaluation.
 *
 * <p>Actual-card H01 credit still comes only from real cards (Clone/Humility/Runeclaw Bear);
 * the sentinel is a low-level mutation detector, never a behavior substitute.
 */
public class WS85FutureStateHardeningTest extends CardTestPlayerBase {

    /**
     * Test-only sentinel: an active layer-6 Outcome.LoseAbility remover that removes nothing.
     * Observational only. Its apply() records whether any entering-tracked object is
     * simultaneously a live battlefield member at dispatch time.
     */
    public static class ProbeSentinelEffect extends ContinuousEffectImpl {

        static volatile boolean dualPresenceObserved = false;
        static volatile String dualPresenceDetail = "";
        static volatile int layerApplyCalls = 0;
        static volatile int pureProbeCalls = 0;
        static volatile boolean failPureProbe = false;
        static volatile String observerError = "";
        static final String INJECTED_FAILURE_MARKER = "WS85-INJECTED-61412-PROBE-FAILURE";

        public ProbeSentinelEffect() {
            // Duration.Custom: test-only lifetime (never ends during the test). A battlefield
            // duration would subject the sentinel to source-existence pruning; Custom keeps
            // the sentinel under the test's own control while remaining visible to the layer
            // pipeline (durations other than While* are included unconditionally).
            super(Duration.Custom, Layer.AbilityAddingRemovingEffects_6, SubLayer.NA, Outcome.LoseAbility);
            staticText = "Sentinel: observe only, remove nothing";
        }

        protected ProbeSentinelEffect(final ProbeSentinelEffect effect) {
            super(effect);
        }

        @Override
        public ProbeSentinelEffect copy() {
            return new ProbeSentinelEffect(this);
        }

        @Override
        public boolean apply(Layer layer, SubLayer sublayer, Ability source, Game game) {
            layerApplyCalls++;
            try {
                List<UUID> entering = new ArrayList<>(game.getBattlefield().getPermanentsEntering().keySet());
                for (UUID id : entering) {
                    if (game.getBattlefield().getPermanent(id) != null) {
                        dualPresenceObserved = true;
                        dualPresenceDetail = "entering-tracked object simultaneously a live member: " + id;
                    }
                }
            } catch (RuntimeException e) {
                observerError = e.toString();
            }
            return false;
        }

        @Override
        public boolean apply(Game game, Ability source) {
            return false;
        }

        /**
         * Pure-probe seam: records invocation (proves the probe ran instead of being
         * skipped) and, when armed, fails explicitly with the injected marker instead of
         * fabricating an answer. Never mutates anything.
         */
        @Override
        public boolean wouldRemoveEnteringAbility(mage.game.permanent.Permanent entering,
                                                  Ability enteringAbility, Ability source, Game game) {
            pureProbeCalls++;
            if (failPureProbe) {
                throw new AssertionError(INJECTED_FAILURE_MARKER);
            }
            return false;
        }

        static void reset() {
            dualPresenceObserved = false;
            dualPresenceDetail = "";
            layerApplyCalls = 0;
            pureProbeCalls = 0;
            failPureProbe = false;
            observerError = "";
        }
    }

    /**
     * Test-only wiring: registers the sentinel as a sourceless Zone.ALL static effect
     * directly in game state (non-temporary). Sourceless + ALL means its usability never
     * depends on any permanent's ability list, so observation cannot be hidden by the very
     * ability-stripping under test. No production code is involved.
     */
    private void installSentinel(Game game, UUID controllerId) {
        ProbeSentinelEffect effect = new ProbeSentinelEffect();
        SimpleStaticAbility ability = new SimpleStaticAbility(Zone.ALL, effect);
        ability.setControllerId(controllerId);
        game.getState().addEffect(effect, ability);
    }

    private Permanent findPermanent(Game game, UUID controllerId, String name) {
        for (Permanent perm : game.getBattlefield().getAllActivePermanents(controllerId)) {
            if (perm.getName().equals(name)) {
                return perm;
            }
        }
        return null;
    }

    private static boolean chainContains(Throwable t, String marker) {
        while (t != null) {
            String message = t.getMessage();
            if (message != null && message.contains(marker)) {
                return true;
            }
            t = t.getCause();
        }
        return false;
    }

    /**
     * P0 control: sentinel installed, no Humility. Normal Clone copy must work and the
     * sentinel must observe no dual presence. Proves the sentinel itself is behavior-neutral
     * (no false positives) and was actually active (non-vacuous: normal layers dispatch it).
     */
    @Test
    public void testP0_SentinelControl_NormalCopyUnaffected() {
        ProbeSentinelEffect.reset();

        addCard(Zone.BATTLEFIELD, playerB, "Runeclaw Bear", 1);

        addCard(Zone.BATTLEFIELD, playerA, "Island", 4);
        addCard(Zone.HAND, playerA, "Clone", 1);

        runCode("install sentinel", 1, PhaseStep.UPKEEP, playerB,
                (info, p, g) -> installSentinel(g, p.getId()));

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Clone");
        setChoice(playerA, true);
        setChoice(playerA, "Runeclaw Bear");

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertPermanentCount(playerA, "Runeclaw Bear", 1);
        assertPowerToughness(playerA, "Runeclaw Bear", 2, 2);
        Assert.assertEquals("sentinel observer must stay silent: " + ProbeSentinelEffect.observerError,
                "", ProbeSentinelEffect.observerError);
        Assert.assertFalse("control: no live-membership leak expected: " + ProbeSentinelEffect.dualPresenceDetail,
                ProbeSentinelEffect.dualPresenceObserved);
        Assert.assertTrue("sentinel must have been dispatched by normal layers (non-vacuous control)",
                ProbeSentinelEffect.layerApplyCalls > 0);
    }

    /**
     * P1 purity: Humility pre-exists, Clone enters. H01-A outcome must hold (zero copy
     * decisions, Clone as itself 1/1) AND the sentinel must never observe the entering Clone
     * as a live battlefield member. Fails on implementations that temporarily insert the
     * real entering object into the live battlefield for hypothetical evaluation.
     */
    @Test
    public void testP1_HumilityFirst_ProbeMustNotExposeEnteringOrMutateLive() {
        ProbeSentinelEffect.reset();

        addCard(Zone.BATTLEFIELD, playerB, "Runeclaw Bear", 1);
        addCard(Zone.BATTLEFIELD, playerB, "Humility", 1);

        addCard(Zone.BATTLEFIELD, playerA, "Island", 4);
        addCard(Zone.HAND, playerA, "Clone", 1);

        runCode("install sentinel", 1, PhaseStep.UPKEEP, playerB,
                (info, p, g) -> installSentinel(g, p.getId()));

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Clone");
        // No setChoice: correct H01-A offers zero copy decisions (strict mode enforces).

        checkPT("P1: Clone is 1/1 under Humility", 1, PhaseStep.POSTCOMBAT_MAIN, playerA, "Clone", 1, 1);

        runCode("P1 under-Humility probe", 1, PhaseStep.POSTCOMBAT_MAIN, playerA,
                (info, p, g) -> {
                    Permanent clone = findPermanent(g, p.getId(), "Clone");
                    Assert.assertNotNull("P1: Clone must be on the battlefield as itself", clone);
                    Assert.assertFalse("P1: Clone must NOT be a copy", clone.isCopy());
                });

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertPermanentCount(playerA, "Clone", 1);
        assertPermanentCount(playerB, "Humility", 1);
        Assert.assertEquals("sentinel observer must stay silent: " + ProbeSentinelEffect.observerError,
                "", ProbeSentinelEffect.observerError);
        Assert.assertTrue("sentinel must have been dispatched (non-vacuous purity probe)",
                ProbeSentinelEffect.layerApplyCalls > 0);
        Assert.assertFalse("FUTURE_STATE_QUERY_LIVE_MUTATION must be 0: " + ProbeSentinelEffect.dualPresenceDetail,
                ProbeSentinelEffect.dualPresenceObserved);
    }

    // Pre-probe live-state snapshot (actual cards only, no sentinel).
    private final Map<String, String> preAbilities = new LinkedHashMap<>();
    private final Map<String, String> preController = new LinkedHashMap<>();
    private final List<String> preOrder = new ArrayList<>();
    private int preBattlefieldSize = 0;

    private static String abilityFingerprint(Permanent perm) {
        List<String> rules = new ArrayList<>();
        for (Ability ability : perm.getAbilities()) {
            rules.add(ability.getRule());
        }
        rules.sort(String::compareTo);
        return String.join(" || ", rules);
    }

    /**
     * P2 live-state snapshot (actual cards): unrelated battlefield objects, battlefield
     * membership, controller/zone identity, stack quiescence, and entering-map hygiene must
     * be unchanged by Clone's entry under Humility apart from the legitimate addition of
     * Clone itself. Documents semantic non-interference of the applicability probe.
     */
    @Test
    public void testP2_HumilityFirst_UnrelatedLiveStateUnchanged() {
        preAbilities.clear();
        preController.clear();
        preOrder.clear();

        addCard(Zone.BATTLEFIELD, playerB, "Runeclaw Bear", 1);
        addCard(Zone.BATTLEFIELD, playerB, "Humility", 1);

        addCard(Zone.BATTLEFIELD, playerA, "Island", 4);
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 3);
        addCard(Zone.HAND, playerA, "Clone", 1);

        runCode("P2 pre-entry snapshot", 1, PhaseStep.PRECOMBAT_MAIN, playerA,
                (info, p, g) -> {
                    preBattlefieldSize = g.getBattlefield().getAllPermanents().size();
                    for (Permanent perm : g.getBattlefield().getAllPermanents()) {
                        String id = perm.getId().toString();
                        preOrder.add(id);
                        preAbilities.put(id, abilityFingerprint(perm));
                        preController.put(id, perm.getControllerId().toString());
                        Assert.assertFalse("pre: Clone must not be on the battlefield yet",
                                perm.getName().equals("Clone"));
                    }
                    Assert.assertEquals("pre: stack must be empty before Clone resolves",
                            0, g.getStack().size());
                });

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Clone");
        // No setChoice: H01-A offers zero copy decisions.

        runCode("P2 post-entry comparison", 1, PhaseStep.POSTCOMBAT_MAIN, playerA,
                (info, p, g) -> {
                    // Every pre-existing permanent keeps identity, controller, zone, abilities.
                    for (String id : preOrder) {
                        Permanent perm = g.getBattlefield().getPermanent(UUID.fromString(id));
                        Assert.assertNotNull("P2: pre-existing permanent must remain: " + id, perm);
                        Assert.assertEquals("P2: controller identity must be unchanged: " + perm.getName(),
                                preController.get(id), perm.getControllerId().toString());
                        Assert.assertEquals("P2: abilities of unrelated permanent must be unchanged: " + perm.getName(),
                                preAbilities.get(id), abilityFingerprint(perm));
                    }
                    // Membership: exactly the pre-existing set plus the entering Clone itself.
                    Assert.assertEquals("P2: battlefield grows by exactly the entering Clone",
                            preBattlefieldSize + 1, g.getBattlefield().getAllPermanents().size());
                    // Entering-map hygiene: no entering-tracked object is also a live member.
                    for (UUID enteringId : new ArrayList<>(g.getBattlefield().getPermanentsEntering().keySet())) {
                        Assert.assertNull("P2: BATTLEFIELD_MEMBERSHIP_LEAK=0, dual presence for " + enteringId,
                                g.getBattlefield().getPermanent(enteringId));
                    }
                    // Stack quiescence after resolution.
                    Assert.assertEquals("P2: STACK_EVENT_RNG_LEAK=0, stack must be empty after entry",
                            0, g.getStack().size());
                });

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertPermanentCount(playerA, "Clone", 1);
        assertPermanentCount(playerB, "Humility", 1);
    }

    /**
     * F1 failure semantics: when future-state applicability evaluation cannot complete, the
     * engine must fail explicitly. It must not fabricate a copy choice, must not fall back
     * to the old forbidden Clone prompt, and must leave no partially mutated live state.
     *
     * <p>Seam: narrow test-only injected failure at the authoritative probe boundary
     * (ProbeSentinelEffect.failPureProbe). No other remover is present, so the probe must
     * reach the failing boundary. The injected marker must propagate to the test; any
     * silent catch-and-allow instead reaches the strict-mode forbidden prompt and
     * therefore carries no marker.
     */
    @Test
    public void testF1_ProbeFailureMustSurfaceExplicitly_NoSilentAllow() {
        ProbeSentinelEffect.reset();
        ProbeSentinelEffect.failPureProbe = true;

        addCard(Zone.BATTLEFIELD, playerB, "Runeclaw Bear", 1);

        addCard(Zone.BATTLEFIELD, playerA, "Island", 4);
        addCard(Zone.HAND, playerA, "Clone", 1);

        runCode("install failing sentinel", 1, PhaseStep.UPKEEP, playerB,
                (info, p, g) -> installSentinel(g, p.getId()));

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Clone");
        // No setChoice on purpose: a silent allow would hit the forbidden prompt.

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);

        Throwable thrown = null;
        try {
            execute();
        } catch (Throwable t) {
            thrown = t;
        }

        Assert.assertNotNull("FAILURE_SEMANTICS: evaluation failure must surface explicitly, not silently allow",
                thrown);
        Assert.assertTrue("SILENT_EVALUATION_FALLBACK=0: injected marker must propagate, got: " + thrown,
                chainContains(thrown, ProbeSentinelEffect.INJECTED_FAILURE_MARKER));
        Assert.assertTrue("probe must have reached the failing boundary (non-vacuous)",
                ProbeSentinelEffect.pureProbeCalls > 0);
        // No fabricated copy decision may have been established from an uncompleted evaluation.
        assertPermanentCount(playerA, "Runeclaw Bear", 0);
        // No partially mutated live state: no entering-tracked object left as a live member.
        for (UUID enteringId : currentGame.getBattlefield().getPermanentsEntering().keySet()) {
            Assert.assertNull("no partially mutated live state: " + enteringId,
                    currentGame.getBattlefield().getPermanent(enteringId));
        }
    }
}
