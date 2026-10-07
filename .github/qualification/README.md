# Trusted candidate qualification (C12)

This gate qualifies an exact Mage candidate SHA with rules the candidate cannot change, execute with
write authority over, or shrink.

## Why this exists

`.github/workflows/maven.yml` runs on `pull_request`, so its definition belongs to the
candidate: editing it edits the thing that judges it. The earlier C12 designs closed that
hole and then four more.

1. **Candidate reports.** Harvesting `target/surefire-reports/TEST-*.xml` proved nothing: a
   candidate POM, plugin, hook or test can author them. Candidate reports are no longer
   read anywhere (CTRL-16).
2. **Writable trust domain.** Candidate Maven and candidate tests ran as the same OS user
   that owned the trusted checkout, the validator and the evidence. A plugin bound to
   `initialize` (which the old audit did not cover) or a test could overwrite `qualify.py`,
   `witness.py`, the source lock or the evidence before the trusted steps ran.
3. **Candidate-controlled corpus.** The required tests were whatever the candidate tree
   enumerated. A candidate could therefore rename most `*Test` classes out of the class regex, move them out of
   `src/test/java` or delete them, and the witness would faithfully run what was left.
4. **Non-functional wiring**, found during this repair:
   - The guard job called the selftest with `--mvn`, but the selftest only accepts `--maven`. The guard job therefore always errored before running any control.
   - The classpath step fed modules through a quoted heredoc, so `$(…)` never expanded.

   Neither gate step could ever have produced a verdict.

## Three identities

| identity | value | role |
| --- | --- | --- |
| `trusted_validator` | `github.sha` (default-branch head) | the executing source: workflow, audit, corpus baseline, sandbox, witness, driver, scorer |
| `candidate` | `pull_request.head.sha` | the tree under test, used only as a `git archive` export of the locked commit |
| `comparison_base` | `git merge-base` of the two | inspected Git data; never merged and never built |

Each identity is locked to SHA **and** TREE.

## Trust domain (P1-1): candidate execution has no write authority over trusted state

All candidate code runs through `sandbox.py`, as the dedicated unprivileged account
`c12cand`. That covers the Maven build, classpath resolution, and the JVM that executes
candidate test bytecode. The account:

- must be separate from the invoking user, must not be root, and must not belong to sudo, admin, wheel, docker, adm or lxd;
- gets an `env -i` allowlisted environment. No `GITHUB_ENV`, `GITHUB_PATH`, `GITHUB_OUTPUT`, `ACTIONS_*` or `RUNNER_*` value crosses (CTRL-32);
- runs from a `git archive` export of the locked SHA in its own sandbox directory. HOME and `user.home` are pinned there, so its Maven repository is the sandbox's own;
- reads trusted bytecode (the driver, JUnit and trusted-compiled tests) only from a root-owned, read-only bundle under `/var/lib/c12-trusted`.

`/opt` is not a safe location. The first GitHub-hosted run of the controls showed that
`/opt` is writable by every user on hosted runners, and the writability probe refused the
sandbox. Anything under `/opt` could be renamed and replaced by the candidate, including
the JDK in `/opt/hostedtoolcache` that later trusted steps run. So `prepare` stages a
root-owned, read-only copy of the JDK in `/var/lib/c12-trusted/jdk` before any candidate
code runs, and every later step (trusted `javac` included) uses only that copy. The copy is
probed as well.

Before any candidate code runs, `sandbox.py prepare` runs a probe **as the candidate
account**. The probe shows that none of these paths, nor any of their non-sticky ancestors, is writable:

- the workspace;
- `RUNNER_TEMP`;
- the runner's Maven cache;
- the workflow command-file directory;
- the bundle.

If any one is writable, the sandbox is refused (CTRL-36).

After every candidate execution, every process of the account is killed and the kill is
verified. Candidate output goes to trusted-owned files, not pipes, so a daemon cannot hold
the trusted runner open.

Before scoring, `sandbox.py verify`:

