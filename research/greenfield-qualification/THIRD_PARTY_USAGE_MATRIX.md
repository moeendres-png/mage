# THIRD-PARTY USAGE MATRIX

Status: **WS03 SUBGATE PASS**  
Checked: 2026-08-28  
Audit base: `c0e42fb42c4a603aff4a76b1284f8271c12bfd42` / tree `fb06c61dd87b4b742722925cd7374d8f037e1f47`  
Q8: `DEFERRED_PENDING_ARCHITECTURE_SELECTION`

This matrix enumerates technically realistic production-use topologies without selecting one. Rows marked `MODELED` are topology models, not statements that the topology is legally sufficient. **Process separation, IPC, or network separation is never treated here as resolving license obligations.** Every production legal implication remains `LEGAL_REVIEW_REQUIRED` until a concrete architecture, packaging, modification, service, and distribution model is selected.

## Exact-pin candidate identities

| Component | Repository | Pin | Verified license | Fork? |
|---|---|---|---|---|
| Forge | `Card-Forge/forge` | `8c7e9afb8e6caee88644b94e25da5852e36f8928` | `GPL-3.0` | no |
| XMage | `magefree/mage` | `86d86b580cd7e1f30b51110d70cecae18c1ce452` | `MIT` | no |
| phase.rs | `phase-rs/phase` | `fae406c4603f450797014f3ac8e8818b3d36c2a4` | `MIT OR Apache-2.0` | no |
| Manabrew | `witchesofthehill/manabrew` | `754ec2aeec495d67d7bb9b89d0fd67ee22281b46` | `AGPL-3.0-or-later` | no |
| Manabrew Forge submodule | `witchesofthehill/forge` | `192b5eab000069bbb8917a5df9d60d4a9128aa07` | `GPL-3.0` | yes |

Exact license-file/blob provenance is authoritative in `LICENSE_INVENTORY.json`; repository-level license classifiers are supplementary.

## Usage modes

| Component | Mode | Modified | Linked | Subprocess | Copied | Vendored | Network service | Binary dist. | Source dist. | Runtime dep. | Evidence | Legal status |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| Forge | `unmodified_external_subprocess_private_runtime` | no | no | yes | no | no | no | no | no | yes | `MODELED` | `LEGAL_REVIEW_REQUIRED` |
| Forge | `modified_fork_external_subprocess` | yes | no | yes | yes | no | no | no | yes | yes | `MODELED` | `LEGAL_REVIEW_REQUIRED` |
| Forge | `linked_or_in_process_engine` | no | yes | no | yes | yes | no | yes | yes | yes | `MODELED` | `LEGAL_REVIEW_REQUIRED` |
| Forge | `wrapped_self_hosted_network_service` | no | no | yes | no | no | yes | no | no | yes | `MODELED` | `LEGAL_REVIEW_REQUIRED` |
| XMage | `forked_in_process_rules_core` | yes | yes | no | yes | no | no | yes | yes | yes | `MODELED` | `LEGAL_REVIEW_REQUIRED` |
| XMage | `isolated_jvm_process_or_service` | yes | no | yes | yes | no | yes | yes | yes | yes | `MODELED` | `LEGAL_REVIEW_REQUIRED` |
| phase.rs | `linked_rust_crate_or_fork` | yes | yes | no | yes | yes | no | yes | yes | yes | `MODELED` | `LEGAL_REVIEW_REQUIRED` |
| phase.rs | `external_process_or_service` | no | no | yes | no | no | yes | no | no | yes | `MODELED` | `LEGAL_REVIEW_REQUIRED` |
| Manabrew | `unmodified_self_hosted_network_service` | no | no | yes | no | yes | yes | no | no | yes | `MODELED` | `LEGAL_REVIEW_REQUIRED` |
| Manabrew | `modified_fork_self_hosted_network_service` | yes | no | yes | yes | yes | yes | no | yes | yes | `MODELED` | `LEGAL_REVIEW_REQUIRED` |
| Manabrew | `linked_or_embedded_components` | yes | yes | no | yes | yes | no | yes | yes | yes | `MODELED` | `LEGAL_REVIEW_REQUIRED` |
| Manabrew Forge submodule | `vendored_git_submodule_inside_manabrew` | yes | yes | no | no | yes | no | yes | yes | yes | `DIRECTLY_VERIFIED` | `LEGAL_REVIEW_REQUIRED` |

The boolean columns describe the modeled technical topology only. They do not encode copyright scope, derivative-work status, license compatibility, or satisfaction of source/notice obligations.

## Mode-specific uncertainty

### Forge — `unmodified_external_subprocess_private_runtime`

- Technical boundary: Pinned Forge executable/JVM is invoked as a separate local process; no source is copied into the production codebase under this modeled topology.
- Remaining uncertainty: GPL implications for this exact orchestration, any shipped executable, IPC contract, installation bundle and operational distribution remain UNKNOWN / LEGAL_REVIEW_REQUIRED. Process separation is not a conclusion about obligations.

### Forge — `modified_fork_external_subprocess`

