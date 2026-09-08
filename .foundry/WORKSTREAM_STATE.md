# WS33B Workstream State (branch-local)

BRANCH = work/ws33-b-high-throughput-20260907
B_HEAD_AT_WRITE = 04bcef6b4a36549bfb89e428e31d5b0496e3ce7b
B_TREE_AT_WRITE = 782a4c6d7df8f9659e5d448971b48a5c976775e4
CANONICAL_HEAD_VERIFIED = 6da237b704ba5e66c58c2334f47e36ef68ca980d
CANONICAL_TREE_VERIFIED = 8f6d0151e4a9095c95925d6f6065214d382bf1dc
FORGE_PIN = 8c7e9afb8e6caee88644b94e25da5852e36f8928

## Global-state discrepancy (recorded, not repaired from here)

Root PROJECT_STATE.md on this branch still cites CURRENT_HEAD=43807b57...
(canonical advanced to 6da237b7). Global PROJECT_STATE.md belongs to the
canonical line; reconciliation must be a focused metadata package on
work/ws33-g3-final-closure-20260902. This branch does NOT own it.

## Target (DIRECTLY_VERIFIED 2026-09-08)

Selector: logical_bucket=WS33B AND
implementation_target=forge.game.ability.AbilityUtils#calculateAmount AND
current_status=UNKNOWN over WS33_INTEGRATED_CLOSURE_LEDGER.jsonl (4188 rows).
Cardinality=273, digest=30dd81f733e0c1dfdb2d3020c0b9b1e0a2ed542fcf78123d641839fb24800024.
Single queue item: WS33B/calculateAmount/ws33-g2-template-010/DECISION+RNG+HIDDEN+REPLAY.
B partition: 675 = 273 calculateAmount + 402 forge.game.cost.Cost.
Checkpoint: checkpoints/WS33B_CALCULATE_AMOUNT_TARGET_PREFLIGHT_20260908.md.

## Path clusters by amount-expression head (CODE_DERIVED from ledger)

Count=116, SVar=34, Remembered=19, TriggeredCard=17, PlayerCountOpponents=14,
TriggerCount=9, TargetedPlayer=9, Targeted=8, ReplaceCount=8,
PlayerCountPlayers=8, TriggeredSpellAbility=6, PlayerCountPropertyYou=4,
Sacrificed=4, Number=3, PlayerCountRegisteredOpponents=2, ParentTargeted=2,
singletons: PlayerCount, TriggeredTarget, TargetedObjects, TargetedController,
TriggeredObject, TriggeredAttacker, TriggerRemembered, PlayerCountDefinedRegistered,
ReplacedCard, RememberedLKI.
Every path has exactly one head. All 273 are SVAR-directive, 316 distinct cards.

## Engine facts (pinned Forge, CODE_DERIVED)

calculateAmount(Card,String,CardTraitBase[,boolean]) at
forge-game/src/main/java/forge/game/ability/AbilityUtils.java:364-727.
Dispatch: blank/null->0; sign strip; numeric->value; SVar lookup (ability then
card; missing Cost*->0 else stderr+0); numeric svar->value; Count/Number->xCount;
SVar->recurse+doXMath; PlayerCount*->playerXCount; OriginalHost/DungeonsCompleted/
ExiledWith/Convoked/Emerged/Crewed/ChosenCard/Remembered[LKI]/Imprinted[LKI]/
Enchanted/Equipped->handlePaid; SpellAbility-only Targeted*/Triggered*/TriggerCount/
ReplaceCount lists->handlePaid|getPaidCards; null->0; maxto clamp; multiplier.
ExternalDecision* input classes are WS01-overlay-provided (absent from pin).
Ws05HiddenInfoProbe.java + WS06 RNG overlay + WS33 runtime overlays present in-repo;
prerequisite pins WS01/WS12/WS32 exist locally.

## Campaign design (decided)

Follow the proven A1 pattern fully present in-repo (preparer TSV+plan, Java
campaign test installed into pinned Forge, record+replay via Maven, Python
certifier, workflow, gate): preparer maps each path to (representative card,
SVar expression, fixture recipe, K); Java test executes recipe, evaluates
production calculateAmount, asserts engine output == deterministic function of
fixture inputs; decision via WS01 external provider; RNG via WS06 seeded tape;
hidden via Ws05 probe; replay byte-equal final state. No card-name production
hacks; no pilot rules; fail closed.

## Milestones

