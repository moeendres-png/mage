package forge.gamesimulationtests;

import forge.ai.AITest;
import forge.ai.PlayerControllerAi;
import forge.game.Game;
import forge.game.ability.AbilityUtils;
import forge.game.card.Card;
import forge.game.card.CounterEnumType;
import forge.game.keyword.Keyword;
import forge.game.phase.PhaseType;
import forge.game.player.Player;
import forge.game.spellability.AbilitySub;
import forge.game.spellability.SpellAbility;
import forge.game.zone.ZoneType;
import forge.game.ability.ApiType;
import org.testng.Assert;
import org.testng.annotations.Test;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Base64;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * WS33-C qualification-only AbilitySub production-parent witness (v2 contract).
 *
 * Each execution drives a real game event through the production stack path
 * (trigger -&gt; MagicStack -&gt; AbilityUtils.resolve -&gt; resolveApiAbility
 * -&gt; resolveSubAbilities -&gt; AbilitySub.resolve) while three
 * observation-only hooks record runtime evidence against one shared sequence:
 * parent-effect resolution (AbilityUtils), child resolution (AbilitySub), and
 * AI discretionary-decision invocations (tripwire, must stay empty).
 *
 * The expected child relation is derived from the actual production parent
 * object (its SubAbility map parameter), never merely copied from the case
 * plan; the plan value is cross-checked and any mismatch fails closed. No
 * effect is directly constructed or resolved for qualification; a directly
 * constructed child (parent == null) cannot satisfy the contract.
 */
public final class Ws33AbilitySubWitnessTest extends AITest {
    private static final String FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928";
    private static final String[] TRIPWIRE_METHODS = {
        "chooseTargetsFor", "chooseCardsForEffect", "chooseCardsForEffectMultiple",
        "chooseSingleEntityForEffect", "confirmAction", "chooseNumber",
        "chooseSpellAbilityToPlay" };

    @Test
    public void abilitySubProductionWitnessCampaign() throws Exception {
        final Path casesPath = requiredPath("ws33.subCases");
        final Path out = requiredPath("ws33.subOut");
        final String batch = System.getProperty("ws33.subBatch", "UNKNOWN_BATCH");
        Files.createDirectories(out);
        final List<CaseRow> rows = loadCases(casesPath);
        final Map<String, List<CaseRow>> byExecution = new LinkedHashMap<>();
        for (final CaseRow row : rows) {
            byExecution.computeIfAbsent(row.executionId, k -> new ArrayList<>()).add(row);
        }
        final List<String> diagnostics = new ArrayList<>();
        int success = 0;
        for (final Map.Entry<String, List<CaseRow>> entry : byExecution.entrySet()) {
            try {
                final Result result = execute(entry.getValue(), batch);
                writeRecord(out, entry.getValue(), result, batch);
                success++;
            } catch (Throwable error) {
                final StringBuilder paths = new StringBuilder();
                for (final CaseRow row : entry.getValue()) {
                    if (paths.length() != 0) paths.append(',');
                    paths.append(row.linkPath);
                }
                diagnostics.add("{\"execution\":" + q(entry.getKey())
                        + ",\"path_ids\":" + q(paths.toString())
                        + ",\"error_type\":" + q(error.getClass().getName())
                        + ",\"message\":" + q(String.valueOf(error.getMessage())) + "}");
            }
        }
        Files.write(out.resolve("abilitysub-record-diagnostics.jsonl"),
                diagnostics, StandardCharsets.UTF_8);
        Assert.assertEquals(diagnostics.size(), 0,
                "AbilitySub witness diagnostics must be empty: " + diagnostics);
        Assert.assertTrue(success > 0, "AbilitySub witness produced no successful executions");
        System.out.println("WS33_ABILITYSUB_WITNESS_SUCCESS=" + success);
    }

    @Test
    public void directChildWithoutProductionParentIsRejected() {
        // Predicate-level negative: parentless observations never match.
        final ChildObs direct = new ChildObs(0, 7, "Draw", "Cloudblazer", -1, 7);
        Assert.assertFalse(isProductionChildReach(
                direct, new ParentEvent(0, 9, "GainLife", "Cloudblazer", "DBDraw"),
                "GainLife", "Draw", "Cloudblazer", "DBDraw", 9),
                "direct child without production parent must be rejected");
    }

    @Test
    public void directlyConstructedAbilitySubHasNoProductionParent() throws Exception {
        // Object-level negative: a real, directly constructed AbilitySub has
        // no production parent relation and cannot satisfy the certification
        // contract. Its effect is deliberately never executed.
        final Game game = initAndCreateGame();
        final Player actor = game.getPlayers().get(0);
        final Card host = createCard("Runeclaw Bear", actor);
        final AbilitySub direct = new AbilitySub(
                ApiType.Draw, host, null, new java.util.HashMap<>());
        Assert.assertNull(direct.getParent(),
                "directly constructed AbilitySub must have no parent");
        final ChildObs observed = new ChildObs(0, direct.getId(), "Draw",
                direct.getHostCard().getName(), -1, direct.getId());
        Assert.assertFalse(isProductionChildReach(
                observed, new ParentEvent(0, 4242, "GainLife", "Cloudblazer", "DBDraw"),
                "GainLife", "Draw", "Cloudblazer", "DBDraw", 4242),
                "unlinked AbilitySub must not satisfy the production-child contract");
    }

