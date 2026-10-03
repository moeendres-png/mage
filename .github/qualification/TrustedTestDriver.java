// Trusted test-execution driver.
//
// This file is trusted default-branch source. The trusted side compiles it and
// runs it; the candidate never supplies, edits or observes it. It exists because
// candidate-authored test evidence cannot be trusted: a candidate POM, plugin,
// lifecycle hook or test can create, suppress or forge any file under its own
// tree, including target/surefire-reports/TEST-*.xml.
//
// So the driver, not the candidate's build, owns the execution: it selects the
// test classes the trusted side enumerated, drives them through the JUnit
// Platform Launcher, and writes the counts it observed itself. Nothing here
// parses a candidate-produced report.
//
// Residual limit, stated rather than hidden: test bytecode executes in this JVM.
// A candidate whose test code deliberately drives this listener through
// reflection is outside what any same-JVM qualification can rule out. That is a
// semantic-coverage question for C13/C16, not a provenance question C12 can
// close; see README "Trust boundary and its limits".

import java.io.IOException;
import java.io.PrintWriter;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeSet;

import org.junit.platform.engine.DiscoverySelector;
import org.junit.platform.engine.discovery.DiscoverySelectors;
import org.junit.platform.engine.support.descriptor.ClassSource;
import org.junit.platform.engine.support.descriptor.MethodSource;
import org.junit.platform.launcher.Launcher;
import org.junit.platform.launcher.LauncherDiscoveryRequest;
import org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder;
import org.junit.platform.launcher.core.LauncherFactory;
import org.junit.platform.launcher.listeners.SummaryGeneratingListener;
import org.junit.platform.launcher.listeners.TestExecutionSummary;
import org.junit.platform.engine.TestExecutionResult;
import org.junit.platform.launcher.TestExecutionListener;
import org.junit.platform.launcher.TestIdentifier;

public final class TrustedTestDriver {

    private static String classNameOf(TestIdentifier identifier) {
        // JUnit 5 reports a method-level identifier whose legacy name is the bare
        // method name, so the typed source is the only reliable way to attribute an
        // execution to the class the trusted side selected. MethodSource is checked
        // explicitly because it is the shape seen for JUnit Jupiter test methods.
        if (identifier.getSource().isPresent()
                && identifier.getSource().get() instanceof MethodSource) {
            return ((MethodSource) identifier.getSource().get()).getClassName();
        }
        if (identifier.getSource().isPresent()
                && identifier.getSource().get() instanceof ClassSource) {
            return ((ClassSource) identifier.getSource().get()).getClassName();
        }
        String legacy = identifier.getLegacyReportingName();
        int hash = legacy.indexOf('#');
        int paren = legacy.indexOf('(');
        int cut = legacy.length();
        if (hash >= 0) {
            cut = Math.min(cut, hash);
        }
        if (paren >= 0) {
            cut = Math.min(cut, paren);
        }
        return legacy.substring(0, cut);
    }

    private static final class CodeSourceStub {
        private final String location;

        private CodeSourceStub(String location) {
            this.location = location;
        }
    }

    private static CodeSourceStub codeSourceOf(Class<?> loaded) {
        try {
            java.security.ProtectionDomain domain = loaded.getProtectionDomain();
            if (domain == null || domain.getCodeSource() == null
                    || domain.getCodeSource().getLocation() == null) {
                return new CodeSourceStub(null);
            }
            URI uri = domain.getCodeSource().getLocation().toURI();
            return new CodeSourceStub(Paths.get(uri).toString());
        } catch (Exception exc) {
            return new CodeSourceStub(null);
        }
    }

    private static String topLevel(String className) {
        // JUnit 5 @Nested classes report as Outer$Inner. The trusted enumeration is
        // over source files, so credit must be attributed to the enclosing top-level
        // class; otherwise a required class containing @Nested tests would look
        // never-entered purely because its own inner tests ran.
        int dollar = className.indexOf('$');
        return dollar > 0 ? className.substring(0, dollar) : className;
    }

    private static String jsonEscape(String value) {
        StringBuilder out = new StringBuilder();
        for (int i = 0; i < value.length(); i++) {
            char c = value.charAt(i);
            switch (c) {
                case '"':
                    out.append("\\\"");
                    break;
                case '\\':
                    out.append("\\\\");
                    break;
                case '\n':
                    out.append("\\n");
                    break;
                case '\r':
                    out.append("\\r");
                    break;
                case '\t':
                    out.append("\\t");
                    break;
                default:
                    if (c < 0x20) {
                        out.append(String.format("\\u%04x", (int) c));
                    } else {
                        out.append(c);
                    }
            }
        }
        return out.toString();
    }

