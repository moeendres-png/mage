# WS33-C Batch 2 selection (phase-fixture family)

Batch digest: `9845779cbfd430b52008c2888d677866d81f74e45224c1ff712e29624f4a1e15` (R7: gnarlbark forced-choice declaration; reference-identity attribution; SBA settle; roster/damage diagnostics) (5 executions, 5 rows/slots, 3 unique new paths).

## Selection-gate outcome for the primary priority (targeted-ETB)

Exhaustive manifest query over remaining template-113 STATE_ONLY paths:
**targeted first-order links = 0**. Every ValidTgts/TargetMin/TargetMax
bearing C link is modeled template-107 (DECISION+REPLAY) by construction.
Targeted-ETB/STATE_ONLY intersection is EMPTY; no targeted batch is
selectable under the current no-decision-protocol contract. Second-order
links of targeted parents (glimmerpoint DelTrig, kor DBPump, puppeteer
Animate) require driving the targeted parent and are excluded for the
same reason. This is reported, not worked around: template-107 needs a
separate authoritative-target decision protocol (Sol-level scope call if
pursued). Scope cap (no 105/119) honored throughout.

## Selected executions (5) / new paths (3) + 2 shared diversity slots

1. `gnarlbark-eot` — restored from deferred. Draw→Blight (2c49adc7…),
   EOT travel + post-travel addAll (R6 hypothesis for R5 silence: the
   trigger waits simultaneous-pending and was never moved to stack).
   Assertions hand-net 0 / M1M1==1.
2. `thunder-etb` — terminal DamageAll root (7574de05…, shared by 65
   occurrences). ETB_SELF (proven fixture) + own Bear setup (bear dies).
   Assertions bear battlefield 0 / bear graveyard 1 / thunder present.
   Terminal matching (same-id pair).
3. `ironsmith-upkeep` — terminal Transform root (a4f6a646…).
   MAIN2 via-move placement (empty-board combat travel) + opp-upkeep
   travel. Assertions Ironfang==1 / Ironsmith==0. Terminal matching.
4. `banshee-upkeep-own` — terminal PutCounterAll root (7574de05… shared
   with thunder: diversity, no new count). Full-round travel with
   opponent library fill (draw survival) + turn-aware stop at OUR upkeep.
   Assertions bear M1M1==1 / banshee M1M1==0 (filter correctness).
5. `snuffers-etb` — terminal PutCounterAll root (7574de05… shared:
   diversity, no new count). ETB_SELF + own Bear (both take M1M1, both
   survive 2/2->1/1 and 3/3->2/2). Assertions bear==1 / snuffers==1.

Effect diversity: Draw/Blight, DamageAll, Transform, PutCounterAll.
Fixture diversity: ETB_SELF x2, EOT-travel, upkeep-opp-travel,
upkeep-own-roundtrip. New machinery per execution exactly one piece:
EOT-addAll (gnarlbark), terminal matching (thunder), upkeep travel
(ironsmith), round-trip + opp fill (banshee); snuffers reuses proven pieces.

## Excluded with cause (representative)

- Kappa/gateway/hraesvelgr Effect-statics: assertion vocabulary gap
  (static content unobservable) -> WITNESS_ASSERTION_INFRASTRUCTURE_PENDING.
- Soul-Shackled/King-Solomons/Reaper/Aerial/Skyclave (TargetMin 0 /
  up-to-one): residual choice even in singleton fixtures -> out of contract.
- Kor/Puppeteer/Tataru/Transpose/Magma/Pizzasaur: targeted first links ->
  template-107, needs decision protocol.
- SP/AB cost fixtures (Papalymo/Uthros/Serra/Mazemind/Elixir/Cut/Transpose):
  WS33B cost surface.
- Combat fixtures (Archnemesis/Coercive/Falcon/Soul-Seizer/Laelia): attack
  declarations outside contract.
- Upkeep-win (Mechanized), commander-gated (Loyal), cast-conditional
  (Frogs), vacuous (Champions X=0, Serene 0-goaded, Estinien X=0),
  unachievable (Lux X>=30), search/shuffle, reveal/hidden, RNG.
- Gnarlbark remains the ONLY sub-link in batch (proven ETB-chain shape).

## Pre-run gate status

Checker (screen incl. Mode=TgtChoose/Dig rules + ApiType-allowlist verified
DB heads + provenance/line/pointer mapping + UNKNOWN + scope + no-dup
except declared-shared) must print BATCH_CHECK=PASS with the digest below
before commit. Then workflow counts (rows/markers) → commit → push → PENDING.
