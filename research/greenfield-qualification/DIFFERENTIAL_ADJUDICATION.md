# Differential Rules Adjudication — WS09

Status: **PASS**  
Q7_DIFFERENTIAL: **PASS**  
Qualification source: `636e0b558d9b1a3c4ea5495c2b489c032960c430` / tree `619f465211b355a48ba0e67b2c6d628c4c596253`  
Qualification run: `33246123537`  
Qualification artifact: `9712936171` (`sha256:44b106695591afb1853d7d11273466c093c95fb7f67aabdce9df3937fe6501ff`)

## Contracts

- Common initial semantic state: PASS.
- Common Decision Tape: PASS; selected scenarios require no discretionary decisions (`[]`).
- Common RNG Tape: PASS; selected scenarios require no RNG (`[]`).
- Canonical trace normalization: PASS.
- First meaningful divergence is recorded by contract; no meaningful divergence occurred for the supported engine pair.
- Engine majority was not used as rules authority.

## Selected shared scenarios

1. `S01_3P_PLAYER_COUNT`: canonical `PLAYER_COUNT=3`.
2. `S02_3P_STARTING_LIFE`: canonical `STARTING_LIFE=40` for P1/P2/P3.

Forge evidence is reused from completed WS07 run `33244368567`, artifact `9712369379`, exact Forge pin `8c7e9afb8e6caee88644b94e25da5852e36f8928`; WS07 was not rerun. XMage is freshly witnessed at exact pin `86d86b580cd7e1f30b51110d70cecae18c1ce452` with one targeted JUnit test against the constructed engine state before `Game.start()`, so no gameplay decisions, shuffles, or RNG enter the common-state boundary.

`phase.rs` and Manabrew are `UNSUPPORTED` for these exact WS09 common constructed-state scenarios because no exact-pin WS09 adapter exists. They remain `UNKNOWN` rather than being promoted to parity.

## Official adjudication

Wizards of the Coast's Commander format page was checked live on 2026-08-29 and the workflow captured a source witness (`sha256:ff767a7c75912274688f3f704da336c352e8d39dac710161954d8f3dd6acc7cb`) confirming 3–5 players and 40 starting life. This is the rules authority for the two selected facts, not engine voting.

## Failure history

Run `33245842856` failed closed because the initial XMage witness incorrectly read a player's pre-start life field, which is `0` before XMage applies the configured starting life during `Game.start()`. The correction did not mutate player state or start a randomized game; instead it witnesses XMage's authoritative configured `startingLife=40` and normalizes that native representation to the same semantic `STARTING_LIFE` event. The corrected qualification run passed all hard gates.

## Gate result

- `common_initial_state_contract = PASS`
- `common_decision_contract = PASS`
- `common_rng_contract = PASS`
- `canonical_trace_contract = PASS`
- `selected_shared_scenarios_executed = true`
- `unadjudicated_meaningful_divergences = 0`
- `majority_vote_used_as_rules_authority = false`
- `Q7_DIFFERENTIAL = PASS`
