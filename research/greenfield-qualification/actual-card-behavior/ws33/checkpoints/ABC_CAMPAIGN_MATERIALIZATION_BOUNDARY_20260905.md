# WS33 ABC Campaign Materialization Boundary — 2026-09-05

Evidence class: `DIRECTLY_VERIFIED` for repository/queue/workflow facts; `CODE_DERIVED` for the execution selection below.

## Canonical source boundary

- branch: `work/ws33-g3-final-closure-20260902`
- pre-materialization HEAD: `14805bc96c2277745b0b25158024ffba20c676f1`
- pre-materialization TREE: `1f206d935577da65776f0f40171fabd74011706d`
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- effective manifest SHA256: `cd48f4279d682ab944e2534bf937d87e5311e83989e97179ae73c5c7d1bb6224`
- consumer-model SHA256: `82638e6b3e4408cc5bddedc49372b6357d3c2bdce6fba7bfab7ed119678f9a48`

## Post-G3 frontier

- TOTAL: 4188
- PASS: 366
- UNKNOWN: 3822
- FAIL: 0
- UNSUPPORTED: 0
- A_UNKNOWN: 179
- B_UNKNOWN: 675
- C_UNKNOWN: 700
- ABC_UNKNOWN: 1554

No coverage is promoted by this checkpoint.

## Runtime-campaign infrastructure adjudication

The current `campaign/` directory contains only the runtime-campaign record schema; there is no generic ABC executor there.

The retained `.github/workflows/ws33-integrated-closure.yml` is a frontier/requirement-projection audit only. It does not execute new actual-card behavior campaigns and cannot close ABC.

The retained `.github/workflows/ws33-q6-runtime-closure.yml` does contain a production-reachable actual-card `TargetRestrictions` Record/Replay campaign path. It:

1. checks out the exact pinned Forge;
2. applies retained Decision, hidden-information, RNG/replay, WS33 input/stack-target and failure-semantics overlays;
3. materializes cases from `WS33_EFFECTIVE_BEHAVIOR_PATH_MANIFEST.json` using `ws33_prepare_target_campaign.py`;
4. executes `Ws33TargetRestrictionsCampaignTest` in Record and Replay modes;
5. captures diagnostics and immutable witness material.

Historical Q6 campaign outputs are not themselves promotable for post-Gen2 ABC. The implementation path is reusable only for a fresh run against the current source/model lineage.

## First resumable ABC execution unit

The highest-volume directly reusable ABC unit identified in the current integrated work queue is:

- logical bucket: `WS33A`
- owner family: `ACTION_COST_DECISION`
- runtime subsystem: `forge.game.spellability.TargetRestrictions`
- scenario group: `ws33-g2-template-123`
- evidence profile: `DECISION+REPLAY`
- unresolved paths in this work item: **122**

This is selected as `ABC-A1` because the existing actual-card campaign is already designed around the same authoritative Forge subsystem and evidence profile. The fresh campaign must not infer legality itself: the external pilot may select only targets/DONE emitted by Forge.

## Execution contract for ABC-A1

A new current-branch workflow may reuse the existing target-campaign generator/test and retained overlays, but must:

- bind to the exact current WS33 source/model lineage and exact Forge pin;
- execute actual Forge card sources, not synthetic `AbilitySub`/direct `effect.resolve(...)` substitutes;
- retain initial/final semantic state, authoritative legal Decision options/responses, and Record/Replay evidence;
- preserve principal scoping where observations exist;
- prohibit silent first/default/random/pass/cancel/AI fallback;
- produce an immutable artifact with internal hashes;
- keep global coverage unchanged until terminal evidence is independently adjudicated;
- promote only current ABC effective-path IDs that have fresh admissible evidence.

## Transaction state

- `ABC_A1_STATUS = READY_TO_MATERIALIZE`
- `ABC_A1_COVERAGE_PROMOTION = FALSE`
- `ABC_STATUS = UNKNOWN`
- `WS33_COMPLETE = FALSE`
