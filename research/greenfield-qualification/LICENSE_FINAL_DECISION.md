# License and Third-Party Decision — WS03 Refresh

Status: **Q8 DEFERRED_PENDING_ARCHITECTURE_SELECTION**  
WS03 license/third-party subgate: **PASS**  
Audit base: `c0e42fb42c4a603aff4a76b1284f8271c12bfd42` / tree `fb06c61dd87b4b742722925cd7374d8f037e1f47`

This refresh supersedes the old `0ea93d09d80e5c126eccb3323b17f14542e5559a` assessment anchor for WS03 provenance only. It does **not** select a production architecture and does **not** provide a legal guarantee.

## Exact-pin license identities

- Forge `8c7e9afb8e6caee88644b94e25da5852e36f8928`: GPL-3.0 license text — `DIRECTLY_VERIFIED`.
- XMage `86d86b580cd7e1f30b51110d70cecae18c1ce452`: MIT — `DIRECTLY_VERIFIED`.
- phase.rs `fae406c4603f450797014f3ac8e8818b3d36c2a4`: `MIT OR Apache-2.0`, version `0.64.0` — `DIRECTLY_VERIFIED`.
- Manabrew `754ec2aeec495d67d7bb9b89d0fd67ee22281b46`: `AGPL-3.0-or-later`, version `3.21.10` — `DIRECTLY_VERIFIED`.
- Manabrew's exact `forge/` gitlink is `witchesofthehill/forge@192b5eab000069bbb8917a5df9d60d4a9128aa07`, a GitHub fork of `Card-Forge/forge`, with GPL-3.0 license text — `DIRECTLY_VERIFIED`.

Immutable file/blob provenance is in `LICENSE_INVENTORY.json`.

## Decision boundary

The following are complete for WS03:

- exact candidate and component license identities;
- exact-pin repository/tree/license provenance;
- copied/modified/vendored-code census for the audited research boundary;
- generated/transformed Scryfall and Wizards-source boundaries;
- modeled production usage modes covering linking, subprocess, network service, modification, copying/vendoring, distribution, and runtime dependency;
- explicit uncertainty labels for every architecture-dependent legal implication.

The following are intentionally **not** decided:

- which Rules Core/component topology will enter production;
- whether a selected in-process, subprocess, IPC, service, fork, or distribution topology satisfies any particular license obligation;
- final source-offer, notice, attribution, corresponding-source, network-use, or redistribution requirements;
- final rights for production bundling/serving of Scryfall-derived or Wizards-origin data/content;
- the complete transitive dependency/license notice set for a not-yet-selected production build.

Process separation alone is not a license conclusion. Upstream project statements about their own derivative/compatibility/network analysis are recorded as upstream declarations, not adopted as this project's legal conclusion. Architecture-dependent implications remain `UNKNOWN / LEGAL_REVIEW_REQUIRED`.

## Gate state

```text
all_candidate_license_identities_verified = true
all_candidate_usage_modes_documented = true
copied_or_vendored_code_inventory_complete = true
generated_data_boundary_documented = true
remaining_uncertainties_explicit = true
unsupported_legal_conclusions = 0

WS03_LICENSE_BOUNDARY_COMPLETE = TRUE
LICENSE_DECISION_COMPLETE = FALSE
Q8 = DEFERRED_PENDING_ARCHITECTURE_SELECTION
```

`LICENSE_DECISION_COMPLETE = FALSE` is expected: the final production license decision cannot be completed before a concrete architecture, packaging, service, modification, and distribution model is selected.

Authorities for this workstream:

- `LICENSE_INVENTORY.json` / `.md`
- `THIRD_PARTY_USAGE_MATRIX.json` / `.md`
- `THIRD_PARTY_BOUNDARY.md`
