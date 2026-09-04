# G3 NON-AF EVENT RUNTIME — RUN 33851809027 PENDING

Classification: `DIRECTLY_VERIFIED` run identity; outcome pending.

- source HEAD: `6fbb0150acf5b9d7c865ac90f0b485d97b482d30`
- source TREE: `73cc2fde2b9ff22a474b3f1460b67257a1d9231a`
- workflow: `WS33 G3 SVar non-AF event runtime`
- run: `33851809027`
- job: `100956085252`
- run count for source HEAD: exactly `1`
- status at checkpoint: `in_progress`

Change under qualification:

1. focused overlay `apply-ws33-nondiscretionary-ability-selection.py` restores pinned Desktop Forge's no-trigger-event behavior only for an authoritative `abilities.size() == 1` list produced by `GameActionUtil.getAdditionalCostSpell`;
2. empty and multi-option lists preserve the existing controller path;
3. `apply-ws33-trigger-reachability.py` delegates to that isolated repair after installing its observation-only admission hook;
4. no card/path special case, no multi-option first/default/random/pass/cancel fallback, no target/cost/RNG/coverage mutation.

Frozen root-cause evidence:
`G3_NON_AF_OPTIONAL_COST_SINGLETON_ROOT_CAUSE_20260904.md`.

No further write is authorized until this run is terminally adjudicated.

`G3_NON_AF_STATUS = UNKNOWN`
`COVERAGE_PROMOTION = FALSE`
`WS33_COMPLETE = FALSE`
`TASK_COMPLETE = NO`
