# WS14 — Atomic Behavior Path Model & Witness ABI — Handoff

WORKSTREAM_COMPLETE: `TRUE`

BRANCH: `work/ws14-behavior-primitive-model-20260829`

BASE_SHA: `6828c7175345d3193d814406428c8ee6b54c1136`

HEAD: `1a80c05bb24608fd2b3b508f6feb32606bf1f01f`  
TREE: `520db3ba7cb7597df4d2eb246a918f395ad2984d`

The HEAD/TREE above are the exact WS14 implementation/workflow/manifest-pin revision qualified by the final Actions run. The generated-manifest commit is recorded separately below; the handoff commit itself is metadata-only and CI-skipped.

MANIFEST_RECORD_HEAD: `f4ddbb11bcdcd5ac6efd4191111942fa118c80cb`  
MANIFEST_RECORD_TREE: `57864999ee672127a106f7d0acbde278ae9a255b`

FORGE_PIN: `8c7e9afb8e6caee88644b94e25da5852e36f8928`

WS11 qualified implementation: `a604db2f8ebedfa9fad32fe71425ea2bfd031ec4`  
WS11 final evidence: run `33251464459`, job `99097754070`, artifact `9714505392`, digest `sha256:74be5debf765e76d3aa8ab8a868795193b8f5dc6b4856d95bf9e94b087a7d581`  
WS11 per-identity SHA-256: `1f46fc66d2049d65c7ede91700c0e76e38b3fb7c49c13bb394dd20aa6ea8ced7`

## Result

identity_count: `1678`  
old_full_script_signature_count: `1677`  
atomic_primitive_count: `174`

primitive_count_by_owner_family:

- `ACTION_COST_DECISION`: `76`
- `TRIGGER_REPLACEMENT_ZONE_SBA`: `53`
- `CONTINUOUS_COPY_CONTROL`: `21`
- `COMBAT_COMMANDER`: `10`
- `HIDDEN_RNG_REPLAY`: `14`

unresolved_binding_count: `1800`  
ambiguous_binding_count: `0`

Unresolved bindings are not silently promoted. They are emitted explicitly with `binding_status=UNKNOWN`, `ambiguity_status=UNKNOWN`, no primitive ID, no owner family, and `evidence_class=UNKNOWN`. The qualified artifact contains `888` keyword directives, `895` SVar expressions, and `17` alternate-mode directives in this explicit unresolved set. WS14 deliberately does not infer Java behavior from English/keyword similarity.

deterministic_materialization: `PASS` — the workflow materialized the complete corpus twice from the same immutable WS11 input and exact Forge pin and required byte-identical `PER_IDENTITY.atomic.jsonl`, `UNRESOLVED_BINDINGS.jsonl`, `WS14_PRIMITIVE_MANIFEST.json`, and runtime gate outputs.

primitive_manifest_sha256: `1137335dd7101df44940a2b0c8cacc5740e2aef0a24eceb541449dd10a5e6f7b`  
per_identity_atomic_sha256: `1e824702ed0dcd4af7d91e66b02ec37fc88dd9ace51ab20bf0abf1f53b605703`  
unresolved_bindings_sha256: `d35b3f2772b7638768e9d66d5e00eed8bc3488530be99e064be44c82e1cb5704`  
runtime_gate_sha256: `a49dbed6f2921d55dadf288376b3d5cca560b0189cc8dca69f8ea9fb4a2f20bf`  
unit_tests_sha256: `b44cf4769fcb47e13e9d45bad0ff6d3e439b222cb1260c35f93f10c3972d5aa7`

## Validation gates

- `1678` known Oracle identities processed: `PASS`
- exact WS11 identity/source provenance and old full-script signatures retained: `PASS`
- every resolved primitive has exactly one owner family from the closed five-family set: `PASS`
- duplicate primitive IDs with conflicting semantics: `0`
- silent unresolved mappings: `0`
- unresolved mappings explicitly `UNKNOWN`: `PASS`
- ambiguous identity/source bindings: `0`
- deterministic repeated materialization: `PASS`
- card-name production hacks: `0`
- synthetic behavior promotion: `FALSE`
- behavior PASS issued from parsing: `FALSE`
- witness ABI positive fixture: `PASS`
- witness ABI negative fixture: `PASS` — the schema-valid but semantically invalid multi-primitive witness is rejected because `primitive_exercise` does not cover `primitive_ids` exactly.

## Tests

Only WS14 validation and deterministic-materialization tests were required by this workstream:

`python3 -m unittest discover -s research/greenfield-qualification/actual-card-behavior/ws14 -p 'test_ws14_*.py' -v`

Result: `PASS`, `6/6`.

The workflow additionally validates both witness fixtures against `WS14_WITNESS_ABI.schema.json`, applies the semantic cross-field witness validator, materializes the model twice, compares deterministic outputs byte-for-byte, and enforces the manifest/gate invariants. Q1–Q5 are not part of this gate.

## GitHub Actions evidence

RUN_ID: `33255369528`  
JOB_ID: `99108011389`  
ARTIFACT_ID: `9715652489`  
ARTIFACT_DIGEST: `sha256:f87f9320703665ad5139140cb24299f9b9abb8f5f16ac5003747f9f9545e8e61`

Artifact: `ws14-behavior-primitive-model`

Artifact contents:

- `WS14_PRIMITIVE_MANIFEST.json`
- `PER_IDENTITY.atomic.jsonl`
- `UNRESOLVED_BINDINGS.jsonl`
- `WS14_GATE.runtime.json`
- `WS14_HASHES.sha256`
- `unit-tests.log`

The workflow verifies that the repository-bound `WS14_PRIMITIVE_MANIFEST.json` is byte-identical to freshly regenerated output. Independent qualifying runs reproduced the same manifest, per-identity, unresolved-binding, runtime-gate, and unit-test hashes listed above.

## Evidence classes

EVIDENCE_CLASSES: `CODE_DERIVED`, `TECHNICALLY_CONFORMANT`, `UNKNOWN`

- Forge script-to-engine dispatch bindings and exact provenance: `CODE_DERIVED`
- deterministic materialization, schema/semantic ABI gates, uniqueness/ownership gates: `TECHNICALLY_CONFORMANT`
- safely unresolved keyword/SVar/alternate-mode bindings: `UNKNOWN`

No WS14 result is `EXTERNALLY_RULE_VALIDATED`, because WS14 does not execute or adjudicate card semantics.

## Q6 boundary

Q6_ACTUAL_CARD_BEHAVIOR: `NOT_ADJUDICATED`

WS14 does **not** mark Q6 PASS and does **not** qualify any behavior merely because a primitive was parsed or resolved. It establishes the reusable atomic path decomposition, exact per-Oracle provenance, unique owner-family partition, and witness ABI for WS15–WS19.

## BLOCKERS

`NONE` for the WS14 scope.

The `1800` explicit `UNKNOWN` bindings remain downstream coverage work rather than a hidden WS14 PASS. They may be resolved systemically by later workstreams only with pinned implementation provenance; card-name exception tables or fuzzy mappings remain prohibited.

## NEXT_ACTION

WS15–WS19 may proceed independently by owner family using `WS14_PRIMITIVE_MANIFEST.json` and `WS14_WITNESS_ABI.schema.json`. Each emitted witness must prove actual exercise of every listed primitive via trace events and state assertions, retain decision/RNG tapes where applicable, and remain fail-closed for unresolved/unsupported paths. Integration must not infer Q6 PASS until downstream witness coverage is independently adjudicated.
