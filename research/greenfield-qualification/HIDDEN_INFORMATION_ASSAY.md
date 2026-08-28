# Hidden Information Assay — Current Qualification State

Status: **scoped raw-transport PASS; overall FAIL / insufficient evidence**.

At current research revision `34036a2d…` the Forge transport red-team
completed successfully at the exact Forge pin. The remote client decoded zero
hidden card names while receiving a full `GameView` and subsequent
`DeltaPacket`s for distinct Mountain/Forest decks. The evidence is GitHub run
`33152614611`, artifact `9678348191`, SHA-256
`126f4062334510582b7fc9eaace074e3568b3805397334a1d8fc88f0d1ca23c8`.

The correction is server-side and per-client: the initial full-state object
stream, delta property maps, and wrapped game events are all redacted using
the authoritative `CardView.canBeShownTo` visibility check. A visibility
transition forces a fresh client CardView so that a previously revealed state
cannot persist after entering a hidden zone. An unresolved client identity is
fail-closed and receives neutral card views.

This replaces neither the historical 74-name leak nor the broader gate. That
historical run remains a negative control; it is not reused as evidence for the
current revision. The following are still unqualified: principal-scoped
observations, logs, exceptions, identity-bearing IDs/hashes, replay,
debug-output, reveal/look lifecycle, and the required 4P Commander campaign.

```text
current 2P decoded-transport identity leaks = 0
all required hidden-information surfaces    = NOT_PROVEN
production hidden-information gate          = FAIL / INSUFFICIENT EVIDENCE
```

See `REMOTE_QUALIFICATION_EVIDENCE.json` for exact run provenance.
