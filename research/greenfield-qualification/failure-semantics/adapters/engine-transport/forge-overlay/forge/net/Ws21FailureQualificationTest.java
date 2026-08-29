package forge.net;

import org.testng.annotations.Test;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.net.InetAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.HashSet;
import java.util.List;
import java.util.Properties;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.atomic.AtomicReference;

/** Parent/supervisor qualification process. It never hosts a game. */
public final class Ws21FailureQualificationTest {
    private static final String PRIVATE_CANARY = "Elite Vanguard";

    @Test(timeOut = 600_000)
    public void engineAndTransportFailuresAreTypedAtActualPaths() throws Exception {
        final String configured = System.getProperty("ws21.evidenceDir");
        if (configured == null || configured.isBlank()) {
            throw new IllegalStateException("ws21.evidenceDir is required");
        }
        final Path root = Path.of(configured).toAbsolutePath();
        final Path workers = root.resolve("workers");
        Files.createDirectories(workers);

        final WorkerResult engine = runWorker(workers.resolve("engine"), "ENGINE", "ws21-engine-4p", null);
        final WorkerResult transport;
        try (PilotEndpoint endpoint = new PilotEndpoint(PilotBehavior.TRUNCATED_RESPONSE)) {
            transport = runWorker(workers.resolve("transport"), "TRANSPORT", "ws21-transport-4p", endpoint);
            endpoint.assertClean();
            check(endpoint.requests.get() == 1L, "transport endpoint did not observe exactly one request");
        }
        final WorkerResult malformed;
        try (PilotEndpoint endpoint = new PilotEndpoint(PilotBehavior.MALFORMED_RESPONSE)) {
            malformed = runWorker(workers.resolve("malformed-control"), "MALFORMED_CONTROL",
                    "ws21-malformed-control-4p", endpoint);
            endpoint.assertClean();
            check(endpoint.requests.get() == 1L, "malformed control endpoint did not observe exactly one request");
        }

        verifyCommon(engine, "ENGINE_FAILURE");
        verifyCommon(transport, "TRANSPORT_FAILURE");
        verifyCommon(malformed, "MALFORMED_RESPONSE");

        check(bool(engine.props, "engine_fault_fired"), "engine fault injector did not fire");
        check(!bool(engine.props, "post_fault_engine_body_reached"),
                "engine executed original changeZone body after the injected failure");
        check(longProp(engine.props, "transport_boundary_propagations") == 0L,
                "engine failure crossed the transport boundary");
        check(!bool(engine.props, "game_completed"), "engine fault silently continued to a completed game");

        check(longProp(transport.props, "transport_requests_written") >= 1L,
                "transport request was not delivered");
        check(longProp(transport.props, "transport_responses_decoded") == 0L,
                "truncated response unexpectedly decoded");
        check(longProp(transport.props, "transport_boundary_propagations") >= 1L,
                "transport exception was not preserved at PlayerControllerHuman boundary");
        check(longProp(transport.props, "decision_validated") == 0L,
                "transport fault reached response validation");
        check(longProp(transport.props, "decision_applied") == 0L,
                "transport fault substituted or applied a decision");
        check(!bool(transport.props, "engine_fault_fired"), "transport control also fired engine fault");
        check(!bool(transport.props, "game_completed"), "transport fault silently continued to a completed game");

        check(longProp(malformed.props, "transport_requests_written") >= 1L,
                "malformed control request was not delivered");
        check(longProp(malformed.props, "transport_responses_decoded") >= 1L,
                "malformed control did not decode as a valid transport frame");
        check(longProp(malformed.props, "transport_boundary_propagations") == 0L,
                "malformed pilot response was incorrectly classified as transport failure");
        check(longProp(malformed.props, "decision_validated") == 0L,
                "malformed response unexpectedly validated");
        check(longProp(malformed.props, "decision_applied") == 0L,
                "malformed response unexpectedly applied a decision");

        final Set<Long> workerPids = new HashSet<>(List.of(
                longProp(engine.props, "worker_pid"),
                longProp(transport.props, "worker_pid"),
                longProp(malformed.props, "worker_pid")));
        check(workerPids.size() == 3, "WS21 scenarios did not use distinct child JVMs");
        check(!workerPids.contains(ProcessHandle.current().pid()), "parent supervisor hosted a game worker");

        final long diagnosticLeaks = diagnosticOccurrences(engine.dir, PRIVATE_CANARY)
                + diagnosticOccurrences(transport.dir, PRIVATE_CANARY)
                + diagnosticOccurrences(malformed.dir, PRIVATE_CANARY);
        check(diagnosticLeaks == 0L, "structured diagnostic payload leaked the private canary");

        final Properties result = new Properties();
        result.setProperty("engine_category", prop(engine.props, "category"));
        result.setProperty("engine_worker_exit", Integer.toString(engine.exit));
        result.setProperty("engine_process_alive_while_reporting", prop(engine.props, "process_alive_while_reporting"));
        result.setProperty("engine_state_committed", prop(engine.props, "state_committed"));
        result.setProperty("engine_original_body_after_fault", prop(engine.props, "post_fault_engine_body_reached"));
        result.setProperty("transport_category", prop(transport.props, "category"));
        result.setProperty("transport_worker_exit", Integer.toString(transport.exit));
        result.setProperty("transport_process_alive_while_reporting", prop(transport.props, "process_alive_while_reporting"));
        result.setProperty("transport_state_committed", prop(transport.props, "state_committed"));
        result.setProperty("transport_decision_applied", prop(transport.props, "decision_applied"));
        result.setProperty("malformed_control_category", prop(malformed.props, "category"));
        result.setProperty("malformed_transport_propagations", prop(malformed.props, "transport_boundary_propagations"));
        result.setProperty("diagnostic_hidden_info_leaks", Long.toString(diagnosticLeaks));
        result.setProperty("distinct_worker_pids", Integer.toString(workerPids.size()));
        result.setProperty("games_per_worker_process", "1");
        try (var writer = Files.newBufferedWriter(root.resolve("WS21_RESULT.properties"), StandardCharsets.UTF_8)) {
            result.store(writer, "WS21 engine plus transport adjudication input");
        }
        Files.writeString(root.resolve("processes.tsv"),
                "engine\t" + longProp(engine.props, "worker_pid") + "\t" + engine.exit + "\n"
                        + "transport\t" + longProp(transport.props, "worker_pid") + "\t" + transport.exit + "\n"
                        + "malformed-control\t" + longProp(malformed.props, "worker_pid") + "\t" + malformed.exit + "\n",
                StandardCharsets.UTF_8);

        System.out.println("WS21_ENGINE_FAILURE=PASS");
        System.out.println("WS21_TRANSPORT_FAILURE=PASS");
        System.out.println("WS21_MALFORMED_RESPONSE_DISTINCTION=PASS");
        System.out.println("WS21_HIDDEN_DIAGNOSTIC_LEAKS=0");
        System.out.println("WS21_PROCESS_PER_GAME=PASS");
    }

