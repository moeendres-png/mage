# WS33 serial successor — preservation investigation + PENDING repair freeze

Date: 2026-09-09. Branch: `work/ws33-serial-integration-af8-b-20260909` (HEAD `cf05b1dd21`, tree `fac64de6e`, clean; 11 ahead/0 behind canonical base; AF8 in ancestry; 5 ahead of AF8 — all re-verified live, matching Sol High locks).
Status: PRESERVATION_DEFECT=CONFIRMED (Case 1). PENDING repair freeze. `COVERAGE_PROMOTION=FALSE` for the repair until executed.

## Phase 0 re-lock

Successor HEAD/TREE equal the Sol High adjudication values; no legitimate advance since. All Phase-0 reads completed (AGENTS.md, PROJECT_STATE.md, operational state, ledger, queue, gate, AF8B promotion evidence + index, all three serial-int checkpoints, G3/A1 operational evidence incl. successor artifact 9979204198 contents and repo-sealed digests). Live counts recomputed: TOTAL=4188 PASS=949 UNKNOWN=3239, B_UNKNOWN=11, queue 3239/234.

## Phase I — PRIOR_VALID_PASS_SET (derived, not inferred)

Exact set of 203 paths, every member verified on all dimensions:

- Stable identity: all 203 present exactly once in the current 4188-ledger (ledger IDs 4188-unique); identical strings in successor artifact ledger, A1 records, manifest partition, promotion evidence.
- Prior PASS: all 203 PASS in sealed immutable successor artifact 9979204198 (digest verified live; artifact-internal counts 488/3700; promotion evidence status PASS, unrelated changes 0, regressions 0).
- Partition: 122 WS33A/`forge.game.spellability.TargetRestrictions` (A1, EXTERNALLY_RULE_VALIDATED, per-record evidence in sealed `a1/` copy: 122/122 records, gate PASS, same Forge pin + manifest) + 81 WS33G/HIDDEN_RNG_REPLAY (G3, TECHNICALLY_CONFORMANT, IDs == pinned manifest HIDDEN_RNG_REPLAY partition exactly; checkpoint G3_COMPLETE_CROSS_QUALIFICATION_20260905.md binds 28+21+32=81 with constituent run/artifact digests).
- Evidence digests: A1 source artifact 9979087306 digest verified live (`a414f73b...`); successor artifact digest verified live (`ae75ff01...`); G3 constituents 8/10 digests verified live, 2 expired (9958136895, 9958147261 — HTTP 404, classified retention-expiry, NOT invalidation: the sealed successor re-verified them at seal time and persists as the authoritative binding).
- Source compatibility: Forge pin identical (`8c7e9afb...`) across A1 gate, B1/B2 gates, manifest, branch state; model manifest/consumer digests identical. No rekeying (id_contract stable).
- Invalidation: NONE. AF8 repair touches only the A-rest SVar harness/overlays/workflow (subsystem-disjoint from TargetRestrictions and HIDDEN/RNG effect paths; harness overlays, not production engine changes). B1/B2 touch only calculateAmount/Cost (subsystem sets disjoint from the 203). No pin/model change. PASS_EVIDENCE_INVALIDATED=FALSE for all 203.
- Current status: all 203 UNKNOWN in the live successor ledger (omitted by the B-only promotion base, which started from the 285 branch coordination files).

Result: INHERITABLE_PASS=203, INVALIDATED_OR_SUPERSEDED=0, DUPLICATE_OR_REKEYED=0, UNKNOWN-among-candidates=0.

## Phase II — disjointness and impact (independently recomputed)

- A(203) ∩ B(664) = 0; ∩ B1-full-273 = 0; ∩ B2-397 = 0; ∩ held-11 = 0.
- Subsystem sets disjoint (A: TargetRestrictions + 15 effect targets; B: calculateAmount + Cost).
- B-664 PASS standing re-verified (all 664 PASS in live ledger; repair must assert no regression).

## Phase III — adjudication: Case 1 CONFIRMED

The 203 are valid, disjoint, inheritable predecessor PASS omitted from the integrated ledger/state. The "branch files superseded" doctrine does not legitimize the omission here: this successor's frontier IS the branch files (ledger/queue/gate mutated for B; PROJECT_STATE + operational state point at them), so the frontier must contain every adjudicated PASS. Leaving sealed PASS as UNKNOWN beside newly-promoted B paths is incoherent and misdirects 203 paths of future work-queue effort. No new coverage credit is created by the repair (all credit sealed 2026-09-05/06).

Expected invariant (fully proven 203-case): TOTAL=4188, PASS=285+203+664=1152, UNKNOWN=3036; shards A 57 / B 11 / C 700 / D 920 / E 1029 / F 319 / G 0 / H 0.

## PENDING repair freeze (no registry mutated yet)

- Frozen live source: HEAD `cf05b1dd21`, TREE `fac64de6e70e10b99474669603c722c7c21553bf`.
- Authorized repair set digest: `sha256:a51c01b8cb953eda0c79bf1a6416061ae47be6672c326e4a92a8122fb8955b43` (sorted 203 IDs, LF-joined, trailing newline).
- Repair must preserve: AF8 integration; B-664 exactly (assert all remain PASS); 6 defaults UNKNOWN; 5 blockers UNKNOWN; every other UNKNOWN stays UNKNOWN.
- Live pre-repair totals: PASS=949 UNKNOWN=3239 (B_UNKNOWN=11). Expected post: PASS=1152 UNKNOWN=3036.
- Mechanism: deterministic `ws33_promote_prior_pass_frontier.py` (G3/A1/B-pattern gates) from frozen `WS33_PRIOR_PASS_PROMOTION_INDEX.json`; staged output independently re-audited before install.

## Classification

Set derivation/disjointness/counts: DIRECTLY_VERIFIED by recomputation. Prior PASS standing: DIRECTLY_VERIFIED (sealed successor artifact + live digests) + CODE_DERIVED (partition/source reads). Expired-constituent classification: CODE_DERIVED + DIRECTLY_VERIFIED (live 404s). Impact analysis: CODE_DERIVED (file/subsystem diff) + DIRECTLY_VERIFIED (pin/model/ledger recomputation).

`COVERAGE_PROMOTION=FALSE`. `WS33_COMPLETE=FALSE`. `TASK_COMPLETE=NO`.
