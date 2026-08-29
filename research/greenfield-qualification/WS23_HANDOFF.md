# WS23 — actual-path failure adapters: card behavior

`WORKSTREAM_COMPLETE = TRUE`

## Provenance

- Repository: `moeendres-png/mage`
- Branch: `work/ws23-card-behavior-failure-adapter-20260829`
- Base / WS14 final HEAD: `d8c1ee0c08c7e7f0bc2bc86c70166ebc198e30d5`
- WS14 tree: `5725f47951938bc71af181cf1617e6b3be158804`
- WS12 retained outcome contract: `80743bdbc2950b00e422f3deb38f04111f30a4d4` (read-only)
- WS17 retained source HEAD: `a5f68f9ec49d19d900e92e505654871d2267ba93` (read-only)
- Forge pin represented by immutable WS17 evidence: `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- `TESTED_HEAD = bb066962376d48bbfa1ce42b96b4c8b57c30d72f`
- `FINAL_HANDOFF_HEAD = SELF`; this documentation-only commit is reported externally after creation.

## Immutable source evidence

WS23 does not rerun or merge WS17. It consumes the already-qualified WS17 witness artifact:

- WS17 run: `33264286138`
- WS17 artifact: `ws17-continuous-copy-control-witnesses`
- WS17 artifact ID: `9718189742`
- WS17 artifact SHA-256: `7133a9b8fdf3246f6a756114396fba6a35cb8b9a28c4cc8622317ab0b0f03cba`

The WS23 workflow independently verified the WS17 run HEAD, successful conclusion, artifact ID/digest, and the artifact's own internal hashes before semantic fault injection.

## Qualified detector

The verifier deterministically selects a successful state assertion from immutable WS17 evidence, requiring:

- `execution = PASS`
- `stdout_only = false`
- baseline `expected == actual`
- immutable Forge trace hash retained

Only in the WS23 verifier workspace it changes the expected semantic value. The actual pinned-Forge state is not modified. The resulting mismatch is detected and classified as exactly:

`CARD_BEHAVIOR_FAILURE`

This proves that a successful engine execution can independently fail semantic verification and therefore remains distinct from `ENGINE_FAILURE`.

The public failure envelope contains no expected/actual semantic values, uses `state_committed=false`, and does not coerce the mismatch to pass/cancel/default/first/random/silent skip.

## Reachability adjudication

- `production_binding = QUALIFIER_ONLY`
- `production_reachable = false` for this verifier
- no production runtime callsite for the actual-card witness verifier is established by the audited topology
- WS23 deliberately does **not** invent a runtime adapter

Therefore WS23 closes the qualifier/verifier detector semantics, but it does not claim that `CARD_BEHAVIOR_FAILURE` is a production-reachable runtime outcome. WS25 must preserve that distinction when adjudicating the global 16-category matrix.

## Dedicated qualification evidence

- Workflow run: `33273319809`
- Job: `99155610511`
- Run result: `SUCCESS`
- Tested HEAD: `bb066962376d48bbfa1ce42b96b4c8b57c30d72f`
- Artifact: `ws23-card-behavior-failure-evidence`
- Artifact ID: `9720758445`
- Artifact SHA-256: `f9084d2166460b4ea2a2c85af64aceee406003d8fc160030ff1846e8b401cba3`

The run directly emitted:

- `WS23_CARD_BEHAVIOR_FAILURE=PASS`
- `WS23_ENGINE_EXECUTION=PASS`
- `WS23_SEMANTIC_VERIFIER=FAIL_AS_CONTROLLED`
- `WS23_PRODUCTION_REACHABLE=FALSE`
- `WORKSTREAM_COMPLETE=TRUE`

Artifact hash verification passed for:

- `WS23_BASELINE.json`
- `WS23_CONTROLLED_EXPECTED.json`
- `WS23_IMMUTABLE_ACTUAL.json`
- `CARD_BEHAVIOR_FAILURE.json`
- `WS23_GATE.json`

## Evidence classification

- immutable WS17 pinned-Forge execution: `TECHNICALLY_CONFORMANT`
- WS23 controlled semantic mismatch detector: `TECHNICALLY_CONFORMANT` for qualifier/verifier behavior
- production runtime reachability of this detector: `NOT ESTABLISHED / production_reachable=false`

## Adjudication

- `CARD_BEHAVIOR_FAILURE qualifier detector = PASS`
- `ENGINE_FAILURE distinction = PASS`
- `hidden-info-safe public payload = PASS`
- `silent fallback absent = PASS`
- `production runtime binding invented = FALSE`
- `WORKSTREAM_COMPLETE = TRUE`
- `FAILURE_SEMANTICS_OVERALL_CLAIMED = FALSE`

This final handoff commit is documentation-only and does not alter the executable detector or its qualification evidence; no rerun is required solely for this commit.
