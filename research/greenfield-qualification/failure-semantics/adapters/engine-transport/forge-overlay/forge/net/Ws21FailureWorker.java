package forge.net;

import forge.deck.Deck;
import forge.deck.DeckSection;
import forge.game.Ws21EngineFaultInjector;
import forge.gamemodes.match.input.ExternalDecisionRequest;
import forge.gamemodes.match.input.ExternalDecisionResponse;
import forge.gamemodes.match.input.UnifiedOutcome;
import forge.gamemodes.match.input.UnifiedOutcomeCategory;
import forge.gamemodes.match.input.Ws21DecisionCommitProbe;
import forge.item.PaperCard;
import forge.model.FModel;
import forge.player.PlayerControllerHuman;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Properties;

/** One OS process, one real 4P Commander game, one WS21 fault scenario. */
public final class Ws21FailureWorker {
    private static final String PRIVATE_CANARY = "Elite Vanguard";

    private Ws21FailureWorker() { }

    public static void main(final String[] args) throws Exception {
        if (args.length != 5) {
            throw new IllegalArgumentException("usage: <mode> <gameId> <gamePort> <pilotPort> <outDir>");
        }
        final String mode = args[0];
        final String gameId = args[1];
        final int gamePort = Integer.parseInt(args[2]);
        final int pilotPort = Integer.parseInt(args[3]);
        final Path outDir = Path.of(args[4]).toAbsolutePath();
        Files.createDirectories(outDir);

        TestUtils.ensureFModelInitialized();
        Ws21EngineFaultInjector.reset();
        Ws21DecisionCommitProbe.reset();
        Ws21PilotTransport.resetProbe();
        System.setProperty("forge.ws01.externalHumanHost", "true");
        if ("ENGINE".equals(mode)) {
            System.setProperty("ws21.engineFault", "true");
        }

        if ("ENGINE".equals(mode)) {
            PlayerControllerHuman.setExternalDecisionProviderFactory(player -> Ws21FailureWorker::policyDecision);
        } else {
            PlayerControllerHuman.setExternalDecisionProviderFactory(player -> new Ws21PilotTransport("127.0.0.1", pilotPort));
        }

        UnifiedNetworkHarness.GameResult result = null;
        Throwable escaped = null;
        try {
            result = new UnifiedNetworkHarness()
                    .playerCount(4)
                    .remoteClients(3)
                    .useAiForRemotePlayers(false)
                    .commander(true)
                    .decks(createQualificationDecks())
                    .port(gamePort)
                    .connectionTimeout(45_000)
                    .gameTimeout(90_000)
                    .execute();
        } catch (Throwable failure) {
            escaped = failure;
        } finally {
            PlayerControllerHuman.setExternalDecisionProviderFactory(null);
            System.clearProperty("forge.ws01.externalHumanHost");
            System.clearProperty("ws21.engineFault");
        }

        final UnifiedOutcomeCategory category = classify(mode, result, escaped);
        final Long decisionId = Ws21DecisionCommitProbe.lastDecisionId() > 0
                ? Ws21DecisionCommitProbe.lastDecisionId() : null;
        final Integer principalId = Ws21DecisionCommitProbe.lastPrincipalId() >= 0
                ? Ws21DecisionCommitProbe.lastPrincipalId() : null;
        final UnifiedOutcome outcome = UnifiedOutcome.failure(category,
                gameId + ":ws21:" + mode.toLowerCase(), gameId, decisionId, principalId);
        writeEvidence(outDir, mode, gameId, result, outcome);

        final UnifiedOutcomeCategory expected = switch (mode) {
            case "ENGINE" -> UnifiedOutcomeCategory.ENGINE_FAILURE;
            case "TRANSPORT" -> UnifiedOutcomeCategory.TRANSPORT_FAILURE;
            case "MALFORMED_CONTROL" -> UnifiedOutcomeCategory.MALFORMED_RESPONSE;
            default -> throw new IllegalArgumentException("unsupported WS21 mode: " + mode);
        };
        if (category != expected) {
            throw new AssertionError("WS21 expected " + expected + " but classified " + category);
        }
        System.out.println("WS21_WORKER=PASS");
        System.out.println("WS21_MODE=" + mode);
        System.out.println("WS21_CATEGORY=" + category.name());
        System.out.println("WS21_WORKER_PID=" + ProcessHandle.current().pid());
    }

