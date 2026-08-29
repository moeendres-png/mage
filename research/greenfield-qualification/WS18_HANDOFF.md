# WS18 — Combat / Commander witnesses

`WORKSTREAM_COMPLETE = TRUE`

- Branch: `work/ws18-witness-combat-commander-20260829`
- Base: `d8c1ee0c08c7e7f0bc2bc86c70166ebc198e30d5`
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- Qualified implementation HEAD/tree: `18ee0c6e4ae7a7c6fb36b1c859c1ecaad2a6c7cf` / `33acc6a34233902380dad857eaef66e2b58bd86b`
- Workflow run/job: `33263491675` / `99129313855`
- Artifact/digest: `9717959307` / `sha256:41868506e9763b9ac6bff23ad9dee706b316881567dc7378ca20bcd386f0e078`

The initial WS18 shard is intentionally fail-closed. It materializes all ten
WS14-owned primitives as `PARTIAL` until a pinned-Forge, state-asserting
witness conforms to the WS14 ABI. Neither the predecessor WS07 Commander
matrix nor source dispatch evidence is promoted to a WS18 semantic witness.

`Q6_ACTUAL_CARD_BEHAVIOR = NOT_ADJUDICATED`

Coverage: `PASS=0`, `PARTIAL=10`, `UNKNOWN=0`, `UNSUPPORTED=0`.

The exact smallest blocker for every owned primitive is an absent pinned-Forge,
state-asserting semantic execution witness. The successful workflow proves the
exact Forge pin compiles and that the shard’s accounting is complete; it does
not promote compilation or WS07 predecessor evidence to behavior proof.
