# WS33 G3 AF Principal Observation v4 — validator repair checkpoint

Status: `REPAIR_PERSISTED_RUN_PENDING`

Evidence classification: `CODE_DERIVED` for the repair contract; qualification remains `UNKNOWN` pending fresh Actions adjudication.

## Repair commits

- v4 lifecycle-bound coarse-signal adjudicator: `8fd338a23fadaa0090aa6c7aa062632e9853eb3d`
- authoritative workflow repair: `9fbf7729eaecbd724d38f598cb5b0bdcf8352212`
- workflow repair TREE: `c5ec075fb35048940ce6da4a8a189f9b107e4c14`

## Repair semantics

The raw AF summary column 9 is retained unchanged. The v4 verifier now records any positive coarse value per run side and permits it only when the exact source profile is `POSITIVE_TEMPORARY_REQUIRED`.

For every positive coarse path, the exact same record/replay side must contain principal-scoped evidence whose events:

- belong to that exact path;
- contain one or more `SERVER_GRANT` events;
- have balanced `SERVER_GRANT`, `CLIENT_VISIBLE`, `SERVER_REVOKE`, `CLIENT_HIDDEN` counts;
- retain `identity_match=true` on every event;
- also pass the base per-`(principal_id,card_id)` strict lifecycle state machine.

Record and replay must expose identical coarse-signal path/value maps. Cross-principal delta remains exactly zero. Positive coarse values on negative/transition-only or unknown profiles fail closed.

This repair is v4-scoped. The existing Direct-G base verifier keeps its strict all-zero summary policy.

## Workflow contract repair

The fresh record step no longer rejects raw column 9 before replay/principal evidence exists. It now performs only engine/record structural prerequisites:

- exactly 21 rows;
- unique path ids;
- current >=21-column ABI;
- status PASS;
- empty runtime failure fields;
- stack admission/resolution `1/1`;
- target-SVar reachability >=1.

The strict hidden-information decision is deferred to the single authoritative v4 adjudication step after record and replay evidence are both present.

The final JSON gate now requires:

- `coarse_hidden_signal_policy=PRINCIPAL_ATTESTED_TEMPORARY_OBSERVATION`;
- raw coarse evidence retained;
- record/replay coarse path maps equal;
- record/replay coarse totals equal;
- unauthorized hidden leak requirement `0`;
- cross-principal requirement `0`;
- no unknown hidden consumer profile;
- coverage mutation `false`.

## Added fail-closed regression proof

The workflow parser/regression step now proves before Forge execution:

1. positive coarse signal + complete principal lifecycle => accepted by v4 contract;
2. positive coarse signal + incomplete revoke/hide lifecycle => FAIL_CLOSED;
3. positive coarse signal on `NEGATIVE_OR_TRANSITION_ONLY` => FAIL_CLOSED;
4. non-zero cross-principal delta => FAIL_CLOSED;
5. existing direct-v15 / AF-v19 ABI and mixed-ABI fail-closed regressions remain active.

## Runs

- intermediate auto-push run `33762335455` at `8fd338a23fadaa0090aa6c7aa062632e9853eb3d`: `SUPERSEDED`, because it uses the pre-repair workflow file and is not qualification-eligible;
- authoritative repair run `33762514428` at `9fbf7729eaecbd724d38f598cb5b0bdcf8352212`: queued at checkpoint; job `100672075188`.

No result from the superseded run may promote coverage or close AF Hidden / Principal Observation.

## Serial next step

Adjudicate `33762514428` to its first material failure or full PASS. If it fails at the known `Manifest` hidden-consumer profile, adjudicate that exact Forge consumer against current source and official rules before any classifier change. Do not start non-AF G32 until AF Hidden / Principal Observation is closed.

AF Hidden / Principal Observation: `UNKNOWN`

Coverage promotion: `FALSE`

`WS33_COMPLETE = FALSE`

`TASK_COMPLETE = NO`
