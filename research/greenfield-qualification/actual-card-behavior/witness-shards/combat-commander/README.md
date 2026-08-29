# WS18 combat / Commander witness shard

This shard owns only `COMBAT_COMMANDER` primitives from WS14. It is deliberately
fail-closed: source provenance, compilation, and predecessor WS07 results do
not constitute a semantic witness. A future PASS record must conform to the
WS14 witness ABI and include an executed pinned-Forge trace, engine-state
assertions, and immutable evidence references.
