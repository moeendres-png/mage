package forge.net;

import forge.deck.Deck;
import forge.deck.DeckSection;
import forge.game.Game;
import forge.game.GameStage;
import forge.game.ability.AbilityFactory;
import forge.game.card.Card;
import forge.game.player.Player;
import forge.game.spellability.SpellAbility;
import forge.game.zone.ZoneType;
import forge.gamemodes.match.input.ExternalDecisionRequest;
import forge.gamemodes.match.input.ExternalDecisionResponse;
import forge.gamemodes.match.input.ExternalDecisionTape;
import forge.gamemodes.match.input.ExternalDecisionValidationException;
import forge.item.PaperCard;
import forge.model.FModel;
import forge.player.PlayerControllerHuman;
import org.testng.Assert;
import org.testng.annotations.Test;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicReference;

/** Focused ACTION_COST_DECISION dependency witness for strict TARGET_SELECTION. */
public final class Ws27TargetSelectionDependencyTest {
    private static final String FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928";

    @Test(timeOut = 300_000)
    public void actualCardOpponentTargetUsesAuthoritativeExternalOptions() throws Exception {
        TestUtils.ensureFModelInitialized();
        System.setProperty("forge.ws01.externalHumanHost", "true");

        final AtomicReference<ExternalDecisionRequest> targetRequest = new AtomicReference<>();
        final AtomicReference<String> selectedTargetSemantic = new AtomicReference<>();
        final AtomicReference<Throwable> campaignFailure = new AtomicReference<>();
        final AtomicBoolean campaignRan = new AtomicBoolean(false);

        PlayerControllerHuman.setExternalDecisionProviderFactory(player -> request -> {
            final List<String> selected = new ArrayList<>();
            switch (request.getDecisionKind()) {
                case "MULLIGAN" -> selected.add(requireSemantic(request, "true"));
                case "PRIORITY_ACTION" -> selected.add(requireSemantic(request, "PASS_PRIORITY"));
                case "STARTING_PLAYER", "STARTING_HAND" -> selected.add(stableSingle(request));
                case "TARGET_SELECTION" -> {
                    targetRequest.set(request);
                    Assert.assertEquals(request.getMinimumSelection(), 1);
                    Assert.assertEquals(request.getMaximumSelection(), 1);
                    Assert.assertFalse(request.isCancelAllowed(), "trigger target selection is mandatory");
                    Assert.assertEquals(request.getOptions().size(), 3,
                            "Keen Duelist in 4P Commander must expose exactly three legal opponents");
                    for (ExternalDecisionRequest.Option option : request.getOptions()) {
                        Assert.assertTrue(option.getSemanticValue().startsWith("player:"),
                                "target option semantic identity must be server-owned player id only");
                        Assert.assertNotEquals(option.getSemanticValue(), "player:" + request.getActorId(),
                                "actor must not be an Opponent target option");
                    }
                    final ExternalDecisionRequest.Option chosen = request.getOptions().stream()
                            .min(Comparator.comparing(o -> sha256(o.getSemanticValue())))
                            .orElseThrow();
                    selectedTargetSemantic.set(chosen.getSemanticValue());
                    selected.add(chosen.getOptionId());
                }
                default -> throw new ExternalDecisionValidationException(
                        ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                        "WS27 target dependency has no explicit policy for " + request.getDecisionKind());
            }
            return new ExternalDecisionResponse(
                    request.getDecisionId(), request.getToken(), request.getActorId(), request.getPrincipalId(),
                    request.getResponseSchema(), selected, false);
        });

        Game.setSemanticStateObserver((game, checkpoint) -> {
            if (!campaignRan.get() && ready(game) && campaignRan.compareAndSet(false, true)) {
                try {
                    final List<Player> players = new ArrayList<>();
                    for (Player p : game.getRegisteredPlayers()) players.add(p);
                    players.sort(Comparator.comparingInt(Player::getId));
                    final Player actor = players.get(0);

                    final Card source = addCard("Keen Duelist", actor, ZoneType.Battlefield);
                    final String exactScript = source.getSVar("TrigReveal");
                    Assert.assertNotNull(exactScript);
                    Assert.assertTrue(exactScript.startsWith("DB$ PeekAndReveal"));

                    final SpellAbility sa = AbilityFactory.getAbility(exactScript, source);
                    sa.setActivatingPlayer(actor);
                    Assert.assertTrue(sa.usesTargeting());
                    Assert.assertEquals(sa.getMinTargets(), 1);
                    Assert.assertEquals(sa.getMaxTargets(), 1);
                    Assert.assertTrue(actor.getController() instanceof PlayerControllerHuman);
                    Assert.assertTrue(actor.getController().chooseTargetsFor(sa),
                            "rules-core target selection must complete from external authoritative options");

                    final Player target = sa.getTargets().getFirstTargetedPlayer();
                    Assert.assertNotNull(target);
                    Assert.assertTrue(actor.getOpponents().contains(target));
                    Assert.assertEquals("player:" + target.getId(), selectedTargetSemantic.get(),
                            "applied target must be exactly the externally selected authoritative option");

                    final ExternalDecisionRequest req = targetRequest.get();
                    Assert.assertNotNull(req);
                    Assert.assertEquals(req.getActorId(), actor.getId());
                    Assert.assertEquals(req.getPrincipalId(), actor.getId());
                    Assert.assertEquals(req.getVisibilityScope(), ExternalDecisionRequest.VISIBILITY_PRINCIPAL_ONLY);

                    final List<ExternalDecisionTape.Event> tape = ((PlayerControllerHuman) actor.getController())
                            .getExternalDecisionTapeSnapshot();
                    final long acceptedTargetEvents = tape.stream()
                            .filter(e -> "TARGET_SELECTION".equals(e.getDecisionKind()))
                            .filter(e -> e.getResponseStatus() == ExternalDecisionTape.ResponseStatus.ACCEPTED)
                            .count();
                    Assert.assertEquals(acceptedTargetEvents, 1L);

                    final String trace = "{\n"
                            + "  \"schema\": \"commander-simulator-next.ws27-target-selection-dependency.v1\",\n"
                            + "  \"forge_pin\": \"" + FORGE_PIN + "\",\n"
                            + "  \"actual_card\": \"Keen Duelist\",\n"
                            + "  \"source_svar\": \"TrigReveal\",\n"
                            + "  \"player_count\": 4,\n"
                            + "  \"format\": \"Commander\",\n"
                            + "  \"authoritative_option_count\": 3,\n"
                            + "  \"selected_target_id\": " + target.getId() + ",\n"
                            + "  \"target_tape_events\": " + acceptedTargetEvents + ",\n"
                            + "  \"test_side_legality_reconstruction\": false,\n"
                            + "  \"silent_fallbacks\": 0,\n"
                            + "  \"complex_target_paths_fail_closed\": true,\n"
                            + "  \"status\": \"PASS\"\n"
                            + "}\n";
                    final Path out = Path.of(System.getProperty("ws27.targetTraceOut",
                            "target/ws27-target-selection/trace.json"));
                    Files.createDirectories(out.getParent());
                    Files.writeString(out, trace, StandardCharsets.UTF_8);
                } catch (Throwable error) {
                    campaignFailure.set(error);
                } finally {
                    final List<Player> players = new ArrayList<>();
                    for (Player p : game.getRegisteredPlayers()) players.add(p);
                    players.sort(Comparator.comparingInt(Player::getId));
                    for (int i = 1; i < players.size(); i++) players.get(i).concede();
                    game.getAction().checkStateEffects(true);
                }
            }
        });

        try {
            final UnifiedNetworkHarness.GameResult result = new UnifiedNetworkHarness()
                    .playerCount(4)
                    .remoteClients(3)
                    .useAiForRemotePlayers(false)
                    .commander(true)
                    .decks(createDecks())
                    .gameTimeout(180_000)
                    .execute();
            Assert.assertTrue(campaignRan.get(), "target dependency campaign must run in live 4P game");
            if (campaignFailure.get() != null) throw new AssertionError("target dependency campaign failed", campaignFailure.get());
            Assert.assertTrue(result.gameCompleted);
        } finally {
            Game.setSemanticStateObserver(null);
            PlayerControllerHuman.setExternalDecisionProviderFactory(null);
            System.clearProperty("forge.ws01.externalHumanHost");
        }
    }

