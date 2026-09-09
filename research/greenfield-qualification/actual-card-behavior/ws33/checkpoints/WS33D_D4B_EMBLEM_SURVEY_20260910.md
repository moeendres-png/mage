# WS33-D D4b emblem/loyalty-setup survey — Tezzeret / Elspeth / Chandra

Date: 2026-09-10. Branch: `work/ws33-d-high-throughput-20260907`.
Source lock reverified (DIRECTLY_VERIFIED): HEAD
`9ef8f05aae2d11508cf51188d4ea5c9f377fef0e`, TREE
`f87d845da65dbb0072f2ea444cbc300dc80b2031`, clean, == origin.
`TASK_COMPLETE=NO`. `TURN_STATUS=RUNNING`. No run registered; no D4b
machinery built yet. Retained D4a evidence rechecked and valid (no rerun):
PASS checkpoint `ABC_D4_RUN_34411858516_PASS.md` present; live GitHub run
34411858516 conclusion success; witness source 94c37c2e; artifact
10127673535; ZIP sha256 `53b58d09…` reproduced in that checkpoint.
D-local partition: EVIDENCED=33 / REMAINING_UNKNOWN=887 (machine-counted).

## 1. Exact candidate rows (DIRECTLY_VERIFIED against ledger + pin scripts)

All three are `ws33-g2-template-049 / STATE_ONLY / EffectEffect`,
ledger `current_status=UNKNOWN`, not in partition-evidenced (33):

- Tezzeret: `forge-behavior-v2:0006052e09b51b869879f3a7741fcc1e5e24905e`
  `tezzeret_betrayer_of_flesh.txt` line 11 `AB$ Effect`,
  `Cost$ SubCounter<6/LOYALTY>`, `Ultimate$ True`,
  `Name$ Emblem — Tezzeret, Betrayer of Flesh`,
  `Triggers$ ArtifactDraw` (`Mode$ Taps | ValidCard$ Artifact.YouCtrl |
  TriggerZones$ Command | Execute$ TrigDraw Draw 1`). Printed loyalty 4.
  Other lines: +1 Draw2-discard2-unless-artifact (Mode TgtChoose,
  decision-gated), -2 Animate (target artifact, wrong direction).
- Elspeth: `forge-behavior-v2:2d5a6d01c9dffdcafb413c849eb685e3f69f10ef`
  `elspeth_knight_errant.txt` line 7 `AB$ Effect`,
  `Cost$ SubCounter<8/LOYALTY>`, `Ultimate$ True`,
  `Name$ Emblem — Elspeth, Knight-Errant`,
  `StaticAbilities$ STIndestructible` (`Mode$ Continuous | Affected$
  Artifact/Creature/Enchantment/Land.YouCtrl | AddKeyword$
  Indestructible`). Printed loyalty 4. Other lines: +1 Token (decision-free),
  +1 Pump (targeted).
- Chandra: `forge-behavior-v2:96a93b323591a45ca785ea0708082b85b594ff22`
  `chandra_torch_of_defiance.txt` line 11 `AB$ Effect`,
  `Cost$ SubCounter<7/LOYALTY>`, `Ultimate$ True`,
  `Name$ Emblem — Chandra, Torch of Defiance`,
  `Triggers$ TrigSpellCast` (`Mode$ SpellCast | Execute$ EffSpellCast
  DealDamage 5 ValidTgts Any`). Printed loyalty 4. Other lines: +1 Dig
  (Optional Play, decision-gated), +1 Mana ritual (decision-free),
  -3 DealDamage (targeted). Sibling paths own lines 5/6/7/8/10
  (templates 173/067/040/028/ValidTgts) — not exercised here.

## 2. Production entry path (standing D4a rule, reconfirmed at pin)

Planeswalkers enter only through production CAST. Direct BF placement
leaves loyalty 0 and `GameAction.handlePlaneswalkerRule` sends the host
to GY at SBA (D4a FAIL 34409161259 evidence). Production entry places
loyalty via the moveTo pipeline: intrinsic `etbCounter:LOYALTY:<base>`
Moved replacement (`CardState.java:792` via
`CardFactoryUtil.makeEtbCounter`) filling the shared CounterTable, applied
by `GameEntityCounterTable.replaceCounterEffect`. Loyalty timing/cost are
engine-owned: sorcery speed for loyalty abilities (`SpellAbility.java:2598`
`!isPwAbility()`), once per turn (`SpellAbilityRestriction.java:450-458`
`getPlaneswalkerAbilityActivated >= limit(1)`).

## 3. Multi-turn loyalty buildup — REJECTED (fail-closed by construction)

Naive setup (+1 activations across turns: Elspeth 4x Token, Chandra 3x Mana,
Tezzeret 2x discard-choice) requires genuine turn passing. It is blocked on
both controller attachments under the frozen D overlay set
(CODE_DERIVED at pin + WS01_HEAD strict boundary):
- Human attached (`dangerouslySetController`): every empty-stack priority
  query throws `PRIORITY_ACTION` (`rejectExternalDecision` is the first line
  of patched `chooseSpellAbilityToPlay`); any combat with a legal attacker
  throws `DECLARE_ATTACKERS`; replacement ordering throws
  `REPLACEMENT_ORDER`. Turn passing cannot proceed by design.
- AI attached (D4a posture, human standalone): `mainLoopStep` with empty
  stack gives the AI priority with live loyalty abilities and (for Elspeth)
  attackers — AI discretionary play. That is forbidden AI fallback and
  nondeterministic witness driving. D4a was safe only because it never
  stepped with an empty stack.
