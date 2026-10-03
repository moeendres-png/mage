# Trusted candidate qualification (C12)

Qualifies an exact Mage candidate SHA using rules the candidate cannot change, and
cannot be moved to another candidate-writable directory to make that true.

## Why this exists

`.github/workflows/maven.yml` runs on `pull_request`, so its own definition belongs to
the candidate: editing it edits the thing that judges it.

That was only the first hole. The reviewed implementation also harvested
`candidate/**/target/surefire-reports/TEST-*.xml` from trusted Python, and that proved
nothing — a candidate POM, Maven plugin, lifecycle hook, test or generated file can
create those files. It was demonstrated, not theorised: a candidate POM that hardcoded
surefire `skipTests` + `excludes` and copied a committed `TEST-*.xml` into the report
directory got `BUILD SUCCESS` from Maven and **`PASS` with `tests=500`** from the old
scorer, having executed nothing.

**Candidate-produced reports are no longer read anywhere.** Not relocated, not
re-hashed, not sanity-checked: absent. `CTRL-16` enforces this structurally by walking
`qualify.py`'s AST and failing if it contains any directory traversal or any candidate
build-output path, and by failing if `witness.py` so much as names a surefire report
path.

## Three identities

| identity | value | role |
| --- | --- | --- |
| `trusted_validator` | `github.sha` (default-branch head) | executing source: workflow, audit, witness, driver, scorer |
| `candidate` | `pull_request.head.sha` | the tree under test, in a separate checkout path |
| `comparison_base` | `git merge-base` of the two | inspected Git data; never merged, never built |

Each is locked to SHA **and** TREE. `CTRL-15` asserts the trusted workflow never passes
the test-only `--candidate-ref` override, so production always fetches the PR head ref.

## The three trusted-side controls

None of them consumes a candidate-authored artifact.

**1. Build-definition audit** (`build_definition_audit.py`). Before anything runs, the
test-execution fingerprint of every changed POM is compared against the comparison base
through Git. Editing your own `skipTests`, surefire/failsafe configuration, test source
or target directories, adding a build extension, or binding a plugin into a post-test
lifecycle phase fails the gate. Scope is deliberately narrow — dependency versions and
ordinary source edits are untouched — so this is not a change freeze.

**2. Maven/build-result binding.** A non-zero candidate build exit is an **unconditional
FAIL**. This was the second hole: scoring ran under `if: always()` with no build-exit
predicate, so a failed build plus forged green XML could reach PASS. It cannot now.

**3. Trusted execution witness** (`witness.py` + `TrustedTestDriver.java`). The trusted
side enumerates required test classes from the candidate's **source** tree, then its own
JUnit Platform driver selects exactly those classes and records the counts **the driver
observed**. A required class the launcher never entered is a FAIL, so a candidate cannot
fabricate green evidence for tests it did not run.

## Verdict rule

`PASS` requires all of: source binding proven; build exit `0`; audit `CLEAN`; trusted
enumeration non-empty; every required class entered; tests found and started; zero
failed, zero aborted, zero failed containers, not all skipped; witness bound to the locked
candidate SHA. Anything missing, unusable or ambiguous is `FAIL` or `UNKNOWN`, both
non-zero. Mergeability is recorded by a separate job the verdict never reads.

## Per-module classpath and execution

Surefire runs each module with its own test classpath in its own forked JVM. The witness
reproduces that rather than approximating it with one combined classpath:

1. `witness.py` enumerates required test classes **per module** from candidate source, so
   the module that owns a class is known before anything runs.
2. The workflow resolves a test classpath **per module** via `dependency:build-classpath`.
3. Any `org/mage/...` repository entry is **dropped** and replaced by the candidate's own
   reactor output directories. This is not cosmetic: resolving outside a full reactor
   points a sibling module at an installed jar, and the workflow restores `~/.m2` between
   runs via `cache: maven`, so such a jar can be silently stale — the witness would then
   run the candidate's tests against a framework that is not the candidate's.
