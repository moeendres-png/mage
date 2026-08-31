# WS33B — Cost + calculateAmount closure shard

This shard starts from the exact qualified WS33 parallel base:

- HEAD `c69686431c7296cb3e1a2f9e0de8b82886c92c46`
- TREE `6b885d02e9a0bc8cad2f93af08db99bda75955a5`
- RUN `33370369458`
- JOB `99419848606`
- ARTIFACT `9750186364` (`ws33-q6-runtime-closure-33370369458`)
- ARTIFACT DIGEST `sha256:b156241094eb14f8270f07ee7338a30768a20f0ec077d8f68b3c7e097c89dacd`
- Forge `8c7e9afb8e6caee88644b94e25da5852e36f8928`

The exact base frontier is 598 UNKNOWN `ACTION_COST_DECISION` paths:
396 `forge.game.cost.Cost` and 202
`forge.game.ability.AbilityUtils#calculateAmount`.

During pre-campaign source verification, ten assigned `calculateAmount` paths were found to
be actual `Event$ ...` replacement-effect definition SVars. Pinned Forge consumes them via
`EffectEffect -> AbilityUtils.getSVar -> ReplacementHandler.parseReplacement`, not through
`calculateAmount`.

The common child contract forbids manufacturing a synthetic `calculateAmount` call merely
to satisfy an incorrect shared assignment, and it forbids this child from changing the shared
WS33 effective-path/coverage/scenario registries. Therefore this shard deliberately fails closed
with `CROSS_SHARD_SHARED_BLOCKER = TRUE` and promotes no paths.

`ws33b_verify_shared_blocker.py` re-derives the exact frontier from the immutable base artifact,
verifies the ten actual card source declarations and their real `ReplacementEffects$` consumers
against the pinned Forge checkout, and emits machine-readable blocker/gate/handoff evidence.