    private static String quoted(Set<String> values) {
        StringBuilder out = new StringBuilder("[");
        boolean first = true;
        for (String value : values) {
            if (!first) {
                out.append(",");
            }
            first = false;
            out.append("\"").append(jsonEscape(value)).append("\"");
        }
        return out.append("]").toString();
    }

    public static void main(String[] args) throws IOException {
        Path evidence = null;
        String classPath = "";
        String bindSha = "";
        String bindTree = "";
        String moduleId = "";
        String moduleOutput = "";
        List<String> selected = new ArrayList<>();

        for (int i = 0; i < args.length; i++) {
            switch (args[i]) {
                case "--evidence":
                    evidence = Paths.get(args[++i]);
                    break;
                case "--class-path":
                    classPath = args[++i];
                    break;
                case "--bind-sha":
                    bindSha = args[++i];
                    break;
                case "--bind-tree":
                    bindTree = args[++i];
                    break;
                case "--module-id":
                    moduleId = args[++i];
                    break;
                case "--module-output":
                    moduleOutput = args[++i];
                    break;
                case "--select":
                    selected.add(args[++i]);
                    break;
                default:
                    System.err.println("TrustedTestDriver: unknown argument " + args[i]);
                    System.exit(3);
            }
        }

        if (evidence == null || classPath.isEmpty() || selected.isEmpty()) {
            System.err.println(
                "TrustedTestDriver: --evidence, --class-path and at least one --select are required");
            System.exit(3);
        }

        // Per-module execution context. A required class must resolve from its own
        // module's output directory, never from a sibling module or a jar that
        // happens to sit earlier on the classpath. Without this check a collision
        // could credit a required test to the wrong module.
        Path resolvedOutput = null;
        if (!moduleOutput.isEmpty()) {
            try {
                resolvedOutput = Paths.get(moduleOutput).toRealPath();
            } catch (IOException exc) {
                System.err.println("TrustedTestDriver: module output not resolvable: " + exc);
                System.exit(3);
            }
        }
        final Path expectedOutput = resolvedOutput;

        // Record which selected classes the launcher actually reached. A class the
        // trusted side required but the launcher never entered cannot be reported as
        // green by anything, including a file the candidate wrote.
        final Set<String> observedClasses = new TreeSet<>();
        final Map<String, Integer> failuresByClass = new LinkedHashMap<>();
        final Map<String, String> classOrigins = new LinkedHashMap<>();
        final Set<String> originViolations = new TreeSet<>();

        TestExecutionListener witness = new TestExecutionListener() {
            @Override
            public void executionStarted(TestIdentifier identifier) {
                if (!identifier.isTest()) {
                    return;
                }
                String className = topLevel(classNameOf(identifier));
                observedClasses.add(className);
                if (expectedOutput == null) {
                    return;
                }
                try {
                    ClassLoader loader = Thread.currentThread().getContextClassLoader();
                    Class<?> loaded = Class.forName(className, false, loader);
                    CodeSourceStub stub = codeSourceOf(loaded);
                    classOrigins.put(className, stub.location);
                    if (stub.location == null || !stub.location.startsWith(expectedOutput.toString())) {
                        originViolations.add(className + " loaded from " + stub.location
                                + " (expected under " + expectedOutput + ")");
                    }
                } catch (ClassNotFoundException | RuntimeException exc) {
                    originViolations.add(className + " origin could not be verified: " + exc);
                }
            }

            @Override
            public void executionFinished(TestIdentifier identifier, TestExecutionResult result) {
                if (result.getStatus() != TestExecutionResult.Status.SUCCESSFUL) {
                    failuresByClass.merge(topLevel(classNameOf(identifier)), 1, Integer::sum);
                }
            }
        };

        SummaryGeneratingListener summaryListener = new SummaryGeneratingListener();

        List<DiscoverySelector> selectors = new ArrayList<>();
        for (String className : selected) {
            selectors.add(DiscoverySelectors.selectClass(className));
        }

        LauncherDiscoveryRequest request = LauncherDiscoveryRequestBuilder.request()
                .selectors(selectors)
                // The trusted enumeration is the whole world for this campaign. A
                // candidate cannot widen or narrow it.
                .build();

        Launcher launcher = LauncherFactory.create();
        launcher.execute(request, witness, summaryListener);

        TestExecutionSummary summary = summaryListener.getSummary();
        Set<String> required = new LinkedHashSet<>(selected);
        Set<String> missing = new LinkedHashSet<>(required);
        missing.removeAll(observedClasses);

        long testsFound = summary.getTestsFoundCount();
        long testsRun = summary.getTestsStartedCount();
        long succeeded = summary.getTestsSucceededCount();
        long failed = summary.getTestsFailedCount();
        long aborted = summary.getTestsAbortedCount();
        long skipped = summary.getTestsSkippedCount();
        long containersFailed = summary.getContainersFailedCount();

        List<String> failureMessages = new ArrayList<>();
        for (org.junit.platform.launcher.listeners.TestExecutionSummary.Failure failure : summary.getFailures()) {
            String message = failure.getException() == null
                    ? String.valueOf(failure.getException())
                    : String.valueOf(failure.getException().getMessage());
            failureMessages.add(failure.getTestIdentifier().getDisplayName() + ": " + message);
        }

        boolean pass = missing.isEmpty()
                && originViolations.isEmpty()
                && testsFound > 0
                && testsRun > 0
                && failed == 0
                && aborted == 0
                && containersFailed == 0
                && skipped < testsFound;

        StringBuilder json = new StringBuilder();
        json.append("{\n");
        json.append("  \"schema\": \"mage.candidate-qualification.trusted-execution-witness/1\",\n");
        json.append("  \"producer\": \"TrustedTestDriver\",\n");
        json.append("  \"evidence_origin\": \"trusted_side_direct_execution\",\n");
        json.append("  \"candidate_authored_evidence_used\": false,\n");
        json.append("  \"module_id\": \"").append(jsonEscape(moduleId)).append("\",\n");
        json.append("  \"module_output\": \"").append(jsonEscape(moduleOutput)).append("\",\n");
        json.append("  \"code_origin_enforced\": ").append(expectedOutput != null).append(",\n");
        json.append("  \"bound_candidate_sha\": \"").append(jsonEscape(bindSha)).append("\",\n");
        json.append("  \"bound_candidate_tree\": \"").append(jsonEscape(bindTree)).append("\",\n");
        json.append("  \"trusted_selected_classes\": ").append(selected.size()).append(",\n");
        json.append("  \"trusted_selected_class_names\": ").append(quoted(new TreeSet<>(selected))).append(",\n");
        json.append("  \"observed_classes\": ").append(quoted(observedClasses)).append(",\n");
        json.append("  \"classes_never_entered\": ").append(quoted(missing)).append(",\n");
        json.append("  \"class_code_origins\": {");
        boolean firstOrigin = true;
        for (Map.Entry<String, String> entry : classOrigins.entrySet()) {
            if (!firstOrigin) {
                json.append(",");
            }
            firstOrigin = false;
            json.append("\"").append(jsonEscape(entry.getKey())).append("\": \"")
                    .append(jsonEscape(entry.getValue())).append("\"");
        }
        json.append("},\n");
        json.append("  \"code_origin_violations\": ").append(quoted(originViolations)).append(",\n");
        json.append("  \"tests_found\": ").append(testsFound).append(",\n");
        json.append("  \"tests_started\": ").append(testsRun).append(",\n");
        json.append("  \"tests_succeeded\": ").append(succeeded).append(",\n");
        json.append("  \"tests_failed\": ").append(failed).append(",\n");
        json.append("  \"tests_aborted\": ").append(aborted).append(",\n");
        json.append("  \"tests_skipped\": ").append(skipped).append(",\n");
        json.append("  \"containers_failed\": ").append(containersFailed).append(",\n");
        // Serialized by hand: Map.toString would emit Java's "k=v", which is not JSON.
        json.append("  \"non_successful_by_class\": {");
        boolean firstEntry = true;
        for (Map.Entry<String, Integer> entry : failuresByClass.entrySet()) {
            if (!firstEntry) {
                json.append(",");
            }
            firstEntry = false;
            json.append("\"").append(jsonEscape(entry.getKey())).append("\": ").append(entry.getValue());
        }
        json.append("},\n");
        json.append("  \"failures\": [");
        for (int i = 0; i < failureMessages.size(); i++) {
            if (i > 0) {
                json.append(",");
            }
            json.append("\"").append(jsonEscape(failureMessages.get(i))).append("\"");
        }
        json.append("],\n");
        json.append("  \"driver_verdict\": \"").append(pass ? "PASS" : "FAIL").append("\"\n");
        json.append("}\n");

        Files.createDirectories(evidence.toAbsolutePath().getParent());
        try (PrintWriter writer = new PrintWriter(
                Files.newBufferedWriter(evidence, StandardCharsets.UTF_8))) {
            writer.print(json);
        }

        System.out.println(
                "TRUSTED_EXECUTION module=" + (moduleId.isEmpty() ? "-" : moduleId)
                        + " selected=" + selected.size()
                        + " observed=" + observedClasses.size()
                        + " never_entered=" + missing.size()
                        + " origin_violations=" + originViolations.size()
                        + " found=" + testsFound
                        + " started=" + testsRun
                        + " succeeded=" + succeeded
                        + " failed=" + failed
                        + " aborted=" + aborted
                        + " skipped=" + skipped
                        + " verdict=" + (pass ? "PASS" : "FAIL"));

        System.exit(pass ? 0 : 1);
    }
}