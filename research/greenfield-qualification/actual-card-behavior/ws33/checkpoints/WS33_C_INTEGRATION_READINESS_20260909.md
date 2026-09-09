# WS33-C read-only integration readiness dossier (NO promotion authority)

Date: 2026-09-09. Prepared from the AF8/B repaired successor
(`work/ws33-serial-integration-af8-b-20260909`) WITHOUT touching C, the
successor ledger, or any source branch. All C facts read via explicit refs
(`git show <C-HEAD>:`) and live gh API. No C ledger promotion performed or authorized here.

## Source lock (re-read live 2026-09-09)

- C_BRANCH = `work/ws33-c-high-throughput-20260907`
- C_HEAD = `449853245141af6e76cf186b019e974813403af3` (== live origin ref; commit `ws33c: pilot re-run 34289612464 PASS (source-seal fix validated)`)
- C_TREE = `32bceaa770c682b320b385a7600cb145c825d94b`
- C_MERGE_BASE (with repaired successor) = `895240f4058076764227a418ad28e84f61d3a7ed`
- C-base ancestry: C-base is an ANCESTOR of canonical base `6da237b7` (C branched from the pre-repair AF8 line: `edd9fb3a21` -> `43807b57b4` -> `00bb441136` -> `895240f4` -> ... -> `6da237b7` -> 6 repair commits -> AF8 HEAD). C-tip is 19 commits behind the repaired successor HEAD by ancestry.
- C run source for re-run: `6b3dde813b6613a1e6891b1cdec2cb8d6de97063` (== parent of C_HEAD; C_HEAD adds only the PASS checkpoint markdown — frozen-source pattern intact).

## Manifest / partition (recomputed against repaired ledger)

- Owned manifest `c-campaign/WS33_C_UNKNOWN_MANIFEST.json`: 700 paths, discrepancy 0, dispatch-time UNKNOWN 700. sha256 `b47510017fbfd5cae478917c37f83c1a41e73095eb49a2fa9ecb43360c809ca4` (as checkpointed).
- Repaired-ledger cross-check (recomputed): ledger WS33C set == manifest 700 EXACTLY; all 700 UNKNOWN in the repaired ledger. C untouched by AF8/B/203 repairs (C_UNKNOWN still 700, identical membership).
- BY_TARGET: AbilitySub 355, SpellApiBased 173, AbilityApiBased 172. CLUSTERS=20; RANK1 = AbilitySub/template-113/STATE_ONLY/176; STATE_ONLY total 305.
- C evidence partition `WS33_C_EVIDENCE_PARTITION.json` (`f1003eb3...`): EVIDENCED=1, REMAINING_UNKNOWN=699 (WITNESS_QUEUED_STATE_ONLY 304; DECISION+REPLAY infra-pending 269; HIDDEN 66; DECISION+HIDDEN+REPLAY 43; RNG mixes 17).

## What run 34289612464 actually proves

- Workflow `WS33-C AbilitySub pilot (production-parent witness)`: conclusion SUCCESS at source `6b3dde81` (source-seal fix: certifier now seals exact run source in-gate; prior gate caveat repaired same turn).
- Artifact `10080893537`, digest `sha256:55a89a49cb8bc72aa2696159e4809c6775370ed2a70af494d542c3688591e909` (live gh API: run SUCCESS, headSha == run source).
- Scope: ONE pilot path `forge-behavior-v2:b42b594f2523a243cf1b4877de9612a831bb71f6` (Cloudblazer ETB TrigGainLife->DBDraw, template-113, STATE_ONLY). 11/11 hashes verify; 3/3 state assertions PASS (life 20->22, hand 1->2); ordered GainLife->Draw production observations identical to run 34289134780; outcome unchanged by re-run.
- Production parent -> child execution DEMONSTRATED for this path: trace shows seq0 GainLife (production root) -> seq1 Draw with parent GainLife/Cloudblazer via `AbilityUtils.resolve` production entrypoint (entrypoint proof in `WS33_C_PARENT_ENTRYPOINT.md`: `AbilityUtils.resolve:1299` -> `resolveApiAbility:1377` -> `resolveSubAbilities:1357` -> child `AbilitySub.resolve:98`; `setSubAbility` wires non-null parent). Direct-child-only construction (parent null) structurally incapable and rejected by in-test fail-closed negative.
- Evidence class supported: TECHNICALLY_CONFORMANT (state + production-parent witness + fail-closed negative; decision NOT_REQUIRED for this untargeted path). NOT EXTERNALLY_RULE_VALIDATED. COVERAGE_PROMOTION=FALSE, COVERAGE_MUTATED=FALSE.