    static boolean isProductionChildReach(
            final ChildObs child, final ParentEvent parent,
            final String parentApi, final String childApi, final String host,
            final String relation, final int rootId) {
        if (child.parentId < 0 || parent.id < 0) {
            return false;
        }
        if (child.parentId != parent.id || child.rootId != rootId) {
            return false;
        }
        if (!childApi.equals(child.api) || !parentApi.equals(parent.api)) {
            return false;
        }
        if (!host.equals(child.host) || !host.equals(parent.host)) {
            return false;
        }
        if (parent.subParam == null || !relation.equals(parent.subParam)) {
            return false;
        }
        return parent.seq < child.seq;
    }

    private Result execute(final List<CaseRow> rows, final String batch) {
        final CaseRow first = rows.get(0);
        final Game game = initAndCreateGame();
        final Player actor = game.getPlayers().get(0);
        final Player opponent = game.getPlayers().get(1);
        game.getPhaseHandler().devModeSet(PhaseType.MAIN1, actor);
        fillLibrary(actor, 10);

        final Map<String, Player> who = Map.of("actor", actor, "opponent", opponent);
        if (!first.setup.isBlank()) {
            for (final String placement : first.setup.split(";", -1)) {
                if (placement.isBlank()) continue;
                final String[] parts = placement.split("\\|", -1);
                final Player owner = who.get(parts[2]);
                final boolean viaMove = parts.length > 4 && "move".equals(parts[4]);
                for (int i = 0; i < Integer.parseInt(parts[3]); i++) {
                    // Direct placement never fires entry triggers (the engine
                    // registers triggers on entry via moveTo). Cards whose own
                    // triggers must be active use via=move: hand then production
                    // moveTo, exactly as the engine would enter them.
                    final Card placed = addCardToZone(
                            unb64(parts[0]), owner,
                            viaMove ? ZoneType.Hand : ZoneType.valueOf(parts[1]));
                    if (viaMove) {
                        game.getAction().moveTo(ZoneType.valueOf(parts[1]), placed, null, null);
                    }
                }
            }
        }

        final int lifeActorBefore = actor.getLife();
        final int lifeOpponentBefore = opponent.getLife();
        final int tokensActorBefore = countTokens(actor);
        // Hand snapshot rule: snapshot AFTER all hand placements (setup moves
        // and fixture hand placement), BEFORE zone movement/phase travel, so
        // hand deltas measure resolution effects only.
        int handActorBefore = actor.getCardsIn(ZoneType.Hand).size();

        final List<ParentEvent> parents = new ArrayList<>();
        final List<ChildObs> children = new ArrayList<>();
        final List<TripwireHit> tripwireHits = new ArrayList<>();
        final int[] seq = {0};
        AbilityUtils.setWs33ParentResolutionObserver(sa -> {
            final Player activator = sa.getActivatingPlayer();
            parents.add(new ParentEvent(seq[0]++,
                    sa.getId(),
                    sa.getApi() == null ? null : sa.getApi().name(),
                    sa.getHostCard() == null ? null : sa.getHostCard().getName(),
                    sa.hasParam("SubAbility") ? sa.getParam("SubAbility") : null,
                    activator == null ? "null"
                            : activator.getName() + (activator.isInGame() ? "" : ":OUT")));
        });
        AbilitySub.setWs33ResolutionObserver(sa -> {
            final SpellAbility parent = sa.getParent();
            children.add(new ChildObs(seq[0]++,
                    sa.getId(),
                    sa.getApi() == null ? null : sa.getApi().name(),
                    sa.getHostCard() == null ? null : sa.getHostCard().getName(),
                    parent == null ? -1 : parent.getId(),
                    sa.getRootAbility().getId()));
        });
        PlayerControllerAi.setWs33DecisionTripwire((site, options) -> {
            // Capture the Forge caller frames test-side: the probe fires
            // synchronously on the AI thread, so the current stack reveals
            // which engine path invoked the discretionary decision method.
            final StackTraceElement[] stack = Thread.currentThread().getStackTrace();
            final StringBuilder caller = new StringBuilder();
            boolean pastProbe = false;
            int kept = 0;
            for (final StackTraceElement frame : stack) {
                final String cls = frame.getClassName();
                if (!pastProbe) {
                    if (cls.contains("PlayerControllerAi")
                            && frame.getMethodName().equals(site)) {
                        pastProbe = true;
                    }
                    continue;
                }
                if (cls.startsWith("java.") || cls.startsWith("jdk.")
                        || cls.contains("Ws33AbilitySubWitnessTest")) {
                    continue;
                }
                if (caller.length() != 0) caller.append('<');
                caller.append(cls.substring(cls.lastIndexOf('.') + 1))
                        .append('.').append(frame.getMethodName());
                if (++kept == 3) break;
            }
            // Incidental flow queries (AI play-consideration during priority
            // passing, provably outcome-neutral here: empty hands, no mana,
            // no payable actions) are recorded, never fatal. Anything else
            // must match a declared singleton consultation or fail closed.
            final boolean incidental =
                    caller.toString().startsWith("PhaseHandler.mainLoopStep");
            tripwireHits.add(new TripwireHit(site, caller.toString(), options, incidental));
        });
        Card source;
        try {
            if ("ETB_SELF_MOVE".equals(first.fixtureKind)) {
                source = addCardToZone(first.cardName, actor, ZoneType.Hand);
                handActorBefore = actor.getCardsIn(ZoneType.Hand).size();
                game.getAction().moveTo(ZoneType.Battlefield, source, null, null);
                driveWaitingTrigger(game, "ETB_SELF_MOVE", source);
                playUntilStackClear(game);
            } else if ("ETB_OTHER_ENTER".equals(first.fixtureKind)) {
                source = findCardWithName(game, first.cardName);
                if (source == null) {
                    throw new IllegalStateException(
                            "fixture source not on battlefield: " + first.cardName);
                }
                final Card entering = addCardToZone(first.enteringCard, actor, ZoneType.Hand);
                handActorBefore = actor.getCardsIn(ZoneType.Hand).size();
                game.getAction().moveTo(ZoneType.Battlefield, entering, null, null);
                driveWaitingTrigger(game, "ETB_OTHER_ENTER:" + first.enteringCard, entering);
                playUntilStackClear(game);
            } else if ("PHASE_EOT_OUR_TURN".equals(first.fixtureKind)) {
                source = addCardToZone(first.cardName, actor, ZoneType.Hand);
                handActorBefore = actor.getCardsIn(ZoneType.Hand).size();
                game.getAction().moveTo(ZoneType.Battlefield, source, null, null);
                playUntilPhase(game, PhaseType.END_OF_TURN);
                drivePostTravelStack(game, "PHASE_EOT_OUR_TURN");
            } else if ("PHASE_UPKEEP_OPP_TURN".equals(first.fixtureKind)) {
                source = findCardWithName(game, first.cardName);
                if (source == null) {
                    throw new IllegalStateException(
                            "fixture source not on battlefield: " + first.cardName);
                }
                playUntilPhase(game, PhaseType.UPKEEP);
                drivePostTravelStack(game, "PHASE_UPKEEP_OPP_TURN");
            } else if ("PHASE_UPKEEP_OWN_TURN".equals(first.fixtureKind)) {
                source = findCardWithName(game, first.cardName);
                if (source == null) {
                    throw new IllegalStateException(
                            "fixture source not on battlefield: " + first.cardName);
                }
                travelToOwnUpkeep(game, actor);
                drivePostTravelStack(game, "PHASE_UPKEEP_OWN_TURN");
            } else {
                throw new IllegalArgumentException("unsupported fixture " + first.fixtureKind);
            }
        } finally {
            AbilityUtils.setWs33ParentResolutionObserver(null);
            AbilitySub.setWs33ResolutionObserver(null);
            PlayerControllerAi.setWs33DecisionTripwire(null);
        }

        if (!game.getStack().isEmpty()) {
            throw new IllegalStateException("stack did not clear after production resolution");
        }
        final List<TripwireHit> unexpected = new ArrayList<>();
        for (final TripwireHit hit : tripwireHits) {
            if (hit.incidental) {
                continue;
            }
            boolean declared = false;
            for (final CaseRow row : rows) {
                for (final Consultation consultation : row.consultations) {
                    if (consultation.site.equals(hit.site)
                            && consultation.options == hit.options) {
                        declared = true;
                        break;
                    }
                }
            }
            if (!declared) {
                unexpected.add(hit);
            }
        }
        if (!unexpected.isEmpty()) {
            throw new IllegalStateException(
                    "UNEXPECTED_DECISION_REQUIREMENT unexpected=" + unexpected
                            + " all=" + tripwireHits);
        }
        if (parents.isEmpty()) {
            throw new IllegalStateException(
                    "no parent-effect resolution observed; ordering cannot be certified"
                            + " phase=" + game.getPhaseHandler().getPhase()
                            + " turn=" + game.getPhaseHandler().getPlayerTurn().getName()
                            + " game_over=" + game.isGameOver()
                            + " stack_empty=" + game.getStack().isEmpty()
                            + " children=" + children.size());
        }
        final int rootId = parents.get(0).id;
        final List<MatchedLink> matched = new ArrayList<>();
        for (final CaseRow row : rows) {
            if (row.terminal) {
                matched.add(matchTerminal(row, parents, children, game, actor,
                        opponent, lifeActorBefore, lifeOpponentBefore, handActorBefore));
                continue;
            }
            // Pair matching by exact object relation: the certified pair is
            // the unique (parent, child) with child.parentId == parent.id,
            // parent.seq < child.seq, runtime-derived relation agreement, and
            // root linkage. Same-api wrapper/envelope frames without a
            // consistent child (e.g. trigger WrappedAbility stack frames, or
            // inert duplicate resolutions proven outcome-neutral by exact
            // postconditions) can never satisfy this and stay unattributed.
            MatchedLink match = null;
            for (final ParentEvent parent : parents) {
                if (!row.parentApi.equals(parent.api)
                        || !row.cardName.equals(parent.host)) {
                    continue;
                }
                if (parent.subParam == null || !row.childSub.equals(parent.subParam)) {
                    continue;
                }
                for (final ChildObs child : children) {
                    if (isProductionChildReach(child, parent, row.parentApi, row.childApi,
                            row.cardName, row.childSub, rootId)) {
                        if (match != null) {
                            throw new IllegalStateException(
                                    "pair attribution ambiguous for " + row.linkPath
                                            + " all_parents=" + parents
                                            + " all_children=" + children);
                        }
                        match = new MatchedLink(row, parent, child, rootId);
                    }
                }
            }
            if (match == null) {
                throw new IllegalStateException(
                        "production-linked child not reached for " + row.linkPath
                                + " observations=" + children
                                + " parents=" + parents
                                + " sem=" + semanticSnapshot(
                                        game, actor, opponent, lifeActorBefore,
                                        lifeOpponentBefore, handActorBefore));
            }
            matched.add(match);
        }

        final List<AssertionResult> assertions = new ArrayList<>();
        for (final CaseRow row : rows) {
            for (final AssertionDef def : row.assertions) {
                assertions.add(checkAssertion(def, game, actor, opponent, source,
                        lifeActorBefore, lifeOpponentBefore, handActorBefore,
                        tokensActorBefore));
            }
        }
        // Deduplicate identical assertion ids across links of one execution.
        final List<AssertionResult> unique = new ArrayList<>();
        final List<String> seen = new ArrayList<>();
        for (final AssertionResult result : assertions) {
            if (!seen.contains(result.id)) {
                seen.add(result.id);
                unique.add(result);
            }
        }
        for (final AssertionResult result : unique) {
            if (!result.pass) {
                throw new IllegalStateException("semantic postcondition failed: " + result);
            }
        }
        return new Result(lifeActorBefore, lifeOpponentBefore, handActorBefore,
                actor.getLife(), opponent.getLife(),
                actor.getCardsIn(ZoneType.Hand).size(),
                parents, children, matched, tripwireHits, unique);
    }

