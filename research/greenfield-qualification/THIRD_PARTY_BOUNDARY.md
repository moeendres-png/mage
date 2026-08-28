# Third-Party Boundary — WS03 Exact-Pin Refresh

Status: **WS03 SUBGATE PASS**  
Q8: `DEFERRED_PENDING_ARCHITECTURE_SELECTION`  
Audit base: `c0e42fb42c4a603aff4a76b1284f8271c12bfd42`  
Audit tree: `fb06c61dd87b4b742722925cd7374d8f037e1f47`

This is a technical provenance and boundary record, not a legal guarantee and not an architecture selection. Verified license text, verified/code-derived technical relationships, modeled future usage topologies, and legal interpretation are kept separate. **Process separation, IPC, or service separation is not treated as resolving license obligations.** Unknown legal implications are recorded as `UNKNOWN / LEGAL_REVIEW_REQUIRED`.

## Exact software boundaries

| Component | Repository | Exact pin / tree | Exact-pin license identity | Provenance |
|---|---|---|---|---|
| Forge | `Card-Forge/forge` | `8c7e9afb8e6caee88644b94e25da5852e36f8928` / `c634b817e037c4531051859f7d00805ffd74931e` | GPL-3.0 license text | `LICENSE` blob `e72bfddabc15be5718a7cc061ac10e47741d8219` |
| XMage | `magefree/mage` | `86d86b580cd7e1f30b51110d70cecae18c1ce452` / `3dbfaec4f8f411374535493c088cf4df09822d9f` | MIT | `LICENSE.txt` blob `3575e469d848ca405ccc8d0ac9d711c94120eb45` |
| phase.rs | `phase-rs/phase` | `fae406c4603f450797014f3ac8e8818b3d36c2a4` / `c23ab64340c6c39062fda5149895947112b77e36` | `MIT OR Apache-2.0` | `LICENSE-MIT` `757ab5c…`, `LICENSE-APACHE` `f5c2a72…`, `Cargo.toml` `d782785…`; version `0.64.0` |
| Manabrew | `witchesofthehill/manabrew` | `754ec2aeec495d67d7bb9b89d0fd67ee22281b46` / `00bbd0644ba47aec420d82283053a9121c7019ec` | `AGPL-3.0-or-later` | `LICENSE.md` blob `d37485c56ae7a4564e321d4aac35e9b99e1b7d9e`; AGPL text blob `be3f7b28e564e7dd05eaf59d64adba1a4065ac0e`; version `3.21.10` |
| Manabrew Forge component | `witchesofthehill/forge` | `192b5eab000069bbb8917a5df9d60d4a9128aa07` / `5c3ceb72012385ed18a223628d953e170b1ae5f5` | GPL-3.0 license text | GitHub fork of `Card-Forge/forge`; `LICENSE` blob `e72bfdd…`; Manabrew `.gitmodules` blob `9f2156f0ca7ce5e9a7512bec63da1c2152e61211` |

Manabrew's own `LICENSE.md` describes its Rust engine as a Forge rewrite, its `forge/` component as vendored GPL code, and its own code as AGPL-3.0-or-later. Those statements are recorded as **upstream declarations**, not adopted as a Commander Simulator Next legal conclusion.

## Copied, modified, and vendored-code census

At the audit base:

- `moeendres-png/mage` is itself a GitHub fork of `magefree/mage`; XMage-derived source is therefore present by fork history/inheritance. WS03 did not create that copy.
- The direct Forge research lane keeps the full Forge checkout external. The repository does contain the research-only diff artifact `research/greenfield-qualification/forge-patches/strict-decision-boundary.patch` (blob `17eaa13c8480ab25234e7d83d78117da62298547`) and its apply script (blob `ca8a2da57d58a2b39559d27db26e114b3e9c2f33`). The patch is applied to an ephemeral qualification checkout; it is not a production distribution decision.
- No new phase.rs or Manabrew source vendor subtree was identified in the audit host at the audited base.
- Manabrew itself has a `forge/` Git submodule whose configured URL is `https://github.com/witchesofthehill/forge.git`; the exact gitlink is `192b5eab000069bbb8917a5df9d60d4a9128aa07`.
- Whether a future distribution/combination of the Forge patch or any selected engine topology creates specific obligations is not adjudicated here: `LEGAL_REVIEW_REQUIRED`.

This census is technical. It does not assert that the absence of a copied source tree, or the presence of a subprocess boundary, changes or eliminates license obligations.

## Generated/transformed data boundary

### Scryfall

The qualification path fetches Scryfall bulk metadata from `https://api.scryfall.com/bulk-data`, selects `type=oracle_cards`, hashes the payload, and transforms selected fields through `research/greenfield-qualification/scryfall_oracle_index.py` (blob `546855bb1e04caf54d1c7c0e06746f9dbe701d96`). The qualification index contains identity and rules-adjacent metadata such as `name`, `face_names`, `oracle_id`, `scryfall_id`, Commander legality, color identity, and type line.

This proves provenance and transformation, not a production redistribution grant. WS03 did not verify a general Scryfall data license sufficient for future bundling/redistribution/serving. Such use is `UNKNOWN / LEGAL_REVIEW_REQUIRED`. Current API/bulk operational guidance is not treated as a license grant.

### Wizards of the Coast

The official Comprehensive Rules remain an external rules authority/reference. Current Wizards policy/terms also identify Wizards-origin card/game content as protected material and impose use restrictions. WS03 does not select or infer a production right to redistribute card text, artwork, symbols, set assets, rules text, or other Wizards-origin material.

Current volatile policy references checked on 2026-08-28:

- `https://magic.wizards.com/en/rules`
- `https://company.wizards.com/en/legal/fancontentpolicy`
- `https://company.wizards.com/en/legal/terms`

Any future production embedding, transformation, or redistribution of Wizards-origin material remains `UNKNOWN / LEGAL_REVIEW_REQUIRED`.

## Production-usage topology boundary

`THIRD_PARTY_USAGE_MATRIX.json` enumerates realistic technical modes for each candidate, including fork/modification state, linking, subprocess use, copied/vendored code, generated data, network-service use, binary/source distribution, and runtime dependency. `THIRD_PARTY_USAGE_MATRIX.md` is its human-readable rendering.

No row is an architecture decision. Modeled rows remain `MODELED`; exact component/license/provenance facts remain `DIRECTLY_VERIFIED` or `CODE_DERIVED`; legal implications remain `LEGAL_REVIEW_REQUIRED`.

## WS03 gate

```text
all_candidate_license_identities_verified = true
all_candidate_usage_modes_documented = true
copied_or_vendored_code_inventory_complete = true
generated_data_boundary_documented = true
remaining_uncertainties_explicit = true
unsupported_legal_conclusions = 0
```

The WS03 subgate is complete. Q8 remains deferred until architecture selection supplies the exact production topology to review.
