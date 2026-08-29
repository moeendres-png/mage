package forge.net;

import org.testng.Assert;
import org.testng.annotations.Test;

import java.io.BufferedReader;
import java.io.IOException;
import java.net.ServerSocket;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Properties;
import java.util.Set;
import java.util.concurrent.TimeUnit;

/** Parent qualification process. It never hosts a game itself. */
public final class Ws08ProcessIsolationQualificationTest {
    private static final String ALPHA_GAME = "ws08-alpha-4p";
    private static final String BETA_GAME = "ws08-beta-4p";
    private static final String ALPHA_CANARY = "Elite Vanguard";
    private static final String BETA_CANARY = "Serra Angel";
    private static final String ALPHA_CONTROLLER = "controller-alpha";
    private static final String BETA_CONTROLLER = "controller-beta";

    @Test(timeOut = 900_000)
    public void processIsolationQualification() throws Exception {
        final String configured = System.getProperty("ws08.evidenceDir");
        if (configured == null || configured.isBlank()) {
            throw new IllegalStateException("ws08.evidenceDir is required");
        }
        final Path root = Path.of(configured).toAbsolutePath();
        Files.createDirectories(root);
        final Path workers = root.resolve("workers");
        Files.createDirectories(workers);

        final WorkerProcess alpha = startWorker(root, workers.resolve("alpha"), "alpha", ALPHA_GAME, 111_111L,
                ALPHA_CANARY, BETA_CANARY, ALPHA_CONTROLLER, allocatePort());
        final WorkerProcess beta = startWorker(root, workers.resolve("beta"), "beta", BETA_GAME, 222_222L,
                BETA_CANARY, ALPHA_CANARY, BETA_CONTROLLER, allocatePort());
        final int alphaExit = waitFor(alpha, Duration.ofMinutes(5));
        final int betaExit = waitFor(beta, Duration.ofMinutes(5));

        final Properties a = loadSummary(alpha.outputDir);
        final Properties b = loadSummary(beta.outputDir);
        final List<String> failures = new ArrayList<>();
        verifyWorker("alpha", alphaExit, a, alpha.outputDir, ALPHA_GAME, ALPHA_CANARY, BETA_CANARY, ALPHA_CONTROLLER, failures);
        verifyWorker("beta", betaExit, b, beta.outputDir, BETA_GAME, BETA_CANARY, ALPHA_CANARY, BETA_CONTROLLER, failures);

        final long stateLeaks = occurrences(alpha.outputDir.resolve("states.jsonl"), BETA_CANARY)
                + occurrences(beta.outputDir.resolve("states.jsonl"), ALPHA_CANARY);
        final long rngLeaks = wrongRngScope(alpha.outputDir.resolve("rng.tsv"), ALPHA_GAME)
                + wrongRngScope(beta.outputDir.resolve("rng.tsv"), BETA_GAME);
        final long decisionQueueLeaks = wrongDecisionScope(alpha.outputDir.resolve("decisions.tsv"), ALPHA_GAME, ALPHA_CONTROLLER)
                + wrongDecisionScope(beta.outputDir.resolve("decisions.tsv"), BETA_GAME, BETA_CONTROLLER);
        final long controllerLeaks = wrongController(alpha.outputDir.resolve("decisions.tsv"), ALPHA_CONTROLLER)
                + wrongController(beta.outputDir.resolve("decisions.tsv"), BETA_CONTROLLER);
        final Set<String> alphaRequestIds = scopedRequestIds(alpha.outputDir.resolve("decisions.tsv"));
        final Set<String> betaRequestIds = scopedRequestIds(beta.outputDir.resolve("decisions.tsv"));
        final Set<String> requestIntersection = new HashSet<>(alphaRequestIds);
        requestIntersection.retainAll(betaRequestIds);
        final Set<String> rawAlphaIds = rawDecisionIds(alpha.outputDir.resolve("decisions.tsv"));
        final Set<String> rawBetaIds = rawDecisionIds(beta.outputDir.resolve("decisions.tsv"));
        final Set<String> rawIntersection = new HashSet<>(rawAlphaIds);
        rawIntersection.retainAll(rawBetaIds);
        final long observationLeaks = longProp(a, "cross_game_observation_leaks") + longProp(b, "cross_game_observation_leaks");
        final boolean distinctPids = longProp(a, "pid") != longProp(b, "pid");
        final boolean parallelOverlap = alpha.startNanos < beta.endNanos && beta.startNanos < alpha.endNanos;
        final boolean distinctStateIdentity = !prop(a, "states_sha256").equals(prop(b, "states_sha256"));
        final boolean distinctRngIdentity = !prop(a, "rng_sha256").equals(prop(b, "rng_sha256"));
        final boolean distinctDecisionIdentity = !prop(a, "decisions_sha256").equals(prop(b, "decisions_sha256"));

        check(stateLeaks == 0, "cross-game state sentinel leak count=" + stateLeaks, failures);
        check(rngLeaks == 0, "cross-game RNG scope leak count=" + rngLeaks, failures);
        check(decisionQueueLeaks == 0, "cross-game decision queue leak count=" + decisionQueueLeaks, failures);
        check(requestIntersection.isEmpty(), "cross-game scoped request-id collisions=" + requestIntersection.size(), failures);
        check(observationLeaks == 0, "cross-game principal observation leak count=" + observationLeaks, failures);
        check(controllerLeaks == 0, "cross-game controller tag leak count=" + controllerLeaks, failures);
        check(distinctPids, "parallel workers did not have distinct OS process ids", failures);
        check(parallelOverlap, "two 4P worker lifetimes did not overlap", failures);
        check(distinctStateIdentity, "deliberately different game states produced the same state digest", failures);
        check(distinctRngIdentity, "deliberately different RNG identities produced the same RNG digest", failures);
        check(distinctDecisionIdentity, "scoped decision identities produced the same digest", failures);

        // Fault phase: run a clean-equivalent alpha survivor concurrently with a
        // fourth JVM, wait until the victim has constructed real Game state, then
        // kill the entire victim JVM. The survivor must byte-match clean alpha's
        // authoritative state/RNG/decision streams.
        final WorkerProcess survivor = startWorker(root, workers.resolve("fault-survivor"), "fault-survivor",
                ALPHA_GAME, 111_111L, ALPHA_CANARY, BETA_CANARY, ALPHA_CONTROLLER, allocatePort());
        final WorkerProcess victim = startWorker(root, workers.resolve("crash-victim"), "crash-victim",
                "ws08-crash-victim-4p", 333_333L, ALPHA_CANARY, BETA_CANARY,
                "controller-crash-victim", allocatePort());
        final boolean victimReachedGame = awaitReady(victim.outputDir.resolve("ready.marker"), victim.process, Duration.ofSeconds(90));
        if (victimReachedGame && victim.process.isAlive()) {
            victim.process.destroyForcibly();
        }
        final int victimExit = waitFor(victim, Duration.ofSeconds(30));
        final int survivorExit = waitFor(survivor, Duration.ofMinutes(5));
        final Properties s = loadSummary(survivor.outputDir);
        verifyWorker("fault-survivor", survivorExit, s, survivor.outputDir,
                ALPHA_GAME, ALPHA_CANARY, BETA_CANARY, ALPHA_CONTROLLER, failures);
        final boolean victimTerminated = victimReachedGame && victimExit != 0;
        final boolean survivorStateMatches = sameBytes(alpha.outputDir.resolve("states.jsonl"), survivor.outputDir.resolve("states.jsonl"));
        final boolean survivorRngMatches = sameBytes(alpha.outputDir.resolve("rng.tsv"), survivor.outputDir.resolve("rng.tsv"));
        final boolean survivorDecisionsMatch = sameBytes(alpha.outputDir.resolve("decisions.tsv"), survivor.outputDir.resolve("decisions.tsv"));
        final boolean failureCorruptsOther = !(victimTerminated && survivorExit == 0
                && survivorStateMatches && survivorRngMatches && survivorDecisionsMatch);
        check(victimReachedGame, "crash victim never reached GAME_CONSTRUCTED", failures);
        check(victimTerminated, "crash victim did not terminate non-zero after destroyForcibly", failures);
        check(!failureCorruptsOther, "single worker failure changed survivor semantic evidence", failures);

        final Properties result = new Properties();
        result.setProperty("parallel_4P_games", "2");
        result.setProperty("parallel_worker_pids_distinct", Boolean.toString(distinctPids));
        result.setProperty("parallel_worker_lifetimes_overlap", Boolean.toString(parallelOverlap));
        result.setProperty("cross_game_state_leaks", Long.toString(stateLeaks));
        result.setProperty("cross_game_rng_leaks", Long.toString(rngLeaks));
        result.setProperty("cross_game_decision_queue_leaks", Long.toString(decisionQueueLeaks));
        result.setProperty("cross_game_request_id_collisions", Integer.toString(requestIntersection.size()));
        result.setProperty("raw_local_decision_id_overlaps", Integer.toString(rawIntersection.size()));
        result.setProperty("request_id_scope", "game_id:principal_id:decision_id:token");
        result.setProperty("cross_game_observation_leaks", Long.toString(observationLeaks));
        result.setProperty("cross_game_controller_state_leaks", Long.toString(controllerLeaks));
        result.setProperty("distinct_state_identity", Boolean.toString(distinctStateIdentity));
        result.setProperty("distinct_rng_identity", Boolean.toString(distinctRngIdentity));
        result.setProperty("distinct_decision_identity", Boolean.toString(distinctDecisionIdentity));
        result.setProperty("victim_reached_GAME_CONSTRUCTED", Boolean.toString(victimReachedGame));
        result.setProperty("victim_exit", Integer.toString(victimExit));
        result.setProperty("survivor_exit", Integer.toString(survivorExit));
        result.setProperty("survivor_state_matches_clean_baseline", Boolean.toString(survivorStateMatches));
        result.setProperty("survivor_rng_matches_clean_baseline", Boolean.toString(survivorRngMatches));
        result.setProperty("survivor_decisions_match_clean_baseline", Boolean.toString(survivorDecisionsMatch));
        result.setProperty("single_worker_failure_corrupts_other_game", Boolean.toString(failureCorruptsOther));
        result.setProperty("alpha_pid", prop(a, "pid"));
        result.setProperty("beta_pid", prop(b, "pid"));
        result.setProperty("survivor_pid", prop(s, "pid"));
        result.setProperty("crash_victim_pid", Long.toString(victim.process.pid()));
        result.setProperty("failure_count", Integer.toString(failures.size()));
        result.setProperty("failures", String.join(" | ", failures));
        try (var writer = Files.newBufferedWriter(root.resolve("ISOLATION_RESULT.properties"), StandardCharsets.UTF_8)) {
            result.store(writer, "WS08 process isolation adjudication input");
        }
        Files.writeString(root.resolve("processes.tsv"),
                "alpha\t" + alpha.process.pid() + "\t" + alphaExit + "\n"
                        + "beta\t" + beta.process.pid() + "\t" + betaExit + "\n"
                        + "fault-survivor\t" + survivor.process.pid() + "\t" + survivorExit + "\n"
                        + "crash-victim\t" + victim.process.pid() + "\t" + victimExit + "\n",
                StandardCharsets.UTF_8);

        Assert.assertTrue(failures.isEmpty(), "WS08 fail-closed assertions: " + String.join("; ", failures));
        System.out.println("WS08_PARALLEL_4P_GAMES=2");
        System.out.println("WS08_CROSS_GAME_STATE_LEAKS=0");
        System.out.println("WS08_CROSS_GAME_RNG_LEAKS=0");
        System.out.println("WS08_CROSS_GAME_DECISION_QUEUE_LEAKS=0");
        System.out.println("WS08_CROSS_GAME_REQUEST_ID_COLLISIONS=0");
        System.out.println("WS08_CROSS_GAME_OBSERVATION_LEAKS=0");
        System.out.println("WS08_CROSS_GAME_CONTROLLER_STATE_LEAKS=0");
        System.out.println("WS08_SINGLE_WORKER_FAILURE_CORRUPTS_OTHER_GAME=false");
    }

