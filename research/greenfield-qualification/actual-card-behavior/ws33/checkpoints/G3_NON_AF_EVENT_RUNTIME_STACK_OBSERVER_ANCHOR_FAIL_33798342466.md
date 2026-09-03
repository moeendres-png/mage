# G3 NON-AF EVENT RUNTIME — STACK OBSERVER ANCHOR FAILURE

Status: `ADJUDICATED FAILURE / NO RUNTIME EXECUTION`

Evidence classification: `UNKNOWN` for the 32 non-AF effective paths. This is a pre-runtime qualification-instrumentation integration failure, not an engine/card-behavior failure.

## Immutable run identity

- workflow source HEAD: `935da1abf48b84f85e4265a26ba65fb546e8cb07`
- workflow source TREE: `f2ede3993608c0a7bf92461462124112d57dcf21`
- run: `33798342466`
- job: `100791376533`
- run/job conclusion: `failure`
- partial-failure artifact: `9910100377`
- artifact digest: `sha256:ced3f9f26efe6f0540b4d8b661f5afad0fea2adc5071762866864658d1fb846a`
- artifact size: `65214` bytes

## Confirmed progress before failure

The previous topology-hash defect is closed in this run:

- exact topology artifact run/head/digest checks: PASS
- topology v2 consumer-model assertion: PASS
- Event Case ABI v2 generation: PASS
- `32 effective paths / 33 parent entrypoints / 21 fields`: PASS
- all immutable retained source checkouts: PASS
- exact source pin verification: PASS
- WS01 decision overlay: PASS
- WS05 hidden overlay: PASS
- WS06 RNG overlay: PASS
- WS33 input-confirm overlay: PASS
- WS33 stack-target overlay: PASS
- WS33 target-selection overlay: PASS
- observation-only TriggerHandler reachability overlay: PASS

## First material failure

Step 11, `Apply qualified runtime overlays plus observation-only event reachability`, failed at:

```text
WS33_STACK_RESOLUTION_REACHABILITY=FAIL observer declaration anchor: expected one match, got 0
```

The overlay expected:

```java
public class MagicStack implements Iterable<SpellAbilityStackInstance> {
```

Pinned Forge `8c7e9afb8e6caee88644b94e25da5852e36f8928` actually declares:

```java
public class MagicStack /* extends MyObservable */ implements Iterable<SpellAbilityStackInstance> {
```

Therefore the failure is an exact source-anchor mismatch in the observation-only overlay. The non-fizzled API-resolution anchor has not yet been reached/adjudicated by this run.

## Qualification effect

- Maven compilation: not reached
- Record campaign: not reached
- Replay campaign: not reached
- non-AF32 behavior status: `UNKNOWN`
- parent33 runtime status: `UNQUALIFIED`
- coverage promotion: `FALSE`

## Required next step

Repair only `apply-ws33-stack-resolution-reachability.py` to bind the exact pinned Forge class declaration (fail closed), persist that repair, then adjudicate exactly the single run triggered by that repair before any additional retry.
