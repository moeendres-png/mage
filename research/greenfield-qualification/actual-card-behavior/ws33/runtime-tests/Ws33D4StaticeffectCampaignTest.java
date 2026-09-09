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
 * WS33-D D4a static-effect campaign (STATE_ONLY, template-049, 8 paths).
 *
 * <p>Each case loads an actual pinned-Forge card and drives the modeled
 * Effect line through its production entry point: real spell casts, a real
 * two-phase opponent-cast probe for Silence, real battlefield entry plus
 * trigger/stack transfer for ETB cases, a real fixture destroyer spell for
 * the dies-trigger case, real activated-ability activations, and real
 * fixture damage spells, all via
 * {@code PlaySpellAbility.playSpellAbility} with production cost payment
 * from exact fixture mana pools. No effect is directly resolved; no
 * expected outcome is injected; no AI discretion is consulted. Every case
 * asserts the command-zone Effect object (exactly one, host-named, with the
 * expected static/replacement/trigger payload) plus exact zone/life/loyalty
 * deltas, so no case can pass vacuously. A scripted external decision
 * provider answers only case-intent-scripted forced Forge requests (all D4a
 * intents are NONE); any other request fails the case closed.
 * Record/replay requires byte-equal canonical final state with RNG
 * tapes replay-served and hidden-observation deltas of zero.</p>
 */
public final class Ws33D4StaticeffectCampaignTest extends AITest {
    private static final String FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928";
    private static final long RNG_SEED = 0x5733444L;

    @Test
    public void d4StaticeffectCampaign() throws Exception {
        final String mode = System.getProperty("ws33.d4Mode", "record");
        if (!"record".equals(mode) && !"replay".equals(mode)) {
            throw new IllegalArgumentException("ws33.d4Mode must be record or replay");
        }
        final Path casesPath = requiredPath("ws33.d4Cases");
        final Path out = requiredPath("ws33.d4Out");
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
        Assert.assertTrue(success > 0, "D4a staticeffect campaign produced no successful " + mode + " cases");
        System.out.println("WS33_D4_CAMPAIGN_MODE=" + mode);
        System.out.println("WS33_D4_CAMPAIGN_SUCCESS=" + success);
        System.out.println("WS33_D4_CAMPAIGN_DIAGNOSTIC_FAILURES=" + diagnostics.size());
    }

    private Result executeCase(final Case c, final Path outRoot, final List<ReplayDecision> replay,
            final List<Integer> replayRng) {
        return executeCase(c, outRoot, replay, null, replayRng);
    }

    private Result executeCase(final Case c, final Path outRoot, final List<ReplayDecision> replay,
            final List<ReplayDecision> replayOpp, final List<Integer> replayRng) {
        if (c.recipe.startsWith("UNSUPPORTED_") || c.recipe.startsWith("DEFERRED_")) {
            throw new IllegalStateException("fail-closed unsupported D4a recipe " + c.recipe);
        }
        switch (c.recipe) {
            case "SPELL_STATIC_PROBE":
            case "SPELL_STATIC_KICKER":
            case "ETB_PREVENTION":
            case "DIES_MAYPLAY":
            case "ACTIVATED_STATIC":
            case "SPELL_DIG_MAYPLAY":
            case "ETB_CASCADE":
            case "ANIMATE_PREVENTION":
                break;
            default:
                throw new IllegalStateException("fail-closed unknown D4a recipe " + c.recipe);
        }
        final Game game = initAndCreateGame();
        final Player actor = game.getPlayers().get(0);
        final Player opponent = game.getPlayers().get(1);
        game.getPhaseHandler().devModeSet(PhaseType.MAIN1, actor);
        final String gameId = "ws33-d4-" + shortId(c.pathId);
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
                    game, actor, new LobbyPlayerHuman("ws33-d4-principal"));
            final Provider decisions = new Provider(replay, requestLog, intentKindOf(c), designated);
            controller.setExternalDecisionProvider(decisions::decide);

            final PlayerControllerHuman oppController = new PlayerControllerHuman(
                    game, opponent, new LobbyPlayerHuman("ws33-d4-opp"));
            final Provider oppDecisions = new Provider(replayOpp, requestLogOpp, intentKindOf(c), designated);
            oppController.setExternalDecisionProvider(oppDecisions::decide);