## Source / digest seals

- Run/job/artifact/digest: DIRECTLY_VERIFIED (live gh API + checkpointed independent adjudication for both 34289134780 and 34289612464).
- Forge pin `8c7e9afb...` throughout. Model manifest/consumer binding for C pilot records: NOT established in the pilot checkpoints (certifier checks source/pin/harness, no model-digest gate found) — must be bound before any C promotion proposal.
- C-base-era tooling predates the 6 AF8 repair commits; C pilot subsystem (AbilitySub production-parent) is disjoint from AF8 SVar-harness changes, but C's workflow/harness files have NOT been rebased onto repaired AF8 tooling (e.g., bounded-number overlay, sealed-bundles) — assess at integration time whether C harness needs the repair-era practices (source-seal pattern already adopted independently).

## Affected files (C-base..C-tip: 17 files, +1435/-0, pure additions)

- `.github/workflows/ws33-c-abilitysub-pilot.yml` (new, standalone)
- `c-campaign/`: manifest, cluster queue, evidence partition, parent entrypoint doc, 4 scripts (derive/prepare/partition/certify), Java harness `Ws33AbilitySubCampaignTest.java`
- 7 C checkpoints (manifest-ready, FAIL/PENDING/PASS x runs)
- No shared-file modifications (no PROJECT_STATE, no ledger/queue/gate, no B/AF8/A/D/E/F campaign files). All 17 paths ABSENT on the repaired successor: zero file-level conflicts for a future merge.

## Overlap with repaired AF8/B successor

- Path-set overlap: C-700 ∩ B-664 = ∅ expected (distinct subsystems/buckets; C-700 == ledger C_UNKNOWN verified above; B-664 all WS33B). C-700 ∩ A1/G3-203 = ∅ (buckets A/G vs C). Pilot path UNKNOWN in repaired ledger (verified live).
- Ancestry overlap: successor already contains everything C-base has and more (C-base ancestor of successor HEAD); a future C integration merges ONLY the 17 C-owned files forward (fast-forward-equivalent for content, pending Sol instruction).
- Historical evidence inheritance impact: none required yet (no C promotion proposed; pilot evidence stands on its own run/artifact with same pin; model binding TBD).

## Exact proposed C transition set

- NONE at this time. No C promotion proposal exists; pilot is 1/700 paths at TECHNICALLY_CONFORMANT; COVERAGE_PROMOTION=FALSE on C branch.
- C's own exact next action (per its checkpoint): rank-1 expansion — template-113 remainder (175 STATE_ONLY paths): extend `ws33_prepare_abilitysub_campaign.py` with verified untargeted-trigger rows, bump workflow case-count assertions, register PENDING, run, adjudicate, re-partition with `ws33_partition_c_evidence.py`.

## Exact next serial integration steps (for a later Sol instruction; NOT executed)

1. Sol authorizes C wave after C expansion run(s) PASS + promotion proposal with PENDING discipline.
2. New isolated integration branch from the repaired successor tip (this branch stays frozen).
3. Integrate C-owned files (expect clean apply: disjoint paths); re-verify C run/artifact/source seals incl. model-digest binding; recompute C-700 UNKNOWN membership + disjointness vs successor PASS (1152); PENDING freeze; promote only proposal-authorized paths; recompute derived registries with the same mechanism pattern; validate; handoff.

## Sol adjudication questions

1. Is TECHNICALLY_CONFORMANT production-parent witness evidence (C pilot shape) an admissible PASS basis for STATE_ONLY C paths, or is EXTERNALLY_RULE_VALIDATED required (rules citations per path as in B)?
2. Confirm model manifest/consumer digest binding requirement for C campaign evidence before promotion.
3. Target-attribution defect (345/700 C paths reference `forge.game.spellability.SpellApiBased/AbilityApiBased`, nonexistent at pin; actual `forge.game.ability.*`): repair attribution metadata first, or qualify with recorded defect + fail-closed treatment?
4. C harness rebase onto repair-era AF8 tooling: required before C expansion runs, or is C's standalone harness + adopted source-seal practice sufficient?

## Classification

Locks/membership/counts/file lists: DIRECTLY_VERIFIED by recomputation. Run/artifact facts: DIRECTLY_VERIFIED (live gh API). C-internal evidence characterization: CODE_DERIVED + EXTERNALLY-referenced (C checkpoints; not re-adjudicated here — read-only dossier).

No promotion authority exercised. `COVERAGE_PROMOTION=FALSE` for C.
