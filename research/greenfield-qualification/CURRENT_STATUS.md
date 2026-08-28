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
`0ea93d09d80e5c126eccb3323b17f14542e5559a`. No historical run is used as
proof for that revision. `REMOTE_QUALIFICATION_EVIDENCE.json` records the
current remote artifacts and their SHA-256 values.

## Provenance

- Research branch: `research/greenfield-engine-shootout-20260827`.
- Current qualification revision/tree: `0ea93d09d80e5c126eccb3323b17f14542e5559a` /
  `64c97a207ad270fa398682c84d8dd238811a8b79`.
- Starting research input retained for traceability: `7f843a29808c086f960128585b49bb18a7ec381a` /
  `c7c570a7e88bc7b4d0cced2d9ef88aed5fd9528e`.
- Exact Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`.
- Strict patch SHA-256 as applied in remote qualification:
  `d783c20c3e43947a84edc4ee2743ac959a5867e71e51b52bd9936f7c85a4cd9b`.

## Qualification gates

| Gate | Current result | Current evidence boundary |
|---|---|---|
| Q0 provenance/schemas | PASS locally | versioned schemas, exact source/pin fields, 23 local Python tests |
| Q1 typed decision externalization | FAIL | remote strict run `33124530375`: 3/109 controller callbacks exported, 106 remain; 15 blocking GUI decisions remain; runtime Decision-Tape absent |
| Q2 hidden information | FAIL / insufficient evidence | remote 2P decoded-transport assay `33124530500`: 0 hidden identity names; required 4P multi-surface red team remains incomplete |
| Q3 RNG/replay | NOT_RUN | current remote runtime run has three fresh processes but lacks `states`, `rng_events`, and `decision_tape` streams; raw logs excluded |
| Q4 process isolation | INSUFFICIENT_EVIDENCE | no selected production core with isolated queues, IDs, observations, and RNGs qualified |
| Q5 Commander/multiplayer | INCOMPLETE | current CLI probes exit successfully for 2P–5P (including 4P), but no semantic/decision evidence or A–T/C01–C22 behavior closure exists |
| Q6 actual-card coverage | INSUFFICIENT_EVIDENCE | Scryfall upstream index 38,626 PASS; project requirement union remains 0/1,721 because source descriptors contain no Oracle IDs |
| Q7 differential adjudication | INCOMPLETE | no common explicit action/RNG/decision tape campaign against XMage/phase.rs |
| Q8 license/third-party boundary | DEFERRED | licenses documented; no production linkage/distribution decision is authorized |

## Implemented and requalified work

The strict Forge patch provides a typed, server-owned entity-selection seam:
authoritative Player/Card/entity option IDs, actor/principal/visibility scope,
min/max/constraints/schema/context, monotonic tokens, validation, one-shot
consumption, and atomic application. Invalid, stale, malformed, foreign,
illegal, missing, timeout, GUI, and legacy paths fail explicitly.

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
