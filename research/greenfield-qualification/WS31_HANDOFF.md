# WS31 — HIDDEN INFORMATION / RNG / SEMANTIC REPLAY CLOSURE — HANDOFF

## Canonical status

**STATUS: BLOCKED / FAIL-CLOSED**  
**WS31_FAMILY_GATE: FAIL**  
**WORKSTREAM_COMPLETE: FALSE**  
**GLOBAL_Q6_CLAIM: FALSE**

This handoff intentionally does **not** claim WS31 completion. The live qualification evidence proves that marking the family PASS at the current source boundary would violate the WS26 shared-harness contract and the post-WS26 ownership/dependency model.

## Repository / branch

- repository: `moeendres-png/mage`
- branch: `work/ws31-v2-hidden-rng-replay-20260830`
- WS26 qualified model source HEAD: `206a39cbaa3eeb98b10c2ddc36d51fe5b1b2f5ef`
- WS26 qualified model source TREE: `837f445f78bb26462653c58baf1532e294151b10`
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- WS01 strict-decision prerequisite: `bf089ea806f54a9bbb64ede205915729e3629684`
- WS05 hidden-info prerequisite: `554bb06af0dd5e542ff8bbfd5e96054a74642d3a`
- WS06 RNG/replay prerequisite: `e23af2b621f2e318014491b8a84146ed4ad3bed6`

## Immutable WS26 source evidence

Verified and consumed:

- WS26 run: `33283478862`
- WS26 job: `99182488884`
- WS26 artifact: `9723722686`
- WS26 artifact SHA-256: `b9e1fc4fd792b0baa1da1c17e3bbc9e01b2557d4b73b8590e680679f53b59883`
- WS26 V2 path count: `4280`
- WS31 owner-family path count: `81`

The immutable WS26 manifest/partition assigns exactly 81 paths to `HIDDEN_RNG_REPLAY`:

- private-state evidence required: 61
- RNG evidence required: 57
- semantic replay required: 80
- decision evidence required: 80

Implementation-family distribution:

- `DigEffect`: 38
- `ScryEffect`: 8
- `DigUntilEffect`: 8
- `PeekAndRevealEffect`: 7
- `SurveilEffect`: 4
- `FlipCoinEffect`: 3
- `ShuffleEffect`: 3
- `RevealHandEffect`: 2
- `RevealEffect`: 2
- `DiscoverEffect`: 2
- `RearrangeTopOfLibraryEffect`: 1
- `ManifestEffect`: 1
- `ClashEffect`: 1
- `TwoPilesEffect`: 1

## First WS31 qualification implementation

Initial implementation commit:

- code SHA: `157f31ef9b8539b4f9b9bc4614bebbd3c2239dc9`
- tree: `b06502528ba2e5ba38bbab2c4fbda034569c90f1`

Files introduced:

- `.github/workflows/ws31-v2-hidden-rng-replay.yml`
- `research/greenfield-qualification/actual-card-behavior/ws31/ws31_prepare_cases.py`
- `research/greenfield-qualification/actual-card-behavior/ws31/ws31_finalize.py`
- `research/greenfield-qualification/actual-card-behavior/ws31/forge-overlay/Ws31HiddenRngReplayQualificationTest.java`

The case materializer binds every one of the 81 V2 IDs to its exact pinned-Forge source path, source line, directive, token, Oracle identity, implementation target and exact script. The campaign runs a real four-player Commander `UnifiedNetworkHarness`, overlays the qualified WS01/WS05/WS06 strict-decision/hidden-info/RNG-replay instrumentation, records decision/RNG tapes, and performs a fresh-JVM replay.

## Qualification runs

### Run 1

- run: `33286159036`
- job: `99189611399`
- head: `157f31ef9b8539b4f9b9bc4614bebbd3c2239dc9`

Verified successful stages:

- exact WS26 boundary / ownership
- immutable WS26 artifact verification including internal hashes
- exact WS01/WS05/WS06/Forge pins
- exact 81-case materialization
- overlay application
- Forge compile
- Process A record campaign
- Process B fresh-process replay

Fail-closed stage:

- public/private evidence finalization

