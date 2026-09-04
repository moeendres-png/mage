# G3 NON-AF Event Runtime — Run 33863979003 — FAILURE

Status: `FAILURE`

## Immutable run binding

- Repository: `moeendres-png/mage`
- Branch: `work/ws33-g3-final-closure-20260902`
- Workflow: `.github/workflows/ws33-g3-svar-event-runtime.yml`
- Run: `33863979003`
- Job: `100994503842`
- SOURCE_HEAD: `35a2a267fa70b87a4d21d5cbae98be3f7bdd27eb`
- SOURCE_TREE: `47ff4fdd99f63fc3489dc8a2055536de31a8165a`
- Artifact ID: `9933311779`
- Artifact name: `ws33-g3-svar-event-runtime-33863979003`
- GitHub artifact digest: `sha256:204cd7c057196220fdb60cd9662443a8703f20cbb7bc02f90d022fe8508353fa`
- Independent downloaded ZIP digest: `sha256:204cd7c057196220fdb60cd9662443a8703f20cbb7bc02f90d022fe8508353fa`
- Digest comparison: `MATCH`

## Terminal adjudication

The runtime record campaign itself is green; the run failed in the strict ABI/Decision/RNG gate before replay.

- Effective non-AF G paths in record evidence: `32/32 PASS`
- Source-proven production parents in record evidence: `33/33 PASS`
- `record/process.json`: `game_completed=true`, `path_count=32`
- Principal/hidden/phase leak indicators: none observed in the run artifact
- Decision-required paths: `22/22 satisfied`, `0 missing`
- RNG-required paths: `9/10 satisfied`, `1 missing`
- Replay: `NOT_RUN` because the pre-replay qualification gate failed; this is the intended fail-closed ordering.

First material Step-15 failure, reproduced from the exact workflow predicate over the exact run artifact:

```text
WS33_G_SVAR_EVENT_RNG_REQUIRED_MISSING=['forge-behavior-v2:24a5352cfaa6ae913df6549ceed0c447d526e89d']
```

## Exactly missing RNG-required path

- Effective path: `forge-behavior-v2:24a5352cfaa6ae913df6549ceed0c447d526e89d`
- Source card / parent: `Descendants' Fury`
- Trigger event: `DamageDoneOnce`
- Target SVar: `TrigDig`
- Dispatch / API: `DigUntil`
- Relevant target script semantic: `RevealRandomOrder$ True`
- Trigger admission: achieved
- Target binding: achieved
- Target execution: achieved
- Resolution callback: achieved
- RNG tape rows correlated to this effective path: `0`

The event/trigger/stack/resolution chain therefore executed; the missing obligation is specifically an observable RNG-consumption witness for the required random-order branch.

## Root-cause evidence

### DIRECTLY_VERIFIED

- Run/job/source/artifact binding above.
- Artifact digest independently matches GitHub's digest.
- The record campaign contains all `32` effective paths and all `33` source parents as PASS.
- Decision obligation is complete at `22/22`.
- The only missing required RNG path is `forge-behavior-v2:24a5352cfaa6ae913df6549ceed0c447d526e89d`.
- That path is `Descendants' Fury -> DamageDoneOnce -> TrigDig -> DigUntil` with `RevealRandomOrder$ True`.
- The pinned Forge `DigUntilEffect` removes the found card from `revealed` and, when `RevealRandomOrder` is true, executes `Collections.shuffle(revealed, MyRandom.getRandom())`.

### CODE_DERIVED

- The exact Step-15 missing-required assertion above is reproduced from the workflow's qualification predicate over this run's immutable artifact.
- The current source-fixture preparation has no generalized guarantee that a `RevealRandomOrder$ True` `DigUntil` case leaves at least two nonmatching revealed cards after removal of the found card.
- If the remaining `revealed` list is empty or singleton, Java shuffle is degenerate and need not consume an RNG value, so the branch can execute without producing an RNG tape event.

### MODELED diagnostic conclusion

This is currently classified as a **qualification-fixture under-exercise of a production-reachable random-order branch**, not as evidence of a Forge rules-core event-resolution defect. The successor must force a non-degenerate random-order case using script semantics rather than card/path-name special casing.

### UNKNOWN

Overall non-AF G runtime qualification remains `UNKNOWN` until a successor run passes the complete record + ABI/Decision/RNG + replay gates.

## Required successor repair

Implement a generalized script-semantic fixture for supported `RevealRandomOrder$ True` cases that:

1. is selected from parsed script semantics, never from card name or effective-path ID;
2. guarantees a non-degenerate revealed remainder for the qualified random-order operation (at least two nonmatching revealed objects remain after the matching object is removed);
3. preserves the actual matcher semantics used by the script;
4. fails closed when the matcher shape cannot be safely materialized;
5. does not modify production rules, legal actions, targets, costs, decisions, RNG implementation, coverage state, or fallback behavior.

After that repair: exactly one successor workflow run, immediately followed by a persistent PENDING checkpoint before any other runtime-affecting write.

## Closure flags

```text
G3_NON_AF_STATUS=UNKNOWN
COVERAGE_PROMOTION=FALSE
WS33_COMPLETE=FALSE
TASK_COMPLETE=NO
```
