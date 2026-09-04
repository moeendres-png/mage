# G3 NON-AF Event Runtime — Run 33863979003 — FAILURE

Status: `FAILURE`

## Immutable run binding

- Repository: `moeendres-png/mage`
- Branch: `work/ws33-g3-final-closure-20260902`
- Workflow: `.github/workflows/ws33-g3-svar-event-runtime.yml`
- Run: `33863979003`
- Job: `100994503842`
- SOURCE_HEAD: `35a2a267fa70b87a4d21d5cbae98be3f7bdd27eb`
- SOURCE_TREE: `85c1d4fe2df0f980d1e4fe43c4bca11b2eeb5108`
- Artifact ID: `9933311779`
- Artifact name: `ws33-g3-svar-event-runtime-33863979003`
- GitHub artifact digest: `sha256:204cd7c057196220fdb60cd9662443a8703f20cbb7bc02f90d022fe8508353fa`
- Independent downloaded ZIP digest: `sha256:204cd7c057196220fdb60cd9662443a8703f20cbb7bc02f90d022fe8508353fa`
- Digest comparison: `MATCH`

The SOURCE_TREE is independently confirmed both by `generated/diagnostic/workflow-source-tree.txt` in the immutable artifact and by GitHub commit metadata for SOURCE_HEAD.

## Terminal adjudication

The record campaign itself is green; the run fails in the strict pre-replay Decision/RNG gate.

- Effective non-AF G paths: `32/32 PASS`
- Source-proven production parents: `33/33 PASS`
- `record/process.json`: `game_completed=true`, `path_count=32`, `outer_failure=null`
- Pilot-visible hidden leaks: `0`
- Cross-principal decision leaks: `0`
- Phase mismatches: `0`
- Decision-required paths: `22/22 satisfied`, `0 missing`
- RNG-required paths: `9/10 satisfied`, `1 missing`
- Replay: `NOT_RUN` because the pre-replay gate failed; fail-closed ordering is preserved.

Exact first material Step-15 failure, reproduced locally from the workflow predicate over this immutable artifact:

```text
WS33_G_SVAR_EVENT_RNG_REQUIRED_MISSING=['forge-behavior-v2:24a5352cfaa6ae913df6549ceed0c447d526e89d']
```

## Missing RNG-required path

- Effective path: `forge-behavior-v2:24a5352cfaa6ae913df6549ceed0c447d526e89d`
- Oracle ID: `97079964-7a2e-42c5-ad4a-9015c18a1e97`
- Source card / parent: `Descendants' Fury`
- Parent mode: `DamageDoneOnce`
- Target SVar: `TrigDigUntil`
- Dispatch / API: `DigUntil`
- Target script contains `Cost$ Sac<1/Card.TriggeredSources>` and `RevealRandomOrder$ True`.
- Parent admission: `1`
- Target binding: `1`
- Parent observer target-execution count: `1`
- Resolution callback count: `1`
- Correlated RNG tape events: `0`

## Corrected reachability diagnosis

### DIRECTLY_VERIFIED

The observation-only `WS33_TRIGGER_PLAY` trace for the exact admitted target ability in this run is:

```text
abilityId=712 sourceTrigger=50010 hostId=385 api=DigUntil
ANNOUNCE_TYPE=true
ANNOUNCE_X=true
CHECK_RESTRICTIONS=true
CAST_TIMING=true
LEGAL_AFTER_STACK=true
PRECOST_REQUISITES=true
PAY_COST=false
PREREQUISITES_MET=false
```

The wrapping triggered ability itself reaches and resolves through MagicStack. The underlying `DigUntil` target ability then fails its cost-payment prerequisite. Therefore the `DigUntilEffect` random-order operation is not reached in this run.

The existing resolution observer fires before the underlying paid ability's semantic effect and cannot, by itself, prove that the paid `DigUntil` effect body executed. Consequently the earlier diagnosis that this was merely a degenerate `Collections.shuffle` witness is withdrawn.

### CODE_DERIVED

Pinned `TriggerDamageDoneOnce.setTriggeringObjects` places the damage-source collection into triggering object `AbilityKey.Sources`. The qualification fixture creates a controlled `Runeclaw Bear` on the battlefield, places it in the `DamageMap`, and production trigger admission succeeds. The target script's sacrifice cost refers to `Card.TriggeredSources`.

The exact unresolved boundary is therefore inside or immediately around authoritative cost materialization/payment for `Sac<1/Card.TriggeredSources>` on the source-proven triggered sub-ability. Current evidence does not yet distinguish among:

1. an event-fixture omission relative to a real production damage event;
2. loss/non-propagation of triggering `Sources` from the wrapper into the executed target ability;
3. an authoritative-choice/payment integration defect;
4. another pinned-Forge cost prerequisite.

### UNKNOWN

No production rules-core repair is justified yet. No qualification-fixture repair is justified yet. The root cause remains `UNKNOWN` until the `TriggeredSources` value, sacrifice candidate set, authoritative decision result, and cost-part outcome are traced on this exact path.

## Required successor diagnostic

Before any behavioral repair:

1. add observation-only, generic cost-boundary tracing for `Sac<1/Card.TriggeredSources>` / sacrifice payment without card-name or effective-path branching;
2. record the triggering `Sources` object visible to the target ability, authoritative sacrifice candidates, selected authoritative option/card, and the cost-part success/failure boundary;
3. preserve rules, legal-option generation, payment semantics, decisions, RNG, coverage and fallbacks unchanged;
4. run exactly one successor workflow from that single diagnostic commit;
5. persist RUN/JOB/SOURCE_HEAD/SOURCE_TREE immediately as PENDING and make no runtime-affecting write until terminal;
6. adjudicate the artifact before choosing fixture vs Forge repair.

## Closure flags

```text
G3_NON_AF_STATUS=UNKNOWN
COVERAGE_PROMOTION=FALSE
WS33_COMPLETE=FALSE
TASK_COMPLETE=NO
```
