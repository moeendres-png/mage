package forge.net;

import forge.game.GameView;
import forge.game.card.CardView;
import forge.game.player.PlayerView;
import forge.game.zone.ZoneType;
import forge.gamemodes.match.input.ExternalDecisionRequest;
import forge.gamemodes.match.input.ExternalDecisionTape;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicLong;

/** WS05-only adversarial observer. It receives only already-decoded client views and strict requests. */
public final class Ws05HiddenInfoProbe {
    private Ws05HiddenInfoProbe() {}

    private static final Set<ZoneType> SCANNED_ZONES = Collections.unmodifiableSet(new LinkedHashSet<>(Arrays.asList(
            ZoneType.Hand, ZoneType.Library, ZoneType.Exile, ZoneType.Sideboard,
            ZoneType.Battlefield, ZoneType.Command, ZoneType.PlanarDeck,
            ZoneType.AttractionDeck, ZoneType.ContraptionDeck)));

    private static final AtomicLong transportLeaks = new AtomicLong();
    private static final AtomicLong crossPrincipalDecisionLeaks = new AtomicLong();
    private static final AtomicLong decisionPayloadLeaks = new AtomicLong();
    private static final AtomicLong replayLeaks = new AtomicLong();
    private static final AtomicLong logLeaks = new AtomicLong();
    private static final AtomicLong exceptionLeaks = new AtomicLong();
    private static final AtomicLong debugLeaks = new AtomicLong();
    private static final AtomicLong identityBearingIdHashLeaks = new AtomicLong();
    private static final AtomicLong faceDownHiddenSamples = new AtomicLong();
    private static final AtomicLong decodedTransportSamples = new AtomicLong();
    private static final AtomicLong decisionRequests = new AtomicLong();
    private static final AtomicLong replayEvents = new AtomicLong();

    private static final Set<String> seenClients = ConcurrentHashMap.newKeySet();
    private static final Map<String, AtomicLong> principalRequestCounts = new ConcurrentHashMap<>();
    private static final Map<String, AtomicLong> phaseSamples = new ConcurrentHashMap<>();
    private static final Map<String, AtomicLong> phaseMismatches = new ConcurrentHashMap<>();
    private static final List<String> bufferedDecisionPayloads = new CopyOnWriteArrayList<>();
    private static final List<String> bufferedReplayPayloads = new CopyOnWriteArrayList<>();
    private static final List<String> leakExamples = new CopyOnWriteArrayList<>();

    private static volatile String phase = "BOOT";
    private static volatile int phaseTargetId = -1;
    private static volatile Set<String> expectedVisibleClients = Collections.emptySet();
    private static volatile String secretName;
    private static volatile String secretDigest;

    public static void reset() {
        transportLeaks.set(0); crossPrincipalDecisionLeaks.set(0); decisionPayloadLeaks.set(0);
        replayLeaks.set(0); logLeaks.set(0); exceptionLeaks.set(0); debugLeaks.set(0);
        identityBearingIdHashLeaks.set(0); faceDownHiddenSamples.set(0); decodedTransportSamples.set(0);
        decisionRequests.set(0); replayEvents.set(0);
        seenClients.clear(); principalRequestCounts.clear(); phaseSamples.clear(); phaseMismatches.clear();
        bufferedDecisionPayloads.clear(); bufferedReplayPayloads.clear(); leakExamples.clear();
        phase = "BOOT"; phaseTargetId = -1; expectedVisibleClients = Collections.emptySet();
        secretName = null; secretDigest = null;
    }

    public static void registerSecret(final String value) {
        if (value == null || value.isBlank()) throw new IllegalArgumentException("secret identity required");
        secretName = value;
        secretDigest = sha256(value);
        for (String payload : bufferedDecisionPayloads) scanPrivatePayload(payload, decisionPayloadLeaks, "decision");
        for (String payload : bufferedReplayPayloads) scanPrivatePayload(payload, replayLeaks, "replay");
    }

    public static void setPhase(final String newPhase, final int targetId, final Set<String> visibleClients) {
        phase = newPhase;
        phaseTargetId = targetId;
        expectedVisibleClients = Collections.unmodifiableSet(new LinkedHashSet<>(visibleClients));
    }

