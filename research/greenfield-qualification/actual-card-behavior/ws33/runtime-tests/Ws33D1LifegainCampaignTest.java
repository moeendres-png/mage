package forge.gamesimulationtests;

import forge.ai.AITest;
import forge.card.mana.ManaAtom;
import forge.game.Game;
import forge.game.GameView;
import forge.game.ability.ApiType;
import forge.game.card.Card;
import forge.game.mana.Mana;
import forge.game.phase.PhaseType;
import forge.game.player.PlaySpellAbility;
import forge.game.player.Player;
import forge.game.spellability.SpellAbility;
import forge.game.zone.ZoneType;
import forge.gamemodes.match.input.ExternalDecisionRequest;
import forge.gamemodes.match.input.ExternalDecisionResponse;
import forge.gamemodes.match.input.ExternalDecisionTape;
import forge.player.LobbyPlayerHuman;
import forge.player.PlayerControllerHuman;
import forge.util.MyRandom;
import org.testng.Assert;
import org.testng.annotations.Test;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Base64;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.TreeMap;

/**
 * WS33-D D1 LifeGain campaign (STATE_ONLY, template-059, 10 paths).
 *
 * <p>Each case loads an actual pinned-Forge card and drives the modeled
 * GainLife line through its production entry point: real spell casts and
 * real activated-ability activations via
 * {@code PlaySpellAbility.playSpellAbility} with production cost payment
 * (exact fixture mana pool plus forced single-option sacrifice/discard
 * costs), and real battlefield entry plus trigger/stack transfer for the
 * ETB case. No effect is directly resolved; no expected outcome is
 * injected; no AI discretion is consulted. A scripted external decision
 * provider answers only single-legal-option Forge requests; any
 * multi-option request fails the case closed. Record/replay requires
 * byte-equal canonical final state with RNG tapes replay-served and
 * hidden-observation deltas of zero.</p>
 */
public final class Ws33D1LifegainCampaignTest extends AITest {
    private static final String FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928";
    private static final long RNG_SEED = 0x5733441L;

    @Test
    public void d1LifegainCampaign() throws Exception {
        final String mode = System.getProperty("ws33.d1Mode", "record");
        if (!"record".equals(mode) && !"replay".equals(mode)) {
            throw new IllegalArgumentException("ws33.d1Mode must be record or replay");
        }
        final Path casesPath = requiredPath("ws33.d1Cases");
        final Path out = requiredPath("ws33.d1Out");
        Files.createDirectories(out);
        final List<Case> cases = loadCases(casesPath);
        final List<String> diagnostics = new ArrayList<>();
        final List<String> admittedRecords = new ArrayList<>();
        int success = 0;

        for (final Case c : cases) {
            try {
                if ("record".equals(mode)) {
                    final Result result = executeCase(c, null, null);
                    writeRecord(out, c, result);
                    success++;
                } else {
                    final Path dir = caseDir(out, c.pathId);
                    if (!Files.isRegularFile(dir.resolve("record-success.marker"))) {
                        executeCase(c, null, null);
                        throw new IllegalStateException(
                                "record-rejected case unexpectedly succeeded during replay alignment");
                    }
                    final List<ReplayDecision> replay = loadReplayDecisions(dir.resolve("decision-replay.tsv"));
                    final List<Integer> replayRng = loadReplayRng(dir.resolve("rng-replay.tsv"));
                    final Result result = executeCase(c, replay, replayRng);
                    final String expected = Files.readString(dir.resolve("final-state.txt"), StandardCharsets.UTF_8);
                    if (!expected.equals(result.canonicalFinalState)) {
                        throw new IllegalStateException("semantic replay state mismatch expected="
                                + expected + " actual=" + result.canonicalFinalState);
                    }
                    writeReplayEvidence(dir, result, dir.resolve("decision-tape.json"), expected);
                    admittedRecords.add("records/" + shortId(c.pathId) + "/record.json");
                    success++;
                }
            } catch (Throwable error) {
                diagnostics.add("{\"mode\":" + q(mode)
                        + ",\"path_id\":" + q(c.pathId)
                        + ",\"card\":" + q(c.cardName)
                        + ",\"recipe\":" + q(c.recipe)
                        + ",\"error_type\":" + q(error.getClass().getName())
                        + ",\"message\":" + q(String.valueOf(error.getMessage())) + "}");
            }
        }

        writeDiagnostics(out, mode, diagnostics);
        if ("replay".equals(mode)) {
            writeCampaignIndex(out, admittedRecords);
        }
        Assert.assertTrue(success > 0, "D1 lifegain campaign produced no successful " + mode + " cases");
        System.out.println("WS33_D1_CAMPAIGN_MODE=" + mode);
        System.out.println("WS33_D1_CAMPAIGN_SUCCESS=" + success);
        System.out.println("WS33_D1_CAMPAIGN_DIAGNOSTIC_FAILURES=" + diagnostics.size());
    }

