// C12 contained test executor.
//
// This class is trusted default-branch source but it is NOT a witness producer.
// It runs in the candidate OS identity and contains no secret, signing key,
// trusted receipt path or qualification verdict authority. A separate trusted
// parent JVM observes entries into the private observer* hooks through JDI and
// writes the only receipt that can earn qualification credit.
//
// The driver is compiled into a named module with no exported/open packages.
// Candidate bytecode therefore cannot invoke the private hooks through normal
// linkage or deep reflection. A containment SecurityManager additionally denies
// hostile candidate code the capabilities needed to escape the process boundary
// or discover/tamper with the already-connected observer channel.

package c12.trusted;

import java.io.FileDescriptor;
import java.io.IOException;
import java.lang.reflect.ReflectPermission;
import java.net.InetAddress;
import java.net.URI;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.security.Permission;
import java.security.ProtectionDomain;
import java.security.SecurityPermission;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import org.junit.platform.engine.DiscoverySelector;
import org.junit.platform.engine.TestEngine;
import org.junit.platform.engine.TestExecutionResult;
import org.junit.platform.engine.discovery.DiscoverySelectors;
import org.junit.platform.engine.support.descriptor.ClassSource;
import org.junit.platform.engine.support.descriptor.MethodSource;
import org.junit.platform.launcher.Launcher;
import org.junit.platform.launcher.core.LauncherConfig;
import org.junit.platform.launcher.LauncherDiscoveryRequest;
import org.junit.platform.launcher.TestExecutionListener;
import org.junit.platform.launcher.TestIdentifier;
import org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder;
import org.junit.platform.launcher.core.LauncherFactory;

public final class TrustedTestDriver {
    private static final Set<String> ALLOWED_ENGINES =
            new HashSet<>(java.util.Arrays.asList("junit-jupiter", "junit-vintage"));
    private static final Set<String> ALLOWED_TRUSTED_JUNIT4_RULE_TYPES =
            new HashSet<>(java.util.Arrays.asList(
                    "org.junit.rules.TestName",
                    "org.junit.rules.TemporaryFolder"));
    // JUnit's own runners only. A custom runner can swallow a failing assertion
    // and still fire a green lifecycle, so custom runners (trusted or candidate)
    // are refused before discovery. The current trusted corpus contains no
    // @RunWith at all; a future default-branch baseline that adds one has to
    // update this allowlist explicitly, which fails closed until it does.
    private static final Set<String> ALLOWED_TRUSTED_JUNIT4_RUNNERS =
            new HashSet<>(java.util.Arrays.asList(
                    "org.junit.runners.BlockJUnit4ClassRunner",
                    "org.junit.runners.Parameterized",
                    "org.junit.runners.Suite",
                    "org.junit.experimental.theories.Theories",
                    "org.junit.internal.runners.JUnit38ClassRunner"));
    // JDI observes method ENTRY and reads only immutable primitive/String args.
    // The bodies intentionally do nothing. They are private and the driver
    // module is not exported/open to the candidate unnamed module.
    private static void observerStart() { }

    private static void observerEvent(
            String phase,
            String engine,
            String uniqueId,
            boolean isTest,
            String className,
            String methodIdentity,
            String status,
            String origin,
            String detail) { }

    private static void observerComplete() { }

    private static final class CodeSourceStub {
        private final String location;
        private CodeSourceStub(String location) { this.location = location; }
    }