- re-derives every file under `.github/qualification` from the trusted commit's Git blobs (`git hash-object` against `git ls-tree`);
- rejects untracked files there. A planted `json.py` would shadow an import (CTRL-35), and every trusted script also runs with `python3 -I -S -B`;
- re-hashes every sealed evidence file;
- re-probes writability and checks for surviving processes.

The workflow fails unless **both** the integrity check and the verdict pass. They are
separate processes, so replacing the scorer cannot also pass the integrity check (CTRL-33).

**Tool resolution (second review).** The inherited PATH on hosted runners lists
world-writable `/opt` entries, such as the tool cache and `pipx_bin`, ahead of `/usr/bin`. Before
any candidate code runs, `prepare --harden-world-writable` removes `o+w` from every
non-sticky world-writable directory. Every trusted step after `prepare` then:

- runs under an absolute `/usr/bin/bash` shell, never one looked up on PATH;
- exports a root-only PATH: staged JDK, staged Maven, `/usr/sbin:/usr/bin:/sbin:/bin`;
- runs Python as `/usr/bin/python3 -I -S -B`.

The trusted scripts resolve `git`, `sudo`, `find`, `tar` and the JDK tools by absolute path.
`prepare` and `verify` also probe every PATH entry (CTRL-63). The qualify job saves no
Maven cache.

**JUnit configuration (second review).** The driver builds its launcher with every
auto-registration switched off: test engines, post-discovery filters, session, discovery
and execution listeners. It adds only the Jupiter and Vintage engines, and checks that
their code source is the trusted JUnit jar. It disables implicit configuration parameters
(`junit-platform.properties`, system properties) and sets extension autodetection off
explicitly. It credits only identifiers from those two engines. JUnit service files and
`junit-platform.properties` in candidate test resources are not copied into the trusted
output.

Without these measures, a candidate could hide a failing test method behind an
auto-detected extension, shipped in test resources, main resources or a new dependency jar
(CTRL-60, 61, 62). Every count would have stayed green.

The candidate JVM is **not a witness producer**. It contains no signing key, receipt path
or qualification verdict authority. A separate trusted parent JVM opens a one-shot JDI
listener, accepts the exact sandboxed child, closes the listener, and observes the private
`observer*` hook entries plus required trusted-test method entries. For each module the
trusted parent owns a fresh HMAC-SHA256 key in trusted-only storage; that key is passed only
to the observer JVM, never to the candidate JVM. The observer signs its receipt, the trusted
aggregator verifies it and deletes the key, and only then can the receipt contribute credit.
Candidate code can write arbitrary witness-shaped decoys in its own tree; they are never
read (CTRL-38).

The executed test bytecode is never the candidate's build output. `witness.py` compiles each
module's test sources itself, from the `git archive` export, with `javac -proc:none`, so no
annotation processor runs. A build that rewrites `target/test-classes` changes nothing that
executes (CTRL-31). The candidate build runs with `-Dmaven.compiler.proc=none`.

`build_definition_audit.py` is defence in depth. It now fingerprints every build plugin in
every phase, build extensions, profiles, the parent POM, the properties the build
interpolates, and `.mvn/**`. A plugin bound to `initialize` is a `build_definition_changed`
FAIL (CTRL-30). Dependencies, dependency management, repositories, module topology and
other qualification-runtime inputs are authority-bearing as well; changing them in the
candidate is a build-definition violation. The root POM also exposes
`file://${basedir}/repository`, so tracked bytes below each module's `repository/`
tree are dependency authority even when no POM changes. Candidate changes there fail
`local_project_repository_changed` (CTRL-92).

### Export integrity, loaded code and tool resolution (review 2026-10-03)

- **The export equals the locked blobs.** `git archive` applies the tree's own `.gitattributes` (`export-subst`, `export-ignore`, `ident`, `eol`, filters). A candidate could therefore build and test bytes that are not its committed blobs. `sandbox.export_commit` now compares every exported path with `ls-tree`: the same set, the same mode, and the same blob id computed from the raw bytes. Any difference refuses the export (CTRL-67).
- **Nothing world-writable remains on the root filesystem.** `--harden-world-writable` strips o+w from files as well as non-sticky directories (`find -xdev`, so other mounts are not walked). A re-check that finds an entry left, or that did not complete, fails `prepare`. Trusted Python runs as `python3 -I -S -B`, so `site` is not imported and no `.pth` file runs. The runner VM is ephemeral.
- **PATH.** A PATH directory is probed for shadowing: the candidate writing a new entry into it, or replacing it through a writable ancestor. Every tool a trusted step runs (`TRUSTED_TOOLS`) is probed at its real path (CTRL-63). Trusted steps run with `PATH=$C12_TRUSTED_PATH`. Both the gate's `guard-controls` job and the self-test workflow stage root-owned, read-only copies of the JDK and Maven.

