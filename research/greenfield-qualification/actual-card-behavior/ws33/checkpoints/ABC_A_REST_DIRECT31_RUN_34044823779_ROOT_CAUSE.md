# WS33 ABC A-rest Direct31 — run 34044823779 root-cause analysis

Status: `ROOT_CAUSE_PERSISTED`

This checkpoint refines the terminal FAIL checkpoint and precedes any next runtime source mutation.

## Cluster 1 — 21 hidden-choice failures

Classification: `HARNESS_PRINCIPAL_BINDING_GAP`.

The current A-rest Direct31 adapter selects:

```java
Player actor=game.getPhaseHandler().getPlayerTurn();
```

At campaign entry the actual run transport log identifies the active player as the local host (`Alice (Host AI)`). The qualified WS33 observation fanout contract deliberately treats that local host differently:

- public `REVEAL_OBSERVATION` may fan out locally without claiming remote evidence;
- discretionary hidden Card choices remain fail-closed unless the principal owns a `RemoteClientGuiGame` observation channel.

The exact failure emitted by 21 paths is therefore expected from the current actor binding:

```text
UNSUPPORTED_DECISION_PATH: hidden authoritative Card choices require RemoteClient principal observation
```

The repair must not weaken this boundary. The actual-card campaign must choose a real remote human principal and place Forge's phase handler in legal MAIN1 for that principal before `PlaySpellAbility` runs. This restores the same principal topology already qualified by G3 while keeping Forge authoritative for timing/targets/costs.

A path-scoped `ExternalObservationTrace` will also be added as observation-only evidence so the hidden obligation can be adjudicated rather than merely avoiding a local-host failure.

## Cluster 2 — six pre-admission false returns

Classification remains `UNKNOWN_PRECONDITION` pending stage evidence.

All six return `false` from `PlaySpellAbility` before authoritative Decision events and before source-root stack admission. The current stack-resolution overlay only emits its prerequisite trace for trigger abilities, so the exact failing production stage is not yet observable for ordinary spells.

A diagnostic-only extension may log the already-evaluated boolean results for all abilities at these existing stages without changing evaluation order/result:

- extra spell `canPlay`
- announce type / X
- restrictions
- `setupTargets`
- cast timing
- legal-after-stack
- CostPayment

This is observation only and cannot manufacture legality or payment.

## Invariants

- no Forge Rules Core defect adjudicated from either cluster;
- no hidden-boundary relaxation allowed;
- no manual target injection allowed;
- no direct resolve allowed;
- no coverage mutation/promotion;
- all 57 A-rest paths remain UNKNOWN.
