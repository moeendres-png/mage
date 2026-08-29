# WS19 — Hidden Information / RNG / Replay Witness Shard

This shard owns exactly the `HIDDEN_RNG_REPLAY` primitive set of the immutable
WS14 manifest. It is intentionally fail-closed: the initial record has no
PASS witnesses because neither the WS05 nor WS06 global gates is evidence that
one of the 14 assigned actual-card Forge effect paths executed.

A later PASS record must satisfy the WS14 witness ABI, execute the exact pinned
Forge implementation through an actual-card scenario, retain an immutable trace
and state evidence, and include principal-scoped observation plus named RNG and
semantic replay evidence when those dimensions are reached. Similar source text,
card identity, stdout, parsing, or prior global qualification is insufficient.

The current coverage document is generated locally during the WS19 workflow;
it is a non-PASS accounting artifact, not a semantic witness registry.