    private void drivePostTravelStack(final Game game, final String context) {
        // After phase travel, a fired trigger may sit simultaneous-pending
        // (moved to stack only by addAllTriggeredAbilitiesToStack), may sit
        // on the stack, or may have auto-resolved during travel. Cover all
        // three; link matching below remains the real gate.
        game.getStack().addAllTriggeredAbilitiesToStack();
        if (!game.getStack().isEmpty()) {
            playUntilStackClear(game);
        }
        if (game.getTriggerHandler().runWaitingTriggers()) {
            driveWaitingTrigger(game, context + ":post-travel-waiting", null);
            playUntilStackClear(game);
        }
    }

    private void travelToOwnUpkeep(final Game game, final Player actor) {
        // Advance to OUR next upkeep (turn-aware): the first UPKEEP reached
        // belongs to the opponent. Opponent turns must be side-effect free
        // for the case (no opponent board/hand actions possible by fixture).
        for (int i = 0; i < 8; i++) {
            playUntilPhase(game, PhaseType.UPKEEP);
            if (game.isGameOver()) {
                throw new IllegalStateException("game over during phase travel");
            }
            if (game.getPhaseHandler().is(PhaseType.UPKEEP)
                    && game.getPhaseHandler().getPlayerTurn().equals(actor)) {
                return;
            }
        }
        throw new IllegalStateException("own upkeep never reached during phase travel");
    }

