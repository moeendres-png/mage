package forge.gamesimulationtests;

import forge.ai.AITest;
import forge.game.Game;
import forge.game.card.Card;
import forge.game.phase.PhaseType;
import forge.game.player.Player;
import forge.game.spellability.AbilitySub;
import forge.game.spellability.SpellAbility;
import forge.game.zone.ZoneType;
import org.testng.Assert;
import org.testng.annotations.Test;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Base64;
import java.util.List;

/**
 * WS33-C qualification-only AbilitySub production-parent campaign.
 *
 * Each case drives a real game event (e.g. triggered ability entering the
 * stack from an actual card) through the production stack resolution path,
 * which calls {@code AbilityUtils.resolve(parent)} and from there the
 * production-linked {@code AbilitySub} child. An observation-only hook on
 * {@code AbilitySub.resolve} (inert unless armed here) records the exact
 * child reached plus its production parent chain. No effect is directly
 * constructed or resolved; a directly constructed child (parent == null)
 * can never satisfy the child-reach assertion.
 */
public final class Ws33AbilitySubCampaignTest extends AITest {
    private static final String FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928";

    @Test
    public void abilitySubProductionParentCampaign() throws Exception {
        final Path casesPath = requiredPath("ws33.subCases");
        final Path out = requiredPath("ws33.subOut");
        Files.createDirectories(out);
        final List<Case> cases = loadCases(casesPath);
        final List<String> diagnostics = new ArrayList<>();
        int success = 0;
        for (final Case c : cases) {
            try {
                final Result result = executeCase(c);
                writeRecord(out, c, result);
                success++;
            } catch (Throwable error) {
                diagnostics.add("{\"path_id\":\"" + escape(c.pathId)
                        + "\",\"error_type\":\"" + escape(error.getClass().getName())
                        + "\",\"message\":\"" + escape(String.valueOf(error.getMessage())) + "\"}");
            }
        }
        Files.write(out.resolve("abilitysub-record-diagnostics.jsonl"),
                diagnostics, StandardCharsets.UTF_8);
        Assert.assertEquals(diagnostics.size(), 0,
                "AbilitySub campaign diagnostics must be empty: " + diagnostics);
        Assert.assertTrue(success > 0, "AbilitySub campaign produced no successful cases");
        System.out.println("WS33_ABILITYSUB_CAMPAIGN_SUCCESS=" + success);
    }

    @Test
    public void directChildWithoutProductionParentIsRejected() {
        // Fail-closed gate: a directly constructed AbilitySub has no
        // production parent (getParent() == null) and therefore must be
        // rejected by the child-reach adjudication used in executeCase.
        final Observed direct = new Observed("Draw", "Cloudblazer", null, null, 0);
        Assert.assertFalse(isProductionChildReach(direct, "GainLife", "Draw", "Cloudblazer"),
                "direct child without production parent must be rejected");
        final Observed ok = new Observed("Draw", "Cloudblazer", "GainLife", "Cloudblazer", 1);
        Assert.assertTrue(isProductionChildReach(ok, "GainLife", "Draw", "Cloudblazer"),
                "production-linked child must be accepted");
    }

    private Result executeCase(final Case c) {
        final Game game = initAndCreateGame();
        final Player actor = game.getPlayers().get(0);
        game.getPhaseHandler().devModeSet(PhaseType.MAIN1, actor);
        fillLibrary(actor, 10);

        final Card source = addCardToZone(c.cardName, actor, ZoneType.Hand);
        final int lifeBefore = actor.getLife();
        final int handBefore = actor.getCardsIn(ZoneType.Hand).size();

        final List<Observed> observed = new ArrayList<>();
        final int[] seq = {0};
        AbilitySub.setWs33ResolutionObserver(sa -> {
            final SpellAbility parent = sa.getParent();
            observed.add(new Observed(
                    sa.getApi() == null ? null : sa.getApi().name(),
                    sa.getHostCard() == null ? null : sa.getHostCard().getName(),
                    parent == null || parent.getApi() == null ? null : parent.getApi().name(),
                    parent == null || parent.getHostCard() == null
                            ? null : parent.getHostCard().getName(),
                    seq[0]++));
        });
        try {
            game.getAction().moveTo(ZoneType.Battlefield, source, null, null);
            if (!game.getTriggerHandler().runWaitingTriggers()
                    || !game.getStack().addAllTriggeredAbilitiesToStack()
                    || game.getStack().isEmpty()) {
                throw new IllegalStateException(
                        "actual trigger fixture did not reach the stack");
            }
            playUntilStackClear(game);
        } finally {
            AbilitySub.setWs33ResolutionObserver(null);
        }

        if (!game.getStack().isEmpty()) {
            throw new IllegalStateException("stack did not clear after production resolution");
        }
        final List<Observed> matches = new ArrayList<>();
        for (final Observed o : observed) {
            if (isProductionChildReach(o, c.parentApi, c.childApi, c.cardName)) {
                matches.add(o);
            }
        }
        if (matches.isEmpty()) {
            throw new IllegalStateException(
                    "production-linked child not reached: expected child api=" + c.childApi
                            + " with production parent api=" + c.parentApi
                            + " on host=" + c.cardName + " observations=" + observed);
        }
        final int lifeAfter = actor.getLife();
        final int handAfter = actor.getCardsIn(ZoneType.Hand).size();
        if (lifeAfter - lifeBefore != c.lifeDelta) {
            throw new IllegalStateException("semantic postcondition life mismatch expected="
                    + c.lifeDelta + " actual=" + (lifeAfter - lifeBefore));
        }
        if (handAfter - handBefore != c.handDeltaNet) {
            throw new IllegalStateException("semantic postcondition hand mismatch expected="
                    + c.handDeltaNet + " actual=" + (handAfter - handBefore));
        }
        return new Result(lifeBefore, handBefore, lifeAfter, handAfter, observed, matches);
    }

