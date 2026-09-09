# WS33-A AF8 — worktree/source-lock established (2026-09-09)

Status: **SOURCE_LOCKED**. `COVERAGE_PROMOTION=FALSE`. `COVERAGE_MUTATED=FALSE`.
All eight AF8 paths: **UNKNOWN** (evidence candidates only, pending coordinator adjudication).

## Source lock (verified live before provisioning)

- REPOSITORY: `moeendres-png/mage`
- BRANCH: `work/ws33-a-trigger-closure-20260907`
- HEAD / AUDIT_BASE: `895240f4058076764227a418ad28e84f61d3a7ed`
- TREE / EXPECTED TREE: `cec73ae51b0168280ea648892f3e9edd46dcd883`
- FORGE_PIN: `8c7e9afb8e6caee88644b94e25da5852e36f8928` (exists)
- WORKTREE: `/home/moeen/code/mage-ws33-a` (fresh `git worktree add --track`, clean `git status --short --branch`)
- Remote A tip re-verified immediately before creation: still exactly `895240f4…`. No drift.
- No workflow triggers on the A branch (no `work/ws33-a` in `.github/workflows/`); A pushes are run-free until explicit dispatch.

## Prior verified state carried forward (not re-derived)

- Exact AF8 path set (8, Quinjet excluded), route input RUN `34063748962` / ARTIFACT `9998291348` /
  SOURCE `48cb9a018f606f1209d14ee587a6ff3f14d263a1` / DIGEST `sha256:6465…f9d0e9`.
- Predecessor AF8 run `34064602879` terminal FAILURE (PATH_ROUTE_PROJECTION + packaging/observation gaps).
- No A runtime run exists yet.

## Investigation completed this turn (CODE_DERIVED, from pinned sources)

- AF8 workflow at HEAD already integrates hardener/adjudicator + always-run sealing, but its overlay
  stack omits `apply-ws33-stack-resolution-reachability.py` and
  `apply-ws33-a-rest-play-stage-observer.py`, although the hardener binds
  `MagicStack.setWs33ResolutionObserver` / `AbilitySub.setWs33ResolutionObserver` /
  `PlaySpellAbility.setWs33PlayStageObserver`. Direct31 v2 order is the template; Direct31 v6 PASS
  (`34058637176`) additionally retains `apply-ws33-mana-cancel-boundary.py` after the play-stage
  observer (rail=TRACED). Assessment: wire all three in v2/v5 order, keep SVar reachability.
- X-announcement route (Forge pin, `PlaySpellAbility.announceValuesLikeX` ->
  `PlayerControllerHuman.announceRequirements`): mandatory-cost productions use
  `chooseNumber(sa,title,min,max)` -> external kind `NUMBER` (1/1 discrete ints);
  non-mandatory uses GUI `getInteger` -> kind `GUI_GET_INTEGER`. Current hardener X policy keys on
  script `Announce$ X` + any 1/1 numeric request with no kind check: too broad. Repair: require
  kind `NUMBER`, keep authoritative options/min/max, keep smallest-positive-int policy.
- `apply-ws33-svar-reachability.py` touches only `AbilitySub.java`; stack-resolution touches
  `MagicStack.java` + `PlaySpellAbility.java` fields; play-stage anchors on stack-resolution's
  helpers: required order stack-resolution -> play-stage is confirmed by anchor dependency.
  `apply-ws33-mana-cancel-boundary.py` supports the traced `InputPayMana` variant, so play-stage
  must precede it (v5 order).

## Remaining repairs (accepted, to implement)

1. Workflow: add the three overlay applications + PASS/rail gates + trigger paths.
2. Hardener: kind-scoped positive-X policy; identity-bound target evidence (source/root/child/
   actor/target ids + per-target before/after zone/keyword); per-policy selection witness export
   (`AF8_SELECTION_WITNESS.tsv`) with forced/non-discretionary classification.
3. Adjudicator: success-gated play stages (not counts); exact zone-movement / keyword-gained
   target postconditions; X-positive + mode-cardinality + creature-target rules derived from case
   scripts (no card-name branches); forced-classification recomputation; witness replay equality.
4. Local gates: py_compile + unit tests incl. new adjudicator negatives; overlay anchor validation
   against pin-fetched Forge files; full Python harness-chain dry run.

## Exact next action

Finish route ZIP download verification (`/tmp/af8-route/routes.zip`, meta.json digest/run/sha
already match), then implement repairs 1-4 in the A worktree only.

`TURN_STATUS=INTERRUPTED`. `TASK_COMPLETE=NO`.
