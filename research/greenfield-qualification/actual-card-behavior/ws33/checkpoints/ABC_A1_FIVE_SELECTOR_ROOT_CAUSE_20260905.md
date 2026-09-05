# WS33 ABC-A1 — five omitted TargetRestrictions selectors root cause

Date: 2026-09-05

Evidence classes: authoritative manifest extraction `DIRECTLY_VERIFIED`; pinned Forge card/source and combat API inspection `DIRECTLY_VERIFIED`; repair design `CODE_DERIVED` until executed.

## Common root cause

All five A1 omissions are valid `ACTION_COST_DECISION / TargetRestrictions / DECISION+REPLAY` paths in the authoritative 4188 model. They were excluded solely because `ws33_prepare_target_campaign.py` has a conservative `SUPPORTED` fixture mapping that does not yet contain their valid target selector strings.

This is a qualification campaign fixture-coverage gap, not evidence of a Forge Rules Core failure and not a model-identity defect.

## Five exact paths

1. `forge-behavior-v2:01655eb4cda1ef1a652a0c085ee7241a5ae241a7`
   - source: `Doctor Doom, King of Latveria`
   - `ValidTgts$ Villain.YouCtrl`
   - pinned Forge source declares the card itself `Legendary Creature Human Noble Villain`.
   - generic fixture: source-bound controlled creature may be selected only if Forge exposes it as authoritative legal target.

2. `forge-behavior-v2:067bdc7754cc85e926900f11e4f1969088cf6da1`
   - source: `Crossbow Infantry`
   - `ValidTgts$ Creature.attacking,Creature.blocking`
   - generic fixture: a real battlefield creature is placed into Forge `Combat` as an attacker using `Combat.addAttacker(card, defender)` and `PhaseHandler.setCombat(combat)`.

3. `forge-behavior-v2:09094286f77af4af8bafe7e1e1101a00c1ad0571`
   - source: `Speed, Young Avenger`
   - `ValidTgts$ Creature.withHaste`
   - pinned Forge source gives the source card `K:Haste`.
   - generic fixture: source-bound controlled creature may be selected only when Forge exposes it as legal.

4. `forge-behavior-v2:0b34a03cf5d6174eb0eda60cd4f97abde7581ad7`
   - source: `Make Your Move`
   - `ValidTgts$ Creature.powerGE4,Artifact,Enchantment`
   - generic fixture: actual `Air Elemental` (4/4) on the opponent battlefield exercises the creature-power branch of the union; Forge remains authority for validity.

5. `forge-behavior-v2:11dd247b928074ba858ba4d44aec905d2a69fb6a`
   - shared selector from multiple actual cards
   - `ValidTgts$ Creature.attacking`
   - generic fixture: same real Forge combat-attacker setup.

## Engine API basis

Pinned Forge `Combat` exposes `addAttacker(Card, GameEntity)` and updates attacking state. Forge test/source patterns establish combat via `new Combat(attackingPlayer)`, `combat.addAttacker(...)`, then `game.getPhaseHandler().setCombat(combat)`.

## Repair constraints

The repair may extend only generic qualification fixture roles/selectors:

- source creature satisfying a source-owned subtype/keyword selector;
- actual combat attacker satisfying combat-state selectors;
- actual power-4 creature satisfying a power-filter union.

The pilot must still choose only a semantic option present in Forge's authoritative request. No card/path-ID production branch, no direct effect resolution, no legality emulation, no silent fallback, and no coverage mutation is permitted.

`ABC_A1_FIVE_SELECTOR_ROOT_CAUSE=CAMPAIGN_FIXTURE_CATALOG_GAP`
`FORGE_RULES_CORE_DEFECT=NOT_ESTABLISHED`
`REPAIR_ELIGIBLE=TRUE`
`COVERAGE_PROMOTION=FALSE`
