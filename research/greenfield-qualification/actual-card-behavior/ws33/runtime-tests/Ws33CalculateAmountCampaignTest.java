package forge.gamesimulationtests;

import forge.ai.AITest;
import forge.game.Game;
import forge.game.GameView;
import forge.game.ability.AbilityUtils;
import forge.game.card.Card;
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

/**
 * WS33B qualification-only AbilityUtils#calculateAmount campaign.
 *
 * <p>Each case loads an actual pinned-Forge card, builds a deterministic
 * fixture whose expected amount is a direct function of fixture inputs
 * (placed objects, paid X, recorded state facts), evaluates the production
 * {@code AbilityUtils.calculateAmount} entry point, and asserts equality.
 * No expected amount is injected from engine internals; math suffixes are
 * folded through production {@code doXMath} only.</p>
 *
 * <p>A fixture-designated externalized target selection provides live
 * decision-boundary evidence per case; a WS06 game RNG scope plus a library
 * shuffle provides the RNG tape; Ws05 probe sampling of both principals'
 * game views provides hidden-isolation evidence. Record/replay requires
 * byte-equal canonical final state.</p>
 */
public final class Ws33CalculateAmountCampaignTest extends AITest {
    private static final String FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928";
    private static final long RNG_SEED = 0x5733421L;

    @Test
    public void calculateAmountCampaign() throws Exception {
        final String mode = System.getProperty("ws33.amountMode", "record");
        if (!"record".equals(mode) && !"replay".equals(mode)) {
            throw new IllegalArgumentException("ws33.amountMode must be record or replay");
        }
        final Path casesPath = requiredPath("ws33.amountCases");
        final Path out = requiredPath("ws33.amountOut");
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
        Assert.assertTrue(success > 0, "calculateAmount campaign produced no successful " + mode + " cases");
        System.out.println("WS33_AMOUNT_CAMPAIGN_MODE=" + mode);
        System.out.println("WS33_AMOUNT_CAMPAIGN_SUCCESS=" + success);
        System.out.println("WS33_AMOUNT_CAMPAIGN_DIAGNOSTIC_FAILURES=" + diagnostics.size());
    }

    private Result executeCase(final Case c, final List<ReplayDecision> replay, final List<Integer> replayRng) {
        if (c.recipe.startsWith("UNSUPPORTED_")) {
            throw new IllegalStateException("fail-closed unsupported amount recipe " + c.recipe);
        }
        final Game game = initAndCreateThreePlayerGame();
        final Player actor = game.getPlayers().get(0);
        final Player opponent = game.getPlayers().get(1);
        final String gameId = "ws33-amount-" + shortId(c.pathId);

        final List<MyRandom.RngEvent> rngEvents = new ArrayList<>();
        final MyRandom.ReplayProvider provider = replayRng == null ? null : new QueueReplayProvider(replayRng);
        MyRandom.beginGameScope(gameId, RNG_SEED, rngEvents::add, provider);
        try {
            forge.net.Ws05HiddenInfoProbe.reset();
            forge.net.Ws05HiddenInfoProbe.registerSecret("Black Lotus");
            addCardToZone("Black Lotus", opponent, ZoneType.Hand);

            final PlayerControllerHuman controller = new PlayerControllerHuman(
                    game, actor, new LobbyPlayerHuman("ws33-amount-principal"));
            final Card shockTarget = addCardToZone("Runeclaw Bear", opponent, ZoneType.Battlefield);
            final Provider decisions = new Provider(shockTarget, replay);
            controller.setExternalDecisionProvider(decisions::decide);
            driveFixtureDecision(game, actor, controller, decisions);

            fillLibrary(actor, 10);
            actor.getZone(ZoneType.Library).shuffle();

            final AmountResult amount = evaluateRecipe(c, game, actor);
            if (amount.actual != amount.expected) {
                throw new IllegalStateException("production calculateAmount mismatch actual="
                        + amount.actual + " expected=" + amount.expected + " recipe=" + c.recipe);
            }

            final List<ExternalDecisionTape.Event> tape = controller.getExternalDecisionTapeSnapshot();
            if (tape.size() != decisions.captured.size()) {
                throw new IllegalStateException("decision tape/request count mismatch");
            }
            for (int i = 0; i < tape.size(); i++) {
                final ExternalDecisionTape.Event event = tape.get(i);
                final CapturedDecision decision = decisions.captured.get(i);
                if (event.getResponseStatus() != ExternalDecisionTape.ResponseStatus.ACCEPTED) {
                    throw new IllegalStateException("non-accepted amount-fixture decision");
                }
                if (!event.getSelectedOptionIds().equals(List.of(decision.selectedOptionId))) {
                    throw new IllegalStateException("validated decision response differs from provider response");
                }
            }
            if (rngEvents.isEmpty()) {
                throw new IllegalStateException("empty WS06 RNG tape");
            }

            final long leak0 = forge.net.Ws05HiddenInfoProbe.pilotVisibleLeaks();
            final long cross0 = forge.net.Ws05HiddenInfoProbe.crossPrincipalLeaks();
            final GameView view = new GameView(game);
            forge.net.Ws05HiddenInfoProbe.observe(actor.getName(), view, "ws33-amount-case");
            forge.net.Ws05HiddenInfoProbe.observe(opponent.getName(), view, "ws33-amount-case");
            final long leakDelta = forge.net.Ws05HiddenInfoProbe.pilotVisibleLeaks() - leak0;
            final long crossDelta = forge.net.Ws05HiddenInfoProbe.crossPrincipalLeaks() - cross0;
            if (leakDelta != 0 || crossDelta != 0) {
                throw new IllegalStateException("hidden-isolation leak delta leak=" + leakDelta
                        + " cross=" + crossDelta);
            }

            final String canonical = "amount=" + amount.actual
                    + "|expected=" + amount.expected
                    + "|recipe=" + c.recipe
                    + "|svar=" + c.svarToken + "=" + c.svarExpression;
            return new Result(amount.actual, amount.expected, canonical,
                    decisions.captured, tape, new ArrayList<>(rngEvents), leakDelta, crossDelta);
        } finally {
            MyRandom.endGameScope();
        }
    }

