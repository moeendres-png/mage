# WS33 ABC A-REST-SVAR AF8 — Run 34165574477 — TERMINAL FAIL

## Identity

- Branch: `work/ws33-g3-final-closure-20260902`
- Run: `34165574477`
- Job: `101875828886`
- Frozen source HEAD: `6120ca3ee9754cbad4600ee45008ee2455b95465`
- Frozen source TREE: `264e881c43c643363f0a499764c0a81ae8285c4e`
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- Route artifact: `9998291348`
- Route artifact SHA256: `646594434eb987009561127f012bd0d974dcec97e67bef0bf478294f1fd9d0e9`
- Expected AF8 path count: `8`
- Expected AF8 path-set SHA256: `10c3825fa3ba1e58aadcaacad1012263c4201438cf8c694db6cb10b3bae7b0f1`

## Terminal workflow result

`FAIL`

Step outcomes relevant to adjudication:

- Strict decision/path parser regression tests: `PASS` (`12/12`)
- Route bundle verification: `PASS`
- Observation-only runtime overlays: `PASS`
- Fresh AF8 Record: `SUCCESS`
- Record evidence postconditions: `PASS`
- AF8 Replay: `SUCCESS`
- Record/Replay byte comparisons for decision options, RNG, effects, client decisions, play stages and normalized play-state log: `PASS`
- Adjudicate AF8 evidence: `FAIL`
- Always-run evidence seal: `SUCCESS`
- Artifact upload: `SUCCESS`

## Exact terminal failure

The standalone adjudicator terminated before its post-adjudication `jq` assertions and before a successful gate could be emitted:

```text
Traceback (most recent call last):
  File ".../ws33_adjudicate_a_rest_svar_af8.py", line 153, in <module>
    raise SystemExit(main())
  File ".../ws33_adjudicate_a_rest_svar_af8.py", line 110, in main
    record_integrity = assert_exact_once_path_evidence(
  File ".../ws33_decision_path_evidence.py", line 304, in assert_exact_once_path_evidence
    raise EvidenceError(f"{prefix}: DECISION_ID {decision_id!r} missing path_id")
ws33_decision_path_evidence.EvidenceError: WS33_A_REST_SVAR_AF8_RECORD: DECISION_ID 'a-rest-svar-af8-alternatives-1-remote' missing path_id
```

Because the adjudicator did not complete, the sealing step correctly materialized a fail-closed gate with:

```json
{
  "gate": "WS33_A_REST_SVAR_AF8_RUNTIME",
  "result": "FAIL",
  "reason": "ADJUDICATION_DID_NOT_COMPLETE",
  "run_id": "34165574477",
  "run_attempt": "1",
  "source_commit": "6120ca3ee9754cbad4600ee45008ee2455b95465",
  "source_tree": "264e881c43c643363f0a499764c0a81ae8285c4e",
  "coverage_mutated": false,
  "coverage_promotion": false
}
```

## Failure classification

Evidence classification: `DIRECTLY_VERIFIED` from immutable GitHub Actions job log and artifact metadata.

Root-cause class: `QUALIFICATION_EVIDENCE_CONTRACT_MISMATCH`.

This run does **not** establish a Forge semantic defect, card-behavior defect, rules defect, `CARD_BEHAVIOR_FAILURE`, or route-projection defect. Fresh Record and Replay both executed successfully. The failure is confined to the qualification/adjudication boundary: a remote-client evidence decision named `a-rest-svar-af8-alternatives-1-remote` has no `path_id`, while the current exact-once path-evidence assertion rejects every non-setup null-path decision.

The semantic role of this remote-client decision must be inspected before modifying the contract. The next repair must preserve fail-closed `path_id` requirements for production/gameplay decisions and may only exempt or reclassify the event if source evidence proves it is auxiliary evidence rather than a path-bound discretionary rules decision.

## Artifact identity and seal

- Artifact ID: `10034108017`
- Artifact name: `ws33-abc-a-rest-svar-af8-34165574477`
- Artifact uncompressed/upload metadata size: `538807994` bytes
- Uploaded artifact ZIP SHA256 reported by GitHub Actions: `5e300282cbfab475d4291b072b1c12c19ac29b64843e93b4d5cc8676b36bcf49`
- Always-run root seal: `PASS`
- Root `SOURCE_CHAIN.json`: emitted
- Root `SHA256SUMS`: emitted
- Internal `sha256sum -c SHA256SUMS`: `PASS`
- `SOURCE_CHAIN_ENTRY_COUNT=7`

The connector refused a separate artifact download because the artifact exceeds its current `536870912`-byte maximum. Therefore the outer ZIP SHA256 is recorded from GitHub Actions upload evidence and is **not** claimed as a separately rehashed local download. The workflow log directly proves successful verification of the sealed internal file manifest.

## Coverage semantics

```text
coverage_mutated=false
coverage_promotion=false
```

No WS33 coverage promotion is authorized by this run. Authoritative coverage remains unchanged until an immutable successor qualification passes all required gates and later cross-certification authorizes promotion.

## Repair invariant

Before any source edit:

1. inspect the producer/source of `a-rest-svar-af8-alternatives-1-remote`;
2. determine whether it is a path-bound gameplay decision or auxiliary remote-client evidence;
3. preserve strict missing-`path_id` rejection for gameplay decisions;
4. add a focused regression proving the intended distinction;
5. rerun AF8 from a newly frozen source HEAD/TREE rather than reclassifying this historical failure.