    private static WorkerResult runWorker(final Path dir, final String mode, final String gameId,
                                          final PilotEndpoint endpoint) throws Exception {
        Files.createDirectories(dir);
        final Path temp = dir.resolve("tmp");
        Files.createDirectories(temp);
        final String cp = System.getProperty("surefire.test.class.path", System.getProperty("java.class.path"));
        final String javaBin = Path.of(System.getProperty("java.home"), "bin", "java").toString();
        final int gamePort = allocatePort();
        final int pilotPort = endpoint == null ? -1 : endpoint.port();
        final ProcessBuilder pb = new ProcessBuilder(javaBin, "-Xmx1024m", "-Djava.io.tmpdir=" + temp,
                "-cp", cp, "forge.net.Ws21FailureWorker", mode, gameId,
                Integer.toString(gamePort), Integer.toString(pilotPort), dir.toString());
        pb.directory(Path.of(System.getProperty("user.dir")).toFile());
        pb.redirectErrorStream(true);
        pb.redirectOutput(dir.resolve("worker.log").toFile());
        final Process process = pb.start();
        if (!process.waitFor(Duration.ofMinutes(3).toMillis(), TimeUnit.MILLISECONDS)) {
            process.destroyForcibly();
            process.waitFor(30, TimeUnit.SECONDS);
            throw new AssertionError(mode + " worker timed out");
        }
        final int exit = process.exitValue();
        final Path summary = dir.resolve("summary.properties");
        check(Files.isRegularFile(summary), mode + " worker did not report structured outcome");
        final Properties props = new Properties();
        try (var reader = Files.newBufferedReader(summary, StandardCharsets.UTF_8)) {
            props.load(reader);
        }
        return new WorkerResult(dir, exit, props);
    }

