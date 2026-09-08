# Commander Simulator Next — Repository Agent Contract

This file applies to Commander Simulator Next research, qualification, integration, and pre-freeze engineering in `moeendres-png/mage`.

It is intentionally stable project context. Volatile workstream state belongs in `PROJECT_STATE.md`, workstream checkpoints, immutable Actions artifacts, and exact GitHub branch/commit identities.

## Source truth

For volatile technical state, use this precedence:

1. newer direct user instructions;
2. freshly verified GitHub branch/commit/tree state;
3. current GitHub Actions runs, jobs, artifacts, digests, and concrete source;
4. exactly pinned external engine versions;
5. current official Magic Comprehensive Rules, Oracle text, and rulings;
6. historical reports, handoffs, chats, and status files.

Names such as `CURRENT`, `FINAL`, or `LATEST` do not prove freshness.

Before material work, verify the exact relevant `HEAD`, `TREE`, run, job, artifact, digest, and external pins when those identities exist for the workstream.

## Production boundary

Before an evidence-based Architecture Freeze, do not create or begin implementing a new Commander Simulator Next production repository.

Research and qualification remain in the research context. Forge, XMage, wrappers, ports, hybrids, or replacement components remain candidates until the architecture is frozen from evidence.

Do not build a new general rules core when an existing qualified core is objectively better. Do not preserve an existing engine merely because it is already present.

## Rules / pilot boundary

The authoritative Rules Core owns:

- legal actions;
- costs and payment legality;
- mana;
- stack and priority;
- targets;
- combat;
- triggers;
- replacement effects;
- continuous effects and layers;
- state-based actions;
- zones;
- Commander rules.

External pilots receive actor/principal-scoped observations and authoritative legal decision options only. Pilots choose discretionary options; they do not reconstruct legality.

Forbidden production-reachable patterns include:

- prompt/UI heuristics as rules logic;
- a second hidden rules engine in a pilot or adapter;
- silent `first`, `default`, `random`, `pass`, `cancel`, or AI fallbacks;
- card-name production hacks;
- manual outcome injection;
- direct-effect shortcuts that bypass the qualified parent/runtime path;
- standalone subability execution substituted for a production-reachable parent path.

Unsupported production-reachable paths fail closed.

## Hidden information, RNG, and replay

Hidden information is principal-scoped. Do not leak private hand/library/look/choice information through observations, decision options, logs, traces, replay metadata, or adapter state.

Semantically relevant randomness must use explicit controlled RNG, be recorded when required, and reproduce under Semantic Replay. Host/library randomness outside the authoritative RNG path is not acceptable evidence.

Replay must prove semantic equivalence required by the active contract; byte equality of incidental files is not automatically semantic proof, and semantic proof cannot silently omit required decision/RNG/private-state evidence.

## Evidence vocabulary

Use these classifications precisely:

- `DIRECTLY_VERIFIED`
- `CODE_DERIVED`
- `TECHNICALLY_CONFORMANT`
- `EXTERNALLY_RULE_VALIDATED`
- `MODELED`
- `SYNTHETIC`
- `UNKNOWN`

Invariants:

```text
UNKNOWN != PASS
PARTIAL != FULL
green workflow != qualification PASS
source presence != card behavior PASS
parsing/import != card behavior PASS
reference-engine parity != official-rules authority
```

A behavior PASS requires the actual evidence demanded by the current witness/qualification contract.

## Workstream and branch discipline

Every technical workstream must have:

- an exact `AUDIT_BASE_SHA` or otherwise explicitly frozen source identity;
- a dedicated branch;
- clear file/subsystem ownership;
- explicit dependencies;
- concrete gates;
- reproducible tests;
- a persistent handoff/checkpoint.

Parallel workstreams must not independently mutate the same canonical branch or silently overwrite another workstream. They may share an exact frozen base, but must use separate branches and owned scopes. Integration and cross-qualification happen separately and serially where coverage promotion requires it.

Do not re-run already valid tests merely for reassurance. Requalification is justified by relevant code/pin/contract changes or inadequate evidence.

