# WS33 ABC — Direct31 run 34047683558 — mana payment root cause v2

Classification: **DIRECTLY_VERIFIED + CODE_DERIVED**
Current blocker class: **PAYMENT_LIFECYCLE_UNKNOWN**
Forge Rules Core defect: **NOT PROVEN**
Pilot hidden mana-rules defect: **NOT IMPLEMENTED / NOT PERMITTED**
Coverage promotion: **FALSE**

## Runtime facts

Run `34047683558` left exactly three record failures: Disperse, Buried Ruin, River's Rebuke. Every pre-cost stage including Forge `setupTargets()` and stack legality returned true; only full `CostPayment.payCost(...)` returned false.

The before-state evidence for all three failures still contains at least ten actor-controlled copies each of Plains, Island, Swamp, Mountain and Forest on the battlefield. The failure is therefore not explained by loss of the seeded colored-land resource pool.

## Exact MANA_PAYMENT source contract

The exact WS01 source consumed by Direct31 applies `apply-ws01-mana-convoke-bridge.py` through `apply-strict-decision-boundary.sh`.

`InputPayMana.driveExternal()` constructs authoritative transitions as follows:

- floating-mana options are included only when `meetsManaRestrictions`, `allowsPayingWithShard` and `manaCost.isNeeded(...)` are all true;
- mana-ability options are included only when Forge `isManaAbilityFor(saPaidFor, colorCanUse)` is true;
- life is emitted only when Forge determines the life alternative is currently available;
- each selected option is revalidated by Forge immediately before application;
- stale or unknown actions throw fail-closed `ExternalDecisionValidationException`;
- AI mana autopay is explicitly forbidden in external mode.

The request mapper passed to `chooseExternalUiOptions` is `value -> value`, so server-side semantic values are the Forge-owned action tokens (`POOL:n`, `ABILITY:n`, `LIFE`, `CANCEL`). The retained DecisionTape intentionally records opaque option IDs instead of this semantic context.

Therefore the qualification pilot does **not** need and must not implement mana legality. The authoritative input already owns immediate transition filtering.

## Remaining uncertainty

The three runtime failures do not throw `ILLEGAL_OPTION`; instead the enclosing `CostPayment.payCost(...)` returns false after accepted `MANA_PAYMENT` requests. It is not yet known whether:

1. an accepted mana ability fails to advance the remaining `ManaCostBeingPaid` state as expected;
2. `InputPayMana` reaches a terminal state that the enclosing cost-payment lifecycle does not accept;
3. another non-mana cost component fails after mana payment (relevant especially to Buried Ruin, but cannot explain the two ordinary spells by itself);
4. another production lifecycle interaction exists.

## Next diagnostic

Add qualification-only, observation-only telemetry inside the already installed `InputPayMana.driveExternal()` path. For every external payment iteration retain:

- source spell/ability identity;
- remaining `ManaCostBeingPaid` string before and after the transition;
- authoritative action tokens emitted by Forge;
- selected server-mapped action token;
- selected mana-ability host and id where applicable;
- `isAlreadyPaid()` state before/after.

The observer must not alter option construction, selection, mana state, cost state, or any boolean return value. Persist the next run PENDING immediately after registration and freeze its source until terminal.