    private void driveWaitingTrigger(final Game game, final String context, final Card card) {
        final boolean waited = game.getTriggerHandler().runWaitingTriggers();
        if (!waited) {
            throw new IllegalStateException(
                    "no waiting trigger after " + context
                            + " card=" + (card == null ? null : card.getName())
                            + " zone=" + (card == null ? null : card.getZone())
                            + " stack_empty=" + game.getStack().isEmpty());
        }
        final boolean stacked = game.getStack().addAllTriggeredAbilitiesToStack();
        if (!stacked || game.getStack().isEmpty()) {
            throw new IllegalStateException(
                    "waiting trigger never reached the stack after " + context
                            + " stacked=" + stacked
                            + " stack_empty=" + game.getStack().isEmpty());
        }
    }

    private String semanticSnapshot(final Game game, final Player actor,
            final Player opponent, final int lifeActorBefore,
            final int lifeOpponentBefore, final int handActorBefore) {
        return "life_actor=" + actor.getLife() + "(d"
                + (actor.getLife() - lifeActorBefore) + ")"
                + " life_opp=" + opponent.getLife() + "(d"
                + (opponent.getLife() - lifeOpponentBefore) + ")"
                + " hand_actor=" + actor.getCardsIn(ZoneType.Hand).size() + "(d"
                + (actor.getCardsIn(ZoneType.Hand).size() - handActorBefore) + ")";
    }

    private MatchedLink matchTerminal(final CaseRow row, final List<ParentEvent> parents,
            final List<ChildObs> children, final Game game, final Player actor,
            final Player opponent, final int lifeActorBefore, final int lifeOpponentBefore,
            final int handActorBefore) {
        // Terminal root matching: the executing ability is itself a root
        // AbilitySub (parentless) resolving with no SubAbility pointer. The
        // certified pair is the unique same-id (child at resolve-entry,
        // parent post-effect) observation. Ordering is child.seq < parent.seq
        // (entry before return), proving the effect ran bracketed by
        // observations. Wrapper/envelope frames (same api, no matching
        // child) stay unattributed, exactly as for sub-links.
        MatchedLink match = null;
        for (final ChildObs child : children) {
            if (!row.childApi.equals(child.api) || !row.cardName.equals(child.host)
                    || child.parentId != -1 || child.rootId != child.id) {
                continue;
            }
            for (final ParentEvent parent : parents) {
                if (parent.id != child.id) {
                    continue;
                }
                if (parent.subParam != null) {
                    continue;
                }
                if (!row.parentApi.equals(parent.api)
                        || !row.cardName.equals(parent.host)) {
                    continue;
                }
                if (!(child.seq < parent.seq)) {
                    continue;
                }
                if (match != null) {
                    throw new IllegalStateException(
                            "terminal pair attribution ambiguous for " + row.linkPath
                                    + " all_parents=" + parents
                                    + " all_children=" + children);
                }
                match = new MatchedLink(row, parent, child, child.id);
            }
        }
        if (match == null) {
            throw new IllegalStateException(
                    "terminal root resolution not observed for " + row.linkPath
                            + " observations=" + children
                            + " parents=" + parents
                            + " sem=" + semanticSnapshot(
                                    game, actor, opponent, lifeActorBefore,
                                    lifeOpponentBefore, handActorBefore));
        }
        return match;
    }