    public static boolean awaitRemoteClients(final int expected, final long timeoutMs) throws InterruptedException {
        long deadline = System.nanoTime() + TimeUnit.MILLISECONDS.toNanos(timeoutMs);
        while (System.nanoTime() < deadline) {
            if (seenClients.size() >= expected) return true;
            Thread.sleep(50L);
        }
        return seenClients.size() >= expected;
    }

    public static void observeDecision(final String boundPrincipalName, final int boundPrincipalId,
                                       final ExternalDecisionRequest request) {
        if (request == null) {
            crossPrincipalDecisionLeaks.incrementAndGet();
            example("null request delivered to principal=" + boundPrincipalName);
            return;
        }
        decisionRequests.incrementAndGet();
        principalRequestCounts.computeIfAbsent(boundPrincipalName, ignored -> new AtomicLong()).incrementAndGet();
        if (request.getPrincipalId() != boundPrincipalId) {
            crossPrincipalDecisionLeaks.incrementAndGet();
            example("request principal mismatch bound=" + boundPrincipalId + " request=" + request.getPrincipalId());
        }
        StringBuilder payload = new StringBuilder();
        payload.append(request.getDecisionKind()).append('|').append(request.getActorId()).append('|')
                .append(request.getPrincipalId()).append('|').append(request.getVisibilityScope()).append('|')
                .append(request.getResponseSchema());
        for (ExternalDecisionRequest.Option option : request.getOptions()) {
            payload.append('|').append(option.getOptionId()).append('|').append(option.getEntityKind())
                    .append('|').append(option.getSemanticValue());
        }
        for (Map.Entry<String, String> entry : request.getConstraints().entrySet()) {
            payload.append('|').append(entry.getKey()).append('=').append(entry.getValue());
        }
        for (Map.Entry<String, String> entry : request.getSemanticContext().entrySet()) {
            payload.append('|').append(entry.getKey()).append('=').append(entry.getValue());
        }
        String serialized = payload.toString();
        bufferedDecisionPayloads.add(serialized);
        scanPrivatePayload(serialized, decisionPayloadLeaks, "decision");
        scanIdentityBearingToken(serialized);
    }

    public static void observeReplay(final ExternalDecisionTape.Event event) {
        if (event == null) return;
        replayEvents.incrementAndGet();
        String payload = event.getEventId() + "|" + event.getDecisionId() + "|" + event.getToken() + "|"
                + event.getDecisionKind() + "|" + event.getActorId() + "|" + event.getPrincipalId() + "|"
                + event.getResponseStatus() + "|" + event.getSelectedOptionIds() + "|" + event.getErrorCode();
        bufferedReplayPayloads.add(payload);
        scanPrivatePayload(payload, replayLeaks, "replay");
        scanIdentityBearingToken(payload);
    }

    public static void observeException(final Throwable error) {
        if (error == null) return;
        String payload = error.getClass().getName() + ":" + String.valueOf(error.getMessage());
        scanPrivatePayload(payload, exceptionLeaks, "exception");
        scanIdentityBearingToken(payload);
    }

    public static void observe(final String clientName, final GameView gameView, final String source) {
        if (clientName == null || gameView == null || gameView.getPlayers() == null) return;
        seenClients.add(clientName);
        PlayerView viewer = null;
        for (PlayerView candidate : gameView.getPlayers()) {
            if (clientName.equals(candidate.getName())) { viewer = candidate; break; }
        }
        if (viewer == null) return;
        decodedTransportSamples.incrementAndGet();

        for (PlayerView owner : gameView.getPlayers()) {
            for (ZoneType zone : SCANNED_ZONES) {
                try {
                    Iterable<CardView> cards = owner.getCards(zone);
                    if (cards == null) continue;
                    for (CardView card : cards) {
                        if (card == null) continue;
                        boolean authorized = authorized(card, viewer);
                        boolean identity = identityBearing(card);
                        if (!authorized && identity) {
                            transportLeaks.incrementAndGet();
                            example("transport:" + source + ":client=" + clientName + ":zone=" + zone + ":phase=" + phase);
                        }
                        if (card.isFaceDown() && !authorized) faceDownHiddenSamples.incrementAndGet();
                        if (!authorized) {
                            String rendered = String.valueOf(card);
                            if (containsSecret(rendered)) {
                                debugLeaks.incrementAndGet();
                                example("debug-string:" + source + ":client=" + clientName + ":phase=" + phase);
                            }
                            String logPayload = source + "|client=" + clientName + "|owner=" + owner.getName()
                                    + "|zone=" + zone + "|card=" + rendered;
                            if (containsSecret(logPayload)) {
                                logLeaks.incrementAndGet();
                                example("principal-log:" + source + ":client=" + clientName + ":phase=" + phase);
                            }
                        }
                        if (card.getId() == phaseTargetId) {
                            String key = phase + "|" + clientName;
                            phaseSamples.computeIfAbsent(key, ignored -> new AtomicLong()).incrementAndGet();
                            boolean expected = expectedVisibleClients.contains(clientName);
                            if (identity != expected) {
                                phaseMismatches.computeIfAbsent(key, ignored -> new AtomicLong()).incrementAndGet();
                                example("lifecycle:" + key + ":expectedIdentity=" + expected + ":actual=" + identity);
                            }
                        }
                    }
                } catch (RuntimeException ignored) {
                    // Some variant zones are absent for ordinary players; absence is not a visibility result.
                }
            }
        }
    }