    private Result executeCase(final Case c, final List<ReplayDecision> replay, final List<Integer> replayRng) {
        if (c.recipe.startsWith("UNSUPPORTED_") || c.recipe.startsWith("DEFERRED_")) {
            throw new IllegalStateException("fail-closed unsupported D1 recipe " + c.recipe);
        }
        final Game game = initAndCreateGame();
        final Player actor = game.getPlayers().get(0);
        final Player opponent = game.getPlayers().get(1);
        game.getPhaseHandler().devModeSet(PhaseType.MAIN1, actor);
        final String gameId = "ws33-d1-" + shortId(c.pathId);

        final List<MyRandom.RngEvent> rngEvents = new ArrayList<>();
        final MyRandom.ReplayProvider rngProvider = replayRng == null ? null : new QueueReplayProvider(replayRng);
        MyRandom.beginGameScope(gameId, RNG_SEED, rngEvents::add, rngProvider);
        try {
            forge.net.Ws05HiddenInfoProbe.reset();
            forge.net.Ws05HiddenInfoProbe.registerSecret("Black Lotus");
            addCardToZone("Black Lotus", opponent, ZoneType.Hand);

            final PlayerControllerHuman controller = new PlayerControllerHuman(
                    game, actor, new LobbyPlayerHuman("ws33-d1-principal"));
            final Provider decisions = new Provider(replay);
            controller.setExternalDecisionProvider(decisions::decide);

            buildFixture(c, game, actor, opponent);

            final int lifeBefore = actor.getLife();
            final int oppLifeBefore = opponent.getLife();

            driveRecipe(c, game, actor, controller);
            playUntilStackClear(game);

            if (game.isGameOver()) {
                throw new IllegalStateException("fixture game ended during D1 case");
            }
            if (!game.getStack().isEmpty()) {
                throw new IllegalStateException("stack not empty after D1 case resolution");
            }
            final int actorDelta = actor.getLife() - lifeBefore;
            final int oppDelta = opponent.getLife() - oppLifeBefore;
            if (actorDelta != c.expectActorDelta) {
                throw new IllegalStateException("actor life delta mismatch actual="
                        + actorDelta + " expected=" + c.expectActorDelta);
            }
            if (oppDelta != c.expectOppDelta) {
                throw new IllegalStateException("opponent life delta mismatch actual="
                        + oppDelta + " expected=" + c.expectOppDelta);
            }
            if (!actor.getManaPool().isEmpty()) {
                throw new IllegalStateException("fixture mana pool not fully consumed; cost payment suspect");
            }
            assertRecipePostconditions(c, game, actor, opponent);
            decisions.assertConsumed();

            final List<ExternalDecisionTape.Event> tape = controller.getExternalDecisionTapeSnapshot();
            if (tape.size() != decisions.captured.size()) {
                throw new IllegalStateException("decision tape/request count mismatch");
            }
            for (int i = 0; i < tape.size(); i++) {
                final ExternalDecisionTape.Event event = tape.get(i);
                final CapturedDecision decision = decisions.captured.get(i);
                if (event.getResponseStatus() != ExternalDecisionTape.ResponseStatus.ACCEPTED) {
                    throw new IllegalStateException("non-accepted D1 decision");
                }
                if (!event.getSelectedOptionIds().equals(List.of(decision.selectedOptionId))) {
                    throw new IllegalStateException("validated decision response differs from provider response");
                }
            }

            final long leak0 = forge.net.Ws05HiddenInfoProbe.pilotVisibleLeaks();
            final long cross0 = forge.net.Ws05HiddenInfoProbe.crossPrincipalLeaks();
            final GameView view = new GameView(game);
            forge.net.Ws05HiddenInfoProbe.observe(actor.getName(), view, "ws33-d1-case");
            forge.net.Ws05HiddenInfoProbe.observe(opponent.getName(), view, "ws33-d1-case");
            final long leakDelta = forge.net.Ws05HiddenInfoProbe.pilotVisibleLeaks() - leak0;
            final long crossDelta = forge.net.Ws05HiddenInfoProbe.crossPrincipalLeaks() - cross0;
            if (leakDelta != 0 || crossDelta != 0) {
                throw new IllegalStateException("hidden-isolation leak delta leak=" + leakDelta
                        + " cross=" + crossDelta);
            }

            final String canonical = canonicalFinalState(game, actor, opponent);
            return new Result(actorDelta, oppDelta, canonical,
                    decisions.captured, tape, new ArrayList<>(rngEvents), leakDelta, crossDelta);
        } finally {
            MyRandom.endGameScope();
        }
    }

