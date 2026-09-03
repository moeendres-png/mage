# G3 NON-AF EVENT RUNTIME — RUN 33816948410 PENDING

Evidence classification: `UNKNOWN` until terminal run/artifact adjudication.

## Run identity

```ini
REPAIR_COMMIT=3bf09bc325ee5094d2a4874bbc133520f5f759dc
SOURCE_TREE=8e0a65344e4257fa51e2b15dfdac35e4883bd9ae
RUN=33816948410
JOB=100851076967
WORKFLOW=.github/workflows/ws33-g3-svar-event-runtime.yml
RUN_NUMBER=4
RUN_ATTEMPT=1
OBSERVED_STATUS=in_progress
CONCLUSION=PENDING
COVERAGE_PROMOTION=FALSE
G3_NON_AF_STATUS=UNKNOWN
```

## Narrow repair represented by this run

The only behavior-fixture change since the adjudicated failure checkpoint for run `33798608932` is the common `ChangesZone` run-parameter value shape in `ws33_prepare_g_svar_event_harness.py`:

```java
rp.put(AbilityKey.Origin, ZoneType.Hand.name());
rp.put(AbilityKey.Destination, ZoneType.Battlefield.name());
```

This matches pinned Forge production `GameAction.changeZone`, which emits zone-name strings for `AbilityKey.Origin` and `AbilityKey.Destination`.

No card-name/path-ID branch, direct target-SVar entry, TriggerHandler bypass, fabricated Decision/RNG evidence, silent fallback, or coverage promotion was introduced.

## Serial retry invariant

Run `33816948410` is the single runtime retry produced by repair commit `3bf09bc325ee5094d2a4874bbc133520f5f759dc`. Do not start or create another runtime retry until this run is terminal, its first material result is adjudicated, and that adjudication is persisted.

## Resume

1. Fetch terminal state for run `33816948410` / job `100851076967`.
2. On failure, secure artifact/digest and freeze the first material failing step/condition before any repair.
3. On Runtime PASS, freeze runtime evidence first; do not globally promote coverage. Then proceed to separate immutable ABI/Decision/RNG/Replay certification and Principal Observation/Hidden31 qualification.
