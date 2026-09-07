# AF8 run 34064602879 — verified root cause

Date: 2026-09-07. TERMINAL_RESULT=FAIL. COVERAGE_PROMOTION=FALSE.

## Immutable identity and independent verification

- SOURCE_HEAD: 84fd0406906885e8c841dd06ef4230b3cc1cc3b4
- SOURCE_TREE: 28e9269127f4242c9d8b25782618e91f7bab1510
- RUN: 34064602879; JOB: 101571045115
- ARTIFACT: 9998600937, ws33-abc-a-rest-svar-af8-34064602879
- ZIP bytes: 538169679
- Independently computed ZIP SHA256: 2cf9c070ef04249eece466ce0b627b7e2c7a9270b57b54c923a1a5472361f3ec
- ZIP digest equals live GitHub metadata. All 6174 file entries read through ZIP CRC validation.
- Three available SHA256SUMS manifests: routes/, routes/cases/, routes/cases/topology/. All 25 declared entries verify, zero missing/mismatched entries.
- Root SHA256SUMS is ABSENT. This absence is not waived or called PASS.
- Full job log inspected for runtime/adjudicator/packaging boundaries. Record and Replay succeeded; fail-closed adjudication failed.
- Reconstructed harness, normalized to CI LF line endings, SHA256: ea824055e9513d92d8344b4bc889acd39a3b0e73cc6526918859015cb6210d33. Exact match to frozen job harness.sha256.

## Primary cause: PATH_ROUTE_PROJECTION

The inherited writeEvidence serializes decision-events-with-path.tsv column zero using enc(path), i.e. Base64 UTF-8. The AF8 inline adjudicator compares that encoded column directly against cleartext effective path IDs.

Direct artifact result for BOTH Record and Replay:

- cleartext comparison matches 0/8 paths;
- strict Base64 decoding matches exactly all 8 expected paths;
- per-path decision counts: 2,2,3,2,2,2,2,3 (18 total);
- five additional events have the explicit setup attribution `null`;
- every attributed event is ACCEPTED, actor=principal=1;
- the only original failure messages are record:decision_path_coverage and replay:decision_path_coverage.

This is a verifier wire-format defect, not evidence that Forge failed to emit decisions. Repair the parser, reject malformed/noncanonical encoding, duplicate principal/event identities, foreign paths, and missing paths; never infer missing evidence.

## Additional independently observed acceptance gaps

1. OTHER / EVIDENCE_PACKAGING: root SHA256SUMS and SOURCE_CHAIN are written after the failing adjudication command. Failure skips them while upload still runs. Move complete manifest/source-chain sealing into an always-run step before upload. Do not modify this historical archive.
2. OBSERVATION_CONTRACT: both PRINCIPAL_OBSERVATIONS files are empty. The old lifecycle loop accepts empty input vacuously. The eight target shapes use Battlefield/Graveyard targets (seven ChangeZone-to-Hand, one Pump). Temporary hidden grants must not be manufactured for public target selection. Nevertheless actual, per-path client confidentiality samples and transition evidence are required; empty temporary-grant traces alone cannot certify them. The frozen WS05 probe already exposes real per-path/client sample counts and mismatch counts that can be captured without altering rules.
3. HARNESS_FIXTURE_LIFECYCLE / SEMANTIC_REPLAY: semanticState records card names/zones/life only. It omits keywords, characteristics and target lineage. The Pump target with TargetMax=X therefore has no positive Fear assertion. Its recorded before/after text only proves source spell movement Hand->Graveyard, not positive target-effect execution. Do not promote that path on targetExecutions>0 alone. Use authoritative execution and positive target/state evidence, not card-name branches or injected results.

## Rules authority

Official rules page checked live: https://magic.wizards.com/en/rules . Its current text link is https://media.wizards.com/2026/downloads/MagicCompRules%2020260819.txt (document states effective August 7, 2026).
CR 400.2 distinguishes public Battlefield/Graveyard from hidden Hand/Library. CR 115.1/601.2c/700.2c bind target selection to the applicable spell/mode. These support the visibility/target obligations, not an engine-wide rules PASS.

## Classification and continuation

Archive identity, contents, counts, exact failure and parser mismatch: DIRECTLY_VERIFIED.
Missing positive characteristic/target assertions and packaging control flow: CODE_DERIVED with runtime evidence gaps directly observed.
Public-zone distinction: EXTERNALLY_RULE_VALIDATED for cited rules only.

Next: repair strict path decoding and unconditional evidence sealing with negative regression tests. Preserve fail-closed acceptance for missing per-path confidentiality and positive effect evidence; capture those through actual runtime before any AF8/A57 PASS or coverage promotion. Do not rerun valid G/A1/Direct31 predecessors.

WS33_COMPLETE=FALSE. TASK_COMPLETE=NO. Existing operational coverage remains 4188 total, 488 PASS, 3700 UNKNOWN, 0 FAIL, 0 UNSUPPORTED; this is the persisted successor frontier, not a new promotion.