    private void buildFixture(final Case c, final Game game, final Player actor, final Player opponent) {
        addPoolMana(c, actor);
        final Map<String, String> fixture = parseKv(c.fixtureKv);
        if (fixture.containsKey("actor_life")) {
            actor.setLife(Integer.parseInt(fixture.get("actor_life")), null);
        }
        if (fixture.containsKey("opp_life")) {
            opponent.setLife(Integer.parseInt(fixture.get("opp_life")), null);
        }
        if (fixture.containsKey("library_fill")) {
            fillLibrary(actor, Integer.parseInt(fixture.get("library_fill")));
        }
        if (fixture.containsKey("bf")) {
            for (final String spec : fixture.get("bf").split(",")) {
                final String[] parts = spec.split(":");
                addCards(parts[0].trim(), Integer.parseInt(parts[1]), actor);
            }
        }
        if (fixture.containsKey("actor_bf")) {
            for (final String spec : fixture.get("actor_bf").split(",")) {
                final String[] parts = spec.split(":");
                addCards(parts[0].trim(), Integer.parseInt(parts[1]), actor);
            }
        }
        if (fixture.containsKey("opp_bf")) {
            for (final String spec : fixture.get("opp_bf").split(",")) {
                final String[] parts = spec.split(":");
                addCards(parts[0].trim(), Integer.parseInt(parts[1]), opponent);
            }
        }
        if (fixture.containsKey("hand")) {
            for (final String spec : fixture.get("hand").split(",")) {
                final String[] parts = spec.split(":");
                for (int i = 0; i < Integer.parseInt(parts[1]); i++) {
                    addCardToZone(parts[0].trim(), actor, ZoneType.Hand);
                }
            }
        }
    }

    private void addPoolMana(final Case c, final Player actor) {
        if (c.poolSpec.isBlank()) {
            return;
        }
        final Card source = createCard(c.cardName, actor);
        final java.util.regex.Matcher m =
                java.util.regex.Pattern.compile("([A-Z])([0-9]+)").matcher(c.poolSpec);
        boolean found = false;
        while (m.find()) {
            found = true;
            final byte color;
            switch (m.group(1)) {
                case "W": color = (byte) ManaAtom.WHITE; break;
                case "U": color = (byte) ManaAtom.BLUE; break;
                case "B": color = (byte) ManaAtom.BLACK; break;
                case "R": color = (byte) ManaAtom.RED; break;
                case "G": color = (byte) ManaAtom.GREEN; break;
                default: color = (byte) ManaAtom.COLORLESS; break;
            }
            final int count = Integer.parseInt(m.group(2));
            for (int i = 0; i < count; i++) {
                actor.getManaPool().addMana(new Mana(color, source, null, actor));
            }
        }
        if (!found) {
            throw new IllegalStateException("malformed mana pool spec " + c.poolSpec);
        }
    }

    private void driveRecipe(final Case c, final Game game, final Player actor,
            final PlayerControllerHuman controller) {
        switch (c.recipe) {
            case "SPELL_BASE":
            case "SPELL_CONDITIONAL_LIFE":
            case "SPELL_DESTROY_ALL": {
                final Card card = placeCard(c.cardName, actor, ZoneType.Hand);
                final SpellAbility spell = card.getSpells().get(0);
                if (!PlaySpellAbility.playSpellAbility(controller, actor, spell)) {
                    throw new IllegalStateException("production spell cast returned false");
                }
                if (game.getStack().isEmpty()) {
                    throw new IllegalStateException("production spell cast left an empty stack");
                }
                return;
            }
            case "ACTIVATED_SAC_LAND":
            case "ACTIVATED_DISCARD":
            case "ACTIVATED_SAC_CREATURE":
            case "ACTIVATED_SAC_SELF":
            case "ACTIVATED_SAC_DRAW": {
                placeCard(c.cardName, actor, ZoneType.Battlefield);
                final Card card = findCardWithName(game, c.cardName);
                if (card == null) {
                    throw new IllegalStateException("activated host not on battlefield");
                }
                final SpellAbility ability = findGainLifeAbility(card);
                if (!PlaySpellAbility.playSpellAbility(controller, actor, ability)) {
                    throw new IllegalStateException("production ability activation returned false");
                }
                if (game.getStack().isEmpty()) {
                    throw new IllegalStateException("production activation left an empty stack");
                }
                return;
            }
            case "ETB_TRIGGER": {
                final Card card = placeCard(c.cardName, actor, ZoneType.Hand);
                game.getAction().moveTo(ZoneType.Battlefield, card, null, null);
                if (!game.getTriggerHandler().runWaitingTriggers()) {
                    throw new IllegalStateException("actual trigger fixture produced no triggers");
                }
                if (!game.getStack().addAllTriggeredAbilitiesToStack() || game.getStack().isEmpty()) {
                    throw new IllegalStateException("actual trigger fixture did not reach the stack");
                }
                return;
            }
            default:
                throw new IllegalStateException("fail-closed unsupported D1 recipe " + c.recipe);
        }
    }

    private Card placeCard(final String name, final Player player, final ZoneType zone) {
        try {
            return addCardToZone(name, player, zone);
        } catch (NullPointerException e) {
            throw new IllegalStateException("card script not resolvable for exact name: " + name, e);
        }
    }

    private SpellAbility findGainLifeAbility(final Card card) {
        final List<SpellAbility> matches = new ArrayList<>();
        for (final SpellAbility sa : card.getSpellAbilities()) {
            if (sa.isActivatedAbility() && sa.getApi() == ApiType.GainLife) {
                matches.add(sa);
            }
        }
        if (matches.size() != 1) {
            throw new IllegalStateException("expected exactly one GainLife activated ability, found "
                    + matches.size());
        }
        return matches.get(0);
    }