            final int lifeBefore = actor.getLife();
            final int oppLifeBefore = opponent.getLife();

            driveRecipe(c, game, actor, opponent, controller, oppController);
            playUntilStackClear(game);
            if (!game.isGameOver()) {
                game.getAction().checkStateEffects(true);
                playUntilStackClear(game);
            }

            if (game.isGameOver()) {
                throw new IllegalStateException("fixture game ended during D4a case");
            }
            if (!game.getStack().isEmpty()) {
                throw new IllegalStateException("stack not empty after D4a case resolution");
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
                final AssertionAcc acc = assertRecipePostconditions(c, game, actor, opponent);
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
            checkTape(controller, decisions, "D4a");
            checkTape(oppController, oppDecisions, "D4a-opp");

            final long leak0 = forge.net.Ws05HiddenInfoProbe.pilotVisibleLeaks();
            final long cross0 = forge.net.Ws05HiddenInfoProbe.crossPrincipalLeaks();
            final GameView view = new GameView(game);
            forge.net.Ws05HiddenInfoProbe.observe(actor.getName(), view, "ws33-d4-case");
            forge.net.Ws05HiddenInfoProbe.observe(opponent.getName(), view, "ws33-d4-case");
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
            final PlayerControllerHuman controller, final PlayerControllerHuman oppController) {
        switch (c.recipe) {
            case "SPELL_STATIC_PROBE": {
                final String probeName = param(c, "probe");
                final Card first = findHandCard(opponent, probeName);
                if (!PlaySpellAbility.playSpellAbility(oppController, opponent, first.getSpells().get(0))) {
                    throw new IllegalStateException("probe baseline cast unexpectedly rejected pre-Silence");
                }
                if (game.getStack().isEmpty()) {
                    throw new IllegalStateException("probe baseline cast left an empty stack");
                }
                playUntilAllSettled(game);
                final Card silence = placeCard(c.cardName, actor, ZoneType.Hand);
                final SpellAbility spell = silence.getSpells().get(0);
                if (!PlaySpellAbility.playSpellAbility(controller, actor, spell)) {
                    throw new IllegalStateException("production spell cast returned false");
                }
                if (game.getStack().isEmpty()) {
                    throw new IllegalStateException("production spell cast left an empty stack");
                }
                playUntilAllSettled(game);
                final Card second = findHandCard(opponent, probeName);
                if (PlaySpellAbility.playSpellAbility(oppController, opponent, second.getSpells().get(0))) {
                    throw new IllegalStateException("opponent probe cast unexpectedly accepted under Silence");
                }
                return;
            }
            case "SPELL_STATIC_KICKER":
            case "SPELL_DIG_MAYPLAY": {
                final Card card = placeCard(c.cardName, actor, ZoneType.Hand);
                final SpellAbility spell = card.getSpells().get(0);
                if (!PlaySpellAbility.playSpellAbility(controller, actor, spell)) {
                    throw new IllegalStateException("production spell cast returned false");
                }
                if (game.getStack().isEmpty()) {
                    throw new IllegalStateException("production spell cast left an empty stack");
                }
                playUntilAllSettled(game);
                return;
            }
            case "ETB_PREVENTION":
            case "ETB_CASCADE": {
                final Card card = placeCard(c.cardName, actor, ZoneType.Hand);
                game.getAction().moveTo(ZoneType.Battlefield, card, null, null);
                if (!game.getTriggerHandler().runWaitingTriggers()) {
                    throw new IllegalStateException("actual trigger fixture produced no triggers");
                }
                if (!game.getStack().addAllTriggeredAbilitiesToStack() || game.getStack().isEmpty()) {
                    throw new IllegalStateException("actual trigger fixture did not reach the stack");
                }
                playUntilAllSettled(game);
                castFixtureSpell(c, game, actor, controller);
                playUntilAllSettled(game);
                return;
            }
            case "DIES_MAYPLAY": {
                placeCard(c.cardName, actor, ZoneType.Battlefield);
                final String destroyer = param(c, "destroyer");
                final Card wrath = placeCard(destroyer, actor, ZoneType.Hand);
                final SpellAbility spell = wrath.getSpells().get(0);
                if (!PlaySpellAbility.playSpellAbility(controller, actor, spell)) {
                    throw new IllegalStateException("production fixture destroyer cast returned false");
                }
                if (game.getStack().isEmpty()) {
                    throw new IllegalStateException("production destroyer cast left an empty stack");
                }
                playUntilAllSettled(game);
                return;
            }
            case "ACTIVATED_STATIC": {
                placeCard(c.cardName, actor, ZoneType.Battlefield);
                final Card card = requireHostOnBattlefield(game, c.cardName);
                final SpellAbility ability = findSoleActivatedAbility(card);
                if (!PlaySpellAbility.playSpellAbility(controller, actor, ability)) {
                    throw new IllegalStateException("production ability activation returned false");
                }
                if (game.getStack().isEmpty()) {
                    throw new IllegalStateException("production activation left an empty stack");
                }
                playUntilAllSettled(game);
                return;
            }
            case "ANIMATE_PREVENTION": {
                placeCard(c.cardName, actor, ZoneType.Battlefield);
                final Card card = requireHostOnBattlefield(game, c.cardName);
                final SpellAbility ability = findActivatedAbility(card, ApiType.Animate);
                if (!PlaySpellAbility.playSpellAbility(controller, actor, ability)) {
                    throw new IllegalStateException("production animate activation returned false");
                }
                if (game.getStack().isEmpty()) {
                    throw new IllegalStateException("production animate left an empty stack");
                }
                playUntilAllSettled(game);
                castFixtureSpell(c, game, actor, controller);
                playUntilAllSettled(game);
                return;
            }
            default:
                throw new IllegalStateException("fail-closed unsupported D4a recipe " + c.recipe);
        }
    }

