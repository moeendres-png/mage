# D3 Q6 Import-Automation Discriminator Report

Date: 2026-09-10 (UTC)
Mode: RESEARCH + ISOLATED PROTOTYPE ONLY
Branch (isolated): `research/d3-q6-import-automation-20260910`
Worktree: `/home/moeen/code/mage-d3q6` (isolated; active WS33/WS48 branches untouched)
Corpus clone (immutable input, not working state): `/home/moeen/forge-corpus`
(partial Forge clone, blob-on-demand; corpus data is not committed)

Recovery note: an earlier `/tmp`-backed worktree was reclaimed by OS tmp
reclamation before commit. All artifacts were rebuilt from scratch at the
persistent paths above and the full experiment re-executed deterministically
(seed 20260910): every headline metric reproduced exactly
(974/933/974/528/186/26/36; 7409/13810 params). Nothing below depends on the
lost `/tmp` state.

**Governing inequality: PARSE/IMPORT != BEHAVIOR PASS.**
No row in this report is promoted to PASS because the parser succeeded.
Behavior PASS count from this experiment: **0 by construction**.
Behavior credit claimed: **0**.

No canonical book mutation. No coverage promotion. No Batch-6.

---

## 1. Objective and verdict

**Question:** can a tooling pipeline remove *most* manual Q6 scenario/import
mechanics while preserving PARSE/IMPORT != BEHAVIOR PASS, over 1000
representative Forge card scripts stratified across mechanics?

**Answer:**

| Claim | Result |
|---|---|
| Syntax intake automated (parse without failure) | 974/1000 (97.4%) — YES |
| Structured field extraction (≥1 param record) | 933/1000 (93.3%) — YES |
| Scenario-skeleton auto-generation | 974/1000 (97.4%) — YES |
| Rows needing **no** manual review | 472/1000 (47.2%) — **NO, not most** |
| Rows requiring manual review | 528/1000 (52.8%) |
| Behavior PASS contributed by this pipeline | 0/1000 (0%) — by design |
| Heuristic semantic-field typing coverage | 7409/13810 params (53.6%) |

The pipeline automates **scaffolding** (intake, inventory, skeleton,
taxonomy pre-tag, provenance) for nearly all inputs, but a **majority still
requires manual review** before any behavior claim, and it contributes
**nothing** to behavior certification. It therefore does **not** remove *most*
manual Q6 mechanics end-to-end.

**Formal recommendation: `BUILD_CLEAN_ROOM_EQUIVALENT`**
(scoped: intake/skeleton/taxonomy pre-tag generator only; behavior gates
unchanged; Forge/Manabrew execution reached solely as an isolated external
process).

- `ADOPT_TOOL_PATTERN` — NO (beyond ideas; GPL/AGPL code cannot be adopted
  into a permissive tree).
- `USE_EXTERNAL_ISOLATED_TOOL` — approved as SECONDARY mode for the parity /
  trace harness and the MIT grammar (black-box subprocess, JSON over stdio,
  no linking). Not the primary recommendation because the harness answers a
  different question (execution fidelity) than the one discriminated here
  (import scaffolding).
- `REJECT` — applies to full import-automation *as a behavior qualifier*
  (see §7); rejected as a whole only if scoped scaffolding value is declined.

---

## 2. Legal / topological reuse determination (no GPL/AGPL copied)

No Manabrew or Forge implementation source was cloned, vendored, linked, or
reimplemented from source. Only public metadata (licenses, READMEs, docs
pages, crates.io records) and the public Forge wiki format description were
read. The prototype was written from the wiki plus direct observation of
pinned corpus files.