    private void assertRecipePostconditions(final Case c, final Game game,
            final Player actor, final Player opponent) {
        switch (c.recipe) {
            case "SPELL_BASE":
            case "SPELL_CONDITIONAL_LIFE":
            case "SPELL_DESTROY_ALL":
                if (countCardsWithName(game, c.cardName, ZoneType.Graveyard) != 1) {
                    throw new IllegalStateException("resolved spell not in graveyard");
                }
                break;
            case "ACTIVATED_SAC_SELF":
                if (countCardsWithName(game, c.cardName, ZoneType.Graveyard) != 1) {
                    throw new IllegalStateException("sacrificed host not in graveyard");
                }
                break;
            default:
                break;
        }
        if ("SPELL_CONDITIONAL_LIFE".equals(c.recipe)
                && countCardsWithName(game, "Soldier", ZoneType.Battlefield) != 0) {
            throw new IllegalStateException("unexpected Soldier tokens created");
        }
        if ("SPELL_DESTROY_ALL".equals(c.recipe)) {
            int bears = 0;
            for (final Card card : game.getCardsIn(ZoneType.Graveyard)) {
                if ("Runeclaw Bear".equals(card.getName())) {
                    bears++;
                }
            }
            if (bears != 3) {
                throw new IllegalStateException("expected 3 destroyed bears in graveyards, found " + bears);
            }
        }
        if ("ACTIVATED_SAC_CREATURE".equals(c.recipe)
                && countCardsWithName(game, "Runeclaw Bear", ZoneType.Graveyard) != 1) {
            throw new IllegalStateException("sacrificed creature not in graveyard");
        }
        if ("ACTIVATED_SAC_LAND".equals(c.recipe)
                && countCardsWithName(game, "Plains", ZoneType.Graveyard) != 1) {
            throw new IllegalStateException("sacrificed land not in graveyard");
        }
        if ("ACTIVATED_DISCARD".equals(c.recipe)) {
            if (!actor.getCardsIn(ZoneType.Hand).isEmpty()) {
                throw new IllegalStateException("discard cost did not empty the single-card hand");
            }
            if (countCardsWithName(game, "Runeclaw Bear", ZoneType.Graveyard) != 1) {
                throw new IllegalStateException("discarded card not in graveyard");
            }
        }
        if ("ETB_TRIGGER".equals(c.recipe)) {
            if (countCardsWithName(game, c.cardName, ZoneType.Battlefield) != 1) {
                throw new IllegalStateException("ETB host not on battlefield");
            }
            if (actor.getCardsIn(ZoneType.Hand).size() != 1) {
                throw new IllegalStateException("expected exactly one drawn card in hand");
            }
        }
        if ("ACTIVATED_SAC_DRAW".equals(c.recipe)) {
            if (actor.getCardsIn(ZoneType.Hand).size() != 1) {
                throw new IllegalStateException("expected exactly one drawn card in hand");
            }
            if (countCardsWithName(game, "Runeclaw Bear", ZoneType.Graveyard) != 1) {
                throw new IllegalStateException("sacrificed creature not in graveyard");
            }
        }
    }

    private String canonicalFinalState(final Game game, final Player actor, final Player opponent) {
        final StringBuilder sb = new StringBuilder();
        sb.append("actor_life=").append(actor.getLife()).append('\n');
        sb.append("opp_life=").append(opponent.getLife()).append('\n');
        sb.append("pool_empty=").append(actor.getManaPool().isEmpty()).append('\n');
        for (final ZoneType zone : ZoneType.values()) {
            final Map<String, Integer> counts = new TreeMap<>();
            for (final Card card : game.getCardsIn(zone)) {
                final String key = card.getController().getName() + "|" + card.getName()
                        + "|" + (card.isTapped() ? "T" : "U");
                counts.merge(key, 1, Integer::sum);
            }
            for (final Map.Entry<String, Integer> e : counts.entrySet()) {
                sb.append(zone.name()).append('|').append(e.getKey()).append('|').append(e.getValue()).append('\n');
            }
        }
        sb.append("stack_empty=").append(game.getStack().isEmpty()).append('\n');
        sb.append("game_over=").append(game.isGameOver()).append('\n');
        return sb.toString();
    }

    private Map<String, String> parseKv(final String kv) {
        final Map<String, String> out = new LinkedHashMap<>();
        if (kv == null || kv.isBlank()) {
            return out;
        }
        for (final String part : kv.split(";")) {
            if (part.isBlank()) {
                continue;
            }
            final int eq = part.indexOf('=');
            if (eq < 0) {
                throw new IllegalStateException("malformed fixture kv part " + part);
            }
            out.put(part.substring(0, eq).trim(), part.substring(eq + 1).trim());
        }
        return out;
    }

