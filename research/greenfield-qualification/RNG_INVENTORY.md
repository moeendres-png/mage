# RNG and Replay Inventory — Current Qualification State

Status: **NOT RUN / INSUFFICIENT EVIDENCE**.

The research package now contains versioned contracts for named `RngEvent`,
`DecisionEvent`, `CanonicalStateDigest`, and semantic replay comparison. The
Forge source census still identifies direct rules-game RNG bypasses and
`MyRandom` call sites, but no current gameplay run emits a complete canonical
RNG/event/decision tape.

Required streams are:

- named RNG stream, draw index, bound, value, and semantic context;
- monotonic decision event IDs with request token and response status;
- public and principal-scoped canonical state digests;
- three fresh processes with identical semantic trajectories.

Raw stdout, stderr, timestamps, process IDs, and wall-clock durations are
forensics only and are never replay criteria. `SEMANTIC_REPLAY_GATE.json`
records the current `NOT_RUN` adjudication.
