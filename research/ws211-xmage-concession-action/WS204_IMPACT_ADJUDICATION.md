# WS211 WS204_IMPACT_ADJUDICATION

WS204_CONCESSION_BLOCKING_CALLBACK_REMEDIATION =
SUPERSEDED_BY_FRESH_ARCHITECTURE_ADJUDICATION.

- WS204 correctly identified that Commander-Lab could not lawfully fabricate
  concession as an external action and failed closed at the bridge. That
  holding stands.
- WS204's proposed engine remediation (blocking discretionary hook,
  `decision_class=concede` Yes/No) is NOT adopted. Fresh inspection at the
  WS206 terminal source proves concession is already a queued anytime
  player-initiated action (`concede`/`setConcedingPlayer`/`concedingPlayers`
  game-thread processing); a blocking prompt would distort CR 104.3a/723.6
  semantics. The correct surface is the availability predicate +
  existing native execution, delivered by WS211.
- No fake prompt, pilot, adapter, or test-helper legality was created.

WS204_BRIDGE_SIDE_CONCESSION_BLOCK = VALID_AT_WS204_SOURCE.

- The Lab bridge correctly refused to invent the action. WS211 unblocks it
  via the Lab successor spec (LAB_SUCCESSOR_SPEC.md), which WS211 does not
  execute. WS204 itself is not rewritten.
