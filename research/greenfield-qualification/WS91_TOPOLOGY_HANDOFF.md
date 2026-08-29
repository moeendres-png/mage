# WS91 — Topology Adjudication Handoff

`WS13_ELIGIBLE = FALSE`

`LICENSE_READY_TOPOLOGY_ISSUED = FALSE`

`INITIAL_ARCHITECTURE_DECISION_FROZEN = FALSE`

## Why no WS13 topology is issued

WS91 independently verified the WS24 and WS25 successor evidence and their WS14–WS23 dependency chains. The two mandatory preconditions for an architecture-specific license adjudication are not satisfied simultaneously — or individually:

- `Q6_ACTUAL_CARD_BEHAVIOR = FAIL_CLOSED`
- `FAILURE_SEMANTICS = FAIL_CLOSED`

Therefore WS91 must not manufacture a topology merely to start WS13. Q8 remains deferred and no architecture freeze is authorized.

## Retained technically proven topology constraints

These are constraints inherited from the qualified WS90 runtime and remain valid because WS14–WS25 did not replace the WS90 runtime implementation on the WS91 branch:

- Rules Core implementation pin: Forge `8c7e9afb8e6caee88644b94e25da5852e36f8928`.
- Qualified runtime source anchor: `55820618e7243bd5ba8cfa33c3148cea8c166c73` / tree `3706900d49c6ef61690c227bb7b4c0067fbcfb44`.
- Isolation model: one OS process per game; same-JVM multi-game isolation is not qualified.
- Pilot boundary: external pilots may choose only among authoritative legal decision options; legality remains Rules Core authority.
- Decision boundary: typed external decision requests/responses with fail-closed response validation.
- Observation boundary: principal-scoped observations; private information is not globally exposed to pilots.
- RNG/replay boundary: named RNG capture plus semantic decision/RNG/state replay.
- Primary production path: four-player Commander; technical conformance evidence covers 2P–5P within the recorded WS90/WS07 boundary.

These constraints are **not** a frozen architecture and are insufficient to determine the final IPC/network, packaging, modification/fork, copied/vendored, and deployment/distribution boundaries required by WS13.

## Q6 blocker

The immutable WS24 gate independently hash-verifies:

- Oracle identities: `1678`
- atomic primitives: `174`
- primitive PASS: `13`
- primitive PARTIAL: `161`
- unresolved WS14 source bindings: `1800`
- identity PARTIAL: `664`
- identity UNKNOWN: `1014`
- `q6_pass = false`

The 13 PASS primitives are backed only by WS16 (`2`) and WS17 (`11`) exact-pinned Forge state witnesses. WS16's successful engine-execution artifact was produced before a later packaging step made that first job red; the separate recovery run independently verified that immutable artifact and emitted the WS14-ABI witness. WS17's 11 PASS witnesses all have `execution=PASS`, `stdout_only=false`, exact Forge pin and immutable 64-hex trace hashes.

**Required next evidence:** resolve remaining source-to-primitive bindings systemically and execute every production-required remaining atomic behavior path on the exact Rules Core pin with authoritative legal choices, state assertions, trace hashes, and decision/RNG tapes where relevant. Parsing, source presence, global Q2/Q3 inheritance, or card-name exceptions are not acceptable behavior proof.

## Failure-semantics blocker

The immutable WS25 gate independently hash-verifies all 16 authoritative outcome categories, but exactly one production-reachable category remains unbound:

`CARD_BEHAVIOR_FAILURE`

WS23 proves the semantic mismatch detector only as `QUALIFIER_ONLY`; it does not prove a production-runtime callsite. Therefore:

- `production_reachable_untyped_failure_outcomes = 1`
- observed prohibited fallback count = `0`
- absence of fallback handling on the unbound production card-behavior path = `UNKNOWN`
- `FAILURE_SEMANTICS = FAIL_CLOSED`

**Required next evidence:** bind a real production-runtime semantic-verifier/capture path, induce an actual card-behavior mismatch there, emit authoritative `CARD_BEHAVIOR_FAILURE`, and prove no failed-state commit, no fallback coercion, and no private-data disclosure.

## Progression gate

Only after new evidence closes both blockers should the Q6 and failure-semantics integration gates be re-run. Q1–Q5 and Q7 must not be rerun unless those changes actually invalidate their qualified paths.

Until then:

```text
WS13_ELIGIBLE                        = FALSE
Q8                                   = DEFERRED
INITIAL_ARCHITECTURE_DECISION_FROZEN = FALSE
READY_FOR_GREENFIELD_BUILD           = FALSE
PRODUCTION_REPOSITORY_CREATED         = FALSE
```
