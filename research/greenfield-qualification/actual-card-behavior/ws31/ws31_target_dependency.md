# WS31 target-selection dependency

WS31 does not implement target legality or target choice in its Hidden/RNG/Replay owner.

At the pinned WS01 strict external-decision boundary, `PlayerControllerHuman.chooseTargetsFor(SpellAbility)` explicitly rejects `TARGET_SELECTION` when an external decision provider is active. Therefore any WS31 path whose exact source ability uses targeting remains dependent on an ACTION_COST_DECISION-owned authoritative target-option adapter.

The WS31 qualification harness must not replace that missing adapter with `SpellAbility.canTarget(...)` scanning or any first/default target policy. Such scanning is retained only as historical diagnostic code and is not admissible for a PASS witness.

The dependency is considered closed only when the consumed prerequisite exposes the rules-core-produced legal target option set through the strict external decision request/response contract with zero silent fallbacks.