    private static CodeSourceStub codeSourceOf(Class<?> loaded) {
        try {
            ProtectionDomain domain = loaded.getProtectionDomain();
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

    private static boolean underAny(Path source, List<Path> prefixes) {
        Path normalized = source.toAbsolutePath().normalize();
        for (Path prefix : prefixes) {
            if (normalized.startsWith(prefix.toAbsolutePath().normalize())) return true;
        }
        return false;
    }

    /**
     * True when the defining loader is a JVM builtin loader: bootstrap, the
     * platform loader or the system/application loader. Only these loaders
     * have the JDK's default {@code findLibrary} (returns null) and cannot
     * attach a caller-supplied ProtectionDomain; a class defined by any other
     * loader is candidate-origin even when it asserts a jrt:/trusted
     * CodeSource, because {@code defineClass(..., ProtectionDomain)} accepts
     * whatever PD the candidate passes.
     */
    private static boolean builtinLoader(ClassLoader loader) {
        return loader == null
                || loader == ClassLoader.getSystemClassLoader()
                || loader == ClassLoader.getPlatformClassLoader();
    }

    private static boolean untrustedControlType(Class<?> type, List<Path> untrustedPrefixes) {
        // Structural classification first: a class defined by a non-builtin
        // loader is candidate-origin regardless of the ProtectionDomain it
        // asserts (defineClass accepts a caller-supplied PD, including a
        // forged jrt: CodeSource).
        if (!builtinLoader(type.getClassLoader())) return true;
        CodeSourceStub stub = codeSourceOf(type);
        if (stub.location == null) {
            return type.getClassLoader() != null;
        }
        try {
            return underAny(Paths.get(stub.location), untrustedPrefixes);
        } catch (RuntimeException exc) {
            return true;
        }
    }

    private static String rejectControlType(
            String kind, Class<?> type, List<Path> untrustedPrefixes, String where) {
        if (!untrustedControlType(type, untrustedPrefixes)) return null;
        CodeSourceStub stub = codeSourceOf(type);
        return "candidate_junit_control_code:" + kind + ":" + type.getName()
                + ":" + where + ":origin=" + (stub.location == null ? "UNKNOWN" : stub.location);
    }

    private static String inspectControlAnnotation(
            java.lang.annotation.Annotation annotation,
            List<Path> untrustedPrefixes,
            String where,
            Set<Class<?>> seenAnnotations) {
        Class<?> annotationType = annotation.annotationType();
        if (!seenAnnotations.add(annotationType)) return null;
        String name = annotationType.getName();
        try {
            if (name.equals("org.junit.runner.RunWith")
                    || name.equals("org.junit.jupiter.api.extension.ExtendWith")
                    || name.equals("org.junit.jupiter.params.provider.ArgumentsSource")
                    || name.equals("org.junit.jupiter.params.converter.ConvertWith")
                    || name.equals("org.junit.jupiter.params.aggregator.AggregateWith")) {
                Object value = annotationType.getMethod("value").invoke(annotation);
                if (value instanceof Class<?>) {
                    String violation = rejectControlType(
                            name, (Class<?>) value, untrustedPrefixes, where);
                    if (violation != null) return violation;
                    if (name.equals("org.junit.runner.RunWith")) {
                        String runner = ((Class<?>) value).getName();
                        if (!ALLOWED_TRUSTED_JUNIT4_RUNNERS.contains(runner)) {
                            return "candidate_junit_control_code:unapproved_runner_type:"
                                    + runner + ":" + where;
                        }
                    }
                } else if (value instanceof Class<?>[]) {
                    for (Class<?> type : (Class<?>[]) value) {
                        String violation = rejectControlType(
                                name, type, untrustedPrefixes, where);
                        if (violation != null) return violation;
                        if (name.equals("org.junit.runner.RunWith")
                                && !ALLOWED_TRUSTED_JUNIT4_RUNNERS.contains(type.getName())) {
                            return "candidate_junit_control_code:unapproved_runner_type:"
                                    + type.getName() + ":" + where;
                        }
                    }
                } else {
                    return "candidate_junit_control_code:malformed_control_annotation:"
                            + name + ":" + where;
                }
            } else if (name.equals("org.junit.jupiter.params.provider.MethodSource")) {
                Object value = annotationType.getMethod("value").invoke(annotation);
                if (!(value instanceof String[])) {
                    return "candidate_junit_control_code:malformed_method_source:" + where;
                }
                for (String ref : (String[]) value) {
                    int hash = ref.indexOf('#');
                    if (hash <= 0) continue;
                    String owner = ref.substring(0, hash);
                    Class<?> source = Class.forName(
                            owner, false, Thread.currentThread().getContextClassLoader());
                    String violation = rejectControlType(
                            name, source, untrustedPrefixes, where);
                    if (violation != null) return violation;
                }
            }

            for (java.lang.annotation.Annotation meta : annotationType.getDeclaredAnnotations()) {
                if (meta.annotationType().getName().startsWith("java.lang.annotation.")) continue;
                String violation = inspectControlAnnotation(
                        meta, untrustedPrefixes, where + "->@" + name, seenAnnotations);
                if (violation != null) return violation;
            }
            return null;
        } catch (ReflectiveOperationException | LinkageError | RuntimeException exc) {
            return "candidate_junit_control_code:unresolved_control_annotation:"
                    + name + ":" + where + ":" + exc.getClass().getName();
        }
    }

    private static String inspectAnnotatedElement(
            java.lang.reflect.AnnotatedElement element,
            List<Path> untrustedPrefixes,
            String where) {
        try {
            for (java.lang.annotation.Annotation annotation : element.getDeclaredAnnotations()) {
                String violation = inspectControlAnnotation(
                        annotation, untrustedPrefixes, where, new HashSet<Class<?>>());
                if (violation != null) return violation;
            }
            // JUnit parameter-level controls (`@ConvertWith`, `@AggregateWith`)
            // are declared on method (or constructor) parameters, never on the
            // element itself.
            java.lang.annotation.Annotation[][] parameters = null;
            if (element instanceof java.lang.reflect.Method) {
                parameters = ((java.lang.reflect.Method) element).getParameterAnnotations();
            } else if (element instanceof java.lang.reflect.Constructor) {
                parameters = ((java.lang.reflect.Constructor<?>) element).getParameterAnnotations();
            }
            if (parameters != null) {
                for (int index = 0; index < parameters.length; index++) {
                    for (java.lang.annotation.Annotation annotation : parameters[index]) {
                        String violation = inspectControlAnnotation(
                                annotation, untrustedPrefixes,
                                where + "#parameter" + index, new HashSet<Class<?>>());
                        if (violation != null) return violation;
                    }
                }
            }
            return null;
        } catch (LinkageError | RuntimeException | java.lang.annotation.AnnotationFormatError exc) {
            return "candidate_junit_control_code:unresolved_annotations:"
                    + where + ":" + exc.getClass().getName();
        }
    }

    private static boolean hasDirectAnnotation(
            java.lang.reflect.AnnotatedElement element, String annotationName) {
        for (java.lang.annotation.Annotation annotation : element.getDeclaredAnnotations()) {
            if (annotationName.equals(annotation.annotationType().getName())) return true;
        }
        return false;
    }

    private static String inspectExecutionControls(
            Class<?> type, List<Path> untrustedPrefixes, Set<Class<?>> seenTypes) {
        if (type == null || type == Object.class || !seenTypes.add(type)) return null;
        String violation = inspectAnnotatedElement(
                type, untrustedPrefixes, "class:" + type.getName());
        if (violation != null) return violation;
        try {
            for (java.lang.reflect.Field field : type.getDeclaredFields()) {
                String where = "field:" + type.getName() + "#" + field.getName();
                violation = inspectAnnotatedElement(field, untrustedPrefixes, where);
                if (violation != null) return violation;
                boolean junit4Rule = hasDirectAnnotation(field, "org.junit.Rule")
                        || hasDirectAnnotation(field, "org.junit.ClassRule");
                if (junit4Rule) {
                    String ownerViolation = rejectControlType(
                            "registered_rule_owner", field.getDeclaringClass(),
                            untrustedPrefixes, where);
                    if (ownerViolation != null) return ownerViolation;
                    Class<?> ruleType = field.getType();
                    String typeViolation = rejectControlType(
                            "registered_rule", ruleType, untrustedPrefixes, where);
                    if (typeViolation != null) return typeViolation;
                    if (!ALLOWED_TRUSTED_JUNIT4_RULE_TYPES.contains(ruleType.getName())) {
                        return "candidate_junit_control_code:unapproved_trusted_rule_type:"
                                + ruleType.getName() + ":" + where;
                    }
                }
                if (hasDirectAnnotation(
                        field, "org.junit.jupiter.api.extension.RegisterExtension")) {
                    return "candidate_junit_control_code:registered_member:" + where;
                }
            }
            for (java.lang.reflect.Constructor<?> constructor : type.getDeclaredConstructors()) {
                String where = "constructor:" + type.getName();
                violation = inspectAnnotatedElement(constructor, untrustedPrefixes, where);
                if (violation != null) return violation;
            }
            for (java.lang.reflect.Method method : type.getDeclaredMethods()) {
                String where = "method:" + type.getName() + "#" + method.getName();
                violation = inspectAnnotatedElement(method, untrustedPrefixes, where);
                if (violation != null) return violation;
                boolean junit4Rule = hasDirectAnnotation(method, "org.junit.Rule")
                        || hasDirectAnnotation(method, "org.junit.ClassRule");
                if (junit4Rule) {
                    String ownerViolation = rejectControlType(
                            "registered_rule_owner", method.getDeclaringClass(),
                            untrustedPrefixes, where);
                    if (ownerViolation != null) return ownerViolation;
                    Class<?> ruleType = method.getReturnType();
                    String typeViolation = rejectControlType(
                            "registered_rule", ruleType, untrustedPrefixes, where);
                    if (typeViolation != null) return typeViolation;
                    if (!ALLOWED_TRUSTED_JUNIT4_RULE_TYPES.contains(ruleType.getName())) {
                        return "candidate_junit_control_code:unapproved_trusted_rule_type:"
                                + ruleType.getName() + ":" + where;
                    }
                }
                if (hasDirectAnnotation(
                        method, "org.junit.jupiter.api.extension.RegisterExtension")) {
                    return "candidate_junit_control_code:registered_member:" + where;
                }
            }
            for (Class<?> iface : type.getInterfaces()) {
                violation = inspectExecutionControls(iface, untrustedPrefixes, seenTypes);
                if (violation != null) return violation;
            }
            // JUnit discovery also runs @Nested classes, and their annotations
            // can register candidate-origin extensions/runners. Inspect them
            // with the same rules instead of trusting the top-level class only.
            for (Class<?> nested : type.getDeclaredClasses()) {
                violation = inspectExecutionControls(nested, untrustedPrefixes, seenTypes);
                if (violation != null) return violation;
            }
            return inspectExecutionControls(type.getSuperclass(), untrustedPrefixes, seenTypes);
        } catch (LinkageError | RuntimeException exc) {
            return "candidate_junit_control_code:preflight_unresolved:"
                    + type.getName() + ":" + exc.getClass().getName();
        }
    }

    private static String executionControlViolation(
            String className, List<Path> untrustedPrefixes) {
        try {
            Class<?> type = Class.forName(
                    className, false, Thread.currentThread().getContextClassLoader());
            return inspectExecutionControls(type, untrustedPrefixes, new HashSet<Class<?>>());
        } catch (ClassNotFoundException | LinkageError | RuntimeException exc) {
            return "candidate_junit_control_code:preflight_unresolved:"
                    + className + ":" + exc.getClass().getName();
        }
    }

    private static String topLevel(String className) {
        int dollar = className.indexOf('$');
        return dollar > 0 ? className.substring(0, dollar) : className;
    }

    private static String engineOf(TestIdentifier identifier) {
        try {
            return identifier.getUniqueIdObject().getEngineId().orElse("?");
        } catch (RuntimeException exc) {
            return "?";
        }
    }

    private static boolean hasUniqueIdSegment(TestIdentifier identifier, String type) {
        try {
            for (org.junit.platform.engine.UniqueId.Segment segment
                    : identifier.getUniqueIdObject().getSegments()) {
                if (type.equals(segment.getType())) return true;
            }
        } catch (RuntimeException ignored) {
            // Unrecognized identifiers fail closed elsewhere.
        }
        return false;
    }

    private static boolean isJupiterFactoryContainer(
            String engine, TestIdentifier identifier) {
        return "junit-jupiter".equals(engine)
                && !identifier.isTest()
                && hasUniqueIdSegment(identifier, "test-factory");
    }

    private static boolean isJupiterDynamicTest(
            String engine, TestIdentifier identifier) {
        return "junit-jupiter".equals(engine)
                && identifier.isTest()
                && hasUniqueIdSegment(identifier, "dynamic-test");
    }

    private static String classNameOf(TestIdentifier identifier) {
        if (identifier.getSource().isPresent()
                && identifier.getSource().get() instanceof MethodSource) {
            return ((MethodSource)identifier.getSource().get()).getClassName();
        }
        if (identifier.getSource().isPresent()
                && identifier.getSource().get() instanceof ClassSource) {
            return ((ClassSource)identifier.getSource().get()).getClassName();
        }
        String legacy = identifier.getLegacyReportingName();
        int hash = legacy.indexOf('#');
        int paren = legacy.indexOf('(');
        int cut = legacy.length();
        if (hash >= 0) cut = Math.min(cut, hash);
        if (paren >= 0) cut = Math.min(cut, paren);
        return legacy.substring(0, cut);
    }

    private static String identityOf(java.lang.reflect.Method method) {
        StringBuilder identity = new StringBuilder(method.getDeclaringClass().getName());
        identity.append("#").append(method.getName()).append("(");
        Class<?>[] parameters = method.getParameterTypes();
        for (int i = 0; i < parameters.length; i++) {
            if (i > 0) identity.append(",");
            identity.append(parameters[i].getTypeName());
        }
        return identity.append(")").toString();
    }

    private static String methodIdentityOf(MethodSource source)
            throws ReflectiveOperationException {
        try {
            return identityOf(source.getJavaMethod());
        } catch (RuntimeException exc) {
            // Vintage Parameterized may decorate the source method as proof[0].
            // Strip only the invocation suffix and accept a unique reflected
            // declaration. Ambiguity earns no observation.
            String name = source.getMethodName();
            int bracket = name.indexOf('[');
            if (bracket >= 0) name = name.substring(0, bracket);
            Class<?> owner = Class.forName(
                    source.getClassName(), false,
                    Thread.currentThread().getContextClassLoader());
            java.lang.reflect.Method hit = null;
            for (java.lang.reflect.Method method : owner.getMethods()) {
                if (!method.getName().equals(name)) continue;
                if (hit != null) {
                    throw new IllegalStateException("ambiguous decorated method " + source);
                }
                hit = method;
            }
            if (hit == null) {
                for (java.lang.reflect.Method method : owner.getDeclaredMethods()) {
                    if (!method.getName().equals(name)) continue;
                    if (hit != null) {
                        throw new IllegalStateException("ambiguous decorated method " + source);
                    }
                    hit = method;
                }
            }
            if (hit == null) throw new NoSuchMethodException(source.toString());
            return identityOf(hit);
        }
    }

    private static String vintageMethodIdentityOf(TestIdentifier identifier)
            throws ReflectiveOperationException {
        List<org.junit.platform.engine.UniqueId.Segment> segments =
                identifier.getUniqueIdObject().getSegments();
        org.junit.platform.engine.UniqueId.Segment last = segments.get(segments.size() - 1);
        String value = last.getValue();
        int open = value.indexOf('(');
        if (!"test".equals(last.getType()) || open <= 0 || !value.endsWith(")")) {
            throw new IllegalStateException("not a vintage test id: " + identifier.getUniqueId());
        }
        String name = value.substring(0, open);
        int invocation = name.indexOf('[');
        if (invocation >= 0) name = name.substring(0, invocation);
        String className = value.substring(open + 1, value.length() - 1);
        Class<?> owner = Class.forName(
                className, false, Thread.currentThread().getContextClassLoader());
        java.lang.reflect.Method method = owner.getMethod(name);
        boolean junit4Test = false;
        for (java.lang.annotation.Annotation annotation : method.getAnnotations()) {
            junit4Test |= "org.junit.Test".equals(annotation.annotationType().getName());
        }
        if (!junit4Test) {
            throw new IllegalStateException("not a JUnit 4 test method: " + identifier.getUniqueId());
        }
        return identityOf(method);
    }

    private static Path trustedJunit() {
        CodeSourceStub stub = codeSourceOf(LauncherFactory.class);
        if (stub.location == null) {
            throw new IllegalStateException("JUnit platform origin unknown");
        }
        return Paths.get(stub.location);
    }

    private static TestEngine[] trustedEngines(Path junitJar) {
        List<TestEngine> engines = new ArrayList<>();
        for (String name : new String[] {
                "org.junit.jupiter.engine.JupiterTestEngine",
                "org.junit.vintage.engine.VintageTestEngine"}) {
            try {
                Class<?> type = Class.forName(
                        name, false, TrustedTestDriver.class.getClassLoader());
                CodeSourceStub origin = codeSourceOf(type);
                if (origin.location == null
                        || !Paths.get(origin.location).equals(junitJar)) {
                    throw new IllegalStateException(
                            "engine " + name + " not from trusted JUnit jar: " + origin.location);
                }
                engines.add((TestEngine)type.getDeclaredConstructor().newInstance());
            } catch (ReflectiveOperationException | LinkageError exc) {
                throw new IllegalStateException("trusted engine unavailable: " + name, exc);
            }
        }
        if (engines.isEmpty()) throw new IllegalStateException("no trusted test engine");
        return engines.toArray(new TestEngine[0]);
    }

    /**
     * Containment after the repair is deliberately narrow. Its job is to protect
     * qualification authority, not to jail ordinary candidate code.
     *
     * What it protects, and why nothing weaker works:
     *
     * - {@code defineClassInPackage.c12.trusted} /
     *   {@code accessClassInPackage.c12.trusted}: candidate class loaders cannot
     *   create or address classes in the trusted hook package. Independent of
     *   this check the driver lives in a non-exported, non-open named module that
     *   the classpath loader cannot even load, so portable reflection
     *   ({@code Class.forName}, {@code setAccessible}, {@code MethodHandles
     *   .privateLookupIn}) cannot reach the hooks either; this is belt and
     *   braces.
     * - {@code setSecurityManager} / {@code setPolicy} /
     *   {@code createAccessControlContext}: the guard cannot be removed or its
     *   policy rewritten by candidate code.
     * - process exec, VM exit, non-loopback connect, multicast, Attach/JVMTI,
     *   JMX control and Unix-domain sockets: the candidate JVM cannot cross into
     *   the runner or the observer process.
     * - {@code /proc}, {@code /sys}, {@code /dev/fd} reads: candidate code cannot
     *   discover or inject into the already-connected JDWP socket or inspect
     *   other processes.
     *
     * What it deliberately no longer does: the pre-repair policy denied deep
     * reflection, class-loader creation, thread-group modification, context
     * class-loader changes, native library loading, context-classloader override,
     * property writes and socket listen/accept under any candidate frame. The
     * real trusted corpus needs every one of those in ordinary library code
     * (JAXB context creation, Mage's plugin class loader, H2 AUTO_SERVER native
     * sockets, thread pools). Those denials made the gate unable to execute the
     * trusted baseline at all (Mage #493: every Mage.Tests container failed with
     * ExceptionInInitializerError, and the witness died at the 18000s timeout),
     * so they were a correctness defect, not a security control. None of them
     * grants authority over the hook channel or over evidence; the authority
     * boundary is the module graph plus the trusted parent observer.
     *
     * Unsafe/ReflectionFactory: the JVM launches with the system module graph
     * minus {@code jdk.unsupported}, so {@code sun.misc.Unsafe} and
     * {@code sun.reflect.ReflectionFactory} cannot be loaded at all. Without
     * that exclusion, allowing deep reflection would let candidate code obtain
     * {@code MethodHandles.Lookup.IMPL_LOOKUP} through Unsafe and reach the
     * hooks.
     */
    @SuppressWarnings("removal")
    private static final class ContainmentSecurityManager extends SecurityManager {
        private final List<Path> untrustedPrefixes = new ArrayList<>();

        ContainmentSecurityManager(List<Path> prefixes) {
            for (Path path : prefixes) {
                this.untrustedPrefixes.add(path.toAbsolutePath().normalize());
            }
        }

        private static boolean loopback(String host) {
            return host == null || "localhost".equals(host) || "127.0.0.1".equals(host)
                    || "::1".equals(host) || "0:0:0:0:0:0:0:1".equals(host);
        }

        private void refuse(String capability) {
            throw new SecurityException("C12 containment denied " + capability);
        }

        private static boolean underAny(Path source, List<Path> prefixes) {
            for (Path prefix : prefixes) {
                if (source.startsWith(prefix)) return true;
            }
            return false;
        }

        /**
         * True when the code that initiated the current native-library load is
         * candidate code. JDK frames (jrt: code source) are skipped: trusted JDK
         * internals and trusted dependencies routinely load their own native
         * libraries beneath candidate frames (H2 sockets load jdk.net's extnet),
         * and those loads must keep working. The first non-JDK frame decides:
         * direct candidate {@code System.loadLibrary}/MethodHandle-laundered
         * loads have a candidate frame first; a JDK-internal load triggered by
         * trusted code has a trusted dependency or JDK frame first.
         */
        /**
         * The first class in the current call chain that is not trusted-driver
         * or JDK-internal code, or null when every frame is JDK code.
         * Structural classification comes first: a frame whose defining loader
         * is not a builtin loader is returned immediately, so a forged jrt:
         * CodeSource cannot make a candidate-defined class look like a JDK
         * frame. Only builtin-loader frames may use the jrt:/code-source rule
         * to be skipped.
         */
        private Class<?> initiatingFrame() {
            for (Class<?> type : getClassContext()) {
                if (type == ContainmentSecurityManager.class
                        || type == SecurityManager.class
                        || type.getName().startsWith("c12.trusted.")) {
                    continue;
                }
                ClassLoader loader = type.getClassLoader();
                if (!builtinLoader(loader)) {
                    return type;
                }
                if (loader == null) {
                    // Bootstrap-loader classes are JDK internals.
                    continue;
                }
                String location;
                try {
                    java.security.ProtectionDomain domain = type.getProtectionDomain();
                    if (domain == null || domain.getCodeSource() == null
                            || domain.getCodeSource().getLocation() == null) {
                        return type;
                    }
                    location = java.net.URI.create(
                            domain.getCodeSource().getLocation().toString()).toString();
                } catch (RuntimeException exc) {
                    return type;
                }
                if (location.startsWith("jrt:")) continue;
                return type;
            }
            return null;
        }

        private boolean candidateInitiatesNativeLoad() {
            Class<?> initiator = initiatingFrame();
            if (initiator == null) return false;
            ClassLoader loader = initiator.getClassLoader();
            if (!builtinLoader(loader)) return true;
            if (loader == null) return false;
            try {
                java.security.ProtectionDomain domain = initiator.getProtectionDomain();
                if (domain == null || domain.getCodeSource() == null
                        || domain.getCodeSource().getLocation() == null) {
                    // Builtin-loader application frames without a code source
                    // fail closed as candidate-origin.
                    return true;
                }
                String location = java.net.URI.create(
                        domain.getCodeSource().getLocation().toString()).toString();
                if (location.startsWith("jrt:")) return false;
                Path source = Paths.get(java.net.URI.create(location))
                        .toAbsolutePath().normalize();
                return underAny(source, untrustedPrefixes);
            } catch (RuntimeException exc) {
                return true;
            }
        }

        @Override public void checkExit(int status) { refuse("vm-exit"); }
        @Override public void checkExec(String cmd) { refuse("process-exec"); }
        @Override public void checkConnect(String host, int port) {
            if (!loopback(host)) refuse("socket-connect");
        }
        @Override public void checkConnect(String host, int port, Object context) { checkConnect(host, port); }
        @Override public void checkMulticast(InetAddress maddr) { refuse("socket-multicast"); }

        @Override public void checkLink(String lib) {
            // JNI is outside the module system: a candidate native library could
            // reach JVMTI/JDWP and the VM internals, so it must never execute
            // from a path the candidate identity can control.
            //
            // Library *names* resolve only from java.library.path and
            // sun.boot.library.path through a builtin loader's default
            // findLibrary, whose sealing is a fail-closed startup
            // precondition; a candidate-defined loader can override
            // findLibrary and return any file, which NativeLibraries then
            // dlopen's without another checkLink, so name loads from
            // non-builtin loaders are refused. An absolute load is the other
            // candidate-influenced shape: a candidate can plant a file
            // anywhere it can write (for example /tmp or /var/tmp) and may
            // clear the write bit on it, so current writability proves nothing
            // about control. Candidate-initiated absolute loads are therefore
            // allowed only when the exact resolved target and every ancestor
            // directory are root-owned, non-writable system paths and the
            // lexical path is not a symlink: then no component can be
            // replaced between this check and dlopen. JDK internals (for
            // example libawt_xawt.so under a candidate-triggered lazy init)
            // keep working; a candidate-written file anywhere
            // candidate-controllable is refused even after chmod. Trusted
            // dependency loads (sqlite's extracted loader) are not
            // candidate-initiated and are unaffected.
            if (lib == null) return;
            boolean absolute = new java.io.File(lib).isAbsolute();
            if (!candidateInitiatesNativeLoad()) return;
            if (!absolute) {
                Class<?> initiator = initiatingFrame();
                if (initiator == null || !builtinLoader(initiator.getClassLoader())) {
                    refuse("loadLibrary-custom-loader:" + lib);
                }
                return;
            }
            Path lexical = Paths.get(lib).toAbsolutePath().normalize();
            Path real;
            try {
                real = lexical.toRealPath();
            } catch (java.io.IOException exc) {
                refuse("loadLibrary-unresolvable:" + lib);
                return;
            }
            if (underAny(real, untrustedPrefixes)) {
                refuse("loadLibrary:" + lib);
                return;
            }
            if (!real.equals(lexical)) {
                // The kernel resolves the lexical path at dlopen time; a link
                // whose component could be rewritten would reopen the window.
                refuse("loadLibrary-symlink:" + lib);
                return;
            }
            for (Path cursor = real; cursor != null; cursor = cursor.getParent()) {
                if (!rootOwnedNonWritable(cursor)) {
                    refuse("loadLibrary-untrusted-path:" + lib);
                    return;
                }
            }
        }

        @Override public void checkRead(String file) {
            if (file != null) {
                String normalized = Paths.get(file).toAbsolutePath().normalize().toString();
                if (normalized.equals("/proc") || normalized.startsWith("/proc/")
                        || normalized.equals("/sys") || normalized.startsWith("/sys/")
                        || normalized.equals("/dev/fd") || normalized.startsWith("/dev/fd/")) {
                    refuse("fd-or-kernel-discovery");
                }
            }
        }

        @Override public void checkRead(String file, Object context) { checkRead(file); }

        @Override public void checkPermission(Permission permission) {
            if (permission == null) return;
            String name = permission.getName();
            String permissionType = permission.getClass().getName();
            // Public management/attach APIs can load agents or execute VM
            // diagnostics; Unix-domain sockets are gated separately from TCP.
            if ("com.sun.tools.attach.AttachPermission".equals(permissionType)
                    || "javax.management.MBeanPermission".equals(permissionType)
                    || "javax.management.MBeanServerPermission".equals(permissionType)
                    || "javax.management.MBeanTrustPermission".equals(permissionType)
                    || ("java.lang.management.ManagementPermission".equals(permissionType)
                        && "control".equals(name))
                    || ("java.net.NetPermission".equals(permissionType)
                        && "accessUnixDomainSocket".equals(name))) {
                refuse("capability-permission:" + permissionType + ":" + name);
                return;
            }
            if (permission instanceof RuntimePermission) {
                if ("setSecurityManager".equals(name)
                        || "manageProcess".equals(name)
                        || "stopThread".equals(name)
                        || name.startsWith("accessClassInPackage.c12.trusted")
                        || name.startsWith("defineClassInPackage.c12.trusted")) {
                    refuse("runtime-permission:" + name);
                }
                return;
            }
            if (permission instanceof SecurityPermission) {
                if ("setPolicy".equals(name)
                        || "createAccessControlContext".equals(name)
                        || "getDomainCombiner".equals(name)
                        || name.startsWith("setProperty.")
                        || name.startsWith("insertProvider")
                        || name.startsWith("removeProvider")) {
                    refuse("security-permission:" + name);
                }
            }
        }
    }

    private static void initializeTrustedRuntimeBeforeContainment() {
        // JUnit Platform initializes java.util.logging lazily while building the
        // discovery request. LogManager's one-time JDK initialization requests
        // RuntimePermission("shutdownHooks"). Perform that trusted bootstrap
        // before the containment boundary is installed; shutdown-hook authority
        // remains unconditionally denied for all post-boundary execution.
        java.util.logging.LogManager.getLogManager();
    }

    /**
     * The JDK reflection-loader admission relies on java.base keeping its
     * internal packages closed to classpath code: otherwise candidate code
     * could construct or extend the admitted loader type directly. The trusted
     * launcher passes no such flags; refuse to run if the JVM was started with
     * any (for example --add-opens/--add-exports java.base/jdk.internal.*).
     */
    private static void requireJdkInternalsSealed() {
        Module base = Object.class.getModule();
        Module unnamed = ClassLoader.getSystemClassLoader().getUnnamedModule();
        for (String pkg : new String[] {
                "jdk.internal.reflect", "jdk.internal.misc",
                "jdk.internal.access", "jdk.internal.loader"}) {
            if (base.isExported(pkg, unnamed) || base.isOpen(pkg, unnamed)) {
                throw new IllegalStateException(
                        "C12 containment precondition failed: java.base/" + pkg
                        + " is exported or opened to classpath code");
            }
        }
    }

    /**
     * True only when {@code path} is owned by root (uid 0) and cannot be
     * written by the candidate identity (this process runs as that identity).
     * Current mode alone is not enough: a candidate-owned file stays
     * candidate-controlled even after chmod clears its write bit, and a
     * candidate-writable ancestor directory allows replacing a file between a
     * check and its use.
     */
    private static boolean rootOwnedNonWritable(Path path) {
        try {
            Object uid = java.nio.file.Files.getAttribute(
                    path, "unix:uid", java.nio.file.LinkOption.NOFOLLOW_LINKS);
            if (!(uid instanceof Integer) || ((Integer) uid).intValue() != 0) {
                return false;
            }
            java.util.Set<java.nio.file.attribute.PosixFilePermission> permissions =
                    java.nio.file.Files.getPosixFilePermissions(
                            path, java.nio.file.LinkOption.NOFOLLOW_LINKS);
            if (permissions.contains(java.nio.file.attribute.PosixFilePermission.GROUP_WRITE)
                    || permissions.contains(java.nio.file.attribute.PosixFilePermission.OTHERS_WRITE)) {
                return false;
            }
            return !java.nio.file.Files.isWritable(path);
        } catch (java.io.IOException | RuntimeException exc) {
            return false;
        }
    }

    /**
     * The native library search paths are fixed at JVM startup. If any entry is
     * writable by the candidate identity or inside a candidate prefix, a
     * candidate could plant a same-named library and have trusted code load it.
     * A missing entry is only safe when its nearest existing ancestor cannot be
     * written or created into by the candidate; the loader would then find
     * nothing there and the entry cannot be materialized. Fail closed before
     * containment instead.
     */
    private static void requireLibraryPathSealed(List<Path> untrustedPrefixes) {
        for (String property : new String[] {"java.library.path", "sun.boot.library.path"}) {
            String libraryPath = System.getProperty(property, "");
            for (String entry : libraryPath.split(java.io.File.pathSeparator)) {
                if (entry.isBlank()) continue;
                Path path;
                try {
                    path = Paths.get(entry).toAbsolutePath().normalize();
                } catch (RuntimeException exc) {
                    throw new IllegalStateException(
                            "C12 containment precondition failed: unreadable " + property + " entry");
                }
                for (Path prefix : untrustedPrefixes) {
                    if (path.startsWith(prefix.toAbsolutePath().normalize())) {
                        throw new IllegalStateException(
                                "C12 containment precondition failed: " + property
                                        + " entry is under a candidate prefix: " + path);
                    }
                }
                Path existing = path;
                while (existing != null
                        && !java.nio.file.Files.exists(
                                existing, java.nio.file.LinkOption.NOFOLLOW_LINKS)) {
                    existing = existing.getParent();
                }
                if (existing == null) {
                    throw new IllegalStateException(
                            "C12 containment precondition failed: " + property
                                    + " entry has no existing ancestor: " + path);
                }
                Path realExisting;
                try {
                    realExisting = existing.toRealPath();
                } catch (java.io.IOException exc) {
                    throw new IllegalStateException(
                            "C12 containment precondition failed: " + property
                                    + " entry is unresolvable: " + existing);
                }
                for (Path prefix : untrustedPrefixes) {
                    if (realExisting.startsWith(prefix.toAbsolutePath().normalize())) {
                        throw new IllegalStateException(
                                "C12 containment precondition failed: " + property
                                        + " entry resolves under a candidate prefix: " + path);
                    }
                }
                for (Path cursor = realExisting; cursor != null; cursor = cursor.getParent()) {
                    if (!rootOwnedNonWritable(cursor)) {
                        throw new IllegalStateException(
                                "C12 containment precondition failed: " + property
                                        + " entry is not a sealed root-owned path: " + path);
                    }
                }
            }
        }
    }

    @SuppressWarnings("removal")
    private static void installContainment(List<Path> untrustedPrefixes) {
        System.setSecurityManager(new ContainmentSecurityManager(untrustedPrefixes));
    }

    public static void main(String[] args) throws Exception {
        String moduleOutput = "";
        List<String> selected = new ArrayList<>();
        List<Path> untrustedPrefixes = new ArrayList<>();
        for (int i = 0; i < args.length; i++) {
            switch (args[i]) {
                case "--module-output": moduleOutput = args[++i]; break;
                case "--select": selected.add(args[++i]); break;
                case "--untrusted-prefix": untrustedPrefixes.add(Paths.get(args[++i])); break;
                default: throw new IllegalArgumentException("unknown argument " + args[i]);
            }
        }
        if (moduleOutput.isEmpty() || selected.isEmpty() || untrustedPrefixes.isEmpty()) {
            throw new IllegalArgumentException(
                    "--module-output, --untrusted-prefix and --select are required");
        }

        final Path expectedOutput = Paths.get(moduleOutput).toRealPath();
        initializeTrustedRuntimeBeforeContainment();
        requireJdkInternalsSealed();
        requireLibraryPathSealed(untrustedPrefixes);
        installContainment(untrustedPrefixes);
        observerStart();

        // A trusted JUnit engine can report SUCCESSFUL without invoking the
        // trusted test body when candidate-built code supplies a runner,
        // extension or provider. Refuse that execution authority before
        // discovery; lifecycle events alone are not qualification proof.
        for (String className : selected) {
            String violation = executionControlViolation(className, untrustedPrefixes);
            if (violation != null) {
                observerEvent("VIOLATION", "junit-jupiter", "c12-preflight:" + className,
                        false, className, "", "", "", violation);
                observerComplete();
                return;
            }
        }

        TestExecutionListener witness = new TestExecutionListener() {
            @Override
            public void executionStarted(TestIdentifier identifier) {
                String engine = engineOf(identifier);
                if (!ALLOWED_ENGINES.contains(engine)) {
                    observerEvent("VIOLATION", engine, identifier.getUniqueId(),
                            identifier.isTest(), "", "", "", "",
                            "foreign engine " + engine + " for " + identifier.getUniqueId());
                    return;
                }
                boolean factoryContainer = isJupiterFactoryContainer(engine, identifier);
                boolean dynamicTest = isJupiterDynamicTest(engine, identifier);
                String method = "";
                boolean vintageTest = identifier.isTest() && "junit-vintage".equals(engine);
                if (vintageTest) {
                    // A Vintage test id names exactly one public no-argument
                    // @org.junit.Test method. Resolving it from the id is exact
                    // even when the class inherits same-named overloads (Mage's
                    // CardTestPlayerAPIImpl.attack(int, TestPlayer, String) next
                    // to a test method attack()), where the name-only MethodSource
                    // fallback below is ambiguous and would drop the observation.
                    try {
                        method = vintageMethodIdentityOf(identifier);
                    } catch (ReflectiveOperationException | RuntimeException unresolved) {
                        method = "";
                    }
                }
                if (method.isEmpty()
                        && !dynamicTest
                        && identifier.getSource().isPresent()
                        && identifier.getSource().get() instanceof MethodSource) {
                    try {
                        method = methodIdentityOf((MethodSource)identifier.getSource().get());
                    } catch (ReflectiveOperationException | RuntimeException exc) {
                        observerEvent("VIOLATION", engine, identifier.getUniqueId(),
                                identifier.isTest(), "", "", "", "",
                                "unresolved_method_identity:" + identifier.getUniqueId());
                    }
                }
                // An unresolved required Vintage method remains unobserved and fails closed.

                String className = "";
                String origin = "";
                if (identifier.isTest() || factoryContainer) {
                    try {
                        className = topLevel(classNameOf(identifier));
                        Class<?> loaded = Class.forName(
                                className, false,
                                Thread.currentThread().getContextClassLoader());
                        CodeSourceStub stub = codeSourceOf(loaded);
                        origin = stub.location == null ? "" : stub.location;
                    } catch (RuntimeException | ClassNotFoundException exc) {
                        observerEvent("VIOLATION", engine, identifier.getUniqueId(),
                                identifier.isTest(), className, method, "", origin,
                                "class_origin_unverified:" + className + ":" + exc.getClass().getName());
                    }
                }
                observerEvent("STARTED", engine, identifier.getUniqueId(),
                        identifier.isTest(), className, method, "", origin, "");
            }

            @Override
            public void executionSkipped(TestIdentifier identifier, String reason) {
                String engine = engineOf(identifier);
                String className = identifier.isTest() ? topLevel(classNameOf(identifier)) : "";
                observerEvent("SKIPPED", engine, identifier.getUniqueId(),
                        identifier.isTest(), className, "", "SKIPPED", "", reason == null ? "" : reason);
            }

            @Override
            public void executionFinished(
                    TestIdentifier identifier, TestExecutionResult result) {
                String engine = engineOf(identifier);
                boolean factoryContainer = isJupiterFactoryContainer(engine, identifier);
                String className = (identifier.isTest() || factoryContainer)
                        ? topLevel(classNameOf(identifier)) : "";
                observerEvent("FINISHED", engine, identifier.getUniqueId(),
                        identifier.isTest(), className, "",
                        result.getStatus().name(), "", "");
            }
        };

        List<DiscoverySelector> selectors = new ArrayList<>();
        for (String className : selected) {
            selectors.add(DiscoverySelectors.selectClass(className));
        }

        LauncherDiscoveryRequest request = LauncherDiscoveryRequestBuilder.request()
                .selectors(selectors)
                .enableImplicitConfigurationParameters(false)
                .configurationParameter("junit.jupiter.extensions.autodetection.enabled", "false")
                .configurationParameter("junit.jupiter.conditions.deactivate", "")
                .configurationParameter("junit.platform.output.capture.stdout", "false")
                .build();

        LauncherConfig config = LauncherConfig.builder()
                .enableTestEngineAutoRegistration(false)
                .enablePostDiscoveryFilterAutoRegistration(false)
                .enableLauncherSessionListenerAutoRegistration(false)
                .enableLauncherDiscoveryListenerAutoRegistration(false)
                .enableTestExecutionListenerAutoRegistration(false)
                .addTestEngines(trustedEngines(trustedJunit()))
                .build();

        Launcher launcher = LauncherFactory.create(config);
        launcher.execute(request, witness);
        observerComplete();
    }
}
