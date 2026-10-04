// Trusted parent-side observer for C12 candidate qualification.
//
// This process runs as the trusted workflow identity. Candidate code never loads
// this class and never receives a receipt key or writable receipt channel. It
// listens for the exact child JVM launched by witness.py through JDWP, disables
// the listening socket as soon as that VM connects, and observes entries into
// private hooks in the non-exported c12.trusted driver module.
//
// The child can make qualification fail by crashing, hanging or corrupting its
// own execution. It cannot manufacture PASS: the receipt is written only here,
// by the trusted parent, from JDI events whose hook class/method identity is
// fixed by trusted source.

import com.sun.jdi.BooleanValue;
import com.sun.jdi.IncompatibleThreadStateException;
import com.sun.jdi.StringReference;
import com.sun.jdi.Value;
import com.sun.jdi.VirtualMachine;
import com.sun.jdi.VMDisconnectedException;
import com.sun.jdi.Bootstrap;
import com.sun.jdi.connect.Connector;
import com.sun.jdi.connect.ListeningConnector;
import com.sun.jdi.event.Event;
import com.sun.jdi.event.EventQueue;
import com.sun.jdi.event.EventSet;
import com.sun.jdi.event.MethodEntryEvent;
import com.sun.jdi.event.VMDeathEvent;
import com.sun.jdi.event.VMDisconnectEvent;
import com.sun.jdi.request.EventRequest;
import com.sun.jdi.request.EventRequestManager;
import com.sun.jdi.request.MethodEntryRequest;
import com.sun.jdi.StackFrame;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import java.util.TreeSet;

public final class TrustedTestObserver {
    private static final String SCHEMA =
            "mage.candidate-qualification.trusted-execution-witness/4";
    private static final String HOOK_CLASS = "c12.trusted.TrustedTestDriver";

    private static String esc(String value) {
        if (value == null) return "";
        StringBuilder out = new StringBuilder();
        for (int i = 0; i < value.length(); i++) {
            char c = value.charAt(i);
            switch (c) {
                case '"': out.append("\\\""); break;
                case '\\': out.append("\\\\"); break;
                case '\n': out.append("\\n"); break;
                case '\r': out.append("\\r"); break;
                case '\t': out.append("\\t"); break;
                default:
                    if (c < 0x20) out.append(String.format("\\u%04x", (int)c));
                    else out.append(c);
            }
        }
        return out.toString();
    }

    private static String jsonString(String value) {
        return "\"" + esc(value) + "\"";
    }

    private static String jsonStrings(Set<String> values) {
        StringBuilder out = new StringBuilder("[");
        boolean first = true;
        for (String value : new TreeSet<>(values)) {
            if (!first) out.append(",");
            first = false;
            out.append(jsonString(value));
        }
        return out.append("]").toString();
    }

    private static String jsonMap(Map<String, ?> values) {
        StringBuilder out = new StringBuilder("{");
        boolean first = true;
        for (Map.Entry<String, ?> entry : new TreeMap<>(values).entrySet()) {
            if (!first) out.append(",");
            first = false;
            out.append(jsonString(entry.getKey())).append(":");
            Object value = entry.getValue();
            if (value instanceof Number || value instanceof Boolean) out.append(value);
            else out.append(jsonString(String.valueOf(value)));
        }
        return out.append("}").toString();
    }

    private static ListeningConnector socketListener() {
        for (ListeningConnector connector : Bootstrap.virtualMachineManager().listeningConnectors()) {
            if ("com.sun.jdi.SocketListen".equals(connector.name())) return connector;
        }
        throw new IllegalStateException("JDI SocketListen connector unavailable");
    }

    private static String text(Value value) {
        if (value == null) return "";
        if (value instanceof StringReference) return ((StringReference)value).value();
        if (value instanceof BooleanValue) return Boolean.toString(((BooleanValue)value).value());
        return value.toString();
    }

