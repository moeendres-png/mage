# ABC-D4a staticeffect run 34409161259 — PENDING (registered, 2nd replacement)

Date: 2026-09-09. Branch: `work/ws33-d-high-throughput-20260907`.
TERMINAL_RESULT=PENDING. COVERAGE_PROMOTION=FALSE. WRITE_FREEZE in effect
for D4a machinery/paths until terminal adjudication.

## Frozen run source

- SOURCE_HEAD=`f658130cb1db3fca089d3d81e4da87c4d2efb885`
  (predecessor f05e00b4 + FAIL adjudication + `return acc` repair,
  stub-compile gated: full harness compiles clean against pin-derived
  API stubs, negative control reproduces the exact prior CI error;
  no recipe/fixture/pool/assertion/digest/pin/contract change)
- SOURCE_TREE=`d5b8c5e8cd900deeeccf60ad256e2dfcd52c4632`
- RUN=`34409161259` (head_sha verified equal to SOURCE_HEAD at registration)
- EXPECTED_ARTIFACT=`ws33-abc-d4-staticeffect-34409161259`
- Predecessor runs terminal FAIL (HARNESS_COMPILE_ERROR residues):
  34406229809 (`acc`/`assertions` param), 34407599333 (`return acc`
  residue); root causes classified before each repair.
- Duplicate push-delivery run 34409164024 (same HEAD) CANCELLED; it is
  not evidence and will never be adjudicated.

## Scope

Identical frozen scope: 8 provable EffectEffect paths (TARGET_DIGEST
`5094aa9178d1ead54d2b9cadb69f0a3c88381047bf8c6412a2559b00d454861b`),
41 deferred (all remain UNKNOWN). D-local evidence stays 25 / 895.

## Exact next action

Poll run 34409161259 to terminal; adjudicate artifact independently
per-path (8 separate verdicts). On PASS: repartition D (25+8 evidenced).
On fail: persist root-cause classification before any further repair.