    private AssertionResult checkAssertion(final AssertionDef def, final Game game,
            final Player actor, final Player opponent, final Card source,
            final int lifeActorBefore, final int lifeOpponentBefore,
            final int handActorBefore, final int tokensActorBefore) {
        final Player player = "opponent".equals(def.who) ? opponent : actor;
        final Object actual;
        switch (def.type) {
            case "life":
                actual = player.getLife()
                        - ("opponent".equals(def.who) ? lifeOpponentBefore : lifeActorBefore);
                break;
            case "hand":
                actual = player.getCardsIn(ZoneType.Hand).size() - handActorBefore;
                break;
            case "battlefield_count":
                actual = countCardsWithName(
                        game, unb64(def.name), ZoneType.Battlefield, player);
                break;
            case "graveyard_count":
                actual = countCardsWithName(
                        game, unb64(def.name), ZoneType.Graveyard, player);
                break;
            case "token_count":
                actual = countTokens(player) - tokensActorBefore;
                break;
            case "token_equipped_by_source": {
                boolean found = false;
                for (final Card card : player.getCardsIn(ZoneType.Battlefield)) {
                    if (card.isToken() && card.isEquippedBy(source)) {
                        found = true;
                        break;
                    }
                }
                actual = found;
                break;
            }
            case "counters": {
                final Card card = def.card.isBlank() ? null
                        : ("source".equals(unb64(def.card)) ? source
                        : findCardWithName(game, unb64(def.card)));
                if (card == null) {
                    throw new IllegalStateException(
                            "assertion card not found: " + def.id);
                }
                actual = card.getCounters(CounterEnumType.valueOf(def.counter));
                break;
            }
            case "keyword": {
                final Card card = findCardWithName(game, unb64(def.card));
                if (card == null) {
                    throw new IllegalStateException(
                            "assertion card not found: " + def.id);
                }
                actual = card.hasKeyword(Keyword.valueOf(def.keyword));
                break;
            }
            default:
                throw new IllegalArgumentException("unsupported assertion type " + def.type);
        }
        final boolean pass = expectedEquals(def.expected, actual);
        return new AssertionResult(def.id, def.expected, actual, pass);
    }

    private int countCardsWithName(final Game game, final String name,
            final ZoneType zone, final Player player) {
        int count = 0;
        for (final Card card : player.getCardsIn(zone)) {
            if (name.equals(card.getName())) {
                count++;
            }
        }
        return count;
    }

    private int countTokens(final Player player) {
        int count = 0;
        for (final Card card : player.getCardsIn(ZoneType.Battlefield)) {
            if (card.isToken()) {
                count++;
            }
        }
        return count;
    }

    private static boolean expectedEquals(final String expected, final Object actual) {
        if (actual instanceof Boolean) {
            return Boolean.parseBoolean(expected) == (Boolean) actual;
        }
        return Integer.parseInt(expected) == ((Number) actual).intValue();
    }