    private static boolean bool(Value value) {
        return value instanceof BooleanValue && ((BooleanValue)value).value();
    }

    private static List<Value> args(MethodEntryEvent event)
            throws IncompatibleThreadStateException {
        StackFrame frame = event.thread().frame(0);
        return frame.getArgumentValues();
    }

    private static Path real(Path path) {
        try { return path.toRealPath(); }
        catch (IOException exc) { return path.toAbsolutePath().normalize(); }
    }

    private static boolean under(String location, Path expected) {
        if (location == null || location.isEmpty()) return false;
        try {
            return real(Paths.get(location)).startsWith(expected);
        } catch (RuntimeException exc) {
            return false;
        }
    }

    private static final class State {
        final String module;
        final String boundSha;
        final String boundTree;
        final Path expectedOutput;
        final Set<String> selected;
        final Set<String> observedClasses = new TreeSet<>();
        final Set<String> observedMethods = new TreeSet<>();
        final Set<String> originViolations = new TreeSet<>();
        final Map<String, String> classOrigins = new TreeMap<>();
        final Map<String, Integer> nonSuccessful = new TreeMap<>();
        final List<String> protocolViolations = new ArrayList<>();
        long testsStarted;
        long testsSucceeded;
        long testsFailed;
        long testsAborted;
        long testsSkipped;
        long containersFailed;
        boolean startSeen;
        boolean completeSeen;
        long sequence;

        State(String module, String sha, String tree, Path expectedOutput, Set<String> selected) {
            this.module = module;
            this.boundSha = sha;
            this.boundTree = tree;
            this.expectedOutput = real(expectedOutput);
            this.selected = new TreeSet<>(selected);
        }

        void hook(String name, List<Value> values) {
            sequence++;
            if ("observerStart".equals(name)) {
                if (startSeen || !values.isEmpty()) {
                    protocolViolations.add("duplicate_or_malformed_start");
                }
                startSeen = true;
                return;
            }
            if ("observerComplete".equals(name)) {
                if (completeSeen || !values.isEmpty()) {
                    protocolViolations.add("duplicate_or_malformed_complete");
                }
                completeSeen = true;
                return;
            }
            if (!"observerEvent".equals(name) || values.size() != 9) {
                protocolViolations.add("unexpected_hook:" + name + ":" + values.size());
                return;
            }
            String phase = text(values.get(0));
            String engine = text(values.get(1));
            String uniqueId = text(values.get(2));
            boolean isTest = bool(values.get(3));
            String className = text(values.get(4));
            String method = text(values.get(5));
            String status = text(values.get(6));
            String origin = text(values.get(7));
            String detail = text(values.get(8));

            if (!("junit-jupiter".equals(engine) || "junit-vintage".equals(engine))) {
                originViolations.add("foreign_engine:" + engine + ":" + uniqueId);
            }
            if ("STARTED".equals(phase)) {
                if (!method.isEmpty()) observedMethods.add(method);
                if (isTest) {
                    testsStarted++;
                    if (!className.isEmpty()) {
                        observedClasses.add(className);
                        if (!origin.isEmpty()) classOrigins.put(className, origin);
                        if (!under(origin, expectedOutput)) {
                            originViolations.add(className + " loaded from " + origin
                                    + " (expected under " + expectedOutput + ")");
                        }
                    }
                }
            } else if ("FINISHED".equals(phase)) {
                if (isTest) {
                    if ("SUCCESSFUL".equals(status)) testsSucceeded++;
                    else if ("FAILED".equals(status)) testsFailed++;
                    else if ("ABORTED".equals(status)) testsAborted++;
                    else protocolViolations.add("unknown_test_status:" + status);
                } else if ("FAILED".equals(status) || "ABORTED".equals(status)) {
                    containersFailed++;
                }
                if (!"SUCCESSFUL".equals(status) && !className.isEmpty()) {
                    nonSuccessful.put(className, nonSuccessful.getOrDefault(className, 0) + 1);
                }
            } else if ("SKIPPED".equals(phase)) {
                if (isTest) testsSkipped++;
            } else if ("VIOLATION".equals(phase)) {
                originViolations.add(detail.isEmpty() ? uniqueId : detail);
            } else {
                protocolViolations.add("unknown_phase:" + phase);
            }
        }