- [x] B0: source lock + target reproduction + workstream state
- [x] B1: preparer v1 (273 cases, 0 skipped) + full overlay stack applied locally
- [x] B2: Java test + 3-case local record+replay smoke green (XPAID/HAND/BATTLEFIELD)
- [x] B3: 238/273 record+replay green locally (all implemented recipes, 0 actionable failures)
- [x] B3b: 273/273 record+replay green locally (batch 4+5; 6 default-zero flagged TECHNICALLY_CONFORMANT+REVIEW)
- [x] B4: CI run 34266311850 SUCCESS + independently adjudicated PASS (artifact 10072131808, 2737/2737 hashes, 273/273 replay, 2457 RNG events) + PASS checkpoint persisted
- [x] B5: 402 Cost cluster: preparer v1 + payment test, 397/402 record+replay green locally, 5 terminal blockers registered
- [x] B6: CI run 34286249888 SUCCESS + independently adjudicated PASS (artifact 10079683394, 3977/3977 hashes, 397/397 replay, 3573 RNG events) + PASS checkpoint persisted
- [x] B7: B1/B2 coverage-promotion proposal for canonical/integration line (proposal only)
- [ ] Remaining: canonical-line promotion, C–F waves, AF8, reconciliation, freeze (all blocked — see below)

## Concurrency note (2026-09-08)

The shared worktree was found checked out to work/ws33-c-high-throughput-20260907
with B commits intact on origin (32227dc7eb). No C-branch state was modified
(git status clean apart from new B2 files); returned to B and verified
integrity (preparer output identical). Possible parallel C worker: do not
assume exclusive worktree ownership; verify branch before editing.

## Phase 3 survey (2026-09-09, DIRECTLY_VERIFIED from live refs)

- Canonical work/ws33-g3-final-closure-20260902 unchanged at
  6da237b704ba5e66c58c2334f47e36ef68ca980d (no promotion consumed B1/B2 yet).
- C/D/E/F/A high-throughput branches: all still at 895240f405 (2026-09-07
  AF8 base). Zero shard commits — C–F frontiers are unowned in Git terms,
  but this shared worktree flips to C spontaneously, so no C–F implementation
  was started here (collision risk; needs a dedicated worktree/worker).
- work/ws33-af8-evidence-contract-repair-20260908: ACTIVE (commits through
  2026-09-08 13:44). Owned by parallel work — not inspected beyond log, not touched.
- B1 run 34266311850 + B2 run 34286249888 remain terminal SUCCESS, latest on B branch.
- No production contracts (P0–P10) exist in-repo; production work is NOT_ELIGIBLE
  (no ARCHITECTURE_FREEZE). No freeze dossier started — WS33 gates are far
  from met (A–F waves + AF8 + cross-qualification outstanding).

## WS33B terminal state

670/675 B paths with passing CI evidence (B1 273 + B2 397, disjoint, disjoint
from base PASS). 5 Cost terminal blockers + 6 B1 fail-closed defaults remain
UNKNOWN-or-held (exact IDs in checkpoints). B workstream has no open engineering
items; all that remains is canonical-owned or review-gated.

## B1/B2 evidence (CODE_DERIVED, local scratch /tmp/opencode/forge-pin @ FORGE_PIN)

- Preparer: ws33_prepare_calculate_amount_campaign.py → 273 cases, recipes
  COUNT_XPAID=17, COUNT_HAND_YOUOWN=4, COUNT_BATTLEFIELD_CREATURE_YOUCTRL=6,
  rest explicit UNSUPPORTED_*; skipped={}.
- Overlay stack applied in CI order (WS01 full + WS05 + WS06 + WS33
  input-confirm/stack-target + WS12 + WS32). NOTE: WS01 must be applied with
  the full forge-patches dir (follow-up patchers incl. compile-fixes are
  required; partial application breaks forge-gui compilation).
- Smoke: 3/3 record SUCCESS 0 diagnostics; 3/3 replay SUCCESS byte-equal
  final state, RNG replay + decision replay consumed, hidden leak deltas 0.
- Fixture lessons recorded: fillLibrary before shuffle (empty library draws
  no RNG); decision-fixture Prodigal Sorcerer counts as actor creature (+1);
  opponent bear / actor Island exercise Valid-filter exclusion.

EXACT_NEXT_ACTION = Canonical worker: consume
checkpoints/WS33B_PROMOTION_PROPOSAL_20260909.md (re-verify digests +
disjointness against live state, adjudicate 6 defaults, persist PENDING,
promote serially). Shard worker with dedicated worktree: own one of C/D/E/F
(zero commits since 895240f405) following the B1/B2 campaign pattern
(preparer + campaign test + filter + certifier + workflow + run + adjudicated
PASS checkpoint). Do NOT start C–F work in this shared worktree.
