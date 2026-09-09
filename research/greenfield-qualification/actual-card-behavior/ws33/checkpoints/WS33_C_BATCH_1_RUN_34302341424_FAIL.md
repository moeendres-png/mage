# WS33-C Batch 1 R6 run 34302341424 terminal PARTIAL/FAIL (adjudicated)

RUN = 34302341424
JOB = 102311731216 (c-abilitysub-pilot, completed/success job? workflow SUCCESS)
RUN_CONCLUSION = success (workflow), GATE = PARTIAL (0/7 evidenced)
SOURCE_HEAD = c5138033796dcb42f86b514a97bca878a09f66ed
SOURCE_TREE = 6fafcfde8baf7caa771eeb1db0839c9e56a8dbee
FORGE_PIN = 8c7e9afb8e6caee88644b94e25da5852e36f8928
ARTIFACT = 10085425128 (ws33-c-abilitysub-batch-34302341424)
ARTIFACT_DIGEST = sha256:1845cca270ba5647821ff844bb069c1047eb802d678eea31b9255d2c9e785189
COVERAGE_PROMOTION = FALSE

## Independent verification (artifact ZIP digest matches GitHub digest)

- Tests run 3, Failures 0, BUILD SUCCESS. Diagnostics empty, 7 markers.
- Pair-matching functional end to end: bane (70->71 seq1<2, 71->72 seq3<4),
  chopper/armor two-link chains, cap keywords, cloudblazer re-witness
  (14->15 seq1<2). Wrapper envelopes present, unattributed, inert.
- Declared singleton consultations observed exactly (AttachEffect caller,
  options=1) in chopper/armor; incidental-only elsewhere.
- ALL in-test semantic assertions PASS with correct VALUES.
- Gate PARTIAL solely due to "semantic expectation mismatch" on every
  first assertion: record `expected` serialized as JSON STRING ("2")
  vs plan INTEGER (2). Values equal, types differ.

## Root cause (HARNESS SERIALIZATION DEFECT, C-local)

`writeRecord` quotes `assertion.expected` via `q()` (string) while the plan
carries ints/bools. No semantic, ordering, attribution, or profile issue.
Evidence itself is valid; the record/plan comparison is type-strict.

## Repair (minimal, systemic)

- Harness: emit typed `expected` (int/bool detection, fallback string).
- Certifier: normalize both sides before comparing (documents the
  JSON-typing contract; strict on semantic value).
- No definition/workflow change: batch digest UNCHANGED (2adfe66e…).

EVIDENCED_PATH_COUNT = 1 (unchanged)
REMAINING_UNKNOWN_COUNT = 699 (unchanged)

## Exact next action

Commit FAIL + fix, push (replacement run, same digest), PENDING,
per-path adjudication, repartition.

TURN_STATUS = INTERRUPTED
TASK_COMPLETE = NO
