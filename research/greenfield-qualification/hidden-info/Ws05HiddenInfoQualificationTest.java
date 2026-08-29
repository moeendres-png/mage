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
import java.util.concurrent.TimeUnit;

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
                for (int j = 0; j < 8; j++) deck.getMain().add(canary);
            }
            deck.getOrCreate(DeckSection.Commander).add(commander);
            decks.add(deck);
        }
        return decks;
    }

    /**
     * Runs the complete visibility lifecycle atomically inside the first real
     * PRIORITY_ACTION boundary. The game thread owns every mutation. After each
     * server-side projection flush, it waits only for the three independent
     * network client observers to confirm receipt before applying the next
     * mutation. Normal game actions therefore cannot move/copy the canary
     * between lifecycle states and invalidate the test subject.
     */
    private static final class VisibilityLifecycle {
        private static final long PHASE_TIMEOUT_MS = 10000L;

        private final Path secretPath;
        private int stage;
        private Throwable failure;
        private Game game;
        private Player owner;
        private Player bob;
        private Player charlie;
        private Player diana;
        private Card target;

        private VisibilityLifecycle(final Path secretPath) {
            this.secretPath = secretPath;
        }

        private synchronized void onAuthoritativeDecisionBoundary(final ExternalDecisionRequest request) {
            if (failure != null || stage != 0) return;
            if (request == null || !"PRIORITY_ACTION".equals(request.getDecisionKind())) return;
            stage = 1;
            try {
                HostedMatch match = HeadlessGuiDesktop.getLastMatch();
                if (match == null || match.getGame() == null || match.getGame().getPlayers().size() != 4) {
                    throw new IllegalStateException("4P hosted game unavailable at first priority boundary");
                }
                game = match.getGame();
                owner = findPlayer(game, "Alice");
                bob = findPlayer(game, "Bob");
                charlie = findPlayer(game, "Charlie");
                diana = findPlayer(game, "Diana");
                target = findCanaryInLibrary(owner);

                Files.createDirectories(secretPath.getParent());
                Files.writeString(secretPath, target.getName(), StandardCharsets.UTF_8);
                Ws05HiddenInfoProbe.registerSecret(target.getName());

                establishAndAwait("HIDDEN_BASE", NONE);

                transition();
                target.addMayLookTemp(bob);
                establishAndAwait("PRIVATE_LOOK", Set.of(BOB));

                transition();
                target.removeMayLookTemp(bob);
                establishAndAwait("HIDDEN_AFTER_LOOK", NONE);

                transition();
                final long revealTimestamp = game.getNextTimestamp();
                target.addMayLookAt(revealTimestamp, game.getPlayers());
                establishAndAwait("PUBLIC_REVEAL", Set.of(BOB, CHARLIE, DIANA));

                transition();
                target.removeMayLookAt(revealTimestamp);
                establishAndAwait("HIDDEN_AFTER_REVEAL", NONE);

                transition();
                target.addMayLookTemp(charlie);
                establishAndAwait("PRIVATE_SEARCH", Set.of(CHARLIE));

                transition();
                target.removeMayLookTemp(charlie);
                establishAndAwait("HIDDEN_AFTER_SEARCH", NONE);

                transition();
                target.addMayLookTemp(diana);
                establishAndAwait("KNOWN_TOP", Set.of(DIANA));

                transition();
                target.removeMayLookTemp(diana);
                establishAndAwait("HIDDEN_AFTER_KNOWN_TOP", NONE);

                transition();
                if (!target.turnFaceDown(true)) {
                    throw new IllegalStateException("failed to turn qualification card face down");
                }
                Card moved = game.getAction().moveToPlay(target, owner, null, null);
                if (moved == null || !moved.isInZone(ZoneType.Battlefield) || !moved.isFaceDown()) {
                    throw new IllegalStateException("face-down battlefield setup did not persist");
                }
                target = moved;
                establishAndAwait("FACE_DOWN_BATTLEFIELD", NONE);

                Ws05HiddenInfoProbe.setPhase("COMPLETE", -1, NONE);
                stage = -1;
            } catch (Throwable error) {
                failure = error;
                Ws05HiddenInfoProbe.observeException(error);
                Ws05HiddenInfoProbe.setPhase("FAILED", -1, NONE);
                stage = -1;
            }
        }

        private void transition() {
            Ws05HiddenInfoProbe.setPhase("TRANSITION", -1, NONE);
        }

        private void establishAndAwait(final String phase, final Set<String> visibleClients) throws InterruptedException {
            Ws05HiddenInfoProbe.setPhase(phase, target.getId(), visibleClients);
            flushPrincipalViews();
            final long deadline = System.nanoTime() + TimeUnit.MILLISECONDS.toNanos(PHASE_TIMEOUT_MS);
            while (System.nanoTime() < deadline) {
                if (phaseObserved(phase)) return;
                Thread.sleep(10L);
            }
            throw new IllegalStateException("principal views did not observe lifecycle phase " + phase);
        }

        private void flushPrincipalViews() {
            final FServerManager server = FServerManager.getInstance();
            for (int slot = 1; slot <= 3; slot++) {
                final RemoteClient client = server.getClientBySlotIndex(slot);
                if (client == null || client.getGui() == null) {
                    throw new IllegalStateException("remote principal projection unavailable for slot " + slot);
                }
                client.getGui().updateGameView();
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