4. `TrustedTestDriver` runs **once per module**, with that module's classes only, and
   verifies via the code source that each executed class really loaded from its own
   module's output.
5. Aggregation happens only in `witness.py`, counting `(module, class)` **pairs** — bare
   class names would collapse two modules that legitimately share a test class FQN.

Every step fails closed. A required module with no resolved classpath, a required class
that is not compiled, a required class the launcher never entered, a module that produced
no witness, or a class loaded from the wrong module all produce `FAIL`/`UNKNOWN`. No module
is ever dropped because resolving it was inconvenient.

The classpath map is candidate-influenced **input** — unavoidable, since executing a
candidate's tests requires its declared dependencies. It is never authority: it can change
which class loads, never whether a required class counts as executed, never the verdict.

## Controls

```
python3 .github/qualification/qualification_selftest.py --offline   # local
python3 .github/qualification/qualification_selftest.py             # as CI runs it
```

`SELFTEST = PASS (25/25 controls ok, 0 not run)`. Controls run before any candidate
result is read; if the selftest fails, no candidate verdict is produced.

| control | kind | asserts |
| --- | --- | --- |
| CTRL-01 | positive | honest candidate, tests actually run by the trusted launcher → PASS |
| CTRL-02 | red | lifecycle hook fabricates green `TEST-*.xml` while executing nothing → FAIL |
| CTRL-03 | red | real failing test **plus** forged green XML → FAIL on both counts |
| CTRL-04 | red | fabricated/copied report, required test never compiled → FAIL |
| CTRL-05 | red | hardcoded surefire suppression: `BUILD SUCCESS`, verdict FAIL |
| CTRL-06 | red | every test `@Disabled` → FAIL |
| CTRL-07 | red | no required test class → UNKNOWN |
| CTRL-08 | red | malformed witness → UNKNOWN |
| CTRL-09 | red | evidence for a tree that is not the locked candidate → UNKNOWN |
| CTRL-10 | positive | correct trusted/candidate pair locks with SHA, TREE, merge base |
| CTRL-11–14 | red | wrong trusted SHA / non-default base / substituted candidate / non-SHA |
| CTRL-15 | red | workflow keeps its no-credential, unmasked, PR-head-ref contract |
| CTRL-16 | red | `qualify.py` traverses nothing; `witness.py` names no report path |
| CTRL-17 | positive | the trusted driver exists as trusted source |
| CTRL-18 | positive | two modules with different test classpaths both execute and aggregate |
| CTRL-19 | positive | a dependency reachable only on its own module classpath is entered |
| CTRL-20 | red | a required module with no resolved classpath → UNKNOWN, never a skip |
| CTRL-21 | red | a required class that cannot resolve on its module classpath → FAIL |
| CTRL-22 | red | one genuinely failing module is not masked by passing siblings |
| CTRL-23 | red | partial module execution cannot aggregate into PASS |
| CTRL-24 | red | a required class owned by a sibling module cannot be credited |
| CTRL-25 | red | a module with zero required classes contributes nothing |

CTRL-19 uses a real installed Maven artifact that only one module may depend on, so
per-module resolution is exercised rather than asserted. CTRL-22 asserts on
`test_failures` specifically: it previously passed for the wrong reason (the failing module
had not compiled), which would have hidden a masking bug.

Every control asserts the verdict actually observed, so the suite is a discriminator
rather than a decoration. Meta control: replacing the scorer with one that returns `PASS`
unconditionally turns 8 controls red and the suite to `SELFTEST = FAIL (9/17)`.

Controls needing Maven/JDK/JUnit report `NOT_RUN`, never `PASS`, when the toolchain is
absent — a missing toolchain must not weaken the gate.

## Trust boundary and its limits

