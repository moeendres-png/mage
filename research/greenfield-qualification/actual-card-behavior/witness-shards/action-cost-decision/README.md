# WS15 action / cost / decision witness shard

This shard owns the 76 WS14 primitives assigned to `ACTION_COST_DECISION`.

It begins fail closed.  The present status record deliberately contains no
`PASS` witness: each listed primitive lacks an executed, actual-card, pinned
Forge semantic witness that binds the primitive to a legal engine path and
asserts engine state.  The WS14 dispatch mapping is retained only as
`CODE_DERIVED` provenance and cannot promote behavior.

To change a row to `PASS`, a successor must supply a WS14-ABI-valid witness
with exact `primitive_exercise`, immutable trace hash, initial and final
semantic state evidence, relevant decision/RNG tapes, `stdout_only=false`, and
official-rules adjudication where semantics require it.  Test-driver logic may
not synthesize legal choices or default player decisions.