    private static boolean authorized(final CardView card, final PlayerView viewer) {
        try {
            return card.canBeShownTo(viewer) && card.canFaceDownBeShownTo(viewer);
        } catch (RuntimeException error) {
            return false;
        }
    }

    private static boolean identityBearing(final CardView card) {
        if (meaningful(card.getName(), "Card", "Face Down Card", "Face-down card")) return true;
        if (meaningful(card.getOracleName())) return true;
        try {
            CardView.CardStateView state = card.getCurrentState();
            if (state != null) {
                if (meaningful(state.getName(), "Card", "Face Down Card", "Face-down card")) return true;
                if (meaningful(state.getOracleName())) return true;
                if (meaningful(state.getTrackableImageKey())) return true;
                if (meaningful(state.getOracleText())) return true;
                if (meaningful(state.getRulesText())) return true;
            }
        } catch (RuntimeException ignored) { }
        return false;
    }

    private static boolean meaningful(final String value, final String... neutral) {
        if (value == null || value.isBlank()) return false;
        for (String n : neutral) if (value.equalsIgnoreCase(n)) return false;
        return true;
    }

    private static void scanPrivatePayload(final String payload, final AtomicLong counter, final String surface) {
        if (containsSecret(payload)) {
            counter.incrementAndGet();
            example(surface + ":secret semantic identity present");
        }
    }

    private static void scanIdentityBearingToken(final String payload) {
        String digest = secretDigest;
        if (digest != null && payload != null && payload.contains(digest)) {
            identityBearingIdHashLeaks.incrementAndGet();
            example("identity-bearing-hash present");
        }
    }

    private static boolean containsSecret(final String payload) {
        if (payload == null) return false;
        String secret = secretName;
        String digest = secretDigest;
        return (secret != null && payload.contains(secret)) || (digest != null && payload.contains(digest));
    }

    private static String sha256(final String value) {
        try {
            byte[] digest = MessageDigest.getInstance("SHA-256").digest(value.getBytes(StandardCharsets.UTF_8));
            StringBuilder out = new StringBuilder();
            for (byte b : digest) out.append(String.format("%02x", b));
            return out.toString();
        } catch (Exception error) {
            throw new IllegalStateException(error);
        }
    }

    private static void example(final String value) {
        if (leakExamples.size() < 40) leakExamples.add(value);
    }

    public static long phaseSampleCount(final String p, final String client) {
        AtomicLong value = phaseSamples.get(p + "|" + client);
        return value == null ? 0 : value.get();
    }

    public static long phaseMismatchCount() {
        long total = 0;
        for (AtomicLong value : phaseMismatches.values()) total += value.get();
        return total;
    }

    public static long pilotVisibleLeaks() {
        return transportLeaks.get() + decisionPayloadLeaks.get() + replayLeaks.get() + logLeaks.get()
                + exceptionLeaks.get() + debugLeaks.get() + identityBearingIdHashLeaks.get();
    }

