# ABC-D4a staticeffect run 34406229809 — PENDING (registered)

Date: 2026-09-09. Branch: `work/ws33-d-high-throughput-20260907`.
TERMINAL_RESULT=PENDING. COVERAGE_PROMOTION=FALSE. WRITE_FREEZE in effect
for D4a machinery/paths until terminal adjudication.

## Frozen run source

- SOURCE_HEAD=`49e597b6522a8f977af20088e93b9a09ba7aea5e`
  (contains: D4 shape survey + sum correction + repaired D4a 8-path
  witness machinery: preparer/filter/certifier/workflow + rewritten
  `Ws33D4StaticeffectCampaignTest`)
- SOURCE_TREE=`978a8f156ca49cb80dc071f462dc5d2a473fd967`
- RUN=`34406229809` (head_sha verified equal to SOURCE_HEAD at registration)
- EXPECTED_ARTIFACT=`ws33-abc-d4-staticeffect-34406229809`

## Scope

8 provable EffectEffect paths (TARGET_DIGEST
`5094aa9178d1ead54d2b9cadb69f0a3c88381047bf8c6412a2559b00d454861b`),
41 deferred (D4b 3 / D4c 21 / D4d 2 / D4e 14 / D4f 1, all remain UNKNOWN).
Same immutable pins/model artifact as D1/D2/D3 (FORGE_PIN `8c7e9afb`,
WS01 `bf089ea8`, WS12 `80743bd`, WS32 `6ca2a7b`, model artifact
`9823383539`). No other D4 path may be exercised or credited by D4a
machinery. D-local evidence stays 25 evidenced / 895 UNKNOWN until
terminal adjudication; survey/repartition alone create zero credit.

## Exact next action

Poll run 34406229809 to terminal; adjudicate artifact independently
per-path (8 separate verdicts). On PASS: repartition D (25+8 evidenced)
and continue per ranked plan (D4b/c/d/e/f + D5 tail). On fail: persist
root-cause classification before any repair.
