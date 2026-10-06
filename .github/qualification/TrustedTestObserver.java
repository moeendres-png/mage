// Trusted parent-side observer for C12 candidate qualification.
//
// This process runs as the trusted workflow identity. Candidate code never loads
// this class and never receives a receipt key or writable receipt channel. It
// listens for the exact child JVM launched by witness.py through JDWP, disables
// the listening socket as soon as that VM connects, and observes entries into
// private hooks in the non-exported c12.trusted driver module plus entries into
// the required test methods.
//
// The child can make qualification fail by crashing, hanging or corrupting its
// own execution. It cannot manufacture PASS: the receipt is written only here,
// by the trusted parent, from JDI events whose hook class/method identity is
// fixed by trusted source.
//
// Observation uses *breakpoints*, not JVMTI method entry/exit requests. HotSpot
// disables JIT compilation globally while a method entry or exit request is
// enabled, which made the pre-repair gate run the real corpus ~30x slower and
// time out (Mage #493: 5h09m witness step, 18000s per-module timeout). A
// breakpoint only deoptimizes the exact method whose location it covers, and
// this observer sets breakpoints on the three trusted hook methods and on the
// entry of each required test method. Body completion is the trusted driver's
// FINISHED/SUCCESSFUL hook for a test whose required method entry was observed:
// JVMTI method exit events cannot be used without the same global JIT penalty,
// and an exceptional exit never emits a FINISHED/SUCCESSFUL hook.

import com.sun.jdi.BooleanValue;
import com.sun.jdi.IncompatibleThreadStateException;
import com.sun.jdi.Location;
import com.sun.jdi.ReferenceType;
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
import com.sun.jdi.event.BreakpointEvent;
import com.sun.jdi.event.ClassPrepareEvent;
import com.sun.jdi.event.MethodEntryEvent;
import com.sun.jdi.event.VMDeathEvent;
import com.sun.jdi.event.VMDisconnectEvent;
import com.sun.jdi.request.BreakpointRequest;
import com.sun.jdi.request.ClassPrepareRequest;
import com.sun.jdi.request.MethodEntryRequest;
import com.sun.jdi.request.EventRequest;
import com.sun.jdi.request.EventRequestManager;
import com.sun.jdi.StackFrame;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import java.util.TreeSet;

public final class TrustedTestObserver {
    private static final String SCHEMA =
            "mage.candidate-qualification.trusted-execution-witness/6";
    private static final String HOOK_CLASS = "c12.trusted.TrustedTestDriver";
    private static final Set<String> HOOK_METHODS =
            Set.of("observerStart", "observerEvent", "observerComplete");

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

    private static List<Value> args(com.sun.jdi.event.LocatableEvent event)
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

    private static List<String> descriptorArguments(String signature) {
        List<String> out = new ArrayList<>();
        int i = signature.indexOf('(') + 1;
        int end = signature.indexOf(')');
        if (i <= 0 || end < i) throw new IllegalArgumentException("bad method descriptor " + signature);
        while (i < end) {
            int arrays = 0;
            while (i < end && signature.charAt(i) == '[') { arrays++; i++; }
            if (i >= end) throw new IllegalArgumentException("bad array descriptor " + signature);
            char code = signature.charAt(i++);
            String type;
            switch (code) {
                case 'B': type = "byte"; break;
                case 'C': type = "char"; break;
                case 'D': type = "double"; break;
                case 'F': type = "float"; break;
                case 'I': type = "int"; break;
                case 'J': type = "long"; break;
                case 'S': type = "short"; break;
                case 'Z': type = "boolean"; break;
                case 'L':
                    int semi = signature.indexOf(';', i);
                    if (semi < 0 || semi > end) throw new IllegalArgumentException("bad object descriptor " + signature);
                    type = signature.substring(i, semi).replace('/', '.');
                    i = semi + 1;
                    break;
                default: throw new IllegalArgumentException("unsupported descriptor " + signature);
            }
            StringBuilder rendered = new StringBuilder(type);
            for (int a = 0; a < arrays; a++) rendered.append("[]");
            out.add(rendered.toString());
        }
        return out;
    }

