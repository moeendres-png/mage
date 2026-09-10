package forge.gamesimulationtests;

import forge.ai.AITest;
import forge.card.mana.ManaAtom;
import forge.game.Game;
import forge.game.GameView;
import forge.game.card.Card;
import forge.game.card.CounterType;
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
 * WS33-D D4c single-target campaign (STATE_ONLY template-049, 4 T1 paths).
 *
 * <p>Each case drives one actual pinned-Forge sorcery/instant with exactly
 * one mandatory target through its production entry point: a real production
 * cast from hand via {@code PlaySpellAbility.playSpellAbility} with exact
 * engine-paid mana, a single engine-authoritative TARGET_SELECTION answered
 * only by unique match to the case-designated ENTITY intent (zero or
 * multiple authoritative matches fail closed; any other decision kind fails
 * closed), an engine-owned pre-resolution designated-target gate
 * ({@code SpellAbility.isTargeting}, recursive over subabilities, so
 * subability-level targets such as Heroic Return's are covered), full
 * production resolution, and a command-zone Effect presence assertion with
 * the expected static/trigger/replacement payload plus exact zone/counter
 * deltas. No effect is directly resolved; no expected outcome is injected;
 * no AI discretion is consulted. Record/replay requires byte-equal canonical
 * final state with RNG tapes replay-served and hidden-observation deltas of
 * zero.</p>
 */
public final class Ws33D4cTargetCampaignTest extends AITest {
    private static final String FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928";
    private static final long RNG_SEED = 0x57334463L;

    @Test
    public void d4cTargetCampaign() throws Exception {
        final String mode = System.getProperty("ws33.d4cMode", "record");
        if (!"record".equals(mode) && !"replay".equals(mode)) {
            throw new IllegalArgumentException("ws33.d4cMode must be record or replay");
        }
        final Path casesPath = requiredPath("ws33.d4cCases");
        final Path out = requiredPath("ws33.d4cOut");
        Files.createDirectories(out);
        final List<Case> cases = loadCases(casesPath);
        final List<String> diagnostics = new ArrayList<>();
        final List<String> admittedRecords = new ArrayList<>();
        int success = 0;

        for (final Case c : cases) {
            try {
                if ("record".equals(mode)) {
                    final Result result = executeCase(c, out, null, null);
                    writeRecord(out, c, result);
                    success++;
                } else {
                    final Path dir = caseDir(out, c.pathId);
                    if (!Files.isRegularFile(dir.resolve("record-success.marker"))) {
                        executeCase(c, out, null, null);
                        throw new IllegalStateException(
                                "record-rejected case unexpectedly succeeded during replay alignment");
                    }
                    final List<ReplayDecision> replay = loadReplayDecisions(dir.resolve("decision-replay.tsv"));
                    final List<ReplayDecision> replayOpp = loadReplayDecisions(dir.resolve("decision-replay-opp.tsv"));
                    final List<Integer> replayRng = loadReplayRng(dir.resolve("rng-replay.tsv"));
                    final Result result = executeCase(c, out, replay, replayOpp, replayRng);
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
        Assert.assertTrue(success > 0, "D4c target campaign produced no successful " + mode + " cases");
        System.out.println("WS33_D4C_CAMPAIGN_MODE=" + mode);
        System.out.println("WS33_D4C_CAMPAIGN_SUCCESS=" + success);
        System.out.println("WS33_D4C_CAMPAIGN_DIAGNOSTIC_FAILURES=" + diagnostics.size());
    }

    private Result executeCase(final Case c, final Path outRoot, final List<ReplayDecision> replay,
            final List<Integer> replayRng) {
        return executeCase(c, outRoot, replay, null, replayRng);
    }

    private Result executeCase(final Case c, final Path outRoot, final List<ReplayDecision> replay,
            final List<ReplayDecision> replayOpp, final List<Integer> replayRng) {
        switch (c.recipe) {
            case "TARGET_SINGLE_GRAVE_SPELL":
            case "TARGET_SINGLE_GRAVE_CREATURE_RETURN":
            case "TARGET_SINGLE_GRAVE_CREATURE_RETURN_COUNTER":
            case "TARGET_SINGLE_BATTLEFIELD_DAMAGE":
                break;
            default:
                throw new IllegalStateException("fail-closed unknown D4c recipe " + c.recipe);
        }
        final Game game = initAndCreateGame();
        final Player actor = game.getPlayers().get(0);
        final Player opponent = game.getPlayers().get(1);
        game.getPhaseHandler().devModeSet(PhaseType.MAIN1, actor);
        final String gameId = "ws33-d4c-" + shortId(c.pathId);
        final Path requestLog = caseDir(outRoot, c.pathId).resolve("decision-requests.jsonl");
        final Path requestLogOpp = caseDir(outRoot, c.pathId).resolve("decision-requests-opp.jsonl");

        final List<MyRandom.RngEvent> rngEvents = new ArrayList<>();
        final MyRandom.ReplayProvider rngProvider = replayRng == null ? null : new QueueReplayProvider(replayRng);
        MyRandom.beginGameScope(gameId, RNG_SEED, rngEvents::add, rngProvider);
        try {
            forge.net.Ws05HiddenInfoProbe.reset();
            forge.net.Ws05HiddenInfoProbe.registerSecret("Black Lotus");
            addCardToZone("Black Lotus", opponent, ZoneType.Hand);

            buildFixture(c, game, actor, opponent);

            final Card designated = resolveDesignation(c, game, actor, opponent);

            final PlayerControllerHuman controller = new PlayerControllerHuman(
                    game, actor, new LobbyPlayerHuman("ws33-d4c-principal"));
            // Registered-controller attachment (Forge pin: AITest wires
            // LobbyPlayerAi, so the game's registered controllers are AI and
            // PlaySpellAbility/setupTargets consult p.getController(), NOT a
            // separately constructed object). The provider-wired Human
            // controller must BE the registered one, exactly as a human-lobby
            // game assigns it (LobbyPlayerHuman.createIngamePlayer +
            // setFirstController); dangerouslySetController performs the same
            // field assignment minus the already-assigned guard. Without
            // this, targeting is answered invisibly by the AI controller and
            // the provider sees zero requests (run 34426307199 FAIL).
            actor.dangerouslySetController(controller);
            final Provider decisions = new Provider(replay, requestLog, intentKindOf(c), designated, true);
            controller.setExternalDecisionProvider(decisions::decide);

            final PlayerControllerHuman oppController = new PlayerControllerHuman(
                    game, opponent, new LobbyPlayerHuman("ws33-d4c-opp"));
            opponent.dangerouslySetController(oppController);
            final Provider oppDecisions = new Provider(replayOpp, requestLogOpp, "NONE", null, false);
            oppController.setExternalDecisionProvider(oppDecisions::decide);

            final int lifeBefore = actor.getLife();
            final int oppLifeBefore = opponent.getLife();

            driveRecipe(c, game, actor, opponent, controller, designated);
            playUntilStackClear(game);
            if (!game.isGameOver()) {
                game.getAction().checkStateEffects(true);
                playUntilStackClear(game);
            }

            if (game.isGameOver()) {
                throw new IllegalStateException("fixture game ended during D4c case");
            }
            if (!game.getStack().isEmpty()) {
                throw new IllegalStateException("stack not empty after D4c case resolution");
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
            final List<String> effectAssertions;
            final List<String> effectAssertionIds;
            try {
                long targetSelections = 0;
                for (final CapturedDecision captured : decisions.captured) {
                    if ("TARGET_SELECTION".equals(captured.request.getDecisionKind())) {
                        targetSelections++;
                    }
                }
                if (!oppDecisions.captured.isEmpty()) {
                    throw new IllegalStateException("opponent principal issued unexpected decisions");
                }
                final AssertionAcc acc = assertRecipePostconditions(c, game, actor, opponent, targetSelections);
                effectAssertions = acc.json;
                effectAssertionIds = acc.ids;
            } catch (IllegalStateException e) {
                throw new IllegalStateException(e.getMessage()
                        + " finalZones={" + canonicalFinalState(game, actor, opponent).replace('\n', ';') + "}", e);
            }
            decisions.assertConsumed();
            oppDecisions.assertConsumed();

            final List<CapturedDecision> allCaptured = new ArrayList<>(decisions.captured);
            allCaptured.addAll(oppDecisions.captured);
            final List<String> allResolutions = new ArrayList<>(decisions.resolutions);
            allResolutions.addAll(oppDecisions.resolutions);
            checkTape(controller, decisions, "D4c");
            checkTape(oppController, oppDecisions, "D4c-opp");

            final long leak0 = forge.net.Ws05HiddenInfoProbe.pilotVisibleLeaks();
            final long cross0 = forge.net.Ws05HiddenInfoProbe.crossPrincipalLeaks();
            final GameView view = new GameView(game);
            forge.net.Ws05HiddenInfoProbe.observe(actor.getName(), view, "ws33-d4c-case");
            forge.net.Ws05HiddenInfoProbe.observe(opponent.getName(), view, "ws33-d4c-case");
            final long leakDelta = forge.net.Ws05HiddenInfoProbe.pilotVisibleLeaks() - leak0;
            final long crossDelta = forge.net.Ws05HiddenInfoProbe.crossPrincipalLeaks() - cross0;
            if (leakDelta != 0 || crossDelta != 0) {
                throw new IllegalStateException("hidden-isolation leak delta leak=" + leakDelta
                        + " cross=" + crossDelta);
            }

            final String canonical = canonicalFinalState(game, actor, opponent);
            final List<ExternalDecisionTape.Event> tape =
                    new ArrayList<>(controller.getExternalDecisionTapeSnapshot());
            tape.addAll(oppController.getExternalDecisionTapeSnapshot());
            return new Result(actorDelta, oppDelta, canonical,
                    allCaptured, tape, new ArrayList<>(rngEvents), leakDelta, crossDelta,
                    allResolutions, effectAssertions, effectAssertionIds, decisions.captured.size());
        } finally {
            MyRandom.endGameScope();
        }
    }

    private void checkTape(final PlayerControllerHuman controller, final Provider decisions,
            final String tag) {
        final List<ExternalDecisionTape.Event> tape = controller.getExternalDecisionTapeSnapshot();
        if (tape.size() != decisions.captured.size()) {
            throw new IllegalStateException(tag + " decision tape/request count mismatch");
        }
        for (int i = 0; i < tape.size(); i++) {
            final ExternalDecisionTape.Event event = tape.get(i);
            final CapturedDecision decision = decisions.captured.get(i);
            if (event.getResponseStatus() != ExternalDecisionTape.ResponseStatus.ACCEPTED) {
                throw new IllegalStateException(tag + " non-accepted decision");
            }
            if (!event.getSelectedOptionIds().equals(List.of(decision.selectedOptionId))) {
                throw new IllegalStateException(tag + " validated decision response differs from provider response");
            }
        }
    }

    private void buildFixture(final Case c, final Game game, final Player actor, final Player opponent) {
        addPoolMana(c.poolSpec, actor, c.cardName);
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
        if (fixture.containsKey("actor_gy")) {
            for (final String spec : fixture.get("actor_gy").split(",")) {
                final String[] parts = spec.split(":");
                final int count = Integer.parseInt(parts[1]);
                for (int i = 0; i < count; i++) {
                    addCardToZone(parts[0].trim(), actor, ZoneType.Graveyard);
                }
            }
        }
        if (fixture.containsKey("opp_gy")) {
            for (final String spec : fixture.get("opp_gy").split(",")) {
                final String[] parts = spec.split(":");
                final int count = Integer.parseInt(parts[1]);
                for (int i = 0; i < count; i++) {
                    addCardToZone(parts[0].trim(), opponent, ZoneType.Graveyard);
                }
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
        if (fixture.containsKey("opp_hand")) {
            for (final String spec : fixture.get("opp_hand").split(",")) {
                final String[] parts = spec.split(":");
                for (int i = 0; i < Integer.parseInt(parts[1]); i++) {
                    addCardToZone(parts[0].trim(), opponent, ZoneType.Hand);
                }
            }
        }
        if (fixture.containsKey("opp_pool")) {
            addPoolMana(fixture.get("opp_pool"), opponent, c.cardName);
        }
    }

    private void addPoolMana(final String spec, final Player player, final String sourceCard) {
        if (spec == null || spec.isBlank()) {
            return;
        }
        final Card source = createCard(sourceCard, player);
        final java.util.regex.Matcher m =
                java.util.regex.Pattern.compile("([A-Z])([0-9]+)").matcher(spec);
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
                player.getManaPool().addMana(new Mana(color, source, null, player));
            }
        }
        if (!found) {
            throw new IllegalStateException("malformed mana pool spec " + spec);
        }
    }

    private void driveRecipe(final Case c, final Game game, final Player actor, final Player opponent,
            final PlayerControllerHuman controller, final Card designated) {
        switch (c.recipe) {
            case "TARGET_SINGLE_GRAVE_SPELL":
            case "TARGET_SINGLE_GRAVE_CREATURE_RETURN":
            case "TARGET_SINGLE_GRAVE_CREATURE_RETURN_COUNTER":
            case "TARGET_SINGLE_BATTLEFIELD_DAMAGE": {
                // Production entry: the spell is CAST from hand; engine-owned
                // mana payment and cast-time target selection apply. The
                // TARGET_SELECTION itself is answered by the case provider
                // (unique authoritative match to the designated entity).
                final Card spellCard = placeCard(c.cardName, actor, ZoneType.Hand);
                final SpellAbility spell = spellCard.getSpells().get(0);
                if (!PlaySpellAbility.playSpellAbility(controller, actor, spell)) {
                    throw new IllegalStateException("production spell cast returned false");
                }
                if (game.getStack().isEmpty()) {
                    throw new IllegalStateException("production spell cast left an empty stack");
                }
                // Engine-owned designated-target gate, pre-resolution: the
                // spell (root or any subability, isTargeting recurses) must
                // target the exact designated Card object. This binds the
                // provider's unique-match selection to engine state before
                // resolution can move the target.
                if (designated == null || !spell.isTargeting(designated)) {
                    throw new IllegalStateException("engine did not retain designated authoritative target")
                    ;
                }
                playUntilAllSettled(game);
                return;
            }
            default:
                throw new IllegalStateException("fail-closed unsupported D4c recipe " + c.recipe);
        }
    }

    private Card placeCard(final String name, final Player player, final ZoneType zone) {
        try {
            return addCardToZone(name, player, zone);
        } catch (NullPointerException e) {
            throw new IllegalStateException("card script not resolvable for exact name: " + name, e);
        }
    }

    private void playUntilAllSettled(final Game game) {
        for (int round = 0; round < 25; round++) {
            playUntilStackClear(game);
            if (game.isGameOver()) {
                return;
            }
            final boolean waiting = game.getTriggerHandler().runWaitingTriggers();
            final boolean stacked = game.getStack().addAllTriggeredAbilitiesToStack();
            if (game.getStack().isEmpty()) {
                return;
            }
            if (!waiting && !stacked) {
                throw new IllegalStateException("stack non-empty with no trigger progress");
            }
        }
        throw new IllegalStateException("stack did not settle within round cap");
    }

    private Card requireCommandEffect(final Case c, final Game game, final AssertionAcc acc,
            final String kind) {
        final List<Card> effects = new ArrayList<>();
        for (final Card card : game.getCardsIn(ZoneType.Command)) {
            if (card.getName().contains(c.cardName)) {
                effects.add(card);
            }
        }
        acc.add("effect-command-present", 1, effects.size());
        if (effects.size() != 1) {
            throw new IllegalStateException("expected exactly one command-zone Effect for host="
                    + c.cardName + " found=" + effects.size());
        }
        final Card effect = effects.get(0);
        final int kindCount;
        switch (kind) {
            case "static":
                kindCount = effect.getStaticAbilities().size();
                break;
            case "replacement":
                kindCount = effect.getReplacementEffects().size();
                break;
            case "trigger":
                kindCount = effect.getTriggers().size();
                break;
            default:
                throw new IllegalStateException("unknown effect kind " + kind);
        }
        acc.add("effect-kind-" + kind + "-present", 1, kindCount > 0 ? 1 : 0);
        if (kindCount == 0) {
            throw new IllegalStateException("command-zone Effect lacks expected " + kind + " payload");
        }
        return effect;
    }

    private static final class AssertionAcc {
        final List<String> json = new ArrayList<>();
        final List<String> ids = new ArrayList<>();

        void add(final String id, final int expected, final int actual) {
            json.add(assertion(id, expected, actual));
            ids.add(id);
        }
    }

    private AssertionAcc assertRecipePostconditions(final Case c, final Game game,
            final Player actor, final Player opponent, final long targetSelections) {
        final AssertionAcc acc = new AssertionAcc();
        // Measured from the authoritative decision tape: exactly one
        // TARGET_SELECTION per case. The designated binding itself is proven
        // by the pre-resolution engine gate in driveRecipe (throw on miss)
        // plus the intent_resolutions unique-match records.
        acc.add("target-designated-chosen", 1, (int) targetSelections);
        if (targetSelections != 1) {
            throw new IllegalStateException("expected exactly one TARGET_SELECTION, found " + targetSelections);
        }
        final String effectKind = effectKindOf(c);
        switch (c.recipe) {
            case "TARGET_SINGLE_GRAVE_SPELL": {
                checkCount(game, acc, "shock-exile", "Shock", ZoneType.Exile, 1);
                checkCount(game, acc, "rupture-graveyard", "Seismic Rupture", ZoneType.Graveyard, 1);
                checkCount(game, acc, "surge-graveyard", "Surge to Victory", ZoneType.Graveyard, 1);
                requireCommandEffect(c, game, acc, effectKind);
                break;
            }
            case "TARGET_SINGLE_GRAVE_CREATURE_RETURN": {
                checkCount(game, acc, "bear-battlefield", "Runeclaw Bear", ZoneType.Battlefield, 1);
                checkCount(game, acc, "memnite-graveyard", "Memnite", ZoneType.Graveyard, 1);
                checkCount(game, acc, "heroic-graveyard", "Heroic Return", ZoneType.Graveyard, 1);
                requireCommandEffect(c, game, acc, effectKind);
                break;
            }
            case "TARGET_SINGLE_GRAVE_CREATURE_RETURN_COUNTER": {
                checkCount(game, acc, "bear-battlefield", "Runeclaw Bear", ZoneType.Battlefield, 1);
                final Card bear = requireBattlefieldCard(game, "Runeclaw Bear", actor);
                final int counters = bear.getCounters(CounterType.getType("MANNEQUIN"));
                acc.add("mannequin-counter-bear", 1, counters);
                if (counters != 1) {
                    throw new IllegalStateException("expected exactly one MANNEQUIN counter on Bear, found "
                            + counters);
                }
                checkCount(game, acc, "memnite-graveyard", "Memnite", ZoneType.Graveyard, 1);
                checkCount(game, acc, "makeshift-graveyard", "Makeshift Mannequin", ZoneType.Graveyard, 1);
                requireCommandEffect(c, game, acc, effectKind);
                break;
            }
            case "TARGET_SINGLE_BATTLEFIELD_DAMAGE": {
                checkCount(game, acc, "bear-battlefield", "Runeclaw Bear", ZoneType.Battlefield, 1);
                checkCount(game, acc, "bear-graveyard", "Runeclaw Bear", ZoneType.Graveyard, 1);
                checkCount(game, acc, "bolt-graveyard", "Intimidation Bolt", ZoneType.Graveyard, 1);
                requireCommandEffect(c, game, acc, effectKind);
                break;
            }
            default:
                throw new IllegalStateException("fail-closed unsupported D4c recipe " + c.recipe);
        }
        return acc;
    }

    private Card requireBattlefieldCard(final Game game, final String name, final Player controller) {
        Card found = null;
        for (final Card card : game.getCardsIn(ZoneType.Battlefield)) {
            if (name.equals(card.getName()) && card.getController() == controller) {
                if (found != null) {
                    throw new IllegalStateException("controller-scoped battlefield card not unique: " + name);
                }
                found = card;
            }
        }
        if (found == null) {
            throw new IllegalStateException("controller-scoped battlefield card absent: " + name);
        }
        return found;
    }

    private void checkCount(final Game game, final AssertionAcc acc, final String id,
            final String name, final ZoneType zone, final int expected) {
        final int actual = countCardsWithName(game, name, zone);
        acc.add(id, expected, actual);
        if (actual != expected) {
            throw new IllegalStateException("assertion " + id + " mismatch actual=" + actual
                    + " expected=" + expected + " name=" + name + " zone=" + zone);
        }
    }

    private String canonicalFinalState(final Game game, final Player actor, final Player opponent) {
        final StringBuilder sb = new StringBuilder();
        sb.append("actor_life=").append(actor.getLife()).append('\n');
        sb.append("opp_life=").append(opponent.getLife()).append('\n');
        sb.append("pool_empty=").append(actor.getManaPool().isEmpty()).append('\n');
        sb.append("opp_pool_empty=").append(opponent.getManaPool().isEmpty()).append('\n');
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
        final Map<String, Integer> loyalty = new TreeMap<>();
        for (final Card card : game.getCardsIn(ZoneType.Battlefield)) {
            if (card.getCurrentLoyalty() > 0) {
                loyalty.put(card.getController().getName() + "|" + card.getName(),
                        card.getCurrentLoyalty());
            }
        }
        for (final Map.Entry<String, Integer> e : loyalty.entrySet()) {
            sb.append("loyalty|").append(e.getKey()).append('|').append(e.getValue()).append('\n');
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

    private static String intentKindOf(final Case c) {
        if ("NONE".equals(c.intent)) {
            return "NONE";
        }
        if (c.intent.startsWith("ENTITY:")) {
            return "ENTITY";
        }
        throw new IllegalStateException("malformed case intent " + c.intent);
    }

    private Card resolveDesignation(final Case c, final Game game, final Player actor, final Player opponent) {
        if (!"ENTITY".equals(intentKindOf(c))) {
            return null;
        }
        final String[] parts = c.intent.split(":", -1);
        if (parts.length != 4) {
            throw new IllegalStateException("malformed ENTITY intent " + c.intent);
        }
        final Player owner = "actor".equals(parts[2]) ? actor
                : "opponent".equals(parts[2]) ? opponent : null;
        if (owner == null) {
            throw new IllegalStateException("malformed ENTITY intent owner " + c.intent);
        }
        final ZoneType zone = "Battlefield".equals(parts[3]) ? ZoneType.Battlefield
                : "Hand".equals(parts[3]) ? ZoneType.Hand
                : "Graveyard".equals(parts[3]) ? ZoneType.Graveyard : null;
        if (zone == null) {
            throw new IllegalStateException("malformed ENTITY intent zone " + c.intent);
        }
        Card found = null;
        for (final Card card : owner.getCardsIn(zone)) {
            if (parts[1].equals(card.getName())) {
                if (found != null) {
                    throw new IllegalStateException("designated entity not unique " + c.intent);
                }
                found = card;
            }
        }
        if (found == null) {
            throw new IllegalStateException("designated entity absent " + c.intent);
        }
        return found;
    }

    private static final class Provider {
        private final List<ReplayDecision> replay;
        private final Path requestLog;
        private final String intentKind;
        private final Card designated;
        private final boolean expectDesignated;
        private int replayIndex;
        private boolean sawDesignated;
        private final List<CapturedDecision> captured = new ArrayList<>();
        private final List<String> resolutions = new ArrayList<>();

        Provider(final List<ReplayDecision> replay, final Path requestLog,
                final String intentKind, final Card designated, final boolean expectDesignated) {
            this.replay = replay;
            this.requestLog = requestLog;
            this.intentKind = intentKind;
            this.designated = designated;
            this.expectDesignated = expectDesignated;
        }

        ExternalDecisionResponse decide(final ExternalDecisionRequest request) {
            logRequest(request);
            final ExternalDecisionRequest.Option chosen;
            final String expectedSelect;
            final String selectedSelect;
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
                expectedSelect = expected.optionId + "|" + expected.semanticValue;
                selectedSelect = chosen.getOptionId() + "|" + chosen.getSemanticValue();
                if (expectDesignated && chosen.getSemanticValue().startsWith("CARD:")) {
                    sawDesignated = true;
                }
            } else if ("TARGET_SELECTION".equals(request.getDecisionKind())) {
                // The engine alone supplies legal target options. The harness
                // transports the externally specified discretionary selection
                // only by unique match to an already engine-authoritative
                // option. Zero or multiple matches fail closed. DONE/CANCEL
                // transitions never match the entity semantic and fail closed.
                if (!"ENTITY".equals(intentKind) || designated == null) {
                    throw new IllegalStateException("fail-closed target selection without ENTITY intent kind="
                            + request.getDecisionKind());
                }
                final String expectedSemantic = "CARD:" + designated.getId();
                final List<ExternalDecisionRequest.Option> matches = new ArrayList<>();
                for (final ExternalDecisionRequest.Option option : request.getOptions()) {
                    if (expectedSemantic.equals(option.getSemanticValue())) {
                        matches.add(option);
                    }
                }
                if (matches.size() != 1) {
                    throw new IllegalStateException("fail-closed designated target not uniquely authoritative kind="
                            + request.getDecisionKind() + " matches=" + matches.size()
                            + " expectedSemantic=" + expectedSemantic);
                }
                chosen = matches.get(0);
                sawDesignated = true;
                expectedSelect = expectedSemantic;
                selectedSelect = chosen.getSemanticValue();
            } else {
                final StringBuilder ids = new StringBuilder();
                for (final ExternalDecisionRequest.Option o : request.getOptions()) {
                    if (ids.length() != 0) ids.append(',');
                    ids.append(o.getOptionId()).append('=').append(o.getSemanticValue());
                }
                throw new IllegalStateException("fail-closed unexpected decision kind="
                        + request.getDecisionKind() + " options=" + request.getOptions().size()
                        + " ids=[" + ids + "] (see decision-requests.jsonl)");
            }
            captured.add(new CapturedDecision(request, chosen.getOptionId(), chosen.getSemanticValue()));
            resolutions.add("{\"kind\":" + q(request.getDecisionKind())
                    + ",\"expected_select\":" + q(expectedSelect)
                    + ",\"selected\":" + q(selectedSelect)
                    + ",\"match\":" + expectedSelect.equals(selectedSelect)
                    + "}");
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
            if (replay == null && expectDesignated && !sawDesignated) {
                throw new IllegalStateException("authoritative designated target was never consumed");
            }
        }

        private void logRequest(final ExternalDecisionRequest request) {
            try {
                Files.createDirectories(requestLog.getParent());
                final StringBuilder json = new StringBuilder();
                json.append("{\"decision_kind\":").append(q(request.getDecisionKind()))
                        .append(",\"option_count\":").append(request.getOptions().size())
                        .append(",\"min\":").append(request.getMinimumSelection())
                        .append(",\"max\":").append(request.getMaximumSelection())
                        .append(",\"cancel_allowed\":").append(request.isCancelAllowed())
                        .append(",\"response_schema\":").append(q(request.getResponseSchema()))
                        .append(",\"options\":[");
                for (int i = 0; i < request.getOptions().size(); i++) {
                    if (i != 0) json.append(',');
                    final ExternalDecisionRequest.Option option = request.getOptions().get(i);
                    json.append("{\"option_id\":").append(q(option.getOptionId()))
                            .append(",\"entity_kind\":").append(q(option.getEntityKind()))
                            .append(",\"entity_id\":").append(option.getEntityId())
                            .append(",\"entity_backed\":").append(option.isEntityBacked())
                            .append(",\"semantic_value\":").append(q(option.getSemanticValue()))
                            .append('}');
                }
                json.append("],\"semantic_context\":{");
                boolean first = true;
                for (final Map.Entry<String, String> e : request.getSemanticContext().entrySet()) {
                    if (!first) json.append(',');
                    first = false;
                    json.append(q(e.getKey())).append(':').append(q(e.getValue()));
                }
                json.append("}}\n");
                Files.write(requestLog, json.toString().getBytes(StandardCharsets.UTF_8),
                        java.nio.file.StandardOpenOption.CREATE,
                        java.nio.file.StandardOpenOption.APPEND);
            } catch (IOException e) {
                throw new IllegalStateException("request log write failed", e);
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

    private static String effectKindOf(final Case c) {
        final String kind = paramValue(c.recipeParams, "effect_kind");
        if (kind == null) {
            throw new IllegalStateException("D4c case lacks effect_kind param for recipe " + c.recipe);
        }
        switch (kind) {
            case "static":
            case "trigger":
            case "replacement":
                return kind;
            default:
                throw new IllegalStateException("unknown D4c effect kind " + kind);
        }
    }

    private static String paramValue(final String recipeParams, final String key) {
        if (recipeParams == null) {
            return null;
        }
        for (final String part : recipeParams.split(";")) {
            if (part.startsWith(key + "=")) {
                final String value = part.substring(key.length() + 1).trim();
                if (!value.isEmpty()) {
                    return value;
                }
            }
        }
        return null;
    }

    private static String rulesRefOf(final Case c) {
        switch (effectKindOf(c)) {
            case "static":
                return "Comprehensive Rules, sections 601 (Casting Spells, targets), 608 (Resolving Spells and Abilities), 604 (Static Abilities)";
            case "trigger":
                return "Comprehensive Rules, sections 601 (Casting Spells, targets), 608 (Resolving Spells and Abilities), 603 (Triggered Abilities)";
            case "replacement":
                return "Comprehensive Rules, sections 601 (Casting Spells, targets), 608 (Resolving Spells and Abilities), 614/616 (Replacement Effects)";
            default:
                throw new IllegalStateException("unknown D4c recipe " + c.recipe);
        }
    }

    private static List<String> traceEventsOf(final Case c) {
        return List.of("EFFECT_COMMAND_PRESENT", "EFFECT_KIND_" + effectKindOf(c).toUpperCase(Locale.ROOT),
                "TARGET_DESIGNATED_CHOSEN", "RNG_TAPED", "HIDDEN_SAMPLED");
    }

    private static void writeRecord(final Path root, final Case c, final Result result) throws IOException {
        final Path dir = caseDir(root, c.pathId);
        Files.createDirectories(dir);
        final Path decisionTape = dir.resolve("decision-tape.json");
        final Path decisionReplay = dir.resolve("decision-replay.tsv");
        final Path decisionReplayOpp = dir.resolve("decision-replay-opp.tsv");
        final Path rngTape = dir.resolve("rng-tape.json");
        final Path rngReplay = dir.resolve("rng-replay.tsv");

        writeDecisionTape(decisionTape, c, result);
        writeDecisionReplay(decisionReplay, result, true);
        writeDecisionReplay(decisionReplayOpp, result, false);
        writeRngTape(rngTape, rngReplay, c, result);
        Files.writeString(dir.resolve("final-state.txt"), result.canonicalFinalState, StandardCharsets.UTF_8);
        Files.writeString(dir.resolve("trace.json"), traceJson(c, result), StandardCharsets.UTF_8);
        Files.writeString(dir.resolve("record.json"), recordJson(c, result), StandardCharsets.UTF_8);
        Files.writeString(dir.resolve("record-success.marker"), "PASS\n", StandardCharsets.UTF_8);
        Files.writeString(dir.resolve("principal-observation.json"), observationJson(c, result),
                StandardCharsets.UTF_8);
    }

    private static String recordJson(final Case c, final Result result) {
        final StringBuilder assertions = new StringBuilder();
        assertions.append(assertion("actor-life-delta", c.expectActorDelta, result.actorDelta)).append(',')
                .append(assertion("opp-life-delta", c.expectOppDelta, result.oppDelta)).append(',')
                .append(assertion("hidden-leak-delta", 0, (int) result.leakDelta)).append(',')
                .append(assertion("cross-principal-leak-delta", 0, (int) result.crossDelta));
        final List<String> assertionIds = new ArrayList<>(List.of("actor-life-delta", "opp-life-delta",
                "hidden-leak-delta", "cross-principal-leak-delta"));
        assertionIds.addAll(result.effectAssertionIds);
        for (final String effectAssertion : result.effectAssertions) {
            assertions.append(',').append(effectAssertion);
        }
        final StringBuilder assertionIdList = new StringBuilder();
        for (int i = 0; i < assertionIds.size(); i++) {
            if (i != 0) assertionIdList.append(',');
            assertionIdList.append(q(assertionIds.get(i)));
        }
        final StringBuilder traceEvents = new StringBuilder();
        final List<String> events = traceEventsOf(c);
        for (int i = 0; i < events.size(); i++) {
            if (i != 0) traceEvents.append(',');
            traceEvents.append(q(events.get(i)));
        }

        final String rel = "records/" + shortId(c.pathId) + "/";
        return "{"
                + "\"schema\":\"commander-simulator-next.ws33-runtime-campaign-record.v1\","
                + "\"witness_id\":" + q("ws33-d4c-target-" + shortId(c.pathId)) + ","
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
                + "\"state_assertions\":[" + assertions + "],"
                + "\"path_exercise\":[{"
                + "\"v2_path_id\":" + q(c.pathId) + ","
                + "\"exercised\":true,"
                + "\"trace_event_ids\":[" + traceEvents + "],"
                + "\"assertion_ids\":[" + assertionIdList + "]"
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
                + q(rulesRefOf(c))
                + "],"
                + "\"evidence_class\":\"EXTERNALLY_RULE_VALIDATED\""
                + "}\n";
    }

    private static String traceJson(final Case c, final Result result) {
        return "{"
                + "\"schema\":\"commander-simulator-next.ws33-d4c-target-trace.v1\","
                + "\"forge_pin\":" + q(FORGE_PIN) + ","
                + "\"path_id\":" + q(c.pathId) + ","
                + "\"oracle_identity\":" + q(c.oracleId) + ","
                + "\"actual_card\":" + q(c.cardName) + ","
                + "\"provenance\":" + q(c.provenance) + ","
                + "\"svar_token\":" + q(c.svarToken) + ","
                + "\"svar_expression\":" + q(c.svarExpression) + ","
                + "\"recipe\":" + q(c.recipe) + ","
                + "\"effect_kind\":" + q(effectKindOf(c)) + ","
                + "\"target_designated_chosen\":true,"
                + "\"actual_rules_core_path\":true,"
                + "\"staticeffect_entry\":\"PlaySpellAbility.playSpellAbility-production-cast\","
                + "\"direct_effect_resolution\":false,"
                + "\"actor_life_delta\":" + result.actorDelta + ","
                + "\"expected_actor_delta\":" + c.expectActorDelta + ","
                + "\"opp_life_delta\":" + result.oppDelta + ","
                + "\"expected_opp_delta\":" + c.expectOppDelta + ","
                + "\"decision_event_count\":" + result.captured.size() + ","
                + "\"rng_event_count\":" + result.rngEvents.size() + ","
                + "\"intent_resolutions\":[" + String.join(",", result.resolutions) + "],"
                + "\"effect_assertions\":[" + String.join(",", result.effectAssertions) + "],"
                + "\"hidden_leak_delta\":" + result.leakDelta + ","
                + "\"cross_principal_leak_delta\":" + result.crossDelta
                + "}\n";
    }

    private static String observationJson(final Case c, final Result result) {
        return "{"
                + "\"schema\":\"commander-simulator-next.ws33-d4c-principal-observation.v1\","
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
                    .append(",\"game_id\":").append(q("ws33-d4c-" + shortId(c.pathId)))
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

    private static void writeDecisionReplay(final Path path, final Result result, final boolean primary)
            throws IOException {
        final StringBuilder text = new StringBuilder();
        final int from = primary ? 0 : result.primaryDecisionCount;
        final int to = primary ? result.primaryDecisionCount : result.captured.size();
        for (int i = from; i < to; i++) {
            final CapturedDecision decision = result.captured.get(i);
            text.append(b64(decision.request.getDecisionKind())).append('\t')
                    .append(b64(decision.selectedOptionId)).append('\t')
                    .append(b64(decision.semanticValue)).append('\n');
        }
        Files.writeString(path, text.toString(), StandardCharsets.UTF_8);
    }

    private static void writeRngTape(final Path tape, final Path replay, final Case c, final Result result)
            throws IOException {
        final StringBuilder json = new StringBuilder();
        json.append("{\"game_id\":").append(q("ws33-d4c-" + shortId(c.pathId)))
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
                throw new IllegalArgumentException("malformed D4c replay decision line");
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
        final Path path = root.resolve("target-" + mode + "-diagnostics.jsonl");
        Files.write(path, diagnostics, StandardCharsets.UTF_8);
    }

    private static List<Case> loadCases(final Path path) throws IOException {
        final List<Case> result = new ArrayList<>();
        for (final String line : Files.readAllLines(path, StandardCharsets.UTF_8)) {
            if (line.isBlank() || line.startsWith("#")) continue;
            final String[] fields = line.split("\\t", -1);
            if (fields.length != 13) {
                throw new IllegalArgumentException("malformed WS33 D4c case line");
            }
            result.add(new Case(
                    fields[0], fields[1], unb64(fields[2]), unb64(fields[3]), unb64(fields[4]),
                    fields[5], unb64(fields[6]), unb64(fields[7]), unb64(fields[8]),
                    Integer.parseInt(fields[9]), Integer.parseInt(fields[10]), unb64(fields[11]),
                    unb64(fields[12])));
        }
        if (result.isEmpty()) {
            throw new IllegalArgumentException("WS33 D4c campaign case set is empty");
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
        final String intent;

        Case(String pathId, String oracleId, String cardName, String svarToken,
                String svarExpression, String recipe, String recipeParams, String poolSpec,
                String fixtureKv, int expectActorDelta, int expectOppDelta, String provenance,
                String intent) {
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
            this.intent = intent;
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
        final List<String> resolutions;
        final List<String> effectAssertions;
        final List<String> effectAssertionIds;
        final int primaryDecisionCount;

        Result(int actorDelta, int oppDelta, String canonicalFinalState,
                List<CapturedDecision> captured, List<ExternalDecisionTape.Event> tape,
                List<MyRandom.RngEvent> rngEvents, long leakDelta, long crossDelta,
                List<String> resolutions, List<String> effectAssertions,
                List<String> effectAssertionIds, int primaryDecisionCount) {
            this.actorDelta = actorDelta;
            this.oppDelta = oppDelta;
            this.canonicalFinalState = canonicalFinalState;
            this.captured = new ArrayList<>(captured);
            this.tape = new ArrayList<>(tape);
            this.rngEvents = new ArrayList<>(rngEvents);
            this.leakDelta = leakDelta;
            this.crossDelta = crossDelta;
            this.resolutions = new ArrayList<>(resolutions);
            this.effectAssertions = new ArrayList<>(effectAssertions);
            this.effectAssertionIds = new ArrayList<>(effectAssertionIds);
            this.primaryDecisionCount = primaryDecisionCount;
        }
    }
}
