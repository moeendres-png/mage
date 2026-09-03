# WS33 G3 AF Principal Observation v4 — record root-cause checkpoint

Status: `FAIL_CLOSED_ROOT_CAUSE_IDENTIFIED`

Evidence classification: `DIRECTLY_VERIFIED` for run/job/artifact/source identity and the failing validator condition; `CODE_DERIVED` for the stale-contract diagnosis. AF Hidden / Principal Observation remains `UNKNOWN` until a corrected fresh run passes.

## Immutable run identity

- repository: `moeendres-png/mage`
- branch: `work/ws33-g3-final-closure-20260902`
- workflow: `WS33 G3 SVar AF principal observation v4`
- workflow source HEAD: `104f40216cf161363f2e2178c1bcbf27368c518d`
- workflow source TREE: `52d102c95a1b71dd7a869b248872e95ae25dbc39`
- run: `33756098495`
- job: `100650763479`
- job conclusion: `failure`
- first material failure: post-execution record validation
- artifact id: `9893663522`
- artifact name: `ws33-g3-af-principal-observation-v4-33756098495`
- artifact digest: `sha256:2c4fe512fca1e31228842f64db93b81e816f652af1cd189ac71d08c1a8b4b166`
- artifact created: `2026-09-03T12:40:25Z`

## Engine / harness result

The immutable artifact proves that the fresh AF execution itself completed:

- `game_completed=true`
- expected AF paths: `21`
- completed path rows: `21`
- external decision coverage: `1.0`
- internal AI fallbacks: `0`
- internal random fallbacks: `0`
- decision ambiguities: `0`
- transport hidden-info leaks: `0`
- cross-principal leak summary field: `0`
- coarse `pilot_visible_hidden_info_leaks`: `1`

The sole positive coarse hidden-visibility signal is the expected explicit reveal consumer:

`forge-behavior-21-choose-player-reveal-hand / ChoosePlayer / RevealHandEffect`

Its summary row is otherwise PASS/reachable/completed and carries `x[9]=1`, `x[10]=0`.

## Principal-scoped v4 attestation

`PRINCIPAL_OBSERVATIONS.jsonl` contains `16` events covering two principals and two distinct observed cards. For every `(principal, card_observation_id)` pair, the observed lifecycle is exactly:

1. `SERVER_GRANT`
2. `SNAPSHOT_VISIBLE`
3. `SERVER_REVOKE`
4. `SNAPSHOT_HIDDEN`

The visible snapshot exposes the fixture identity `Linden Harbor Mentor`; the post-revoke snapshot is hidden. Grants and revocations are balanced. The same observed card identities are represented for both principals, proving cross-principal attribution rather than a single-principal shortcut.

Artifact-local hashes retained during adjudication:

- `record/process.json`: `sha256:6c1cc21fe6ba4167a0cad40e7e7fbb17042225448bd9dd68b44f46e18a39998f`
- `record/PRINCIPAL_OBSERVATIONS.jsonl`: `sha256:010133fde68549769f9dd71a2abfacc20d451f11d5ae2e9b53b5564c8558599`
- `record/case-summary.tsv`: `sha256:2e78155166e6ed9c112b51cb58adf0bf45401590199facc033d58f9db7f5c8f`

## First material root cause

The post-run validator in `.github/workflows/ws33-g3-svar-af-principal-observation-v4.yml` rejects every positive `case-summary.tsv` coarse hidden-visibility signal via the stale predicate:

```python
x[9] != '0'
```

The v4 adjudicator `ws33_adjudicate_g_principal_observation_v4.py` repeats the same stale all-zero assumption even though its base adjudicator already classifies `forge-behavior-21-choose-player-reveal-hand` specially and requires a positive historical coarse reveal signal only for that path.

This creates an internal gate-contract contradiction:

- base G adjudication: the RevealHand path must retain a positive coarse reveal signal; unrelated paths must remain zero;
- v4 principal adjudication / workflow record validator: every path must have coarse signal zero;
- v4 principal trace: independently proves the authorized temporary reveal and complete revocation lifecycle.

Therefore run `33756098495` is not evidence of an engine failure. It is a fail-closed qualification failure caused by duplicated pre-v4 validation logic in the evidence layer.

## Coarse probe semantics retained, not waived

The historical WS05 coarse probe increments `pilot_visible_hidden_info_leaks` when a hidden object's identity is visible while its server-side authorization predicate is not represented as authorized at that sampling point. It does not encode the complete principal-scoped temporary-reveal lifecycle.

The corrective contract MUST NOT rewrite, suppress, or globally waive this metric. Instead:

- the positive coarse signal remains raw evidence;
- only the known explicit RevealHand path may carry it;
- all unrelated paths must still have coarse value `0`;
- the positive signal is acceptable only when v4 principal evidence proves exact grant / visible / revoke / hidden lifecycle;
- transport leakage and cross-principal leakage must remain `0`;
- missing, malformed, unbalanced, or incomplete lifecycle evidence must fail closed.

## Required systemic repair

1. Remove the duplicate all-path `x[9] == 0` assumption from the v4 layer while retaining the base path-specific coarse classification.
2. Bind any permitted positive coarse reveal signal to successful v4 lifecycle attestation; no path-id-only waiver.
3. Keep cross-principal, transport, ambiguity, fallback, reachability, completion, and path-count checks fail closed.
4. Make the workflow record step call the authoritative v4 adjudicator instead of maintaining a second divergent row-only legality contract.
5. Add regression cases proving:
   - expected RevealHand coarse signal + complete lifecycle = PASS;
   - positive coarse signal without complete revocation lifecycle = FAIL;
   - positive coarse signal on an unrelated path = FAIL;
   - cross-principal leakage remains FAIL.

## Serial execution boundary

No rerun is authorized from this checkpoint. The next material action is the validator/adjudicator repair plus deterministic local regression proof, committed separately. Only after that repair is persistent may the focused AF principal-observation workflow be dispatched again.

AF Behavior: `21/21 PASS`

AF Decision: `9/9 PASS`

AF RNG: `4/4 PASS`

AF Replay: `12/12 PASS`

AF Hidden / Principal Observation: `UNKNOWN`

Coverage promotion: `FALSE`

`WS33_COMPLETE = FALSE`

`TASK_COMPLETE = NO`
