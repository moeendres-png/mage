# WS83 Root Cause (systemic, CODE_DERIVED + DIRECTLY_VERIFIED behavior)

Symptom (DIRECTLY_VERIFIED pre-fix): with Humility pre-existing, casting Clone reaches
`EntersBattlefieldEffect.replaceEvent` optional prompt "Use effect of Clone? Yes/No"
(`WS81H01CorrectedTest.testA` strict-mode `Missing CHOICE def`, 3 run / 1 failure).

Call chain: Spell resolve -&gt; ZonesHandler zone-change gate + `permanentsEntering` blueprint +
`permanent.entersBattlefield` SELF then OTHER `game.replaceEvent` -&gt;
`ContinuousEffects.replaceEvent` -&gt; `getApplicableReplacementEffects` admits Clone effect -&gt;
`EntersBattlefieldEffect.replaceEvent:101 chooseUse` (proven symptom location, not repair location).

Systemic defect: `ContinuousEffects.getApplicableReplacementEffects` (Mage/.../ContinuousEffects.java:354-391)
is the earliest authoritative applicability boundary and implements no CR 614.12 future-state check.
It tests event type, dedup, useable-zone (entering shortcut always true), used, scopeRelevant/selfScope,
and per-effect `applies` (target==source + condition only). It never asks whether the source ability
would exist on the battlefield future state after pre-existing continuous effects.

Compounding provenance: `ReplacementEffectImpl:14-24` quotes the outdated 614.12 phrasing
("ignoring continuous effects from any other source"); current authority expressly includes
"continuous effects that already exist and would apply." XMage therefore models the old rule:
entering Clone never appears in `Battlefield.field` during `entersBattlefield`, so Humility's
layer-6 loop (`getActivePermanents`, Humility.java:67-68) never strips it pre-entry, and
`hasSourceObjectAbility`/`isInUseableZone` still report the copy ability present.

Class: ENGINE_DEFECT (shared, provider/harness-agnostic; TestPlayer only surfaces it).
Not card-specific: any self-scope entering replacement (Clone, Phantasmal Image, Vesuva tapped/copy,
Adaptive Automaton subtype, etc.) under any pre-existing global layer-6 `LoseAbility` remover
(Humility custom effect, Dress Down generic LoseAllAbilitiesAllEffect, etc.) takes the same path.
Over-broad alternatives rejected: card-name/Humility strings, H01 branches, blanket copy disable,
prompt-result injection, provider/harness compensation, parallel future-state engine, duplicated
layer semantics in Clone/CopyPermanentEffect/tests/adapters.

Repair direction (implemented): evaluate self entering replacements at the earliest systemic boundary
by reusing each active layer-6 `LoseAbility` effect's own `apply` filter logic against the entering
permanent temporarily exposed to battlefield queries; suppress only when the entering ability would
be removed. Targeted/fixed-set removals cannot match an entering object they were never set for;
global removers match only entering objects satisfying their own filter (creature vs land).
Fail-closed toward existing behavior on any evaluation problem; reentrancy-guarded.
