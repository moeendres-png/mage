# ABC-D4c single-target run 34432378875 — PENDING (registered, FINAL authorized)

Date: 2026-09-10. Branch: `work/ws33-d-high-throughput-20260907`.
TERMINAL_RESULT=PENDING. COVERAGE_PROMOTION=FALSE. WRITE_FREEZE in effect
for D4c-T1 machinery/paths until terminal adjudication.

## Frozen run source

- SOURCE_HEAD=`eb6235f413cba3587f223c86a13260660a78e011`
  (parent `bd90ee383be310b38b7c2913586fc35cccd8ef7a` == D4c remote
  authority at push time; delta vs authority is exactly Repair #2:
  harness entity-id unique-match correction in
  `runtime-tests/Ws33D4cTargetCampaignTest.java` plus terminal FAIL
  adjudication `ABC_D4C_RUN_34429297453_FAIL.md`; preparer/filter/
  certifier/overlays byte-identical to adjudicated run source `470ca9f70d`;
  local gates green: py_compile, javac zero syntax errors, Option
  `isEntityBacked`/`getEntityId` API proven in strict-decision-boundary
  patch, certifier fail-closed exit 1; no path-set/digest/pin/fixture/
  contract change)
- SOURCE_TREE=`1ff41cb01262524f8a97d9a0085b02a35a0a137e`
- RUN=`34432378875` (head_sha verified equal to SOURCE_HEAD at registration)
- EXPECTED_JOB=`d4c-target` (job id `102730394507` at registration)
- EXPECTED_ARTIFACT=`ws33-abc-d4c-target-34432378875`
- Immutable dependencies unchanged from runs 34426307199/34429297453
  (Forge pin `8c7e9afb…`, WS01 `bf089ea8…`, WS12 `80743bd…`, WS32
  `6ca2a7b…`, model artifact 9823383539, manifest `cd48f427…`, consumer
  model `82638e6b…`).
- COVERAGE_PROMOTION=FALSE. This consumes the single FINAL authorized
  D4c-T1 execution (Repair #2: bounded entity-id unique-match correction
  for the DIRECTLY_VERIFIED HARNESS defect of run 34429297453 — wrong
  target encoding assumption `CARD:<id>` vs authoritative entity-id
  encoding; predecessor defect #1 was the detached controller of run
  34426307199). No fourth run is authorized.

## Scope

Identical frozen T1 scope: 4 single-mandatory-target spell-cast paths
(TARGET_DIGEST
`1c16bf25383cb2f710513f3ac1c7b64dd9a48c53f8f481d9566a6dcdca9f00c6`),
45 deferred. D-local evidence stays 36 / 884 until terminal adjudication.
Intents all ENTITY. Expected: exactly 4 TARGET_SELECTION events (1/case,
ACCEPTED, entity-id unique-match to the registered controller), 0 RNG,
0 leaks, 0 divergence. Predecessor records were never promoted nor
reinterpreted. All four T1 paths remain UNKNOWN until certified.

## Exact next action

Poll run 34432378875 to terminal; adjudicate artifact independently
per-path (4 separate verdicts). On PASS: certify only the 4 T1 paths
(repartition to 40 evidenced / 880 remaining only if the certifier
proves it); persist terminal PASS checkpoint. On FAIL: adjudicate exact
causal class; leave all four T1 paths UNKNOWN unless actually certified;
terminate D4c FAIL CLOSED with no further repair-run cycle. Do not start
D4d/D4e/D4f, Batch-6, or Full107. ARCHITECTURE_FREEZE = NOT CLAIMED.
PRODUCTION_PROVIDER = NOT SELECTED.
