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

## Controls

```
python3 .github/qualification/qualification_selftest.py --offline   # local
python3 .github/qualification/qualification_selftest.py             # as CI runs it
```

`SELFTEST = PASS (17/17 controls ok, 0 not run)`. Controls run before any candidate
result is read; if the selftest fails, no candidate verdict is produced.

| control | kind | asserts |
| --- | --- | --- |
| CTRL-01 | positive | honest candidate, tests actually run by the trusted launcher → PASS |
| CTRL-02 | red | lifecycle hook fabricates green `TEST-*.xml` while executing nothing → FAIL |
| CTRL-03 | red | real failing test **plus** forged green XML → FAIL on both counts |
| CTRL-04 | red | fabricated/copied report, required test never compiled → UNKNOWN |
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