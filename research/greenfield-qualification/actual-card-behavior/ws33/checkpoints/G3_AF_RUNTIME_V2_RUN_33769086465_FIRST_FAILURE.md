# WS33 G3 AF runtime v2 — run 33769086465 first-failure adjudication

Status: `RUNTIME_GREEN_GATE_ASSERTION_BUG`

Evidence classification: `DIRECTLY_VERIFIED` for Actions/artifact/runtime outputs; `CODE_DERIVED` for the gate-root-cause adjudication.

## Exact run identity

- branch: `work/ws33-g3-final-closure-20260902`
- workflow: `WS33 G3 SVar AF runtime v2 hidden witness`
- run: `33769086465`
- job: `100694379650`
- workflow source HEAD: `7fc18ccd062278d8690e77c0b04fad44bc9b213b`
- workflow source TREE: `992da510930c5e0c9b919feb3e4319655e1f6aec`
- conclusion: `failure`
- artifact id: `9899227922`
- artifact digest: `sha256:ee3de852a4eedf3e96638a2c48ce8d549da9471d49b4b49df51259d3ca5bfb2e`

## What actually passed

The strengthened witness transform completed with:

- `WS33_G_SVAR_AF_HIDDEN_WITNESS=PASS`
- source = actual target script plus actual source SVar
- validity = Forge `Card.isValid`
- card-name branch = `0`
- path-id branch = `0`

The Maven execution itself completed successfully. The immutable artifact contains exactly 21 case-summary rows, and every row has:

- status `PASS`;
- empty runtime failure fields;
- stack admission `1`;
- stack resolution `1`;
- target-SVar reachability `>=1`.

For both Scry target consumers the strengthened run now records two authoritative decision events. In particular the formerly zero-branch source-dependent Scry path `forge-behavior-v2:a817142bdd146d535481895c85387094a2c7ad62` records:

- `TARGET_SELECTION`;
- `SCRY_BOTTOM_SELECTION`.

This proves that the source-dependent `ScryNum$ X` witness reached a positive Scry branch rather than the prior `scry(0)` no-op branch.

## Exact first material failure

The workflow's post-runtime Python gate hard-codes:

```text
if 'INPUT_CONFIRM' not in events: FAIL
```

That assertion is incorrect for the actual externalized Scry transport. The authoritative request/event kind emitted by the strengthened runtime is `SCRY_BOTTOM_SELECTION`, not `INPUT_CONFIRM`.

Therefore the Actions conclusion `failure` is caused by a qualification-gate decision-kind naming error after a green engine execution, not by a Forge rules/runtime failure and not by failure of the strengthened witness.

## Repair boundary

Repair only the runtime-v2 gate so that the positive Scry witness requires the actual authoritative Scry decision kind `SCRY_BOTTOM_SELECTION` (and retains the existing decision-count and all 21 runtime invariants). Do not weaken stack, target-reachability, status, failure-field, or source-shape checks. Do not add card-name/path-id branches.

The run itself is not promoted to qualification PASS because its workflow gate failed. A fresh Actions run after the gate repair is required.

Coverage promotion: `FALSE`

AF behavior v2 qualification: `UNKNOWN`

AF Hidden / Principal Observation: `UNKNOWN`

`WS33_COMPLETE = FALSE`

`TASK_COMPLETE = NO`
