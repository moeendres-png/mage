# RNG and Replay Inventory — Current Qualification State

Status: **NOT RUN / INSUFFICIENT EVIDENCE**.

Current qualification revision: `5897a196405e6fc1743f41b4d5f9bf6367884930` /
`7d2ed2c97fc3579561c9166110f61a757cd88ca9`.

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

The current static inventory run `33155888005` (artifact `9679578243`) finds
10 forbidden stock fallback sites, 8 direct rules-game RNG bypasses, and 20
`MyRandom` call sites. The current runtime run `33155888017` executes three
fresh 4P processes but emits
none of the required state, RNG, or decision streams. Raw stdout, stderr,
timestamps, process IDs, and wall-clock durations are forensics only and are
never replay criteria. `SEMANTIC_REPLAY_GATE.json` records the current
`NOT_RUN` adjudication.
