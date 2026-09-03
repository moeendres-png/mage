# WS33 G3 AF Principal Observation v4 — root-cause reconstruction correction

Status: `CORRECTION_PERSISTED`

Evidence classification: `DIRECTLY_VERIFIED` against current branch source and downloaded artifact `9893663522`.

This checkpoint supersedes two reconstructed details in `G3_AF_PRINCIPAL_OBSERVATION_RECORD_ROOT_CAUSE_33756098495.md`; it does not alter the run-level root cause that the fresh execution was rejected by stale coarse hidden-signal validation.

## Correct current-source facts

1. The current base verifier `ws33_adjudicate_g_principal_observation.py` does **not** contain a pre-existing RevealHand-specific coarse-signal exception. Its current `check_summary()` also requires `int(row[9]) == 0` for every path.
2. The current v4 wrapper repeats the same all-zero requirement in its ABI-aware `check_summary_v4()` override.
3. Therefore the contradiction is between the new principal-observation lifecycle evidence and both current summary validators, not between a special-casing base validator and the v4 wrapper.

The repair will remain v4-scoped/default-preserving so already-qualified Direct-G behavior is not silently reinterpreted.

## Correct downloaded observation facts

The actual `record/PRINCIPAL_OBSERVATIONS.jsonl` from artifact `9893663522` contains `504` events using the schema:

`sequence, path_id, kind, principal_id, card_id, decision_kind, identity_match`

For the sole path with positive coarse row-9 signal:

`forge-behavior-v2:17f8532940a8967b06c70c70431c410d86c56c19 / ChoosePlayer / RevealHandEffect`

there are `28` principal-observation events covering seven cards for principal `1`. Every card stream is exactly:

`SERVER_GRANT -> CLIENT_VISIBLE -> SERVER_REVOKE -> CLIENT_HIDDEN`

Counts for that path are therefore:

- `SERVER_GRANT = 7`
- `CLIENT_VISIBLE = 7`
- `SERVER_REVOKE = 7`
- `CLIENT_HIDDEN = 7`
- `identity_match = true` for all events

The earlier reconstructed `16 events / two principals / two cards` detail is not part of this artifact and is withdrawn.

## Summary-row facts

Exactly one of the 21 record summary rows has a non-zero coarse field:

- path: `forge-behavior-v2:17f8532940a8967b06c70c70431c410d86c56c19`
- dispatch: `ChoosePlayer`
- implementation: `forge.game.ability.effects.RevealHandEffect`
- status: `PASS`
- decision events: `2`
- RNG events: `0`
- coarse hidden signal `row[9]`: `1`
- cross-principal delta `row[10]`: `0`
- runtime failure type/message: empty
- stack admission/resolution: `1/1`
- reachability count: `1`

The AF target consumer for this path is `RevealHand` with `Look$ True`, and the source-profile classifier already identifies `RevealHand` as `POSITIVE_TEMPORARY_REQUIRED`.

## Correct repair contract

The raw row-9 value must remain unchanged. The v4 validator may classify a positive value as an **attested temporary-observation signal** only when all of the following hold for that exact path and run side:

- source profile is `POSITIVE_TEMPORARY_REQUIRED`;
- cross-principal delta is zero;
- principal observation events are present for the exact path;
- every observed `(principal_id, card_id)` stream passes the strict `SERVER_GRANT -> CLIENT_VISIBLE -> SERVER_REVOKE -> CLIENT_HIDDEN` state machine;
- identity comparison is true for every event;
- positive observation/grant evidence is present;
- record and replay observation multisets remain deterministic.

A positive coarse signal on a negative/transition-only or unknown profile remains fail-closed. Missing/incomplete lifecycle evidence remains fail-closed. This is classification, not suppression or a path-id-only waiver.

## Serial boundary

No rerun has been started. Next step remains: implement this v4-scoped contract, add deterministic regression tests, persist the repair, then dispatch the focused AF gate.

`WS33_COMPLETE = FALSE`

`TASK_COMPLETE = NO`