## Required corpus (P1-2): the trusted baseline decides what must run

`test_corpus_baseline.json` lists every required `(module, class)` pair and every enabled
test method of those classes (`module::Class#method`). The policy reads it **at the
trusted validator commit** (`corpus_policy.py`, Git data only):

| situation | result |
| --- | --- |
| baseline missing / malformed / stale (≠ trusted enumeration, or a different rule) | UNKNOWN |
| a baseline test is no longer enumerated in the candidate (deleted, renamed out of the regex, moved out of a test root or to another module) with no default-branch approval | FAIL `baseline_test_removed` |
| a baseline test was added on the default branch after the candidate's merge base | FAIL `candidate_behind_default_branch` |
| a baseline method of a retained class is deleted, renamed, loses its test annotation or gains a disabling one (`@Ignore`, `@Disabled*`, `@Enabled*`, on itself or an enclosing type) with no default-branch approval | FAIL `baseline_test_method_removed` |
| a required method (every baseline method still owed) is not reported started by the trusted driver | FAIL `required_test_methods_not_started` |
| the candidate's own baseline file does not describe the candidate | FAIL `candidate_corpus_baseline_not_updated` |
| additions (classes or methods) | delta-visible only: never executed as authority and never credited (CTRL-86) |

### Method identities

A method is a required test when it carries `@Test`, `@ParameterizedTest`, `@RepeatedTest`,
`@TestFactory` or `@TestTemplate`, or when it is a public no-argument `test*` method of a JUnit 3
`TestCase` subclass. Comments and literals are ignored. The v4 identity binds the binary declaring
class (including each nested type) and `methodName(qualifiedErasedParameterTypes)`.
Arrays retain their shape; varargs become arrays. Primitive types and explicitly
qualified reference spellings are supported. Import resolution, type-variable
bounds and nested parameter type resolution are never guessed: unsupported
spellings fail closed. The driver uses the declaring Java method and actual
`Class.getTypeName()` types, with no guessed identity on resolution failure.
JUnit Vintage reports a JUnit 4 test without a `MethodSource` when its name is overloaded
by a method of the same name in the class hierarchy. Mage has two today:
`AlpineHoundmasterTest#attack()` and `BasriKetTest#attack()`, next to the
inherited `attack(int, TestPlayer, String)` helper. For such a test the driver
reads `name(class)` from the vintage unique id. It then resolves the public no-argument
method that carries `org.junit.Test`. If that resolution fails, the method is
simply not observed, so a required method fails closed as not started (CTRL-79/80).
Inherited tests retain declaring-class attribution; parameterized and repeated
invocations share only their own declaration identity. Different qualified
types cannot replace each other, even when only one occurs per revision.
All 6835 enabled native Mage baseline declarations currently have no parameters;
this restriction does not drop existing required tests.

The static reading is not the authority. The trusted driver records every method the launcher
started (`observed_methods`, attributed to the declaring class), and `qualify.py` requires every
required method to appear there. If the static reading is fooled, for example by a candidate
annotation named `Test` (CTRL-59), the method never starts and the verdict is FAIL.

Coverage was measured on Mage master `6a2422d7`. Inside the 1997 baseline classes, every
`@Test`-family annotation outside comments and literals maps to exactly one enumerated
method: 6974 annotated methods plus one JUnit 3 method, 6975 in total. Of these, 6835 are
enabled and 140 are disabled. A method the reading could not see (a custom meta-annotation,
none in Mage today) would be protected only at class level.

The approved path for a removal or rename takes **two reviewed changes**:

1. Land an `approved_removals` entry on the default branch. It needs an entry, a reason and a review reference. The tests still exist, so this change qualifies.
2. Remove the tests, together with their entries and the approval.

An approval that exists only in the candidate's own copy grants that candidate nothing
(CTRL-49).

Regenerate the baseline after adding or removing tests:

```
python3 -I -S -B .github/qualification/corpus_policy.py generate --repo . --rev HEAD \
  --keep-approvals-from .github/qualification/test_corpus_baseline.json \
  --out .github/qualification/test_corpus_baseline.json
```

The current baseline has 1997 classes over 7 modules and 6835 enabled methods. It is identical
to the enumeration of this branch.

## Verdict rule

`PASS` requires all of the following:

- the sandbox is READY;
- the source binding is proven (prepared SHA = locked SHA; locked tree = the tree of that SHA);
- the sandboxed build exits `0`;
- the audit is `CLEAN`;
- the corpus policy is `OK`;
- every required pair is trusted-compiled, authenticated and entered;
- tests were found and started, with zero failed, zero aborted and zero failed containers, and not all skipped;
- the witness is bound to the locked SHA;
- trusted-state integrity is `OK`.

Anything else is `FAIL` or `UNKNOWN`, both non-zero. A proven FAIL is never softened to
UNKNOWN. Mergeability is recorded by a separate job that the verdict never reads.

## Per-module execution

- **Candidate classpath is observation, not authority.** The candidate build still runs one reactor session and records `target/c12-test-classpath.txt` per module, but this map is used only to prove that every required module resolved. It does not decide which dependency bytes the trusted driver executes.
- **Trusted pre-candidate reactor graph.** Before any candidate code runs, the default-branch validator runs its own `test-compile dependency:build-classpath` over the trusted reactor. `TRUSTED_MODULE_CLASSPATHS.json` is sealed before candidate execution and is the runtime graph authority. Trusted reactor `target/classes` entries are mapped to the corresponding candidate main outputs (the code under test); external Maven entries execute only from the candidate-inaccessible trusted Maven cache. Maven dependency order is preserved exactly. An unrelated sibling therefore cannot be injected merely because it has required tests (CTRL-91), and a trusted reactor edge cannot be symlink-redirected to another sibling output with a colliding FQN (CTRL-94).
- **Output containment.** Every mapped reactor output must resolve under the candidate checkout. The tested module's own `target/classes` must resolve to its exact lexical path; a symlink/ancestor escape is refused before execution, so code moved to a candidate-writable path outside the containment prefixes cannot shed the hostile-bytecode policy (CTRL-93).
- **Classpath collection.** `resolve_classpaths.py` refuses a symlink as the classpath record itself. Missing candidate-observation or trusted-authority entries fail closed.
- **Evidence persistence.** The qualification artifact includes both candidate and trusted classpath maps/records plus the before-candidate and after-witness evidence seals.
- **Per-module driver runs.** The driver runs once per module. It enforces that each trusted test class loads from that module's trusted-compiled output, credits `@Nested` classes to the top-level class, and aggregates over `(module, class)` pairs.

## Controls

```
python3 -I -S -B .github/qualification/qualification_selftest.py --offline --sandbox-user <account>   # local
python3 -I -S -B .github/qualification/qualification_selftest.py --sandbox-user c12cand               # CI
```

Every pipeline control runs the production path against a real Git fixture:

1. lock;
2. audit;
3. sandbox prepare with the probe;
4. sandboxed build;
5. classpath collection;
6. witness (corpus policy, trusted compile, sandboxed driver plus trusted parent JDI observer);
7. seals;
8. integrity check;
9. scorer.

The executed scripts are the copies committed in the fixture's trusted commit, so a
candidate able to overwrite them would be overwriting the scorer that actually runs. Red
controls must also show their **intended reason**.

Historical first-epoch `SELFTEST = PASS (56/56 controls ok, 0 not run)` was run locally as a separate
unprivileged account (`nobody`, offline) in about 5 minutes. With the previous driver, CTRL-60 to 62 gave a false PASS: candidate configuration hid a failing test. The PR-time workflow
`candidate-qualification-selftest.yml` runs the same suite on GitHub-hosted runners with the
real `c12cand` account.