    public static long crossPrincipalLeaks() { return crossPrincipalDecisionLeaks.get(); }
    public static long faceDownSamples() { return faceDownHiddenSamples.get(); }
    public static long transportSamples() { return decodedTransportSamples.get(); }
    public static long requestCount() { return decisionRequests.get(); }
    public static long replayCount() { return replayEvents.get(); }

    public static void writeEvidence(final Path path, final boolean gameCompleted, final int playerCount,
                                     final String format, final long fullSyncs, final long deltas,
                                     final boolean lifecycleComplete) throws Exception {
        Map<String, Long> principalCounts = new LinkedHashMap<>();
        List<String> principalKeys = new ArrayList<>(principalRequestCounts.keySet());
        Collections.sort(principalKeys);
        for (String key : principalKeys) principalCounts.put(key, principalRequestCounts.get(key).get());
        Map<String, Long> samples = new LinkedHashMap<>();
        List<String> sampleKeys = new ArrayList<>(phaseSamples.keySet());
        Collections.sort(sampleKeys);
        for (String key : sampleKeys) samples.put(key, phaseSamples.get(key).get());

        boolean pass = gameCompleted && playerCount == 4 && "Commander".equals(format)
                && fullSyncs > 0 && deltas > 0 && lifecycleComplete
                && pilotVisibleLeaks() == 0 && crossPrincipalLeaks() == 0
                && phaseMismatchCount() == 0 && faceDownSamples() > 0
                && transportSamples() > 0 && requestCount() > 0 && replayCount() > 0
                && principalCounts.size() == 4 && principalCounts.values().stream().allMatch(v -> v > 0);

        String json = "{\n"
                + "  \"schema\": \"commander-simulator-next.ws05-hidden-info-runtime.v1\",\n"
                + "  \"status\": \"" + (pass ? "PASS" : "FAIL") + "\",\n"
                + "  \"player_count\": " + playerCount + ",\n"
                + "  \"format\": \"" + escape(format) + "\",\n"
                + "  \"game_completed\": " + gameCompleted + ",\n"
                + "  \"full_state_syncs\": " + fullSyncs + ",\n"
                + "  \"delta_packets\": " + deltas + ",\n"
                + "  \"decoded_transport_samples\": " + transportSamples() + ",\n"
                + "  \"decision_requests\": " + requestCount() + ",\n"
                + "  \"replay_events\": " + replayCount() + ",\n"
                + "  \"face_down_hidden_samples\": " + faceDownSamples() + ",\n"
                + "  \"pilot_visible_hidden_info_leaks\": " + pilotVisibleLeaks() + ",\n"
                + "  \"cross_principal_decision_leaks\": " + crossPrincipalLeaks() + ",\n"
                + "  \"transport_leaks\": " + transportLeaks.get() + ",\n"
                + "  \"decision_payload_leaks\": " + decisionPayloadLeaks.get() + ",\n"
                + "  \"replay_surface_leaks\": " + replayLeaks.get() + ",\n"
                + "  \"log_surface_leaks\": " + logLeaks.get() + ",\n"
                + "  \"exception_surface_leaks\": " + exceptionLeaks.get() + ",\n"
                + "  \"debug_surface_leaks\": " + debugLeaks.get() + ",\n"
                + "  \"identity_bearing_id_hash_leaks\": " + identityBearingIdHashLeaks.get() + ",\n"
                + "  \"lifecycle_mismatches\": " + phaseMismatchCount() + ",\n"
                + "  \"lifecycle_complete\": " + lifecycleComplete + ",\n"
                + "  \"principal_request_counts\": " + mapJson(principalCounts) + ",\n"
                + "  \"phase_samples\": " + mapJson(samples) + ",\n"
                + "  \"secret_material_emitted\": false\n"
                + "}\n";
        Files.createDirectories(path.getParent());
        Files.writeString(path, json, StandardCharsets.UTF_8);
    }

    private static String mapJson(final Map<String, Long> map) {
        StringBuilder out = new StringBuilder("{");
        boolean first = true;
        for (Map.Entry<String, Long> entry : map.entrySet()) {
            if (!first) out.append(',');
            first = false;
            out.append('\"').append(escape(entry.getKey())).append("\":").append(entry.getValue());
        }
        return out.append('}').toString();
    }

    private static String escape(final String value) {
        if (value == null) return "";
        return value.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n");
    }
}
