# Commander Simulator Next — Next Handoff

Date: 2026-08-28

## Entry state

```text
INITIAL_ARCHITECTURE_DECISION_FROZEN = FALSE
FIRST_BLOCKING_GATE = DECISION_EXTERNALIZATION
FIRST_BLOCKING_SUBGATE = FULL_DECISION_CENSUS_AND_TYPED_CALLBACK_COVERAGE
```

Do not create `moeendres-png/commander-simulator-next`. Do not use the old
Commander-Lab checkout as a Rules Core source.

## Exact current evidence

- Qualification revision/tree: `34036a2d6704c0b70c0a59d071bc938870db0c2b` /
  `33e3968b35fc5cd2967f12d8f57c4b7ebab2d21f`.
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`.
- Strict patch SHA-256: `42ff6d7301287af90b3c5b1ba9d809d78f19018d80f4a8ba5b0eeacad0d1e581`.
- Current strict gate: run `33152614647`, artifact `9678342430`, gate `FAIL`.
- Current hidden-transport assay: run `33152614611`, artifact `9678348191`,
  0 decoded identity leaks in the scoped 2P test.
- Current replay failure: run `33152614679`, artifact `9678412031`, missing
  canonical state/RNG/decision streams in all three fresh processes.

## Completed without repeating historical work

1. Robust Scryfall gzip/plain ingest, deterministic Oracle dedup, and
   upstream count 38,626.
2. Fail-closed 1,721-union materializer; it remains `NOT_RUN` at 0/1,721
   because materialized Oracle-ID inputs are absent.
3. Typed server-side Forge entity selection plus a server-mapped discrete
   facade, with explicit negative-response validation and no
   GUI/AI/first/random/default/pass/cancel fallback. The facade remains
   static/compile-only and is not runtime-qualified.
4. Current static census: 109 controller callbacks, 15 blocking GUI decisions,
   3 directly exported, 106 remaining.
5. Versioned Decision/RNG/State/Tape schemas, semantic replay validator, A–T,
   C01–C22, card-coverage, differential, isolation, and license artifacts.
6. Per-client hidden-card redaction in full state, deltas, events, and
   visibility transitions; current raw decoded transport name-leak count is 0.
7. Current 2P–5P CLI probe executions, including a successful 4P CLI probe;
   these are not semantic replay or Decision-Tape evidence.

## Required next work — no substitutions allowed

1. Replace the remaining 106 callback paths and 15 blocking GUI decision
   paths with typed server-owned requests, or prove a path is structurally
   non-discretionary and unreachable in the bounded 2P–5P Commander scope.
   A generic `UNSUPPORTED_DECISION_PATH` is a fail-closed diagnostic, not
   production coverage.
2. Emit runtime DecisionRequest/DecisionEvent records for every open decision
   and test valid, stale, foreign actor/principal, malformed, missing,
   timeout, illegal-option, and one-shot responses under real 4P gameplay.
3. Extend the hidden-information campaign to 4P and cover principal-scoped
   observations, raw bytes/metadata, logs, exceptions, IDs/hashes, replay,
   debug output, and reveal/look lifecycle. Require zero leaks across every
   surface.
4. Replace global/random bypasses with named game-scoped RNG streams and emit
   an event tape plus canonical state digests. Reproduce one 4P trajectory in
   three fresh processes without using stdout/stderr/timestamps as criteria.
5. Obtain materialized source Oracle IDs for the exact 1,721 requirement
   union. Do not map names, invent identities, or promote unknown cards.
6. Execute A–T and C01–C22 plus behavior coverage through the strict boundary,
   then conduct first-divergence adjudication against XMage and phase.rs.
7. Complete process-isolation and license/distribution gates. Only then may an
   ADR/scorecard be frozen and the private production repository be created.

## Guardrails

Google Drive is read-only. No deck, inventory, purchase, allocation, or
Playtest-Lab state may change. Historical results are context only, never
current-head proof.