| family | controls |
| --- | --- |
| P1-1 trust domain | CTRL-26–29: test code overwrites `qualify.py`, `witness.py`, the source lock and evidence (target unchanged, integrity OK, a genuinely failing candidate stays FAIL); CTRL-30: initialize-phase plugin; CTRL-31: test-bytecode mutation; CTRL-32: environment scrubbed (positive); CTRL-33–35: simulated breaches are caught; CTRL-36: writable trusted path refused; CTRL-38: candidate-side witness decoy ignored; CTRL-84: hostile-bytecode authority containment; CTRL-85/86: candidate test edits/additions earn no authority; CTRL-87/88/89: candidate Jupiter extension, candidate Vintage runner or a swallowing custom runner cannot fabricate green lifecycle credit; CTRL-90: a trusted test using JUnit's own Parameterized runner earns credit; CTRL-92: module-local Maven repository mutation is authority-bearing; CTRL-99: ordinary corpus operations (deep reflection, class loaders, context class loaders, property writes, loopback listen) stay allowed; CTRL-100: a candidate-origin extension registered on a `@Nested` class is refused |
| P1-2 corpus | CTRL-40: honest (positive); CTRL-41: mass rename leaving one; CTRL-42: delete; CTRL-43: move out of test roots; CTRL-44: rename out of regex; CTRL-45: green subset; CTRL-46: legitimate addition (positive); CTRL-47: addition without baseline update; CTRL-48: approved removal path (positive); CTRL-49: removal without default-branch approval; CTRL-50: malformed baseline; CTRL-51: missing baseline; CTRL-52: stale baseline; CTRL-53: candidate behind default branch; CTRL-56: within-class method shrink; CTRL-57: method disabled; CTRL-58: method renamed; CTRL-59: required method never started (static reading fooled); CTRL-64: approved method removal (positive); CTRL-65: method additions (positive) |
| reports, suppression, binding | CTRL-01–09 |
| source lock | CTRL-10–14 |
| static | CTRL-15: workflow contract (Maven only inside the sandbox, `-I -B`, independent integrity enforcement); CTRL-16: no report harvesting; CTRL-17: driver present; CTRL-37: no candidate test bytecode |
| per-module | CTRL-18–25; CTRL-91: unrelated sibling FQN cannot shadow a trusted dependency; CTRL-93: module-output symlink escape is refused; CTRL-94: trusted reactor output cannot be symlink-redirected to a sibling |
| JUnit configuration and PATH (second review) | CTRL-60–62: an auto-detected extension via test resources, main resources or a dependency jar cannot hide a failing test; CTRL-63: a candidate-writable PATH entry refuses the sandbox and fails integrity; CTRL-66: a `.class` test resource cannot replace trusted-compiled bytecode |

**Meta-control.** With a scorer that always returns `PASS`, the suite reports
Historical first-epoch `SELFTEST = FAIL (19/52)` (not a current-suite denominator). CTRL-33–36 stay red even then, because integrity is enforced
independently of the scorer. A missing toolchain or sandbox reports `NOT_RUN`, and the
suite fails.

## Limits, stated