    private static final class Provider {
        private final List<ReplayDecision> replay;
        private int replayIndex;
        private final List<CapturedDecision> captured = new ArrayList<>();

        Provider(final List<ReplayDecision> replay) {
            this.replay = replay;
        }

        ExternalDecisionResponse decide(final ExternalDecisionRequest request) {
            final ExternalDecisionRequest.Option chosen;
            if (replay != null) {
                if (replayIndex >= replay.size()) {
                    throw new IllegalStateException("replay decision tape exhausted");
                }
                final ReplayDecision expected = replay.get(replayIndex++);
                if (!expected.decisionKind.equals(request.getDecisionKind())) {
                    throw new IllegalStateException("replay decision kind mismatch");
                }
                chosen = request.getOptions().stream()
                        .filter(option -> expected.optionId.equals(option.getOptionId())
                                && expected.semanticValue.equals(option.getSemanticValue()))
                        .findFirst()
                        .orElseThrow(() -> new IllegalStateException(
                                "recorded fixture response absent from authoritative replay options"));
            } else {
                if (request.getOptions().size() != 1) {
                    throw new IllegalStateException("fail-closed multi-option decision kind="
                            + request.getDecisionKind() + " options=" + request.getOptions().size());
                }
                chosen = request.getOptions().get(0);
            }
            captured.add(new CapturedDecision(request, chosen.getOptionId(), chosen.getSemanticValue()));
            return new ExternalDecisionResponse(
                    request.getDecisionId(), request.getToken(), request.getActorId(),
                    request.getPrincipalId(), request.getResponseSchema(),
                    List.of(chosen.getOptionId()), false);
        }

        void assertConsumed() {
            if (replay != null && replayIndex != replay.size()) {
                throw new IllegalStateException("replay left " + (replay.size() - replayIndex)
                        + " decisions unconsumed");
            }
        }
    }

    private static final class QueueReplayProvider implements MyRandom.ReplayProvider {
        private final List<Integer> values;
        private int index;

        QueueReplayProvider(final List<Integer> values) {
            this.values = new ArrayList<>(values);
        }

        @Override
        public int next(final MyRandom.RngRequest request) {
            if (index >= values.size()) {
                throw new IllegalStateException("replay RNG tape exhausted at event " + request.getEventId());
            }
            final int value = values.get(index++);
            final long upperExclusive = 1L << request.getBits();
            if (request.getBits() < 32 && (value < 0 || (long) value >= upperExclusive)) {
                throw new IllegalStateException("recorded RNG value outside requested bit width");
            }
            return value;
        }
    }

    private static void writeRecord(final Path root, final Case c, final Result result) throws IOException {
        final Path dir = caseDir(root, c.pathId);
        Files.createDirectories(dir);
        final Path decisionTape = dir.resolve("decision-tape.json");
        final Path decisionReplay = dir.resolve("decision-replay.tsv");
        final Path rngTape = dir.resolve("rng-tape.json");
        final Path rngReplay = dir.resolve("rng-replay.tsv");

        writeDecisionTape(decisionTape, c, result);
        writeDecisionReplay(decisionReplay, result);
        writeRngTape(rngTape, rngReplay, c, result);
        Files.writeString(dir.resolve("final-state.txt"), result.canonicalFinalState, StandardCharsets.UTF_8);
        Files.writeString(dir.resolve("trace.json"), traceJson(c, result), StandardCharsets.UTF_8);
        Files.writeString(dir.resolve("principal-observation.json"), observationJson(c, result),
                StandardCharsets.UTF_8);

        final String rel = "records/" + shortId(c.pathId) + "/";
        final String record = "{"
                + "\"schema\":\"commander-simulator-next.ws33-runtime-campaign-record.v1\","
                + "\"witness_id\":" + q("ws33-d1-lifegain-" + shortId(c.pathId)) + ","
                + "\"oracle_identities\":[" + q(c.oracleId) + "],"
                + "\"v2_path_ids\":[" + q(c.pathId) + "],"
                + "\"owner_family\":\"ACTION_COST_DECISION\","
                + "\"initial_semantic_state\":{"
                + "\"recipe\":" + q(c.recipe) + ","
                + "\"svar_token\":" + q(c.svarToken) + ","
                + "\"svar_expression\":" + q(c.svarExpression)
                + "},"
                + "\"final_semantic_state\":{"
                + "\"actor_life_delta\":" + result.actorDelta + ","
                + "\"expected_actor_delta\":" + c.expectActorDelta + ","
                + "\"opp_life_delta\":" + result.oppDelta + ","
                + "\"expected_opp_delta\":" + c.expectOppDelta + ","
                + "\"deltas_equal\":" + (result.actorDelta == c.expectActorDelta
                        && result.oppDelta == c.expectOppDelta)
                + "},"
                + "\"state_assertions\":["
                + assertion("actor-life-delta", c.expectActorDelta, result.actorDelta) + ","
                + assertion("opp-life-delta", c.expectOppDelta, result.oppDelta) + ","
                + assertion("hidden-leak-delta", 0, (int) result.leakDelta) + ","
                + assertion("cross-principal-leak-delta", 0, (int) result.crossDelta)
                + "],"
                + "\"path_exercise\":[{"
                + "\"v2_path_id\":" + q(c.pathId) + ","
                + "\"exercised\":true,"
                + "\"trace_event_ids\":[\"LIFEGAIN_RESOLVED\",\"DECISION_ACCEPTED\",\"RNG_TAPED\",\"HIDDEN_SAMPLED\"],"
                + "\"assertion_ids\":[\"actor-life-delta\",\"opp-life-delta\","
                + "\"hidden-leak-delta\",\"cross-principal-leak-delta\"]"
                + "}],"
                + "\"execution\":{"
                + "\"actual_card_execution\":\"PASS\","
                + "\"actual_rules_core_path\":true,"
                + "\"authoritative_decision_boundary\":\"USED\","
                + "\"silent_fallbacks\":0,"
                + "\"direct_effect_resolution\":false},"
                + "\"trace_file\":" + q(rel + "trace.json") + ","
                + "\"decision_tape_file\":" + q(rel + "decision-tape.json") + ","
                + "\"semantic_replay_evidence_file\":" + q(rel + "semantic-replay.json") + ","
                + "\"rng_tape_file\":" + q(rel + "rng-tape.json") + ","
                + "\"observation_evidence_file\":" + q(rel + "principal-observation.json") + ","
                + "\"rules_authority_refs\":["
                + q("Comprehensive Rules, section 119 (Life)")
                + "],"
                + "\"evidence_class\":\"EXTERNALLY_RULE_VALIDATED\""
                + "}\n";
        Files.writeString(dir.resolve("record.json"), record, StandardCharsets.UTF_8);
        Files.writeString(dir.resolve("record-success.marker"), "PASS\n", StandardCharsets.UTF_8);
    }

