# F-22 / F-23 XMage multiplayer candidate successor

## Source Lock
- Parent candidate: `f79e4168902e65063034b21be6f4585397fd43b3`
- Parent candidate tree: `18c3e8e7588627b22accc08a644729399d702ee3`
- Branch: `sol/xmage-f22-f23-successor-20260929`

## Work Completed
- F-22: battle protector state-based action now treats a protector who left the game as unsuitable and re-runs the engine's native protector choice.
- F-23: the ordinary `Game.getOpponents(playerId)` contract now returns only opponents still in the game.
- The explicit `getOpponents(playerId, false)` overload is retained for engine code that deliberately needs the turn-start range snapshot.
- VoteHandler and Myriad explicitly exclude players who left because they enumerate players-in-range directly rather than through `getOpponents`.

## Rules Authority
Verified against Wizards Comprehensive Rules:
- 310.11 / 310.12a: an unsuitable Siege protector is replaced by its controller as a state-based action; Siege protectors must be opponents.
- 800.4: a player leaves the game immediately; subsequent gameplay treats only players still in the game as participants/opponents, while rule 800.4 contains explicit LKI/choice exceptions.
- 801.2c explains why XMage retains a turn-start range snapshot; that snapshot is preserved only behind the explicit boolean overload.

## Tests / Evidence Included
Actual-card regressions:
- Invasion of Zendikar — protector leaves, new protector chosen, battle remains attackable.
- Inspired Sphinx — opponent counts at 4P and 5P after one/two opponents leave.
- Beza, the Bounding Spring — departed high-life player no longer satisfies an opponent comparison.
- Warchief Giant (myriad) — no token/decision for a departed opponent.
API contract regression:
- default opponent query excludes a departed player while explicit `false` snapshot access remains available.

Council's Judgment voting is additionally covered by the Commander Lab regression already merged there and will be enabled by the Lab repin successor.

## Evidence Status
Code and tests are committed through the GitHub connector. No local Maven runtime was available in this connector-only execution environment. Runtime status remains NOT_RUN until GitHub Actions / downstream candidate qualification executes these exact bytes.

## PASS / FAIL / UNKNOWN
- CODE_DERIVED: F-22 and F-23 fixes implemented on the exact current candidate parent.
- RUNTIME_VERIFIED: UNKNOWN pending CI.
- EXTERNALLY_RULE_VALIDATED: the relevant current Wizards rule text was checked; runtime behavior still requires tests.
- Architecture Freeze: NOT CLAIMED.
- Production Provider: NOT SELECTED.

## Exact Next Action
Run candidate CI / Mage.Tests on this exact head. If green, consume the exact successor head in Commander Lab, re-enable the F-22/F-23 bridge regressions, repin, and perform impacted qualification.