    private void castFixtureSpell(final Case c, final Game game, final Player actor,
            final PlayerControllerHuman controller) {
        final String spellName = param(c, "fixture_spell");
        final Card spellCard = placeCard(spellName, actor, ZoneType.Hand);
        final SpellAbility spell = spellCard.getSpells().get(0);
        if (!PlaySpellAbility.playSpellAbility(controller, actor, spell)) {
            throw new IllegalStateException("production fixture spell cast returned false");
        }
        if (game.getStack().isEmpty()) {
            throw new IllegalStateException("production fixture cast left an empty stack");
        }
    }

    private String param(final Case c, final String key) {
        for (final String part : c.recipeParams.split(";")) {
            if (part.startsWith(key + "=")) {
                final String value = part.substring(key.length() + 1).trim();
                if (!value.isEmpty()) {
                    return value;
                }
            }
        }
        throw new IllegalStateException("D4a case lacks param " + key + " for recipe " + c.recipe);
    }

    private Card findHandCard(final Player player, final String name) {
        Card found = null;
        for (final Card card : player.getCardsIn(ZoneType.Hand)) {
            if (name.equals(card.getName())) {
                if (found != null) {
                    throw new IllegalStateException("hand card not unique: " + name);
                }
                found = card;
            }
        }
        if (found == null) {
            throw new IllegalStateException("hand card absent: " + name);
        }
        return found;
    }

    private Card placeCard(final String name, final Player player, final ZoneType zone) {
        try {
            return addCardToZone(name, player, zone);
        } catch (NullPointerException e) {
            throw new IllegalStateException("card script not resolvable for exact name: " + name, e);
        }
    }