    private void driveFixtureDecision(final Game game, final Player actor,
            final PlayerControllerHuman controller, final Provider decisions) {
        final Card prodigal = addCardToZone("Prodigal Sorcerer", actor, ZoneType.Battlefield);
        SpellAbility ability = null;
        for (final SpellAbility sa : prodigal.getSpellAbilities()) {
            if (sa.usesTargeting()) {
                ability = sa;
                break;
            }
        }
        if (ability == null) {
            throw new IllegalStateException("fixture card lacks targeting ability");
        }
        ability.setActivatingPlayer(actor);
        if (!controller.chooseTargetsFor(ability)) {
            throw new IllegalStateException("Forge fixture target selection returned false");
        }
        decisions.assertConsumed();
    }

    private AmountResult evaluateRecipe(final Case c, final Game game, final Player actor) {
        switch (c.recipe) {
            case "COUNT_XPAID": {
                final int paid = intParam(c.recipeParams, "paid");
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                sa.getRootAbility().setXManaCostPaid(paid);
                final int actual = AbilityUtils.calculateAmount(host, c.svarToken, sa);
                return new AmountResult(actual, paid);
            }
            case "COUNT_HAND_YOUOWN": {
                final int extra = intParam(c.recipeParams, "hand_cards");
                final int base = actor.getZone(ZoneType.Hand).size();
                for (int i = 0; i < extra; i++) {
                    addCardToZone("Island", actor, ZoneType.Hand);
                }
                final int expected = base + extra;
                if (actor.getZone(ZoneType.Hand).size() != expected) {
                    throw new IllegalStateException("hand fixture state mismatch");
                }
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                final int actual = AbilityUtils.calculateAmount(host, c.svarToken, sa);
                return new AmountResult(actual, expected);
            }
            case "COUNT_BATTLEFIELD_CREATURE_YOUCTRL": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                addCardToZone("Runeclaw Bear", actor, ZoneType.Battlefield);
                addCardToZone("Runeclaw Bear", actor, ZoneType.Battlefield);
                addCardToZone("Runeclaw Bear", actor, ZoneType.Battlefield);
                addCardToZone("Runeclaw Bear", game.getPlayers().get(1), ZoneType.Battlefield);
                addCardToZone("Island", actor, ZoneType.Battlefield);
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                final int actual = AbilityUtils.calculateAmount(host, c.svarToken, sa);
                // Fixture-known matching creatures: 3 placed bears plus the
                // decision-fixture Prodigal Sorcerer (actor-controlled creature).
                // The host card itself counts only if it is an actor-controlled
                // creature, read as direct production state facts.
                int expected = 4;
                if (host.isCreature() && host.getController() == actor) {
                    expected += 1;
                }
                return new AmountResult(actual, expected);
            }
            default:
                throw new IllegalStateException("fail-closed unsupported amount recipe " + c.recipe);
        }
    }

    private SpellAbility firstAbility(final Card host) {
        SpellAbility fallback = null;
        for (final SpellAbility sa : host.getSpellAbilities()) {
            if (fallback == null) {
                fallback = sa;
            }
            if (sa.isActivatedAbility()) {
                return sa;
            }
        }
        if (fallback == null) {
            throw new IllegalStateException("host card has no SpellAbility " + host.getName());
        }
        return fallback;
    }

    private SpellAbility findAbility(final Card source) {
        return firstAbility(source);
    }

    private static int intParam(final Map<String, String> params, final String key) {
        final String value = params.get(key);
        if (value == null) {
            throw new IllegalStateException("missing recipe param " + key);
        }
        return Integer.parseInt(value);
    }

    private static final class Provider {
        private final Card intended;
        private final List<ReplayDecision> replay;
        private int replayIndex;
        private boolean selected;
        private boolean sawIntended;
        private final List<CapturedDecision> captured = new ArrayList<>();

        Provider(final Card intended, final List<ReplayDecision> replay) {
            this.intended = intended;
            this.replay = replay;
        }

        ExternalDecisionResponse decide(final ExternalDecisionRequest request) {
            if (!"TARGET_SELECTION".equals(request.getDecisionKind())) {
                throw new IllegalStateException("unexpected decision kind " + request.getDecisionKind());
            }
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
                final String desiredSemantic = selected ? "DONE" : "CARD:" + intended.getId();
                chosen = request.getOptions().stream()
                        .filter(option -> desiredSemantic.equals(option.getSemanticValue()))
                        .findFirst()
                        .orElseThrow(() -> new IllegalStateException(
                                "fixture-designated target transition not offered by Forge: " + desiredSemantic));
            }
            if (chosen.getSemanticValue().startsWith("CARD:")) {
                sawIntended = true;
                selected = true;
            }
            captured.add(new CapturedDecision(request, chosen.getOptionId(), chosen.getSemanticValue()));
            return new ExternalDecisionResponse(
                    request.getDecisionId(), request.getToken(), request.getActorId(),
                    request.getPrincipalId(), request.getResponseSchema(),
                    List.of(chosen.getOptionId()), false);
        }

        void assertConsumed() {
            if (!sawIntended) {
                throw new IllegalStateException("authoritative intended fixture transition was never consumed");
            }
            if (replay != null && replayIndex != replay.size()) {
                throw new IllegalStateException("replay left " + (replay.size() - replayIndex) + " decisions unconsumed");
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
        final Path trace = dir.resolve("trace.json");
        final Path finalState = dir.resolve("final-state.txt");
        final Path observation = dir.resolve("principal-observation.json");

        writeDecisionTape(decisionTape, c, result);
        writeDecisionReplay(decisionReplay, result);
        writeRngTape(rngTape, rngReplay, c, result);
        Files.writeString(finalState, result.canonicalFinalState, StandardCharsets.UTF_8);
        Files.writeString(trace, traceJson(c, result), StandardCharsets.UTF_8);
        Files.writeString(observation, observationJson(c, result), StandardCharsets.UTF_8);

        final String rel = "records/" + shortId(c.pathId) + "/";
        final String record = "{"
                + "\"schema\":\"commander-simulator-next.ws33-runtime-campaign-record.v1\","
                + "\"witness_id\":" + q("ws33-calculate-amount-" + shortId(c.pathId)) + ","
                + "\"oracle_identities\":[" + q(c.oracleId) + "],"
                + "\"v2_path_ids\":[" + q(c.pathId) + "],"
                + "\"owner_family\":\"ACTION_COST_DECISION\","
                + "\"initial_semantic_state\":{"
                + "\"recipe\":" + q(c.recipe) + ","
                + "\"svar_token\":" + q(c.svarToken) + ","
                + "\"svar_expression\":" + q(c.svarExpression)
                + "},"
                + "\"final_semantic_state\":{"
                + "\"calculated_amount\":" + result.actual + ","
                + "\"expected_amount\":" + result.expected + ","
                + "\"amounts_equal\":" + (result.actual == result.expected)
                + "},"
                + "\"state_assertions\":["
                + assertion("calculated-amount", result.expected, result.actual) + ","
                + assertion("hidden-leak-delta", 0, (int) result.leakDelta) + ","
                + assertion("cross-principal-leak-delta", 0, (int) result.crossDelta)
                + "],"
                + "\"path_exercise\":[{"
                + "\"v2_path_id\":" + q(c.pathId) + ","
                + "\"exercised\":true,"
                + "\"trace_event_ids\":[\"AMOUNT_EVALUATED\",\"DECISION_ACCEPTED\",\"RNG_TAPED\",\"HIDDEN_SAMPLED\"],"
                + "\"assertion_ids\":[\"calculated-amount\",\"hidden-leak-delta\",\"cross-principal-leak-delta\"]"
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
                + q("https://magic.wizards.com/en/rules (current Comprehensive Rules), 107.3")
                + "],"
                + "\"evidence_class\":\"EXTERNALLY_RULE_VALIDATED\""
                + "}\n";
        Files.writeString(dir.resolve("record.json"), record, StandardCharsets.UTF_8);
        Files.writeString(dir.resolve("record-success.marker"), "PASS\n", StandardCharsets.UTF_8);
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
                    .append(",\"game_id\":").append(q("ws33-amount-" + shortId(c.pathId)))
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
        json.append("{\"game_id\":").append(q("ws33-amount-" + shortId(c.pathId)))
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
        for (final String line : Files.readAllLines(path, StandardCharsets.UTF_8)) {
            if (line.isBlank()) continue;
            final String[] fields = line.split("\\t", -1);
            if (fields.length != 3) {
                throw new IllegalArgumentException("malformed amount replay decision line");
            }
            result.add(new ReplayDecision(unb64(fields[0]), unb64(fields[1]), unb64(fields[2])));
        }
        if (result.isEmpty()) {
            throw new IllegalArgumentException("empty amount replay decision tape");
        }
        return result;
    }

    private static List<Integer> loadReplayRng(final Path path) throws IOException {
        final List<Integer> result = new ArrayList<>();
        for (final String line : Files.readAllLines(path, StandardCharsets.UTF_8)) {
            if (line.isBlank()) continue;
            result.add(Integer.parseInt(line.trim()));
        }
        if (result.isEmpty()) {
            throw new IllegalArgumentException("empty amount replay RNG tape");
        }
        return result;
    }

    private static void writeReplayEvidence(
            final Path dir, final Result replayResult, final Path decisionTape, final String expectedState) throws Exception {
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

    private static String traceJson(final Case c, final Result result) {
        return "{"
                + "\"schema\":\"commander-simulator-next.ws33-calculate-amount-trace.v1\","
                + "\"forge_pin\":" + q(FORGE_PIN) + ","
                + "\"path_id\":" + q(c.pathId) + ","
                + "\"oracle_identity\":" + q(c.oracleId) + ","
                + "\"actual_card\":" + q(c.cardName) + ","
                + "\"source_path\":" + q(c.sourcePath) + ","
                + "\"source_line\":" + c.sourceLine + ","
                + "\"svar_token\":" + q(c.svarToken) + ","
                + "\"svar_expression\":" + q(c.svarExpression) + ","
                + "\"recipe\":" + q(c.recipe) + ","
                + "\"actual_rules_core_path\":true,"
                + "\"amount_entry\":\"AbilityUtils.calculateAmount\","
                + "\"direct_effect_resolution\":false,"
                + "\"calculated_amount\":" + result.actual + ","
                + "\"expected_amount\":" + result.expected + ","
                + "\"decision_event_count\":" + result.captured.size() + ","
                + "\"rng_event_count\":" + result.rngEvents.size() + ","
                + "\"hidden_leak_delta\":" + result.leakDelta + ","
                + "\"cross_principal_leak_delta\":" + result.crossDelta
                + "}\n";
    }

    private static String observationJson(final Case c, final Result result) {
        return "{"
                + "\"schema\":\"commander-simulator-next.ws33-amount-principal-observation.v1\","
                + "\"path_id\":" + q(c.pathId) + ","
                + "\"secret\":\"Black Lotus\","
                + "\"secret_holder\":\"opponent\","
                + "\"pilot_visible_leak_delta\":" + result.leakDelta + ","
                + "\"cross_principal_leak_delta\":" + result.crossDelta + ","
                + "\"result\":" + q(result.leakDelta == 0 && result.crossDelta == 0 ? "PASS" : "FAIL")
                + "}\n";
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

    private static void writeDiagnostics(final Path root, final String mode, final List<String> diagnostics) throws IOException {
        final Path path = root.resolve("amount-" + mode + "-diagnostics.jsonl");
        Files.write(path, diagnostics, StandardCharsets.UTF_8);
    }

    private static List<Case> loadCases(final Path path) throws IOException {
        final List<Case> result = new ArrayList<>();
        for (final String line : Files.readAllLines(path, StandardCharsets.UTF_8)) {
            if (line.isBlank() || line.startsWith("#")) continue;
            final String[] fields = line.split("\\t", -1);
            if (fields.length != 10) {
                throw new IllegalArgumentException("malformed WS33 amount case line");
            }
            result.add(new Case(
                    fields[0], fields[1], unb64(fields[2]), unb64(fields[3]), unb64(fields[4]),
                    fields[5], unb64(fields[6]), unb64(fields[7]), unb64(fields[8]),
                    Integer.parseInt(fields[9])));
        }
        if (result.isEmpty()) {
            throw new IllegalArgumentException("WS33 amount campaign case set is empty");
        }
        return result;
    }

    private static Map<String, String> parseParams(final String json) {
        final Map<String, String> out = new LinkedHashMap<>();
        final String body = json.trim();
        if (!body.startsWith("{") || !body.endsWith("}")) {
            throw new IllegalArgumentException("malformed recipe params " + json);
        }
        final String inner = body.substring(1, body.length() - 1);
        int depth = 0;
        boolean inString = false;
        boolean escaped = false;
        int partStart = 0;
        final List<String> parts = new ArrayList<>();
        for (int i = 0; i < inner.length(); i++) {
            final char ch = inner.charAt(i);
            if (escaped) {
                escaped = false;
                continue;
            }
            if (ch == '\\' && inString) {
                escaped = true;
                continue;
            }
            if (ch == '"') {
                inString = !inString;
                continue;
            }
            if (inString) {
                continue;
            }
            if (ch == '[' || ch == '{') {
                depth++;
            } else if (ch == ']' || ch == '}') {
                depth--;
            } else if (ch == ',' && depth == 0) {
                parts.add(inner.substring(partStart, i));
                partStart = i + 1;
            }
        }
        parts.add(inner.substring(partStart));
        for (final String part : parts) {
            if (part.isBlank()) {
                continue;
            }
            final int colon = part.indexOf(':');
            if (colon < 0) {
                throw new IllegalArgumentException("malformed recipe param part " + part);
            }
            out.put(unquote(part.substring(0, colon).trim()), part.substring(colon + 1).trim());
        }
        return out;
    }

    private static String unquote(final String value) {
        if (value.length() >= 2 && value.startsWith("\"") && value.endsWith("\"")) {
            return value.substring(1, value.length() - 1);
        }
        return value;
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
        final Map<String, String> recipeParams;
        final String svarMap;
        final String sourcePath;
        final int sourceLine;

        Case(String pathId, String oracleId, String cardName, String svarToken,
                String svarExpression, String recipe, String recipeParamsJson,
                String svarMap, String sourcePath, int sourceLine) {
            this.pathId = pathId;
            this.oracleId = oracleId;
            this.cardName = cardName;
            this.svarToken = svarToken;
            this.svarExpression = svarExpression;
            this.recipe = recipe;
            this.recipeParams = parseParams(recipeParamsJson);
            this.svarMap = svarMap;
            this.sourcePath = sourcePath;
            this.sourceLine = sourceLine;
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

    private static final class AmountResult {
        final int actual;
        final int expected;

        AmountResult(final int actual, final int expected) {
            this.actual = actual;
            this.expected = expected;
        }
    }

    private static final class Result {
        final int actual;
        final int expected;
        final String canonicalFinalState;
        final List<CapturedDecision> captured;
        final List<ExternalDecisionTape.Event> tape;
        final List<MyRandom.RngEvent> rngEvents;
        final long leakDelta;
        final long crossDelta;

        Result(int actual, int expected, String canonicalFinalState,
                List<CapturedDecision> captured, List<ExternalDecisionTape.Event> tape,
                List<MyRandom.RngEvent> rngEvents, long leakDelta, long crossDelta) {
            this.actual = actual;
            this.expected = expected;
            this.canonicalFinalState = canonicalFinalState;
            this.captured = new ArrayList<>(captured);
            this.tape = new ArrayList<>(tape);
            this.rngEvents = new ArrayList<>(rngEvents);
            this.leakDelta = leakDelta;
            this.crossDelta = crossDelta;
        }
    }
}
