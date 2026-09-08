# WS33B B1 — fail-closed default evidence: adjudication note

Status: REVIEW_REQUIRED_DEAD_EXPRESSION (independent adjudication).
Branch: work/ws33-b-high-throughput-20260907.
Scope: 6 of 273 B1 calculateAmount paths whose production evaluation yields
the engine's fail-closed default (0) because the scripted expression has no
matching production branch in pinned Forge
(8c7e9afb8e6caee88644b94e25da5852e36f8928).

## Paths

1. Kemba's Legion — X = Count$Valid Equipment.Attached
   - `ZoneType.listValueOf("Equipment.Attached")` parses to an empty zone
     list (no zone token matches), so `game.getCardsIn([])` is empty and the
     count is 0 even with an Equipment attached via production
     `attachToEntity`. Verified by execution (attached Lightning Greaves,
     engine returned 0). No exception; fail-closed default.
2. Estinien Varlineau x2 — X = PlayerCountRegisteredOpponents$HasPropertywasDealtCombatDamageThisTurnBy Card.Self,Dragon GE1
   - No production branch matches property
     `wasDealtCombatDamageThisTurnBy...` (zero matches in forge-game and
     forge-gui sources); the unknown-property tail returns false for every
     player, so the count is 0. Verified by execution.
3. Exsanguinate / Hoarder's Greed — AFLifeLost / CheckRepeat = Number$0
   - Script default with no payment link in the SVar; production
     `xCount` Number branch yields 0. Verified by execution.
4. Inferno Trap — CreaturesDmg = Count$NumDamageThisTurn Creature You
   - No production xCount branch matches `NumDamageThisTurn`; the generic
     zone assembly finds no zone tokens and yields 0. Verified by execution.

## Evidence treatment (proposed)

Each record carries `evidence_class = TECHNICALLY_CONFORMANT` (not
EXTERNALLY_RULE_VALIDATED) plus `default_zero_evidence = true` and
`review_required = DEAD_EXPRESSION`. Decision/RNG/hidden/replay evidence
is complete and identical in shape to the other 267 paths. The zero is the
verified actual engine behavior, not an injected outcome.

## Question for independent adjudication

Whether fail-closed-default evidence qualifies these 6 paths for coverage
promotion, or whether they must remain UNKNOWN until (a) engine support for
the expressions exists, or (b) a negative-evidence (fail-closed) path
qualification is defined. This worker does NOT self-authorize their
promotion: the B1 gate records the flag, and any successor promotion must
explicitly adjudicate it.

## Classification

CODE_DERIVED (source reads) + DIRECTLY_VERIFIED (executed engine outcomes
in B1 record/replay). No engine source was modified for these paths.
