# WS33-C pilot re-run 34289612464 terminal PASS (source-seal fix validated)

RUN = 34289612464
JOB_CONCLUSION = success
WORKFLOW_SOURCE_HEAD = 6b3dde813b6613a1e6891b1cdec2cb8d6de97063
FORGE_PIN = 8c7e9afb8e6caee88644b94e25da5852e36f8928
ARTIFACT = 10080893537 (ws33-c-abilitysub-pilot-34289612464)
ARTIFACT_DIGEST = sha256:55a89a49cb8bc72aa2696159e4809c6775370ed2a70af494d542c3688591e909
COVERAGE_PROMOTION = FALSE

## Independent verification (same rigor as 34289134780)

- ZIP digest equals GitHub artifact digest: PASS.
- Gate: status PASS, same pilot path, **source_head/tree now seal exact run
  source** (6b3dde81…/621c5807…) — certifier fix confirmed working.
- All 11 hash entries verify; 3/3 state assertions PASS; ordered
  GainLife->Draw production observations identical to prior run.
- Full per-record adjudication already persisted for the identical witness
  in WS33_C_PILOT_RUN_34289134780_PASS.md; this re-run changes no path
  outcome.

## Partition unchanged

EVIDENCED_PATH_COUNT = 1, REMAINING_UNKNOWN_COUNT = 699 (partition file
f1003eb3e9108ba4bce8ae940949a644f5281f1d31d26e270924ec5ccd6d1105 still current).

## Exact next action

Rank-1 expansion (template-113 remainder, 175 STATE_ONLY paths): extend
`ws33_prepare_abilitysub_campaign.py` with verified untargeted-trigger rows
(parent SVar + child Sub pointer + fixture kind + deltas, one card per row),
bump workflow case-count assertions, register PENDING, run, adjudicate,
re-partition with `ws33_partition_c_evidence.py`.

TURN_STATUS = INTERRUPTED
TASK_COMPLETE = NO