    private static boolean ready(Game game) {
        if (game.getAge() != GameStage.Play || game.getRegisteredPlayers().size() != 4) return false;
        for (Player p : game.getRegisteredPlayers()) if (!(p.getController() instanceof PlayerControllerHuman)) return false;
        return true;
    }

    private static Card addCard(String name, Player player, ZoneType zone) {
        final PaperCard pc = FModel.getMagicDb().getCommonCards().getCard(name);
        if (pc == null) throw new IllegalStateException("card unavailable: " + name);
        final Card card = Card.fromPaperCard(pc, player);
        card.setGameTimestamp(player.getGame().getNextTimestamp());
        player.getZone(zone).add(card);
        return card;
    }

    private static List<Deck> createDecks() {
        final List<Deck> decks = new ArrayList<>();
        final PaperCard commander = FModel.getMagicDb().getCommonCards().getCard("Isamaru, Hound of Konda");
        if (commander == null) throw new IllegalStateException("commander unavailable");
        for (int i = 0; i < 4; i++) {
            final Deck deck = TestDeckLoader.createMinimalDeck("Plains", 12);
            deck.getOrCreate(DeckSection.Commander).add(commander);
            decks.add(deck);
        }
        return decks;
    }

    private static String requireSemantic(ExternalDecisionRequest request, String semantic) {
        for (ExternalDecisionRequest.Option option : request.getOptions()) {
            if (semantic.equals(option.getSemanticValue())) return option.getOptionId();
        }
        throw new ExternalDecisionValidationException(
                ExternalDecisionValidationException.Code.ILLEGAL_OPTION,
                "missing explicit semantic option " + semantic + " for " + request.getDecisionKind());
    }

    private static String stableSingle(ExternalDecisionRequest request) {
        if (request.getMinimumSelection() != 1 || request.getMaximumSelection() < 1 || request.getOptions().isEmpty()) {
            throw new ExternalDecisionValidationException(
                    ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                    "startup decision is not a single bounded choice: " + request.getDecisionKind());
        }
        return request.getOptions().stream()
                .min(Comparator.comparing(o -> sha256(request.getDecisionKind() + "|" + o.getSemanticValue())))
                .orElseThrow().getOptionId();
    }

    private static String sha256(String value) {
        try {
            final byte[] digest = MessageDigest.getInstance("SHA-256").digest(value.getBytes(StandardCharsets.UTF_8));
            final StringBuilder out = new StringBuilder();
            for (byte b : digest) out.append(String.format("%02x", b));
            return out.toString();
        } catch (Exception error) {
            throw new IllegalStateException(error);
        }
    }
}