    private static WorkerProcess startWorker(
            final Path root, final Path outDir, final String label, final String gameId, final long seed,
            final String canary, final String foreignCanary, final String controllerTag, final int port) throws IOException {
        Files.createDirectories(outDir);
        final String cp = System.getProperty("surefire.test.class.path", System.getProperty("java.class.path"));
        final String javaBin = Path.of(System.getProperty("java.home"), "bin", "java").toString();
        final Path temp = outDir.resolve("tmp");
        Files.createDirectories(temp);
        final ProcessBuilder pb = new ProcessBuilder(
                javaBin, "-Xmx1024m", "-Djava.io.tmpdir=" + temp,
                "-cp", cp, "forge.net.Ws08ProcessIsolationWorker",
                label, gameId, Long.toString(seed), canary, foreignCanary, controllerTag,
                Integer.toString(port), outDir.toString());
        pb.directory(Path.of(System.getProperty("user.dir")).toFile());
        pb.redirectErrorStream(true);
        pb.redirectOutput(outDir.resolve("worker.log").toFile());
        final long start = System.nanoTime();
        return new WorkerProcess(pb.start(), outDir, start);
    }

    private static int waitFor(final WorkerProcess worker, final Duration timeout) throws Exception {
        if (!worker.process.waitFor(timeout.toMillis(), TimeUnit.MILLISECONDS)) {
            worker.process.destroyForcibly();
            worker.process.waitFor(30, TimeUnit.SECONDS);
            worker.endNanos = System.nanoTime();
            return 124;
        }
        worker.endNanos = System.nanoTime();
        return worker.process.exitValue();
    }

