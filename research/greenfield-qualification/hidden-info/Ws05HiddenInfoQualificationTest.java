package forge.net;

import forge.deck.Deck;
import forge.deck.DeckSection;
import forge.game.Game;
import forge.game.card.Card;
import forge.game.player.Player;
import forge.game.zone.ZoneType;
import forge.gamemodes.match.HostedMatch;
import forge.gamemodes.match.input.ExternalDecisionRequest;
import forge.gamemodes.match.input.ExternalDecisionResponse;
import forge.gamemodes.match.input.ExternalDecisionTape;
import forge.gamemodes.match.input.ExternalDecisionValidationException;
import forge.gamemodes.net.server.FServerManager;
import forge.gamemodes.net.server.RemoteClient;
import forge.item.PaperCard;
import forge.model.FModel;
import forge.player.PlayerControllerHuman;
import org.testng.Assert;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Set;

/** Real 4P Commander WS05 campaign over network views and the strict external-pilot boundary. */
public class Ws05HiddenInfoQualificationTest {
    private static final String BOB = "Bob (Remote)";
    private static final String CHARLIE = "Charlie (Remote)";
    private static final String DIANA = "Diana (Remote)";
    private static final String HIDDEN_CANARY = "Elite Vanguard";
    private static final Set<String> NONE = Collections.emptySet();

    @BeforeClass
    public static void setUp() {
        TestUtils.ensureFModelInitialized();
    }

    @Test(timeOut = 300000)
    public void fourPlayerPrincipalScopedHiddenInformationBoundary() throws Exception {
        final Path evidence = Path.of(System.getProperty("ws05.evidencePath"));
        final Path secretPath = Path.of(System.getProperty("ws05.secretPath"));
        final VisibilityLifecycle lifecycle = new VisibilityLifecycle(secretPath);

        Ws05HiddenInfoProbe.reset();
        System.setProperty("forge.ws01.externalHumanHost", "true");
        ExternalDecisionTape.setEventObserver(Ws05HiddenInfoProbe::observeReplay);
        PlayerControllerHuman.setExternalDecisionProviderFactory(player -> request -> {
            Ws05HiddenInfoProbe.observeDecision(player.getName(), player.getId(), request);
            lifecycle.onAuthoritativeDecisionBoundary(request);
            return decide(request);
        });

        UnifiedNetworkHarness.GameResult result = null;
        try {
            result = new UnifiedNetworkHarness()
                    .playerCount(4)
                    .remoteClients(3)
                    .useAiForRemotePlayers(false)
                    .commander(true)
                    .decks(createQualificationDecks())
                    .connectionTimeout(45000)
                    .gameTimeout(180000)
                    .execute();
        } finally {
            PlayerControllerHuman.setExternalDecisionProviderFactory(null);
            ExternalDecisionTape.setEventObserver(null);
        }

        if (result == null) throw new IllegalStateException("network harness returned no result");
        final boolean coverage = requiredLifecycleCoverage();
        Ws05HiddenInfoProbe.writeEvidence(
                evidence, result.gameCompleted, result.playerCount, result.gameFormat,
                result.fullStateSyncsReceived, result.deltaPacketsReceived, coverage);

        if (lifecycle.failure() != null) {
            throw new AssertionError("WS05 lifecycle exercise failed", lifecycle.failure());
        }
        Assert.assertTrue(result.passed(), "4P Commander network game must complete: " + result.toSummary());
        Assert.assertTrue(coverage, "all principal/lifecycle phase observations must be present");
        Assert.assertEquals(Ws05HiddenInfoProbe.pilotVisibleLeaks(), 0L, "pilot-visible hidden identity leak");
        Assert.assertEquals(Ws05HiddenInfoProbe.crossPrincipalLeaks(), 0L, "cross-principal DecisionRequest leak");
        Assert.assertEquals(Ws05HiddenInfoProbe.phaseMismatchCount(), 0L, "look/reveal lifecycle mismatch");
        Assert.assertTrue(Ws05HiddenInfoProbe.faceDownSamples() > 0, "face-down hidden transport not exercised");
        Assert.assertTrue(Ws05HiddenInfoProbe.requestCount() > 0, "strict DecisionRequest path not exercised");
        Assert.assertTrue(Ws05HiddenInfoProbe.replayCount() > 0, "replay-facing DecisionTape not exercised");

        exceptionSurfaceContract();
        System.out.println("WS05_PILOT_VISIBLE_HIDDEN_INFO_LEAKS=0");
        System.out.println("WS05_CROSS_PRINCIPAL_DECISION_LEAKS=0");
        System.out.println("WS05_LOOK_REVEAL_LIFECYCLE=PASS");
        System.out.println("WS05_SECRET_CHOICE_EXCEPTION=PASS");
        System.out.println("WS05_HIDDEN_INFO=PASS");
    }

