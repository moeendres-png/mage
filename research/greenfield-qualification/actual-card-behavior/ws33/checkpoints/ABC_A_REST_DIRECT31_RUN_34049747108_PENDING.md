# WS33 ABC — A-rest Direct31 corrected mana lifecycle diagnostic — PENDING

Status: **PENDING**
Coverage promotion: **FALSE**
Coverage mutation during witness: **FORBIDDEN**
Run source: **FROZEN**

- source HEAD: `6953607ff45cb89bb3748a0c96d36bb70c396801`
- source TREE: `f6ec854e527445645150b0283a9380915127fcf7`
- run: `34049747108`
- job: `101531078646`
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- expected artifact: `ws33-abc-a-rest-direct31-runtime-34049747108`
- exact paths: `31`
- predecessor coverage: `488 PASS / 3700 UNKNOWN`

This run differs from failed diagnostic run 34049430602 only by removal of the unsupported observation expression `ManaPool.size()`. Payment options, selection, cost/mana state, and booleans are unchanged. Its purpose remains observation-only diagnosis of the three previously verified `PAY_COST=false` paths.

Do not change this run source until terminal. Persist terminal FAIL/PASS and artifact digest before any subsequent repair or promotion.