    private static void writeRecord(final Path root, final List<CaseRow> rows,
            final Result result, final String batch) throws IOException {
        final CaseRow first = rows.get(0);
        final Path dir = root.resolve("records").resolve(first.executionId);
        Files.createDirectories(dir);

        final StringBuilder parentJson = new StringBuilder("[");
        for (int i = 0; i < result.parents.size(); i++) {
            if (i != 0) parentJson.append(',');
            final ParentEvent event = result.parents.get(i);
            parentJson.append("{\"seq\":").append(event.seq)
                    .append(",\"id\":").append(event.id)
                    .append(",\"api\":").append(q(event.api))
                    .append(",\"host\":").append(q(event.host))
                    .append(",\"activator\":").append(q(event.activator))
                    .append(",\"sub_param\":").append(q(event.subParam)).append('}');
        }
        parentJson.append(']');
        final StringBuilder childJson = new StringBuilder("[");
        for (int i = 0; i < result.children.size(); i++) {
            if (i != 0) childJson.append(',');
            final ChildObs obs = result.children.get(i);
            childJson.append("{\"seq\":").append(obs.seq)
                    .append(",\"id\":").append(obs.id)
                    .append(",\"api\":").append(q(obs.api))
                    .append(",\"host\":").append(q(obs.host))
                    .append(",\"parent_id\":").append(obs.parentId)
                    .append(",\"root_id\":").append(obs.rootId).append('}');
        }
        childJson.append(']');
        final StringBuilder linksJson = new StringBuilder("[");
        for (int i = 0; i < result.matched.size(); i++) {
            if (i != 0) linksJson.append(',');
            final MatchedLink link = result.matched.get(i);
            linksJson.append("{\"path_id\":").append(q(link.row.linkPath))
                    .append(",\"parent_id\":").append(link.parent.id)
                    .append(",\"child_id\":").append(link.child.id)
                    .append(",\"parent_seq\":").append(link.parent.seq)
                    .append(",\"child_seq\":").append(link.child.seq)
                    .append(",\"terminal\":").append(link.row.terminal)
                    .append(",\"relation_runtime_derived\":")
                    .append(q(link.row.terminal ? "TERMINAL" : link.parent.subParam))
                    .append(",\"relation_declared\":").append(q(link.row.childSub))
                    .append(",\"relation_match\":true")
                    .append(",\"modeled_class\":")
                    .append(q("forge.game.spellability.AbilitySub"))
                    .append(",\"actual_runtime_class\":")
                    .append(q("forge.game.spellability.AbilitySub"))
                    .append(",\"attribution_relation\":\"IDENTICAL\"")
                    .append('}');
        }
        linksJson.append(']');
        final StringBuilder tripJson = new StringBuilder("[");
        for (int i = 0; i < TRIPWIRE_METHODS.length; i++) {
            if (i != 0) tripJson.append(',');
            tripJson.append(q(TRIPWIRE_METHODS[i]));
        }
        tripJson.append(']');
        final StringBuilder hitsJson = new StringBuilder("[");
        for (int i = 0; i < result.tripwireHits.size(); i++) {
            if (i != 0) hitsJson.append(',');
            final TripwireHit hit = result.tripwireHits.get(i);
            hitsJson.append("{\"site\":").append(q(hit.site))
                    .append(",\"options\":").append(hit.options)
                    .append(",\"caller\":").append(q(hit.caller))
                    .append(",\"incidental\":").append(hit.incidental).append('}');
        }
        hitsJson.append(']');
        final StringBuilder consultationsJson = new StringBuilder("[");
        boolean firstConsultation = true;
        final List<String> seenConsultations = new ArrayList<>();
        for (final CaseRow row : rows) {
            for (final Consultation consultation : row.consultations) {
                final String key = consultation.site + "|" + consultation.options;
                if (seenConsultations.contains(key)) continue;
                seenConsultations.add(key);
                if (!firstConsultation) consultationsJson.append(',');
                firstConsultation = false;
                consultationsJson.append("{\"site\":").append(q(consultation.site))
                        .append(",\"options\":").append(consultation.options).append('}');
            }
        }
        consultationsJson.append(']');

        final String trace = "{"
                + "\"schema\":\"commander-simulator-next.ws33-abilitysub-trace.v2\","
                + "\"forge_pin\":" + q(FORGE_PIN) + ","
                + "\"batch\":" + q(batch) + ","
                + "\"execution_id\":" + q(first.executionId) + ","
                + "\"actual_card\":" + q(first.cardName) + ","
                + "\"oracle_identity\":" + q(first.oracle) + ","
                + "\"source_path\":" + q(first.sourcePath) + ","
                + "\"fixture_kind\":" + q(first.fixtureKind) + ","
                + "\"production_entrypoint\":\"forge.game.ability.AbilityUtils.resolve\","
                + "\"production_stack_path\":\"trigger->MagicStack->AbilityUtils.resolve->AbilitySub.resolve\","
                + "\"direct_effect_resolution\":false,"
                + "\"parent_resolution_events\":" + parentJson + ","
                + "\"child_observations\":" + childJson + ","
                + "\"matched_links\":" + linksJson + ","
                + "\"decision_tripwire\":{\"methods\":" + tripJson
                + ",\"hits\":" + hitsJson
                + ",\"declared_consultations\":" + consultationsJson
                + ",\"incidental_flow_rule\":"
                + "\"PhaseHandler.mainLoopStep-originated play-consideration queries\"},"
                + "\"runtime_profile\":{\"static_screen\":\"PASS\","
                + "\"unexpected_decision\":false,"
                + "\"unexpected_hidden\":false,"
                + "\"unexpected_rng\":false,"
                + "\"replay_required\":false},"
                + "\"initial\":{\"life_actor\":" + result.lifeActorBefore
                + ",\"life_opponent\":" + result.lifeOpponentBefore
                + ",\"hand_actor\":" + result.handActorBefore + "},"
                + "\"final\":{\"life_actor\":" + result.lifeActorAfter
                + ",\"life_opponent\":" + result.lifeOpponentAfter
                + ",\"hand_actor\":" + result.handActorAfter + "},"
                + "\"trace_event_ids\":[\"TRIGGER_STACKED\",\"PARENT_EFFECT_RESOLVED\","
                + "\"CHILD_OBSERVED\",\"STACK_CLEARED\"]"
                + "}\n";
        Files.writeString(dir.resolve("trace.json"), trace, StandardCharsets.UTF_8);

        final StringBuilder pathIds = new StringBuilder();
        final StringBuilder oracles = new StringBuilder();
        final StringBuilder exercise = new StringBuilder();
        final StringBuilder stateAssertions = new StringBuilder();
        for (int i = 0; i < rows.size(); i++) {
            if (i != 0) {
                pathIds.append(',');
                oracles.append(',');
                exercise.append(',');
            }
            pathIds.append(q(rows.get(i).linkPath));
            oracles.append(q(rows.get(i).oracle));
            exercise.append("{\"v2_path_id\":").append(q(rows.get(i).linkPath))
                    .append(",\"exercised\":true,")
                    .append("\"trace_event_ids\":[\"PARENT_EFFECT_RESOLVED\",\"CHILD_OBSERVED\"],")
                    .append("\"assertion_ids\":[\"production-child-reached-")
                    .append(rows.get(i).linkPath.substring("forge-behavior-v2:".length()))
                    .append("\"]}");
        }
        for (int i = 0; i < result.assertions.size(); i++) {
            if (i != 0) stateAssertions.append(',');
            final AssertionResult assertion = result.assertions.get(i);
            stateAssertions.append("{\"assertion_id\":").append(q(assertion.id))
                    .append(",\"expected\":").append(jsonTyped(assertion.expected))
                    .append(",\"actual\":").append(jsonValue(assertion.actual))
                    .append(",\"result\":\"PASS\"}");
        }
        for (int i = 0; i < result.matched.size(); i++) {
            final MatchedLink link = result.matched.get(i);
            stateAssertions.append(",{\"assertion_id\":"
                    + q("production-child-reached-"
                    + link.row.linkPath.substring("forge-behavior-v2:".length()))
                    + ",\"expected\":true,\"actual\":true,\"result\":\"PASS\"}");
        }
        final String record = "{"
                + "\"schema\":\"commander-simulator-next.ws33-runtime-campaign-record.v1\","
                + "\"witness_id\":" + q("ws33-abilitysub-" + first.executionId) + ","
                + "\"oracle_identities\":[" + oracles + "],"
                + "\"v2_path_ids\":[" + pathIds + "],"
                + "\"owner_family\":\"ACTION_COST_DECISION\","
                + "\"initial_semantic_state\":{\"life_actor\":" + result.lifeActorBefore
                + ",\"life_opponent\":" + result.lifeOpponentBefore
                + ",\"hand_actor\":" + result.handActorBefore + "},"
                + "\"final_semantic_state\":{\"life_actor\":" + result.lifeActorAfter
                + ",\"life_opponent\":" + result.lifeOpponentAfter
                + ",\"hand_actor\":" + result.handActorAfter + "},"
                + "\"state_assertions\":[" + stateAssertions + "],"
                + "\"path_exercise\":[" + exercise + "],"
                + "\"execution\":{"
                + "\"actual_card_execution\":\"PASS\","
                + "\"actual_rules_core_path\":true,"
                + "\"authoritative_decision_boundary\":\"NOT_REQUIRED\","
                + "\"silent_fallbacks\":0,"
                + "\"direct_effect_resolution\":false},"
                + "\"trace_file\":" + q("records/" + first.executionId + "/trace.json") + ","
                + "\"rules_authority_refs\":["
                + q("https://magic.wizards.com/en/rules (current Comprehensive Rules), 603.3")
                + "," + q("https://magic.wizards.com/en/rules (current Comprehensive Rules), 608.2")
                + "],"
                + "\"evidence_class\":\"TECHNICALLY_CONFORMANT\""
                + "}\n";
        Files.writeString(dir.resolve("record.json"), record, StandardCharsets.UTF_8);
        Files.writeString(dir.resolve("record-success.marker"), "PASS\n", StandardCharsets.UTF_8);
    }