| Component | License (verified 2026-09-10) | Reuse mode | Rationale |
|---|---|---|---|
| Forge engine + card scripts (`Card-Forge/forge`, pin `8c7e9af`) | GPL-3.0-or-later (repo `LICENSE`) | `REFERENCE_ONLY` (scripts: pinned input data, provenance retained, not redistributed) | Copyleft; engine internals not consulted |
| Manabrew workspace: engine, `forge-carddb`, `forge-card-script` (current), `parity` | AGPL-3.0-or-later (`Cargo.toml` workspace + `LICENSE.md`: "vendored `forge/` tree stays GPL-3.0-or-later") | `NOT_USABLE` for embedding; `REFERENCE_ONLY` for public docs; `SEPARATE_TOOL_PROCESS` for execution/parity | AGPL network clause + GPL derivation; usable only as black-box subprocess |
| `forge-card-script` 0.1.1 (crates.io record) | GPL-3.0-or-later | `NOT_USABLE` / `REFERENCE_ONLY` | Same as above (version skew AGPL vs GPL noted; both copyleft) |
| `tree-sitter-forge-card-script` | MIT (`LICENSE`, © 2026 khaliostr) | `USE_EXTERNAL_ISOLATED_TOOL` (also pattern-idea reference) | Only component legally embeddable; kept as subprocess to preserve topology. Known coverage gap: unknown `Key:` yields error node where the permissive parser degrades gracefully |
| Forge wiki (scripting API, triggers, custom-card guides) | Public documentation | `REFERENCE_ONLY` | Format knowledge source for clean-room work |
| Manabrew `PARITY_AND_IR.md`, `forge-dsl-semantics.md` | Public docs of AGPL project | `REFERENCE_ONLY` | Design knowledge (late-bound SVar resolution, typed-IR-as-implementation-difference) used as ideas only |

Recorded reuse verdicts:

- Manabrew embedded reuse = `NOT_USABLE`
- Manabrew docs/patterns = `REFERENCE_ONLY`
- tree-sitter grammar = external isolated tooling candidate
  (`USE_EXTERNAL_ISOLATED_TOOL`)

Uncertainties: none material — every component resolved to a mode above
(no `UNKNOWN` reuse mode). If the MIT grant on the tree-sitter grammar were
ever relicensed, it would fall back to `REFERENCE_ONLY`.

Clean-room controls applied to `forge_script_parser.py` (`d3q6-cleanroom-0.1.0`):
line-classification + byte-span + never-fail-diagnostics follows the *idea*
of the MIT grammar only; all token tables (`KNOWN_TOP_KEYS`,
`KNOWN_ABILITY_KINDS`, `KNOWN_TRIGGER_MODES`) were curated from the public
wiki and observed corpus, deliberately minimal so coverage gaps are *measured*
rather than hidden.

---

## 3. Corpus pin and stratified sample (not first-1000-alphabetical)

