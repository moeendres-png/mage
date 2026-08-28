# Commander Simulator Next — Current Qualification Status

Date: 2026-08-28

## Verdict

```text
INITIAL_ARCHITECTURE_DECISION_FROZEN = FALSE
READY_FOR_GREENFIELD_BUILD          = FALSE
READY_FOR_TRUSTED_REAL_DECK_SIMULATION = FALSE
PRODUCTION_REPOSITORY_CREATED       = FALSE
```

The research-only qualification increment is current through revision
`34036a2d6704c0b70c0a59d071bc938870db0c2b`. The affected strict-boundary,
hidden-transport, census/RNG, and runtime workflows were all rerun at that
exact revision; no historical run is used as proof for it.
`REMOTE_QUALIFICATION_EVIDENCE.json` records the current remote artifacts and
their SHA-256 values.

## Provenance

- Research branch: `research/greenfield-engine-shootout-20260827`.
- Current qualification revision/tree: `34036a2d6704c0b70c0a59d071bc938870db0c2b` /
  `33e3968b35fc5cd2967f12d8f57c4b7ebab2d21f`.
- Starting research input retained for traceability: `7f843a29808c086f960128585b49bb18a7ec381a` /
  `c7c570a7e88bc7b4d0cced2d9ef88aed5fd9528e`.
- Exact Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`.
- Strict patch SHA-256 as applied in remote qualification:
  `42ff6d7301287af90b3c5b1ba9d809d78f19018d80f4a8ba5b0eeacad0d1e581`.

## Qualification gates

| Gate | Current result | Current evidence boundary |
|---|---|---|
| Q0 provenance/schemas | PASS locally | versioned schemas, exact source/pin fields, 24 local Python tests |
| Q1 typed decision externalization | FAIL | remote strict run `33152614647`: entity seam and server-mapped discrete facade compile; only 3/109 direct controller routes, 15 blocking GUI paths and runtime Decision-Tape remain unqualified |
| Q2 hidden information | FAIL / insufficient evidence | remote 2P decoded-transport assay `33152614611`: 0 hidden identity names; required 4P multi-surface red team remains incomplete |
| Q3 RNG/replay | NOT_RUN | remote runtime run `33152614679` repeats 2P–5P/RogShai probes but lacks `states`, `rng_events`, and `decision_tape` streams; raw logs excluded |
| Q4 process isolation | INSUFFICIENT_EVIDENCE | no selected production core with isolated queues, IDs, observations, and RNGs qualified |
| Q5 Commander/multiplayer | INCOMPLETE | current CLI probes exit successfully for 2P–5P (including 4P), but no semantic/decision evidence or A–T/C01–C22 behavior closure exists |
| Q6 actual-card coverage | INSUFFICIENT_EVIDENCE | Scryfall upstream index 38,626 PASS; project requirement union remains 0/1,721 because source descriptors contain no Oracle IDs |
| Q7 differential adjudication | INCOMPLETE | no common explicit action/RNG/decision tape campaign against XMage/phase.rs |
| Q8 license/third-party boundary | DEFERRED | licenses documented; no production linkage/distribution decision is authorized |

## Implemented and requalified work

The strict Forge patch provides a typed, server-owned entity-selection seam and
an experimental server-mapped discrete-choice facade: authoritative
Player/Card/entity or opaque server-mapped option IDs,
actor/principal/visibility scope, min/max/constraints/schema/context,
monotonic tokens, validation, one-shot consumption, and atomic application.
Invalid, stale, malformed, foreign, illegal, missing, timeout, GUI, legacy,
and unknown paths fail explicitly. The facade is static/compile evidence only,
not a runtime Decision-Tape qualification.

The current requalification also corrected the concrete hidden-information
leak. Per-client redaction now applies to full GameView serialization, delta
maps, wrapped events, and visibility transitions. The scoped red-team result
is zero leaked names; it is not promoted beyond that test scope.

## First blocking gate and handoff

```text
DECISION_EXTERNALIZATION
  -> FULL_DECISION_CENSUS_AND_TYPED_CALLBACK_COVERAGE = FAIL
```

No deck, inventory, allocation, purchase, opponent-data, Drive, or
Commander-Lab Rules-Core state was changed. The next non-redundant work is in
`NEXT_HANDOFF.md`.