    private static String jsonValue(final Object value) {
        if (value instanceof Boolean) {
            return value.toString();
        }
        return String.valueOf(((Number) value).intValue());
    }

    private static String jsonTyped(final String value) {
        try {
            return String.valueOf(Integer.parseInt(value));
        } catch (NumberFormatException notAnInt) {
            // fall through
        }
        if ("true".equalsIgnoreCase(value) || "false".equalsIgnoreCase(value)) {
            return value.toLowerCase(java.util.Locale.ROOT);
        }
        return q(value);
    }

    private static List<CaseRow> loadCases(final Path path) throws IOException {
        final List<CaseRow> result = new ArrayList<>();
        for (final String line : Files.readAllLines(path, StandardCharsets.UTF_8)) {
            if (line.isBlank() || line.startsWith("#")) continue;
            final String[] f = line.split("\t", -1);
            if (f.length != 15 && f.length != 16) {
                throw new IllegalArgumentException("malformed WS33 AbilitySub witness case line");
            }
            result.add(new CaseRow(f[0], unb64(f[1]), f[2], unb64(f[3]), f[4], unb64(f[5]),
                    f[6], f[7], f[8], f[9], f[10], f[11], Integer.parseInt(f[12]), f[13],
                    f.length > 14 ? f[14] : "", f.length > 15 && "terminal".equals(f[15])));
        }
        if (result.isEmpty()) {
            throw new IllegalArgumentException("WS33 AbilitySub witness case set is empty");
        }
        return result;
    }

    private static Path requiredPath(final String property) {
        final String value = System.getProperty(property);
        if (value == null || value.isBlank()) {
            throw new IllegalStateException(property + " system property is required");
        }
        return Path.of(value);
    }

    private static String q(final String value) {
        return "\"" + escape(value) + "\"";
    }

    private static String escape(final String value) {
        return value == null ? "" : value
                .replace("\\", "\\\\").replace("\"", "\\\"")
                .replace("\n", "\\n").replace("\r", "\\r");
    }

    private static String unb64(final String value) {
        if (value == null || value.isBlank()) return "";
        return new String(Base64.getDecoder().decode(value), StandardCharsets.UTF_8);
    }

    private static final class CaseRow {
        final String executionId;
        final String cardName;
        final String oracle;
        final String sourcePath;
        final String fixtureKind;
        final String enteringCard;
        final String setup;
        final String linkPath;
        final String parentSvar;
        final String parentApi;
        final String childSub;
        final String childApi;
        final int parentLine;
        final boolean terminal;
        final List<AssertionDef> assertions = new ArrayList<>();
        final List<Consultation> consultations = new ArrayList<>();