    private static UnifiedOutcomeCategory classify(final String mode,
                                                    final UnifiedNetworkHarness.GameResult result,
                                                    final Throwable escaped) {
        if ("ENGINE".equals(mode)) {
            if (!Ws21EngineFaultInjector.faultFired()) {
                throw new AssertionError("controlled engine fault was never reached", escaped);
            }
            if (Ws21EngineFaultInjector.postFaultBodyReached()) {
                throw new AssertionError("engine continued into GameAction.changeZone after the injected failure", escaped);
            }
            return UnifiedOutcomeCategory.ENGINE_FAILURE;
        }
        if ("TRANSPORT".equals(mode)) {
            if (Ws21PilotTransport.requestsWritten() < 1L
                    || Ws21PilotTransport.responsesDecoded() != 0L
                    || Ws21DecisionCommitProbe.transportPropagated() < 1L
                    || Ws21DecisionCommitProbe.validated() != 0L
                    || Ws21DecisionCommitProbe.applied() != 0L) {
                throw new AssertionError("transport fault did not stop at the actual request/response boundary", escaped);
            }
            return UnifiedOutcomeCategory.TRANSPORT_FAILURE;
        }
        if ("MALFORMED_CONTROL".equals(mode)) {
            if (Ws21PilotTransport.requestsWritten() < 1L
                    || Ws21PilotTransport.responsesDecoded() < 1L
                    || Ws21DecisionCommitProbe.transportPropagated() != 0L
                    || Ws21DecisionCommitProbe.validated() != 0L
                    || Ws21DecisionCommitProbe.applied() != 0L) {
                throw new AssertionError("malformed-response control did not remain distinct from transport failure", escaped);
            }
            return UnifiedOutcomeCategory.MALFORMED_RESPONSE;
        }
        throw new IllegalArgumentException("unsupported WS21 mode: " + mode);
    }

    private static ExternalDecisionResponse policyDecision(final ExternalDecisionRequest request) {
        final List<String> selected = new ArrayList<>();
        switch (request.getDecisionKind()) {
            case "MULLIGAN" -> selected.add(requireSemantic(request, "true"));
            case "PRIORITY_ACTION" -> selected.add(requireSemantic(request, "PASS_PRIORITY"));
            case "STARTING_PLAYER", "STARTING_HAND" -> selected.add(lowestOptionId(request));
            case "MAX_HAND_SIZE_DISCARD" -> selectLowestExact(request, selected);
            case "DECLARE_ATTACKERS", "DECLARE_BLOCKERS" -> selected.add(requireSemantic(request, "DONE"));
            default -> throw new IllegalStateException("unexpected engine-control decision: " + request.getDecisionKind());
        }
        return new ExternalDecisionResponse(request.getDecisionId(), request.getToken(), request.getActorId(),
                request.getPrincipalId(), request.getResponseSchema(), selected, false);
    }

    private static String requireSemantic(final ExternalDecisionRequest request, final String semantic) {
        for (final ExternalDecisionRequest.Option option : request.getOptions()) {
            if (semantic.equals(option.getSemanticValue())) return option.getOptionId();
        }
        throw new IllegalStateException("required semantic option absent");
    }

    private static String lowestOptionId(final ExternalDecisionRequest request) {
        return request.getOptions().stream().map(ExternalDecisionRequest.Option::getOptionId)
                .min(Comparator.naturalOrder()).orElseThrow();
    }

    private static void selectLowestExact(final ExternalDecisionRequest request, final List<String> selected) {
        final List<String> ids = request.getOptions().stream().map(ExternalDecisionRequest.Option::getOptionId)
                .sorted().toList();
        if (request.getMinimumSelection() != request.getMaximumSelection()
                || request.getMinimumSelection() > ids.size()) {
            throw new IllegalStateException("control policy requires exact selection cardinality");
        }
        selected.addAll(ids.subList(0, request.getMinimumSelection()));
    }