    private static String methodIdentity(com.sun.jdi.Method method) {
        return method.declaringType().name() + "#" + method.name() + "("
                + String.join(",", descriptorArguments(method.signature())) + ")";
    }

    private static String declaringClass(String methodIdentity) {
        int hash = methodIdentity.indexOf('#');
        if (hash <= 0) throw new IllegalArgumentException("bad method identity " + methodIdentity);
        return methodIdentity.substring(0, hash);
    }

    private static boolean isJupiterFactoryUniqueId(String uniqueId) {
        return uniqueId != null
                && uniqueId.startsWith("[engine:junit-jupiter]")
                && uniqueId.contains("/[test-factory:");
    }

    private static String hmacHex(byte[] key, byte[] data) throws Exception {
        Mac mac = Mac.getInstance("HmacSHA256");
        mac.init(new SecretKeySpec(key, "HmacSHA256"));
        return HexFormat.of().formatHex(mac.doFinal(data));
    }

    private static final class State {
        final String module;
        final String boundSha;
        final String boundTree;
        final Path expectedOutput;
        final Set<String> selected;
        final Set<String> requiredMethods;
        final Set<String> observedClasses = new TreeSet<>();
        final Set<String> observedMethods = new TreeSet<>();
        final Set<String> bodyEnteredMethods = new TreeSet<>();
        final Set<String> bodyCompletedMethods = new TreeSet<>();
        final Map<Long, String> activeTestIds = new TreeMap<>();
        final Map<Long, String> activeMethods = new TreeMap<>();
        final Map<String, String> factoryMethodById = new TreeMap<>();
        final Map<String, Integer> bodyEntriesByTest = new TreeMap<>();
        final Map<String, Integer> bodyCompletionsByTest = new TreeMap<>();
        final Set<String> originViolations = new TreeSet<>();
        final Set<String> controlViolations = new TreeSet<>();
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

        State(String module, String sha, String tree, Path expectedOutput,
                Set<String> selected, Set<String> requiredMethods) {
            this.module = module;
            this.boundSha = sha;
            this.boundTree = tree;
            this.expectedOutput = real(expectedOutput);
            this.selected = new TreeSet<>(selected);
            this.requiredMethods = new TreeSet<>(requiredMethods);
        }

        void bodyEntry(long threadId, String identity) {
            String expected = activeMethods.get(threadId);
            String uniqueId = activeTestIds.get(threadId);
            if (uniqueId != null && identity.equals(expected)) {
                bodyEnteredMethods.add(identity);
                bodyEntriesByTest.put(uniqueId, bodyEntriesByTest.getOrDefault(uniqueId, 0) + 1);
            }
        }

