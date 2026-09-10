# WS33D Q6 historical impact gate — detached-controller hiding vs D-family PASS evidence

Date: 2026-09-10. Branch: `work/ws33-d-high-throughput-20260907`.
HEAD=`925545b97cb1bb57b723b8c890ea703d7ce2c561`,
TREE=`400208106b30c25ccd513456b12c0f8c1cfe7e09` (terminal D4c FAIL-CLOSED state).
TYPE=ANALYSIS_ONLY. No source changed, no run registered, no rerun performed,
no coverage promotion. COVERAGE_PROMOTION=FALSE.

## Trigger (why this gate exists)

D4c proved two facts about the inherited D-family harness wiring
(`PlayerControllerHuman` constructed but never registered; engine consults
registered AI controllers; `PlaySpellAbility` targeting/payment route via
`p.getController()`):
1. Run 34426307199: TARGET_SELECTION never reached a detached provider
   (zero `decision-requests.jsonl`); registered AI answered invisibly.
2. Run 34432378875: under registered wiring, mana payment surfaces as
   MANA_PAYMENT — i.e. casts that looked "decision-free" under detached
   wiring can contain a genuine native payment choice.
Hence every retained PASS that relied on "zero requests reached provider"
must be re-adjudicated per-PASS, not invalidated wholesale.

## Method (DIRECTLY_VERIFIED, immutable inputs)

- All 5 D-family PASS artifacts re-downloaded; ZIP sha256 reproduced equal
  to the checkpoint-recorded digests (D1 `4d840fcc…`, D2 `aa5f031e…`,
  D3 `0e598b09…`, D4a `53b58d09…`, D4b `885ed04b…`). Historical artifacts
  treated as immutable inputs.
- Per-case `decision-requests.jsonl` presence/content inventoried;
  diagnostics confirmed 0 bytes; success markers counted (10/8/7/8/3).
- All 5 PASS harnesses read at their exact PASS SHAs: none calls
  `dangerouslySetController` — all providers were attached to explicitly
  passed-but-unregistered controllers. Casts/activations go through
  production `PlaySpellAbility.playSpellAbility(controller, …)`.
- Key routing distinction (code-derived at PASS SHAs + pin-evidenced by
  D4c): resolution-time ENTITY_LIST_SELECTION / CONFIRM_PAYMENT are issued
  to the explicitly-passed controller object (observed even when
  detached); TARGET_SELECTION / MANA_PAYMENT route via the registered
  controller (invisible under detached wiring). Artifact logs confirm
  exactly this split: every observed request is ENTITY_LIST_SELECTION or
  CONFIRM_PAYMENT; zero TARGET_SELECTION/MANA_PAYMENT anywhere.
- Fixture forcing checked per flagged path from frozen case TSVs
  (pool specs, zones, life) + pin-read card survey
  (`WS33D_D4_SHAPE_SURVEY_20260909.md`) + record assertions.

## Per-PASS verdicts

### D1 lifegain, run 34348893940 (10 paths) — NO_IMPACT

- Q1 (native decisions expected?): YES for 6 (4 ENTITY forced-selection,
  2 CONFIRM_TRUE payment-affirm); NO for 4 NONE (automatic lifegain).
- Q2 (observed?): all 6 expected decisions OBSERVED: 6 record dirs carry
  `decision-requests.jsonl` (ENTITY sole `ENTITY:card:N` + disallowed
  CANCEL companion; CONFIRM `{true,false}` affirmed true), each with
  identical record+replay lines (replay re-issued, tape matched).
  Sac/discard costs all sole-option by fixture (Plains:1, Bear:1,
  Bear-in-hand:1, self) — forced, and the selections were transported,
  not assumed.
- Q3 (independent proof?): 4 NONE paths: vacuous tapes + exact pools
  (W4, W2C4, W3 — single-composition, fixed costs, no kicker/X/Compleated/
  targets in set) + life/zone/pool assertions + replay divergence 0.
  Angel's Mercy/Timely/Avenge/Cloudblazer involve no legal alternative
  act. Opponents bare or bodies-only (Avenge opp 1 Bear, no hand/mana).
- No TARGET/MANA surface existed on these paths (targetless spells,
  exact pools); nothing was hidden that should have surfaced.

### D2 lifelose, run 34373666283 (8 paths) — 7 NO_IMPACT + 1 TARGETED_REQUALIFICATION_REQUIRED

- 7 paths NO_IMPACT: Urborg Syphon-Mage ENTITY sole-discard OBSERVED via
  transported log (replay-matched); Night's Whisper / Circle of Power
  fixed costs from exact pools; Painful Truths converge FORCED by exact
  pool composition (W1B1C1 fully spent → colors WB = 2, single payment
  route); Caustic Hound / Grave Venerations mandatory dies-triggers via
  exact Wrath pool; Shimmercreep state-count ETB (no announcement).
- 1 path TARGETED_REQUALIFICATION_REQUIRED (narrow scope):
  `2daa72d1` Vraska, Betrayal's Sting (PLANESWALKER_DRAW_LOSE, pool B2C4,
  intent NONE, 0 requests). The Compleated `{B/P}` payment was made as B
  with no prompt, answered invisibly by the registered AI. A Compleated
  symbol is a genuine 2-option native payment choice (B vs 2 life); under
  registered wiring it is expected to surface as MANA_PAYMENT (proven for
  mana payment by run 34432378875). Q1 YES / Q2 registered-AI-invisible /
  Q3 split: the lifelose EFFECT (loyalty-ability draw+lose) is proven
  independently (life/loyalty/pool assertions, replay divergence 0,
  "no life" pins the payment outcome), but the payment CHOICE itself is
  outcome-pinned only, never transported.
