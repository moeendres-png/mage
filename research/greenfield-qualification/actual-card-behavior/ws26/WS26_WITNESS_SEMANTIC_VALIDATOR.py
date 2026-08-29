#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
PIN='8c7e9afb8e6caee88644b94e25da5852e36f8928'
OWNERS={'ACTION_COST_DECISION','TRIGGER_REPLACEMENT_ZONE_SBA','CONTINUOUS_COPY_CONTROL','COMBAT_COMMANDER','HIDDEN_RNG_REPLAY'}
REQ={'schema','witness_id','source_head','source_tree','forge_pin','oracle_identities','parent_ws14_primitive_ids','v2_path_ids','owner_family','initial_semantic_state','final_semantic_state','state_assertions','primitive_exercise','path_exercise','decision_tape_ref','rng_tape_ref','observation_evidence_ref','execution','trace_ref','trace_sha256','stdout_only','rules_authority_refs','evidence_class','status'}
def fail(msg): raise ValueError(msg)
def load(p): return json.loads(Path(p).read_text())
def validate(w,manifest,base:Path):
    missing=REQ-set(w)
    if missing: fail('missing required fields: '+','.join(sorted(missing)))
    if w['schema']!='commander-simulator-next.actual-card-witness.v2': fail('schema mismatch')
    if w['forge_pin']!=PIN or w['forge_pin']!=manifest['forge_pin']: fail('source/Forge pin mismatch')
    if w['source_head']!=manifest['source_head'] or w['source_tree']!=manifest['source_tree']: fail('source/Forge pin mismatch')
    if w['owner_family'] not in OWNERS: fail('invalid owner family')
    if not w['oracle_identities'] or not w['v2_path_ids']: fail('missing V2 path coverage')
    paths={p['v2_path_id']:p for p in manifest['paths']}
    for pid in w['v2_path_ids']:
        if pid not in paths: fail('unknown V2 path')
        p=paths[pid]
        if p['owner_family']!=w['owner_family']: fail('owner mismatch')
        par=p.get('parent_ws14_primitive_id')
        if par and par not in w['parent_ws14_primitive_ids']: fail('mismatched parent primitive')
        if p['required_decision_evidence'] and not w['decision_tape_ref']: fail('missing decision tape for decision-required path')
        if p['required_rng_evidence'] and not w['rng_tape_ref']: fail('missing RNG tape for RNG-required path')
        if p['required_hidden_info_evidence'] and not w['observation_evidence_ref']: fail('missing observation evidence for hidden-info path')
    if w['stdout_only'] is not False: fail('stdout_only=true')
    if not w['initial_semantic_state'] or not w['final_semantic_state'] or not w['state_assertions']: fail('incomplete state assertion')
    if any(x.get('result')!='PASS' or 'expected' not in x or 'actual' not in x for x in w['state_assertions']): fail('incomplete state assertion')
    ex={x.get('v2_path_id') for x in w['path_exercise'] if x.get('exercised') is True and x.get('trace_event_ids') and x.get('assertion_ids')}
    if not set(w['v2_path_ids'])<=ex: fail('missing V2 path coverage')
    e=w['execution']
    if e.get('engine')!='pinned-forge' or e.get('actual_rules_core_path') is not True: fail('non-production engine execution')
    if e.get('silent_fallbacks')!=0: fail('silent fallback')
    if e.get('authoritative_decision_boundary') not in {'USED','NOT_REQUIRED'}: fail('authoritative decision boundary invalid')
    if w['decision_tape_ref']:
        d=load(base/w['decision_tape_ref']); events=d.get('events',d if isinstance(d,list) else [])
        for ev in events:
            opts=ev.get('legal_options'); resp=ev.get('response')
            if not isinstance(opts,list) or resp not in opts or ev.get('validation_result')!='PASS': fail('illegal/non-authoritative pilot response')
            if ev.get('fallback_used'): fail('silent fallback')
    if w['rng_tape_ref']:
        r=load(base/w['rng_tape_ref'])
        if not r.get('events'): fail('missing RNG tape for RNG-required path')
    if w['observation_evidence_ref']:
        o=load(base/w['observation_evidence_ref'])
        if o.get('unauthorized_private_exposure_count',0)!=0: fail('cross-principal private observation exposure')
    tr=base/w['trace_ref']
    if not tr.exists() or hashlib.sha256(tr.read_bytes()).hexdigest()!=w['trace_sha256']: fail('forged/nonmatching trace hash')
    if w['status']=='PASS' and not w['rules_authority_refs']: fail('PASS witness lacks rules authority refs')
    return True

def main():
    p=argparse.ArgumentParser();p.add_argument('witness');p.add_argument('--manifest',required=True);p.add_argument('--base',default='.')
    a=p.parse_args();validate(load(a.witness),load(a.manifest),Path(a.base));print('PASS')
if __name__=='__main__': main()
