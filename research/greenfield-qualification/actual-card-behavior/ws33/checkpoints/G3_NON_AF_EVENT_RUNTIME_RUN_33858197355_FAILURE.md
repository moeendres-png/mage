# G3 non-AF event runtime — run 33858197355 FAILURE

## Immutable run identity

- RUN: `33858197355`
- JOB: `100976276642`
- SOURCE_HEAD: `1bbf1a497492d4c23df60268550e94bebb1581ab`
- SOURCE_TREE: `08827a0e72ff928071290511597b0da4659dc480`
- ARTIFACT: `9931146326`
- ARTIFACT_DIGEST: `sha256:836e0ad3071cc86f9fc98896a690b5e156a8e284f34219a8904e7702430de5bc`
- downloaded ZIP SHA256: `836e0ad3071cc86f9fc98896a690b5e156a8e284f34219a8904e7702430de5bc` — exact match
- workflow: `ws33-g3-svar-event-runtime.yml`
- terminal conclusion: `failure`

## Gate result

- source/topology/pins/overlays/harness: PASS
- 33-parent record campaign: PASS
- record adjudication: FAIL
- tape-driven replay: NOT RUN
- evidence upload: PASS
- coverage promotion: FALSE

## Directly verified record state

The repair that reached this run is effective at runtime level:

- parent runtime: `33/33 PASS`
- effective path runtime: `32/32 PASS`
- every parent has source admission `1`, target binding `1`, target execution `>=1`
- Study Hall (`forge-behavior-v2:ae82d4423a23aaf18b7da0e9215165e8d55ba5f2`) is now `1/1/1` and PASS
- no parent/path runtime failure remains in this artifact

## First material failure

Re-running the exact Step-15 Python adjudicator against this immutable artifact yields:

`WS33_G_SVAR_EVENT_DECISION_REQUIRED_MISSING=['forge-behavior-v2:1b1d899f942620f8251e98ad58577e873d18c540', 'forge-behavior-v2:529d886326a79bdcfd263f2125506132e7a320f6', 'forge-behavior-v2:7ba3879ce621c87153fcc8d3292a88872b0d074e', 'forge-behavior-v2:da6d57cc4b8b7bcde7baa9519f6d13ce63fb775b']`

Those paths are respectively source-proven by:

1. Songbirds' Blessing — `DigUntil`
2. Director Nick Fury — `Dig`
3. Armored Skyhunter — `Dig`
4. Herald's Horn — `PeekAndReveal`

All four are marked `decision_required=1` in the generated 21-field event-case input, but `decision-events-with-path.tsv` contains zero events attributed to each path. This is the first strict failure and therefore the next diagnosis boundary.

The same exact verifier also shows `decision_required=22`, with accepted decision events attributable to 18 of those required paths.

## Secondary blocked failure

If the Decision gate is evaluated without stopping first, the artifact also has one missing required RNG path:

`forge-behavior-v2:24a5352cfaa6ae913df6549ceed0c447d526e89d` — Descendants' Fury / `DigUntil`.

`rng_required=10`; RNG events are attributable to 9 required paths and zero to this path. This is recorded now but MUST NOT be repaired by inference before the Decision root cause is adjudicated; both may share the same producer/attribution boundary.

## Evidence classification

- run/artifact identity: `DIRECTLY_VERIFIED`
- parent/path runtime PASS counts: `DIRECTLY_VERIFIED`
- exact Step-15 reproduction and missing path sets: `DIRECTLY_VERIFIED`
- systemic cause of missing Decision/RNG attribution: `UNKNOWN`

## What is ruled out

- Study Hall trigger admission/binding/execution is no longer the blocker.
- No remaining parent runtime or effective-path runtime blocker is present in this record artifact.
- Coverage must not be promoted because Decision/RNG obligations and replay are not yet satisfied.

## Next atomic package

Read-only correlate the four Decision-missing and one RNG-missing paths against raw decision/rng tapes, request traces, resolver APIs and path-attribution producer lifecycle. Determine whether the discretionary/RNG event actually occurs without path attribution, is legitimately absent because the generated obligation is wrong, or is suppressed by a qualification fixture. Repair only the proven systemic model/producer/fixture defect, never by card/path name. Then one repair commit -> exactly one runtime run -> immediate PENDING checkpoint -> terminal adjudication.

`G3_NON_AF_STATUS = UNKNOWN`

`COVERAGE_PROMOTION = FALSE`

`WS33_COMPLETE = FALSE`

`TASK_COMPLETE = NO`