    private static boolean awaitReady(final Path marker, final Process process, final Duration timeout) throws Exception {
        final Instant deadline = Instant.now().plus(timeout);
        while (Instant.now().isBefore(deadline)) {
            if (Files.isRegularFile(marker) && Files.size(marker) > 0) return true;
            if (!process.isAlive()) return Files.isRegularFile(marker);
            Thread.sleep(100L);
        }
        return Files.isRegularFile(marker);
    }

    private static void verifyWorker(
            final String label, final int exit, final Properties p, final Path dir,
            final String gameId, final String ownCanary, final String foreignCanary,
            final String controllerTag, final List<String> failures) throws Exception {
        check(exit == 0, label + " exit=" + exit, failures);
        check("4".equals(prop(p, "player_count")), label + " player_count=" + prop(p, "player_count"), failures);
        check(boolProp(p, "game_completed"), label + " game not completed", failures);
        check(boolProp(p, "game_passed"), label + " game result not passed", failures);
        check(prop(p, "failure").isEmpty(), label + " failure=" + prop(p, "failure"), failures);
        check(gameId.equals(prop(p, "game_id")), label + " wrong game id", failures);
        check(controllerTag.equals(prop(p, "controller_tag")), label + " wrong controller tag", failures);
        check(longProp(p, "state_count") > 0, label + " empty state stream", failures);
        check(longProp(p, "rng_count") > 0, label + " empty RNG stream", failures);
        check(longProp(p, "decision_count") > 0, label + " empty decision stream", failures);
        check(longProp(p, "controller_invocations") > 0, label + " controller never invoked", failures);
        check(longProp(p, "observation_samples") > 0, label + " no principal observations", failures);
        check(longProp(p, "full_state_syncs") > 0, label + " no full state sync", failures);
        check(longProp(p, "delta_packets") > 0, label + " no delta packets", failures);
        check(longProp(p, "pilot_visible_hidden_info_leaks") == 0, label + " same-game hidden-info leak", failures);
        check(longProp(p, "cross_principal_decision_leaks") == 0, label + " cross-principal decision leak", failures);
        check(longProp(p, "cross_game_observation_leaks") == 0, label + " foreign-game observation sentinel leak", failures);
        check(occurrences(dir.resolve("states.jsonl"), ownCanary) > 0, label + " own state sentinel absent", failures);
        check(occurrences(dir.resolve("states.jsonl"), foreignCanary) == 0, label + " foreign state sentinel present", failures);
    }

