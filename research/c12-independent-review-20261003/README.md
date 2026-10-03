# C12 independent requalification, 2026-10-03

Source before review: Mage PR39 `2afe121f58c043cc8104e0b9ed6a5b285e81d29a`, tree `f14db82fe9073b2782d8d0fd53732c8a5e373fbe`.
Current master `6a2422d77ac9ab598703fe26fc9af963baba3388` was merged normally; the required class baseline now includes the new PriorityEliminationTest (1997 entries).

## Confirmed findings

- **Blocking corpus defect, unresolved:** a trusted fixture has ten JUnit methods in ProbeTest. The candidate leaves one in the same class and updates its identical class-only baseline. The full production pipeline grants PASS and qualification_credit=true, with integrity OK and actual one-test execution. Class preservation does not preserve the required method corpus. This is an independently executed synthetic fixture, not Mage card-behavior evidence.
- **Counter parser defect, repaired:** a controlled trusted-producer fault emits authenticated tests_failed=-1 after honest passing JUnit execution. The old full pipeline grants PASS. The repaired scorer grants FAIL invalid_execution_counter with qualification_credit=false and integrity OK. Authentication alone does not validate producer counts; this control is not an authentication bypass.

The repaired scorer rejects absent, boolean, non-integer and negative counters, mismatched duplicate totals, inconsistent started/outcome totals and outcomes exceeding discovery. An unchanged positive witness passes; 42 scalar-shape controls and three consistency controls reject malformed data. CTRL54 adds the authenticated producer-fault control to the full gate selftest.

## Durable evidence / reproduction

Each case directory contains the exact small synthetic Git fixture as fixture.bundle, plus lossless source lock, witness, integrity and verdict records. SOURCE_EVIDENCE.json binds compressed/raw bytes, source parent, master integration and qualification patch. To inspect a fixture independently: `git clone CASE/fixture.bundle NEW_DIRECTORY`, then inspect its exact SOURCE_LOCK revisions with Git. No private local object store is required.

Run `python3 reproduce.py --repo QUALIFICATION_SOURCE_CHECKOUT --work-root NEW_ROOT_OWNED_DIRECTORY --sandbox-root NEW_SRV_DIRECTORY --seed-maven-repo CACHED_M2 --junit-classpath PINNED_JUNIT_1_9_3_JAR --sandbox-user EXISTING_UNPRIVILEGED_USER --out REPORT.json` as root. The existing Harness executes candidate Maven/Java only under the separate account. For before-state use exact2afe source; for after-state use this branch. The unchanged-ten-methods control must PASS. Negative-counter must FAIL after repair. Ten-methods-to-one still incorrectly PASS and is the executable next blocker; do not interpret that as successful qualification.

Counter contracts: `python3 -m unittest discover -s .github/qualification -p test_counter_contract.py -v`. Full hosted selftest and independent review of the new head remain required. Earlier52-control hosted PASS is historical and does not cover this added control or the unresolved method-removal route.

## Status / exact next action

C12_IMPLEMENTATION = PARTIAL; C12_CORPUS = FAIL; C12_RUNTIME = UNKNOWN; C12_OVERALL = PARTIAL.
Do not merge PR39. First extend trusted corpus preservation below class granularity using actual test identities, with full-path controls for method removal, annotation removal, rename, additions and an independently trusted approved-removal path. Preserve existing baseline/ownership boundaries; avoid a regex-based Java parser or candidate-controlled minimum. Test body weakening remains a source-review concern and cannot be proven absent by counts.

The first local launcher failed only while reading the external source-tree Git identity under root ownership protection, after the pipeline had completed. Its verdict was recovered from the retained records; no second execution was credited. Local launcher copies are superseded by the portable reproducer and are non-authoritative. No failure evidence was promoted to Rules or provider qualification.

## Raw-module counter follow-up

The first aggregate guard was insufficient: authenticated module tests_failed=-1.0 was converted to zero by aggregation and still earned PASS. Each raw module counter is now validated before aggregation; sums must match aggregate counters. The full pipeline now rejects that producer fault, preserving integrity OK and denying qualification credit. CTRL55 exercises this path. Four counter contract tests (including35 module-shape controls) and16/16 affected full-path corpus controls pass. The exact synthetic fixtures and raw records are in module-counter-followup/SOURCE_EVIDENCE.json. The earlier15-control report is superseded for this added guard; current54-control hosted selftest remains pending. Within-class method shrink remains a blocking FAIL.
