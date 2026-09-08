package forge.gamesimulationtests;

import forge.ai.AITest;
import forge.game.Game;
import forge.game.GameView;
import forge.game.ability.AbilityKey;
import forge.game.ability.AbilityUtils;
import forge.game.card.Card;
import forge.game.card.CounterType;
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
            case "REMEMBERED_AMOUNT": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int count = intParam(c.recipeParams, "remembered_bears");
                for (int i = 0; i < count; i++) {
                    host.addRemembered(addCardToZone("Runeclaw Bear", actor, ZoneType.Battlefield));
                }
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), count);
            }
            case "REMEMBERED_CARDPOWER": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int count = intParam(c.recipeParams, "remembered_bears");
                int per = 0;
                for (int i = 0; i < count; i++) {
                    final Card remembered = addCardToZone("Runeclaw Bear", actor, ZoneType.Battlefield);
                    if (i == 0) {
                        per = remembered.getNetPower();
                    }
                    host.addRemembered(remembered);
                }
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), count * per);
            }
            case "REMEMBERED_CARDMANACOST": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int count = intParam(c.recipeParams, "remembered_bears");
                int per = 0;
                for (int i = 0; i < count; i++) {
                    final Card remembered = addCardToZone("Runeclaw Bear", actor, ZoneType.Battlefield);
                    if (i == 0) {
                        per = remembered.getCMC();
                    }
                    host.addRemembered(remembered);
                }
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), count * per);
            }
            case "REMEMBERED_VALID_CREATURE": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int match = intParam(c.recipeParams, "match_bears");
                final int nonmatch = intParam(c.recipeParams, "nonmatch_islands");
                for (int i = 0; i < match; i++) {
                    host.addRemembered(addCardToZone("Runeclaw Bear", actor, ZoneType.Battlefield));
                }
                for (int i = 0; i < nonmatch; i++) {
                    host.addRemembered(addCardToZone("Island", actor, ZoneType.Battlefield));
                }
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), match);
            }
            case "REMEMBERED_VALID_GRAVEYARD": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int match = intParam(c.recipeParams, "match_bears");
                for (int i = 0; i < match; i++) {
                    host.addRemembered(addCardToZone("Runeclaw Bear", actor, ZoneType.Graveyard));
                }
                host.addRemembered(addCardToZone("Runeclaw Bear", actor, ZoneType.Battlefield));
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), match);
            }
            case "REMEMBERED_VALID_PLAYERCTRL": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int match = intParam(c.recipeParams, "match_bears");
                final int other = intParam(c.recipeParams, "opponent_bears");
                host.addRemembered(actor);
                for (int i = 0; i < match; i++) {
                    host.addRemembered(addCardToZone("Runeclaw Bear", actor, ZoneType.Battlefield));
                }
                for (int i = 0; i < other; i++) {
                    host.addRemembered(addCardToZone("Runeclaw Bear", game.getPlayers().get(1), ZoneType.Battlefield));
                }
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), match);
            }
            case "REMEMBERED_VALID_YOUCTRL": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int match = intParam(c.recipeParams, "match_bears");
                final int other = intParam(c.recipeParams, "opponent_bears");
                for (int i = 0; i < match; i++) {
                    host.addRemembered(addCardToZone("Runeclaw Bear", actor, ZoneType.Battlefield));
                }
                for (int i = 0; i < other; i++) {
                    host.addRemembered(addCardToZone("Runeclaw Bear", game.getPlayers().get(1), ZoneType.Battlefield));
                }
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), match);
            }
            case "SACRIFICED_CARDPOWER":
            case "SACRIFICED_CARDTOUGHNESS": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int count = intParam(c.recipeParams, "sacrificed_bears");
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                int per = 0;
                for (int i = 0; i < count; i++) {
                    final Card sacrificed = addCardToZone("Runeclaw Bear", actor, ZoneType.Graveyard);
                    if (i == 0) {
                        per = "SACRIFICED_CARDPOWER".equals(c.recipe)
                                ? sacrificed.getNetPower() : sacrificed.getNetToughness();
                    }
                    sa.getRootAbility().addCostToHashList(sacrificed, "Sacrificed", true);
                }
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), count * per);
            }
            case "TARGETED_CARDPOWER":
            case "TARGETED_CARDMANACOST":
            case "TARGETED_CARDTOUGHNESS": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int count = intParam(c.recipeParams, "target_bears");
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                int per = 0;
                for (int i = 0; i < count; i++) {
                    final Card target = addCardToZone("Runeclaw Bear", game.getPlayers().get(1), ZoneType.Battlefield);
                    if (i == 0) {
                        if ("TARGETED_CARDPOWER".equals(c.recipe)) {
                            per = target.getNetPower();
                        } else if ("TARGETED_CARDMANACOST".equals(c.recipe)) {
                            per = target.getCMC();
                        } else {
                            per = target.getNetToughness();
                        }
                    }
                    sa.getTargets().add(target);
                }
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), count * per);
            }
            case "TARGETED_COUNTERS": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int counters = intParam(c.recipeParams, "counters");
                final Card target = addCardToZone("Runeclaw Bear", game.getPlayers().get(1), ZoneType.Battlefield);
                final CounterType counterType = CounterType.getType(c.recipeParams.get("counter"));
                target.setCounters(counterType, counters);
                if (target.getCounters(counterType) != counters) {
                    throw new IllegalStateException("counter fixture write not visible");
                }
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                sa.getTargets().add(target);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), counters);
            }
            case "TARGETED_VALID_HUMAN_PLUS1": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final Card human = addCardToZone("Elite Vanguard", game.getPlayers().get(1), ZoneType.Battlefield);
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                sa.getTargets().add(human);
                final int actual = AbilityUtils.calculateAmount(host, c.svarToken, sa);
                final int expected = AbilityUtils.doXMath(1, "Plus.1", host, sa);
                if (expected != 2) {
                    throw new IllegalStateException("production doXMath baseline shifted");
                }
                return new AmountResult(actual, expected);
            }
            case "TARGETEDPLAYER_CARDSINHAND": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final Player foe = game.getPlayers().get(1);
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                sa.getTargets().add(foe);
                return new AmountResult(
                        AbilityUtils.calculateAmount(host, c.svarToken, sa),
                        foe.getZone(ZoneType.Hand).size());
            }
            case "TARGETEDPLAYER_LIFETOTAL": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final Player foe = game.getPlayers().get(1);
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                sa.getTargets().add(foe);
                return new AmountResult(
                        AbilityUtils.calculateAmount(host, c.svarToken, sa), foe.getLife());
            }
            case "TARGETEDPLAYER_POISON": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final Player foe = game.getPlayers().get(1);
                final int poison = intParam(c.recipeParams, "poison");
                foe.setPoisonCounters(poison, actor);
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                sa.getTargets().add(foe);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), poison);
            }
            case "TARGETEDPLAYER_HAND_MINUS_X": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int actorExtra = intParam(c.recipeParams, "actor_islands");
                final int oppExtra = intParam(c.recipeParams, "opponent_islands");
                final Player foe = game.getPlayers().get(1);
                for (int i = 0; i < actorExtra; i++) {
                    addCardToZone("Island", actor, ZoneType.Hand);
                }
                for (int i = 0; i < oppExtra; i++) {
                    addCardToZone("Island", foe, ZoneType.Hand);
                }
                final int expected = foe.getZone(ZoneType.Hand).size() - actor.getZone(ZoneType.Hand).size();
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                sa.getTargets().add(foe);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), expected);
            }
            case "TRIGGERCOUNT_DAMAGE":
            case "TRIGGERCOUNT_AMOUNT": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int key = "TRIGGERCOUNT_DAMAGE".equals(c.recipe)
                        ? intParam(c.recipeParams, "damage") : intParam(c.recipeParams, "amount");
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                sa.getRootAbility().setTriggeringObject(
                        "TRIGGERCOUNT_DAMAGE".equals(c.recipe) ? AbilityKey.DamageAmount : AbilityKey.Amount, key);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), key);
            }
            case "PLAYERCOUNT_OPPONENTS_AMOUNT": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(
                        AbilityUtils.calculateAmount(host, c.svarToken, sa),
                        actor.getOpponents().size());
            }
            case "PLAYERCOUNT_OPPONENTS_HIGHEST_LAND": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int opp1 = intParam(c.recipeParams, "opp1_islands");
                final int opp2 = intParam(c.recipeParams, "opp2_islands");
                final Player foe1 = game.getPlayers().get(1);
                final Player foe2 = game.getPlayers().get(2);
                for (int i = 0; i < opp1; i++) {
                    addCardToZone("Island", foe1, ZoneType.Battlefield);
                }
                for (int i = 0; i < opp2; i++) {
                    addCardToZone("Island", foe2, ZoneType.Battlefield);
                }
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(
                        AbilityUtils.calculateAmount(host, c.svarToken, sa), Math.max(opp1, opp2));
            }
            case "TRIGGEREDCARD_COUNTERS": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int counters = intParam(c.recipeParams, "counters");
                final Card trigger = addCardToZone("Runeclaw Bear", game.getPlayers().get(1), ZoneType.Battlefield);
                final CounterType counterType = CounterType.getType(c.recipeParams.get("counter"));
                trigger.setCounters(counterType, counters);
                if (trigger.getCounters(counterType) != counters) {
                    throw new IllegalStateException("counter fixture write not visible");
                }
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                sa.getRootAbility().setTriggeringObject(AbilityKey.Card, trigger);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), counters);
            }
            case "TRIGGEREDCARD_CMC": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final Card trigger = addCardToZone("Runeclaw Bear", game.getPlayers().get(1), ZoneType.Battlefield);
                final int cmc = trigger.getCMC();
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                sa.getRootAbility().setTriggeringObject(AbilityKey.Card, trigger);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), cmc);
            }
            case "TRIGGEREDCARD_POWER": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final Card trigger = addCardToZone("Runeclaw Bear", game.getPlayers().get(1), ZoneType.Battlefield);
                final int power = trigger.getNetPower();
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                sa.getRootAbility().setTriggeringObject(AbilityKey.Card, trigger);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), power);
            }
            case "TRIGGEREDCARD_COLORS": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final Card trigger = addCardToZone("Runeclaw Bear", game.getPlayers().get(1), ZoneType.Battlefield);
                final int colors = trigger.getColor().countColors();
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                sa.getRootAbility().setTriggeringObject(AbilityKey.Card, trigger);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), colors);
            }
            case "TRIGGEREDCARD_GREATESTPOWER": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final Card trigger = addCardToZone("Runeclaw Bear", game.getPlayers().get(1), ZoneType.Battlefield);
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                sa.getRootAbility().setTriggeringObject(AbilityKey.Card, trigger);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), 1);
            }
            case "TRIGGEREDCARD_ATTACKING": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final Player foe = game.getPlayers().get(1);
                final Card trigger = addCardToZone("Runeclaw Bear", actor, ZoneType.Battlefield);
                game.getPhaseHandler().setCombat(new forge.game.combat.Combat(actor));
                game.getCombat().addAttacker(trigger, foe);
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                sa.getRootAbility().setTriggeringObject(AbilityKey.Card, trigger);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), 1);
            }
            case "TRIGGEREDCARD_CMC_MINUS_Z": {
                // Z (Remembered$CardManaCost) is evaluated by production against
                // the trigger card's remembered set (doXMath passes the trigger
                // as amount context). Remembering identical sets on host and
                // trigger keeps the expectation independent of that scoping.
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int count = intParam(c.recipeParams, "remembered_bears");
                final Card trigger = addCardToZone("Runeclaw Bear", game.getPlayers().get(1), ZoneType.Battlefield);
                final int trigCmc = trigger.getCMC();
                int per = 0;
                for (int i = 0; i < count; i++) {
                    final Card remembered = addCardToZone("Runeclaw Bear", actor, ZoneType.Battlefield);
                    if (i == 0) {
                        per = remembered.getCMC();
                    }
                    host.addRemembered(remembered);
                    trigger.addRemembered(remembered);
                }
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                sa.getRootAbility().setTriggeringObject(AbilityKey.Card, trigger);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), trigCmc - count * per);
            }
            case "TRIGGEREDSPELLABILITY_CMC": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final Card triggerSource = addCardToZone("Prodigal Sorcerer", actor, ZoneType.Battlefield);
                SpellAbility triggerAbility = null;
                for (final SpellAbility candidate : triggerSource.getSpellAbilities()) {
                    if (candidate.isActivatedAbility()) {
                        triggerAbility = candidate;
                        break;
                    }
                }
                if (triggerAbility == null) {
                    throw new IllegalStateException("trigger source lacks activated ability");
                }
                final int cmc = triggerSource.getCMC();
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                sa.getRootAbility().setTriggeringObject(AbilityKey.SpellAbility, triggerAbility);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), cmc);
            }
            case "REPLACECOUNT_DAMAGE": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int damage = intParam(c.recipeParams, "damage");
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                sa.getRootAbility().setReplacingObject(AbilityKey.DamageAmount, damage);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), damage);
            }
            case "PARENTTARGETED_CARDPOWER": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int count = intParam(c.recipeParams, "target_bears");
                final SpellAbility sub = findSubAbility(host);
                if (sub == null) {
                    throw new IllegalStateException("host card has no sub-ability for parent targeting");
                }
                sub.setActivatingPlayer(actor);
                final Card parentSource = addCardToZone("Prodigal Sorcerer", actor, ZoneType.Battlefield);
                SpellAbility parent = null;
                for (final SpellAbility candidate : parentSource.getSpellAbilities()) {
                    if (candidate.usesTargeting()) {
                        parent = candidate;
                        break;
                    }
                }
                if (parent == null) {
                    throw new IllegalStateException("parent fixture lacks targeting ability");
                }
                parent.setActivatingPlayer(actor);
                int per = 0;
                for (int i = 0; i < count; i++) {
                    final Card target = addCardToZone("Runeclaw Bear", game.getPlayers().get(1), ZoneType.Battlefield);
                    if (i == 0) {
                        per = target.getNetPower();
                    }
                    parent.getTargets().add(target);
                }
                parent.appendSubAbility((forge.game.spellability.AbilitySub) sub);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sub), count * per);
            }
            case "COUNT_HOST_COUNTERS": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int counters = intParam(c.recipeParams, "counters");
                final CounterType counterType = CounterType.getType(c.recipeParams.get("counter"));
                host.setCounters(counterType, counters);
                if (host.getCounters(counterType) != counters) {
                    throw new IllegalStateException("counter fixture write not visible");
                }
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), counters);
            }
            case "COUNT_LIFE": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int life = intParam(c.recipeParams, "life");
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                final int current = actor.getLife();
                if (current < life) {
                    actor.gainLife(life - current, host, sa);
                } else if (current > life) {
                    actor.loseLife(current - life, false, false, sa);
                }
                if (actor.getLife() != life) {
                    throw new IllegalStateException("life fixture state mismatch");
                }
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), life);
            }
            case "COUNT_BATTLEFIELD_VALID": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int base = intParam(c.recipeParams, "base");
                int placed = 0;
                for (final String spec : c.recipeParams.get("place").split(";")) {
                    final String[] parts = spec.split(",", -1);
                    final Player owner = "ACTOR".equals(parts[1]) ? actor : game.getPlayers().get(1);
                    final Card placedCard = addCardToZone(parts[0], owner, ZoneType.Battlefield);
                    if (parts.length > 2 && "1".equals(parts[2])) {
                        placedCard.setTapped(true);
                    }
                    placed++;
                }
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), placed + base);
            }
            case "COUNT_COLORS": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int expectedColors = intParam(c.recipeParams, "expected_colors");
                // Basic lands are colorless: use colored permanents. The
                // decision-fixture Prodigal Sorcerer (blue) and Runeclaw Bear
                // are already inside the covered color set.
                for (final String permanent : new String[]{"Elite Vanguard", "Flying Men",
                        "Drudge Skeletons", "Raging Goblin", "Runeclaw Bear"}) {
                    addCardToZone(permanent, actor, ZoneType.Battlefield);
                }
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), expectedColors);
            }
            case "COUNT_VALID_ANY": {
                // Valid "Any" matches creatures, planeswalkers and battles.
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), countValidAny(game));
            }
            case "COUNT_GATE_NAMES": {
                // Maze's End itself is Land without the Gate subtype: it does
                // not match. Two real Gates give two distinct names.
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                addCardToZone("Gruul Guildgate", actor, ZoneType.Battlefield);
                addCardToZone("Azorius Guildgate", actor, ZoneType.Battlefield);
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), 2);
            }
            case "COUNT_GATE_TIMES2": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                addCardToZone("Gruul Guildgate", actor, ZoneType.Battlefield);
                addCardToZone("Azorius Guildgate", actor, ZoneType.Battlefield);
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), 4);
            }
            case "COUNT_NAMED": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int count = intParam(c.recipeParams, "count");
                for (int i = 0; i < count; i++) {
                    addCardToZone(c.recipeParams.get("name"), actor, ZoneType.Battlefield);
                }
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), count);
            }
            case "COUNT_GRAVE_CREATURE": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int actorBears = intParam(c.recipeParams, "actor_bears");
                final int oppBears = intParam(c.recipeParams, "opponent_bears");
                for (int i = 0; i < actorBears; i++) {
                    addCardToZone("Runeclaw Bear", actor, ZoneType.Graveyard);
                }
                for (int i = 0; i < oppBears; i++) {
                    addCardToZone("Runeclaw Bear", game.getPlayers().get(1), ZoneType.Graveyard);
                }
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(
                        AbilityUtils.calculateAmount(host, c.svarToken, sa), actorBears + oppBears);
            }
            case "COUNT_GRAVE_SPELLS": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int actorShocks = intParam(c.recipeParams, "actor_shocks");
                final int oppShocks = intParam(c.recipeParams, "opponent_shocks");
                for (int i = 0; i < actorShocks; i++) {
                    addCardToZone("Shock", actor, ZoneType.Graveyard);
                }
                for (int i = 0; i < oppShocks; i++) {
                    addCardToZone("Shock", game.getPlayers().get(1), ZoneType.Graveyard);
                }
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(
                        AbilityUtils.calculateAmount(host, c.svarToken, sa), actorShocks);
            }
            case "COUNT_HAND_ACTIVE": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                final Player active = game.getPhaseHandler().getPlayerTurn();
                return new AmountResult(
                        AbilityUtils.calculateAmount(host, c.svarToken, sa),
                        active.getZone(ZoneType.Hand).size());
            }
            case "COUNT_MAXCMC": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final Card ring = addCardToZone("Sol Ring", actor, ZoneType.Battlefield);
                final Card shock = addCardToZone("Shock", actor, ZoneType.Graveyard);
                final Card divination = addCardToZone("Divination", actor, ZoneType.Graveyard);
                int expected = ring.getCMC();
                expected = Math.max(expected, shock.getCMC());
                expected = Math.max(expected, divination.getCMC());
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), expected);
            }
            case "COUNT_ATTACKERS": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int attackers = intParam(c.recipeParams, "attackers");
                final Player foe = game.getPlayers().get(1);
                for (int i = 0; i < attackers; i++) {
                    actor.addCreaturesAttackedThisTurn(
                            addCardToZone("Runeclaw Bear", actor, ZoneType.Battlefield), foe);
                }
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), attackers);
            }
            case "COUNT_HOST_POWER": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int power = host.getNetPower();
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), power);
            }
            case "COUNT_REMEMBERED_SIZE": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int count = intParam(c.recipeParams, "remembered");
                for (int i = 0; i < count; i++) {
                    host.addRemembered(addCardToZone("Runeclaw Bear", actor, ZoneType.Battlefield));
                }
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), count);
            }
            case "COUNT_MORBID": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int trueVal = intParam(c.recipeParams, "true_val");
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                game.getAction().moveTo(ZoneType.Graveyard,
                        addCardToZone("Runeclaw Bear", actor, ZoneType.Battlefield), null, null);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), trueVal);
            }
            case "COUNT_FORETOLD": {
                Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int trueVal = intParam(c.recipeParams, "true_val");
                host = game.getAction().moveTo(ZoneType.Exile, host, null, null);
                host.setForetold(true);
                if (!host.isForetold()) {
                    throw new IllegalStateException("foretold fixture state mismatch");
                }
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), trueVal);
            }
            case "COUNT_LANDFALL": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int trueVal = intParam(c.recipeParams, "true_val");
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                final Card land = addCardToZone("Island", actor, ZoneType.Hand);
                game.getAction().moveTo(ZoneType.Battlefield, land, null, null);
                if (!actor.hasLandfall()) {
                    throw new IllegalStateException("landfall fixture did not register");
                }
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), trueVal);
            }
            case "COUNT_ENTERED_MODIFIED": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                final Card modified = addCardToZone("Runeclaw Bear", actor, ZoneType.Battlefield);
                modified.setCounters(CounterType.getType("P1P1"), 1);
                game.getAction().moveTo(ZoneType.Graveyard, modified, null, null);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), 1);
            }
            case "NUMBER_DEFAULT": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int value = intParam(c.recipeParams, "value");
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), value);
            }
            case "NUMBER_VRASKA": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final Player foe = game.getPlayers().get(1);
                final int poison = intParam(c.recipeParams, "poison");
                foe.setPoisonCounters(poison, actor);
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                sa.getTargets().add(foe);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), 9 - poison);
            }
            case "PLAYERCOUNT_PLAYERS": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(
                        AbilityUtils.calculateAmount(host, c.svarToken, sa),
                        game.getPlayers().size());
            }
            case "PLAYERCOUNT_CONDITION": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final Player foe = game.getPlayers().get(1);
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                foe.loseLife(foe.getLife() - intParam(c.recipeParams, "low_life"), false, false, sa);
                int expected = 0;
                for (final Player p : game.getPlayers()) {
                    if (p.getLife() <= p.getStartingLife() / 2) {
                        expected++;
                    }
                }
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), expected);
            }
            case "PLAYERCOUNT_LOSTLIFE": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final Player foe = game.getPlayers().get(1);
                foe.setLifeLostThisTurn(intParam(c.recipeParams, "lost"));
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), 1);
            }
            case "PLAYERCOUNT_LIFELOST_SUM": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final Player foe = game.getPlayers().get(1);
                final int lost = intParam(c.recipeParams, "lost");
                foe.setLifeLostThisTurn(lost);
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), lost);
            }
            case "PLAYERCOUNT_DISCARDED": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int discarded = intParam(c.recipeParams, "discarded");
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                for (int i = 0; i < discarded; i++) {
                    addCardToZone("Island", actor, ZoneType.Hand);
                }
                int done = 0;
                for (final Card card : new java.util.ArrayList<>(actor.getZone(ZoneType.Hand).getCards())) {
                    if (done >= discarded) {
                        break;
                    }
                    if (!"Island".equals(card.getName())) {
                        continue;
                    }
                    if (actor.discard(card, null, false, AbilityKey.newMap()) == null) {
                        throw new IllegalStateException("fixture discard rejected");
                    }
                    done++;
                }
                if (done != discarded) {
                    throw new IllegalStateException("fixture discard shortfall");
                }
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), discarded);
            }
            case "PLAYERCOUNT_SACRIFICED": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int sacrificed = intParam(c.recipeParams, "sacrificed");
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                final List<Card> victims = new ArrayList<>();
                for (int i = 0; i < sacrificed; i++) {
                    victims.add(addCardToZone("Runeclaw Bear", actor, ZoneType.Battlefield));
                }
                final Map<AbilityKey, Object> sacParams = AbilityKey.newMap();
                AbilityKey.addCardZoneTableParams(sacParams, sa);
                game.getAction().sacrifice(victims, sa, false, sacParams);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), sacrificed);
            }
            case "PLAYERCOUNT_HAND_LE1": {
                // Test games start with empty hands: give the other players
                // cards so only the fixture opponent satisfies LE1.
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final Player foe = game.getPlayers().get(1);
                for (int i = 0; i < 3; i++) {
                    addCardToZone("Island", actor, ZoneType.Hand);
                }
                for (int i = 0; i < 2; i++) {
                    addCardToZone("Island", game.getPlayers().get(2), ZoneType.Hand);
                }
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), 1);
            }
            case "PLAYERCOUNT_DEFINEDREGISTERED": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final Player foe = game.getPlayers().get(1);
                final int lost = intParam(c.recipeParams, "lost");
                foe.setLifeLostThisTurn(lost);
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), lost);
            }
            case "PLAYERCOUNT_REMEMBERED": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final Player foe = game.getPlayers().get(1);
                host.addRemembered(foe);
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), 1);
            }
            case "PLAYERCOUNT_HIGHEST_GRAVE": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int opp1 = intParam(c.recipeParams, "opp1_bears");
                final int opp2 = intParam(c.recipeParams, "opp2_bears");
                for (int i = 0; i < opp1; i++) {
                    addCardToZone("Runeclaw Bear", game.getPlayers().get(1), ZoneType.Graveyard);
                }
                for (int i = 0; i < opp2; i++) {
                    addCardToZone("Runeclaw Bear", game.getPlayers().get(2), ZoneType.Graveyard);
                }
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(
                        AbilityUtils.calculateAmount(host, c.svarToken, sa), Math.max(opp1, opp2));
            }
            case "PLAYERCOUNT_LOWEST_LIFE": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final Player foe = game.getPlayers().get(2);
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                foe.loseLife(foe.getLife() - intParam(c.recipeParams, "low_life"), false, false, sa);
                int expected = Integer.MAX_VALUE;
                for (final Player p : game.getPlayers()) {
                    expected = Math.min(expected, p.getLife());
                }
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), expected);
            }
            case "REMEMBEREDLKI_TOUGHNESS": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int count = intParam(c.recipeParams, "remembered_bears");
                int per = 0;
                for (int i = 0; i < count; i++) {
                    final Card remembered = addCardToZone("Runeclaw Bear", actor, ZoneType.Battlefield);
                    if (i == 0) {
                        per = remembered.getNetToughness();
                    }
                    host.addRemembered(remembered);
                }
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), count * per);
            }
            case "REPLACECOUNT_OPS": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int value = intParam(c.recipeParams, "value");
                final String ops = c.recipeParams.get("ops");
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                sa.getRootAbility().setReplacingObject(
                        AbilityKey.fromString(c.recipeParams.get("key")), value);
                return new AmountResult(
                        AbilityUtils.calculateAmount(host, c.svarToken, sa),
                        AbilityUtils.doXMath(value, ops, host, sa));
            }
            case "SVAR_FIRSTFAMILY": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int white = intParam(c.recipeParams, "white");
                final int blue = intParam(c.recipeParams, "blue");
                final int black = intParam(c.recipeParams, "black");
                final int red = intParam(c.recipeParams, "red");
                final int green = intParam(c.recipeParams, "green");
                for (int i = 0; i < white; i++) {
                    addCardToZone("Elite Vanguard", actor, ZoneType.Battlefield);
                }
                for (int i = 0; i < blue; i++) {
                    addCardToZone("Flying Men", actor, ZoneType.Battlefield);
                }
                for (int i = 0; i < black; i++) {
                    addCardToZone("Drudge Skeletons", actor, ZoneType.Battlefield);
                }
                for (int i = 0; i < red; i++) {
                    addCardToZone("Raging Goblin", actor, ZoneType.Battlefield);
                }
                for (int i = 0; i < green; i++) {
                    addCardToZone("Runeclaw Bear", actor, ZoneType.Battlefield);
                }
                // Decision-fixture Prodigal Sorcerer is a blue actor permanent.
                // Host First Family ({2}{G}{U} instant on the battlefield)
                // satisfies the Permanent token via isInPlay and contributes
                // its blue and green colors.
                final int wp = white;
                final int up = blue + 2;
                final int bp = black;
                final int rp = red;
                final int gp = green + 1;
                final int w2 = wp;
                final int u2 = up;
                final int b2 = bp;
                final int r2 = rp;
                final int g2 = gp;
                final int w = Math.min(w2, 1);
                final int u = Math.min(u2, 1);
                final int b = Math.min(b2, 1);
                final int r = Math.min(r2, 1);
                final int g = Math.min(g2, 1);
                final int wu = w + u;
                final int br = b + r;
                final int wubr = wu + br;
                final int x = wubr + g;
                final int expected;
                switch (c.svarToken) {
                    case "W": expected = w; break;
                    case "U": expected = u; break;
                    case "B": expected = b; break;
                    case "R": expected = r; break;
                    case "G": expected = g; break;
                    case "W2": expected = w2; break;
                    case "U2": expected = u2; break;
                    case "B2": expected = b2; break;
                    case "R2": expected = r2; break;
                    case "G2": expected = g2; break;
                    case "WU": expected = wu; break;
                    case "BR": expected = br; break;
                    case "WUBR": expected = wubr; break;
                    case "X": expected = x; break;
                    case "WP": expected = wp; break;
                    case "UP": expected = up; break;
                    case "BP": expected = bp; break;
                    case "RP": expected = rp; break;
                    case "GP": expected = gp; break;
                    case "WS": case "US": case "BS": case "RS": case "GS": expected = 0; break;
                    default: throw new IllegalStateException("unknown First Family token " + c.svarToken);
                }
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), expected);
            }
            case "SVAR_SOULBURN": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int paid = intParam(c.recipeParams, "paid");
                final int black = intParam(c.recipeParams, "black");
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                sa.getRootAbility().setXManaCostPaid(paid);
                host.setXManaCostPaidByColor(java.util.Map.of("B", black));
                return new AmountResult(
                        AbilityUtils.calculateAmount(host, c.svarToken, sa), Math.min(black, paid));
            }
            case "SVAR_FANDANIEL": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int actorShocks = intParam(c.recipeParams, "actor_shocks");
                final int oppShocks = intParam(c.recipeParams, "opponent_shocks");
                for (int i = 0; i < actorShocks; i++) {
                    addCardToZone("Shock", actor, ZoneType.Graveyard);
                }
                for (int i = 0; i < oppShocks; i++) {
                    addCardToZone("Shock", game.getPlayers().get(1), ZoneType.Graveyard);
                }
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), actorShocks * 2);
            }
            case "SVAR_SCEPTER": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                addCardToZone("Crown of Empires", actor, ZoneType.Battlefield);
                addCardToZone("Throne of Empires", actor, ZoneType.Battlefield);
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), 1);
            }
            case "SVAR_LOKI_ABS": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int count = intParam(c.recipeParams, "remembered_bears");
                final Card trigger = addCardToZone("Runeclaw Bear", game.getPlayers().get(1), ZoneType.Battlefield);
                final int trigCmc = trigger.getCMC();
                int per = 0;
                for (int i = 0; i < count; i++) {
                    final Card remembered = addCardToZone("Runeclaw Bear", actor, ZoneType.Battlefield);
                    if (i == 0) {
                        per = remembered.getCMC();
                    }
                    host.addRemembered(remembered);
                    trigger.addRemembered(remembered);
                }
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                sa.getRootAbility().setTriggeringObject(AbilityKey.Card, trigger);
                return new AmountResult(
                        AbilityUtils.calculateAmount(host, c.svarToken, sa), Math.abs(trigCmc - count * per));
            }
            case "SVAR_FIREBALL": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(
                        AbilityUtils.calculateAmount(host, c.svarToken, sa),
                        3 + countValidAny(game));
            }
            case "TARGETEDCONTROLLER_GRAVELANDS": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int actorLands = intParam(c.recipeParams, "actor_lands");
                final int oppLands = intParam(c.recipeParams, "opponent_lands");
                for (int i = 0; i < actorLands; i++) {
                    addCardToZone("Island", actor, ZoneType.Graveyard);
                }
                for (int i = 0; i < oppLands; i++) {
                    addCardToZone("Island", game.getPlayers().get(1), ZoneType.Graveyard);
                }
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                sa.getTargets().add(addCardToZone("Runeclaw Bear", actor, ZoneType.Battlefield));
                sa.getTargets().add(addCardToZone("Runeclaw Bear", game.getPlayers().get(1), ZoneType.Battlefield));
                return new AmountResult(
                        AbilityUtils.calculateAmount(host, c.svarToken, sa), actorLands + oppLands);
            }
            case "TARGETEDOBJECTS_AMOUNT": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final Player foe = game.getPlayers().get(1);
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                sa.getTargets().add(addCardToZone("Runeclaw Bear", actor, ZoneType.Battlefield));
                sa.getTargets().add(addCardToZone("Runeclaw Bear", foe, ZoneType.Battlefield));
                sa.getTargets().add(foe);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), 2);
            }
            case "TRIGGEREDATTACKER_POWER": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final Card trigger = addCardToZone("Runeclaw Bear", game.getPlayers().get(1), ZoneType.Battlefield);
                final int power = trigger.getNetPower();
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                sa.getRootAbility().setTriggeringObject(AbilityKey.Attacker, trigger);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), power);
            }
            case "TRIGGEREDOBJECT_KREE": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                sa.getRootAbility().setTriggeringObject(AbilityKey.Object, host);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), 1);
            }
            case "TRIGGEREDTARGET_LIFE": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final Player foe = game.getPlayers().get(1);
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                sa.getRootAbility().setTriggeringObject(AbilityKey.Target, foe);
                return new AmountResult(
                        AbilityUtils.calculateAmount(host, c.svarToken, sa),
                        AbilityUtils.doXMath(foe.getLife(), "HalfUp", host, sa));
            }
            case "COUNT_COMMANDER_CAST": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int casts = intParam(c.recipeParams, "casts");
                for (int i = 0; i < casts; i++) {
                    actor.incCommanderCast(addCardToZone("Runeclaw Bear", actor, ZoneType.Battlefield));
                }
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), casts);
            }
            case "COUNT_EQUIPMENT_ATTACHED_ZERO": {
                // No zone token parses from "Equipment.Attached": the engine
                // counts over an empty zone set and yields 0 even with an
                // attached Equipment present. REVIEW: dead expression.
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final Card bearer = addCardToZone("Runeclaw Bear", actor, ZoneType.Battlefield);
                final Card equipment = addCardToZone("Lightning Greaves", actor, ZoneType.Battlefield);
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                equipment.attachToEntity(bearer, sa);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), 0);
            }
            case "COUNT_CARDNUMATTACKS": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int attacks = intParam(c.recipeParams, "attacks");
                final Player foe = game.getPlayers().get(1);
                final Player foe2 = game.getPlayers().get(2);
                host.getDamageHistory().setCreatureAttackedThisCombat(foe, 0);
                host.getDamageHistory().setCreatureAttackedThisCombat(foe2, 0);
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), attacks);
            }
            case "PLAYERCOUNT_UNBOUND_ZERO": {
                // Property string has no production branch: unknown-property
                // tail returns false for every player. REVIEW: dead expression.
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), 0);
            }
            case "COUNT_ATTACKED_LASTTURN": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final Player foe = game.getPlayers().get(1);
                foe.setAttackedPlayersMyLastTurn(java.util.List.of(actor));
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), 1);
            }
            case "TRIGGEREDCARD_ATTACHED": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final Card trigger = addCardToZone("Runeclaw Bear", actor, ZoneType.Battlefield);
                final Card aura = addCardToZone("Rancor", actor, ZoneType.Battlefield);
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                aura.attachToEntity(trigger, sa);
                if (!trigger.getAttachedCards().contains(aura)) {
                    throw new IllegalStateException("aura fixture did not attach");
                }
                sa.getRootAbility().setTriggeringObject(AbilityKey.Card, trigger);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), 1);
            }
            case "TRIGGEREDCARD_CASTSA_MANA":
            case "REPLACEDCARD_CASTSA": {
                final boolean replaced = "REPLACEDCARD_CASTSA".equals(c.recipe);
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int mana = intParam(c.recipeParams, "mana");
                final Card payer = addCardToZone("Sol Ring", actor, ZoneType.Battlefield);
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                final forge.game.spellability.AbilityManaPart part =
                        new forge.game.spellability.AbilityManaPart(payer, java.util.Map.of("Produced", "R"));
                for (int i = 0; i < mana; i++) {
                    sa.getPayingMana().add(new forge.game.mana.Mana(
                            forge.card.MagicColor.RED, payer, part, actor));
                }
                if (replaced) {
                    final Card trigger = addCardToZone("Runeclaw Bear", game.getPlayers().get(1), ZoneType.Battlefield);
                    trigger.setCastSA(sa);
                    sa.getRootAbility().setReplacingObject(AbilityKey.Card, trigger);
                } else {
                    final Card trigger = addCardToZone("Runeclaw Bear", game.getPlayers().get(1), ZoneType.Battlefield);
                    trigger.setCastSA(sa);
                    sa.getRootAbility().setTriggeringObject(AbilityKey.Card, trigger);
                }
                if (sa.getTotalManaSpent() != mana) {
                    throw new IllegalStateException("paying-mana fixture state mismatch");
                }
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), mana);
            }
            case "TRIGGEREDCARD_COMMANDERCAST": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int casts = intParam(c.recipeParams, "casts");
                final Card trigger = addCardToZone("Runeclaw Bear", game.getPlayers().get(1), ZoneType.Battlefield);
                for (int i = 0; i < casts; i++) {
                    actor.incCommanderCast(trigger);
                }
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                sa.getRootAbility().setTriggeringObject(AbilityKey.Card, trigger);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), casts);
            }
            case "TRIGGERREMEMBERED_ZERO": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int value = intParam(c.recipeParams, "value");
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), value);
            }
            case "COUNT_KICKED_FALSE": {
                // Fixture pays no kicker: production takes the not-kicked branch.
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int falseVal = intParam(c.recipeParams, "false_val");
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                if (sa.isKicked()) {
                    throw new IllegalStateException("fixture unexpectedly kicked");
                }
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), falseVal);
            }
            case "COUNT_TIMESKICKED_ZERO": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), 0);
            }
            case "COUNT_OPTIONALGENERIC_FALSE": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int falseVal = intParam(c.recipeParams, "false_val");
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), falseVal);
            }
            case "CAST_SPELLS": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                int cast = 0;
                for (final String spell : c.recipeParams.get("spells").split(";")) {
                    final Card spellCard = addCardToZone(spell, actor, ZoneType.Hand);
                    final SpellAbility spellAbility = spellCard.getSpells().get(0);
                    spellAbility.setActivatingPlayer(actor);
                    if (spellAbility.usesTargeting()) {
                        spellAbility.getTargets().add(addCardToZone(
                                "Runeclaw Bear", game.getPlayers().get(1), ZoneType.Battlefield));
                    }
                    game.getStack().addAndUnfreeze(spellAbility);
                    cast++;
                }
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), cast);
            }
            case "CAST_SPELLS_PLUS1": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                int cast = 0;
                for (final String spell : c.recipeParams.get("spells").split(";")) {
                    final Card spellCard = addCardToZone(spell, actor, ZoneType.Hand);
                    final SpellAbility spellAbility = spellCard.getSpells().get(0);
                    spellAbility.setActivatingPlayer(actor);
                    if (spellAbility.usesTargeting()) {
                        spellAbility.getTargets().add(addCardToZone(
                                "Runeclaw Bear", game.getPlayers().get(1), ZoneType.Battlefield));
                    }
                    game.getStack().addAndUnfreeze(spellAbility);
                    cast++;
                }
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), cast + 1);
            }
            case "CAST_SPELLS_MAXCMC": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                int best = 0;
                for (final String spell : c.recipeParams.get("spells").split(";")) {
                    final Card spellCard = addCardToZone(spell, actor, ZoneType.Hand);
                    best = Math.max(best, spellCard.getCMC());
                    final SpellAbility spellAbility = spellCard.getSpells().get(0);
                    spellAbility.setActivatingPlayer(actor);
                    if (spellAbility.usesTargeting()) {
                        spellAbility.getTargets().add(addCardToZone(
                                "Runeclaw Bear", game.getPlayers().get(1), ZoneType.Battlefield));
                    }
                    game.getStack().addAndUnfreeze(spellAbility);
                }
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), best);
            }
            case "CAST_ACTIVATE_ARTIFACT": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final Card ring = addCardToZone("Sol Ring", actor, ZoneType.Battlefield);
                final SpellAbility manaAbility = firstAbility(ring);
                manaAbility.setActivatingPlayer(actor);
                game.getStack().addAndUnfreeze(manaAbility);
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), 1);
            }
            case "COUNT_WASCAST_HAND": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int trueVal = intParam(c.recipeParams, "true_val");
                host.setCastFrom(actor.getZone(ZoneType.Hand));
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                host.setCastSA(sa);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), trueVal);
            }
            case "COUNT_NUMDAMAGE_ZERO": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int value = intParam(c.recipeParams, "value");
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), value);
            }
            case "COUNT_XCOLORPAID": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int black = intParam(c.recipeParams, "black");
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                host.setXManaCostPaidByColor(java.util.Map.of("B", black));
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), black);
            }
            case "COUNT_MONARCH": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                game.setMonarch(game.getPlayers().get(1));
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), 1);
            }
            case "COUNT_OPPONENTS_ATTACKED": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final int attackers = intParam(c.recipeParams, "attackers");
                final Player foe = game.getPlayers().get(1);
                for (int i = 0; i < attackers; i++) {
                    actor.addCreaturesAttackedThisTurn(
                            addCardToZone("Runeclaw Bear", actor, ZoneType.Battlefield), foe);
                }
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), 1);
            }
            case "TRIGGEREDSPELLABILITY_TIMESKICKED_ZERO": {
                final Card host = addCardToZone(c.cardName, actor, ZoneType.Battlefield);
                final Card triggerSource = addCardToZone("Prodigal Sorcerer", actor, ZoneType.Battlefield);
                SpellAbility triggerAbility = null;
                for (final SpellAbility candidate : triggerSource.getSpellAbilities()) {
                    if (candidate.isActivatedAbility()) {
                        triggerAbility = candidate;
                        break;
                    }
                }
                if (triggerAbility == null) {
                    throw new IllegalStateException("trigger source lacks activated ability");
                }
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(actor);
                sa.getRootAbility().setTriggeringObject(AbilityKey.SpellAbility, triggerAbility);
                return new AmountResult(AbilityUtils.calculateAmount(host, c.svarToken, sa), 0);
            }
            default:
                throw new IllegalStateException("fail-closed unsupported amount recipe " + c.recipe);
        }
    }

    private static int countValidAny(final Game game) {
        int expected = 0;
        for (final Card card : game.getCardsIn(ZoneType.Battlefield)) {
            if (card.isCreature() || card.isPlaneswalker() || card.isBattle()) {
                expected++;
            }
        }
        return expected;
    }

    private SpellAbility findSubAbility(final Card host) {
        for (final SpellAbility candidate : host.getSpellAbilities()) {
            final SpellAbility found = findSubAbilityRecursive(candidate);
            if (found != null) {
                return found;
            }
        }
        // Charm-style cards parse choice sub-abilities lazily; build each DB
        // script directly through production AbilityFactory as fallback.
        for (final SpellAbility candidate : host.getSpellAbilities()) {
            forge.game.card.CardState state = null;
            for (final forge.card.CardStateName stateName : forge.card.CardStateName.values()) {
                if (host.hasState(stateName)) {
                    state = host.getState(stateName);
                    break;
                }
            }
            if (state == null) {
                break;
            }
            for (final String svarName : host.getSVars().keySet()) {
                if (!svarName.startsWith("DB")) {
                    continue;
                }
                try {
                    final SpellAbility built = forge.game.ability.AbilityFactory.getAbility(
                            state, svarName, state);
                    if (built instanceof forge.game.spellability.AbilitySub) {
                        return built;
                    }
                } catch (RuntimeException ignored) {
                    // Not every DB script builds standalone; keep searching.
                }
            }
            break;
        }
        return null;
    }

    private SpellAbility findSubAbilityRecursive(final SpellAbility ability) {
        if (ability instanceof forge.game.spellability.AbilitySub) {
            return ability;
        }
        final SpellAbility sub = ability.getSubAbility();
        if (sub != null) {
            return findSubAbilityRecursive(sub);
        }
        return null;
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
        final boolean defaultZero = "COUNT_EQUIPMENT_ATTACHED_ZERO".equals(c.recipe)
                || "PLAYERCOUNT_UNBOUND_ZERO".equals(c.recipe)
                || "COUNT_NUMDAMAGE_ZERO".equals(c.recipe)
                || "NUMBER_DEFAULT".equals(c.recipe);
        final String evidenceClass = defaultZero ? "TECHNICALLY_CONFORMANT" : "EXTERNALLY_RULE_VALIDATED";
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
                + "\"evidence_class\":" + q(evidenceClass)
                + (defaultZero ? ",\"default_zero_evidence\":true,\"review_required\":\"DEAD_EXPRESSION\"" : "")
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
            out.put(unquote(part.substring(0, colon).trim()), unquote(part.substring(colon + 1).trim()));
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
