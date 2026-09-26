# RG-06B — Rules Authority / Hidden-Information Analysis

- Governing Rules: CR 707 (face-down spells/permanents: no text, no name,
  2/2), CR 702.36 (morph turn-up as special action), hidden-information
  principle (face-down identity concealed; actions must not name it).
- Engine behavior is evidence, not authority; the assertions above bind the
  required Rules-visible facts: placeholder name, 2/2, morphed flag, silent
  playable surface, working turn-up, zero revealed cards.
- Hidden-info proof (test `restoredMorph...`, post-start observation):
  `game.getState().getRevealed().size() == 0` and no `getPlayable` entry from
  the restored source names "Akroma". Face-up-only ability TEXT is likewise
  absent from the offered surface (the pump rule never appears).
- Unsupported mixed Manifest/Cloak-over-Morph/Disguise restoration remains
  fail-closed in the seam (unchanged code) and is covered by the inherited
  `invalidFaceDownRestoreFailsBeforeMutation` regression (green).
- No second face-down model, no bridge/pilot filtering, no suppression logic
  added anywhere. The native invariant (ID-based `AbilitiesImpl.contains`
  removal) already enforces the Rules shape.
