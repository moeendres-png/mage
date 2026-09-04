# WS33 G3 non-AF event runtime — run 33853539153 terminal failure

Classification: DIRECTLY_VERIFIED / CODE_DERIVED

Canonical branch before checkpoint:

- HEAD: `c10e650c70bc3de5987eeb8f5d05a473052f21d9`
- TREE: `1903fdafb159acc946e7090cffc1e1845e208a05`

Qualification source and immutable evidence:

- SOURCE_HEAD: `98bf38cf6c97f81faacfdefd40b718909ae5494d`
- SOURCE_TREE: `5fe6275585d6068d2fa92166fcf4693672b90c5b`
- RUN: `33853539153`
- JOB: `100961524939`
- ARTIFACT: `9929351802`
- DIGEST: `sha256:126138f1ec2a6c84bad1f823c9814eeaf8213adb4815dbe67181f5a911ae6107`
- local artifact SHA-256 independently matched the GitHub digest exactly.

## Workflow result

- exact immutable topology/case materialization: PASS
- exact source pins: PASS
- qualified principal-observation/lifetime overlays: PASS
- 33-parent harness preparation: PASS
- Step 14 `Execute 33-parent record campaign`: PASS
- Step 15 `Adjudicate record behavior and minimum Decision/RNG obligations`: FAIL
- replay: correctly skipped
- artifact upload: PASS

The principal-observation/lifetime repair therefore removed the prior hidden-card runtime blocker. It is not a qualification PASS because the strict parent gate still rejects eight parents.

## Exact Step-15 parent partition

`parent-summary.tsv` has 33 rows. 25 parents satisfy the strict runtime gate; 8 fail. `case-summary.tsv` has 32 effective paths; 24 pass and the same 8 unique paths fail.

Failing parents:

1. `forge-behavior-v2:242680ed5d889cd7f00fc41e2e70ec8945aaf9c1#1` — Keen Duelist — `Phase` — target `TrigReveal / PeekAndReveal` — admission/binding/execution `0/0/0` — `source-proven trigger admission count=0`.
2. `forge-behavior-v2:529d886326a79bdcfd263f2125506132e7a320f6#1` — Director Nick Fury — `AttackersDeclared` — target `TrigDig / Dig` — `0/0/0` — `ClassCastException: Player cannot be cast to Iterable`.
3. `forge-behavior-v2:ae82d4423a23aaf18b7da0e9215165e8d55ba5f2#1` — Study Hall — `SpellCast`, source directive `SVAR TrigSpent` — target `TrigScry / Scry` — `0/0/0` — `source-proven trigger admission count=0`.
4. `forge-behavior-v2:c27478a04d0da0cca433e9c9d06be9d04b540c66#1` — Chimil, the Inner Sun — `Phase` — target `TrigDiscover / Discover` — `0/0/0` — admission count 0.
5. `forge-behavior-v2:cd96db9587a128622bf87f0b7a943e0a1602ca61#1` — Plargg and Nassari — `Phase` — target `TrigDigUntil / DigUntil` — `0/0/0` — admission count 0.
6. `forge-behavior-v2:dc484d9d0750c36858479fcfa778252fedaeb62d#1` — H.E.R.B.I.E., Lovable Robot — `Phase` — target `TrigSurveil / Surveil` — `0/0/0` — admission count 0.
7. `forge-behavior-v2:f614e8861efa1f77d46e504be933771e4794ea9f#1` — Champions from Beyond — `AttackersDeclared` — target `TrigScry / Scry` — `0/0/0` — same `Player cannot be cast to Iterable` ClassCastException.
8. `forge-behavior-v2:fcee6d7a218aefb965cc2606199f4470ba6ab2e7#1` — Negative Zone Portal — `Phase` — target `TrigFlip / FlipCoin` — `0/0/0` — admission count 0.

Because the parent gate fails first, Decision/RNG minimum obligations and replay are not adjudicated by this run and must not be promoted from partial traces.

## Two directly proven event-shape defects

### A. Phase registration ordering

The generated campaign currently calls `game.getTriggerHandler().resetActiveTriggers()` before `dispatchSourceEvent(...)`. For `Phase` parents, `dispatchSourceEvent` only later calls `game.getPhaseHandler().devModeSet(targetPhase, actor)`.

Pinned Forge `TriggerHandler.resetActiveTriggers()` calls `isTriggerActive()`, and `isTriggerActive()` calls `regtrig.phasesCheck(game)` before registering the trigger. Therefore a Phase trigger is omitted whenever the ambient prior phase does not already equal its `Phase$ ...` restriction. The result is case-order-dependent and explains the five remaining Phase admission-zero parents. A Phase parent that happened to encounter a matching ambient phase can pass, so the historical green Phase row does not invalidate this defect.

Authorized systemic repair: establish the source event's target phase before rebuilding active triggers; do not special-case card names or individual Phase values.

### B. AttackersDeclared `AttackedTarget` shape

The event harness currently writes:

`rp.put(AbilityKey.AttackedTarget, opponent)`

for `AttackersDeclared`.

Pinned Forge production `PhaseHandler` writes the aggregate attacked-target collection to `AbilityKey.AttackedTarget`. Pinned `TriggerAttackersDeclared.setTriggeringObjects()` casts that runParam to `Iterable<GameEntity>`. The scalar Player fixture therefore causes the observed ClassCastException.

Authorized systemic repair: construct the same aggregate Iterable/collection shape used by production for `AttackersDeclared`; do not alter trigger code.

## Remaining unknown within this failure set

`Study Hall / TriggersWhenSpent` is not explained by the two event-shape defects above. The harness creates the source-proven `TrigSpent` delayed trigger through the actual `AbilityManaPart.addTriggersWhenSpent(spell)` path and then admits the commander spell through `MagicStack.addAndUnfreeze`. Its exact rejection condition is still UNKNOWN.

No Study Hall-specific or TriggersWhenSpent repair is authorized yet. The next campaign may include observation-only expected-trigger rejection telemetry so the exact `canRunTrigger` gate can be established directly.

## State

- non-AF runtime qualification: UNKNOWN
- 25/33 parents are materially green in this record; not promoted
- 24/32 effective paths materially green in this record; not promoted
- coverage mutation: not authorized
- G3 remains open
- ABC/D/E/F remain blocked by serial order
