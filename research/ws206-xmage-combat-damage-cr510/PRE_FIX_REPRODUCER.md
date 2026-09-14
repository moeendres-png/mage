# WS206 Pre-Fix Reproducer

Status: PRE_FIX_REPRODUCER = BUG_CONFIRMED (defect proven on pinned base before fix;
the bug-demonstrating assertion shape is preserved in POST_FIX tests as reject-then-accept).

Test: `Mage.Tests/.../ws206/WS206TrampleReproducerTest.java`
(actual cards, native engine, strict choose mode).

- Attacker: Colossal Dreadmaw (6/6 trample), playerA.
- Blockers: Grizzly Bears (2/2) + Silvercoat Lion (2/2), playerB.
- Attempt: `setChoiceAmount(playerA, 4, 0)` => 4 to Bears, 0 to Lion, 2 through.
- Why it reaches the engine: lethal sum = 2+2 = 4 = totalMin, so
  `MultiAmountType.isGoodValues([4,0], min 0/max 6 each, total 4..6)` passes, even though
  Lion (0 < lethal 2) with positive through-damage violates CR 702.19b.

Pre-fix observed engine log (verbatim):

- `PlayerA using choice: X=4 (by setChoice, on multi amount)`
- `PlayerA using choice: X=0 (by setChoice, on multi amount)`
- `PlayerB loses 2 life at combat from Colossal Dreadmaw`
- `Colossal Dreadmaw deals 4 damage to Grizzly Bears`
- `Grizzly Bears died` (no damage ever assigned to Silvercoat Lion)

Pre-fix assertions that PASSED (illegal executed): Lion damage 0, defender life 18,
Bears graveyard 1, Lion survives. No rejection, no re-request.

Post-fix behavior of the same attempt: engine rejects (per-blocker lethal check with
through = 2 > 0 fails for Lion), informs the choosing player, and re-requests
(up to 5 attempts, then legal-by-construction fallback). With only the illegal choices
supplied, the test engine reports `Missing CHOICE def ... Multi amount: Assign combat
damage among creatures blocking Colossal Dreadmaw` — proof the first attempt did not
execute. The committed reproducer therefore supplies illegal-then-legal
`setChoiceAmount(playerA, 4, 0, 2, 2)` and asserts the legal retry executes
(both blockers die, defender at 18). POST_FIX: PASS.