The original workflow intentionally skipped the immutable PASS artifact after the failing finalizer.

### Run 2 — diagnostic-preserving rerun

Diagnostic-preservation commit:

- code SHA: `c0c628d6dafb2908f4713fb095077662bfd7bffa`
- tree: `325bd13469add01b3ade5919839193dbce22a992`

Run:

- run: `33303678035`
- job: `99236303823`
- head: `c0c628d6dafb2908f4713fb095077662bfd7bffa`
- diagnostic artifact: `9729827884`
- diagnostic artifact digest: `sha256:f336d0f79841caa5e36954178bd588fda414b3bb5f4c6ba53ca7620829f05d9f`

Again successful:

- boundary / immutable WS26 artifact / exact pins
- 81-case materialization
- overlays
- compile
- Process A record
- Process B fresh-process replay

The finalizer again failed closed, but the new `if: always()` diagnostic artifact preserved the raw private tapes, both case summaries, process metadata, public FAIL gate and inventories without weakening the PASS-only immutable qualification artifact.

## Direct diagnostic results

From diagnostic artifact `9729827884`:

- case rows: 81
- Process A execution status: 79 PASS / 2 FAIL
- Process B execution status: 79 PASS / 2 FAIL
- replay-required paths: 80
- semantic replay divergence: **0**
- `all_replay_required_paths_zero_divergence = true`
- `decision_tape_missing_where_required = 47`
- RNG-required paths without per-path attributed RNG tape: 39
- hidden paths with current probe leak deltas: 50
- current finalizer path failures: 66
- current `WS31_FAMILY_GATE = FAIL`
- current `WORKSTREAM_COMPLETE = false`

The two direct execution failures are reproducible in both record and replay:

1. `forge-behavior-v2:47e7c38e8a2842670b6877f12667bf6f2a4958ed` — `RevealEffect`, source card `Singe-Mind Ogre`  
   Failure: `UNSUPPORTED_DECISION_PATH: legacy GUI input cannot block while the external decision boundary is active; unsupported synchronized input: InputConfirm`

2. `forge-behavior-v2:efe2eeacc2950f7a80e8381d0d419960c1b25c30` — `RevealHandEffect`, source card `Night Terrors`  
   Same strict-decision failure on `InputConfirm`.

No silent fallback occurred. The production-reachable unsupported decision paths failed closed as required.

## Critical conformance finding: current runner cannot be promoted to PASS

The WS26 shared harness contract explicitly forbids:

- `direct_effect_resolve_bypass`
- `cost_bypass`
- `target_bypass`
- `stack_priority_bypass_when_required`
- hidden-info / RNG recording bypasses

The current WS31 exploratory runner reconstructs the exact script with `AbilityFactory.getAbility(...)` and executes the effect with `sa.resolve()` after qualification-side target binding. This was useful to isolate the hidden/RNG/replay layer and produced strong diagnostic evidence, but it is **not a conformant final V2 behavior witness** under the authoritative WS26 contract. Therefore its 79 successful direct resolutions must not be promoted to behavior PASS.

Evidence classification for those direct-effect diagnostic executions remains supporting / diagnostic evidence, not a final V2 PASS witness.

## Critical dependency finding: 80/81 paths depend on ACTION_COST_DECISION

Direct inspection of the immutable WS26 V2 manifest shows:

- 80 WS31 paths have `cross_family_dependencies = ["ACTION_COST_DECISION"]`
- 1 path (`ManifestEffect`) has no cross-family dependency

This exactly matches the 80 paths requiring decision/replay evidence.

Live GitHub verification on 2026-08-30 shows target branch:

`work/ws27-v2-action-cost-decision-20260830`

still at:

`206a39cbaa3eeb98b10c2ddc36d51fe5b1b2f5ef`

which is the WS26 base itself. No qualified WS27 action/cost/decision closure is currently available for WS31 to consume.

Consequently, attempting to replace the missing ACTION_COST_DECISION behavior inside WS31 would violate workstream ownership and create a second action/cost/decision rules layer. This is explicitly disallowed by the project architecture.

## Hidden-info diagnostic interpretation

