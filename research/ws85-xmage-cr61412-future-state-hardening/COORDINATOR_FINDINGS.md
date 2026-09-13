# WS85 Coordinator Findings (reproduced, not re-adjudicated)

Accepted WS83 evidence (taken as given):

- WS83 root-cause location: ContinuousEffects.getApplicableReplacementEffects.
- WS81 pre-fix: A FAIL, B PASS, C PASS.
- WS83 runtime on ffefc195: A PASS, B PASS, C PASS.
- WS83 systemic actual-card tests: PASS.
- Clone/Humility/Vesuva/Phantasmal Image regressions: PASS.
- CARD_NAME_HACKS: 0. SECOND_RULES_ENGINE: 0 (as claimed by WS83's test/evidence design).

Successor status:

- WS83_TECHNICAL_SUCCESSOR_ACCEPTED = NO (reason: implementation safety and claim scope).

Material defect 1 — live game mutation (reproduced DIRECTLY_VERIFIED in WS85):

- The WS83 helper obtained the real entering Permanent, called
  game.getBattlefield().addPermanent(entering), invoked active layer-6
  remover.apply(...) against the real Game, restored only the entering
  permanent's ability list, and removed the entering permanent afterward.
- WS85 sentinel evidence: the entering object was observed simultaneously tracked
  as entering AND a live battlefield member during the probe in P0/P1
  (dual-presence flag set; stack-frame classification viaProbe=true for every
  observation). HumilityEffect.apply-style global loops therefore ran against live
  state with only entering-local restoration.
- Violates the architectural requirement for non-mutating applicability evaluation.

Material defect 2 — silent failure fallback (reproduced DIRECTLY_VERIFIED in WS85):

- The helper caught evaluation exceptions and returned false (allow replacement =
  old behavior).
- WS85 F1 on WS83 code: with the failure seam armed (unread by old code), the run
  completed without explicit failure and reached the old forbidden Clone copy
  prompt (Missing CHOICE under strict mode), carrying no failure marker.
- Violates explicit fail-closed-not-silent semantics.

Material defect 3 — claim scope (corrected in WS85):

- WS83 implemented pre-existing layer-6 Outcome.LoseAbility removal of the source
  ability only. That is a bounded subset, not a full general CR 614.12
  future-state engine.
- WS85 binds the technical claim to exactly the implemented subset
  (CR61412_LAYER6_ABILITY_REMOVAL_SUPPORT) and records FULL_CR61412_FUTURE_STATE_SUPPORT
  as UNKNOWN, never PASS.
