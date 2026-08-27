# Actual Card Requirement Manifest — Closeout State

Status: **INCOMPLETE / FAIL CLOSED**.

## Directly verified domain controls

- Physically held unique identities: **1338**.
- Operational own unique identities: **1007**.
- RogShai: exact **100**; normalized-list SHA-256 `2b6258ae1c778784ed252bb46ff828343055177146634c77847506d33f4a4362`.
- Kaervek: exact **100**; canonical deck hash `aa7a90a4e5cf32f40b1c9832d329aa03f6f7bf130f2d2e9c1e80d10e97c53c7a`.
- Dargo/Tymna theorycraft candidate identities: **743**.
- Real opponent unknown slots: **at least 142**; no synthetic completion is promoted to observed/verified truth.

## Precons

Run `33089467077`, artifact `9653672924`, extracted exactly the required 11 lists and asserted 100 slots for each. Forge is only the extraction helper. Official Wizards decklists remain content authority.

## Why this is not COMPLETE

The research branch does not yet contain the required deduplicated per-Oracle-identity union with all source-class flags and behavior priorities. The existing 1007-own and Kaervek materializations plus the 11-precon extraction are provenance inputs, not the final merged manifest.

Accordingly `ACTUAL_CARD_MANIFEST_COMPLETE = FALSE` and no behavior coverage percentage is inferred from presence or parsing.
