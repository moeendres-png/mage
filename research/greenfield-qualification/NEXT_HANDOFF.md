# Commander Simulator Next — Next Dependency Wave After WS91

Date: 2026-08-29

## Entry state

```text
WS91_WORKSTREAM_COMPLETE              = TRUE
INITIAL_ARCHITECTURE_DECISION_FROZEN = FALSE
READY_FOR_GREENFIELD_BUILD           = FALSE
WS13_ELIGIBLE                        = FALSE
Q6_ACTUAL_CARD_BEHAVIOR              = FAIL_CLOSED
FAILURE_SEMANTICS                    = FAIL_CLOSED
Q8                                    = DEFERRED
```

Do not create `moeendres-png/commander-simulator-next`.

## Canonical retained runtime anchor

- WS90 qualified runtime head/tree: `55820618e7243bd5ba8cfa33c3148cea8c166c73` / `3706900d49c6ef61690c227bb7b4c0067fbcfb44`.
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`.
- Q1–Q5 remain PASS within their previously qualified boundaries and were not rerun because WS14–WS25 did not invalidate those runtime paths.
- Q7 remains PASS only within its recorded scope and was not rerun.

## Blocker A — Q6 actual-card semantic behavior

Canonical successor gate: WS24.

Verified result:

```text
identity_count             = 1678
primitive_count            = 174
primitive_pass             = 13
primitive_partial          = 161
unresolved_binding_count   = 1800
Q6_ACTUAL_CARD_BEHAVIOR    = FAIL_CLOSED
```

The 13 PASS primitives are genuine exact-pinned Forge state witnesses from WS16 and WS17. They do not justify extrapolation to the remaining 161 primitives or to the 1,800 unresolved WS14 source bindings.

### Exact next evidence

1. Resolve the remaining WS14 source-to-primitive bindings systemically. Do not use card-name exception tables or fuzzy semantic promotion.
2. Execute each remaining production-required atomic behavior path against Forge `8c7e9afb8e6caee88644b94e25da5852e36f8928`.
3. Each PASS witness must exercise the actual primitive, assert initial/final engine state, retain immutable trace evidence, set `stdout_only=false`, and retain authoritative decision/RNG tapes where applicable.
4. External pilots may select only from Rules-Core-generated legal options; a test driver may not become a second rules engine.
5. Q2/Q3 success remains prerequisite evidence only and may not be inherited as per-card behavior PASS.
6. Re-run WS24 integration only after new witness/binding evidence changes its inputs.

## Blocker B — production `CARD_BEHAVIOR_FAILURE`

Canonical successor gate: WS25.

Verified result:

```text
failure_category_count                         = 16
production_reachable_untyped_failure_outcomes = 1
unbound_category                               = CARD_BEHAVIOR_FAILURE
qualifier_detector                             = PASS
production_runtime_binding                     = UNKNOWN
FAILURE_SEMANTICS                              = FAIL_CLOSED
```

### Exact next evidence

Bind a real production-runtime card-behavior semantic verifier/capture path. At that actual path:

1. induce a controlled semantic mismatch after successful engine execution;
2. emit authoritative `CARD_BEHAVIOR_FAILURE` rather than `ENGINE_FAILURE`, cancel, pass, default, first, random, or silent skip;
3. prove `state_committed=false` for the failed semantic result;
4. prove prohibited fallback behavior is absent;
5. prove the public failure payload does not disclose private semantic values;
6. re-run WS25 integration only after this production binding exists.

## Requalification policy

Do not rerun Q1–Q5 or Q7 merely because these blocker workstreams execute. Requalify a predecessor only if the implemented fix changes its pinned source, runtime contract, detector, process topology, decision boundary, observation boundary, RNG/replay boundary, Commander path, or differential adapter in a way that can invalidate the prior evidence.

## WS13 gate

WS13 must **not** start yet. The exact entry condition remains:

```text
Q6_ACTUAL_CARD_BEHAVIOR = PASS
AND
FAILURE_SEMANTICS = PASS
```

Only after both conditions hold in one compatible candidate runtime topology may a subsequent integration workstream issue the concrete topology required for architecture-specific license adjudication.