    private static ExternalDecisionResponse decide(final ExternalDecisionRequest request) {
        final List<String> selected = new ArrayList<>();
        switch (request.getDecisionKind()) {
            case "MULLIGAN" -> selected.add(requireSemantic(request, "true"));
            case "PRIORITY_ACTION" -> selected.add(requireSemantic(request, "PASS_PRIORITY"));
            case "STARTING_PLAYER", "STARTING_HAND" -> selected.add(lowestOptionId(request));
            case "MAX_HAND_SIZE_DISCARD" -> selectLowestExact(request, selected);
            case "DECLARE_ATTACKERS", "DECLARE_BLOCKERS" -> selected.add(requireSemantic(request, "DONE"));
            default -> throw new ExternalDecisionValidationException(
                    ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                    "WS05 pilot has no explicit policy for " + request.getDecisionKind());
        }
        return new ExternalDecisionResponse(
                request.getDecisionId(), request.getToken(), request.getActorId(), request.getPrincipalId(),
                request.getResponseSchema(), selected, false);
    }

    private static String requireSemantic(final ExternalDecisionRequest request, final String semantic) {
        for (ExternalDecisionRequest.Option option : request.getOptions()) {
            if (semantic.equals(option.getSemanticValue())) return option.getOptionId();
        }
        throw new ExternalDecisionValidationException(
                ExternalDecisionValidationException.Code.ILLEGAL_OPTION,
                "authoritative option missing for " + request.getDecisionKind());
    }

    private static String lowestOptionId(final ExternalDecisionRequest request) {
        String best = null;
        for (ExternalDecisionRequest.Option option : request.getOptions()) {
            if (best == null || option.getOptionId().compareTo(best) < 0) best = option.getOptionId();
        }
        if (best == null) throw new ExternalDecisionValidationException(
                ExternalDecisionValidationException.Code.ILLEGAL_OPTION,
                "authoritative option set empty for " + request.getDecisionKind());
        return best;
    }

    private static void selectLowestExact(final ExternalDecisionRequest request, final List<String> selected) {
        final List<ExternalDecisionRequest.Option> ordered = new ArrayList<>(request.getOptions());
        ordered.sort(java.util.Comparator.comparing(ExternalDecisionRequest.Option::getOptionId));
        final int count = request.getMinimumSelection();
        if (count < 0 || count > ordered.size() || count != request.getMaximumSelection()) {
            throw new ExternalDecisionValidationException(
                    ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                    "WS05 qualification policy requires exact cardinality for " + request.getDecisionKind());
        }
        for (int i = 0; i < count; i++) selected.add(ordered.get(i).getOptionId());
    }

    private static List<Deck> createQualificationDecks() {
        final List<Deck> decks = new ArrayList<>();
        final PaperCard commander = FModel.getMagicDb().getCommonCards().getCard("Isamaru, Hound of Konda");
        final PaperCard canary = FModel.getMagicDb().getCommonCards().getCard(HIDDEN_CANARY);
        if (commander == null) throw new IllegalStateException("qualification commander card is unavailable");
        if (canary == null) throw new IllegalStateException("hidden-information canary card is unavailable");
        for (int i = 0; i < 4; i++) {
            final Deck deck = TestDeckLoader.createMinimalDeck("Plains", i == 0 ? 12 : 20);
            if (i == 0) {
                // Eight copies guarantee at least one canary remains in the library after a seven-card opening hand.
                for (int j = 0; j < 8; j++) deck.getMain().add(canary);
            }
            deck.getOrCreate(DeckSection.Commander).add(commander);
            decks.add(deck);
        }
        return decks;
    }

