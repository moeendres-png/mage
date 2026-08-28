# LICENSE INVENTORY

Status: **WS03 SUBGATE PASS**  
Checked: 2026-08-28  
Audit base: `c0e42fb42c4a603aff4a76b1284f8271c12bfd42`  
Audit tree: `fb06c61dd87b4b742722925cd7374d8f037e1f47`

This inventory records exact-pin license identity and provenance. It is **not legal advice**, does not select an architecture, and does not infer that process or network separation resolves license obligations.

## Exact-pin components

| Component | Repository | Pin / tree | Verified license | Fork / vendor relationship |
|---|---|---|---|---|
| Audit host / XMage fork | `moeendres-png/mage` | `c0e42fb42c4a603aff4a76b1284f8271c12bfd42` / `fb06c61dd87b4b742722925cd7374d8f037e1f47` | MIT | GitHub fork of `magefree/mage`; full XMage-derived source is present in the research repository |
| Forge | `Card-Forge/forge` | `8c7e9afb8e6caee88644b94e25da5852e36f8928` / `c634b817e037c4531051859f7d00805ffd74931e` | GPL-3.0 license text | not a fork |
| XMage upstream | `magefree/mage` | `86d86b580cd7e1f30b51110d70cecae18c1ce452` / `3dbfaec4f8f411374535493c088cf4df09822d9f` | MIT | not a fork |
| phase.rs | `phase-rs/phase` | `fae406c4603f450797014f3ac8e8818b3d36c2a4` / `c23ab64340c6c39062fda5149895947112b77e36` | `MIT OR Apache-2.0` | not a fork; Cargo version `0.64.0` |
| Manabrew | `witchesofthehill/manabrew` | `754ec2aeec495d67d7bb9b89d0fd67ee22281b46` / `00bbd0644ba47aec420d82283053a9121c7019ec` | `AGPL-3.0-or-later` | not a fork; pinned release commit identifies Manabrew `3.21.10` |
| Manabrew Forge submodule | `witchesofthehill/forge` | `192b5eab000069bbb8917a5df9d60d4a9128aa07` / `5c3ceb72012385ed18a223628d953e170b1ae5f5` | GPL-3.0 license text | GitHub fork of `Card-Forge/forge`; exact gitlink from Manabrew `.gitmodules`/tree |

## Immutable license evidence

- Forge `LICENSE`: blob `e72bfddabc15be5718a7cc061ac10e47741d8219`.
- XMage `LICENSE.txt`: blob `3575e469d848ca405ccc8d0ac9d711c94120eb45`.
- phase.rs `LICENSE-MIT`: blob `757ab5c3f8cddd11a8f05d4d16d6d0bd5bc5ba1a`; `LICENSE-APACHE`: blob `f5c2a72aa04b76d55ba884bee16541b2a6851bfc`; `Cargo.toml`: blob `d7827853c3d53cfdec17e74fcef07f67b1d62c9f` declares `MIT OR Apache-2.0`.
- Manabrew `LICENSE.md`: blob `d37485c56ae7a4564e321d4aac35e9b99e1b7d9e`; `LICENSE-AGPL-3.0-or-later`: blob `be3f7b28e564e7dd05eaf59d64adba1a4065ac0e`.
- Manabrew Forge fork `LICENSE`: blob `e72bfddabc15be5718a7cc061ac10e47741d8219`.
- Manabrew `.gitmodules`: blob `9f2156f0ca7ce5e9a7512bec63da1c2152e61211`, URL `https://github.com/witchesofthehill/forge.git`, branch `manabrew`.

GitHub's repository-level license classifier is supplementary only. Exact license files/declarations at the pinned commits are the license-identity evidence for this workstream.

## Copied / modified / vendored census

- **Audit host:** this repository is itself an XMage fork. XMage-derived source is therefore present by Git history/fork inheritance; it is not a newly copied vendor subtree created by WS03.
- **Forge direct research lane:** the exact external Forge checkout is modified only in the qualification job by `forge-patches/strict-decision-boundary.patch` (blob `17eaa13c8480ab25234e7d83d78117da62298547`) using `apply-strict-decision-boundary.sh` (blob `ca8a2da57d58a2b39559d27db26e114b3e9c2f33`). The patched checkout is not committed or distributed by WS03.
- **XMage / phase.rs / Manabrew external pins:** no new source copy or vendor subtree into the audit host was identified in the audited research topology.
- **Manabrew:** recursive checkout contains `forge/` as a Git submodule to the separate GPL Forge fork at exact pin `192b5e…`.
- **Patch licensing:** whether the project-authored Forge patch, once applied/combined/distributed in a future product, creates additional obligations is `LEGAL_REVIEW_REQUIRED`.

## Data-source boundary

The current qualification workflow calls `https://api.scryfall.com/bulk-data`, selects `type=oracle_cards`, hashes the downloaded payload, and transforms it with `scryfall_oracle_index.py` (blob `546855bb1e04caf54d1c7c0e06746f9dbe701d96`). The generated index carries `name`, `face_names`, `oracle_id`, `scryfall_id`, Commander legality, color identity, and type line.

That transformation is technical provenance only. This audit did **not** establish a general Scryfall data license sufficient for future production redistribution. Bundling or serving Scryfall-derived datasets is therefore `UNKNOWN / LEGAL_REVIEW_REQUIRED`.

Wizards' current Fan Content Policy states that Wizards IP includes, among other things, cards, pictures/artwork, graphics, files, and text, and excludes verbatim copying/reposting from its fan-content definition. Current policy URLs checked on 2026-08-28:

- https://company.wizards.com/en/legal/fancontentpolicy
- https://company.wizards.com/en/legal/terms

Those are volatile policy sources, not immutable license grants. No production right to card text, images, symbols, set assets, rules text, or other Wizards-origin material is inferred here.

## Gate

```text
all_candidate_license_identities_verified = true
copied_or_vendored_code_inventory_complete = true
generated_data_boundary_documented = true
remaining_uncertainties_explicit = true
unsupported_legal_conclusions = 0
```

Machine-readable authority: `LICENSE_INVENTORY.json`.
