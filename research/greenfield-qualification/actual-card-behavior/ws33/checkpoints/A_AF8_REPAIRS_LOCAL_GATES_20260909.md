# WS33-A AF8 — repairs + local gates complete (2026-09-09)

Parent: `A_AF8_WORKTREE_SOURCE_LOCK_20260909.md`.
Status: **REPAIRS_COMPLETE_LOCAL_GATES_GREEN**. `COVERAGE_PROMOTION=FALSE`. `COVERAGE_MUTATED=FALSE`.
All eight AF8 paths: **UNKNOWN** canonically (no remote run yet; candidates only).

## Source

- BRANCH: `work/ws33-a-trigger-closure-20260907`
- HEAD: `3a7182d4c6` (pushed; two commits over audit base: source-lock checkpoint + this repair batch)
- Remote A tip at push time: this HEAD. No workflow triggers on the A branch; push ran nothing.
- FORGE_PIN `8c7e9afb8e6caee88644b94e25da5852e36f8928` re-verified by full clone + checkout.

## Immutable route input (DIRECTLY_VERIFIED)

- RUN `34063748962` / ARTIFACT `9998291348` / SOURCE `48cb9a018f606f1209d14ee587a6ff3f14d263a1`.
- Metadata digest/run/sha match; downloaded ZIP digest `sha256:6465…f9d0e9` PASS; ZIP CRC PASS (6138 entries);
  root SHA256SUMS PASS; route GATE predicate PASS (26/8/1/2/17/27, overlap 0, no legality inference).
- `a-rest-svar-af8.tsv`: exact 8/8 expected paths, 19-col ABI, ABILITY roots, flags 1/0/1/1, Quinjet absent.
- Case anatomy (from artifact, card-name-free repair grounding): 7 Charm + 1 ChangeZone dispatches;
  7 ChangeZone-to-Hand targets; 1 Pump/Fear TargetMax-X target on the sole `Announce$ X` parent.

## Repairs (A-owned surface only; shared overlays consumed unchanged)

1. Workflow overlay wiring (`.github/workflows/ws33-abc-a-rest-svar-af8-runtime.yml`): added
   `stack-resolution-reachability` + `a-rest-play-stage-observer` + `mana-cancel-boundary` after
   `svar-reachability` (Direct31 v2 position/v5 order; SVar observation preserved), with PASS/rail
   gates mirroring v2/v5, trigger paths, both unit-test modules, new evidence file assertions/comparisons,
   new hardener marker greps, and adjudicator-flag predicate
   (`identity_bound_evidence_required`, `forced_selection_classification_required`).
2. Hardener (`ws33_harden_a_rest_svar_af8_runtime.py`): positive-X branch is scoped to the
   true authoritative X-announcement kind `GUI_GET_INTEGER` (Forge pin, verified in source and
   at runtime: `announceValuesLikeX -> announceRequirements -> getGui().getInteger`, because
   `Cost.isMandatory` is false for ordinary casts — only PlayEffect/Discover free casts set
   mandatory and reach `chooseNumber`/`NUMBER`). An initial `NUMBER` gate was corrected after
   the local Record proved the real kind. `NUMBER`/other numeric requests keep generic handling.
   Added per-path source-card/root-ability/actor binding, per-target before-zone/keyword capture
   (pre-`effect.resolve`) and after-zone/keyword assertion (exact Hand movement; observed keyword),
   `AF8_TARGET_EVIDENCE.tsv` (13 col) and `AF8_SELECTION_WITNESS.tsv` (12 col, entity-backed rows
   carry counts only, discrete semantics per-item Base64) exports, forced(empty-vs-single-option
   aware)/non-discretionary classification.
3. Adapter (`ws33_adapt_g_svar_af_harness_to_a_af8.py`): MODE branch witnesses
   `SOURCE_PROVEN_DESIRED_PLUS_MINIMUM` selection.
4. Adjudicator (`ws33_adjudicate_a_rest_svar_af8.py`): new target-detail gate (exact movement,
   keyword-gained, creature-gain for Creature-restricted scripts, single source/root/actor chain,
   child presence, duplicate/foreign rejection, record-vs-replay multiset equality), selection gate
   (schema, principal scope actor==principal, cardinality, unknown-basis rejection, forced
   recomputation via binomial legal-selection count, X-positive-NUMBER rule, Charm MODE
   selected==max(1,min) rule, replay equality), play-stage success gate (dispatch-API success row,
   `PLAY_ABILITY_TRUE` + `PREREQUISITES_MET` true, terminal-false rejection) replacing counts-only.
