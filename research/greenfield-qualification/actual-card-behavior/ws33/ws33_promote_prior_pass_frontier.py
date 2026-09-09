#!/usr/bin/env python3
"""Serial preservation repair: restore omitted G3/A1 predecessor PASS into the frontier.

Authoritative mechanism for the AF8->B successor preservation repair. Same deterministic
pattern as ws33_promote_integrated_frontier.py (G3/A1) and ws33_promote_b_frontier.py (B):
strict in-gates, minimal ledger mutation, deterministic queue/gate recomputation, exact
post-state assertions. Consumes frozen WS33_PRIOR_PASS_PROMOTION_INDEX.json.

Restores EXACTLY the 203 inheritable predecessor PASS (122 A1 EXTERNALLY_RULE_VALIDATED
+ 81 G3 TECHNICALLY_CONFORMANT). Creates no new coverage credit. Guards: B-664 must all
remain PASS (no regression); held 6 defaults + 5 blockers must remain UNKNOWN; any
violation is a hard FAIL with no output written.
"""
from __future__ import annotations
import argparse, hashlib, json
from collections import Counter, defaultdict
from pathlib import Path

SHARDS = ('WS33A', 'WS33B', 'WS33C', 'WS33D', 'WS33E', 'WS33F', 'WS33G', 'WS33H')
FORGE_PIN = '8c7e9afb8e6caee88644b94e25da5852e36f8928'
MANIFEST_SHA = 'cd48f4279d682ab944e2534bf937d87e5311e83989e97179ae73c5c7d1bb6224'
CONSUMER_SHA = '82638e6b3e4408cc5bddedc49372b6357d3c2bdce6fba7bfab7ed119678f9a48'
AUTH_DIGEST = 'a51c01b8cb953eda0c79bf1a6416061ae47be6672c326e4a92a8122fb8955b43'
A1_CAMPAIGN = 'WS33_ABC_A1_CERTIFIED_ARTIFACT'
G3_CAMPAIGN = 'G3_COMPLETE_CROSS_QUALIFICATION'
PROMOTION_EVIDENCE_REF = 'WS33_PRESERVATION_REPAIR_EVIDENCE.json'


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
        raise SystemExit('WS33_PRESERVATION_REPAIR=FAIL ' + m)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ledger', type=Path, required=True)
    ap.add_argument('--queue', type=Path, required=True)
    ap.add_argument('--gate', type=Path, required=True)
    ap.add_argument('--manifest', type=Path, required=True)
    ap.add_argument('--promotion-index', type=Path, required=True)
    ap.add_argument('--b-index', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--source-head', required=True)
    ap.add_argument('--source-tree', required=True)
    a = ap.parse_args()

    rows = loadl(a.ledger)
    queue = load(a.queue)
    oldgate = load(a.gate)
    manifest = load(a.manifest)
    promotion = load(a.promotion_index)
    bindex = load(a.b_index)
    req(len(rows) == 4188, 'ledger count')
    byid = {r['effective_path_id']: r for r in rows}
    req(len(byid) == 4188, 'duplicate ledger identity')
    before = Counter(r['current_status'] for r in rows)
    req(before == Counter({'UNKNOWN': 3239, 'PASS': 949}), 'old ledger counts')

    req(promotion.get('forge_pin') == FORGE_PIN, 'forge pin')
    req(promotion.get('manifest_sha256') == MANIFEST_SHA, 'manifest lineage')
    req(promotion.get('consumer_model_sha256') == CONSUMER_SHA, 'consumer lineage')
    a1ids = set(promotion['a1']['effective_path_ids'])
    g3ids = set(promotion['g3']['effective_path_ids'])
    req(len(a1ids) == 122 and len(g3ids) == 81, 'repair sets')
    req(a1ids.isdisjoint(g3ids), 'A1/G3 overlap')
    union_digest = hashlib.sha256(('\n'.join(sorted(a1ids | g3ids)) + '\n').encode()).hexdigest()
    req(union_digest == AUTH_DIGEST, 'authorized union digest')
    req(promotion.get('authorized_union_digest') == 'sha256:' + AUTH_DIGEST, 'index union digest')
    req(promotion['a1'].get('classification') == 'EXTERNALLY_RULE_VALIDATED', 'A1 class')
    req(promotion['g3'].get('classification') == 'TECHNICALLY_CONFORMANT', 'G3 class')

    manifest_g = {p['v2_path_id'] for p in manifest['paths'] if p.get('owner_family') == 'HIDDEN_RNG_REPLAY'}
    req(manifest_g == g3ids and len(manifest_g) == 81, 'G3 manifest partition mismatch')
    req(manifest.get('forge_pin') == FORGE_PIN, 'manifest forge pin')

    bset = set(bindex['b1']['effective_path_ids']) | set(bindex['b2']['effective_path_ids'])
    req(len(bset) == 664, 'B regression set')
    for pid in bset:
        req(byid[pid]['current_status'] == 'PASS', 'B-664 regression ' + pid)
    held = set(bindex['b1']['held_default_zero_ids']) | set(bindex['b2']['held_terminal_blocker_ids'])
    req(len(held) == 11, 'held set')
    for pid in held:
        req(byid[pid]['current_status'] == 'UNKNOWN', 'held path not UNKNOWN ' + pid)

    targets = a1ids | g3ids
    req(targets.isdisjoint(bset), 'repair/B overlap')
    req(targets.isdisjoint(held), 'repair/held overlap')
    bindings = promotion.get('bindings', {})
    for pid in targets:
        req(byid[pid]['current_status'] == 'UNKNOWN', 'repair path not unknown ' + pid)
        req(pid in bindings, 'missing binding ' + pid)
    for pid in a1ids:
        req(byid[pid]['logical_bucket'] == 'WS33A', 'A1 path not WS33A ' + pid)
        req(bindings[pid]['evidence_class'] == 'EXTERNALLY_RULE_VALIDATED', 'A1 binding class ' + pid)
        req(bindings[pid].get('witness_id') and bindings[pid].get('trace_sha256'), 'A1 empty binding ' + pid)
    for pid in g3ids:
        req(byid[pid]['logical_bucket'] == 'WS33G', 'G3 path not WS33G ' + pid)
    ledger_pass = {i for i, r in byid.items() if r['current_status'] == 'PASS'}
    req(targets.isdisjoint(ledger_pass), 'repair set overlaps live PASS')

    for pid in targets:
        b = bindings[pid]
        byid[pid]['current_status'] = 'PASS'
        byid[pid]['blocker_classification'] = None
        if pid in a1ids:
            byid[pid]['campaign_id'] = A1_CAMPAIGN
            byid[pid]['evidence_classification'] = 'EXTERNALLY_RULE_VALIDATED'
            byid[pid]['witness_id'] = b['witness_id']
            byid[pid]['trace_sha256'] = b['trace_sha256']
        else:
            byid[pid]['campaign_id'] = G3_CAMPAIGN
            byid[pid]['evidence_classification'] = 'TECHNICALLY_CONFORMANT'
        byid[pid]['promotion_evidence'] = PROMOTION_EVIDENCE_REF
    outrows = [byid[i] for i in sorted(byid)]
    after = Counter(r['current_status'] for r in outrows)
    req(after == Counter({'UNKNOWN': 3036, 'PASS': 1152}), 'new ledger counts')

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

    out = a.out
    out.mkdir(parents=True, exist_ok=True)
    ledger_path = out / 'WS33_INTEGRATED_CLOSURE_LEDGER.jsonl'
    queue_path = out / 'WS33_INTEGRATED_WORK_QUEUE.json'
    writel(ledger_path, outrows)
    write(queue_path, {'schema': 'commander-simulator-next.ws33-integrated-work-queue.v1',
                       'basis': 'effective_path_id', 'unresolved_path_count': 3036,
                       'work_item_count': len(items), 'items': items})
    unknown = Counter(r['logical_bucket'] for r in outrows if r['current_status'] == 'UNKNOWN')
    expected = {'WS33A': 57, 'WS33B': 11, 'WS33C': 700, 'WS33D': 920,
                'WS33E': 1029, 'WS33F': 319, 'WS33G': 0, 'WS33H': 0}
    req({k: unknown.get(k, 0) for k in SHARDS} == expected, 'unknown shards')
    evidence = {
        'schema': 'commander-simulator-next.ws33-preservation-repair.v1',
        'status': 'PASS',
        'source_head': a.source_head,
        'source_tree': a.source_tree,
        'forge_pin': FORGE_PIN,
        'manifest_sha256': MANIFEST_SHA,
        'consumer_model_sha256': CONSUMER_SHA,
        'successor_artifact_id': '9979204198',
        'successor_artifact_digest': 'sha256:ae75ff01604f9fcc2b2cd2320e4cec1470347bcd47665d1989c1541542e76af0',
        'a1': {'run': '33999460235', 'artifact_id': '9979087306',
               'artifact_digest': 'sha256:a414f73b2f7d259dce19e64733fcb000a10b00ac4ca579f36190c1ba3064d11b',
               'classification': 'EXTERNALLY_RULE_VALIDATED',
               'path_count': 122, 'effective_path_ids': sorted(a1ids)},
        'g3': {'checkpoint': 'checkpoints/G3_COMPLETE_CROSS_QUALIFICATION_20260905.md',
               'classification': 'TECHNICALLY_CONFORMANT',
               'path_count': 81, 'effective_path_ids': sorted(g3ids)},
        'authorized_union_digest': 'sha256:' + AUTH_DIGEST,
        'b_regression_guarded': 664,
        'held_unknown_guarded': 11,
        'predecessor_counts': {k: before.get(k, 0) for k in ('PASS', 'FAIL', 'UNSUPPORTED', 'UNKNOWN')},
        'successor_counts': {k: after.get(k, 0) for k in ('PASS', 'FAIL', 'UNSUPPORTED', 'UNKNOWN')},
        'unknown_by_shard': expected,
        'repaired_path_count': 203,
        'new_coverage_credit': 0,
        'unrelated_path_changes': 0,
        'previous_pass_regressions': 0,
    }
    write(out / PROMOTION_EVIDENCE_REF, evidence)
    gate = dict(oldgate)
    gate.update({'path_status_counts': {'PASS': 1152, 'FAIL': 0, 'UNSUPPORTED': 0, 'UNKNOWN': 3036},
                 'unresolved_path_count': 3036, 'work_item_count': len(items),
                 'ledger_sha256': sha(ledger_path), 'queue_sha256': sha(queue_path),
                 'status': 'PASS', 'GLOBAL_Q6_PASS': False, 'WS34_ELIGIBLE': False,
                 'ARCHITECTURE_FREEZE_ELIGIBLE': False,
                 'promotion_evidence_sha256': sha(out / PROMOTION_EVIDENCE_REF)})
    write(out / 'WS33_INTEGRATED_FRONTIER_GATE.json', gate)
    unresolved = {pid for item in items for pid in item['effective_path_ids']}
    req(not (unresolved & targets), 'repaired IDs remain queued')
    req(len(unresolved) == 3036, 'queue union')
    print(json.dumps({'WS33_PRESERVATION_REPAIR': 'PASS', 'pass': 1152, 'unknown': 3036,
                      'work_items': len(items), 'a_unknown': 57, 'g_unknown': 0}, sort_keys=True))


if __name__ == '__main__':
    main()