- Disposition: effect evidence RETAINED as supporting (not demoted, not
  double-counted); the payment leg is queued for targeted re-transport
  under future authority with a payment-choice intent (no run authorized
  by this gate). D-local count stays 36 / 884 with this limitation noted.

### D3 damageall, run 34380960438 (7 paths) — NO_IMPACT

- Q1: NO for all 7 (all NONE-intent by design). Q2: confirmed — zero
  `decision-requests.jsonl` in the artifact, vacuous tapes, diagnostics
  empty; provider would have thrown fail-closed on ANY request.
- Q3: X values state-defined, not announced (Chain Reaction X = 3
  battlefield creatures; Volcanic Torrent X = 1 GY instant/sorcery
  self-count — both proven by kill/survival assertions incl. flying
  exclusion and SBA-to-GY legs); Divination/Concentrate fixture draws
  choiceless; Wrath/Seismic pools exact; cascade-free (no library
  fixture, nothing to find); triggers mandatory and sequential;
  opponents bodies-only. Replay divergence 0.

### D4a staticeffect, run 34411858516 (8 paths) — NO_IMPACT

- Q1/Q2: all 8 NONE-intent; zero request logs; fail-closed provider would
  have thrown on any prompt (diagnostics empty ⟹ no prompt reached the
  passed controller; registered-AI surfaces covered by forcing below).
- Q3 per flagged path (all others automatic/static with exact pools):
  Unstable Footing kicker UNAFFORDABLE by fixture economics (pool R1 vs
  kicked cost) — forced skip; Burning Curiosity blight additional cost
  UNPAYABLE (no creatures in fixture) — forced unpaid → exile-2 asserted,
  MayPlay-exiled permission unexercised in-run (life 0-deltas, exile-two
  pinned, static present); Hildibrand dies trigger has NO OptionalDecider
  at pin (mandatory; MayPlay is a granted STPlay permission, D6 business,
  not a runtime choice); Seaweed deaths SEQUENTIAL single-trigger steps
  (Bear→Seismic, Hawk→trigger; no simultaneous-trigger ordering choice);
  Leitmotif sole activated ability, exact pool U1C2; Gideon +0-loyalty
  animate fixed, 1-spare-C pool (leftover ≠ choice); Silence opponent
  locked by engine CantBeCast with hand/pool outcome asserted
  (probe-baseline GY + rejected hand — engine-automatic rejection, no
  choice for anyone; only opponent in the corpus holding cards+mana).
- This closes the optional-cost/trigger prompt audit queued in the
  34426307199 FAIL checkpoint: no such prompt existed on any D4a path.

### D4b emblem, run 34419391829 (3 paths) — NO_IMPACT

- Q1/Q2: all NONE-intent; zero request logs; diagnostics empty.
- Q3: ultimates are the SOLE ApiType.Effect loyalty abilities (fixed
  selection); loyalty-cost payment engine-enforced from counter state
  (exact, unshortable); entry-doubling (printed 4 → 8) engine-owned via
  Doubling Season bridge with fail-closed entry gate; emblem triggers
  automatic (payload presence asserted); Elspeth static proven by Wrath
  consequence + engine SBA (loyalty-0 GY); pools exactly cover
  cast+enabler+fixture lines; opponents bare.

### D4c — no retained PASS (terminal FAIL CLOSED, runs 34426307199 / 34429297453 / 34432378875). Unaffected by this gate; nothing to requalify.

## Rolled-up record (skill fields)

- OLD_SOURCE_LOCK=`925545b97c` (unchanged — analysis only, no new lock).
- CHANGED_PATHS: none. CHANGE_CLASS: EPISTEMIC (new harness-understanding
  from D4c applied to historical evidence; zero semantic/build/observation
  surface change).
- AFFECTED_GATES: none invalidated. D-local evidence stays 36 / 884 with
  one scoped limitation (Vraska payment leg).
- UNAFFECTED_GATES: D1/D3/D4a/D4b PASS gates + D2 gate for 7/8 paths.
- REQUIRED_RERUNS: NONE now (this gate authorizes no execution; "do not
  rerun unaffected evidence" honored — nothing rerun). QUEUED (future
  authority only): 1 targeted payment-leg re-transport for Vraska
  `2daa72d1` under registered wiring with a payment-choice intent.
- UNKNOWN: 0. Every retained path adjudicated on positive evidence
  (transported logs + replay match, or fixture-forcing + state assertions
  + empty diagnostics + divergence 0). No wholesale invalidation.
- VERDICT: D-family retained PASS evidence SURVIVES with the single noted
  limitation. ARCHITECTURE_FREEZE = NOT CLAIMED. PRODUCTION_PROVIDER =
  NOT SELECTED. No D4d/D4e/D4f, Batch-6, or Full107 started.

## Exact next action

Coordinator decision on the queued Vraska payment-leg re-transport (new
workstream, registered wiring, payment-choice intent; effect evidence
stands). Otherwise D-workstream remains: D4c FAIL CLOSED, D1–D4b retained
per this gate.
