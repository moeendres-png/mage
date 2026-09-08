#!/usr/bin/env python3
"""Serial WS33B frontier promotion (B1 calculateAmount + B2 Cost) for the integration line.

Authoritative mechanism for the AF8->B serial integration successor. Modeled exactly on
ws33_promote_integrated_frontier.py (G3/A1 precedent): strict in-gates, minimal ledger
mutation (status + campaign + evidence binding), deterministic queue/gate recomputation,
exact post-state assertions. Consumes the frozen WS33_ABC_B1_B2_PROMOTION_INDEX.json.

Promotes EXACTLY the 664 authorized EXTERNALLY_RULE_VALIDATED paths (267 B1 + 397 B2).
The six B1 default-zero paths and five Cost terminal blockers must remain UNKNOWN;
any violation is a hard FAIL with no output written.
"""
from __future__ import annotations
import argparse, hashlib, json
from collections import Counter, defaultdict
from pathlib import Path

SHARDS = ('WS33A', 'WS33B', 'WS33C', 'WS33D', 'WS33E', 'WS33F', 'WS33G', 'WS33H')
FORGE_PIN = '8c7e9afb8e6caee88644b94e25da5852e36f8928'
MANIFEST_SHA = 'cd48f4279d682ab944e2534bf937d87e5311e83989e97179ae73c5c7d1bb6224'
CONSUMER_SHA = '82638e6b3e4408cc5bddedc49372b6357d3c2bdce6fba7bfab7ed119678f9a48'
AUTH_DIGEST = '57e210b8d2a5a79f3aaa3a4b124e3d92e2d6d3fc8447fa74d31f299d9366f75c'
B1_CAMPAIGN = 'WS33_ABC_B1_CALCULATE_AMOUNT'
B2_CAMPAIGN = 'WS33_ABC_B2_COST'
PROMOTION_EVIDENCE_REF = 'WS33_POST_AF8B_PROMOTION_EVIDENCE.json'


def load(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))