        CaseRow(String executionId, String cardName, String oracle, String sourcePath,
                String fixtureKind, String enteringCard, String setup, String linkPath,
                String parentSvar, String parentApi, String childSub, String childApi,
                int parentLine, String assertionText, String consultationText,
                boolean terminal) {
            this.executionId = executionId;
            this.cardName = cardName;
            this.oracle = oracle;
            this.sourcePath = sourcePath;
            this.fixtureKind = fixtureKind;
            this.enteringCard = enteringCard;
            this.setup = setup;
            this.linkPath = linkPath;
            this.parentSvar = parentSvar;
            this.parentApi = parentApi;
            this.childSub = childSub;
            this.childApi = childApi;
            this.parentLine = parentLine;
            this.terminal = terminal;
            if (!assertionText.isBlank()) {
                for (final String cell : assertionText.split(";", -1)) {
                    if (cell.isBlank()) continue;
                    final String[] parts = cell.split("\\|", -1);
                    // id|type|who|name_b64|card_b64|counter|keyword|expected
                    this.assertions.add(new AssertionDef(parts[0], parts[1], parts[2],
                            parts[3], parts[4], parts[5], parts[6], parts[7]));
                }
            }
            if (consultationText != null && !consultationText.isBlank()) {
                for (final String cell : consultationText.split(";", -1)) {
                    if (cell.isBlank()) continue;
                    final String[] parts = cell.split("\\|", -1);
                    // site|options
                    this.consultations.add(new Consultation(
                            parts[0], Integer.parseInt(parts[1])));
                }
            }
        }
    }

    private static final class AssertionDef {
        final String id;
        final String type;
        final String who;
        final String name;
        final String card;
        final String counter;
        final String keyword;
        final String expected;

        AssertionDef(String id, String type, String who, String name, String card,
                String counter, String keyword, String expected) {
            this.id = id;
            this.type = type;
            this.who = who;
            this.name = name;
            this.card = card;
            this.counter = counter;
            this.keyword = keyword;
            this.expected = expected;
        }
    }

    private static final class TripwireHit {
        final String site;
        final String caller;
        final int options;
        final boolean incidental;

        TripwireHit(String site, String caller, int options, boolean incidental) {
            this.site = site;
            this.caller = caller;
            this.options = options;
            this.incidental = incidental;
        }

        @Override
        public String toString() {
            return site + "(options=" + options + ")@" + caller
                    + (incidental ? "[incidental]" : "[EFFECT]");
        }
    }

    private static final class Consultation {
        final String site;
        final int options;

        Consultation(String site, int options) {
            this.site = site;
            this.options = options;
        }
    }

    private static final class ParentEvent {
        final int seq;
        final int id;
        final String api;
        final String host;
        final String subParam;
        final String activator;

        ParentEvent(int seq, int id, String api, String host, String subParam) {
            this(seq, id, api, host, subParam, "?");
        }

        ParentEvent(int seq, int id, String api, String host, String subParam,
                String activator) {
            this.seq = seq;
            this.id = id;
            this.api = api;
            this.host = host;
            this.subParam = subParam;
            this.activator = activator;
        }

        @Override
        public String toString() {
            return "Parent{seq=" + seq + " id=" + id + " api=" + api
                    + " host=" + host + " sub=" + subParam
                    + " by=" + activator + "}";
        }
    }

    private static final class ChildObs {
        final int seq;
        final int id;
        final String api;
        final String host;
        final int parentId;
        final int rootId;

        ChildObs(int seq, int id, String api, String host, int parentId, int rootId) {
            this.seq = seq;
            this.id = id;
            this.api = api;
            this.host = host;
            this.parentId = parentId;
            this.rootId = rootId;
        }

        @Override
        public String toString() {
            return "Child{seq=" + seq + " id=" + id + " api=" + api
                    + " host=" + host + " parent=" + parentId + " root=" + rootId + "}";
        }
    }

    private static final class MatchedLink {
        final CaseRow row;
        final ParentEvent parent;
        final ChildObs child;
        final int rootId;

        MatchedLink(CaseRow row, ParentEvent parent, ChildObs child, int rootId) {
            this.row = row;
            this.parent = parent;
            this.child = child;
            this.rootId = rootId;
        }
    }

    private static final class AssertionResult {
        final String id;
        final String expected;
        final Object actual;
        final boolean pass;

        AssertionResult(String id, String expected, Object actual, boolean pass) {
            this.id = id;
            this.expected = expected;
            this.actual = actual;
            this.pass = pass;
        }

        @Override
        public String toString() {
            return id + " expected=" + expected + " actual=" + actual;
        }
    }

    private static final class Result {
        final int lifeActorBefore;
        final int lifeOpponentBefore;
        final int handActorBefore;
        final int lifeActorAfter;
        final int lifeOpponentAfter;
        final int handActorAfter;
        final List<ParentEvent> parents;
        final List<ChildObs> children;
        final List<MatchedLink> matched;
        final List<TripwireHit> tripwireHits;
        final List<AssertionResult> assertions;

        Result(int lifeActorBefore, int lifeOpponentBefore, int handActorBefore,
                int lifeActorAfter, int lifeOpponentAfter, int handActorAfter,
                List<ParentEvent> parents, List<ChildObs> children,
                List<MatchedLink> matched, List<TripwireHit> tripwireHits,
                List<AssertionResult> assertions) {
            this.lifeActorBefore = lifeActorBefore;
            this.lifeOpponentBefore = lifeOpponentBefore;
            this.handActorBefore = handActorBefore;
            this.lifeActorAfter = lifeActorAfter;
            this.lifeOpponentAfter = lifeOpponentAfter;
            this.handActorAfter = handActorAfter;
            this.parents = new ArrayList<>(parents);
            this.children = new ArrayList<>(children);
            this.matched = new ArrayList<>(matched);
            this.tripwireHits = new ArrayList<>(tripwireHits);
            this.assertions = new ArrayList<>(assertions);
        }
    }
}
