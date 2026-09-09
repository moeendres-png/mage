#!/usr/bin/env python3
"""Regression: AF8/B successor must preserve all adjudicated predecessor PASS.

Pins the preservation-repair invariants against the live integrated ledger:
- the exact 203 G3/A1 predecessor paths are PASS with retained classifications;
- the exact B-664 promotion is intact (no regression);
- the 6 B1 defaults + 5 Cost blockers remain UNKNOWN;
- global counts and shard frontier are exactly the repaired values.

No fixtures, no network, deterministic. Fails closed on any deviation.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).parent
EXPECTED_UNION_DIGEST = 'a51c01b8cb953eda0c79bf1a6416061ae47be6672c326e4a92a8122fb8955b43'


def fail(message: str) -> None:
    raise SystemExit('WS33_PRESERVATION_REGRESSION=FAIL ' + message)


def main() -> None:
    ledger = [json.loads(line) for line in (ROOT / 'WS33_INTEGRATED_CLOSURE_LEDGER.jsonl').read_text().splitlines() if line.strip()]
    if len(ledger) != 4188:
        fail('ledger count')
    byid = {row['effective_path_id']: row for row in ledger}
    if len(byid) != 4188:
        fail('duplicate ledger identity')

    index = json.loads((ROOT / 'checkpoints' / 'WS33_PRIOR_PASS_PROMOTION_INDEX.json').read_text())
    a1 = set(index['a1']['effective_path_ids'])
    g3 = set(index['g3']['effective_path_ids'])
    if len(a1) != 122 or len(g3) != 81 or not a1.isdisjoint(g3):
        fail('repair index sets')
    import hashlib
    digest = hashlib.sha256(('\n'.join(sorted(a1 | g3)) + '\n').encode()).hexdigest()
    if digest != EXPECTED_UNION_DIGEST:
        fail('repair union digest')

    for pid in a1:
        row = byid.get(pid)
        if not row or row['current_status'] != 'PASS':
            fail('A1 path not PASS ' + pid)
        if row['evidence_classification'] != 'EXTERNALLY_RULE_VALIDATED':
            fail('A1 class ' + pid)
        if row['campaign_id'] != 'WS33_ABC_A1_CERTIFIED_ARTIFACT':
            fail('A1 campaign ' + pid)
    for pid in g3:
        row = byid.get(pid)
        if not row or row['current_status'] != 'PASS':
            fail('G3 path not PASS ' + pid)
        if row['evidence_classification'] != 'TECHNICALLY_CONFORMANT':
            fail('G3 class ' + pid)
        if row['campaign_id'] != 'G3_COMPLETE_CROSS_QUALIFICATION':
            fail('G3 campaign ' + pid)

    bindex = json.loads((ROOT / 'checkpoints' / 'WS33_ABC_B1_B2_PROMOTION_INDEX.json').read_text())
    bset = set(bindex['b1']['effective_path_ids']) | set(bindex['b2']['effective_path_ids'])
    if len(bset) != 664:
        fail('B set')
    for pid in bset:
        if byid.get(pid, {}).get('current_status') != 'PASS':
            fail('B-664 regression ' + pid)
    held = set(bindex['b1']['held_default_zero_ids']) | set(bindex['b2']['held_terminal_blocker_ids'])
    if len(held) != 11:
        fail('held set')
    for pid in held:
        if byid.get(pid, {}).get('current_status') != 'UNKNOWN':
            fail('held path not UNKNOWN ' + pid)

    from collections import Counter
    counts = Counter(row['current_status'] for row in ledger)
    if (counts['PASS'], counts['UNKNOWN'], counts.get('FAIL', 0), counts.get('UNSUPPORTED', 0)) != (1152, 3036, 0, 0):
        fail('global counts ' + json.dumps(dict(counts), sort_keys=True))
    shards = {s: sum(1 for row in ledger if row['current_status'] == 'UNKNOWN' and row['logical_bucket'] == s)
              for s in ('WS33A', 'WS33B', 'WS33C', 'WS33D', 'WS33E', 'WS33F', 'WS33G', 'WS33H')}
    expected = {'WS33A': 57, 'WS33B': 11, 'WS33C': 700, 'WS33D': 920,
                'WS33E': 1029, 'WS33F': 319, 'WS33G': 0, 'WS33H': 0}
    if shards != expected:
        fail('shard frontier ' + json.dumps(shards, sort_keys=True))

    queue = json.loads((ROOT / 'WS33_INTEGRATED_WORK_QUEUE.json').read_text())
    union = {pid for item in queue['items'] for pid in item['effective_path_ids']}
    if queue['unresolved_path_count'] != 3036 or len(union) != 3036:
        fail('queue union')
    if union & (a1 | g3):
        fail('repaired IDs remain queued')
    print('WS33_PRESERVATION_REGRESSION=PASS pass=1152 unknown=3036 a=57 g=0 b_intact=664 held=11')


if __name__ == '__main__':
    main()