    private static List<Deck> createQualificationDecks() {
        final PaperCard commander = FModel.getMagicDb().getCommonCards().getCard("Isamaru, Hound of Konda");
        final PaperCard canary = FModel.getMagicDb().getCommonCards().getCard(PRIVATE_CANARY);
        if (commander == null || canary == null) {
            throw new IllegalStateException("WS21 qualification cards are unavailable");
        }
        final List<Deck> decks = new ArrayList<>();
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

    private static void writeEvidence(final Path outDir, final String mode, final String gameId,
                                      final UnifiedNetworkHarness.GameResult result,
                                      final UnifiedOutcome outcome) throws Exception {
        final long pid = ProcessHandle.current().pid();
        final String outcomeJson = "{"
                + "\"schema\":\"" + escape(UnifiedOutcome.SCHEMA) + "\","
                + "\"category\":\"" + outcome.getCategory().name() + "\","
                + "\"correlation_id\":\"" + escape(outcome.getCorrelationId()) + "\","
                + "\"game_id\":\"" + escape(outcome.getGameId()) + "\","
                + "\"decision_id\":" + nullable(outcome.getDecisionId()) + ","
                + "\"principal_id\":" + nullable(outcome.getPrincipalId()) + ","
                + "\"public_message\":\"" + escape(outcome.getPublicMessage()) + "\","
                + "\"state_committed\":" + outcome.isStateCommitted()
                + "}";
        Files.writeString(outDir.resolve("outcome.json"), outcomeJson + "\n", StandardCharsets.UTF_8);

        final String trace = "{"
                + "\"schema\":\"commander-simulator-next.ws21-fault-trace.v1\","
                + "\"sequence\":1,"
                + "\"mode\":\"" + escape(mode) + "\","
                + "\"game_id\":\"" + escape(gameId) + "\","
                + "\"category\":\"" + outcome.getCategory().name() + "\","
                + "\"worker_pid\":" + pid + ","
                + "\"process_alive_while_reporting\":true,"
                + "\"state_committed\":" + outcome.isStateCommitted() + ","
                + "\"engine_fault_fired\":" + Ws21EngineFaultInjector.faultFired() + ","
                + "\"engine_fault_site\":\"" + escape(Ws21EngineFaultInjector.faultSite()) + "\","
                + "\"post_fault_engine_body_reached\":" + Ws21EngineFaultInjector.postFaultBodyReached() + ","
                + "\"decision_opened\":" + Ws21DecisionCommitProbe.opened() + ","
                + "\"decision_validated\":" + Ws21DecisionCommitProbe.validated() + ","
                + "\"decision_applied\":" + Ws21DecisionCommitProbe.applied() + ","
                + "\"transport_boundary_propagations\":" + Ws21DecisionCommitProbe.transportPropagated() + ","
                + "\"transport_stage\":\"" + escape(Ws21DecisionCommitProbe.lastTransportStage()) + "\","
                + "\"transport_requests_written\":" + Ws21PilotTransport.requestsWritten() + ","
                + "\"transport_responses_decoded\":" + Ws21PilotTransport.responsesDecoded()
                + "}";
        Files.writeString(outDir.resolve("fault-trace.jsonl"), trace + "\n", StandardCharsets.UTF_8);

        final Properties props = new Properties();
        props.setProperty("mode", mode);
        props.setProperty("game_id", gameId);
        props.setProperty("worker_pid", Long.toString(pid));
        props.setProperty("category", outcome.getCategory().name());
        props.setProperty("state_committed", Boolean.toString(outcome.isStateCommitted()));
        props.setProperty("process_alive_while_reporting", "true");
        props.setProperty("engine_fault_fired", Boolean.toString(Ws21EngineFaultInjector.faultFired()));
        props.setProperty("post_fault_engine_body_reached", Boolean.toString(Ws21EngineFaultInjector.postFaultBodyReached()));
        props.setProperty("decision_opened", Long.toString(Ws21DecisionCommitProbe.opened()));
        props.setProperty("decision_validated", Long.toString(Ws21DecisionCommitProbe.validated()));
        props.setProperty("decision_applied", Long.toString(Ws21DecisionCommitProbe.applied()));
        props.setProperty("transport_boundary_propagations", Long.toString(Ws21DecisionCommitProbe.transportPropagated()));
        props.setProperty("transport_requests_written", Long.toString(Ws21PilotTransport.requestsWritten()));
        props.setProperty("transport_responses_decoded", Long.toString(Ws21PilotTransport.responsesDecoded()));
        props.setProperty("game_completed", Boolean.toString(result != null && result.gameCompleted));
        try (var writer = Files.newBufferedWriter(outDir.resolve("summary.properties"), StandardCharsets.UTF_8)) {
            props.store(writer, "WS21 safe failure witness");
        }
    }

    private static String nullable(final Object value) {
        return value == null ? "null" : value.toString();
    }

    private static String escape(final String value) {
        if (value == null) return "";
        return value.replace("\\", "\\\\").replace("\"", "\\\"")
                .replace("\n", "\\n").replace("\r", "\\r");
    }
}
