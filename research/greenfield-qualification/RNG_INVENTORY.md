# RNG and Replay Inventory — Current Qualification State

Status: **NOT RUN / INSUFFICIENT EVIDENCE**.

Current qualification revision: `34036a2d6704c0b70c0a59d071bc938870db0c2b` /
`33e3968b35fc5cd2967f12d8f57c4b7ebab2d21f`.

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

The current static inventory run `33152614624` (artifact `9678318483`) finds
10 forbidden stock fallback sites, 8 direct rules-game RNG bypasses, and 20
`MyRandom` call sites. The current runtime run `33152614679` executes three
fresh 4P processes but emits
none of the required state, RNG, or decision streams. Raw stdout, stderr,
timestamps, process IDs, and wall-clock durations are forensics only and are
never replay criteria. `SEMANTIC_REPLAY_GATE.json` records the current
`NOT_RUN` adjudication.
