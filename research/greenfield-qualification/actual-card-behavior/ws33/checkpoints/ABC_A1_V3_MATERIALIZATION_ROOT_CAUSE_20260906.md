# WS33 ABC-A1 — v3 materialization root cause

Date: 2026-09-06

## Boundary

Run `33985683468` failed closed after the authoritative 4188-model, exact A1 queue, pinned Forge, retained runtime overlays, and ten-shape fixture extension all passed. Record/Replay did not execute.

The immutable run artifact (`9975099085`, digest `sha256:3c0213abaead8918dd4480662b8efba8abddaab64912abe7e8110cf5f61ba104`) contains the authoritative successor manifest used by the run. Direct inspection resolves the five missing A1 IDs as follows:

| path | actual Forge source | `ValidTgts` |
|---|---|---|
| `forge-behavior-v2:2bf2f0d5c2d61940587e2c2fa31ee9f60cdec6ca` | `profane_command.txt` | `Creature.YouCtrl+cmcLEX` |
| `forge-behavior-v2:2f3d57f249c9fa37e8dc3f64df7d54d72324c03c` | `devout_decree.txt` | `Creature.Black,Planeswalker.Red,Creature.Red,Planeswalker.Black` |
| `forge-behavior-v2:315d6b9ec71c42854f97cf459af32690efa5429e` | `sevinnes_reclamation.txt` | `Permanent.cmcLE3+YouCtrl` |
| `forge-behavior-v2:373ca7a7eec7d46a5a04f8bcc1a1eb703e31fe04` | `thancred_waters.txt` | `Permanent.Legendary+Other+YouCtrl` |
| `forge-behavior-v2:4a2633aaa9053346a7cc99621ffc78d4d77620a2` | `execute.txt` | `Creature.White` |

All five have `implementation_target = forge.game.spellability.TargetRestrictions`, owner `ACTION_COST_DECISION`, and require Decision + Replay evidence but no Hidden-Info or RNG evidence.

## Root cause

The conservative qualification campaign preparer did not yet map these five valid selector shapes to fixture roles. This is a `QUALIFICATION_CAMPAIGN_MATERIALIZATION_GAP`, not a Forge Rules Core failure.

No production rules behavior needs to be changed. The systemic qualification repair is to extend the selector-shape catalog only:

- `Creature.YouCtrl+cmcLEX` -> existing own zero-CMC creature graveyard fixture (`Ornithopter`), allowing Forge's own X/CMC predicate to decide legality;
- four-way black/red Creature/Planeswalker union -> black creature fixture (`Walking Corpse`);
- `Permanent.cmcLE3+YouCtrl` -> existing own artifact fixture (`Sol Ring`) with the preparer's authoritative graveyard context;
- `Permanent.Legendary+Other+YouCtrl` -> own legendary-permanent fixture (`Isamaru, Hound of Konda`), distinct from source;
- `Creature.White` -> white creature fixture (`Isamaru, Hound of Konda`).

The chosen card scripts were directly verified at Forge pin `8c7e9afb8e6caee88644b94e25da5852e36f8928`: `Walking Corpse` is `Creature Zombie` with mana cost `1 B`; `Isamaru, Hound of Konda` is `Legendary Creature Dog` with mana cost `W`.

The external pilot remains unable to select anything unless Forge emits the object in authoritative legal options. No path-ID or card-name production branch is introduced.

Evidence classes:

- successor manifest path resolution: `DIRECTLY_VERIFIED`
- source-script selector values: `DIRECTLY_VERIFIED`
- root cause: `CODE_DERIVED`
- proposed fixture extension: `MODELED` until fresh execution

`ABC_A1_V3_ROOT_CAUSE=QUALIFICATION_CAMPAIGN_MATERIALIZATION_GAP`
`ABC_A1_RULES_CORE_DEFECT=FALSE`
`ABC_A1_COVERAGE_PROMOTION=FALSE`
