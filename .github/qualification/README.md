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
- rejects untracked files there. A planted `json.py` would shadow an import (CTRL-35), and every trusted script also runs with `python3 -I -B`;
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
- runs Python as `/usr/bin/python3 -I -B`.

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

The driver authenticates its witness with HMAC-SHA256. The key is delivered on stdin from
an unlinked trusted file. The driver reads it and closes stdin before any candidate class
loads, and keeps it only in a local of `main()`. Candidate test code can write into the
driver's (candidate-writable) output directory, but a forged witness carries no valid MAC
(CTRL-38).

The executed test bytecode is never the candidate's build output. `witness.py` compiles each
module's test sources itself, from the `git archive` export, with `javac -proc:none`, so no
annotation processor runs. A build that rewrites `target/test-classes` changes nothing that
executes (CTRL-31). The candidate build runs with `-Dmaven.compiler.proc=none`.

`build_definition_audit.py` is defence in depth. It now fingerprints every build plugin in
every phase, build extensions, profiles, the parent POM, the properties the build
interpolates, and `.mvn/**`. A plugin bound to `initialize` is a `build_definition_changed`
FAIL (CTRL-30). Dependency declarations remain free.

## Required corpus (P1-2): the trusted baseline decides what must run

`test_corpus_baseline.json` lists every required `(module, class)` pair. The policy reads
it **at the trusted validator commit** (`corpus_policy.py`, Git data only):

| situation | result |
| --- | --- |
| baseline missing / malformed / stale (≠ trusted enumeration, or a different rule) | UNKNOWN |
| a baseline test is no longer enumerated in the candidate (deleted, renamed out of the regex, moved out of a test root or to another module) with no default-branch approval | FAIL `baseline_test_removed` |
| a baseline test was added on the default branch after the candidate's merge base | FAIL `candidate_behind_default_branch` |
| the candidate's own baseline file does not describe the candidate | FAIL `candidate_corpus_baseline_not_updated` |
| additions | required as well, and must run |

The approved path for a removal or rename takes **two reviewed changes**:

1. Land an `approved_removals` entry on the default branch. It needs an entry, a reason and a review reference. The tests still exist, so this change qualifies.
2. Remove the tests, together with their entries and the approval.

An approval that exists only in the candidate's own copy grants that candidate nothing
(CTRL-49).

Regenerate the baseline after adding or removing tests:

```
python3 -I -B .github/qualification/corpus_policy.py generate --repo . --rev HEAD \
  --keep-approvals-from .github/qualification/test_corpus_baseline.json \
  --out .github/qualification/test_corpus_baseline.json
```

The current baseline has 1996 entries over 7 modules, and is identical to the
default-branch enumeration.

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

- **Single reactor session.** The candidate build is one reactor session: `mvn test-compile dependency:build-classpath -Dmdep.outputFile=target/c12-test-classpath.txt`. Sibling modules therefore resolve to the candidate's own reactor output, not to an installed and possibly stale `org/mage` jar. Any remaining `org/mage` repository entry is still dropped.
- **Classpath collection.** `resolve_classpaths.py` reads each module's file back, refusing symlinks. The module list comes from the trusted Git enumeration. A missing module fails closed.
- **Per-module driver runs.** The driver runs once per module. It enforces that each class loads from that module's trusted-compiled output, credits `@Nested` classes to the top-level class, and aggregates over `(module, class)` pairs.

## Controls

```
python3 -I -B .github/qualification/qualification_selftest.py --offline --sandbox-user <account>   # local
python3 -I -B .github/qualification/qualification_selftest.py --sandbox-user c12cand               # CI
```

Every pipeline control runs the production path against a real Git fixture:

1. lock;
2. audit;
3. sandbox prepare with the probe;
4. sandboxed build;
5. classpath collection;
6. witness (corpus policy, trusted compile, sandboxed and authenticated driver);
7. seals;
8. integrity check;
9. scorer.

The executed scripts are the copies committed in the fixture's trusted commit, so a
candidate able to overwrite them would be overwriting the scorer that actually runs. Red
controls must also show their **intended reason**.

