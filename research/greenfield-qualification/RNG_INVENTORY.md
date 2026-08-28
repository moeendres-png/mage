# RNG and Replay Inventory — Current Qualification State

Status: **NOT RUN / INSUFFICIENT EVIDENCE**.

Current qualification revision: `0ea93d09d80e5c126eccb3323b17f14542e5559a` /
`64c97a207ad270fa398682c84d8dd238811a8b79`.

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

The current static inventory run `33124530367` (artifact `9667812533`) finds
10 forbidden stock fallback sites and 8 direct rules-game RNG bypasses. The
current runtime run `33124530414` executes three fresh 4P processes but emits
none of the required state, RNG, or decision streams. Raw stdout, stderr,
timestamps, process IDs, and wall-clock durations are forensics only and are
never replay criteria. `SEMANTIC_REPLAY_GATE.json` records the current
`NOT_RUN` adjudication.