- Technical boundary: A maintained Forge fork carries project changes and is executed out of process. The fork/source relationship is explicit; the runtime boundary remains a subprocess.
- Remaining uncertainty: Obligations for maintaining, distributing, offering source for, or otherwise conveying the modified Forge fork and any combined installer remain UNKNOWN / LEGAL_REVIEW_REQUIRED. Process separation does not resolve them.

### Forge — `linked_or_in_process_engine`

- Technical boundary: Forge code/binaries are incorporated into the same runtime/build product or otherwise linked/embedded rather than isolated as an external process.
- Remaining uncertainty: The legal characterization of the combined work, applicable GPL obligations, compatible licensing of project code, corresponding-source scope and distribution terms require legal review before selection.

### Forge — `wrapped_self_hosted_network_service`

- Technical boundary: A service wrapper exposes engine functionality over a network while Forge runs behind the service boundary.
- Remaining uncertainty: Network operation must not be assumed to eliminate GPL or other obligations; wrapper/IPC/service composition, hosting, deployment and any distribution remain UNKNOWN / LEGAL_REVIEW_REQUIRED.

### XMage — `forked_in_process_rules_core`

- Technical boundary: A project-maintained XMage fork is modified and used directly in the production runtime/build.
- Remaining uncertainty: MIT notice/license preservation is a verified license-text fact, but the exact production packaging, third-party dependency notices, Wizards/Scryfall data boundaries and any additional obligations remain architecture-dependent and require review.

### XMage — `isolated_jvm_process_or_service`

- Technical boundary: A modified XMage fork runs in a separate JVM/process or service and is controlled through an adapter/protocol.
- Remaining uncertainty: Process/service separation is technical only and is not used as a legal conclusion; packaging, notices, dependency licenses, deployment and distribution still require exact review.

### phase.rs — `linked_rust_crate_or_fork`

- Technical boundary: phase.rs is used as a linked Rust dependency or maintained fork inside the product build.
- Remaining uncertainty: The project must select and satisfy one permitted license path and all dependency/notice requirements for the concrete build; exact obligations remain LEGAL_REVIEW_REQUIRED until packaging is fixed.

### phase.rs — `external_process_or_service`

- Technical boundary: An unmodified pinned phase.rs build is invoked through a process or service boundary rather than linked into the controller.
- Remaining uncertainty: Technical separation does not itself determine license obligations; deployment, binary conveyance, selected dual-license path and transitive dependencies require architecture-specific review.

### Manabrew — `unmodified_self_hosted_network_service`

- Technical boundary: An exact unmodified Manabrew node is self-hosted and accessed over its service/protocol boundary; its own repository includes a vendored Forge submodule.
- Remaining uncertainty: AGPL network/source obligations, GPL treatment of the vendored Forge component, protocol/client composition, deployment and any distribution require concrete legal review. Upstream LICENSE.md analysis is not adopted as our conclusion.

### Manabrew — `modified_fork_self_hosted_network_service`

- Technical boundary: A project-maintained Manabrew fork, including its Forge submodule relationship, runs as a self-hosted service.
- Remaining uncertainty: Modified AGPL service obligations, corresponding/source-offer scope, Forge GPL component treatment, client/protocol relationship and deployment/distribution are LEGAL_REVIEW_REQUIRED.

### Manabrew — `linked_or_embedded_components`

- Technical boundary: Manabrew engine/components are embedded, linked, or copied into the same production code/build rather than used only via its network protocol.
- Remaining uncertainty: Combination of AGPL Manabrew code, GPL Forge component and project code is a high-impact legal boundary requiring explicit counsel/review before selection; no compatibility or obligation conclusion is made here.

### Manabrew Forge submodule — `vendored_git_submodule_inside_manabrew`

- Technical boundary: At the exact Manabrew pin, forge/ is a Git submodule pointing to witchesofthehill/forge@192b5eab000069bbb8917a5df9d60d4a9128aa07; that repository is a GitHub fork of Card-Forge/forge.
- Remaining uncertainty: The legal effect of this vendored relationship within any Commander Simulator Next deployment/distribution remains architecture-dependent and LEGAL_REVIEW_REQUIRED.

## Data-source modes

- **Scryfall bulk research transform:** current research tooling downloads `oracle_cards`, transforms selected identity/legality fields, and records source/payload provenance. Production bundling, redistribution, or serving is not selected and remains `UNKNOWN / LEGAL_REVIEW_REQUIRED`. Operational API guidance is not treated as a license grant.
- **Wizards rules reference:** the official Comprehensive Rules are treated as an external rules authority/reference. WS03 does not select wholesale production embedding or redistribution of Wizards-origin text/assets; any such future use remains `UNKNOWN / LEGAL_REVIEW_REQUIRED`.

## Gate

```text
all_candidate_license_identities_verified = true
all_candidate_usage_modes_documented = true
copied_or_vendored_code_inventory_complete = true
generated_data_boundary_documented = true
remaining_uncertainties_explicit = true
unsupported_legal_conclusions = 0
```

Machine-readable authority: `THIRD_PARTY_USAGE_MATRIX.json`.
