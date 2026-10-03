# Trusted candidate qualification (C12)

Qualifies an exact Mage candidate SHA using workflow code the candidate cannot change.

## Why this exists

`.github/workflows/maven.yml` runs on `pull_request`, so its own definition is part of
the candidate. A candidate that edits `maven.yml` edits the thing that judges it. That
is true even for a perfectly honest-looking workflow file.

`candidate-qualification.yml` is triggered by `pull_request_target`, so GitHub executes
the copy on the default branch. The candidate supplies data, never the rules.

## Three identities

| identity | value | role |
| --- | --- | --- |
| `trusted_validator` | `github.sha` (default-branch head) | the executing source: guard, workflow, log4j config |
| `candidate` | `github.event.pull_request.head.sha` | the tree under test; checked out to a separate path |
| `comparison_base` | `git merge-base` of the two | inspected Git data only; never merged, never built |

They are written to `SOURCE_LOCK.json` with both SHA and TREE, and the verdict is bound
to them. `CTRL-16` asserts the trusted workflow never passes the test-only
`--candidate-ref` override, so production always fetches the PR head ref.

## A green Maven exit code is not qualification credit

This is the hole that survives a trusted workflow. Maven is a candidate-controlled build
tool, so a candidate POM can suppress its own tests and still exit 0. Verified locally
against mage's own surefire configuration (`3.1.2`, `useFile=false`):

- `<skipTests>true</skipTests>` and `<maven.test.skip>` as **properties** are defeated by
  the trusted `-DskipTests=false -Dmaven.test.skip=false` overrides — the tests really run
  (`CTRL-03`).
- the same flags hardcoded in **`<configuration>`** survive those overrides. Maven prints
  `BUILD SUCCESS`, executes nothing, and writes no surefire report (`CTRL-02`).

So the guard scores harvested surefire XML, not the process exit status. `PASS` requires
positive proof that tests were discovered and executed. Absent, empty, malformed or
ambiguous evidence is `FAIL` or `UNKNOWN`, never `PASS`.

## Verdict rules

`PASS` requires: source binding proven, at least one parseable surefire report, executed
tests greater than zero, zero failures, zero errors, and not every test skipped.
`UNKNOWN` is returned when the source lock itself cannot be trusted. Both `FAIL` and
`UNKNOWN` exit non-zero.

Mergeability is recorded by a separate job and is never read by the verdict. A synthetic
merge result is Git data about the pull request, not qualification evidence.

## Controls

`qualification_selftest.py` runs first in the workflow. If it fails, no candidate result
is read. It asserts each control's *actual* verdict, so it is a real discriminator: swap
in a guard that always returns `PASS` and eight controls go red.

```
python3 .github/qualification/qualification_selftest.py --offline
python3 .github/qualification/qualification_selftest.py            # online, as in CI
```

Controls that need a real Maven or Git run report `NOT_RUN`, never `PASS`, when the
toolchain is unavailable — a missing toolchain must not silently weaken the gate.

| control | kind | asserts |
| --- | --- | --- |
| CTRL-01 | positive | an honest candidate that runs its tests earns credit |
| CTRL-02 | red | hardcoded surefire skip/excludes: `BUILD SUCCESS`, verdict `FAIL` |
| CTRL-03 | red (defeated) | property-level suppression loses to the trusted overrides |
| CTRL-04 | red | a candidate-forged `PASS` evidence file is never consumed |
| CTRL-05 | red | a candidate copy of the guard is recorded but inert |
| CTRL-06 | red | green reports for an unlocked tree are a `FAIL` |
| CTRL-07 | red | malformed report XML never becomes `PASS` |
| CTRL-08 | red | a genuinely failing test is a `FAIL` |
| CTRL-09 | red | all-`@Disabled` tests are a `FAIL` |
| CTRL-10 | red | `NOT_RUN` (no build output) is never `PASS` |
| CTRL-11 | positive | a correct trusted/candidate pair locks with SHA, TREE and merge base |
| CTRL-12 | red | a trusted SHA that is not the executing checkout cannot lock |
| CTRL-13 | red | a base ref other than the default branch cannot lock |
| CTRL-14 | red | a candidate SHA the fetched ref does not resolve to cannot lock |
| CTRL-15 | red | a non-SHA candidate identity cannot lock |
| CTRL-16 | red | the trusted workflow keeps its no-credential, unmasked, PR-head-ref contract |

## Residual risk

Qualification executes candidate build code, which is inherent: the candidate is a Java
project and its tests must run. The workflow therefore runs read-only with
`permissions: contents: read`, `persist-credentials: false` on both checkouts, and no
secret references, so the job token is not reachable from the candidate build. A
candidate build still has network egress on the runner. Removing that requires a
sandboxed build executor and is out of scope here.

## Status

This workflow is **not** a required status check and does not claim to be one. It is
advisory until a separate governance decision makes it required.

`PRODUCTION_PROVIDER = NOT_SELECTED` · `ARCHITECTURE_FREEZE = NOT_CLAIMED`