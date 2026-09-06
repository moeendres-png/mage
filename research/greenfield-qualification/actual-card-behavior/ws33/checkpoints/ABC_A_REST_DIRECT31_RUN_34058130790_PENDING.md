# WS33 ABC — A-rest Direct31 runtime v5 cancel-boundary normalization — PENDING

Status: **PENDING**
Coverage promotion: **FALSE**
Coverage mutation during witness: **FORBIDDEN**
Run source: **FROZEN**

- source HEAD: `23d16c74cc5ec853f17896369ac6ce86443e5391`
- source TREE: `5928fa3ba2bcd9bc9404d3faf025b9558732dbe2`
- run: `34058130790`
- job: `101553684254`
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- expected artifact: `ws33-abc-a-rest-direct31-runtime-34058130790`
- exact Direct31 paths: `31`
- predecessor topology artifact: `9980023181`
- predecessor coverage: `488 PASS / 3700 UNKNOWN`

This run preserves the v4 actual-card, remote-principal, target, CostPayment, hidden-observation, RNG and replay routes. Its sole behavioral boundary delta is systemic MANA_PAYMENT cancellation representation: the WS01-authorized non-mandatory cancel transition is carried through `ExternalDecisionRequest.cancelAllowed` / `ExternalDecisionResponse.cancel`, not as an ordinary `CANCEL` option mixed with Forge-filtered payment transitions.

The qualification pilot does not infer mana legality. All payment options remain constructed and revalidated by Forge. No card-name branch, direct mana injection, cost bypass, target injection, direct resolution, or coverage promotion is permitted.

Do not modify this run source until terminal adjudication and immutable artifact digest are persisted.