- Source: `https://github.com/Card-Forge/forge.git`
- Pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`
  ("Fix Nori, Teller of Tales (#11713)", 2026-08-27T11:56:16Z) —
  identical to the WS33 `FORGE_PIN`, so results are comparable.
- Population: **33,666** `*.txt` under `forge-gui/res/cardsfolder` at pin.
- Method: deterministic seeded shuffle (`seed=20260910`) of the full sorted
  file list → fetch 3,500 candidates via `git show FETCH_HEAD:<path>`
  (0 fetch errors) → greedy stratify to **1,000** with per-stratum quotas and
  ≥15-per-adversarial-tag minimums. Directory-letter–independent by
  construction (shuffle precedes selection).
- Provenance per row: remote + pin + subject + date + file path + SHA-256 of
  fetched content + parser version + seed. Retention: **1000/1000 (100%)**.

Stratum composition of the final 1000:

| Stratum | n |
|---|---|
| trigger | 183 |
| ability (activated/spell, non-targeting) | 184 |
| targets | 151 |
| svar_heavy (nested SVar chains) | 120 |
| static | 116 |
| choices | 84 |
| replacement | 80 |
| keyword/vanilla | 82 |

Family mapping (WS33 taxonomy, pre-tags only, not evidence):

| Family | n |
|---|---|
| ACTION_COST_DECISION | 997 |
| TRIGGER_REPLACEMENT_ZONE_SBA | 379 |
| HIDDEN_RNG_REPLAY | 287 |
| CONTINUOUS_COPY_CONTROL | 170 |

---

## 4. Required adversarial cases — all present

| Adversarial class | n / 1000 | Example signal |
|---|---|---|
| nested SVar chains | 164 | `invoke_despair.txt`: SVar depth **11**, 14 edges |
| targets | 225 | `ValidTgts$` / `TargetMin/Max$` |
| choices / modes | 438 | `Charm` (65 files), `GenericChoice`, `Optional$` |
| mana / cost | 939 | `ManaCost$`, `Mana` abilities (100 files) |
| triggers | 183 | 26 distinct `T:Mode$` values |
| replacements | 89 | `R:` lines + `ReplaceEffect` (11) |
| hidden information | 106 | face-down / reveal / look-at |
| randomness | 228 | coin / dice / shuffle |
| copy / control | 170 | `CopyPermanent`, `CopySpellAbility`, gain-control |
| multiplayer-referencing | 47 | each-player / vote / monarch |

Deepest chain observed: `forge-gui/res/cardsfolder/i/invoke_despair.txt`
(depth 11 over `DBLoseLifeC/DBDrawC/DBCleanC/DBSacrificeE/…`). SVar resolution
in the prototype is non-expanding (depth measured, never eagerly resolved),
consistent with the late-bound semantics documented in the Manabrew reference
docs — followed as an idea, not as code.

---

## 5. Headline metrics (the report table)

| Metric (n=1000) | Count | Rate |
|---|---|---|
| Input scripts | 1000 | — |
| Parsed (no fatal diagnostic; parser never throws) | 974 | 97.4% |
| Structured (≥1 param record extracted) | 933 | 93.3% |
| Scenario-skeleton-generatable | 974 | 97.4% |
| Manual-review-required | 528 | 52.8% |
| Unsupported (any unknown top-level key) | 186 | 18.6% |
| Ambiguous (missing `:` / bad SVar sep / dup params) | 26 | 2.6% |
| False-positive semantic-parse probes | 36 | 3.6% |
| Semantic-field heuristic typing (params) | 7409/13810 | 53.6% |
| Behavior PASS promoted | 0 | 0% |

Decomposition of "unsupported" (top-level keys — the shallowest layer):

| Directive | Files | Disposition |
|---|---|---|
| `topkey:AI` (AI hint lines) | 180 | Benign metadata; allowlist gap, closable in minutes |
| `topkey:HandLifeModifier` | 6 | Real (avatar/vanguard-style); needs schema row |
| `topkey:MeldPair` / `topkey:Draft` | 1 each | Real but rare; needs schema rows |

True semantic-topkey unsupported after excluding benign `AI:` hints: **~8
files (0.8%)**. The real semantic gaps live one layer deeper:

- **Ability verbs** (`SP$/AB$/DB$`): 108 distinct verbs in sample; **443
  files** use ≥1 verb outside the minimal 35-verb table. Top gaps: `Cleanup`
  (150, structural boilerplate), `Mana` (100, basic!), `Charm` (65, modal
  spells), `Dig` (42), `ChangeZoneAll` (36), `PumpAll` (29), `Counter` (23),
  `Mill` (21). Closing this is mechanical curation from the public Forge
  wiki API list (~150+ entries), not research — but it is *required* before
  any "mostly automated" claim.
- **Trigger modes** (`T:Mode$`): 26 distinct; **46/183 trigger files (25%)**
  use 15 modes outside the minimal table — led by `Attacks` (29 files),
  then `ChaosEnsues`, `Blocks`, `Always`, `AttackerBlocked`,
  `DamageDealtOnce`, `ChangesZoneAll`, planechase/dungeon novelties
  (`Forage`, `FullyUnlock`, `UnlockDoor`, `RolledDieOnce`,
  `TokenCreatedOnce`). Static modes are healthy (`Continuous` 130,
  cost-modifier family intact).
- **Ambiguity** (2.6%): e.g.
  `s/sundering_eruption_volcanic_fissure.txt:12` (line without `:` —
  multi-face separator edge); duplicate-param and empty-key diagnostics make
  up the rest. All fail closed into manual review.
- **False-positive probes** (3.6%): heuristic flag where an ability record
  exists but no mana/target/choice signal was typed. Every probe is a
  manual-review redirect, never a silent pass.

Bounded `import → construct → execute → trace → compare` subset (n=20
simplest cards: no SVar nesting, no hidden/random/copy/multiplayer):
prototype-constructed ability inventory vs an *independent* regex
re-extraction agreed **20/20** on ability/SVar presence shape, with
`behavior_pass=false` and `evidence_class=SYNTHETIC` on every row. This
validates *scaffolding determinism only*. No native Forge execution was
performed (JDK/Maven Forge build exceeds the isolated-prototype budget); the
honest upgrade path is specified in §6 rather than claimed.

---

## 6. Parity-harness design (SEPARATE_TOOL_PROCESS, not built here)

For any future `construct → execute against Forge → capture native trace →
compare` claim to be admissible, execution must run as an **isolated external
process** with this topology:

```text
[clean-room skeleton JSON] → [external Forge Java harness subprocess]
        → stdout/JSON trace snapshots → [black-box comparator]
        → first-divergence report (phase/turn/player/object/field)