        String receipt(String observerStatus, String vmDescription) {
            Set<String> missing = new TreeSet<>(selected);
            missing.removeAll(observedClasses);
            long found = testsStarted + testsSkipped;
            boolean pass = "COMPLETE".equals(observerStatus)
                    && startSeen && completeSeen
                    && protocolViolations.isEmpty()
                    && originViolations.isEmpty()
                    && missing.isEmpty()
                    && found > 0
                    && testsStarted > 0
                    && testsFailed == 0
                    && testsAborted == 0
                    && containersFailed == 0
                    && testsSkipped < found;
            StringBuilder out = new StringBuilder();
            out.append("{\n");
            out.append("  \"schema\": ").append(jsonString(SCHEMA)).append(",\n");
            out.append("  \"producer\": \"TrustedTestObserver\",\n");
            out.append("  \"evidence_origin\": \"trusted_parent_jdi_observation\",\n");
            out.append("  \"candidate_authored_evidence_used\": false,\n");
            out.append("  \"candidate_witness_authority\": false,\n");
            out.append("  \"execution_mode\": \"per_module_external_observer\",\n");
            out.append("  \"observer_status\": ").append(jsonString(observerStatus)).append(",\n");
            out.append("  \"observer_sequence_events\": ").append(sequence).append(",\n");
            out.append("  \"vm_description\": ").append(jsonString(vmDescription)).append(",\n");
            out.append("  \"module_id\": ").append(jsonString(module)).append(",\n");
            out.append("  \"module_output\": ").append(jsonString(expectedOutput.toString())).append(",\n");
            out.append("  \"bound_candidate_sha\": ").append(jsonString(boundSha)).append(",\n");
            out.append("  \"bound_candidate_tree\": ").append(jsonString(boundTree)).append(",\n");
            out.append("  \"trusted_selected_classes\": ").append(selected.size()).append(",\n");
            out.append("  \"trusted_selected_class_names\": ").append(jsonStrings(selected)).append(",\n");
            out.append("  \"observed_classes\": ").append(jsonStrings(observedClasses)).append(",\n");
            out.append("  \"classes_never_entered\": ").append(jsonStrings(missing)).append(",\n");
            out.append("  \"observed_methods\": ").append(jsonStrings(observedMethods)).append(",\n");
            out.append("  \"class_code_origins\": ").append(jsonMap(classOrigins)).append(",\n");
            out.append("  \"code_origin_violations\": ").append(jsonStrings(originViolations)).append(",\n");
            out.append("  \"protocol_violations\": ").append(jsonStrings(new LinkedHashSet<>(protocolViolations))).append(",\n");
            out.append("  \"tests_found\": ").append(found).append(",\n");
            out.append("  \"tests_started\": ").append(testsStarted).append(",\n");
            out.append("  \"tests_succeeded\": ").append(testsSucceeded).append(",\n");
            out.append("  \"tests_failed\": ").append(testsFailed).append(",\n");
            out.append("  \"tests_aborted\": ").append(testsAborted).append(",\n");
            out.append("  \"tests_skipped\": ").append(testsSkipped).append(",\n");
            out.append("  \"containers_failed\": ").append(containersFailed).append(",\n");
            out.append("  \"non_successful_by_class\": ").append(jsonMap(nonSuccessful)).append(",\n");
            out.append("  \"driver_verdict\": ").append(jsonString(pass ? "PASS" : "FAIL")).append("\n");
            out.append("}\n");
            return out.toString();
        }
    }

