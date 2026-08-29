#!/usr/bin/env python3
from __future__ import annotations
import argparse, copy, importlib.util, json, shutil
from pathlib import Path

def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,o): Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(o,sort_keys=True,separators=(',',':'))+'\n',encoding='utf-8')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--validator',type=Path,required=True);ap.add_argument('--schema',type=Path,required=True);a=ap.parse_args()
    out=a.out;manifest=load(out/'WS26_BEHAVIOR_PATH_MANIFEST_V2.json');schema=load(a.schema);positive=load(out/'WS26_POSITIVE_WITNESS.json')
    spec=importlib.util.spec_from_file_location('v',a.validator);v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
    v.validate(positive,manifest,out,schema)
    paths=manifest['paths']
    def pick(key):
        for p in paths:
            if p.get(key): return p
        raise SystemExit('no path for '+key)
    decision=pick('required_decision_evidence');rng=pick('required_rng_evidence');hidden=pick('required_hidden_info_evidence')
    base=copy.deepcopy(positive);results=[];root=out/'negative-fixtures';root.mkdir(exist_ok=True)
    def synth(p,wid):
        w=copy.deepcopy(base);w['witness_id']=wid;w['source_head']=manifest['source_head'];w['source_tree']=manifest['source_tree'];w['owner_family']=p['owner_family'];w['oracle_identities']=p['representative_actual_oracle_identities'][:1] or ['synthetic-contract-fixture'];par=p.get('parent_ws14_primitive_id');w['parent_ws14_primitive_ids']=[par] if par else [];w['v2_path_ids']=[p['v2_path_id']];w['primitive_exercise']=[{'primitive_id':par,'exercised':True}] if par else [];w['path_exercise']=[{'v2_path_id':p['v2_path_id'],'parent_ws14_primitive_id':par,'exercised':True,'assertion_ids':[w['state_assertions'][0]['assertion_id']],'trace_event_ids':['synthetic-contract-event']}];w['decision_tape_ref']=None;w['rng_tape_ref']=None;w['observation_evidence_ref']=None;w['status']='FAIL_CLOSED';w['evidence_class']='SYNTHETIC';w['rules_authority_refs']=[];return w
    def good_decision(): return {'events':[{'decision_id':'d1','actor':'p1','principal':'p1','decision_type':'TEST','legal_options':['option:1'],'response':'option:1','validation_result':'PASS','state_before_decision':{},'state_after_response':{},'fallback_used':False}]}
    def good_rng(): return {'events':[{'stream':'ws26.synthetic.contract','event_order':1,'operation':'test','result':1}]}
    def good_obs(): return {'unauthorized_private_exposure_count':0,'observations':[{'principal':'p1','visibility_scope':'PRINCIPAL_ONLY'}]}
    def satisfy(w,p,files):
        if p.get('required_decision_evidence'):w['decision_tape_ref']='decision.json';files['decision.json']=good_decision()
        if p.get('required_rng_evidence'):w['rng_tape_ref']='rng.json';files['rng.json']=good_rng()
        if p.get('required_hidden_info_evidence'):w['observation_evidence_ref']='obs.json';files['obs.json']=good_obs()
    def run(name,w,expected,files=None):
        d=root/name;d.mkdir(parents=True,exist_ok=True);shutil.copyfile(out/'WS26_POSITIVE_TRACE.json',d/'WS26_POSITIVE_TRACE.json');w=copy.deepcopy(w);w['trace_ref']='WS26_POSITIVE_TRACE.json';files=files or {}
        for fn,obj in files.items():dump(d/fn,obj)
        code=None
        try:v.validate(w,manifest,d,schema)
        except v.WitnessError as e:code=e.code
        if code not in expected:raise SystemExit(f'{name}: expected {expected}, got {code}')
        dump(d/'witness.json',w);results.append({'fixture':name,'result':'PASS_REJECTED','rejection_code':code})
    w=copy.deepcopy(base);w['v2_path_ids']=[];w['path_exercise']=[];run('01-missing-v2-path-coverage',w,{'SCHEMA_INVALID','MISSING_V2_PATH_COVERAGE'})
    w=copy.deepcopy(base);w['parent_ws14_primitive_ids']=[];run('02-mismatched-parent-primitive',w,{'PARENT_PRIMITIVE_MISMATCH'})
    w=copy.deepcopy(base);w['trace_sha256']='0'*64;run('03-forged-trace-hash',w,{'TRACE_HASH_MISMATCH'})
    w=copy.deepcopy(base);w['stdout_only']=True;run('04-stdout-only',w,{'SCHEMA_INVALID','STDOUT_ONLY_FORBIDDEN'})
    w=synth(decision,'negative-illegal-response');files={};satisfy(w,decision,files);files['decision.json']['events'][0]['response']='option:999';run('05-illegal-non-authoritative-response',w,{'ILLEGAL_NON_AUTHORITATIVE_RESPONSE'},files)
    w=synth(rng,'negative-missing-rng');files={};satisfy(w,rng,files);w['rng_tape_ref']=None;files.pop('rng.json',None);run('06-missing-rng-tape',w,{'RNG_TAPE_REQUIRED'},files)
    w=synth(decision,'negative-missing-decision');files={};satisfy(w,decision,files);w['decision_tape_ref']=None;files.pop('decision.json',None);run('07-missing-decision-tape',w,{'DECISION_TAPE_REQUIRED'},files)
    w=synth(hidden,'negative-hidden-exposure');files={};satisfy(w,hidden,files);files['obs.json']={'unauthorized_private_exposure_count':1,'observations':[{'principal':'p2','visibility_scope':'PRINCIPAL_ONLY'}]};run('08-cross-principal-private-exposure',w,{'HIDDEN_INFO_VIOLATION'},files)
    w=copy.deepcopy(base);w['forge_pin']='0'*40;run('09-source-forge-pin-mismatch',w,{'SCHEMA_INVALID','SOURCE_PIN_MISMATCH'})
    w=copy.deepcopy(base);w['state_assertions']=[];run('10-incomplete-state-assertion',w,{'SCHEMA_INVALID','INCOMPLETE_STATE_ASSERTION'})
    result={'schema':'commander-simulator-next.ws26-negative-fixture-results.v1','positive_fixture':'PASS','negative_fixture_count':len(results),'negative_ABI_fixtures':'PASS','illegal_response_rejected':'PASS','results':results,'evidence_class':'TECHNICALLY_CONFORMANT'};dump(out/'WS26_NEGATIVE_FIXTURE_RESULTS.json',result)
    gate=load(out/'WS26_HARNESS_GATE.json');gate['negative_ABI_fixtures']='PASS';gate['illegal_response_rejected']='PASS';gate['negative_fixture_results']=results;dump(out/'WS26_HARNESS_GATE.json',gate)
    print('WS26_HARNESS_FIXTURES=PASS')
if __name__=='__main__':main()