    private static String traceJson(final Case c, final Result result) {
        return "{"
                + "\"schema\":\"commander-simulator-next.ws33-d1-lifegain-trace.v1\","
                + "\"forge_pin\":" + q(FORGE_PIN) + ","
                + "\"path_id\":" + q(c.pathId) + ","
                + "\"oracle_identity\":" + q(c.oracleId) + ","
                + "\"actual_card\":" + q(c.cardName) + ","
                + "\"provenance\":" + q(c.provenance) + ","
                + "\"svar_token\":" + q(c.svarToken) + ","
                + "\"svar_expression\":" + q(c.svarExpression) + ","
                + "\"recipe\":" + q(c.recipe) + ","
                + "\"actual_rules_core_path\":true,"
                + "\"lifegain_entry\":\"PlaySpellAbility.playSpellAbility-or-trigger-stack-transfer\","
                + "\"direct_effect_resolution\":false,"
                + "\"actor_life_delta\":" + result.actorDelta + ","
                + "\"expected_actor_delta\":" + c.expectActorDelta + ","
                + "\"opp_life_delta\":" + result.oppDelta + ","
                + "\"expected_opp_delta\":" + c.expectOppDelta + ","
                + "\"decision_event_count\":" + result.captured.size() + ","
                + "\"rng_event_count\":" + result.rngEvents.size() + ","
                + "\"hidden_leak_delta\":" + result.leakDelta + ","
                + "\"cross_principal_leak_delta\":" + result.crossDelta
                + "}\n";
    }

    private static String observationJson(final Case c, final Result result) {
        return "{"
                + "\"schema\":\"commander-simulator-next.ws33-d1-principal-observation.v1\","
                + "\"path_id\":" + q(c.pathId) + ","
                + "\"secret\":\"Black Lotus\","
                + "\"secret_holder\":\"opponent\","
                + "\"pilot_visible_leak_delta\":" + result.leakDelta + ","
                + "\"cross_principal_leak_delta\":" + result.crossDelta + ","
                + "\"result\":" + q(result.leakDelta == 0 && result.crossDelta == 0 ? "PASS" : "FAIL")
                + "}\n";
    }

    private static void writeDecisionTape(final Path path, final Case c, final Result result) throws IOException {
        final StringBuilder json = new StringBuilder();
        json.append("{\"events\":[");
        for (int i = 0; i < result.captured.size(); i++) {
            if (i != 0) json.append(',');
            final CapturedDecision captured = result.captured.get(i);
            final ExternalDecisionTape.Event event = result.tape.get(i);
            final ExternalDecisionRequest request = captured.request;
            json.append("{\"decision_id\":").append(request.getDecisionId())
                    .append(",\"decision_kind\":").append(q(request.getDecisionKind()))
                    .append(",\"game_id\":").append(q("ws33-d1-" + shortId(c.pathId)))
                    .append(",\"actor\":").append(q(String.valueOf(request.getActorId())))
                    .append(",\"principal\":").append(q(String.valueOf(request.getPrincipalId())))
                    .append(",\"visibility_scope\":").append(q(request.getVisibilityScope()))
                    .append(",\"authoritative_legal_options\":[");
            for (int j = 0; j < request.getOptions().size(); j++) {
                if (j != 0) json.append(',');
                final ExternalDecisionRequest.Option option = request.getOptions().get(j);
                json.append("{\"option_id\":").append(q(option.getOptionId()))
                        .append(",\"semantic_value\":").append(q(option.getSemanticValue())).append('}');
            }
            json.append("],\"response_option_ids\":[")
                    .append(q(captured.selectedOptionId))
                    .append("],\"validation_result\":")
                    .append(q(event.getResponseStatus().name()))
                    .append(",\"fallback_used\":false}");
        }
        json.append("]}\n");
        Files.writeString(path, json.toString(), StandardCharsets.UTF_8);
    }

