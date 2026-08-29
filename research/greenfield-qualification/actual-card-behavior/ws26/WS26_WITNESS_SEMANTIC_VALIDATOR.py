#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import jsonschema

PIN='8c7e9afb8e6caee88644b94e25da5852e36f8928'
OWNERS={'ACTION_COST_DECISION','TRIGGER_REPLACEMENT_ZONE_SBA','CONTINUOUS_COPY_CONTROL','COMBAT_COMMANDER','HIDDEN_RNG_REPLAY'}
class WitnessError(ValueError):
    def __init__(self,code,msg): super().__init__(msg); self.code=code

def fail(code,msg): raise WitnessError(code,msg)
def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def allowed_sources(manifest):
    out={(manifest['source_head'],manifest['source_tree'])}
    out.update((x['head'],x['tree']) for x in manifest.get('inherited_execution_sources',[]))
    return out

def decision_events(doc):
    if isinstance(doc,list): return doc
    return doc.get('events',[]) if isinstance(doc,dict) else []
def option_ids(opts):
    out=[]
    for x in opts or []:
        if isinstance(x,str): out.append(x)
        elif isinstance(x,dict): out.append(x.get('option_id') or x.get('id'))
    return [x for x in out if x is not None]
def responses(v): return v if isinstance(v,list) else ([] if v is None else [v])

def validate(w,manifest,base:Path,schema):
    try: jsonschema.Draft202012Validator(schema).validate(w)
    except jsonschema.ValidationError as e: fail('SCHEMA_INVALID',e.message)
    if w['forge_pin']!=PIN or manifest.get('forge_pin')!=PIN: fail('SOURCE_PIN_MISMATCH','Forge pin mismatch')
    if (w['source_head'],w['source_tree']) not in allowed_sources(manifest): fail('SOURCE_PIN_MISMATCH','witness source is neither WS26 source nor an exact inherited execution source')
    if w['owner_family'] not in OWNERS: fail('OWNER_MISMATCH','invalid owner family')
    paths={p['v2_path_id']:p for p in manifest.get('paths',[])}
    if not w['v2_path_ids']: fail('MISSING_V2_PATH_COVERAGE','empty V2 coverage')
    for pid in w['v2_path_ids']:
        if pid not in paths: fail('MISSING_V2_PATH_COVERAGE','unknown V2 path '+pid)
        p=paths[pid]
        if p['owner_family']!=w['owner_family']: fail('OWNER_MISMATCH',pid)
        par=p.get('parent_ws14_primitive_id')
        if par and par not in w['parent_ws14_primitive_ids']: fail('PARENT_PRIMITIVE_MISMATCH',pid)
        if p.get('required_decision_evidence') and not w['decision_tape_ref']: fail('DECISION_TAPE_REQUIRED',pid)
        if p.get('required_rng_evidence') and not w['rng_tape_ref']: fail('RNG_TAPE_REQUIRED',pid)
        if p.get('required_hidden_info_evidence') and not w['observation_evidence_ref']: fail('OBSERVATION_EVIDENCE_REQUIRED',pid)
    if w['stdout_only'] is not False: fail('STDOUT_ONLY_FORBIDDEN','stdout_only=true')
    if not w['initial_semantic_state'] or not w['final_semantic_state'] or not w['state_assertions']: fail('INCOMPLETE_STATE_ASSERTION','state evidence missing')
    aids=set()
    for x in w['state_assertions']:
        if x.get('result')!='PASS' or 'expected' not in x or 'actual' not in x: fail('INCOMPLETE_STATE_ASSERTION','assertion incomplete')
        aids.add(x['assertion_id'])
    exercised={}
    for x in w['path_exercise']:
        if x.get('exercised') is True and x.get('trace_event_ids') and x.get('assertion_ids'):
            if not set(x['assertion_ids'])<=aids: fail('INCOMPLETE_STATE_ASSERTION','path references unknown assertion')
            exercised[x['v2_path_id']]=x
    if not set(w['v2_path_ids'])<=set(exercised): fail('MISSING_V2_PATH_COVERAGE','not every claimed path is exercised')
    for pid,x in exercised.items():
        par=paths[pid].get('parent_ws14_primitive_id')
        if x.get('parent_ws14_primitive_id')!=par: fail('PARENT_PRIMITIVE_MISMATCH',pid)
    prim_ex={x.get('primitive_id') for x in w['primitive_exercise'] if x.get('exercised') is True}
    if not set(w['parent_ws14_primitive_ids'])<=prim_ex: fail('PARENT_PRIMITIVE_MISMATCH','parent primitive not exercised')
    e=w['execution']
    if e.get('engine')!='pinned-forge' or e.get('actual_rules_core_path') is not True: fail('NON_PRODUCTION_EXECUTION','pinned Rules Core required')
    if e.get('silent_fallbacks')!=0: fail('SILENT_FALLBACK','silent fallback')
    if e.get('authoritative_decision_boundary') not in {'USED','NOT_REQUIRED'}: fail('DECISION_BOUNDARY_INVALID','invalid boundary state')
    if w['decision_tape_ref']:
        evs=decision_events(load(base/w['decision_tape_ref']))
        if not evs: fail('DECISION_TAPE_REQUIRED','empty decision tape')
        for ev in evs:
            legal=set(option_ids(ev.get('legal_options') or ev.get('options'))); resp=responses(ev.get('response') if 'response' in ev else ev.get('selected_option_ids'))
            if ev.get('validation_result',ev.get('response_status')) not in {'PASS','ACCEPTED'}: fail('ILLEGAL_NON_AUTHORITATIVE_RESPONSE','response not accepted')
            if any(x not in legal for x in resp): fail('ILLEGAL_NON_AUTHORITATIVE_RESPONSE','response outside authoritative set')
            if ev.get('fallback_used'): fail('SILENT_FALLBACK','decision fallback used')
    if w['rng_tape_ref']:
        r=load(base/w['rng_tape_ref'])
        if not r.get('events'): fail('RNG_TAPE_REQUIRED','empty RNG tape')
        if any('stream' not in x and 'stream_id' not in x for x in r['events']): fail('RNG_TAPE_REQUIRED','unnamed RNG stream')
    if w['observation_evidence_ref']:
        o=load(base/w['observation_evidence_ref'])
        leaks=max(o.get('unauthorized_private_exposure_count',0),o.get('cross_principal_private_exposure_count',0))
        if leaks!=0: fail('HIDDEN_INFO_VIOLATION','cross-principal private exposure')
    tr=base/w['trace_ref']
    if not tr.is_file() or hashlib.sha256(tr.read_bytes()).hexdigest()!=w['trace_sha256']: fail('TRACE_HASH_MISMATCH','trace hash mismatch')
    if w['status']=='PASS' and not w['rules_authority_refs']: fail('RULES_AUTHORITY_REQUIRED','PASS lacks official rules authority')
    return True

def main():
    p=argparse.ArgumentParser();p.add_argument('witness');p.add_argument('--manifest',required=True);p.add_argument('--schema',required=True);p.add_argument('--base',default='.')
    a=p.parse_args()
    try:
        validate(load(a.witness),load(a.manifest),Path(a.base),load(a.schema));print('WS26_WITNESS_VALIDATION=PASS')
    except WitnessError as e:
        print('WS26_WITNESS_VALIDATION=FAIL code='+e.code+' message='+str(e));raise SystemExit(2)
if __name__=='__main__':main()
