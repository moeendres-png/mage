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
import java.security.AccessController;
import java.security.Permission;
import java.security.Policy;
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
    private static final RuntimePermission CAPABILITY_PERMISSION =
            new RuntimePermission("c12.trustedCapability");

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

    private static boolean untrustedControlType(Class<?> type, List<Path> untrustedPrefixes) {
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
                } else if (value instanceof Class<?>[]) {
                    for (Class<?> type : (Class<?>[]) value) {
                        String violation = rejectControlType(
                                name, type, untrustedPrefixes, where);
                        if (violation != null) return violation;
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
            return null;
        } catch (LinkageError | RuntimeException exc) {
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

    @SuppressWarnings("removal")
    private static final class ContainmentPolicy extends Policy {
        private final Policy delegate;
        private final List<Path> untrustedPrefixes;

        ContainmentPolicy(Policy delegate, List<Path> prefixes) {
            this.delegate = delegate;
            this.untrustedPrefixes = new ArrayList<>();
            for (Path path : prefixes) {
                this.untrustedPrefixes.add(path.toAbsolutePath().normalize());
            }
        }

        private boolean untrustedDomain(ProtectionDomain domain) {
            if (domain == null || domain.getCodeSource() == null
                    || domain.getCodeSource().getLocation() == null) {
                return false;
            }
            try {
                Path source = Paths.get(domain.getCodeSource().getLocation().toURI())
                        .toAbsolutePath().normalize();
                return underAny(source, untrustedPrefixes);
            } catch (Exception exc) {
                // An opaque non-bootstrap application domain cannot gain the
                // capability marker merely because origin resolution failed.
                return domain.getClassLoader() != null;
            }
        }

        @Override
        public boolean implies(ProtectionDomain domain, Permission permission) {
            if (CAPABILITY_PERMISSION.equals(permission)) {
                return !untrustedDomain(domain);
            }
            return delegate == null || delegate.implies(domain, permission);
        }

        @Override
        public void refresh() {
            if (delegate != null) delegate.refresh();
        }
    }

    @SuppressWarnings("removal")
    private static final class ContainmentSecurityManager extends SecurityManager {
        private final List<Path> untrustedPrefixes;
        private final ThreadLocal<Boolean> inspecting =
                ThreadLocal.withInitial(() -> Boolean.FALSE);

        ContainmentSecurityManager(List<Path> prefixes) {
            this.untrustedPrefixes = new ArrayList<>();
            for (Path path : prefixes) {
                this.untrustedPrefixes.add(path.toAbsolutePath().normalize());
            }
        }

        private boolean untrustedOnStack() {
            if (inspecting.get()) return false;
            inspecting.set(Boolean.TRUE);
            try {
                for (Class<?> type : getClassContext()) {
                    String name = type.getName();
                    if (name.startsWith("c12.trusted.")) continue;
                    ProtectionDomain domain;
                    try {
                        domain = type.getProtectionDomain();
                    } catch (SecurityException exc) {
                        continue;
                    }
                    if (domain == null || domain.getCodeSource() == null
                            || domain.getCodeSource().getLocation() == null) {
                        continue;
                    }
                    try {
                        Path source = Paths.get(domain.getCodeSource().getLocation().toURI())
                                .toAbsolutePath().normalize();
                        for (Path prefix : untrustedPrefixes) {
                            if (source.startsWith(prefix)) return true;
                        }
                    } catch (Exception ignored) { }
                }
                return false;
            } finally {
                inspecting.set(Boolean.FALSE);
            }
        }

        /**
         * True only when the class loader under construction is the JDK's own
         * reflection accessor loader. Core reflection and serialization
         * (MethodAccessorGenerator, via ObjectStreamClass in JUnit's TestPlan,
         * for example) create one per generated accessor; it defines only
         * JDK-generated accessor bytecode in a JDK-chosen domain, so candidate
         * code can neither choose its bytes nor forge a trusted code source
         * through it. The type is identified by bootstrap-loader identity and
         * exact name, which candidate code cannot define. Every other loader,
         * URLClassLoader and candidate subclasses included, stays denied: a
         * new loader could define classes under an arbitrary code source and
         * so launder the provenance this boundary relies on.
         */
        private boolean constructingJdkReflectionLoader() {
            for (Class<?> type : getClassContext()) {
                if (type == ContainmentSecurityManager.class
                        || type == SecurityManager.class
                        || type == ClassLoader.class) {
                    continue;
                }
                // The first frame past ClassLoader's constructor checks is the
                // constructor of the concrete loader being created.
                return type.getClassLoader() == null
                        && "jdk.internal.reflect.DelegatingClassLoader".equals(type.getName());
            }
            return false;
        }

        @SuppressWarnings("removal")
        private void refuse(String capability) {
            boolean denied = untrustedOnStack();
            if (!denied) {
                try {
                    AccessController.checkPermission(CAPABILITY_PERMISSION);
                } catch (SecurityException exc) {
                    denied = true;
                }
            }
            if (denied) {
                throw new SecurityException("C12 containment denied " + capability);
            }
        }

        private void denyAlways(String capability) {
            // These capabilities are unnecessary to the trusted test launcher
            // once containment is installed and can directly cross the process
            // boundary or disable the boundary itself. Do not rely on stack or
            // AccessControlContext provenance here: AccessController.doPrivileged
            // and JDK-owned MethodHandle proxies can intentionally truncate the
            // caller context.
            throw new SecurityException("C12 containment denied " + capability);
        }

        @Override public void checkExit(int status) { denyAlways("vm-exit"); }
        @Override public void checkExec(String cmd) { denyAlways("process-exec"); }
        @Override public void checkConnect(String host, int port) { denyAlways("socket-connect"); }
        @Override public void checkConnect(String host, int port, Object context) { denyAlways("socket-connect"); }
        @Override public void checkListen(int port) { denyAlways("socket-listen"); }
        @Override public void checkAccept(String host, int port) { denyAlways("socket-accept"); }
        @Override public void checkMulticast(InetAddress maddr) { denyAlways("socket-multicast"); }

        @Override public void checkRead(String file) {
            if (file != null) {
                String normalized = Paths.get(file).toAbsolutePath().normalize().toString();
                if (normalized.equals("/proc") || normalized.startsWith("/proc/")
                        || normalized.equals("/sys") || normalized.startsWith("/sys/")
                        || normalized.equals("/dev/fd") || normalized.startsWith("/dev/fd/")) {
                    denyAlways("fd-or-kernel-discovery");
                }
            }
        }

        @Override public void checkRead(String file, Object context) { checkRead(file); }
        @Override public void checkRead(FileDescriptor fd) {
            // Existing ordinary descriptors are used by trusted runtime code.
            // Candidate discovery of descriptors by pathname is blocked above.
        }

        @Override public void checkPermission(Permission permission) {
            if (permission == null || inspecting.get()) return;
            String name = permission.getName();
            String permissionType = permission.getClass().getName();
            // Public management/attach APIs can cross the ordinary Java call
            // boundary and, in the case of Attach/JVMTI or DiagnosticCommand
            // MBeans, can load agents or execute VM diagnostics without calling
            // Runtime.loadLibrary from candidate code. Unix-domain sockets are
            // permission-gated separately from TCP checkConnect/checkListen.
            if ("com.sun.tools.attach.AttachPermission".equals(permissionType)
                    || "javax.management.MBeanPermission".equals(permissionType)
                    || "javax.management.MBeanServerPermission".equals(permissionType)
                    || "javax.management.MBeanTrustPermission".equals(permissionType)
                    || ("java.lang.management.ManagementPermission".equals(permissionType)
                        && "control".equals(name))
                    || ("java.net.NetPermission".equals(permissionType)
                        && "accessUnixDomainSocket".equals(name))) {
                denyAlways("capability-permission:" + permissionType + ":" + name);
                return;
            }
            if (permission instanceof ReflectPermission
                    && "suppressAccessChecks".equals(name)) {
                refuse("deep-reflection");
                return;
            }
            if (permission instanceof RuntimePermission) {
                if ("createClassLoader".equals(name) && constructingJdkReflectionLoader()) {
                    return;
                }
                if ("setSecurityManager".equals(name)
                        || "shutdownHooks".equals(name)
                        || "setIO".equals(name)
                        || "createClassLoader".equals(name)
                        || "setContextClassLoader".equals(name)
                        || "enableContextClassLoaderOverride".equals(name)
                        || "modifyThread".equals(name)
                        || "modifyThreadGroup".equals(name)
                        || "manageProcess".equals(name)
                        || "setDefaultUncaughtExceptionHandler".equals(name)
                        || "stopThread".equals(name)
                        || name.startsWith("loadLibrary.")
                        || name.startsWith("accessClassInPackage.sun.misc")
                        || name.startsWith("accessClassInPackage.jdk.internal.misc")
                        || name.startsWith("accessClassInPackage.c12.trusted")
                        || name.startsWith("defineClassInPackage.c12.trusted")) {
                    denyAlways("runtime-permission:" + name);
                    return;
                }
                if ("accessDeclaredMembers".equals(name)
                        || "getClassLoader".equals(name)) {
                    // JUnit/trusted tests legitimately need these. Keep the
                    // provenance check, with the ACC marker as defense in depth.
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
                    denyAlways("security-permission:" + name);
                }
            }
            if (permission instanceof java.util.PropertyPermission
                    && permission.getActions().contains("write")) {
                refuse("property-write:" + name);
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

    @SuppressWarnings("removal")
    private static void installContainment(List<Path> untrustedPrefixes) {
        Policy.setPolicy(new ContainmentPolicy(Policy.getPolicy(), untrustedPrefixes));
        SecurityManager manager = new ContainmentSecurityManager(untrustedPrefixes);
        SecurityManager ignored = System.getSecurityManager();
        System.setSecurityManager(manager);
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
                if (!dynamicTest
                        && identifier.getSource().isPresent()
                        && identifier.getSource().get() instanceof MethodSource) {
                    try {
                        method = methodIdentityOf((MethodSource)identifier.getSource().get());
                    } catch (ReflectiveOperationException | RuntimeException exc) {
                        observerEvent("VIOLATION", engine, identifier.getUniqueId(),
                                identifier.isTest(), "", "", "", "",
                                "unresolved_method_identity:" + identifier.getUniqueId());
                    }
                } else if (identifier.isTest() && "junit-vintage".equals(engine)) {
                    try {
                        method = vintageMethodIdentityOf(identifier);
                    } catch (ReflectiveOperationException | RuntimeException ignored) {
                        // A required Vintage method then remains unobserved and fails closed.
                    }
                }

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