    static boolean isProductionChildReach(
            final Observed o, final String parentApi, final String childApi, final String host) {
        if (o.childApi == null || o.parentApi == null || o.parentHost == null) {
            return false;
        }
        return o.childApi.equals(childApi)
                && o.parentApi.equals(parentApi)
                && host.equals(o.childHost)
                && host.equals(o.parentHost);
    }

    private static void writeRecord(final Path root, final Case c, final Result r) throws IOException {
        final Path dir = root.resolve("records").resolve(shortId(c.pathId));
        Files.createDirectories(dir);
        final StringBuilder obs = new StringBuilder("[");
        for (int i = 0; i < r.observed.size(); i++) {
            if (i != 0) obs.append(',');
            final Observed o = r.observed.get(i);
            obs.append("{\"seq\":").append(o.seq)
                    .append(",\"child_api\":").append(q(o.childApi))
                    .append(",\"child_host\":").append(q(o.childHost))
                    .append(",\"parent_api\":").append(q(o.parentApi))
                    .append(",\"parent_host\":").append(q(o.parentHost)).append('}');
        }
        obs.append(']');
        final String trace = "{"
                + "\"schema\":\"commander-simulator-next.ws33-abilitysub-trace.v1\","
                + "\"forge_pin\":" + q(FORGE_PIN) + ","
                + "\"path_id\":" + q(c.pathId) + ","
                + "\"oracle_identity\":" + q(c.oracleId) + ","
                + "\"actual_card\":" + q(c.cardName) + ","
                + "\"source_path\":" + q(c.sourcePath) + ","
                + "\"source_line\":" + c.sourceLine + ","
                + "\"parent_svar\":" + q(c.parentSvar) + ","
                + "\"child_sub\":" + q(c.childSub) + ","
                + "\"production_entrypoint\":\"forge.game.ability.AbilityUtils.resolve\","
                + "\"production_stack_path\":\"trigger->MagicStack->AbilityUtils.resolve->AbilitySub.resolve\","
                + "\"direct_effect_resolution\":false,"
                + "\"child_observations\":" + obs + ","
                + "\"initial\":{\"life\":" + r.lifeBefore + ",\"hand_size\":" + r.handBefore + "},"
                + "\"final\":{\"life\":" + r.lifeAfter + ",\"hand_size\":" + r.handAfter + "},"
                + "\"trace_event_ids\":[\"TRIGGER_STACKED\",\"PARENT_RESOLVED\",\"CHILD_OBSERVED\",\"STACK_CLEARED\"]"
                + "}\n";
        Files.writeString(dir.resolve("trace.json"), trace, StandardCharsets.UTF_8);
        final String record = "{"
                + "\"schema\":\"commander-simulator-next.ws33-runtime-campaign-record.v1\","
                + "\"witness_id\":" + q("ws33-abilitysub-" + shortId(c.pathId)) + ","
                + "\"oracle_identities\":[" + q(c.oracleId) + "],"
                + "\"v2_path_ids\":[" + q(c.pathId) + "],"
                + "\"owner_family\":\"ACTION_COST_DECISION\","
                + "\"initial_semantic_state\":{\"life\":" + r.lifeBefore
                + ",\"hand_size\":" + r.handBefore + "},"
                + "\"final_semantic_state\":{\"life\":" + r.lifeAfter
                + ",\"hand_size\":" + r.handAfter
                + ",\"life_delta\":" + (r.lifeAfter - r.lifeBefore)
                + ",\"hand_delta_net\":" + (r.handAfter - r.handBefore) + "},"
                + "\"state_assertions\":["
                + assertion("life-delta", c.lifeDelta, r.lifeAfter - r.lifeBefore) + ","
                + assertion("hand-delta-net", c.handDeltaNet, r.handAfter - r.handBefore) + ","
                + assertion("production-child-reached", true, !r.matches.isEmpty())
                + "],"
                + "\"path_exercise\":[{"
                + "\"v2_path_id\":" + q(c.pathId) + ","
                + "\"exercised\":true,"
                + "\"trace_event_ids\":[\"PARENT_RESOLVED\",\"CHILD_OBSERVED\"],"
                + "\"assertion_ids\":[\"life-delta\",\"hand-delta-net\",\"production-child-reached\"]"
                + "}],"
                + "\"execution\":{"
                + "\"actual_card_execution\":\"PASS\","
                + "\"actual_rules_core_path\":true,"
                + "\"authoritative_decision_boundary\":\"NOT_REQUIRED\","
                + "\"silent_fallbacks\":0,"
                + "\"direct_effect_resolution\":false},"
                + "\"trace_file\":" + q("records/" + shortId(c.pathId) + "/trace.json") + ","
                + "\"rules_authority_refs\":["
                + q("https://magic.wizards.com/en/rules (current Comprehensive Rules), 603.3")
                + "," + q("https://magic.wizards.com/en/rules (current Comprehensive Rules), 608.2")
                + "],"
                + "\"evidence_class\":\"TECHNICALLY_CONFORMANT\""
                + "}\n";
        Files.writeString(dir.resolve("record.json"), record, StandardCharsets.UTF_8);
        Files.writeString(dir.resolve("record-success.marker"), "PASS\n", StandardCharsets.UTF_8);
    }

