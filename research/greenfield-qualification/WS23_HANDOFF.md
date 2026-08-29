# WS23 — actual-path failure adapters: card behavior

## Scope

WS23 owns only `CARD_BEHAVIOR_FAILURE` and consumes WS17 evidence read-only. It must not merge or rerun the WS17 Forge witness suite and must not modify the shared WS12 schema/gate.

## Frozen inputs

- Base: `d8c1ee0c08c7e7f0bc2bc86c70166ebc198e30d5`
- WS14 tree: `5725f47951938bc71af181cf1617e6b3be158804`
- WS12 outcome contract: `80743bdbc2950b00e422f3deb38f04111f30a4d4` (read-only)
- WS17 HEAD: `a5f68f9ec49d19d900e92e505654871d2267ba93` (read-only)
- WS17 successful run: `33264286138`
- WS17 witness artifact: `9718189742`, SHA-256 `7133a9b8fdf3246f6a756114396fba6a35cb8b9a28c4cc8622317ab0b0f03cba`
- Forge pin represented by the immutable WS17 witness: `8c7e9afb8e6caee88644b94e25da5852e36f8928`

## Detector design

The WS23 verifier deterministically selects a successful, state-asserting WS17 atomic witness without using any card name. It first requires the immutable baseline to have `execution=PASS`, `stdout_only=false`, and `expected == actual`.

Only inside the WS23 verification workspace, the expected semantic value is changed while the immutable WS17 actual value and trace hash remain untouched. The verifier must detect the resulting expected/actual mismatch and emit the retained WS12 public outcome `CARD_BEHAVIOR_FAILURE` with `state_committed=false`.

This demonstrates the required distinction from `ENGINE_FAILURE`: the pinned-Forge execution represented by the source witness succeeded, while the semantic verifier independently fails its controlled assertion.

Expected and actual semantic values are retained in hashed qualification evidence but are not copied into the public failure envelope. No pass/cancel/first/random/default/silent-skip fallback is permitted.

## Reachability adjudication

The current WS14 topology does not establish a production runtime callsite for the actual-card semantic witness verifier. WS23 therefore **does not invent a production adapter**. Its binding is `QUALIFIER_ONLY` and `production_reachable=false` for the implemented detector.

The WS12 category definition describes `CARD_BEHAVIOR_FAILURE` as production-reachable. Because WS23 cannot directly prove such a runtime callsite, WS25 must keep that production binding fail-closed unless independent integration evidence establishes it.

## Completion rule

`WORKSTREAM_COMPLETE=TRUE` requires a dedicated WS23 workflow to verify the exact bases and immutable WS17 artifact provenance, execute the controlled semantic mismatch detector, hash expected and actual evidence, prove a hidden-info-safe public payload, prove distinction from `ENGINE_FAILURE`, and assert that production reachability was not invented.

Overall `FAILURE_SEMANTICS` is not claimed by WS23.

## Final live evidence

Pending the dedicated branch-tip qualification run.