```

Rules: pin the Forge commit; run identical decks/seed/deterministic choices on
both sides; compare snapshots field-by-field; treat the harness binary and its
output as untrusted input (schema-validated, never imported). The Manabrew
parity concept is followed at this architectural level only. No AGPL/GPL code
is linked, vendored, or reimplemented from source at any point.

---

## 7. WS33 manual-work replacement estimate (explicitly bounded)

WS33-style per-path work decomposes (by cost, not by file count) into roughly:
(a) intake/inventory/skeleton, (b) scenario semantics (targets, choices, zones,
SBA timing), (c) Record/Replay witness execution, (d) adjudication/evidence
sealing. This pipeline automates (a) at ~97%, assists (b) at ~50% (pre-tags at
53.6% heuristic typing, verb/mode inventories still to curate), and contributes
**zero** to (c) and (d) — which dominate cost on adversarial mechanics
(nested SVars, hidden info, randomness, copy/control, multiplayer).

Estimate: **~25–40% of per-path mechanical toil** replaceable by the scoped
scaffolding generator; **~0% of behavior-certification work**. At WS33 scale
(4188 effective paths, 3700 UNKNOWN), that is a meaningful toil reduction for
triage and skeleton authoring, but it moves **no** row from UNKNOWN to PASS and
must never be booked as coverage.

---

## 8. Artifacts (isolated branch only)

- `research/d3-q6-import-automation/forge_script_parser.py`
  (`d3q6-cleanroom-0.1.0`) — clean-room parser + feature/taxonomy/skeleton
  generator. Evidence class: SYNTHETIC (tooling, not behavior evidence).
- `research/d3-q6-import-automation/run_experiment.py` — deterministic
  sampler/runner (seed 20260910; stratum quotas; adversarial minimums).
- `research/d3-q6-import-automation/aux_census.py` — T-mode/verb census with
  correct T-vs-S distinction (`aux_census.json`).
- `research/d3-q6-import-automation/results_sample.json` — 1000 rows, each
  with path, provenance, content-SHA256, features, taxonomy pre-tags,
  diagnostics, skeleton (`behavior_pass=false` throughout).
- `research/d3-q6-import-automation/results_summary.json` — aggregate metrics.
- `research/d3-q6-import-automation/smoke_sample.json` /
  `smoke_summary.json` — 20-row pilot (kept for audit trail).
- This report: `research/d3-q6-import-automation/D3_Q6_IMPORT_AUTOMATION_REPORT.md`.

Verification performed: full 3500-fetch/1000-sample run green (0 fetch
errors); smoke pilot green; syntax checks green; corpus pin re-verified
(`8c7e9af` = "Fix Nori, Teller of Tales (#11713)", 2026-08-27; 33,669
cardsfolder entries); full rerun after worktree recovery reproduced every
headline metric exactly; active-branch cleanliness preserved (all work in the
isolated worktree/branch).

Evidence classification of everything in §5: **SYNTHETIC** (prototype
telemetry) unless labeled CODE_DERIVED (pin/license facts re-verified against
live remotes). Nothing here is DIRECTLY_VERIFIED behavior evidence and nothing
may be cited as such.

---

## 9. Recommendation (single, formal)

**`BUILD_CLEAN_ROOM_EQUIVALENT`** — build a clean-room intake/skeleton/
taxonomy pre-tag generator (this prototype's lineage), with hard scope rails:

1. Output is scaffolding only (skeleton JSON + pre-tags + provenance);
   every row defaults to manual-review-required unless a stated allowlist
   (AI hints, curated verb/mode tables) positively clears it.
2. `UNKNOWN` stays `UNKNOWN`; the tool has no PASS path (enforced in code:
   `behavior_pass=false`, `evidence_class=SYNTHETIC`).
3. Verb/mode inventories are curated from public Forge wiki documentation
   (clean-room data curation), closing the measured 443-file verb gap and
   46-file T-mode gap before any efficiency re-measurement.
4. Any execution/trace comparison runs exclusively as
   `SEPARATE_TOOL_PROCESS` (§6); GPL/AGPL components stay `REFERENCE_ONLY` /
   `NOT_USABLE` for embedding.
5. Re-measure on the frozen sample (seed + pin unchanged) after inventory
   curation; the discriminator passes for scaffolding only if manual-review
   drops below 50% *without* weakening classifier strictness.

`REJECT` is the correct verdict for import-automation **as a behavior
qualifier** today and remains in force for any proposal to promote rows on
parser success. `ADOPT_TOOL_PATTERN` beyond ideas, and any linking or
vendoring of GPL/AGPL implementation, are prohibited.