## Systemic repair rule

When an actual-card witness establishes a systemic engine problem:

1. isolate the minimal production-reachable failing case;
2. classify the root cause;
3. repair the generic subsystem rather than card names;
4. add a generic regression test;
5. rerun the original actual-card witness;
6. adjudicate whether previous PASS evidence was invalidated.

Do not infer a generic Forge/core defect merely because a path is still `UNKNOWN`.

## Failure semantics

Keep failure classes distinct. In particular:

- `ENGINE_FAILURE` requires actual engine-side failure after engine execution begins;
- `CARD_BEHAVIOR_FAILURE` requires successful engine execution followed by a semantic verification mismatch;
- `UNSUPPORTED_RULES_PATH` is reserved for a genuinely production-reachable unsupported rules path.

Qualification/adjudication/evidence-contract failures must not be mislabeled as engine or card-behavior failures.

## Repository map

Important existing areas include:

- Forge/XMage modules at repository root (`Mage.*`, `mage-*`, and related Maven modules);
- `.github/workflows/**` for current qualification and validation pipelines;
- `research/greenfield-qualification/**` for Commander Simulator Next research contracts, engine patches/overlays, evidence, and workstreams;
- `research/greenfield-qualification/actual-card-behavior/**` for actual-card behavior qualification;
- `research/greenfield-qualification/actual-card-behavior/ws33/**` for the current WS33 closure program;
- root `PROJECT_STATE.md` for the current resumable project/workstream index where present.

Inspect the live tree before assuming a path exists.

## Build and validation guidance

The exact workstream workflow is the authority for its validation commands. Current research workflows use combinations of:

```bash
python -m py_compile <qualification scripts>
python -m unittest -v <focused qualification tests>
```

and pinned Forge witness execution shaped like:

```bash
xvfb-run -a mvn -B -pl forge-gui-desktop -am \
  -Dtest=<qualification test class> \
  <workstream properties> \
  -Dsurefire.failIfNoSpecifiedTests=false \
  -DfailIfNoTests=false \
  test
```

The root Maven project also documents normal Maven build/install flows, but a generic green Maven build is not Commander Simulator Next qualification evidence.

Preferred validation order:

```text
inspect exact source/contracts
→ reproduce or materialize focused evidence
→ implement smallest systemic change
→ focused tests
→ relevant regression tests
→ actual-card witness/campaign
→ replay/hidden/RNG gates where relevant
→ immutable artifact/evidence adjudication
→ persistent handoff
```

## Persistent execution / resumability

Treat every model turn, local process, and GitHub Actions run as interruptible.

After every material package:

- persist code/evidence/checkpoints to GitHub;
- record exact source identities and commands;
- update the active workstream state/checkpoint when that workstream owns one;
- never leave a material resumability fact only in chat.

For a newly registered qualification run, persist a PENDING checkpoint as required by the active workstream before relying on the run. At terminal status persist PASS or FAIL before repairing or promoting coverage. Historical artifacts remain immutable inputs.

## AI execution routing

Model choice is an execution-cost policy, never evidence authority.

Use the repository routing package under:

`research/greenfield-qualification/agent-workflow/`

Default policy:

```text
semantic/architectural planning and adversarial review -> normal GPT-5.6 Sol chat
bounded repository implementation                 -> Codex Terra
mechanical follow-up with semantics already fixed -> Codex Luna
hard root-cause escalation only                    -> Codex Sol
```

Escalate bounded implementation to Codex Sol only when evidence supports a difficult class such as a model/core representation defect, generic rules-core defect, architecture boundary, persistent replay/concurrency problem, or repeated failed Terra repair.

Luna must not adjudicate new Magic semantics, weaken tests, invent PASS evidence, or change qualification meaning.

## Completion discipline

Do not claim COMPLETE unless the full stated scope and its gates are actually satisfied. When blocked, persist the partial state and precise blocker; do not convert missing evidence into PASS.

Workstream-specific completion gates in current checkpoints/contracts override generic examples in this file.