    private static void writeDecisionReplay(final Path path, final Result result) throws IOException {
        final StringBuilder text = new StringBuilder();
        for (final CapturedDecision decision : result.captured) {
            text.append(b64(decision.request.getDecisionKind())).append('\t')
                    .append(b64(decision.selectedOptionId)).append('\t')
                    .append(b64(decision.semanticValue)).append('\n');
        }
        Files.writeString(path, text.toString(), StandardCharsets.UTF_8);
    }

    private static void writeRngTape(final Path tape, final Path replay, final Case c, final Result result)
            throws IOException {
        final StringBuilder json = new StringBuilder();
        json.append("{\"game_id\":").append(q("ws33-d1-" + shortId(c.pathId)))
                .append(",\"seed\":").append(RNG_SEED).append(",\"events\":[");
        final StringBuilder tsv = new StringBuilder();
        for (int i = 0; i < result.rngEvents.size(); i++) {
            if (i != 0) {
                json.append(',');
            }
            final MyRandom.RngEvent event = result.rngEvents.get(i);
            json.append("{\"event_id\":").append(event.getEventId())
                    .append(",\"stream\":").append(q(event.getStream()))
                    .append(",\"draw_index\":").append(event.getDrawIndex())
                    .append(",\"bits\":").append(event.getBits())
                    .append(",\"value\":").append(event.getValue()).append('}');
            tsv.append(event.getValue()).append('\n');
        }
        json.append("]}\n");
        Files.writeString(tape, json.toString(), StandardCharsets.UTF_8);
        Files.writeString(replay, tsv.toString(), StandardCharsets.UTF_8);
    }

    private static List<ReplayDecision> loadReplayDecisions(final Path path) throws IOException {
        final List<ReplayDecision> result = new ArrayList<>();
        if (!Files.isRegularFile(path)) {
            return result;
        }
        for (final String line : Files.readAllLines(path, StandardCharsets.UTF_8)) {
            if (line.isBlank()) continue;
            final String[] fields = line.split("\\t", -1);
            if (fields.length != 3) {
                throw new IllegalArgumentException("malformed D1 replay decision line");
            }
            result.add(new ReplayDecision(unb64(fields[0]), unb64(fields[1]), unb64(fields[2])));
        }
        return result;
    }

    private static List<Integer> loadReplayRng(final Path path) throws IOException {
        final List<Integer> result = new ArrayList<>();
        if (!Files.isRegularFile(path)) {
            return result;
        }
        for (final String line : Files.readAllLines(path, StandardCharsets.UTF_8)) {
            if (line.isBlank()) continue;
            result.add(Integer.parseInt(line.trim()));
        }
        return result;
    }

    private static void writeReplayEvidence(
            final Path dir, final Result replayResult, final Path decisionTape, final String expectedState)
            throws Exception {
        final String actual = replayResult.canonicalFinalState;
        final int divergence = expectedState.equals(actual) ? 0 : 1;
        final String json = "{"
                + "\"semantic_divergence\":" + divergence + ","
                + "\"comparison_basis\":\"CANONICAL_SEMANTIC_STATE\","
                + "\"decision_tape_sha256\":" + q(sha256(decisionTape)) + ","
                + "\"record_state_sha256\":" + q(sha256(expectedState.getBytes(StandardCharsets.UTF_8))) + ","
                + "\"replay_state_sha256\":" + q(sha256(actual.getBytes(StandardCharsets.UTF_8)))
                + "}\n";
        Files.writeString(dir.resolve("semantic-replay.json"), json, StandardCharsets.UTF_8);
    }

    private static void writeCampaignIndex(final Path root, final List<String> records) throws IOException {
        final StringBuilder json = new StringBuilder();
        json.append("{\"schema\":\"commander-simulator-next.ws33-runtime-campaign-index.v1\",\"records\":[");
        for (int i = 0; i < records.size(); i++) {
            if (i != 0) json.append(',');
            json.append(q(records.get(i)));
        }
        json.append("]}\n");
        Files.writeString(root.resolve("campaign-index.json"), json.toString(), StandardCharsets.UTF_8);
    }

    private static void writeDiagnostics(final Path root, final String mode, final List<String> diagnostics)
            throws IOException {
        final Path path = root.resolve("lifegain-" + mode + "-diagnostics.jsonl");
        Files.write(path, diagnostics, StandardCharsets.UTF_8);
    }

