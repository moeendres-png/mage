# WS33-C Batch-4 SELECTION (Effect-static vocabulary premiere)

SOURCE_HEAD = (frozen at commit; see PENDING)
SOURCE_TREE = (frozen at commit; see PENDING)
FORGE_PIN = 8c7e9afb8e6caee88644b94e25da5852e36f8928
PARTITION = 11 EVIDENCED / 689 UNKNOWN
INVENTORY = WS33_C_EFFECT_STATIC_INVENTORY.json sha256 65aebfd9766722516c5aaaca5bdf8bd675e6e99f6d68784f14b3c4890870483a (23 rows)
BATCH_DIGEST = TBD (filled after preparer run, before commit)

## Chosen assertion primitive

`effect_static_present`: counts Command-zone effect cards carrying a
matching static (mode-contains and/or has-param) with the fixture source
object in remembered linkage. Pure engine-state observation (verified
against EffectEffect.resolve + Card/StaticAbility/CardTraitBase APIs at
FORGE_PIN): no layers computed, no legality reproduced, no outcome
injected. Optional `after_eot_absent` second phase re-evaluates the same
observation as count==0 after real EOT travel (rollback proof where the
lifetime ends this turn).

## Selected paths (3 NEW)

1. forge-behavior-v2:634a4b2d09d12a138afd0544c87c7d2bdb57a05a
   Kappa Cannoneer TrigPutCounter->DBUnblockable (sub-link).
   Provenance: forge-gui/res/cardsfolder/k/kappa_cannoneer.txt:8.
   Fixture ETB_OTHER_ENTER (Sol Ring enters; Kappa pre-placed via move,
   setup drain). Assertions: kappa P1P1==2 + effect_static_present
   (CantBlockBy/linked/1, after_eot_absent).
2. forge-behavior-v2:998516b92a13efe9c0e1c324a8123069ab954815
   Terminal Unblockable root, shared x5 (Kappa:9, gateway:6, ...).
   Fixture A (kappa-etb): Kappa ETB_SELF (self-entry fires own trigger;
   setup drain) — same execution as (1), second link.
   Fixture B (gateway-etb-other): Sneak pre-placed via move + Gruul
   Guildgate enters via moveTo. Assertions: effect_static_present
   (CantBlockBy/linked/1, after_eot_absent).
3. forge-behavior-v2:2dd428f906c3201282d1e251a9daf937f3413b94
   Terminal MayPlay root (Hildibrand dies). Fixture: Hildibrand via-move
   + Thunder ETB (DamageAll outlet; thunder's own path already evidenced,
   not claimed). Assertions: hildibrand-graveyard==1 +
   effect_static_present (Continuous+MayPlay/linked/1, no after-phase:
   lifetime UntilTheEndOfYourNextTurn exceeds window; rollback machinery
   is card-independent, proven on (1)/(2)).

## Expected before/active/after semantics

- BEFORE: no Command effect card remembering source with the static
  (asserted count==0 pre-resolution? No — pre-state asserted implicitly:
  fresh game has empty Command zone; post-resolution count==1 proves
  creation. Documented, not separately asserted to avoid vacuous checks...
  actually command zone COULD hold prior effects in multi-execution runs?
  Each execution is a FRESH game (initAndCreateGame per execution), so
  Command starts empty. The count==1 assertion subsumes before/after
  creation proof. AFTER (EOT): count==0 re-asserted where lifetime ends.)
- ACTIVE: count==1 + mode/linkage match.
- AFTER_REMOVAL: Kappa/Gateway via EOT travel (same turn); Hildibrand
  documented beyond-window (generic rollback machinery, proven on Kappa).

## Profiles / obligations

All three: template-113, STATE_ONLY flags (no decision/hidden/RNG/replay
required by model). Runtime tripwire + static screen + postconditions per
established contract. Forced-choice bundles: none expected (no controller
consultations in these chains; any non-incidental hit fails closed).
Direct-child negatives retained (predicate + object, green in-run).
Source seal + hash sealing as established.

## Excluded candidates/reasons (inventory classes)

- 11 COST_OWNERSHIP_BLOCKED (SP/AB cast or cost surfaces).
- 5 TARGET_DECISION_COLLISION (ValidTgts first links; template-107 scope).
- 2 HIDDEN_RNG_SEARCH_REVEAL_BLOCKED (Dig/choice/hidden).
- 2 COMBAT_BLOCKED (willie UnlessCost+combat; klaw cast/combat triggers).
- Mechanized DBWin: win-special vacuous semantics.
- Lux/serene/estinien phase rows: unmeetable/vacuous (prior analysis).
- Gateway shares Kappa's terminal (diversity slot, no new count).

## Batch shape

Executions: kappa-etb-other (2 links), gateway-etb-other (1 link,
shared), hildibrand-dies (1 link). Rows: 4. Slots: 4. Unique NEW: 3.
Markers expected: 3.