5. Tests (`test_ws33_adjudicate_a_rest_svar_af8.py`, new): 24 fixture-based tests (PASS baseline + 23
   focused negatives covering every new rule).

## Local gates (all green)

- Route/ABI/case-set: PASS (above).
- `py_compile` on all touched scripts + both test modules: PASS. Workflow YAML parse (17 steps): PASS.
- Unit tests: 36/36 OK (12 parser + 24 adjudicator).
- Full Python harness chain dry run on real WS31 source: PASS with all markers; workflow harness
  greps (required + forbidden incl. `! prepareSourceParentChoices(spec,sa)`,
  `! getStack().addAndUnfreeze(sa)`) verified against output.
- Overlay validation against pin-fetched Forge files: svar/stack-resolution PASS twice byte-identical;
  no earlier-stack script touches MagicStack/PlaySpellAbility/AbilitySub (WS01 patch file list +
  patcher grep); play-stage PlaySpellAbility hunk applies cleanly post-stack-resolution;
  play-stage InputPayMana hunk + mana-cancel rail=TRACED established by Direct31 v6 PASS artifact
  on the same pin (prerequisite: WS01 mana-convoke bridge, preserved order); ws12+ws32 apply cleanly
  incl. post-stack-resolution MagicStack anchors.
- Full Forge pin clone: all hardener-referenced Java symbols verified
  (`GameEntity.getId`, `SpellAbility.getId`, `Card.getZone/getType/isCreature/hasKeyword(String)/isInZone`,
  `ZoneType.smartValueOf`, `ExternalDecisionRequest.getActorId/getPrincipalId`, `Option` accessors).
- Real overlay stack applied to full pin tree in exact workflow order: all PASS markers + v5 gates green.
- Generated harness `test-compile` green (`Ws33ARestSVarAf8QualificationTest` + inner classes built).
- Java brace/paren/bracket balance on generated harness: balanced; witness call sites 3/3.

## In flight / next

- Local bounded Record with real AF8 cases on the replica (`/tmp/af8-local`): 7/8 PASS with exact
  Graveyard/Battlefield-to-Hand movement, identity chains, MODE witnesses and zero leaks.
  Profane Command (`fa2b8db7`) FAILs closed with
  `UNSUPPORTED_DECISION_PATH: GUI_GET_INTEGER: integer range is not a bounded exact option set`:
  its X range is `[0, Integer.MAX_VALUE]` (no XMax/AnnounceMax/targeting cap in the source-proven
  script; `CostPart.getMaxAmountX` returns null for mana X), and the shared WS01 adapter refuses
  to externalize unbounded integer ranges BEFORE any pilot policy can engage. Bounding X policy
  (e.g., affordability-capped enumeration or a dedicated X-range request type) is a shared
  WS01 decision/runtime semantic change and therefore OUTSIDE A ownership: coordinator approval
  required. No A-owned workaround exists that is not outcome injection (setting X in-harness),
  rules mutation (XMin/XMax/AnnounceMax), or shared-semantics change (adapter bound). The seven
  passing paths' evidence is preserved unaffected.
- A witness-delimiter defect found by the local run (literal `\t` in `AF8_SELECTION_WITNESS.tsv`
  from a doubled escape in the hardener raw string) was fixed and is being re-validated by a
  second local Record/Replay before any remote dispatch.
- EXACT NEXT ACTION: confirm second local Record/Replay (expect 7 PASS + 1 shared-boundary
  FAIL_CLOSED), commit + push the kind/delimiter corrections, freeze source at the new HEAD,
  dispatch `ws33-abc-a-rest-svar-af8-runtime.yml` on the A branch via `workflow_dispatch`,
  persist PENDING checkpoint with RUN/JOB/artifact binding, then download + adjudicate with the
  new adjudicator. The remote run is expected to reproduce 7/8 PASS with Profane FAIL_CLOSED on
  the documented shared WS01 boundary; present that as the adjudication question, not as an
  A-harness defect.

`TURN_STATUS=INTERRUPTED`. `TASK_COMPLETE=NO`.