The WS05 probe is an adversarial observer over decoded client views and strict decision/replay payloads. The current WS31 direct-mutation campaign repeatedly injects hidden-zone cards directly into the live game state while transport synchronization is active. The resulting large leak counter is therefore not safe to dismiss as cosmetic, but it also cannot be used as a final per-path hidden-info adjudication because the campaign itself bypasses the conformant action/zone transition path.

The final conformant WS31 rerun must establish each private transition through the qualified rules-core path and retain actual per-principal decoded transport observations. Filling non-requesting principals with synthetic zero-count rows is not sufficient proof of principal-scoped visibility.

## RNG diagnostic interpretation

Fresh-process semantic replay is already strong: all 80 replay-required paths reproduced the canonical semantic before/after digests exactly.

However, 39 of 57 RNG-required paths currently have no RNG event attributed to the direct-effect interval. A final witness must not manufacture synthetic RNG merely to satisfy the counter. It must bind RNG evidence to the qualified rules-core path that establishes or consumes the random/hidden ordering relevant to that V2 path, with a named stream and retained tape.

## Required unblock sequence

WS31 may be truthfully completed only after all of the following are available:

1. **ACTION_COST_DECISION closure is qualified and consumable** for the 80 cross-family-dependent WS31 paths.
2. The strict external decision boundary includes a rules-core adapter for the production-reachable `InputConfirm` paths demonstrated above; no legacy GUI blocking and no fallback.
3. WS31 replaces `AbilityFactory ... -> sa.resolve()` as the final witness route with the actual-card/rules-core action, cost, target, stack/priority and resolution path required by WS26.
4. Hidden-info evidence is collected from actual principal-scoped decoded client observations for each required private transition.
5. RNG evidence is tied to named rules-core RNG streams/tapes for all 57 required paths without injecting irrelevant synthetic draws.
6. The full 81-path campaign is recorded and replayed in fresh processes.
7. Only then may the hard gate require and prove:
   - `private_paths_principal_scoped = true`
   - `unauthorized_private_leaks = 0`
   - `all_random_paths_named_rng = true`
   - `all_random_paths_have_rng_tape = true`
   - `all_replay_required_paths_zero_divergence = true`
   - `decision_tape_missing_where_required = 0`
   - `WS31_FAMILY_GATE = PASS`
   - `WORKSTREAM_COMPLETE = TRUE`
8. The final immutable artifact must then be independently downloaded and its internal `WS31_HASHES.sha256` verified before this handoff is replaced by a completion handoff.

## Official rules authority

Current official Comprehensive Rules were independently checked against Wizards' rules page and the effective 2026-08-07 text. WS31-relevant references include:

- 401.2 — library hidden/order restrictions
- 402.3 — hand visibility
- 608.2c-d — choices and resolution
- 701.20 — reveal
- 701.22 — scry
- 701.24 — shuffle
- 701.25 — surveil
- 701.30 — clash
- 701.40 — manifest
- 701.57 — discover
- 705 — coin flips

Sources:

- `https://magic.wizards.com/en/rules`
- `https://media.wizards.com/2026/downloads/MagicCompRules%2020260807.txt`

## Evidence classification

- WS26 pins, partition counts, dependency count, workflow stage results, diagnostic artifact metadata and raw diagnostic counts: **DIRECTLY_VERIFIED**
- exact source-script extraction / implementation-target binding: **CODE_DERIVED**
- 80-path fresh-process semantic replay equality in the diagnostic campaign: **TECHNICALLY_CONFORMANT for replay mechanics only**, not a final V2 behavior PASS because the exercise path violates the WS26 final-witness route contract
- official Magic rule adjudication: **EXTERNALLY_RULE_VALIDATED**
- final 81-path behavior qualification: **UNKNOWN / NOT PASS** until the unblock sequence is satisfied

## No overclaim

This branch does not claim:

- global Q6 PASS
- Architecture Freeze
- production readiness
- full actual-card behavior PASS for the 81 WS31 paths
- that source presence/parsing/import is behavior proof
- that the current direct-effect diagnostic runner is a final conformant witness

The correct canonical outcome at this point is **fail-closed dependency handoff**, not a fabricated PASS.
