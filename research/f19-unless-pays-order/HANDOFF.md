# F-19: "you may draw a card unless that player pays {N}": payer decides first

Commander Simulator Next tracker: moeendres-png/commander-playtest-lab#323.
Author: Claude Opus 5.5 (Claude Code), 2026-09-29.

## Source lock
- Base: the exact candidate pin `b19596980f2734496ea1896504253e1bdd2756dd` (head of Mage PR #16). Not master; upstream master has the same defect.
- Authority: official Oracle and rulings (Scryfall, 2026-09-29), Rhystic Study:
  - "The player gets the option to pay when this triggered ability resolves."
  - "You don't have to decide whether or not to draw a card until after the player decides whether or not to pay."

## Defect
`RhysticStudyDrawEffect` and the Mystic Remora draw effect asked the controller "Draw a card?" first, and asked the opponent "Pay {N}?" only if the controller said yes. The payer therefore learned the controller's intent, and the payment decision was skipped whenever the controller declined.

## Fix (card-local, both cards)
- The opponent is asked first, and only if the cost can be paid (`canPay`, as in the engine's own `DoUnlessTargetPlayerOrTargetsControllerPaysEffect`).
- If they pay, nothing more happens.
- Otherwise the controller decides whether to draw.

## Native evidence
- `Mage.Tests` `org.mage.test.multiplayer.UnlessThatPlayerPaysOrderTest`: 4 players, and the paying opponent C is not the active player.
- Six scenarios:
  - Rhystic Study, C pays: A is never asked and doesn't draw.
  - Rhystic Study, C declines and A draws.
  - Rhystic Study, C declines and A declines.
  - Rhystic Study, C is willing but unable (their only Mountain paid for Shock): A still decides and draws.
  - Mystic Remora, C pays {4} first.
  - Mystic Remora, C declines and A draws.
- A recording player asserts the exact question order.
- Results:
  - red on the pin: 6/6 fail;
  - green with the fix: 6/6;
  - `org.mage.test.multiplayer` package with the patched `Mage.Sets`: 75/75.
- No other test or code references the two changed effect classes.

## Not done here
- No Lab repin. Lab `XmageMultiplayerUnlessCostTest` keeps its disabled payer-first expectation until a repin admits this commit.