    public static void main(String[] argv) throws Exception {
        String module = "";
        String sha = "";
        String tree = "";
        Path output = null;
        Path receipt = null;
        Set<String> selected = new LinkedHashSet<>();
        for (int i = 0; i < argv.length; i++) {
            switch (argv[i]) {
                case "--module-id": module = argv[++i]; break;
                case "--bind-sha": sha = argv[++i]; break;
                case "--bind-tree": tree = argv[++i]; break;
                case "--module-output": output = Paths.get(argv[++i]); break;
                case "--receipt": receipt = Paths.get(argv[++i]); break;
                case "--select": selected.add(argv[++i]); break;
                default: throw new IllegalArgumentException("unknown argument " + argv[i]);
            }
        }
        if (module.isEmpty() || sha.isEmpty() || tree.isEmpty() || output == null
                || receipt == null || selected.isEmpty()) {
            throw new IllegalArgumentException("observer binding arguments are incomplete");
        }

        ListeningConnector connector = socketListener();
        Map<String, Connector.Argument> listenArgs = connector.defaultArguments();
        if (listenArgs.containsKey("localAddress")) listenArgs.get("localAddress").setValue("127.0.0.1");
        if (listenArgs.containsKey("port")) listenArgs.get("port").setValue("0");
        if (listenArgs.containsKey("timeout")) listenArgs.get("timeout").setValue("120000");
        String address = connector.startListening(listenArgs);
        System.out.println("TRUSTED_OBSERVER_LISTENING " + address);
        System.out.flush();

        State state = new State(module, sha, tree, output, selected);
        String observerStatus = "INCOMPLETE";
        String vmDescription = "";
        VirtualMachine vm = null;
        try {
            vm = connector.accept(listenArgs);
            connector.stopListening(listenArgs);
            vmDescription = vm.name() + " " + vm.version();

            EventRequestManager manager = vm.eventRequestManager();
            MethodEntryRequest entries = manager.createMethodEntryRequest();
            entries.addClassFilter(HOOK_CLASS);
            entries.setSuspendPolicy(EventRequest.SUSPEND_ALL);
            entries.enable();

            vm.resume();
            EventQueue queue = vm.eventQueue();
            boolean done = false;
            while (!done) {
                EventSet set = queue.remove(300000);
                if (set == null) {
                    state.protocolViolations.add("observer_event_timeout");
                    break;
                }
                try {
                    for (Event event : set) {
                        if (event instanceof MethodEntryEvent) {
                            MethodEntryEvent entered = (MethodEntryEvent)event;
                            String name = entered.method().name();
                            if (name.startsWith("observer")) {
                                state.hook(name, args(entered));
                            }
                        } else if (event instanceof VMDeathEvent) {
                            observerStatus = state.completeSeen ? "COMPLETE" : "INCOMPLETE";
                            done = true;
                        } else if (event instanceof VMDisconnectEvent) {
                            observerStatus = state.completeSeen ? "COMPLETE" : "INCOMPLETE";
                            done = true;
                        }
                    }
                } finally {
                    try { set.resume(); } catch (VMDisconnectedException ignored) { }
                }
            }
            if (!"COMPLETE".equals(observerStatus) && state.completeSeen) observerStatus = "COMPLETE";
        } catch (VMDisconnectedException exc) {
            observerStatus = state.completeSeen ? "COMPLETE" : "INCOMPLETE";
        } finally {
            try { connector.stopListening(listenArgs); } catch (Exception ignored) { }
        }

        Files.createDirectories(receipt.toAbsolutePath().getParent());
        Files.write(receipt, state.receipt(observerStatus, vmDescription).getBytes(StandardCharsets.UTF_8));
        System.out.println("TRUSTED_OBSERVER = " + observerStatus
                + " module=" + module + " started=" + state.testsStarted
                + " failed=" + state.testsFailed + " violations="
                + (state.originViolations.size() + state.protocolViolations.size()));
        System.out.flush();

        if (!"COMPLETE".equals(observerStatus) || !state.startSeen || !state.completeSeen) {
            System.exit(2);
        }
    }
}
