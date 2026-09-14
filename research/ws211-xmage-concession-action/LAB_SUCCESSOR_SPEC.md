# WS211 COMMANDER-LAB SUCCESSOR SPEC (execution-ready, NOT executed in WS211)

Scope: Lab-side only. WS211 does not mutate Commander-Lab. The successor
workstream implements this spec against the WS211 Mage candidate below.

## 1. Inputs (pinned)

- MAGE_CANDIDATE: moeendres-png/mage @ WS211 head (this branch head after
  publication), containing `Game.canConcede(UUID)` and the `Game.concede`
  stale guard. Gating predicate: `research/ws211-xmage-concession-action/
  VALIDATION.json` shows `ws211_total: 20/20 PASS`.
- WS204 architecture (read-only ref 5994019b4da59e27a388eec47e6805404bd98df9):
  `src/commander_lab/models/game.py` — `ActionType.CONCEDE`,
  `LegalAction(action_id, actor_id, action_type, ...)`,
  `ActionProposal(proposal_id, actor_id, legal_action_id, action_type, ...)`;  `src/commander_lab/engine/rules/bridge.py` — `concede(game_id, *,
  player_id)` gated on capability `concede_supported`
  (`models/engine_runtime.py`, default False = current fail-closed block).
- WS205 G04 evidence (read-only ref 1dee8b77f7243900eec5a7cc05fb1fe26467aea9):
  slot `RQ-C3-G04` actual-card/player-rule qualification pattern
  (`qualification/ws205-xmage-ws90-first-wave/`, `ws205_adjudicate.py`
  anti-second-Rules-engine rule). G04 re-runs against the new surface.

## 2. Required Lab behavior

1. **Capability probe**: the XMage client adapter exposes
   `can_concede(game_id, player_id) -> bool` calling engine
   `Game.canConcede`; `concede_supported` becomes True only when the probe
   succeeds against a live WS211 engine (never hard-coded True).
2. **Projection**: `legal_actions(principal)` includes exactly one
   `LegalAction(action_type=CONCEDE, actor_id=principal.player_id,
   ...)` iff `can_concede` is True for that principal. No Lab-side
   `is_alive`-style liveness logic anywhere on the path (delete or gate any
   equivalent; the engine answer is the sole authority).
3. **Binding**: the CONCEDE `LegalAction.actor_id` is the principal's own
   player id. `ActionProposal` for CONCEDE is accepted only when
   `proposal.actor_id == legal_action.actor_id`; proposals naming any other
   actor (notably `getTurnControlledBy()`) are rejected fail-closed.
4. **Submission**: accepted CONCEDE proposals call
   `bridge.concede(game_id, player_id=proposal.actor_id)` — the native
   engine concession request. No Lab-side loss flags, no player removal,
   no direct `leave` invocation.
5. **No second Rules engine**: projection is a pure function of
   `can_concede` + engine state views; no Lab legality model for concession
   (WS205 adjudication rule applies).

## 3. Proof obligations (all must pass)

- `legal_actions` offers CONCEDE exactly when the engine says available
  (positive at game start for an in-game principal; negative for unknown /
  post-game / already-left actors).
- `action_submission` executes native concession (principal leaves, loses).
- 4-player game: conceder leaves; other three continue (game not ended).
- Stale/wrong-actor submissions fail closed (unknown id, already-left id,
  controller id substituted for controlled id — all rejected, state intact).
- No requested-option filtering on the concede path (replay the
  requested set verbatim through submission).
- Rerun G04 actual-card/player-rule qualification with CONCEDE enabled.

## 4. Non-goals

No Mage changes; no WS204/WS205 mutation; no provider selection; no freeze
claim; no behavior credit in the successor beyond its own contract.
BEHAVIOR_CREDIT_CHANGE = 0 carries over.