    /**
     * Drives every visibility mutation from the same synchronous Decision boundary used by the game loop.
     * The canary is bound only after the first real priority decision, after opening-hand/mulligan zone churn,
     * so every subsequent permission mutation targets the authoritative live Card instance rather than a stale
     * zone-change copy with the same card id. A TRANSITION phase suppresses observations while a visibility
     * mutation is in flight; only a fully established before/after projection is adjudicated.
     */
    private static final class VisibilityLifecycle {
        private final Path secretPath;
        private int stage;
        private Throwable failure;
        private Game game;
        private Player owner;
        private Player bob;
        private Player charlie;
        private Player diana;
        private Card target;
        private long revealTimestamp;

        private VisibilityLifecycle(final Path secretPath) {
            this.secretPath = secretPath;
        }

        private synchronized void onAuthoritativeDecisionBoundary(final ExternalDecisionRequest request) {
            if (failure != null || stage < 0) return;
            try {
                if (stage == 0) {
                    if (request == null || !"PRIORITY_ACTION".equals(request.getDecisionKind())) return;
                    HostedMatch match = HeadlessGuiDesktop.getLastMatch();
                    if (match == null || match.getGame() == null || match.getGame().getPlayers().size() != 4) return;
                    game = match.getGame();
                    owner = findPlayer(game, "Alice");
                    bob = findPlayer(game, "Bob");
                    charlie = findPlayer(game, "Charlie");
                    diana = findPlayer(game, "Diana");
                    target = findCanaryInLibrary(owner);
                    Files.createDirectories(secretPath.getParent());
                    Files.writeString(secretPath, target.getName(), StandardCharsets.UTF_8);
                    Ws05HiddenInfoProbe.registerSecret(target.getName());
                    establish("HIDDEN_BASE", NONE);
                    stage = 1;
                    return;
                }

                if (stage == 1 && phaseObserved("HIDDEN_BASE")) {
                    transition();
                    target.addMayLookTemp(bob);
                    establish("PRIVATE_LOOK", Set.of(BOB));
                    stage = 2;
                    return;
                }
                if (stage == 2 && phaseObserved("PRIVATE_LOOK")) {
                    transition();
                    target.removeMayLookTemp(bob);
                    establish("HIDDEN_AFTER_LOOK", NONE);
                    stage = 3;
                    return;
                }
                if (stage == 3 && phaseObserved("HIDDEN_AFTER_LOOK")) {
                    transition();
                    revealTimestamp = game.getNextTimestamp();
                    target.addMayLookAt(revealTimestamp, game.getPlayers());
                    establish("PUBLIC_REVEAL", Set.of(BOB, CHARLIE, DIANA));
                    stage = 4;
                    return;
                }
                if (stage == 4 && phaseObserved("PUBLIC_REVEAL")) {
                    transition();
                    target.removeMayLookAt(revealTimestamp);
                    establish("HIDDEN_AFTER_REVEAL", NONE);
                    stage = 5;
                    return;
                }
                if (stage == 5 && phaseObserved("HIDDEN_AFTER_REVEAL")) {
                    transition();
                    target.addMayLookTemp(charlie);
                    establish("PRIVATE_SEARCH", Set.of(CHARLIE));
                    stage = 6;
                    return;
                }
                if (stage == 6 && phaseObserved("PRIVATE_SEARCH")) {
                    transition();
                    target.removeMayLookTemp(charlie);
                    establish("HIDDEN_AFTER_SEARCH", NONE);
                    stage = 7;
                    return;
                }
                if (stage == 7 && phaseObserved("HIDDEN_AFTER_SEARCH")) {
                    transition();
                    target.addMayLookTemp(diana);
                    establish("KNOWN_TOP", Set.of(DIANA));
                    stage = 8;
                    return;
                }
                if (stage == 8 && phaseObserved("KNOWN_TOP")) {
                    transition();
                    target.removeMayLookTemp(diana);
                    establish("HIDDEN_AFTER_KNOWN_TOP", NONE);
                    stage = 9;
                    return;
                }
                if (stage == 9 && phaseObserved("HIDDEN_AFTER_KNOWN_TOP")) {
                    transition();
                    if (!target.turnFaceDown(true)) {
                        throw new IllegalStateException("failed to turn qualification card face down");
                    }
                    Card moved = game.getAction().moveToPlay(target, owner, null, null);
                    if (moved == null || !moved.isInZone(ZoneType.Battlefield) || !moved.isFaceDown()) {
                        throw new IllegalStateException("face-down battlefield setup did not persist");
                    }
                    target = moved;
                    establish("FACE_DOWN_BATTLEFIELD", NONE);
                    stage = 10;
                    return;
                }
                if (stage == 10 && phaseObserved("FACE_DOWN_BATTLEFIELD")) {
                    Ws05HiddenInfoProbe.setPhase("COMPLETE", -1, NONE);
                    stage = -1;
                }
            } catch (Throwable error) {
                failure = error;
                Ws05HiddenInfoProbe.observeException(error);
                Ws05HiddenInfoProbe.setPhase("FAILED", -1, NONE);
            }
        }