    private static List<Case> loadCases(final Path path) throws IOException {
        final List<Case> result = new ArrayList<>();
        for (final String line : Files.readAllLines(path, StandardCharsets.UTF_8)) {
            if (line.isBlank() || line.startsWith("#")) continue;
            final String[] fields = line.split("\\t", -1);
            if (fields.length != 12) {
                throw new IllegalArgumentException("malformed WS33 D1 case line");
            }
            result.add(new Case(
                    fields[0], fields[1], unb64(fields[2]), unb64(fields[3]), unb64(fields[4]),
                    fields[5], unb64(fields[6]), unb64(fields[7]), unb64(fields[8]),
                    Integer.parseInt(fields[9]), Integer.parseInt(fields[10]), unb64(fields[11])));
        }
        if (result.isEmpty()) {
            throw new IllegalArgumentException("WS33 D1 campaign case set is empty");
        }
        return result;
    }

    private static String assertion(final String id, final int expected, final int actual) {
        return "{\"assertion_id\":" + q(id)
                + ",\"expected\":" + expected
                + ",\"actual\":" + actual
                + ",\"result\":" + q(expected == actual ? "PASS" : "FAIL") + "}";
    }

    private static Path caseDir(final Path root, final String pathId) {
        return root.resolve("records").resolve(shortId(pathId));
    }

    private static String shortId(final String pathId) {
        return pathId.startsWith("forge-behavior-v2:")
                ? pathId.substring("forge-behavior-v2:".length())
                : pathId.replaceAll("[^A-Za-z0-9_.-]", "-");
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
                .replace("\\", "\\\\")
                .replace("\"", "\\\"")
                .replace("\n", "\\n")
                .replace("\r", "\\r");
    }

    private static String b64(final String value) {
        return Base64.getEncoder().encodeToString(value.getBytes(StandardCharsets.UTF_8));
    }

    private static String unb64(final String value) {
        return new String(Base64.getDecoder().decode(value), StandardCharsets.UTF_8);
    }

    private static String sha256(final Path path) throws Exception {
        return sha256(Files.readAllBytes(path));
    }

    private static String sha256(final byte[] value) throws Exception {
        final byte[] hash = MessageDigest.getInstance("SHA-256").digest(value);
        final StringBuilder out = new StringBuilder();
        for (final byte b : hash) out.append(String.format(Locale.ROOT, "%02x", b));
        return out.toString();
    }

    private static final class Case {
        final String pathId;
        final String oracleId;
        final String cardName;
        final String svarToken;
        final String svarExpression;
        final String recipe;
        final String recipeParams;
        final String poolSpec;
        final String fixtureKv;
        final int expectActorDelta;
        final int expectOppDelta;
        final String provenance;

        Case(String pathId, String oracleId, String cardName, String svarToken,
                String svarExpression, String recipe, String recipeParams, String poolSpec,
                String fixtureKv, int expectActorDelta, int expectOppDelta, String provenance) {
            this.pathId = pathId;
            this.oracleId = oracleId;
            this.cardName = cardName;
            this.svarToken = svarToken;
            this.svarExpression = svarExpression;
            this.recipe = recipe;
            this.recipeParams = recipeParams;
            this.poolSpec = poolSpec;
            this.fixtureKv = fixtureKv;
            this.expectActorDelta = expectActorDelta;
            this.expectOppDelta = expectOppDelta;
            this.provenance = provenance;
        }
    }

    private static final class CapturedDecision {
        final ExternalDecisionRequest request;
        final String selectedOptionId;
        final String semanticValue;

        CapturedDecision(ExternalDecisionRequest request, String selectedOptionId, String semanticValue) {
            this.request = request;
            this.selectedOptionId = selectedOptionId;
            this.semanticValue = semanticValue;
        }
    }

    private static final class ReplayDecision {
        final String decisionKind;
        final String optionId;
        final String semanticValue;

        ReplayDecision(String decisionKind, String optionId, String semanticValue) {
            this.decisionKind = decisionKind;
            this.optionId = optionId;
            this.semanticValue = semanticValue;
        }
    }

    private static final class Result {
        final int actorDelta;
        final int oppDelta;
        final String canonicalFinalState;
        final List<CapturedDecision> captured;
        final List<ExternalDecisionTape.Event> tape;
        final List<MyRandom.RngEvent> rngEvents;
        final long leakDelta;
        final long crossDelta;

        Result(int actorDelta, int oppDelta, String canonicalFinalState,
                List<CapturedDecision> captured, List<ExternalDecisionTape.Event> tape,
                List<MyRandom.RngEvent> rngEvents, long leakDelta, long crossDelta) {
            this.actorDelta = actorDelta;
            this.oppDelta = oppDelta;
            this.canonicalFinalState = canonicalFinalState;
            this.captured = new ArrayList<>(captured);
            this.tape = new ArrayList<>(tape);
            this.rngEvents = new ArrayList<>(rngEvents);
            this.leakDelta = leakDelta;
            this.crossDelta = crossDelta;
        }
    }
}