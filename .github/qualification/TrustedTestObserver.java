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
import com.sun.jdi.event.BreakpointEvent;
import com.sun.jdi.event.ClassPrepareEvent;
import com.sun.jdi.event.VMDeathEvent;
import com.sun.jdi.event.VMDisconnectEvent;
import com.sun.jdi.request.EventRequest;
import com.sun.jdi.request.BreakpointRequest;
import com.sun.jdi.request.ClassPrepareRequest;
import com.sun.jdi.request.EventRequestManager;
import com.sun.jdi.Location;
import com.sun.jdi.ReferenceType;
import com.sun.jdi.StackFrame;
import com.sun.jdi.ThreadReference;

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
import java.util.HashSet;
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
            "mage.candidate-qualification.trusted-execution-witness/5";
    private static final String HOOK_CLASS = "c12.trusted.TrustedTestDriver";
    private static final String HOOK_MODULE = "c12.trusted";
    private static final Set<String> HOOK_METHODS =
            Set.of("observerStart", "observerEvent", "observerComplete");
    private static final String KIND = "c12.kind";
    private static final String KIND_HOOK = "hook";
    private static final String KIND_ENTRY = "body-entry";
    private static final String KIND_RETURN = "body-return";
    private static final String IDENTITY = "c12.identity";

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

    private static List<Value> args(BreakpointEvent event)
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
        final Map<String, Integer> bodyEntriesByTest = new TreeMap<>();
        final Map<String, Integer> bodyExitsByTest = new TreeMap<>();
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

        /** Returns the active test credited with this entry, or null. */
        String bodyEntry(long threadId, String identity) {
            String expected = activeMethods.get(threadId);
            String uniqueId = activeTestIds.get(threadId);
            if (uniqueId != null && identity.equals(expected)) {
                bodyEnteredMethods.add(identity);
                bodyEntriesByTest.put(uniqueId, bodyEntriesByTest.getOrDefault(uniqueId, 0) + 1);
                return uniqueId;
            }
            return null;
        }

        /**
         * A normal return of the very frame whose entry was credited to
         * {@code enteredFor}. Credit only while that same test is still active.
         */
        void bodyExit(long threadId, String identity, String enteredFor) {
            String expected = activeMethods.get(threadId);
            String uniqueId = activeTestIds.get(threadId);
            if (uniqueId != null && uniqueId.equals(enteredFor) && identity.equals(expected)
                    && bodyEntriesByTest.getOrDefault(uniqueId, 0) > 0) {
                bodyCompletedMethods.add(identity);
                bodyExitsByTest.put(uniqueId, bodyExitsByTest.getOrDefault(uniqueId, 0) + 1);
                // A TestFactory container stays active while its dynamic children
                // execute. Its authority-bearing method body, however, is complete
                // as soon as the factory method returns normally. Close the
                // correlation window here so dynamic child lifecycle events cannot
                // inherit or overwrite factory-method body credit.
                if (isJupiterFactoryUniqueId(uniqueId)) {
                    activeTestIds.remove(threadId);
                    activeMethods.remove(threadId);
                }
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
                if ((isTest || factoryMethod) && !method.isEmpty()) {
                    if (activeTestIds.containsKey(threadId)) {
                        protocolViolations.add("overlapping_test_on_thread:" + threadId);
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
                    // removal) earns no credit and owes no body receipt.
                    if ("SUCCESSFUL".equals(status) && activeMethod != null
                            && requiredMethods.contains(activeMethod)) {
                        if (bodyEntriesByTest.getOrDefault(uniqueId, 0) < 1
                                || bodyExitsByTest.getOrDefault(uniqueId, 0) < 1) {
                            controlViolations.add(
                                    "required_method_body_not_completed:" + activeMethod + ":" + uniqueId);
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
                            String activeMethod = activeMethods.remove(threadId);
                            if ("SUCCESSFUL".equals(status) && activeMethod != null
                                    && (bodyEntriesByTest.getOrDefault(uniqueId, 0) < 1
                                        || bodyExitsByTest.getOrDefault(uniqueId, 0) < 1)) {
                                controlViolations.add(
                                        "required_method_body_not_completed:" + activeMethod + ":" + uniqueId);
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
            out.append("  \"method_body_exits_by_test\": ").append(jsonMap(bodyExitsByTest)).append(",\n");
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

    /**
     * Instruction length of the JVM opcode at {@code pc} (JVMS chapter 6).
     * Unknown or reserved opcodes throw, so a method that cannot be decoded is
     * never armed and its body stays unproven (fail closed).
     */
    private static int instructionLength(byte[] code, int pc) {
        int op = code[pc] & 0xff;
        if (op <= 0x0f) return 1;
        switch (op) {
            case 0x10: case 0x12: case 0x15: case 0x16: case 0x17: case 0x18: case 0x19:
            case 0x36: case 0x37: case 0x38: case 0x39: case 0x3a: case 0xa9: case 0xbc:
                return 2;
            case 0x11: case 0x13: case 0x14: case 0x84: case 0xb2: case 0xb3: case 0xb4:
            case 0xb5: case 0xb6: case 0xb7: case 0xb8: case 0xbb: case 0xbd: case 0xc0:
            case 0xc1: case 0xc6: case 0xc7:
                return 3;
            case 0xc5:
                return 4;
            case 0xb9: case 0xba: case 0xc8: case 0xc9:
                return 5;
            case 0xc4:
                return (code[pc + 1] & 0xff) == 0x84 ? 6 : 4;
            case 0xaa: {
                int base = (pc + 4) & ~3;
                int low = readInt(code, base + 4);
                int high = readInt(code, base + 8);
                long length = base - pc + 12 + 4L * ((long) high - low + 1);
                if (high < low || length > code.length) {
                    throw new IllegalArgumentException("bad tableswitch at " + pc);
                }
                return (int) length;
            }
            case 0xab: {
                int base = (pc + 4) & ~3;
                int pairs = readInt(code, base + 4);
                long length = base - pc + 8 + 8L * pairs;
                if (pairs < 0 || length > code.length) {
                    throw new IllegalArgumentException("bad lookupswitch at " + pc);
                }
                return (int) length;
            }
            default:
                if ((op >= 0x1a && op <= 0x35) || (op >= 0x3b && op <= 0x83)
                        || (op >= 0x85 && op <= 0x98) || (op >= 0xac && op <= 0xb1)
                        || op == 0xbe || op == 0xbf || op == 0xc2 || op == 0xc3) {
                    return 1;
                }
                if (op >= 0x99 && op <= 0xa8) return 3;
                throw new IllegalArgumentException("undecodable opcode 0x"
                        + Integer.toHexString(op) + " at " + pc);
        }
    }

    private static int readInt(byte[] code, int at) {
        return ((code[at] & 0xff) << 24) | ((code[at + 1] & 0xff) << 16)
                | ((code[at + 2] & 0xff) << 8) | (code[at + 3] & 0xff);
    }

    /** Code indices of every return instruction (ireturn..return) in a method. */
    static List<Long> returnIndices(byte[] code) {
        List<Long> out = new ArrayList<>();
        int pc = 0;
        while (pc < code.length) {
            int op = code[pc] & 0xff;
            if (op >= 0xac && op <= 0xb1) out.add((long) pc);
            int length = instructionLength(code, pc);
            if (length <= 0 || pc + length > code.length) {
                throw new IllegalArgumentException("truncated instruction at " + pc);
            }
            pc += length;
        }
        return out;
    }

    /**
     * Arms breakpoints on the trusted hooks and on every required method body as
     * each class is prepared, and pairs each body return with its own entry.
     */
    private static final class Arming {
        private static final class Pending {
            final com.sun.jdi.Method method;
            final String identity;
            final int depth;
            final String enteredFor;
            Pending(com.sun.jdi.Method method, String identity, int depth, String enteredFor) {
                this.method = method;
                this.identity = identity;
                this.depth = depth;
                this.enteredFor = enteredFor;
            }
        }

        final EventRequestManager manager;
        final Set<String> requiredMethods;
        final State state;
        final Set<String> watchedClasses = new HashSet<>();
        final Set<ReferenceType> armedTypes = new HashSet<>();
        final Map<Long, List<Pending>> pending = new HashMap<>();
        int hookMethodsArmed;

        Arming(EventRequestManager manager, Set<String> requiredMethods, State state) {
            this.manager = manager;
            this.requiredMethods = requiredMethods;
            this.state = state;
        }

        /** One exact-name ClassPrepare request per class: cost is per class load only. */
        void watch(String className) {
            if (!watchedClasses.add(className)) return;
            ClassPrepareRequest prepare = manager.createClassPrepareRequest();
            prepare.addClassFilter(className);
            prepare.setSuspendPolicy(EventRequest.SUSPEND_ALL);
            prepare.enable();
        }

        private void breakpoint(Location location, String kind, String identity) {
            BreakpointRequest request = manager.createBreakpointRequest(location);
            request.putProperty(KIND, kind);
            if (identity != null) request.putProperty(IDENTITY, identity);
            request.setSuspendPolicy(EventRequest.SUSPEND_ALL);
            request.enable();
        }

        void arm(ReferenceType type) {
            String name = type.name();
            if (!watchedClasses.contains(name) || !type.isPrepared() || !armedTypes.add(type)) return;
            if (HOOK_CLASS.equals(name)) {
                // Only the class of the trusted, closed driver module carries the
                // hooks; a same-named class anywhere else is not the driver.
                com.sun.jdi.ModuleReference module = type.module();
                if (module == null || !HOOK_MODULE.equals(module.name())) {
                    state.protocolViolations.add("foreign_hook_class_loaded:"
                            + (module == null ? "?" : module.name()));
                } else {
                    for (com.sun.jdi.Method method : type.methods()) {
                        if (HOOK_METHODS.contains(method.name()) && method.isStatic()
                                && method.isPrivate()) {
                            breakpoint(method.locationOfCodeIndex(0), KIND_HOOK, null);
                            hookMethodsArmed++;
                        }
                    }
                }
            }
            for (com.sun.jdi.Method method : type.methods()) {
                if (method.isAbstract() || method.isNative()) continue;
                String identity;
                try {
                    identity = methodIdentity(method);
                } catch (IllegalArgumentException exc) {
                    continue;
                }
                if (!requiredMethods.contains(identity)) continue;
                try {
                    List<Long> returns = returnIndices(method.bytecodes());
                    Location entry = method.locationOfCodeIndex(0);
                    if (entry == null) throw new IllegalStateException("no code index 0");
                    List<Location> exits = new ArrayList<>();
                    for (long index : returns) {
                        Location exit = method.locationOfCodeIndex(index);
                        if (exit == null) throw new IllegalStateException("no code index " + index);
                        exits.add(exit);
                    }
                    breakpoint(entry, KIND_ENTRY, identity);
                    for (Location exit : exits) breakpoint(exit, KIND_RETURN, identity);
                } catch (RuntimeException exc) {
                    state.protocolViolations.add("required_method_not_armed:" + identity
                            + ":" + exc.getClass().getName());
                }
            }
        }

        private static boolean onStack(ThreadReference thread, Pending entry, int count)
                throws IncompatibleThreadStateException {
            return count >= entry.depth
                    && entry.method.equals(thread.frame(count - entry.depth).location().method());
        }

        /** Drop entries whose frame has left the stack without a normal return. */
        void forgetUnwound(ThreadReference thread) throws IncompatibleThreadStateException {
            List<Pending> open = pending.get(thread.uniqueID());
            if (open == null || open.isEmpty()) return;
            int count = thread.frameCount();
            open.removeIf(entry -> {
                try {
                    return !onStack(thread, entry, count);
                } catch (IncompatibleThreadStateException exc) {
                    return true;
                }
            });
        }

        void entered(BreakpointEvent hit) throws IncompatibleThreadStateException {
            ThreadReference thread = hit.thread();
            com.sun.jdi.Method method = hit.location().method();
            String identity = (String) hit.request().getProperty(IDENTITY);
            forgetUnwound(thread);
            int depth = thread.frameCount();
            List<Pending> open = pending.computeIfAbsent(thread.uniqueID(), k -> new ArrayList<>());
            for (Pending entry : open) {
                // Code index 0 can be a loop head: the same frame passing it
                // again is not a new invocation.
                if (entry.depth == depth && entry.method.equals(method)) return;
            }
            String enteredFor = state.bodyEntry(thread.uniqueID(), identity);
            open.add(new Pending(method, identity, depth, enteredFor));
        }

        void returned(BreakpointEvent hit) throws IncompatibleThreadStateException {
            ThreadReference thread = hit.thread();
            com.sun.jdi.Method method = hit.location().method();
            List<Pending> open = pending.get(thread.uniqueID());
            if (open == null) return;
            int depth = thread.frameCount();
            for (int i = open.size() - 1; i >= 0; i--) {
                Pending entry = open.get(i);
                if (entry.depth == depth && entry.method.equals(method)) {
                    open.remove(i);
                    if (entry.enteredFor != null) {
                        state.bodyExit(thread.uniqueID(), entry.identity, entry.enteredFor);
                    }
                    return;
                }
            }
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

            // Breakpoints, never MethodEntry/MethodExit requests. JDWP turns any
            // MethodEntry/MethodExit request into a VM-wide JVMTI event: HotSpot
            // then runs EVERY thread in interpreter-only mode and posts EVERY
            // method call and return in the JVM to the agent, which evaluates
            // every request's class filter for each of them. With one entry and
            // one exit request per required declaring class (about 2,000 in
            // Mage.Tests) that is thousands of filter evaluations per Java call,
            // interpreted, and the real-corpus witness ran for hours. A breakpoint
            // costs nothing outside its own location, and HotSpot keeps compiling
            // everything else.
            //
            // The proof is unchanged: a body ENTRY is the first bytecode of the
            // exact required method executing (code index 0); a body EXIT is that
            // same frame (same thread, same method, same stack depth) reaching one
            // of the method's own return instructions, i.e. a normal return.
            // Exceptional exits never execute a return instruction, exactly like
            // JDWP MethodExit, which does not report exception-popped frames.
            EventRequestManager manager = vm.eventRequestManager();
            if (!vm.canGetBytecodes()) {
                throw new IllegalStateException("target VM cannot report bytecodes");
            }
            Arming arming = new Arming(manager, requiredMethods, state);
            arming.watch(HOOK_CLASS);
            for (String identity : requiredMethods) arming.watch(declaringClass(identity));
            for (com.sun.jdi.ReferenceType loaded : vm.allClasses()) arming.arm(loaded);

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
                    // EventSet is a Set, not a causally ordered list. Breakpoints at
                    // one location share a set (an empty body's entry and return are
                    // both code index 0). Re-impose the causal partial order:
                    // class arming -> STARTED -> body ENTRY -> body RETURN -> other
                    // hooks -> VM end.
                    List<BreakpointEvent> hookStarted = new ArrayList<>();
                    List<BreakpointEvent> bodyEntered = new ArrayList<>();
                    List<BreakpointEvent> bodyReturned = new ArrayList<>();
                    List<BreakpointEvent> otherHooks = new ArrayList<>();
                    List<Event> terminalEvents = new ArrayList<>();

                    for (Event event : set) {
                        if (event instanceof ClassPrepareEvent) {
                            arming.arm(((ClassPrepareEvent) event).referenceType());
                        } else if (event instanceof BreakpointEvent) {
                            BreakpointEvent hit = (BreakpointEvent) event;
                            Object kind = hit.request().getProperty(KIND);
                            if (KIND_HOOK.equals(kind)) {
                                List<Value> values = args(hit);
                                if ("observerEvent".equals(hit.location().method().name())
                                        && values.size() == 9
                                        && "STARTED".equals(text(values.get(0)))) {
                                    hookStarted.add(hit);
                                } else {
                                    otherHooks.add(hit);
                                }
                            } else if (KIND_ENTRY.equals(kind)) {
                                bodyEntered.add(hit);
                            } else if (KIND_RETURN.equals(kind)) {
                                bodyReturned.add(hit);
                            }
                        } else if (event instanceof VMDeathEvent
                                || event instanceof VMDisconnectEvent) {
                            terminalEvents.add(event);
                        }
                    }

                    for (BreakpointEvent hit : hookStarted) {
                        arming.forgetUnwound(hit.thread());
                        state.hook(hit.location().method().name(), args(hit),
                                hit.thread().uniqueID());
                    }
                    for (BreakpointEvent hit : bodyEntered) arming.entered(hit);
                    for (BreakpointEvent hit : bodyReturned) arming.returned(hit);
                    for (BreakpointEvent hit : otherHooks) {
                        arming.forgetUnwound(hit.thread());
                        state.hook(hit.location().method().name(), args(hit),
                                hit.thread().uniqueID());
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
            if (arming.hookMethodsArmed != 3) {
                state.protocolViolations.add("observer_hooks_not_armed:" + arming.hookMethodsArmed);
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
