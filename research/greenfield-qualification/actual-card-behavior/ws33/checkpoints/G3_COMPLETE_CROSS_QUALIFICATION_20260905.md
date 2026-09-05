# G3 COMPLETE — CROSS-QUALIFICATION

Date: 2026-09-05

Evidence classification: constituent runtime/run/artifact facts `DIRECTLY_VERIFIED`; cross-evidence set reconciliation `TECHNICALLY_CONFORMANT`.

## Exact canonical boundary

Pre-cross-qualification branch HEAD/TREE:

- HEAD `8029b9d9fb5be9ee657c4e4b61366f06dacf1ef6`
- TREE `6e075105f8b851e7e65381cb58ceac717bcbda1c`

Required pins remain unchanged:

- Forge `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- effective-manifest file SHA256 `cd48f4279d682ab944e2534bf937d87e5311e83989e97179ae73c5c7d1bb6224`
- topology consumer-model SHA256 `82638e6b3e4408cc5bddedc49372b6357d3c2bdce6fba7bfab7ed119678f9a48`

## Authoritative partition

Topology evidence proves the Generation-3 G frontier partition:

`G81 = Direct28 + AF21 + nonAF32`

Cardinality: `28 + 21 + 32 = 81`.

The topology artifact remains immutable:

- run `33681121017`
- artifact `9866293827`
- digest `sha256:6a41f66937b4bf1bcf782045d869ece183c0be49b345eac654dc3588cb98b96b`

## Direct28

- behavior Record/Replay run `33516084949`
- artifact `9803814288`
- digest `sha256:493f3549b6483d4fea9644f3a0216deb108a9ac581b651ff3e083499bcb14b5a`
- Principal Observation run `33552816460`
- artifact `9818304005`
- digest `sha256:7b39edd3cd67f1e0b398db90fbb592b7786372fe5b398b1a0bed39e79d24bbfc`
- status: fully qualified 28/28.

## AF21

- runtime-v2 run `33773548765`, artifact `9900656730`, digest `sha256:b339b3eba6daaee5b7f59e9e3c05a7af611c1479ebd3d7b6e2c94d04f72e0708`
- ABI/Decision/RNG/Replay-v2 run `33773805031`, artifact `9901008043`, digest `sha256:bf58a7154e8e2623bc9e6f4acf10c933b7d4fd692a357a643b881c586f4c15ef`
- original Principal Observation run `33774853355`, artifact `9901438964`, digest `sha256:2e60f7c79ad642f3f3942db4b3e84a9392cde5662126c0eb84153a3f0469cb5d`
- current shared-tool requalification run `33929441412`, artifact `9958136895`, digest `sha256:deef7497dd5f4d9837b1c747462f0bfef30d8f0080174a0a8a814cfd12b75022`
- current requalification proves paths21, hidden19, Record/Replay observations equal, retained hidden IDs0, cross-principal leaks0, and observation-only Decision/RNG/semantic nonperturbation.
- status: fully qualified 21/21.

## non-AF32

- Runtime Record/Replay run `33928315020`, artifact `9957712911`, digest `sha256:2241adad950188fc0f0adb0d0a1395a399251470dc8d8e75ded96d68d61aea0b`
- 32/32 paths, 33/33 source parents, Decision22/22, RNG10/10, tape-driven Replay PASS.
- separate ABI/Decision/RNG/Replay certification run `33929080030`, artifact `9957878386`, digest `sha256:d26c61446bf023af1f26ba6d9ef7f94e843e7726915c6b47578f8226662793da`; consumes the exact frozen runtime artifact.
- Principal Observation run `33929441452`, artifact `9958147261`, digest `sha256:5d7ab4034b3b674b3d907a50dfb3d7f5bbac5a3eb1abaf8c0ec42eeb1c958ed5`.
- Hidden31 adjudication PASS; Record/Replay observation equivalence; retained hidden IDs0; cross-principal leaks0; rules_mutation=false; pilot_fallback=false; coverage_mutated=false.
- status: fully qualified 32/32.

## Cross-cutting adjudication

Across the complete disjoint G81 partition, the required constituent evidence now establishes:

- authoritative Forge execution rather than pilot legality inference;
- legal Decision requests with authoritative option identity where Decision is required;
- required RNG events and tape-driven replay;
- semantic Record/Replay equivalence at each qualified constituent boundary;
- principal-scoped Hidden Information observation and grant/revoke lifecycle where required;
- no retained hidden identity payload in the qualified observation evidence;
- no cross-principal decision/observation leak in the qualified evidence;
- no first/default/random/pass/cancel silent fallback introduced by the G3 repairs;
- no Rules-Core mutation by qualification adapters;
- no constituent coverage mutation before this explicit cross-qualification.

No known G constituent remains FAIL, UNKNOWN, or UNSUPPORTED after this reconciliation.

## G3.6 result

`G3.6_CROSS_QUALIFICATION = PASS`

`G_TOTAL = 81`

`G_PASS = 81`

`G_UNKNOWN = 0`

`G_FAIL = 0`

`G_UNSUPPORTED = 0`

`G3_COMPLETE = TRUE`

This checkpoint promotes only the G partition. It does not claim WS33 completion. The next mandatory operation is a live 4188-frontier recomputation with this G promotion, followed strictly by `ABC -> D -> E -> F -> final cross-qualification`.

`WS33_COMPLETE = FALSE`
`TASK_COMPLETE = NO`