        void hook(String name, List<Value> values, long threadId) {
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
                boolean factoryMethod = !isTest
                        && isJupiterFactoryUniqueId(uniqueId)
                        && !method.isEmpty()
                        && requiredMethods.contains(method);
                if (factoryMethod) {
                    factoryMethodById.put(uniqueId, method);
                }
                if ((isTest || factoryMethod) && !method.isEmpty()) {
                    String previous = activeTestIds.get(threadId);
                    if (previous != null) {
                        // A Jupiter TestFactory container stays active while its
                        // dynamic children execute. Its own method body returns
                        // before the children start, so a child on the same
                        // thread closes the factory window instead of being an
                        // overlap. No body-exit event is needed: the factory's
                        // completion is credited from its body entry plus the
                        // container FINISHED status below.
                        if (isJupiterFactoryUniqueId(previous)
                                && bodyEntriesByTest.containsKey(previous)) {
                            activeTestIds.remove(threadId);
                            activeMethods.remove(threadId);
                        } else {
                            protocolViolations.add("overlapping_test_on_thread:" + threadId);
                        }
                    }
                    activeTestIds.put(threadId, uniqueId);
                    activeMethods.put(threadId, method);
                }
                if (isTest) testsStarted++;
                if (isTest || factoryMethod) {
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
                    String activeId = activeTestIds.remove(threadId);
                    String activeMethod = activeMethods.remove(threadId);
                    if (activeId != null && !activeId.equals(uniqueId)) {
                        protocolViolations.add("test_finish_id_mismatch:" + activeId + ":" + uniqueId);
                    }
                    // Body credit is owed only for required methods; a test that the
                    // trusted export still runs but no longer requires (an approved
                    // removal) earns no credit and owes no body receipt. Completion
                    // is the required method body entry observed by this parent plus
                    // the trusted driver's FINISHED/SUCCESSFUL report: an exceptional
                    // exit never reports SUCCESSFUL.
                    if ("SUCCESSFUL".equals(status) && activeMethod != null
                            && requiredMethods.contains(activeMethod)) {
                        if (bodyEntriesByTest.getOrDefault(uniqueId, 0) < 1) {
                            controlViolations.add(
                                    "required_method_body_not_entered:" + activeMethod + ":" + uniqueId);
                        } else {
                            bodyCompletedMethods.add(activeMethod);
                            bodyCompletionsByTest.put(uniqueId,
                                    bodyCompletionsByTest.getOrDefault(uniqueId, 0) + 1);
                        }
                    }
                    if ("SUCCESSFUL".equals(status)) testsSucceeded++;
                    else if ("FAILED".equals(status)) testsFailed++;
                    else if ("ABORTED".equals(status)) testsAborted++;
                    else protocolViolations.add("unknown_test_status:" + status);
                } else {
                    if (isJupiterFactoryUniqueId(uniqueId)) {
                        String activeId = activeTestIds.get(threadId);
                        if (uniqueId.equals(activeId)) {
                            activeTestIds.remove(threadId);
                            activeMethods.remove(threadId);
                        }
                        // The factory method identity is tracked by the STARTED
                        // hook even after the window closed for its children.
                        // Recover the required method from the per-test entry
                        // bookkeeping below.
                        String factoryMethod = factoryMethodById.get(uniqueId);
                        if ("SUCCESSFUL".equals(status) && factoryMethod != null
                                && requiredMethods.contains(factoryMethod)) {
                            if (bodyEntriesByTest.getOrDefault(uniqueId, 0) < 1) {
                                controlViolations.add(
                                        "required_method_body_not_entered:" + factoryMethod + ":" + uniqueId);
                            } else {
                                bodyCompletedMethods.add(factoryMethod);
                                bodyCompletionsByTest.put(uniqueId,
                                        bodyCompletionsByTest.getOrDefault(uniqueId, 0) + 1);
                            }
                        }
                    }
                    if ("FAILED".equals(status) || "ABORTED".equals(status)) {
                        containersFailed++;
                    }
                }
                if (!"SUCCESSFUL".equals(status) && !className.isEmpty()) {
                    nonSuccessful.put(className, nonSuccessful.getOrDefault(className, 0) + 1);
                }
            } else if ("SKIPPED".equals(phase)) {
                if (isTest) testsSkipped++;
            } else if ("VIOLATION".equals(phase)) {
                String violation = detail.isEmpty() ? uniqueId : detail;
                if (violation.startsWith("candidate_junit_control_code:")
                        || violation.startsWith("candidate_jvm_capability:")) {
                    controlViolations.add(violation);
                } else {
                    originViolations.add(violation);
                }
            } else {
                protocolViolations.add("unknown_phase:" + phase);
            }
        }

