# WS33 ABC — A-rest Direct31 runtime v6 observation-verifier repair — PENDING

Status: **PENDING**
Coverage promotion: **FALSE**
Coverage mutation during witness: **FORBIDDEN**
Run source: **FROZEN**

- source HEAD: `8a1f89d146b33b5539047bddffae196c8fada680`
- source TREE: `4a75e4711c16814434b156c7ccba01148dbab69a`
- run: `34058637176`
- job: `101555047425`
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- expected artifact: `ws33-abc-a-rest-direct31-runtime-34058637176`
- exact Direct31 paths: `31`
- predecessor topology artifact: `9980023181`
- predecessor coverage: `488 PASS / 3700 UNKNOWN`

Runtime code, cancellation normalization, actor/observation instrumentation, target/cost/mana routes and fixture state are unchanged from v5. The only source delta is the evidence verifier: server observation reasons remain part of semantic Record/Replay equality, while client `delta:<n>` transport sequence labels are shape-validated but excluded from semantic equality. Client path/kind/principal/card/identity tuples and strict per-card lifecycles remain exact requirements.

No coverage mutation or promotion is permitted while this run executes. Do not modify the frozen source until terminal artifact adjudication is persisted.