- **Execution JVM versus evidence authority.** Candidate production bytecode still executes inside the sandboxed driver JVM because the trusted tests must exercise the candidate. That JVM has no receipt key/path or evidence-writing authority. The trusted parent observer is a separate process and records the only qualification receipt.
- **Containment is authority-scoped, not a general jail.** The driver is a non-exported, non-open named module: the classpath loader may resolve the class by name, but every member access is refused (`setAccessible` throws `InaccessibleObjectException`), the trusted hook package cannot be defined into, and JNI hook calls are refused because the observer requires the frame below each hook entry to be the trusted driver itself (CTRL-84). `jdk.unsupported` is excluded from the system module graph, so `sun.misc.Unsafe` and `sun.reflect.ReflectionFactory` do not exist; that closes the `MethodHandles.Lookup.IMPL_LOOKUP` route that Unsafe would otherwise provide. The SecurityManager keeps only authority-relevant denials: manager/policy removal, process spawn, non-loopback sockets, multicast, `/proc`/`/sys`/`/dev/fd`, Attach/JVMTI, JMX control, Unix-domain sockets, process handles and VM exit. Ordinary library behaviour (deep reflection, class-loader creation, thread groups, context class loaders, property writes, loopback sockets) is deliberately allowed because the trusted corpus needs it; denying it made the gate unable to run the trusted baseline at all (see "Repair epoch"). Native loading is allowed only by library *name* from `java.library.path`/`sun.boot.library.path`, whose entries are verified root-owned and non-writable as a fail-closed startup precondition, or by absolute path when the resolved target and every ancestor are root-owned, non-writable and non-symlinked; a candidate-initiated absolute load of any candidate-controllable target is refused, including a candidate-created file whose write bit the candidate cleared (CTRL-84).
- **Candidate JUnit execution control is fail-closed.** A green Jupiter/Vintage lifecycle is insufficient when candidate-built code can control invocation. Before discovery the trusted driver inspects selected trusted test classes and refuses candidate-origin runners/extensions/providers or registered Rule/Extension members, and refuses every `@RunWith` runner outside JUnit's own runner types. Thus a candidate `InvocationInterceptor`, a custom Vintage runner, or a swallowing runner cannot suppress a trusted failing assertion and manufacture PASS (CTRL-87/88/89).
- **Body proof is entry plus trusted success, not a JVMTI method exit.** The parent observer sets a breakpoint on the entry of every required method and credits completion only when the trusted driver reports the active test FINISHED/SUCCESSFUL; an exceptional exit never reports SUCCESSFUL. JVMTI method entry/exit requests were the original real-corpus hang: HotSpot disables JIT compilation globally while one is enabled (measured ~20–30x on unrelated code), and the 2026-10-06 gate timed out after 18000s with only 17 of 1975 class pairs entered. Breakpoints deoptimize only the exact method and are the only JDI mechanism used for execution observation.
- **Authoritative test source is trusted.** Executed test bytecode is compiled from the trusted-validator commit, not the candidate's edited test source. Candidate production code remains the subject under test. Unsupported dynamic/template constructs that cannot be bound to a parent-observed required-method entry plus a trusted successful finish fail closed rather than receiving credit.
- **The class regex is narrower than surefire's defaults.** Surefire also runs `Test*` classes, for example `TestPartnerCommanders`. The C12 class regex (`(Test|Tests|TestCase|Spec|IT)$`) does not select those, so 16 Mage test files that contain `@Test` methods are not required. Widening the regex is a separate decision: it would also select helper classes named `Test*`, which can never be entered.
- **Which classes run.** Every required class must still compile from its own module (`required_tests_not_compiled`). The driver runs the selected classes (`selected_test_classes`), and each must be entered:
  - the required classes that own at least one required test method;
  - the concrete required classes that only inherit enabled tests (`required_inheriting_classes`). Examples are Mage's `SmoothedLondonMulliganTest`, which overrides a hook and inherits `LondonMulliganTest`'s seven tests. Inheritance is read from the source: the declared superclass is resolved by package, single-type imports and on-demand imports among all test sources, and the chain must reach a class that declares an enabled test. A trusted inheriting class stays owed while it exists, so making it abstract in the candidate fails (`required_tests_never_entered`).
  - `qualify.py` re-derives the selection from the policy and fails `selected_set_not_policy_derived` on any difference.
  - A corpus class with neither stays protected by the class-level policy and must still compile, but it is not run. It is listed in `corpus_classes_without_required_methods`. Examples are an abstract base, a class-level `@Ignore`, or a helper without `@Test`.
  - **Limit:** an inherited test is not required by name; it is credited through its class being entered and every failure counting. A superclass outside the test source roots, or named as a nested type, is not resolved, so a class inheriting only from such a superclass is not run.
