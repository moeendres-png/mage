# WS33-C pilot replacement run 34289134780 terminal PASS (independently adjudicated)

RUN = 34289134780
JOB = 102271495186
JOB_CONCLUSION = success
WORKFLOW_SOURCE_HEAD = 582f7be6fd8f0dae56467aa4235d83ce13307acb
WORKFLOW_SOURCE_TREE = d2ddb231a0a0bf3e2992d536b89f303ad9d687dd
FORGE_PIN = 8c7e9afb8e6caee88644b94e25da5852e36f8928
ARTIFACT = 10080709685 (ws33-c-abilitysub-pilot-34289134780)
ARTIFACT_DIGEST = sha256:3bdc2a51ca5766ce0c9db77fb9ea1e6fc752fcb20b25df77c9e28a7b4acbbcf4
COVERAGE_PROMOTION = FALSE
COVERAGE_MUTATED = FALSE

## Independent verification (artifact ZIP digest matches GitHub digest)

- `Tests run: 2, Failures: 0, Errors: 0` + BUILD SUCCESS
  (`Ws33AbilitySubCampaignTest`: production-parent campaign + fail-closed
  direct-child negative).
- `WS33_ABILITYSUB_CAMPAIGN_SUCCESS=1`; diagnostics 0 bytes; 1
  record-success.marker.
- Record `ws33-abilitysub-b42b594f...`: life 20->22 (+2), hand 1->2 (net +1),
  all 3 state assertions PASS, `actual_rules_core_path=true`,
  `silent_fallbacks=0`, `direct_effect_resolution=false`, decision
  NOT_REQUIRED, evidence TECHNICALLY_CONFORMANT.
- Trace: ordered child observations on host Cloudblazer —
  seq0 GainLife (chain root, parentless as production roots are),
  seq1 Draw with parent GainLife/Cloudblazer — proving the exact
  TrigGainLife->DBDraw link for
  `forge-behavior-v2:b42b594f2523a243cf1b4877de9612a831bb71f6`
  via `AbilityUtils.resolve` production entrypoint. Direct-child-only
  evidence structurally incapable of this (parent null) and rejected.
- `WS33_C_PILOT_HASHES.sha256`: all 11 entries verify against artifact bytes.
- Gate `WS33_C_PILOT_GATE.json`: status PASS, pilot_paths=1, promotion false.

## Gate caveat (minor certifier defect, repaired same turn)

The sealed gate's `source_head/tree` fields hardcode the audit lock, not the
run source. True run source is sealed in
`workflow-source-head/tree.txt` (above) and used in the partition record.
Certifier now takes `--source-head/--source-tree` (workflow passes
`$GITHUB_SHA` + `HEAD^{tree}`); all future runs seal exact source in-gate.

## Partition (branch-owned, not canonical)

- `c-campaign/WS33_C_EVIDENCE_PARTITION.json`
  sha256 f1003eb3e9108ba4bce8ae940949a644f5281f1d31d26e270924ec5ccd6d1105
- EVIDENCED_PATH_COUNT = 1 (path above, run/job/artifact bound).
- REMAINING_UNKNOWN_COUNT = 699 with explicit root-cause classes:
  WITNESS_QUEUED_STATE_ONLY 304; DECISION+REPLAY infra-pending 269;
  HIDDEN 66; DECISION+HIDDEN+REPLAY 43; RNG mixes 17 total.
- Model attribution defect (345 paths, `spellability` vs `ability` package)
  stands recorded in the owned manifest; unaffected by this PASS.

## Evidence classification

- run/job/artifact/digest/hash verification: DIRECTLY_VERIFIED.
- pinned-Forge production-parent execution + semantic postconditions:
  TECHNICALLY_CONFORMANT (as recorded by campaign).
- Rules refs 603.3/608.2 retained by record: EXTERNALLY_RULE_VALIDATED
  only as recorded; no official-rules claim beyond the campaign record.

## Exact next action

Expand mechanically across rank-1 remainder (template-113, 175 left,
STATE_ONLY, cost-free): extend preparer with verified untargeted-trigger
rows, extend workflow case count, register PENDING, run, adjudicate,
re-partition. Then next STATE_ONLY clusters (105/119). Decision/hidden/RNG
clusters stay UNKNOWN/WITNESS_INFRASTRUCTURE_PENDING (no pilot-side
legality, no fallback logic — escalate to Sol if authoritative decision
taping for SubAbility choices needs architecture input).

TURN_STATUS = INTERRUPTED
TASK_COMPLETE = NO
