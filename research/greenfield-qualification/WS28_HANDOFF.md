# WS28 handoff — trigger / replacement / zone / SBA

## Canonical boundary

- Owner family: `TRIGGER_REPLACEMENT_ZONE_SBA`
- WS26 base: `206a39cbaa3eeb98b10c2ddc36d51fe5b1b2f5ef`
- WS26 tree: `837f445f78bb26462653c58baf1532e294151b10`
- Pinned Forge: `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- Partition: 1,174 V2 paths; exactly 2 WS16-compatible child reuses; 1,172 new paths.

## Status

`WS28_FAMILY_GATE=FAIL_CLOSED` and `WORKSTREAM_COMPLETE=false`.

The two exact WS16 reuses remain the only inherited executions. No sibling
paths are inherited. The current source materializes a complete,
machine-readable fail-closed row for each of the 1,172 remaining V2 paths and
writes an empty `WS28_WITNESSES.jsonl`; it intentionally does not fabricate
ABI V2 witnesses from source text, inventory labels, or a generic trigger
event.

## Runtime evidence already inspected

Run `33310649549` (commit `bd1d33ddcce6d5d8a5d351e132711c651a70ef77`) and
the subsequent gate run `33310760173` (commit
`18ae6f1a08eb07ee8b84ac61cb3da3ab94a42552`) completed their 327-case
ChangesZone diagnostic census but failed its all-PASS assertion. The failures
are fixture/harness assertions (event detection, candidate matching,
destination and premature stack expectations); they are not a demonstrated
pinned-Forge shared-core defect. Therefore `SHARED_CORE_FIX_REQUIRED=false`
and no production core source was changed.

## Required condition for a PASS continuation

Each of the 1,172 new paths must receive a real actual-card execution through
the pinned Forge rules core, a current official-rules adjudication where the
assertion is rules-sensitive, and a validated WS26 Witness ABI V2 document.
Required decision, RNG, principal-scoped observation, and replay references
must be supplied for the paths that request them. Trigger witnesses must
retain event/detection/controller/ordering/stack/resolution state;
replacement witnesses must retain the actual applicable set and authoritative
choice; SBA witnesses must invoke engine SBA processing rather than test-side
mutation.

The closure artifact contains `WS28_PATH_COVERAGE.json`, inventories,
`WS28_RULES_ADJUDICATION.json`, `WS28_GATE.json`, and
`WS28_HASHES.sha256`. Its hash list is the immutable evidence index for the
particular workflow run. A workflow may only turn green once its gate reports
all hard gates `PASS`; no global Q6 claim is made here.
