# Commander Simulator Next — Next Dependency Wave

Date: 2026-08-29

## Entry state

```text
INTEGRATION_COMPLETE                  = TRUE
INITIAL_ARCHITECTURE_DECISION_FROZEN = FALSE
READY_FOR_GREENFIELD_BUILD           = FALSE
FIRST_BLOCKING_GATE                   = Q6_ACTUAL_CARD_BEHAVIOR
PARALLEL_CROSS_BLOCKER                = FAILURE_SEMANTICS
SEQUENTIAL_BLOCKER                    = Q8_LICENSE_THIRD_PARTY
```

Do not create `moeendres-png/commander-simulator-next`.

## Canonical runtime evidence entering the next wave

- WS90 qualified runtime head/tree: `55820618e7243bd5ba8cfa33c3148cea8c166c73` /
  `3706900d49c6ef61690c227bb7b4c0067fbcfb44`.
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`.
- Integrated Q5/Q7-Forge run/job/artifact: `33250119165` / `99094251297` /
  `9714119110`, SHA-256
  `d5bdb8b59045c78c5c3774bac1f9091c7b32327834eea9abf106412452cdcb4c`.
- Q1/Q2/Q3/Q4/Q5 are PASS within the exact boundaries recorded in
  `WS90_INTEGRATION_ADJUDICATION.json`.
- Q6 is FAIL; Q8 is deferred; failure semantics are incomplete.

## WS11 — Actual-card semantic behavior closure

Create a separately owned branch from the final WS90 integration ref. Do not
reuse WS10's `Q6=PASS` criterion unchanged.

Required correction:

1. Remove global dependency inheritance as per-identity behavior evidence.
   A card with a decision/hidden/RNG path may cite WS01/WS05/WS06 as a required
   contract prerequisite, but that prerequisite cannot by itself set the card's
   behavioral flag to PASS.
2. Replace `dedicated_behavior_required = hard_suspicious_marker_present` with
   a rules/behavior reachability model. Absence of TODO/unsupported markers is
   not evidence that a card's semantics are correct.
3. Bind every one of the exact WS02 1,678 Oracle identities to executable
   semantic evidence. Mechanic/path-signature grouping is allowed only when the
   mapping from each identity to the exercised authoritative engine path is
   machine-readable and the shared path is itself semantically executed.
4. Verify at least the actual production-reachable behavior categories needed
   by the corpus: legal actions, costs/mana, targets, modes/choices, stack and
   priority, triggers, replacement/continuous effects, state-based actions,
   zones, combat, Commander rules, hidden-information transitions and RNG.
5. Per identity emit PRESENT, LOADABLE, EXECUTABLE, DECISION_COMPLETE,
   HIDDEN_INFO_SAFE, REPLAY_SAFE and BEHAVIOR_VERIFIED_WHERE_REQUIRED with
   evidence class and concrete run/trace binding. UNKNOWN is not PASS; PARTIAL
   is not FULL.
6. Construction-only evidence remains useful but cannot close behavioral Q6.
7. No card-name-specific production hacks. Repair systemic engine gaps.

Hard gate: Q6 may become PASS only when no production-required identity relies
on global-contract inheritance in place of actual semantic behavior evidence.

## WS12 — Unified failure-semantics contract

May run in parallel with WS11 on a separate branch with non-overlapping
ownership. Implement and qualify an integrated outcome model that distinguishes
at least:

`SUCCESS`, `PLAYER_CANCELLED`, `ACTION_NOT_COMPLETABLE`, `ILLEGAL_RESPONSE`,
`MALFORMED_RESPONSE`, `STALE_RESPONSE`, `WRONG_ACTOR`, `TIMEOUT`,
`UNSUPPORTED_DECISION_PATH`, `UNSUPPORTED_RULES_PATH`, `ENGINE_FAILURE`,
`TRANSPORT_FAILURE`, `PROCESS_FAILURE`, `REPLAY_DIVERGENCE`,
`HIDDEN_INFO_VIOLATION`, `CARD_BEHAVIOR_FAILURE`.

No technical failure may be coerced to cancel/pass/default. Add executable
negative tests and machine-readable evidence for each production-reachable
category.

## WS13 — Architecture-specific Q8 closure

Run only after WS11/WS12 have narrowed the actual candidate topology enough to
make the distribution/linkage/interop boundary concrete. Reuse WS03's exact
license inventory; do not repeat license discovery without a pin change.
Adjudicate the chosen topology explicitly and keep any legal uncertainty as
`LEGAL_REVIEW_REQUIRED`/non-PASS.

## Differential follow-up

Current Q7 is PASS only for its two selected shared scenarios. If WS11 exposes
any meaningful Forge/reference-engine divergence, adjudicate each divergence
against current official Magic rules; do not use engine majority as authority.

## Exact next action

Start WS11 and WS12 as separate workstreams from the final WS90 integration
HEAD, with fixed base SHA, file ownership and hard gates. Do not start a
production repository and do not freeze the architecture before both complete
and Q8 is subsequently closed.
