# RG-06B — Root Cause (adjudicated: no engine defect)

## Claimed defect

A permanent restored as Morph via `restoreFaceDownStateForGameLoad` exposes
or executes face-up-only activated abilities through `getPlayable`, while a
naturally established Morph does not.

## Traced call chain (exact)

1. `BecomesFaceDownCreatureEffect.restoreFaceDownStateForGameLoad`
   (`Mage/.../continuous/BecomesFaceDownCreatureEffect.java:246`) validates,
   reuses the card-native morph blueprint, then calls
   `makeFaceDownObject(game, sourceId, permanent, MORPHED, additionalAbilities)`.
2. `makeFaceDownObject` (:384) renames to the face-down placeholder, clears
   types/color, then partitions `object.getAbilities()`:
   - abilities also present in `game.getCard(id).getAbilities()` proceed;
   - `worksFaceDown` ones are kept (rule hidden);
   - all others land in `abilitiesToRemove` →
     `permanent.removeAbilities(...)` (identity via `isSameInstance`).
3. `getPlayable` (`PlayerImpl.java:4290` → `:4306`) sim-copies the game and
   enumerates battlefield permanents' abilities with NO face-down exemption —
   so any ability still present WOULD be offered. Suppression therefore lives
   entirely in step 2's removal.
4. The membership test in step 2 is `AbilitiesImpl.contains` (:243), which is
   ID-based (`getId()`/`getOriginalId()` equality, plus MageSingleton rule
   fallback) — NOT Java instance identity. Permanent ability copies preserve
   IDs (`AbilityImpl` copy constructor), so own abilities match and are
   removed; genuinely gained abilities (equipment/auras, differing IDs) are
   kept, as intended.

## Why the two states do NOT diverge

- Restored morph: removal verified empirically 8 → 3 abilities (Akroma), all
  non-face-down own abilities gone including the `{R}` pump; `getPlayable`
  (both hidden flags, duel + commander games, pre- and post-start) offers
  nothing from the restored source.
- Natural morph: `PermanentCard` construction with `faceDown=true` filters via
  `copyFromCard` to `worksFaceDown` only — same end state (2/2, turn-up +
  info abilities), same clean `getPlayable`.
- Both converge: placeholder name, 2/2, morphed flag, 3 abilities, silent
  playable surface, normal genuine turn-up (Sagu 6/6 pre-existing; Akroma
  6/6 + pump-offered added in RG-06B).

## The vacuous RED explained

`permanent(game, "Akroma, Angel of Fury")` inside `runCode` runs AFTER the
rename to the face-down placeholder, so name lookup throws. The RED proved
only fixture invalidity. Repaired via captured native UUID
(`game.getPermanent(id)`).

## Adjudication

No systemic engine divergence exists on this baseline for this mechanism.
The Lab-observed "3/2 pump" could not be reproduced through any faithful
native path; probable Lab-harness artifact (label-substring offer matching
without source-identity binding, or a refused-restore face-up offer
misread — the Lab guard leaves Akroma face-up, where the pump is
legitimately offered). Lab-side re-examination is recommended in the later
Lab re-pin workstream; the Lab `ACTIVATED_ABILITY_PRESENT` guard stays as
harmless defense-in-depth and is NOT removed by this (engine-only) stream.

No production fix is warranted. Authoring one would violate the hard gate
against modifying production code merely to affect a test run.
