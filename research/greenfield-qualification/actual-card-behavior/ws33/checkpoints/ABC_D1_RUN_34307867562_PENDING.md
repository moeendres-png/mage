# ABC-D1 lifegain run 34307867562 — PENDING (registered)

Date: 2026-09-09. Branch: `work/ws33-d-high-throughput-20260907`.
TERMINAL_RESULT=PENDING. COVERAGE_PROMOTION=FALSE. WRITE_FREEZE in effect
for all D1 paths until terminal adjudication.

## Frozen run source

- SOURCE_HEAD=`9b7622936c1701a2aa8dd562d698c37b446d70a6`
- SOURCE_TREE=`b026fc182db96df663e06bfe2a19547e614ec171`
- RUN=`34307867562` (head_sha verified equal to SOURCE_HEAD at registration)
- JOB=pending (record at first poll); EXPECTED_ARTIFACT=`ws33-abc-d1-lifegain-34307867562`
- WORKFLOW=`.github/workflows/ws33-abc-d1-lifegain.yml` (this source)

## Frozen selection

- Queue item WS33D/template-059/STATE_ONLY/LifeGainEffect (22 UNKNOWN).
- Provable D1 set: 10 path ids, TARGET_DIGEST=
  `7de915711efb5e70387af86481f844bc701db7e4d448a5032255f71e5e6fbc40`
  (reproduced by local preparer+filter runs before freeze).
- Deferred registry: 12 exact ids with D6/D7 reasons (no silent drop).
- Anti-double-credit at freeze: 10 ∩ Serial-promoted-664 = 0;
  10 ∩ held = 0; retained-PASS `ede58d66` not selected.
- Plan: `generated/campaign/d1/ABC_D1_PLAN.json`; deferred:
  `generated/campaign/d1/ABC_D1_DEFERRED.json`.

## Immutable dependencies

- FORGE_PIN=`8c7e9afb8e6caee88644b94e25da5852e36f8928`
- WS01=`bf089ea806f54a9bbb64ede205915729e3629684`
- WS12=`80743bdbc2950b00e422f3deb38f04111f30a4d4`
- WS32=`6ca2a7bbacd074cc84fa4a6019c4d26e5e3717a9`
- MODEL_ARTIFACT=`9823383539` digest
  `sha256:aab73ba2ede151bbd0b803c2164d3067ddd65f17d49cf655c34eef67d903595d`
- MANIFEST=`cd48f4279d682ab944e2534bf937d87e5311e83989e97179ae73c5c7d1bb6224`
- CONSUMER=`82638e6b3e4408cc5bddedc49372b6357d3c2bdce6fba7bfab7ed119678f9a48`

## Expected evidence

10 markers, 10-record campaign index, empty record+replay diagnostics,
ACCEPTED-only decision tapes (single-option forced), RNG tapes
replay-served, hidden 0-leak, replay divergence 0, gate
`ABC_D1_GATE.json` + `ABC_D1_HASHES.sha256`.

## Exact next action

Poll run 34307867562 to terminal status; on completion adjudicate
artifact independently (ZIP digest, internal hashes, per-path records);
persist PASS/PARTIAL/FAIL before any repair; repartition only exact
validated paths; proceed to D2 (LifeLose 061) on reusable machinery.