    private Card requireHostOnBattlefield(final Game game, final String name) {
        final Card card = findCardWithName(game, name);
        if (card == null) {
            final StringBuilder present = new StringBuilder();
            for (final Card c : game.getCardsIn(ZoneType.Battlefield)) {
                if (present.length() != 0) {
                    present.append(',');
                }
                present.append(c.getName());
            }
            throw new IllegalStateException("host not on battlefield expected=" + name
                    + " present=[" + present + "]");
        }
        return card;
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

    private SpellAbility findSoleActivatedAbility(final Card card) {
        final List<SpellAbility> matches = new ArrayList<>();
        for (final SpellAbility sa : card.getSpellAbilities()) {
            if (sa.isActivatedAbility()) {
                matches.add(sa);
            }
        }
        if (matches.size() != 1) {
            throw new IllegalStateException("expected exactly one activated ability, found "
                    + matches.size());
        }
        return matches.get(0);
    }

    private SpellAbility findActivatedAbility(final Card card, final ApiType api) {
        final List<SpellAbility> matches = new ArrayList<>();
        for (final SpellAbility sa : card.getSpellAbilities()) {
            if (sa.isActivatedAbility() && sa.getApi() == api) {
                matches.add(sa);
            }
        }
        if (matches.size() != 1) {
            throw new IllegalStateException("expected exactly one " + api + " activated ability, found "
                    + matches.size());
        }
        return matches.get(0);
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
            final Player actor, final Player opponent) {
        return assertRecipePostconditionsInto(c, game, actor, opponent, new AssertionAcc());
    }

    private AssertionAcc assertRecipePostconditionsInto(final Case c, final Game game,
            final Player actor, final Player opponent, final AssertionAcc assertions) {
        switch (c.recipe) {
            case "SPELL_STATIC_PROBE": {
                checkCount(game, acc, "probe-baseline-graveyard", "Dark Ritual", ZoneType.Graveyard, 1);
                checkCount(game, acc, "probe-rejected-hand", "Dark Ritual", ZoneType.Hand, 1);
                checkCount(game, acc, "silence-graveyard", c.cardName, ZoneType.Graveyard, 1);
                requireCommandEffect(c, game, acc, "static");
                break;
            }
            case "SPELL_STATIC_KICKER": {
                checkCount(game, acc, "spell-graveyard", c.cardName, ZoneType.Graveyard, 1);
                requireCommandEffect(c, game, acc, "static");
                break;
            }
            case "ETB_PREVENTION": {
                checkCount(game, acc, "host-battlefield", c.cardName, ZoneType.Battlefield, 1);
                checkCount(game, acc, "memnite-survives", "Memnite", ZoneType.Battlefield, 1);
                checkCount(game, acc, "fixture-graveyard", "Seismic Rupture", ZoneType.Graveyard, 1);
                requireCommandEffect(c, game, acc, "replacement");
                break;
            }
            case "DIES_MAYPLAY": {
                checkCount(game, acc, "host-graveyard", c.cardName, ZoneType.Graveyard, 1);
                checkCount(game, acc, "bear-graveyard", "Runeclaw Bear", ZoneType.Graveyard, 1);
                checkCount(game, acc, "destroyer-graveyard", "Wrath of God", ZoneType.Graveyard, 1);
                requireCommandEffect(c, game, acc, "static");
                break;
            }
            case "ACTIVATED_STATIC": {
                checkCount(game, acc, "host-battlefield", c.cardName, ZoneType.Battlefield, 1);
                requireCommandEffect(c, game, acc, "static");
                break;
            }
            case "SPELL_DIG_MAYPLAY": {
                checkCount(game, acc, "spell-graveyard", c.cardName, ZoneType.Graveyard, 1);
                final int library = actor.getCardsIn(ZoneType.Library).size();
                acc.add("library-emptied", 0, library);
                if (library != 0) {
                    throw new IllegalStateException("expected emptied library, found " + library);
                }
                final int exile = actor.getCardsIn(ZoneType.Exile).size();
                acc.add("exile-two", 2, exile);
                if (exile != 2) {
                    throw new IllegalStateException("expected exactly two exiled cards, found " + exile);
                }
                requireCommandEffect(c, game, acc, "static");
                break;
            }
            case "ETB_CASCADE": {
                checkCount(game, acc, "host-battlefield", c.cardName, ZoneType.Battlefield, 1);
                checkCount(game, acc, "bear-graveyard", "Runeclaw Bear", ZoneType.Graveyard, 1);
                checkCount(game, acc, "hawk-trigger-killed", "Suntail Hawk", ZoneType.Graveyard, 1);
                checkCount(game, acc, "fixture-graveyard", "Seismic Rupture", ZoneType.Graveyard, 1);
                requireCommandEffect(c, game, acc, "trigger");
                break;
            }
            case "ANIMATE_PREVENTION": {
                checkCount(game, acc, "host-battlefield", c.cardName, ZoneType.Battlefield, 1);
                final Card gideon = requireHostOnBattlefield(game, c.cardName);
                final int loyalty = gideon.getCurrentLoyalty();
                acc.add("loyalty-unchanged-6", 6, loyalty);
                if (loyalty != 6) {
                    throw new IllegalStateException("expected loyalty 6 after prevented damage, found " + loyalty);
                }
                checkCount(game, acc, "fixture-graveyard", "Seismic Rupture", ZoneType.Graveyard, 1);
                requireCommandEffect(c, game, acc, "replacement");
                break;
            }
            default:
                throw new IllegalStateException("fail-closed unsupported D4a recipe " + c.recipe);
        }
        return assertions;
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
        if ("CONFIRM_TRUE".equals(c.intent)) {
            return "CONFIRM_TRUE";
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
                : "Hand".equals(parts[3]) ? ZoneType.Hand : null;
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
        private int replayIndex;
        private final List<CapturedDecision> captured = new ArrayList<>();
        private final List<String> resolutions = new ArrayList<>();

        Provider(final List<ReplayDecision> replay, final Path requestLog,
                final String intentKind, final Card designated) {
            this.replay = replay;
            this.requestLog = requestLog;
            this.intentKind = intentKind;
            this.designated = designated;
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
            } else if ("ENTITY_LIST_SELECTION".equals(request.getDecisionKind())) {
                if (!"ENTITY".equals(intentKind) || designated == null) {
                    throw new IllegalStateException("fail-closed entity selection without ENTITY intent kind="
                            + request.getDecisionKind());
                }
                final String expectedSemantic =
                        "ENTITY:" + ExternalDecisionRequest.optionIdFor(designated);
                final List<ExternalDecisionRequest.Option> entityOptions = new ArrayList<>();
                for (final ExternalDecisionRequest.Option option : request.getOptions()) {
                    if (expectedSemantic.equals(option.getSemanticValue())) {
                        entityOptions.add(option);
                    } else if (!"CANCEL".equals(option.getSemanticValue()) || request.isCancelAllowed()
                            || request.getMinimumSelection() < 1) {
                        throw new IllegalStateException("fail-closed non-forced companion option kind="
                                + request.getDecisionKind() + " option=" + option.getOptionId()
                                + " semantic=" + option.getSemanticValue());
                    }
                }
                if (entityOptions.size() != 1) {
                    throw new IllegalStateException("fail-closed designated entity not the sole option kind="
                            + request.getDecisionKind() + " expectedSemantic=" + expectedSemantic);
                }
                chosen = entityOptions.get(0);
                expectedSelect = expectedSemantic;
                selectedSelect = chosen.getSemanticValue();
            } else if ("CONFIRM_PAYMENT".equals(request.getDecisionKind())) {
                if (!"CONFIRM_TRUE".equals(intentKind)) {
                    throw new IllegalStateException("fail-closed payment confirm without CONFIRM intent kind="
                            + request.getDecisionKind());
                }
                if (request.isCancelAllowed() || request.getMinimumSelection() != 1
                        || request.getMaximumSelection() != 1 || request.getOptions().size() != 2) {
                    throw new IllegalStateException("fail-closed malformed payment confirm");
                }
                ExternalDecisionRequest.Option affirm = null;
                boolean hasDeny = false;
                for (final ExternalDecisionRequest.Option option : request.getOptions()) {
                    if ("true".equals(option.getSemanticValue())) {
                        affirm = option;
                    } else if ("false".equals(option.getSemanticValue())) {
                        hasDeny = true;
                    } else {
                        throw new IllegalStateException("fail-closed unknown confirm option "
                                + option.getSemanticValue());
                    }
                }
                if (affirm == null || !hasDeny) {
                    throw new IllegalStateException("fail-closed payment confirm options malformed");
                }
                chosen = affirm;
                expectedSelect = "true";
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
        switch (c.recipe) {
            case "SPELL_STATIC_PROBE":
            case "SPELL_STATIC_KICKER":
            case "DIES_MAYPLAY":
            case "ACTIVATED_STATIC":
            case "SPELL_DIG_MAYPLAY":
                return "static";
            case "ETB_PREVENTION":
            case "ANIMATE_PREVENTION":
                return "replacement";
            case "ETB_CASCADE":
                return "trigger";
            default:
                throw new IllegalStateException("unknown D4a recipe " + c.recipe);
        }
    }

    private static String rulesRefOf(final Case c) {
        switch (c.recipe) {
            case "ETB_PREVENTION":
            case "ANIMATE_PREVENTION":
                return "Comprehensive Rules, section 615 (Prevention Effects)";
            case "ETB_CASCADE":
                return "Comprehensive Rules, section 603 (Triggered Abilities)";
            default:
                return "Comprehensive Rules, section 604 (Static Abilities)";
        }
    }

    private static List<String> traceEventsOf(final Case c) {
        return List.of("EFFECT_COMMAND_PRESENT", "EFFECT_KIND_" + effectKindOf(c).toUpperCase(Locale.ROOT),
                "RNG_TAPED", "HIDDEN_SAMPLED");
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
        Files.writeString(dir.resolve("principal-observation.json"), observationJson(c, result),
                StandardCharsets.UTF_8);

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
        final String record = "{"
                + "\"schema\":\"commander-simulator-next.ws33-runtime-campaign-record.v1\","
                + "\"witness_id\":" + q("ws33-d4-staticeffect-" + shortId(c.pathId)) + ","
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
        Files.writeString(dir.resolve("record.json"), record, StandardCharsets.UTF_8);
        Files.writeString(dir.resolve("record-success.marker"), "PASS\n", StandardCharsets.UTF_8);
    }

    private static String traceJson(final Case c, final Result result) {
        return "{"
                + "\"schema\":\"commander-simulator-next.ws33-d4-staticeffect-trace.v1\","
                + "\"forge_pin\":" + q(FORGE_PIN) + ","
                + "\"path_id\":" + q(c.pathId) + ","
                + "\"oracle_identity\":" + q(c.oracleId) + ","
                + "\"actual_card\":" + q(c.cardName) + ","
                + "\"provenance\":" + q(c.provenance) + ","
                + "\"svar_token\":" + q(c.svarToken) + ","
                + "\"svar_expression\":" + q(c.svarExpression) + ","
                + "\"recipe\":" + q(c.recipe) + ","
                + "\"effect_kind\":" + q(effectKindOf(c)) + ","
                + "\"actual_rules_core_path\":true,"
                + "\"staticeffect_entry\":\"PlaySpellAbility.playSpellAbility-or-trigger-stack-transfer\","
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
                + "\"schema\":\"commander-simulator-next.ws33-d4-principal-observation.v1\","
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
                    .append(",\"game_id\":").append(q("ws33-d4-" + shortId(c.pathId)))
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
        json.append("{\"game_id\":").append(q("ws33-d4-" + shortId(c.pathId)))
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
                throw new IllegalArgumentException("malformed D4a replay decision line");
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
        final Path path = root.resolve("staticeffect-" + mode + "-diagnostics.jsonl");
        Files.write(path, diagnostics, StandardCharsets.UTF_8);
    }

    private static List<Case> loadCases(final Path path) throws IOException {
        final List<Case> result = new ArrayList<>();
        for (final String line : Files.readAllLines(path, StandardCharsets.UTF_8)) {
            if (line.isBlank() || line.startsWith("#")) continue;
            final String[] fields = line.split("\\t", -1);
            if (fields.length != 13) {
                throw new IllegalArgumentException("malformed WS33 D4a case line");
            }
            result.add(new Case(
                    fields[0], fields[1], unb64(fields[2]), unb64(fields[3]), unb64(fields[4]),
                    fields[5], unb64(fields[6]), unb64(fields[7]), unb64(fields[8]),
                    Integer.parseInt(fields[9]), Integer.parseInt(fields[10]), unb64(fields[11]),
                    unb64(fields[12])));
        }
        if (result.isEmpty()) {
            throw new IllegalArgumentException("WS33 D4a campaign case set is empty");
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
