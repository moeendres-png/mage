# WS33-C milestone checkpoint: owned manifest + rank-1 pilot harness ready

BRANCH = work/ws33-c-high-throughput-20260907
AUDIT_BASE_SHA = 895240f4058076764227a418ad28e84f61d3a7ed
AUDIT_BASE_TREE = cec73ae51b0168280ea648892f3e9edd46dcd883
HEAD = 895240f4058076764227a418ad28e84f61d3a7ed
TREE = cec73ae51b0168280ea648892f3e9edd46dcd883
SOURCE_LOCK_MATCH = TRUE (branch did not advance; no new lock needed)
FORGE_PIN = 8c7e9afb8e6caee88644b94e25da5852e36f8928
COVERAGE_PROMOTION = FALSE
COVERAGE_MUTATED = FALSE

## Owned manifest (recomputed from canonical inputs, deterministic)

- `c-campaign/WS33_C_UNKNOWN_MANIFEST.json`
  sha256 b47510017fbfd5cae478917c37f83c1a41e73095eb49a2fa9ecb43360c809ca4
- `c-campaign/WS33_C_CLUSTER_QUEUE.json`
  sha256 a88842375e5e91894acb238c6306a60760dc77d0f098e5dbbd2069e2dbca1482
- OWNED_PATH_COUNT = 700; dispatch-time C UNKNOWN = 700; DISCREPANCY = 0.
- BY_TARGET: AbilitySub 355, SpellApiBased 173, AbilityApiBased 172.
- CLUSTERS = 20; RANK1 = AbilitySub / ws33-template-113 / STATE_ONLY / 176.
- STATE_ONLY total = 305 (cheapest gate order).

## New findings (branch-owned, canonical inputs untouched)

1. **Target attribution defect** (model/path attribution, not engine):
   `forge.game.spellability.SpellApiBased` and
   `forge.game.spellability.AbilityApiBased` do not exist at FORGE_PIN;
   actual classes are `forge.game.ability.SpellApiBased` and
   `forge.game.ability.AbilityApiBased` (345/700 C paths affected).
   `forge.game.spellability.AbilitySub` is correct. Recorded per-path as
   `target_attribution_defect` in the owned manifest. Effective path IDs
   unchanged (immutable).
2. **Production parent entrypoint proven at pin** (see
   `c-campaign/WS33_C_PARENT_ENTRYPOINT.md`): `AbilityUtils.resolve`
   (AbilityUtils.java:1299) -> `resolveApiAbility` (:1377) ->
   `resolveSubAbilities` (:1357) -> child `AbilitySub.resolve`
   (AbilitySub.java:98). `MagicStack` calls `AbilityUtils.resolve` (6 call
   sites). `SpellAbility.setSubAbility` wires `child.setParent(this)`, so a
   production-linked child always has a non-null parent while a directly
   constructed child has `parent == null` — the fail-closed discriminator.
3. **Pilot path**: `forge-behavior-v2:b42b594f...` ({SubAbility: DBDraw},
   template-113, STATE_ONLY, 6 card occurrences) via Cloudblazer ETB
   (`TrigGainLife` -> `DBDraw`), untargeted/choice-free/cost-free, avoiding
   the WS33B Cost/payment surface.

## Work completed

- `c-campaign/ws33_derive_c_manifest.py` (deterministic manifest+queue).
- `c-campaign/WS33_C_PARENT_ENTRYPOINT.md` (entrypoint + evidence proof).
- `c-campaign/ws33_prepare_abilitysub_campaign.py` (1-case pilot TSV+plan).
- `c-campaign/Ws33AbilitySubCampaignTest.java` (generic production-parent
  harness, record mode + in-test fail-closed negative).
- `c-campaign/ws33_certify_abilitysub_pilot.py` (adjudicator + self-test).

## Tests / evidence

- `py_compile` all three scripts: PASS.
- Adjudicator `--self-test` (positive accept + direct-child-only reject):
  PASS.
- Preparer determinism: pilot TSV sha256
  bc1046c480e1be0f7707082347ebcc4b912434f4b3ca104aec6e55d39dab50de.
- `apply-ws33-svar-reachability.py` overlay applies cleanly to
  `AbilitySub.java` at FORGE_PIN on a scratch copy: PASS
  (observation_only=TRUE). Scratch only; no Forge tree mutated.
- ApiType `Draw`/`GainLife` exist at pin: verified.
- Evidence classification: DIRECTLY_VERIFIED (command outputs/hashes);
  CODE_DERIVED (entrypoint/attribution mapping from pinned source).

## PASS / UNKNOWN partition (branch-owned, not canonical)

- EVIDENCED_PATH_COUNT = 0 (no Forge witness run yet).
- REMAINING_UNKNOWN_COUNT = 700.
- ROOT_CAUSE_CLASSES so far: MODEL_ATTRIBUTION_DEFECT (345 paths, package
  string); WITNESS_PENDING (all 700, pilot harness ready, run not started).

## Remaining blockers

- No external/authority blocker. Pilot Forge run (record) not yet started;
  requires new workflow `ws33-c-abilitysub-pilot.yml` (branch-owned) that
  checks out FORGE_PIN, applies the svar-reachability overlay, copies the
  harness test, runs record mode, and uploads artifacts.

## Exact next action

1. Add `.github/workflows/ws33-c-abilitysub-pilot.yml` (record-only pilot,
   1 case) on this branch, commit, push.
2. Register PENDING checkpoint with RUN/JOB IDs, then dispatch/adjudicate
   the pilot run; on terminal status persist PASS/FAIL with root cause
   before any repair.
3. On pilot PASS, expand mechanically across rank-1 (template-113)
   untargeted-trigger rows, then next STATE_ONLY clusters; classify
   decision/hidden/RNG clusters as WITNESS_INFRASTRUCTURE_PENDING with
   explicit per-cluster blockers.

TURN_STATUS = INTERRUPTED
TASK_COMPLETE = NO