The honest limit, because it is not solvable inside C12: candidate test **bytecode**
executes inside the trusted driver's JVM, as the same OS user. A candidate whose test
code deliberately drives the trusted listener through reflection is beyond what any
same-JVM qualification can exclude. That is a semantic-coverage question — it belongs to
C13 (#494) and C16 (#497), not to C12's provenance boundary. C12's guarantee is precise
and narrower: **no candidate-authored artifact, POM, plugin, lifecycle hook or generated
file can produce qualification credit.**

Two consequences worth being explicit about:

- The candidate build runs `test-compile` only. Its own test execution is redundant work,
  so the workflow does not pay for it twice.
- CPU/wall accounting was evaluated as a suppression detector and **rejected on
  evidence**: an honest 2-test campaign measured 6.9–7.2 s CPU against 5.6–6.0 s for a
  fully suppressed one, because Maven's own startup dominates. A magnitude threshold
  would have been a heuristic that separates nothing.

## Known production-path gaps (not closed here)

The controls prove the *trust property* on a real Maven/JDK/JUnit toolchain, and the
witness has been run against the **real Mage reactor**, not only synthetic fixtures. What
remains unproven is stated rather than papered over.

**Real-scale validation performed.** Against Mage master at `7edc440c83`, with real
`dependency:build-classpath` resolution for all 7 modules that own required tests
(`Mage`, `Mage.Client`, `Mage.Common`, `Mage.Server`, `Mage.Server.Console`, `Mage.Tests`,
`Mage.Verify`; 1996 required classes):

- 102 stale installed sibling jars detected and dropped across the module classpaths;
- the two modules compiled locally (`Mage`, `Mage.Common`) executed **115 real tests,
  115 succeeded, 0 failed** through the per-module trusted driver;
- `code_origin_violations: []` — origin enforcement held on real Mage classes;
- the 5 uncompiled modules were reported as `modules_without_witness`, and the scorer
  returned `FAIL` naming all of them plus `partial_module_execution: 10 of 1996 required
  module/class pairs entered`. No silent skip, no fabricated PASS.

**Remaining gap: full-reactor execution of `Mage.Tests` (1976 classes).** Building the
whole reactor locally was out of budget for this run, so the large module has not been
executed end to end. The mechanism is proven on real Mage code in two modules and the
fail-closed behaviour is proven on the uncompiled remainder; what is unproven is the
behaviour with all 1996 classes actually running. That is a runtime-scale question, not a
trust question, and it resolves on the first live run.

**Inherited `Mage.Verify` red blocks the positive live control.** On plain master
(`103a1e0001`, run `37101432319`) `maven.yml` fails with `Mage Verify ... FAILURE` while
`Mage Tests ... SUCCESS [02:35 min]`. That red predates C12 — it also fails at `6e3db5046`
and on the #38 merge. Because the trusted enumeration includes
`mage.verify.VerifyCardDataTest`, the C12 gate will fail that class for **every**
candidate, including a docs-only one.

It is deliberately **not** excluded. Narrowing the required set to make a control pass
would be exactly the silent coverage weakening this workstream exists to prevent. Which
signals belong in the qualification campaign is C13's decision (#494); the drift root cause
is C14's (#495).

## Runtime bootstrap

`pull_request_target` executes the default-branch copy, so this workflow cannot prove
itself live on the PR that introduces it. `C12_RUNTIME` stays `UNKNOWN` until it is on
`master` and the live controls have run.

Ordinary Mage CI is currently red in `Mage.Verify` from external card/set reference
drift. That is #495's surface and is **not** repaired here. It does mean a "docs-only →
PASS" live control cannot be assumed: the positive control must be designed to isolate
the C12 signal from the inherited `Mage.Verify` red, or it must wait for #495. See
"Remaining blockers" in the #493 handoff.

This workflow is **not** a required status check and does not claim to be one.

`PRODUCTION_PROVIDER = NOT_SELECTED` · `ARCHITECTURE_FREEZE = NOT_CLAIMED`