    private static long wrongRngScope(final Path path, final String gameId) throws IOException {
        long wrong = 0;
        for (final String line : Files.readAllLines(path, StandardCharsets.UTF_8)) {
            if (line.isBlank()) continue;
            final String[] fields = line.split("\\t", -1);
            if (fields.length != 6 || !gameId.equals(fields[1])) wrong++;
        }
        return wrong;
    }

    private static long wrongDecisionScope(final Path path, final String gameId, final String controllerTag) throws IOException {
        long wrong = 0;
        for (final String line : Files.readAllLines(path, StandardCharsets.UTF_8)) {
            if (line.isBlank()) continue;
            final String[] fields = line.split("\\t", -1);
            if (fields.length != 8 || !fields[0].startsWith(gameId + ":")
                    || !controllerTag.equals(fields[1]) || !"ACCEPTED".equals(fields[7])) wrong++;
        }
        return wrong;
    }

    private static long wrongController(final Path path, final String controllerTag) throws IOException {
        long wrong = 0;
        for (final String line : Files.readAllLines(path, StandardCharsets.UTF_8)) {
            if (line.isBlank()) continue;
            final String[] fields = line.split("\\t", -1);
            if (fields.length < 2 || !controllerTag.equals(fields[1])) wrong++;
        }
        return wrong;
    }