def loadl(p):
    return [json.loads(x) for x in Path(p).read_text(encoding='utf-8').splitlines() if x.strip()]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write(p, x):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(x, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def writel(p, rows):
    Path(p).write_text(''.join(json.dumps(x, sort_keys=True, separators=(',', ':')) + '\n' for x in rows), encoding='utf-8')


def req(c, m):
    if not c:
        raise SystemExit('WS33_B_PROMOTED_FRONTIER=FAIL ' + m)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ledger', type=Path, required=True)
    ap.add_argument('--queue', type=Path, required=True)
    ap.add_argument('--gate', type=Path, required=True)
    ap.add_argument('--promotion-index', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--source-head', required=True)
    ap.add_argument('--source-tree', required=True)
    a = ap.parse_args()

    rows = loadl(a.ledger)
    queue = load(a.queue)
    oldgate = load(a.gate)
    promotion = load(a.promotion_index)
    req(len(rows) == 4188, 'ledger count')
    byid = {r['effective_path_id']: r for r in rows}
    req(len(byid) == 4188, 'duplicate ledger identity')
    before = Counter(r['current_status'] for r in rows)
    req(before == Counter({'UNKNOWN': 3903, 'PASS': 285}), 'old ledger counts')

    req(promotion.get('forge_pin') == FORGE_PIN, 'forge pin')
    req(promotion.get('manifest_sha256') == MANIFEST_SHA, 'manifest lineage')
    req(promotion.get('consumer_model_sha256') == CONSUMER_SHA, 'consumer lineage')
    b1ids = set(promotion['b1']['effective_path_ids'])
    b2ids = set(promotion['b2']['effective_path_ids'])
    defaults = set(promotion['b1']['held_default_zero_ids'])
    blockers = set(promotion['b2']['held_terminal_blocker_ids'])
    req(len(b1ids) == 267 and len(b2ids) == 397, 'promotion sets')
    req(len(defaults) == 6 and len(blockers) == 5, 'held sets')
    req(b1ids.isdisjoint(b2ids), 'B1/B2 overlap')
    req((b1ids | b2ids).isdisjoint(defaults), 'authorized/default overlap')
    req((b1ids | b2ids).isdisjoint(blockers), 'authorized/blocker overlap')
    req(defaults.isdisjoint(blockers), 'default/blocker overlap')
    union_digest = hashlib.sha256(('\n'.join(sorted(b1ids | b2ids)) + '\n').encode()).hexdigest()
    req(union_digest == AUTH_DIGEST, 'authorized union digest')
    req(promotion.get('authorized_union_digest') == 'sha256:' + AUTH_DIGEST, 'index union digest')
    req(promotion['b1'].get('classification') == 'EXTERNALLY_RULE_VALIDATED', 'B1 class')
    req(promotion['b2'].get('classification') == 'EXTERNALLY_RULE_VALIDATED', 'B2 class')

    b1items = [x for x in queue['items'] if x.get('logical_bucket') == 'WS33B'
               and x.get('runtime_subsystem') == 'forge.game.ability.AbilityUtils#calculateAmount'
               and x.get('scenario_group_id') == 'ws33-g2-template-010'
               and x.get('evidence_profile') == 'DECISION+RNG+HIDDEN+REPLAY']
    req(len(b1items) == 1 and set(b1items[0]['effective_path_ids']) == (b1ids | defaults)
        and b1items[0]['unresolved_path_count'] == 273, 'canonical B1 queue mismatch')
    cost_union = {i for x in queue['items'] if x.get('logical_bucket') == 'WS33B'
                  and x.get('runtime_subsystem') == 'forge.game.cost.Cost'
                  for i in x['effective_path_ids']}
    req(cost_union == (b2ids | blockers) and len(cost_union) == 402, 'canonical B2 queue mismatch')

    targets = b1ids | b2ids
    bindings = promotion.get('bindings', {})
    for pid in targets:
        req(byid[pid]['current_status'] == 'UNKNOWN', 'promoted ledger path not unknown ' + pid)
        req(byid[pid]['logical_bucket'] == 'WS33B', 'promoted path not WS33B ' + pid)
        req(pid in bindings and bindings[pid]['evidence_class'] == 'EXTERNALLY_RULE_VALIDATED',
            'missing positive binding ' + pid)
        req(bindings[pid].get('witness_id') and bindings[pid].get('trace_sha256'), 'empty binding ' + pid)
    ledger_pass = {i for i, r in byid.items() if r['current_status'] == 'PASS'}
    req(targets.isdisjoint(ledger_pass), 'authorized set overlaps live PASS')
    for pid in defaults | blockers:
        req(byid[pid]['current_status'] == 'UNKNOWN', 'held path not UNKNOWN ' + pid)

    for pid in targets:
        b = bindings[pid]
        byid[pid]['current_status'] = 'PASS'
        byid[pid]['blocker_classification'] = None
        byid[pid]['campaign_id'] = B1_CAMPAIGN if pid in b1ids else B2_CAMPAIGN
        byid[pid]['evidence_classification'] = 'EXTERNALLY_RULE_VALIDATED'
        byid[pid]['witness_id'] = b['witness_id']
        byid[pid]['trace_sha256'] = b['trace_sha256']
        byid[pid]['promotion_evidence'] = PROMOTION_EVIDENCE_REF
    outrows = [byid[i] for i in sorted(byid)]
    after = Counter(r['current_status'] for r in outrows)
    req(after == Counter({'UNKNOWN': 3239, 'PASS': 949}), 'new ledger counts')

    groups = defaultdict(list)
    for row in outrows:
        if row['current_status'] == 'PASS':
            continue
        key = (row['logical_bucket'], row['owner_family'], row['runtime_subsystem'],
               row['scenario_group_id'], row['evidence_profile'])
        groups[key].append(row['effective_path_id'])
    items = []
    for (bucket, owner, subsystem, scenario, profile), ids in groups.items():
        items.append({'logical_bucket': bucket, 'owner_family': owner, 'runtime_subsystem': subsystem,
                      'scenario_group_id': scenario, 'evidence_profile': profile,
                      'unresolved_path_count': len(ids), 'effective_path_ids': sorted(ids),
                      'priority_basis': 'DESCENDING_UNRESOLVED_PATH_COUNT_THEN_STABLE_KEYS'})
    items.sort(key=lambda r: (-r['unresolved_path_count'], r['logical_bucket'], r['runtime_subsystem'], r['scenario_group_id']))
    b1res = [x for x in items if x.get('scenario_group_id') == 'ws33-g2-template-010']
    req(len(b1res) == 1 and set(b1res[0]['effective_path_ids']) == defaults, 'B1 residual mismatch')
    costres = {i for x in items if x.get('logical_bucket') == 'WS33B'
               and x.get('runtime_subsystem') == 'forge.game.cost.Cost' for i in x['effective_path_ids']}
    req(costres == blockers, 'B2 residual mismatch')

    out = a.out
    out.mkdir(parents=True, exist_ok=True)
    ledger_path = out / 'WS33_INTEGRATED_CLOSURE_LEDGER.jsonl'
    queue_path = out / 'WS33_INTEGRATED_WORK_QUEUE.json'
    writel(ledger_path, outrows)
    write(queue_path, {'schema': 'commander-simulator-next.ws33-integrated-work-queue.v1',
                       'basis': 'effective_path_id', 'unresolved_path_count': 3239,
                       'work_item_count': len(items), 'items': items})
    unknown = Counter(r['logical_bucket'] for r in outrows if r['current_status'] == 'UNKNOWN')
    expected = {'WS33A': 179, 'WS33B': 11, 'WS33C': 700, 'WS33D': 920,
                'WS33E': 1029, 'WS33F': 319, 'WS33G': 81, 'WS33H': 0}
    req({k: unknown.get(k, 0) for k in SHARDS} == expected, 'unknown shards')
    evidence = {
        'schema': 'commander-simulator-next.ws33-post-af8b-promotion.v1',
        'status': 'PASS',
        'source_head': a.source_head,
        'source_tree': a.source_tree,
        'forge_pin': FORGE_PIN,
        'manifest_sha256': MANIFEST_SHA,
        'consumer_model_sha256': CONSUMER_SHA,
        'af8_source_head': '1922a5172f0e004dd95c279744c641775a80b15a',
        'af8_run': '34222323657',
        'b_source_head': '2c6ceedebb250165893d942251acf7550346c405',
        'b1': {'run': '34266311850', 'artifact_id': '10072131808',
               'artifact_digest': promotion['b1']['artifact_digest'],
               'classification': 'EXTERNALLY_RULE_VALIDATED',
               'path_count': 267, 'effective_path_ids': sorted(b1ids)},
        'b2': {'run': '34286249888', 'artifact_id': '10079683394',
               'artifact_digest': promotion['b2']['artifact_digest'],
               'classification': 'EXTERNALLY_RULE_VALIDATED',
               'path_count': 397, 'effective_path_ids': sorted(b2ids)},
        'authorized_union_digest': 'sha256:' + AUTH_DIGEST,
        'held_default_zero_ids': sorted(defaults),
        'held_terminal_blocker_ids': sorted(blockers),
        'predecessor_counts': {k: before.get(k, 0) for k in ('PASS', 'FAIL', 'UNSUPPORTED', 'UNKNOWN')},
        'successor_counts': {k: after.get(k, 0) for k in ('PASS', 'FAIL', 'UNSUPPORTED', 'UNKNOWN')},
        'unknown_by_shard': expected,
        'promoted_path_count': 664,
        'unrelated_path_changes': 0,
        'previous_pass_regressions': 0,
    }
    write(out / PROMOTION_EVIDENCE_REF, evidence)
    gate = dict(oldgate)
    gate.update({'path_status_counts': {'PASS': 949, 'FAIL': 0, 'UNSUPPORTED': 0, 'UNKNOWN': 3239},
                 'unresolved_path_count': 3239, 'work_item_count': len(items),
                 'ledger_sha256': sha(ledger_path), 'queue_sha256': sha(queue_path),
                 'status': 'PASS', 'GLOBAL_Q6_PASS': False, 'WS34_ELIGIBLE': False,
                 'ARCHITECTURE_FREEZE_ELIGIBLE': False,
                 'promotion_evidence_sha256': sha(out / PROMOTION_EVIDENCE_REF)})
    write(out / 'WS33_INTEGRATED_FRONTIER_GATE.json', gate)
    unresolved = {pid for item in items for pid in item['effective_path_ids']}
    req(not (unresolved & targets), 'promoted IDs remain queued')
    req(len(unresolved) == 3239, 'queue union')
    print(json.dumps({'WS33_B_PROMOTED_FRONTIER': 'PASS', 'pass': 949, 'unknown': 3239,
                      'work_items': len(items), 'b_unknown': 11}, sort_keys=True))


if __name__ == '__main__':
    main()
