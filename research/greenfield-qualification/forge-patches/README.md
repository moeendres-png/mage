# Forge strict Decision Export patch

This directory contains a research-only patch for the exact Forge checkout
`8c7e9afb8e6caee88644b94e25da5852e36f8928`. It is applied only in an ephemeral
qualification checkout; it is not an upstream Forge commit and does not create
the private production repository.

The patch exports the authoritative `InputSelectEntitiesFromList` entity set
for card/player/entity selection, validates typed responses server-side, and
suppresses GUI prompt/zone rendering while the provider is installed. All
other decision callbacks remain explicitly unqualified. The qualification
gate therefore stays fail-closed until the complete controller census,
runtime decision tape, hidden-information boundary, and replay gates pass.

Apply with:

```text
bash research/greenfield-qualification/forge-patches/apply-strict-decision-boundary.sh <forge-root> <patch-file>
```
