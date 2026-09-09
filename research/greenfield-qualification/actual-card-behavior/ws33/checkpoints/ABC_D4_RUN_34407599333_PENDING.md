# ABC-D4a staticeffect run 34407599333 — PENDING (registered, replacement)

Date: 2026-09-09. Branch: `work/ws33-d-high-throughput-20260907`.
TERMINAL_RESULT=PENDING. COVERAGE_PROMOTION=FALSE. WRITE_FREEZE in effect
for D4a machinery/paths until terminal adjudication.

## Frozen run source

- SOURCE_HEAD=`f05e00b4c107af9f5343218dc0ccee4d401803ac`
  (predecessor 49e597b6 + FAIL adjudication + one-line `acc` repair;
  no recipe/fixture/pool/assertion/digest/pin/contract change)
- SOURCE_TREE=`e44b80ff0cf98bba4bd2f8cb24e62e933d5383ae`
- RUN=`34407599333` (head_sha verified equal to SOURCE_HEAD at registration)
- EXPECTED_ARTIFACT=`ws33-abc-d4-staticeffect-34407599333`
- Predecessor run 34406229809 terminal FAIL (HARNESS_COMPILE_ERROR);
  root cause classified in `ABC_D4_RUN_34406229809_FAIL.md` before repair.

## Scope

Identical frozen scope: 8 provable EffectEffect paths (TARGET_DIGEST
`5094aa9178d1ead54d2b9cadb69f0a3c88381047bf8c6412a2559b00d454861b`),
41 deferred (all remain UNKNOWN). D-local evidence stays 25 / 895.

## Exact next action

Poll run 34407599333 to terminal; adjudicate artifact independently
per-path (8 separate verdicts). On PASS: repartition D (25+8 evidenced).
On fail: persist root-cause classification before any further repair.