        private void transition() {
            Ws05HiddenInfoProbe.setPhase("TRANSITION", -1, NONE);
        }

        private void establish(final String phase, final Set<String> visibleClients) {
            Ws05HiddenInfoProbe.setPhase(phase, target.getId(), visibleClients);
            flushPrincipalViews();
        }

        /**
         * RemoteClientGuiGame.updateGameView() is explicitly the game-thread-only server-side projection sync.
         * Calling it at the authoritative decision boundary makes each lifecycle state observable immediately
         * without sleeps, client-side filtering, or mutation from a second thread.
         */
        private void flushPrincipalViews() {
            final FServerManager server = FServerManager.getInstance();
            for (int slot = 1; slot <= 3; slot++) {
                final RemoteClient client = server.getClientBySlotIndex(slot);
                if (client != null && client.getGui() != null) {
                    client.getGui().updateGameView();
                }
            }
        }

        private Throwable failure() {
            return failure;
        }
    }

    private static Player findPlayer(final Game game, final String prefix) {
        for (Player player : game.getPlayers()) if (player.getName().startsWith(prefix)) return player;
        throw new IllegalStateException("player not found: " + prefix);
    }

    private static Card findCanaryInLibrary(final Player owner) {
        for (Card card : owner.getCardsIn(ZoneType.Library)) {
            if (HIDDEN_CANARY.equals(card.getName())) return card;
        }
        throw new IllegalStateException("hidden canary did not remain in host library");
    }

    private static boolean phaseObserved(final String phase) {
        return Ws05HiddenInfoProbe.phaseSampleCount(phase, BOB) > 0
                && Ws05HiddenInfoProbe.phaseSampleCount(phase, CHARLIE) > 0
                && Ws05HiddenInfoProbe.phaseSampleCount(phase, DIANA) > 0;
    }

    private static boolean requiredLifecycleCoverage() {
        String[] phases = {
                "HIDDEN_BASE", "PRIVATE_LOOK", "HIDDEN_AFTER_LOOK", "PUBLIC_REVEAL",
                "HIDDEN_AFTER_REVEAL", "PRIVATE_SEARCH", "HIDDEN_AFTER_SEARCH", "KNOWN_TOP",
                "HIDDEN_AFTER_KNOWN_TOP", "FACE_DOWN_BATTLEFIELD"
        };
        for (String phase : phases) {
            if (!phaseObserved(phase)) return false;
        }
        return true;
    }

    private static void exceptionSurfaceContract() {
        final String syntheticSecret = "WS05_SYNTHETIC_SECRET_CHOICE_DO_NOT_ECHO";
        ExternalDecisionRequest request = new ExternalDecisionRequest(
                9001L, 9002L, "SECRET_CHOICE", 1, 1,
                ExternalDecisionRequest.VISIBILITY_PRINCIPAL_ONLY,
                List.of(ExternalDecisionRequest.Option.discrete("choice:0", "CHOICE", syntheticSecret)),
                1, 1, false, Collections.emptyMap(),
                ExternalDecisionRequest.DISCRETE_RESPONSE_SCHEMA, Collections.emptyMap());
        ExternalDecisionResponse wrongPrincipal = new ExternalDecisionResponse(
                request.getDecisionId(), request.getToken(), request.getActorId(), 2,
                request.getResponseSchema(), List.of("choice:0"), false);
        try {
            forge.gamemodes.match.input.ExternalDecisionValidator.validate(
                    request, wrongPrincipal, request.getToken(), request.getActorId(), request.getPrincipalId(), false, false);
            Assert.fail("wrong-principal secret choice response must be rejected");
        } catch (ExternalDecisionValidationException expected) {
            Ws05HiddenInfoProbe.observeException(expected);
            Assert.assertFalse(String.valueOf(expected.getMessage()).contains(syntheticSecret),
                    "validation exception echoed secret choice semantics");
        }
    }
}
