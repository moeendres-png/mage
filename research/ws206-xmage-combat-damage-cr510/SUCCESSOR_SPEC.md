# WS206 Commander-Lab Successor Spec (NOT executed in WS206)

Goal: qualify a repinned Lab against the WS206 engine candidate without reopening
WS205 or mutating WS204 artifacts.

1. Repin: set the Lab successor's XMage pin to the exact WS206 candidate commit
   (the commit produced by this workstream on
   ws206/xmage-combat-damage-cr510-hardening-20260914; record SHA + tree at successor start).
2. Preserve WS204 generic action semantics: no Lab-side combat-legality workaround;
   Lab continues to decide only discretionary numeric values through the generic
   `multi_amount` path.
3. Prove reachability: drive an actual-card multiple-blocker combat (e.g. 6/6 trample
   vs 2/2 + 2/2) through generic `legal_actions` / `action_submission` and show the
   engine prompts the `getMultiAmountWithIndividualConstraints`-backed multi-amount
   dialogue for the attacker's damage division (log the dialogue title/header +
   per-option bounds + totalMin/totalMax).
4. Behavior matrix via generic submission: legal lethal-each-plus-through executes;
   legal zero-through free distribution executes; illegal blocker-below-lethal plus
   positive through is rejected/re-requested engine-side (illegal values never
   materialize as damage), with a corrected retry accepted.
5. Regressions: rerun affected WS204 cases plus D1-D5 that touch combat or
   multi-amount choice; record PASS/FAIL/UNKNOWN per case with no unrelated reopening.
6. Out: repin qualification report (PASS/FAIL/UNKNOWN + evidence), owned by the
   successor workstream. WS206 itself performs no Lab execution.

CONCESSION successor (bounded recommendation only, still OUT_OF_SCOPE here): if a
concession path is still desired, a later workstream should specify it against
CR 104.3a as a game-level action with state-based handling, isolated from combat
damage assignment, with its own reproducer and regressions. Not designed further here.