`SELFTEST = PASS (56/56 controls ok, 0 not run)`. This was run locally as a separate
unprivileged account (`nobody`, offline) in about 5 minutes. With the previous driver, CTRL-60 to 62 gave a false PASS: candidate configuration hid a failing test. The PR-time workflow
`candidate-qualification-selftest.yml` runs the same suite on GitHub-hosted runners with the
real `c12cand` account.

| family | controls |
| --- | --- |
| P1-1 trust domain | CTRL-26–29: test code overwrites `qualify.py`, `witness.py`, the source lock and evidence (target unchanged, integrity OK, a genuinely failing candidate stays FAIL); CTRL-30: initialize-phase plugin; CTRL-31: test-bytecode mutation; CTRL-32: environment scrubbed (positive); CTRL-33–35: simulated breaches are caught (replaced scorer, rewritten sealed evidence, planted module); CTRL-36: writable trusted path refused; CTRL-38: forged witness rejected |
| P1-2 corpus | CTRL-40: honest (positive); CTRL-41: mass rename leaving one; CTRL-42: delete; CTRL-43: move out of test roots; CTRL-44: rename out of regex; CTRL-45: green subset; CTRL-46: legitimate addition (positive); CTRL-47: addition without baseline update; CTRL-48: approved removal path (positive); CTRL-49: removal without default-branch approval; CTRL-50: malformed baseline; CTRL-51: missing baseline; CTRL-52: stale baseline; CTRL-53: candidate behind default branch |
| reports, suppression, binding | CTRL-01–09 |
| source lock | CTRL-10–14 |
| static | CTRL-15: workflow contract (Maven only inside the sandbox, `-I -B`, independent integrity enforcement); CTRL-16: no report harvesting; CTRL-17: driver present; CTRL-37: no candidate test bytecode |
| per-module | CTRL-18–25 |
| JUnit configuration and PATH (second review) | CTRL-60–62: an auto-detected extension via test resources, main resources or a dependency jar cannot hide a failing test; CTRL-63: a candidate-writable PATH entry refuses the sandbox and fails integrity |

**Meta-control.** With a scorer that always returns `PASS`, the suite reports
`SELFTEST = FAIL (19/52)`. CTRL-33–36 stay red even then, because integrity is enforced
independently of the scorer. A missing toolchain or sandbox reports `NOT_RUN`, and the
suite fails.

## Limits, stated

- **The same JVM is shared.** Candidate test code, and the main or dependency code it reaches, runs in the driver's JVM. Such code can read that process's memory, including the MAC key, so the MAC defeats forgery from outside the run, not deliberate in-process tampering. That code can also tamper with JVM state at runtime. Attach is disabled (`-XX:+DisableAttachMechanism`) and the key is zeroed after use, but nothing in the same process can rule this out. What C12 does guarantee: the candidate cannot write trusted state, cannot change which test bytecode runs, cannot reconfigure the launcher declaratively, and cannot shrink the corpus. Any in-process tampering must therefore come from reviewable candidate source.
- **Test code is candidate code.** It runs as the sandbox account. A test whose own source is weak (an empty body, a swallowed assertion, a method-level shrink inside a kept class) is a source-review and coverage question for C13/C16. The corpus baseline is class-level.
- **Network egress.** Candidate build code still has the runner's network access. The job is read-only, persists no credentials and references no secret.
- **Main-class bytecode** comes from the candidate's Maven build under an audited build definition, with annotation processing disabled.
- **The inherited `Mage.Verify` red** (`VerifyCardDataTest`, external card-data drift) fails every candidate's positive control. It is deliberately not excluded. Which signals belong in the campaign is C13's decision (#494), and the drift is C14's (#495).
- **Runtime.** `pull_request_target` runs the default-branch copy, so the gate cannot prove itself live on the PR that introduces it. `C12_RUNTIME` stays `UNKNOWN` until the post-merge live controls run. The workflow is **not** a required status check.

`PRODUCTION_PROVIDER = NOT_SELECTED` · `ARCHITECTURE_FREEZE = NOT_CLAIMED`