- `devModeSet` turn-skipping is documented in-engine as a setup hack that
  skips phase effects; per-turn loyalty reset semantics would not be genuine
  game progression. Rejected as construction-adjacent.
Tezzeret's +1 additionally needs discard-choice + hidden-hand decisions
(D6 family) — unusable in STATE_ONLY scope regardless.

## 4. Adopted COMMON_D4B_MECHANISM: Doubling Season entry-doubling (single turn)

`doubling_season.txt` at pin: `ManaCost:4 G`, Enchantment,
`R:Event$ AddCounter | ActiveZones$ Battlefield | ValidCard$
Permanent.YouCtrl+inZoneBattlefield | EffectOnly$ True | ReplaceWith$
DoubleCounters` (`DB$ ReplaceCounter | Amount$ Y`,
`Y:ReplaceCount$CounterNum/Twice`). Engine bridge verified at pin
(CODE_DERIVED): `ReplaceAddCounter.modeCheck` returns true for
`ReplacementType.Moved` when a CounterMap is present, so the AddCounter
replacement IS consulted during the ETB Moved event; `changeZone` sets
`EffectOnly=true` for battlefield entry; `ReplacementHandler.getReplacementList`
projects the entering card's LKI into the battlefield zone for validity;
`canReplaceETB` passes for a pre-existing Doubling Season; application is
sequential single-candidate steps (empty map excludes the doubler until the
intrinsic loyalty entry fills it — no ordering decision), with `Updated`
re-run (CR 614.16). Predicted entry loyalty: 8 for all three walkers
(rules-conformant per CR 306.5b/614.1c and Doubling Season's ETB-doubling
ruling). The CI run proves or refutes this empirically: the harness asserts
entry loyalty == 8 before paying the ultimate; any deviation fails closed
(no credit, path stays UNKNOWN).
Flow per case (one actor MAIN1, no turn passing, zero decisions):
cast Doubling Season (production) → cast walker (production) → assert
loyalty 8 → activate sole `ApiType.Effect` ultimate (production cost payment;
engine rejects short payment) → assert emblem + final loyalty.
- Elspeth: -8 → loyalty 0 → SBA GY (same `handlePlaneswalkerRule` path as
  D4a Gideon evidence). Consequence TIER-1: production Wrath of God with
  fixture actor Runeclaw Bear surviving (indestructible static proof;
  cross-case control is D4a Hildibrand where the same destroyer killed the
  same Bear). No Soldier tokens are created (no +1 activations needed).
- Chandra: -7 → loyalty 1 on BF. Presence TIER-2 (leitmotif precedent):
  emblem present with `TrigSpellCast` trigger payload. Damage consequence
  belongs to sibling line 7 (template-040) and needs Any-target selection
  (not externalized in D overlays) — recorded as D6-upgrade, never a blocker.
- Tezzeret: -6 → loyalty 2 on BF. Presence TIER-2: emblem present with
  `ArtifactDraw` trigger payload. Tap-draw consequence needs hidden info
  (draw) — recorded as hidden/D8-upgrade, never a blocker.
Mana pools (exact, engine-paid, pool-empty asserted; D4a mixed-pool precedent):
Elspeth `W4G1C8` (DS 4G + walker 2WW + Wrath 2WW), Chandra `R2G1C6`,
Tezzeret `U2G1C6`. Opponent holds only the Black Lotus hidden secret
(D4a posture; AI passes as evidenced 8/8 in D4a).
Engine-native observation: exactly one command-zone Effect whose name
contains the walker name, with static payload (Elspeth) or trigger payload
(Chandra/Tezzeret), plus zone/loyalty/life deltas. CR refs: 113 (emblems),
604 (Elspeth static), 603 (Chandra/Tezzeret trigger payloads), 606/117
(loyalty costs), 614 (DS replacement), 704.5i (Elspeth SBA).

## 5. Classification

- Tezzeret L11 (`0006052e…`): COMMON_D4B_MECHANISM (setup-decision concern
  eliminated by the doubling route; trigger-presence tier).
- Elspeth L7 (`2d5a6d01…`): COMMON_D4B_MECHANISM (static-consequence tier).
- Chandra L11 (`96a93b32…`): COMMON_D4B_MECHANISM (trigger-presence tier).
Coherent bounded family of 3. No DISTINCT_MECHANISM, no DEFER, no UNKNOWN
among the three. XHIGH escalation NOT triggered: single-turn, decision-free,
no shared-surface changes, no overlay changes, no rules ambiguity; the one
CODE_DERIVED bridge (Moved-time doubling) is empirically gated fail-closed.

## 6. D4b frozen attempt set and exact next action

Recipes: `EMBLEM_STATIC` (Elspeth + Wrath probe, effect_kind static),
`EMBLEM_TRIGGER_PRESENCE` (Chandra, Tezzeret, effect_kind trigger).
Intents all NONE. Build D-owned generic machinery only: D4b preparer table,
D4b filter (3 + 46 cover, digest over 3, anti-double-credit vs ledger-PASS
AND partition-evidenced-33 AND retained `ede58d66`), D4b harness
(`Ws33D4bEmblemCampaignTest`), D4b certifier, D4b workflow. Reuse: per-path
preparer table pattern, production-CAST entry rule, loyalty canonical state,
command-zone Effect assertions, CR taxonomy, opponent-controller probe
posture, stub-compile local gate. No A/C/serial/shared contract change.
Then: stub-compile + dry-run + digest stability + syntax gates; PENDING +
WRITE_FREEZE; one 3-path run; per-path adjudication.