    private static Set<String> scopedRequestIds(final Path path) throws IOException {
        final Set<String> result = new HashSet<>();
        for (final String line : Files.readAllLines(path, StandardCharsets.UTF_8)) {
            if (!line.isBlank()) result.add(line.split("\\t", -1)[0]);
        }
        return result;
    }

    private static Set<String> rawDecisionIds(final Path path) throws IOException {
        final Set<String> result = new HashSet<>();
        for (final String line : Files.readAllLines(path, StandardCharsets.UTF_8)) {
            if (!line.isBlank()) {
                final String[] f = line.split("\\t", -1);
                if (f.length >= 4) result.add(f[2] + ":" + f[3]);
            }
        }
        return result;
    }

    private static long occurrences(final Path path, final String needle) throws IOException {
        if (!Files.exists(path)) return 0;
        long count = 0;
        try (BufferedReader reader = Files.newBufferedReader(path, StandardCharsets.UTF_8)) {
            String line;
            while ((line = reader.readLine()) != null) {
                int from = 0;
                while ((from = line.indexOf(needle, from)) >= 0) {
                    count++;
                    from += needle.length();
                }
            }
        }
        return count;
    }

    private static boolean sameBytes(final Path left, final Path right) throws IOException {
        return Files.exists(left) && Files.exists(right) && java.util.Arrays.equals(Files.readAllBytes(left), Files.readAllBytes(right));
    }

    private static Properties loadSummary(final Path dir) throws IOException {
        final Properties p = new Properties();
        final Path path = dir.resolve("summary.properties");
        if (!Files.exists(path)) return p;
        try (var reader = Files.newBufferedReader(path, StandardCharsets.UTF_8)) { p.load(reader); }
        return p;
    }

    private static int allocatePort() throws IOException {
        try (ServerSocket socket = new ServerSocket(0)) { return socket.getLocalPort(); }
    }

    private static String prop(final Properties p, final String key) { return p.getProperty(key, ""); }
    private static long longProp(final Properties p, final String key) {
        final String value = prop(p, key);
        return value.isEmpty() ? -1 : Long.parseLong(value);
    }
    private static boolean boolProp(final Properties p, final String key) { return Boolean.parseBoolean(prop(p, key)); }
    private static void check(final boolean condition, final String message, final List<String> failures) {
        if (!condition) failures.add(message);
    }

    private static final class WorkerProcess {
        final Process process;
        final Path outputDir;
        final long startNanos;
        long endNanos = Long.MAX_VALUE;

        WorkerProcess(final Process process, final Path outputDir, final long startNanos) {
            this.process = process;
            this.outputDir = outputDir;
            this.startNanos = startNanos;
        }
    }
}
