# WS33-C Batch-5 SELECTION (solo kappa sub-link re-witness)

SOURCE_HEAD = (frozen at commit; see PENDING)
SOURCE_TREE = (frozen at commit; see PENDING)
FORGE_PIN = 8c7e9afb8e6caee88644b94e25da5852e36f8928
PARTITION = 13 EVIDENCED / 687 UNKNOWN
INVENTORY = WS33_C_EFFECT_STATIC_INVENTORY.json sha256 65aebfd9766722516c5aaaca5bdf8bd675e6e99f6d68784f14b3c4890870483a (23 rows, unchanged)
BATCH_DIGEST = (computed by checker/preparer; see PENDING)

## Target (1 UNKNOWN)

forge-behavior-v2:634a4b2d09d12a138afd0544c87c7d2bdb57a05a
Kappa Cannoneer TrigPutCounter->DBUnblockable (sub-link).
Provenance: forge-gui/res/cardsfolder/k/kappa_cannoneer.txt:8
(SVar TrigPutCounter DB$ PutCounter @ line 8 with SubAbility$
DBUnblockable; child SVar DBUnblockable DB$ Effect).
Row scope: template-113, STATE_ONLY, AbilitySub target; canonical
coverage UNKNOWN; absent from the branch evidenced partition (no
allow-rewitness required).

Batch-4 verdict (run 34407243931, independently adjudicated): pair
(20,21) exactly matched BUT static observation count=2 shared across
setup + fixture firings, unmappable from record bytes; certifier
fail-closed UNKNOWN ("effect-static observation not unique").
Cause FIXTURE_DEFECT (shared-execution design): the batch-4
kappa-etb-other execution carried TWO links (sub-link 634a4b2d +
terminal 998516b9), so the effect_static_present assertion evaluated
once per row and emitted two same-id observations; additionally both
the via=move setup firing and the fixture firing each created one
Command-zone effect (absolute count 2).

## Chosen assertion primitive (unchanged)

`effect_static_present` + `after_eot_absent`, as batch-4.

## Solo execution

kappa-etb-other-place: Kappa pre-placed via=place (direct Battlefield
placement fires no entry trigger), fixture Sol Ring ETB_OTHER_ENTER.
Single link (the sub-link only; the terminal 998516b9 is already
EVIDENCED and is not re-witnessed). Assertions: kappa P1P1==1 +
effect_static_present (CantBlockBy/linked/1, after_eot_absent) +
hand-net-actor -1.

Expected: exactly one fixture firing -> absolute finals 1/1 prove
exactly-once; one same-id static observation -> singular and uniquely
attributable under the standing certifier gate.

## R11 C-owned generic repair (required; pin-proven)

via=place alone is insufficient, and would fail closed as silence:
AITest.addCardToZone at the pin is createCard + raw zone add (no
moveTo, no zone-change event, no trigger registration); GameAction.
changeZone registers only the MOVED card (clearActiveTriggers +
registerActiveTrigger on the entering copy); TriggerHandler.
runWaitingTrigger/runTrigger iterate activeTriggers only; and no
checkStateEffects runs between setup placement and the fixture
trigger. A raw-placed Kappa would therefore never fire: the fixture
waiting entry would resolve to statics-only and the harness would
throw "waiting trigger never reached the stack".

Repair (Ws33AbilitySubWitnessTest.java, C-owned, generic): after setup
verification, call game.getTriggerHandler().resetActiveTriggers().
This is exactly the engine's own per-SBA-flush bookkeeping
(GameAction calls resetActiveTriggers after every state-effects
flush at the pin; collect-then-rebuild from all in-game cards). It
fires nothing and fabricates no entry event: the via=place card's own
entry trigger correctly stays silent (retrospective ChangesZone
events do not exist), while its standing triggers become observable
for the fixture window. Via=move placements are unaffected (their
triggers were registered by their own production moveTo;
rebuild-then-re-add is duplicate-safe). No card names consulted, no
legality derived, no outcome injected, no shared/foreign change.

Controller safety (pin): Card.getController falls back to owner when
the controller field is unset, and CardFactory sets owner at
creation; a via=place card controlled by its owner satisfies both
ValidCard$ Artifact.YouCtrl and controller_is_actor identically to
the via=move case. The per-firing counter increment is 1
(TrigPutCounter carries no CounterNum$; batch-4 absolute finals 2/2
over two firings), hence expected 1.

## Profiles / obligations

template-113, STATE_ONLY flags. Runtime tripwire + static screen +
postconditions per established contract. Forced-choice bundles: none
expected. Direct-child negatives retained. Source seal + hash sealing
as established.

## Excluded / retained

- 998516b9 terminal Unblockable: retained EVIDENCED, not re-witnessed.
- 2dd428f9 terminal MayPlay: retained EVIDENCED, not re-witnessed.
- All other UNKNOWN: out of batch-5 scope (no broadening).

## Batch shape

Executions: kappa-etb-other-place (1 link). Rows: 1. Slots: 1.
Unique NEW-or-rewitness: 1 (currently UNKNOWN everywhere; no
rewitness declaration needed). Markers expected: 1.