- **Method identity binds declaring class and qualified erased parameter signature (v4).** Nested and overloaded test removal controls CTRL-71–78 protect separate declarations. Ambiguous normalized signatures cannot earn PASS. A required `@ParameterizedTest`, `@RepeatedTest` or `@TestFactory` counts as started when its container starts, even if every invocation is skipped. Static enumeration misses composed or meta `@Test` annotations, `@Theory`, and JUnit 3 `final` methods. Such methods are not required by name: they still run when their class runs, but a regression in a method whose class is never run is not seen.
- **Network egress.** Candidate build code still has the runner's network access. The job is read-only, persists no credentials and references no secret.
- **Main-class bytecode** comes from the candidate's Maven build under an audited build definition, with annotation processing disabled. Which reactor outputs may participate is fixed by the trusted pre-candidate dependency graph, and their canonical paths must remain inside the candidate checkout; candidate classpath text itself grants no runtime authority.
- **The inherited `Mage.Verify` red** (`VerifyCardDataTest`, external card-data drift) fails every candidate's positive control. It is deliberately not excluded. Which signals belong in the campaign is C13's decision (#494), and the drift is C14's (#495).
- **Runtime.** `pull_request_target` runs the default-branch copy, so the gate cannot prove itself live on the PR that introduces it. `C12_RUNTIME` stays `UNKNOWN` until the post-merge live controls run. The workflow is **not** a required status check.

`PRODUCTION_PROVIDER = NOT_SELECTED` · `ARCHITECTURE_FREEZE = NOT_CLAIMED`

## Method identity migration (2026-10-04)

Baseline/policy v4 and aggregate witness/evidence v7 replace the lossy method-name and same-JVM evidence-authority contracts. The parent-observed execution witness moved to /6 in the 2026-10-06 repair (breakpoint observation; body completion is entry plus trusted FINISHED/SUCCESSFUL, and `method_body_completions_by_test` replaces the exit map). Historical execution-witness epochs receive no credit under this validator. Exact-head controls must pass before integration, and a fresh default-branch `pull_request_target` run must qualify a real successor PR before C12 runtime is claimed.

## Repair epoch (2026-10-06)

The 2026-10-06 merge of PR #43 was reverted through PR #51 after the real-corpus witness did not terminate. The reverted implementation is restored here deliberately as the repair base, with these evidence-backed changes:

- **Root cause of the hang, measured.** Run `37425332885` job `112154726073` shows the witness step at 5h09m and `Mage.Tests: contained_execution_failure: candidate execution timed out after 18000s`, with only 17 of 1975 module/class pairs entered (the six small modules; Mage.Tests entered none). The pre-#43 driver ran the same corpus in ~5 minutes (run `37398807739` job `112065715326`). A micro-reproduction (`enabling one MethodEntryRequest` filtered on an unrelated class) slows unrelated code from 0.15s/round to 5.1s/round; a matching filter with SUSPEND_ALL takes >40s/round. HotSpot disables JIT globally while any method entry/exit request is enabled. The observer now uses breakpoints only.
- **The containment policy prevented honest execution.** With the pre-repair containment, every Mage.Tests container failed with `ExceptionInInitializerError` (JAXB `setAccessible` denied under a candidate frame), and the denied list also included class-loader creation, thread-group modification, native loading and H2 `AUTO_SERVER` loopback sockets. That is why no Mage.Tests class was ever entered. Containment is now authority-scoped (see Limits) and the corpus subset runs 153/153 with full body completion locally.
- **Module resolution.** The named-module driver launch resolved only `java.logging`; `java.sql` was absent and the corpus failed with `NoClassDefFoundError: java/sql/SQLException`. The launch now resolves every system module except `jdk.unsupported`.
- **Diagnosability.** A sandboxed candidate timeout now preserves the bounded stdout/stderr produced before the kill instead of discarding it.

The regenerated baseline still protects all 1997 classes and 6835 enabled methods
(140 disabled); no removal approvals, test bodies, engine code or denominator were
changed. The current qualification engine pin is unaffected. Exact-head hosted
controls and a post-merge live qualification remain mandatory before runtime PASS.

Historical diagnostic evidence remains under `research/c12-log-safety-20261004/`.
Candidate diagnostic text is ASCII JSON-escaped and raw JSON artifacts retain the original
values; that historical evidence is bounded to its own source epoch.
