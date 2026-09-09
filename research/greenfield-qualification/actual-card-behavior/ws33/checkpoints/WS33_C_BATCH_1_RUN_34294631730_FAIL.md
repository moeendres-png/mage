# WS33-C Batch 1 run 34294631730 terminal FAIL (adjudicated)

RUN = 34294631730
JOB = 102288462712
JOB_CONCLUSION = failure (step "Execute batch Record", test compilation)
SOURCE_HEAD = f67cff1a1537ae1bdb4c8d2da3d218f79618ab94
SOURCE_TREE = 14587d1482163874cc38b54497bf1abc6c0a9402
FORGE_PIN = 8c7e9afb8e6caee88644b94e25da5852e36f8928
ARTIFACT = ws33-c-abilitysub-batch-34294631730 (overlay + materialization logs)
COVERAGE_PROMOTION = FALSE

## What passed (DIRECTLY_VERIFIED from run log)

- Manifest binding, all self-tests, runtime pins.
- All overlays incl. NEW parent-resolution + decision-tripwire PASS.
- Batch materialization PASS (7 executions / 9 path-slots, digest match).

## Root cause (HARNESS DEFECT, branch-owned test code, compile-time)

`Ws33AbilitySubWitnessTest.java:151`: `for (final String placement :
first.setup)` iterates a String. The setup cell is a `;`-joined string and
must be split first (empty setup skipped). Forge `javac` correctly rejects
it; no production/overlay/model behavior implicated.

Local reproducer: none needed beyond the compiler diagnostic (deterministic
compile error, no runtime involved). The identical pattern will be covered
by keeping CI compilation as the gate plus a local brace/paren + API review
checklist for future harness edits.

## Classification

- Failing layer: branch-owned harness (test-compile).
- NOT engine / overlay / model / witness-reachability.
- No Sol escalation (no semantic/architecture question).

## Repair plan (minimal)

Split `first.setup` on `;` (skip when blank) in `execute()`. Re-run the
identical batch (same digest) as replacement run.

EVIDENCED_PATH_COUNT = 1 (unchanged)
REMAINING_UNKNOWN_COUNT = 699 (unchanged)

## Exact next action

Commit this FAIL checkpoint + one-spot harness fix, push, register
replacement run PENDING, adjudicate per-path.

TURN_STATUS = INTERRUPTED
TASK_COMPLETE = NO