    private static void verifyCommon(final WorkerResult worker, final String expectedCategory) throws Exception {
        check(worker.exit == 0, expectedCategory + " worker exited non-zero: " + worker.exit);
        check(expectedCategory.equals(prop(worker.props, "category")),
                "expected " + expectedCategory + " but got " + prop(worker.props, "category"));
        check(bool(worker.props, "process_alive_while_reporting"),
                expectedCategory + " was not reported by the live worker process");
        check(!bool(worker.props, "state_committed"), expectedCategory + " committed failed state");
        final String outcome = Files.readString(worker.dir.resolve("outcome.json"), StandardCharsets.UTF_8);
        check(outcome.contains("\"category\":\"" + expectedCategory + "\""), "outcome category mismatch");
        check(outcome.contains("\"state_committed\":false"), "outcome state commit mismatch");
    }

    private static long diagnosticOccurrences(final Path dir, final String needle) throws Exception {
        long count = 0L;
        for (final String name : List.of("outcome.json", "fault-trace.jsonl", "summary.properties")) {
            final String text = Files.readString(dir.resolve(name), StandardCharsets.UTF_8);
            int at = 0;
            while ((at = text.indexOf(needle, at)) >= 0) {
                count++;
                at += needle.length();
            }
        }
        return count;
    }

    private static int allocatePort() throws Exception {
        try (ServerSocket socket = new ServerSocket(0, 1, InetAddress.getLoopbackAddress())) {
            return socket.getLocalPort();
        }
    }

    private enum PilotBehavior { TRUNCATED_RESPONSE, MALFORMED_RESPONSE }

    private static final class PilotEndpoint implements AutoCloseable {
        private final ServerSocket server;
        private final Thread thread;
        private final PilotBehavior behavior;
        private final AtomicReference<Throwable> failure = new AtomicReference<>();
        private final AtomicLong requests = new AtomicLong();

        PilotEndpoint(final PilotBehavior behavior) throws Exception {
            this.behavior = behavior;
            this.server = new ServerSocket(0, 1, InetAddress.getLoopbackAddress());
            this.thread = new Thread(this::serve, "WS21-PilotEndpoint-" + behavior);
            this.thread.setDaemon(true);
            this.thread.start();
        }

        int port() { return server.getLocalPort(); }

        private void serve() {
            try (Socket socket = server.accept()) {
                socket.setSoTimeout(15_000);
                final DataInputStream in = new DataInputStream(new BufferedInputStream(socket.getInputStream()));
                final Ws21PilotWire.RequestFrame request = Ws21PilotWire.readRequest(in);
                requests.incrementAndGet();
                final DataOutputStream out = new DataOutputStream(new BufferedOutputStream(socket.getOutputStream()));
                if (behavior == PilotBehavior.TRUNCATED_RESPONSE) {
                    out.writeUTF(Ws21PilotWire.RESPONSE_MAGIC);
                    out.writeLong(request.decisionId);
                    out.flush();
                    return;
                }
                final String selected = request.optionIds.isEmpty() ? "choice:ws21-invalid" : request.optionIds.get(0);
                Ws21PilotWire.writeResponse(out, request, "commander-simulator-next.ws21.invalid-response-schema",
                        List.of(selected), false);
                out.flush();
            } catch (Throwable thrown) {
                failure.set(thrown);
            }
        }

        void assertClean() throws Exception {
            thread.join(20_000L);
            check(!thread.isAlive(), "pilot endpoint did not terminate");
            if (failure.get() != null) {
                throw new AssertionError("pilot endpoint failed", failure.get());
            }
        }

        @Override
        public void close() throws Exception {
            server.close();
            thread.join(5_000L);
        }
    }

    private record WorkerResult(Path dir, int exit, Properties props) { }

    private static String prop(final Properties props, final String key) {
        final String value = props.getProperty(key);
        if (value == null) throw new AssertionError("missing property: " + key);
        return value;
    }

    private static boolean bool(final Properties props, final String key) {
        return Boolean.parseBoolean(prop(props, key));
    }

    private static long longProp(final Properties props, final String key) {
        return Long.parseLong(prop(props, key));
    }

    private static void check(final boolean condition, final String message) {
        if (!condition) throw new AssertionError(message);
    }
}