    private static List<Case> loadCases(final Path path) throws IOException {
        final List<Case> result = new ArrayList<>();
        for (final String line : Files.readAllLines(path, StandardCharsets.UTF_8)) {
            if (line.isBlank() || line.startsWith("#")) continue;
            final String[] f = line.split("\t", -1);
            if (f.length != 12) {
                throw new IllegalArgumentException("malformed WS33 AbilitySub case line");
            }
            result.add(new Case(f[0], f[1], unb64(f[2]), f[3], f[4], f[5], f[6],
                    unb64(f[7]), Integer.parseInt(f[8]), f[9],
                    Integer.parseInt(f[10]), Integer.parseInt(f[11])));
        }
        if (result.isEmpty()) {
            throw new IllegalArgumentException("WS33 AbilitySub case set is empty");
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

    private static String assertion(final String id, final int expected, final int actual) {
        return "{\"assertion_id\":" + q(id) + ",\"expected\":" + expected
                + ",\"actual\":" + actual + ",\"result\":\"PASS\"}";
    }

    private static String assertion(final String id, final boolean expected, final boolean actual) {
        return "{\"assertion_id\":" + q(id) + ",\"expected\":" + expected
                + ",\"actual\":" + actual + ",\"result\":\"PASS\"}";
    }

    private static String shortId(final String pathId) {
        return pathId.startsWith("forge-behavior-v2:")
                ? pathId.substring("forge-behavior-v2:".length())
                : pathId.replaceAll("[^A-Za-z0-9_.-]", "-");
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
        return new String(Base64.getDecoder().decode(value), StandardCharsets.UTF_8);
    }

    private static final class Case {
        final String pathId;
        final String oracleId;
        final String cardName;
        final String parentSvar;
        final String childSub;
        final String parentApi;
        final String childApi;
        final String sourcePath;
        final int sourceLine;
        final String fixtureKind;
        final int lifeDelta;
        final int handDeltaNet;

        Case(String pathId, String oracleId, String cardName, String parentSvar,
                String childSub, String parentApi, String childApi, String sourcePath,
                int sourceLine, String fixtureKind, int lifeDelta, int handDeltaNet) {
            this.pathId = pathId;
            this.oracleId = oracleId;
            this.cardName = cardName;
            this.parentSvar = parentSvar;
            this.childSub = childSub;
            this.parentApi = parentApi;
            this.childApi = childApi;
            this.sourcePath = sourcePath;
            this.sourceLine = sourceLine;
            this.fixtureKind = fixtureKind;
            this.lifeDelta = lifeDelta;
            this.handDeltaNet = handDeltaNet;
        }
    }

    private static final class Observed {
        final String childApi;
        final String childHost;
        final String parentApi;
        final String parentHost;
        final int seq;

        Observed(String childApi, String childHost, String parentApi, String parentHost, int seq) {
            this.childApi = childApi;
            this.childHost = childHost;
            this.parentApi = parentApi;
            this.parentHost = parentHost;
            this.seq = seq;
        }

        @Override
        public String toString() {
            return "Observed{child=" + childApi + "@" + childHost
                    + " parent=" + parentApi + "@" + parentHost + " seq=" + seq + "}";
        }
    }

    private static final class Result {
        final int lifeBefore;
        final int handBefore;
        final int lifeAfter;
        final int handAfter;
        final List<Observed> observed;
        final List<Observed> matches;

        Result(int lifeBefore, int handBefore, int lifeAfter, int handAfter,
                List<Observed> observed, List<Observed> matches) {
            this.lifeBefore = lifeBefore;
            this.handBefore = handBefore;
            this.lifeAfter = lifeAfter;
            this.handAfter = handAfter;
            this.observed = new ArrayList<>(observed);
            this.matches = new ArrayList<>(matches);
        }
    }
}