        String receipt(String observerStatus, String vmDescription) {
            Set<String> missing = new TreeSet<>(selected);
            missing.removeAll(observedClasses);
            Set<String> missingBodies = new TreeSet<>(requiredMethods);
            missingBodies.removeAll(bodyCompletedMethods);
            if (!activeTestIds.isEmpty()) protocolViolations.add("active_tests_at_receipt");
            long found = testsStarted + testsSkipped;
            boolean pass = "COMPLETE".equals(observerStatus)
                    && startSeen && completeSeen
                    && protocolViolations.isEmpty()
                    && originViolations.isEmpty()
                    && controlViolations.isEmpty()
                    && missing.isEmpty()
                    && missingBodies.isEmpty()
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
            out.append("  \"receipt_authentication\": \"trusted_parent_hmac_sha256\",\n");
            out.append("  \"receipt_key_in_candidate_jvm\": false,\n");
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
            out.append("  \"trusted_required_methods\": ").append(jsonStrings(requiredMethods)).append(",\n");
            out.append("  \"body_entered_methods\": ").append(jsonStrings(bodyEnteredMethods)).append(",\n");
            out.append("  \"body_completed_methods\": ").append(jsonStrings(bodyCompletedMethods)).append(",\n");
            out.append("  \"methods_never_body_completed\": ").append(jsonStrings(missingBodies)).append(",\n");
            out.append("  \"method_body_entries_by_test\": ").append(jsonMap(bodyEntriesByTest)).append(",\n");
            out.append("  \"method_body_completions_by_test\": ").append(jsonMap(bodyCompletionsByTest)).append(",\n");
            out.append("  \"class_code_origins\": ").append(jsonMap(classOrigins)).append(",\n");
            out.append("  \"code_origin_violations\": ").append(jsonStrings(originViolations)).append(",\n");
            out.append("  \"control_violations\": ").append(jsonStrings(controlViolations)).append(",\n");
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

    private static void installBreakpoints(
            ReferenceType type,
            EventRequestManager manager,
            Set<String> handledClasses,
            Set<String> requiredMethods,
            Set<Location> hookLocations,
            Map<Location, String> bodyLocations,
            State state) {
        if (!handledClasses.add(type.name())) return;
        if (HOOK_CLASS.equals(type.name())) {
            for (com.sun.jdi.Method method : type.methods()) {
                if (!HOOK_METHODS.contains(method.name())) continue;
                Location location = method.location();
                if (location == null) {
                    state.protocolViolations.add("hook_location_unavailable:" + method.name());
                    continue;
                }
                if (hookLocations.contains(location)) continue;
                BreakpointRequest request = manager.createBreakpointRequest(location);
                request.setSuspendPolicy(EventRequest.SUSPEND_EVENT_THREAD);
                request.enable();
                hookLocations.add(location);
            }
            return;
        }
        for (com.sun.jdi.Method method : type.methods()) {
            String identity;
            try {
                identity = methodIdentity(method);
            } catch (RuntimeException exc) {
                continue;
            }
            if (!requiredMethods.contains(identity)) continue;
            Location location = method.location();
            if (location == null) continue;
            if (bodyLocations.containsKey(location)) continue;
            BreakpointRequest request = manager.createBreakpointRequest(location);
            request.setSuspendPolicy(EventRequest.SUSPEND_EVENT_THREAD);
            request.enable();
            bodyLocations.put(location, identity);
        }
    }

    public static void main(String[] argv) throws Exception {
        String module = "";
        String sha = "";
        String tree = "";
        Path output = null;
        Path receipt = null;
        Path receiptMac = null;
        Path authKeyFile = null;
        Set<String> selected = new LinkedHashSet<>();
        Set<String> requiredMethods = new LinkedHashSet<>();
        for (int i = 0; i < argv.length; i++) {
            switch (argv[i]) {
                case "--module-id": module = argv[++i]; break;
                case "--bind-sha": sha = argv[++i]; break;
                case "--bind-tree": tree = argv[++i]; break;
                case "--module-output": output = Paths.get(argv[++i]); break;
                case "--receipt": receipt = Paths.get(argv[++i]); break;
                case "--receipt-mac": receiptMac = Paths.get(argv[++i]); break;
                case "--auth-key-file": authKeyFile = Paths.get(argv[++i]); break;
                case "--select": selected.add(argv[++i]); break;
                case "--require-method": requiredMethods.add(argv[++i]); break;
                default: throw new IllegalArgumentException("unknown argument " + argv[i]);
            }
        }
        if (module.isEmpty() || sha.isEmpty() || tree.isEmpty() || output == null
                || receipt == null || receiptMac == null || authKeyFile == null || selected.isEmpty()) {
            throw new IllegalArgumentException("observer binding arguments are incomplete");
        }
        byte[] receiptKey = Files.readAllBytes(authKeyFile);
        if (receiptKey.length < 32) throw new IllegalArgumentException("observer authentication key is too short");

        ListeningConnector connector = socketListener();
        Map<String, Connector.Argument> listenArgs = connector.defaultArguments();
        if (listenArgs.containsKey("localAddress")) listenArgs.get("localAddress").setValue("127.0.0.1");
        if (listenArgs.containsKey("port")) listenArgs.get("port").setValue("0");
        if (listenArgs.containsKey("timeout")) listenArgs.get("timeout").setValue("120000");
        String address = connector.startListening(listenArgs);
        System.out.println("TRUSTED_OBSERVER_LISTENING " + address);
        System.out.flush();

        State state = new State(module, sha, tree, output, selected, requiredMethods);
        String observerStatus = "INCOMPLETE";
        String vmDescription = "";
        VirtualMachine vm = null;
        try {
            vm = connector.accept(listenArgs);
            connector.stopListening(listenArgs);
            vmDescription = vm.name() + " " + vm.version();

            EventRequestManager manager = vm.eventRequestManager();

            // Only required test classes are prepared with a filter. ClassPrepare
            // stops the VM so every body breakpoint is in place before any of the
            // class's code can run. Each class gets its own request: HotSpot does
            // not match a ClassPrepare request that carries more than one class
            // filter (observed on JDK 17.0.20; a single-filter request works).
            // The hook class is in a named module and does not match a
            // ClassPrepare class filter at all, so it is bootstrapped below.
            Set<String> requiredDeclaringClasses = new TreeSet<>();
            for (String identity : requiredMethods) requiredDeclaringClasses.add(declaringClass(identity));
            for (String className : requiredDeclaringClasses) {
                ClassPrepareRequest prepare = manager.createClassPrepareRequest();
                prepare.addClassFilter(className);
                prepare.setSuspendPolicy(EventRequest.SUSPEND_ALL);
                prepare.enable();
            }

            // The hook class is loaded by the module layer and its ClassPrepare
            // event cannot be filtered by name. A method-entry request on the
            // hook class is observed until its first event, which hands us the
            // ReferenceType; the observer then installs the hook breakpoints and
            // disables the method-entry request immediately. The request exists
            // for a few driver-startup methods only, so the global JIT penalty of
            // method-entry events (the original hang) lasts microseconds.
            MethodEntryRequest hookBootstrap = manager.createMethodEntryRequest();
            hookBootstrap.addClassFilter(HOOK_CLASS);
            hookBootstrap.setSuspendPolicy(EventRequest.SUSPEND_ALL);
            hookBootstrap.enable();

            Set<Location> hookLocations = new LinkedHashSet<>();
            Map<Location, String> bodyLocations = new LinkedHashMap<>();
            Set<String> handledClasses = new LinkedHashSet<>();

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
                    // EventSet is a Set, not a causally ordered list. HotSpot may
                    // batch the trusted STARTED hook, the required body entry and
                    // the FINISHED hook in one set. Processing FINISHED first
                    // would erase the thread correlation before the body entry is
                    // observed and fabricate a "body not entered" failure.
                    // Re-impose only the causal partial order qualification needs:
                    // class prepare -> STARTED -> body ENTRY -> other hooks -> VM end.
                    List<ClassPrepareEvent> prepared = new ArrayList<>();
                    List<BreakpointEvent> hookStarted = new ArrayList<>();
                    List<BreakpointEvent> bodyEntered = new ArrayList<>();
                    List<BreakpointEvent> otherHooks = new ArrayList<>();
                    List<Event> terminalEvents = new ArrayList<>();

                    for (Event event : set) {
                        if (event instanceof ClassPrepareEvent) {
                            prepared.add((ClassPrepareEvent) event);
                        } else if (event instanceof MethodEntryEvent) {
                            // Hook-class bootstrap: the first method entry in the
                            // driver gives us its ReferenceType. Install the hook
                            // breakpoints and drop the method-entry request in the
                            // same stop-the-world window, before any hook runs.
                            MethodEntryEvent entry = (MethodEntryEvent) event;
                            ReferenceType type = entry.method().declaringType();
                            if (HOOK_CLASS.equals(type.name())) {
                                hookBootstrap.disable();
                                installBreakpoints(type, manager, handledClasses, requiredMethods,
                                        hookLocations, bodyLocations, state);
                                if (HOOK_METHODS.contains(entry.method().name())) {
                                    state.hook(entry.method().name(), args(entry),
                                            entry.thread().uniqueID());
                                }
                            }
                        } else if (event instanceof BreakpointEvent) {
                            BreakpointEvent hit = (BreakpointEvent) event;
                            Location location = hit.location();
                            if (hookLocations.contains(location)) {
                                String name = hit.location().method().name();
                                if ("observerEvent".equals(name)) {
                                    List<Value> values;
                                    try {
                                        values = args(hit);
                                    } catch (IncompatibleThreadStateException exc) {
                                        state.protocolViolations.add(
                                                "hook_arguments_unavailable:" + name);
                                        continue;
                                    }
                                    if (values.size() == 9 && "STARTED".equals(text(values.get(0)))) {
                                        hookStarted.add(hit);
                                    } else {
                                        otherHooks.add(hit);
                                    }
                                } else {
                                    otherHooks.add(hit);
                                }
                            } else {
                                bodyEntered.add(hit);
                            }
                        } else if (event instanceof VMDeathEvent
                                || event instanceof VMDisconnectEvent) {
                            terminalEvents.add(event);
                        }
                    }

                    for (ClassPrepareEvent event : prepared) {
                        installBreakpoints(event.referenceType(), manager, handledClasses,
                                requiredMethods, hookLocations, bodyLocations, state);
                    }
                    for (BreakpointEvent hit : hookStarted) {
                        state.hook(hit.location().method().name(), args(hit), hit.thread().uniqueID());
                    }
                    for (BreakpointEvent hit : bodyEntered) {
                        String identity = bodyLocations.get(hit.location());
                        if (identity != null && requiredMethods.contains(identity)) {
                            state.bodyEntry(hit.thread().uniqueID(), identity);
                        }
                    }
                    for (BreakpointEvent hit : otherHooks) {
                        state.hook(hit.location().method().name(), args(hit), hit.thread().uniqueID());
                    }
                    for (Event event : terminalEvents) {
                        if (event instanceof VMDeathEvent
                                || event instanceof VMDisconnectEvent) {
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
        String receiptText = state.receipt(observerStatus, vmDescription);
        byte[] receiptBytes = receiptText.getBytes(StandardCharsets.UTF_8);
        Files.write(receipt, receiptBytes);
        String receiptHmac = hmacHex(receiptKey, receiptBytes);
        Files.write(receiptMac, (receiptHmac + "\n").getBytes(StandardCharsets.US_ASCII));
        Arrays.fill(receiptKey, (byte)0);
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
