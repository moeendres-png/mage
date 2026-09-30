# XMage multiplayer candidate: integration of F-18 / F-19 / F-20 / F-21

Author: Claude Opus 5.5 (Claude Code), 2026-09-29.

- Coordinator authority: candidate integration and Lab repin workstream.
- This is **not** a Production Provider selection and **not** an Architecture Freeze.

## Source lock
- Base: the exact prior candidate pin `b19596980f2734496ea1896504253e1bdd2756dd` (tree `04c00f25`, head of Mage PR #16).
- Branch: `claude/xmage-mp-candidate-20260929`.

| Donor | Finding | Head | Integrated as |
|---|---|---|---|
| Mage PR #19 | F-18 Commander-zone SBA choices in APNAP order, applied together | `6044132ecde384997d23121a8622ed308f68ae5d` | merged unchanged |
| Mage PR #20 | F-19 Rhystic Study / Mystic Remora: payer decides first | `0962f0b5d5147f606b517501b384a225af9f646a` | merged unchanged |
| Mage PR #21 | F-20 initiative passes on when its holder leaves (CR 726.4; 726.2 controller) | `9ec76cc6a9833d739fa83675b3b38e780f72dd7c` | merged unchanged |
| Mage PR #22 | F-21 simultaneous each-player / each-opponent choices in APNAP order | `0082ad2983fc6d1b26f1d217e749cfc3a58d6c0b` | **not merged; bounded port** (see below) |
| branch `claude/f20r-apnap-choice-primitive-20260929` | bounded F-21 APNAP primitive | `e5729e7da708` | merged |

## Integration decisions
- **F-18 (#19) and F-20 (#21)** both touch `GameImpl.java`, in disjoint hunks: `checkStateBasedActions` vs `leave`. They merge automatically and their tests pass together.
- **F-20 (#21)** was verified against the CR text:
  - 726.4: "If the player who has the initiative leaves the game, the active player takes the initiative … If the active player is leaving the game or if there is no active player, the next player in turn order takes the initiative."
  - 726.2: the initiative's inherent triggers are controlled by the player who had the initiative when they triggered.
- **F-21 (#22), bounded correction.** Donor #22 redefined `Game.getOpponents()` globally to APNAP order. `getOpponents()` has a documented contract ("Use it to iterate by starting turn order") and hundreds of order-insensitive callers, so **it is kept unchanged**. Instead:
  - New primitive `Game.getPlayerIdsInApnapOrder()`: players still in the game, from the active player in turn order. It walks a copy of the static turn-order list with `PlayerList.getNext(game, false)`, which honours reversed turn order, skips players who left, and leaves the priority pointer untouched. This generalises the idiom Tempt with Reflections already uses.
  - New primitive `Game.getOpponentsInApnapOrder(playerId)`: the same, restricted to that player's opponents in range of influence.
  - Only demonstrated order-sensitive consumers, where several players choose simultaneously (CR 101.4), are migrated:
    - `SacrificeAllEffect`, both "each player" and "each opponent" (so `SacrificeOpponentsEffect`, e.g. Liliana's Triumph and Innocent Blood); range of influence is kept;
    - Grave Pact ("each other player", not only opponents; range kept);
    - the tempting-offer cards Tempt with Bunnies, Discovery, Glory, Immortality, Mayhem and Vengeance. Tempt with Reflections was already APNAP-correct.
  - Donor #22's native tests (`SimultaneousSacrificeApnap3-6P`) are carried unchanged and pass under the bounded design.
- **Not migrated (by design):** order-insensitive `getOpponents` consumers (counting, membership, symmetric application, set construction). About 70 card-local "each player sacrifices" loops that start from the controller are listed in donor #22's handoff. They are only wrong on another player's turn and are candidates for later, individually justified migration.

## Donor #22 versus the accepted bounded F-21 integration

| Donor #22 hunk (`0082ad2983fc`) | Disposition |
|---|---|
| `Game.getOpponents(playerId, excludeLeaved)`: stream changed from `getPlayerList()` to `getPlayersInApnapOrder()`, with a comment "101.4 … start with the active player" | **REJECTED.** `getOpponents` keeps its documented contract ("Use it to iterate by starting turn order") for all of its callers. |
| New `Game.getPlayersInApnapOrder()`: includes players who left; raw `getNext()`/`getPrevious()` | **REPLACED** by `Game.getPlayerIdsInApnapOrder()` (players still in the game, via `PlayerList.getNext(game, false)`) and `Game.getOpponentsInApnapOrder(playerId)` (plus range of influence). |
| `SacrificeAllEffect`: the all-players path switched to APNAP; the opponents path relied on the rejected global `getOpponents` change | **PORTED.** Both paths use the explicit primitives; range of influence is kept. |
| Grave Pact: APNAP order plus a range filter | **PORTED** onto `getPlayerIdsInApnapOrder()`, keeping "each other player" (not reduced to opponents). |
| Tests `SimultaneousSacrificeApnap{3,4,5,6}PTest` and base; `research/f21-apnap-simultaneous-choices/HANDOFF.md` | **ACCEPTED UNCHANGED** as acceptance evidence. All pass under the bounded design. |

Bounded F-21 commits: `e5729e7da708` (the primitive, six tempting-offer consumers, primitive and contract tests) and `5a82748823` (the `SacrificeAllEffect` / Grave Pact port plus donor #22's tests).

## Changed production files
- `Mage/src/main/java/mage/game/GameImpl.java` (F-18, F-20)
- `Mage/src/main/java/mage/designations/Initiative.java` (F-20)
- `Mage/src/main/java/mage/game/Game.java` (F-21 primitive only; `getOpponents` unchanged)
- `Mage/src/main/java/mage/abilities/effects/common/SacrificeAllEffect.java` (F-21)
- `Mage.Sets/src/mage/cards/g/GravePact.java` (F-21)
- `Mage.Sets/src/mage/cards/r/RhysticStudy.java`, `Mage.Sets/src/mage/cards/m/MysticRemora.java` (F-19)
- `Mage.Sets/src/mage/cards/t/TemptWith{Bunnies,Discovery,Glory,Immortality,Mayhem,Vengeance}.java` (F-21)

## Native evidence (combined source)
Targeted, with `mvn -o -pl Mage,Mage.Sets,Mage.Tests test -Dtest=…` (the patched core and sets built in the reactor; nothing installed):

| Suite | Result |
|---|---|
| F-18 `CommanderZoneApnap{3,4,5,6}PTest` | 12/12 |
| F-19 `UnlessThatPlayerPaysOrderTest` | 6/6 |
| F-20 `InitiativeLeavesGame{3,4,5,6}PTest` | 16/16 |
| F-21 donor `SimultaneousSacrificeApnap{3,4,5,6}PTest` | 20/20 |
| F-21 `EachOpponentApnap{3,4,5,6}PTest` (tempting offer, caster at three seats) | 12/12 |
| F-21 `ApnapOrderPrimitiveTest` (four active seats, non-active reference, reversed turn order, departed player, `getOpponents` contract regression) | 5/5 |
| F-21 `ApnapOrderRangeOfInfluenceTest` | 1/1 |

Full `Mage.Tests` on the combined source (`mvn -o -pl Mage,Mage.Sets,Mage.Tests test`): **7001 run, 0 failures, 0 errors, 125 skipped**, i.e. the pin baseline of 6929 run / 125 skipped plus exactly the 72 new tests. No new failures.

## Lab repin
The Lab pin moves to this branch's head (the commit adding this handoff). That repin is a separate Lab workstream with its own impact adjudication.
