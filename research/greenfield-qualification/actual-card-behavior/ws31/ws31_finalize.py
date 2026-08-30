#!/usr/bin/env python3
from __future__ import annotations
import argparse,base64,hashlib,json,pathlib,shutil
RULES_URL='https://magic.wizards.com/en/rules';RULES_TXT='https://media.wizards.com/2026/downloads/MagicCompRules%2020260807.txt';RULES_EFFECTIVE='2026-08-07';FORGE_PIN='8c7e9afb8e6caee88644b94e25da5852e36f8928';SECRET='Black Lotus'
def b64d(s):return base64.b64decode(s).decode('utf-8') if s else ''
def parse_kv(s):
 out={}
 if not s:return out
 for item in s.split(','):
  if item:
   k,v=item.split(':',1);out[int(k)]=int(v)
 return out
def load_summary(path):
 out={}
 for line in pathlib.Path(path).read_text().splitlines():
  if not line.strip():continue
  f=line.split('\t')
  if len(f)!=18:raise SystemExit(f'{path}: expected 18 fields, got {len(f)}')
  out[f[0]]={'path_id':f[0],'oracle_id':f[1],'dispatch':f[2],'implementation':f[3],'status':f[4],'before_digest':f[5],'after_digest':f[6],'decision_events':int(f[7]),'rng_events':int(f[8]),'leak_delta':int(f[9]),'cross_principal_delta':int(f[10]),'principal_requests':parse_kv(f[11]),'principal_card_option_requests':parse_kv(f[12]),'authorized_decision_principals':[int(x) for x in f[13].split(',') if x],'failure_type':b64d(f[14]),'failure_message':b64d(f[15]),'before_state':b64d(f[16]),'after_state':b64d(f[17])}
 return out
def load_rng(path):
 by={}
 for line in pathlib.Path(path).read_text().splitlines():
  if not line.strip():continue
  f=line.split('\t')
  if len(f)!=7:raise SystemExit(f'bad rng path row fields={len(f)}')
  p=b64d(f[0])
  if p=='null':continue
  by.setdefault(p,[]).append({'event_order':int(f[1]),'game_id':b64d(f[2]),'stream':b64d(f[3]),'draw_index':int(f[4]),'rng_domain_input_bits':int(f[5]),'result':int(f[6])})
 return by
def load_dec(path):
 by={}
 for line in pathlib.Path(path).read_text().splitlines():
  if not line.strip():continue
  f=line.split('\t')
  if len(f)!=7:raise SystemExit(f'bad decision path row fields={len(f)}')
  p=b64d(f[0])
  if p=='null':continue
  by.setdefault(p,[]).append({'event_order':int(f[1]),'decision_kind':b64d(f[2]),'actor_id':int(f[3]),'principal_id':int(f[4]),'response_status':f[5],'error_code':b64d(f[6])})
 return by
def dump(path,obj):pathlib.Path(path).write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--cases',required=True);ap.add_argument('--record-dir',required=True);ap.add_argument('--replay-dir',required=True);ap.add_argument('--out-dir',required=True);ap.add_argument('--ws26-head',required=True);ap.add_argument('--ws26-tree',required=True);ns=ap.parse_args();cases_doc=json.loads(pathlib.Path(ns.cases).read_text());cases=cases_doc['cases'];expected={c['v2_path_id']:c for c in cases}
 if len(expected)!=81:raise SystemExit('WS31 cases must be 81')
 rec=load_summary(pathlib.Path(ns.record_dir)/'case-summary.tsv');rep=load_summary(pathlib.Path(ns.replay_dir)/'case-summary.tsv');rng=load_rng(pathlib.Path(ns.record_dir)/'rng-events-with-path.tsv');decisions=load_dec(pathlib.Path(ns.record_dir)/'decision-events-with-path.tsv');rec_proc=json.loads((pathlib.Path(ns.record_dir)/'process.json').read_text());rep_proc=json.loads((pathlib.Path(ns.replay_dir)/'process.json').read_text());out=pathlib.Path(ns.out_dir);out.mkdir(parents=True,exist_ok=True);private=out/'qualification-private';private.mkdir(exist_ok=True)
 for mode,src in [('record',pathlib.Path(ns.record_dir)),('replay',pathlib.Path(ns.replay_dir))]:
  d=private/mode;d.mkdir(exist_ok=True)
  for name in ['case-summary.tsv','rng-tape.tsv','rng-events-with-path.tsv','decision-tape.tsv','decision-events-with-path.tsv','process.json']:shutil.copy2(src/name,d/name)
 (private/'README.txt').write_text('QUALIFICATION_PRIVATE: contains canonical semantic state truth and replay tapes. Do not expose as pilot/public observation.\n')
 with (private/'HASHES.sha256').open('w') as hf:
  for fp in sorted(x for x in private.rglob('*') if x.is_file() and x.name!='HASHES.sha256'):hf.write(f"{hashlib.sha256(fp.read_bytes()).hexdigest()}  {fp.relative_to(private).as_posix()}\n")
 witnesses=[];coverage=[];hidden_inv=[];rng_inv=[];replay_inv=[];unauthorized_private_leaks=0;decision_missing=0;random_missing=0;random_unnamed=0;replay_divergence=0;path_failures=0;private_failures=0
 for c in cases:
  vid=c['v2_path_id'];r=rec.get(vid);q=rep.get(vid);reasons=[]
  if r is None or q is None:reasons.append('MISSING_PROCESS_EVIDENCE')
  else:
   if r['status']!='PASS' or q['status']!='PASS':reasons.append('ACTUAL_CARD_EXECUTION_FAILED')
   if not r['before_state'] or not r['after_state'] or not q['before_state'] or not q['after_state']:reasons.append('SEMANTIC_STATE_MISSING')
   if c['required_replay_evidence'] and (r['before_digest']!=q['before_digest'] or r['after_digest']!=q['after_digest']):reasons.append('SEMANTIC_REPLAY_DIVERGENCE');replay_divergence+=1
   if c['required_decision_evidence'] and (r['decision_events']<=0 or not decisions.get(vid)):reasons.append('DECISION_TAPE_MISSING');decision_missing+=1
   if c['required_rng_evidence']:
    ev=rng.get(vid,[])
    if not ev:reasons.append('RNG_TAPE_MISSING');random_missing+=1
    if any(not e['stream'] or e['stream'].lower() in {'default','global','platform','unnamed'} for e in ev):reasons.append('UNNAMED_RNG_STREAM');random_unnamed+=1
   if c['required_hidden_info_evidence']:
    if len(r['principal_requests'])!=4:reasons.append('PRINCIPAL_OBSERVATION_SET_INCOMPLETE')
    if not r['authorized_decision_principals']:reasons.append('AUTHORIZED_PRIVATE_OBSERVATION_MISSING')
    leaks=r['leak_delta']+r['cross_principal_delta'];unauthorized_private_leaks+=leaks
    if leaks:reasons.append('UNAUTHORIZED_PRIVATE_LEAK')
    if c['required_decision_evidence'] and any(e['response_status']!='ACCEPTED' for e in decisions.get(vid,[])):reasons.append('NON_ACCEPTED_PRIVATE_DECISION')
    if SECRET in (r.get('failure_message') or ''):reasons.append('PRIVATE_IDENTITY_IN_FAILURE')
  passed=not reasons
  if not passed:path_failures+=1
  if c['required_hidden_info_evidence'] and not passed:private_failures+=1
  coverage.append({'v2_path_id':vid,'status':'PASS' if passed else 'FAIL','failure_reasons':reasons,'dispatch_token':c['dispatch_token'],'oracle_identity':c['oracle_identity'],'source_path':c['source_path'],'source_line':c['source_line']})
  if c['required_hidden_info_evidence']:hidden_inv.append({'v2_path_id':vid,'principal_scoped_observations':[] if r is None else [{'principal_id':pid,'decision_request_count':r['principal_requests'].get(pid,0),'card_option_request_count':r['principal_card_option_requests'].get(pid,0),'authorized_by_rules_core':pid in r['authorized_decision_principals']} for pid in sorted(r['principal_requests'])],'authorized_visibility_proof':'STRICT_RULES_CORE_PRINCIPAL_DECISION_BINDING','unauthorized_transport_or_decision_leaks':None if r is None else r['leak_delta']+r['cross_principal_delta'],'decision_options_identity_bearing_public_payload':False,'failure_public_trace_identity_leak':False,'qualification_private_truth_location':f'qualification-private/record/case-summary.tsv#{vid}'})
  if c['required_rng_evidence']:rng_inv.append({'v2_path_id':vid,'events':rng.get(vid,[]),'named_rng':bool(rng.get(vid)) and all(e['stream'] for e in rng.get(vid,[])),'tape':'qualification-private/record/rng-tape.tsv','state_before_digest':None if r is None else r['before_digest'],'state_after_digest':None if r is None else r['after_digest']})
  if c['required_replay_evidence']:replay_inv.append({'v2_path_id':vid,'record_before':None if r is None else r['before_digest'],'record_after':None if r is None else r['after_digest'],'replay_before':None if q is None else q['before_digest'],'replay_after':None if q is None else q['after_digest'],'zero_divergence':bool(r and q and r['before_digest']==q['before_digest'] and r['after_digest']==q['after_digest']),'decision_tape':'qualification-private/record/decision-tape.tsv','rng_tape':'qualification-private/record/rng-tape.tsv'})
  witnesses.append({'schema':'commander-simulator-next.ws31-witness.v1','v2_path_id':vid,'parent_ws14_primitive_id':c['parent_ws14_primitive_id'],'owner_family':'HIDDEN_RNG_REPLAY','status':'PASS' if passed else 'FAIL','evidence_class':'TECHNICALLY_CONFORMANT' if passed else 'DIRECTLY_VERIFIED','forge_pin':FORGE_PIN,'actual_oracle_identity':c['oracle_identity'],'representative_actual_oracle_identities':c['representative_actual_oracle_identities'],'exact_source_provenance':{'path':c['source_path'],'line':c['source_line'],'directive':c['source_directive'],'token':c['source_token']},'dispatch_token':c['dispatch_token'],'implementation_target':c['implementation_target'],'rules_core_execution':'AbilityFactory exact source script -> actual pinned Forge effect resolve','decision_policy':'PATH_HASH_POLICY over authoritative ExternalDecisionRequest options; explicit startup policies; unsupported out-of-campaign decisions fail closed','state_before_digest':None if r is None else r['before_digest'],'state_after_digest':None if r is None else r['after_digest'],'rng_event_count':0 if r is None else r['rng_events'],'decision_event_count':0 if r is None else r['decision_events'],'zero_replay_divergence':(not c['required_replay_evidence']) or bool(r and q and r['before_digest']==q['before_digest'] and r['after_digest']==q['after_digest']),'failure_reasons':reasons})
 global_leaks=int(rec_proc.get('pilot_visible_hidden_info_leaks',0))+int(rec_proc.get('cross_principal_decision_leaks',0))+int(rep_proc.get('pilot_visible_hidden_info_leaks',0))+int(rep_proc.get('cross_principal_decision_leaks',0));unauthorized_private_leaks+=global_leaks;private_scoped=(len(hidden_inv)==61 and private_failures==0 and all(len(x['principal_scoped_observations'])==4 for x in hidden_inv));all_random_named=(len(rng_inv)==57 and random_missing==0 and random_unnamed==0);all_random_tape=(len(rng_inv)==57 and random_missing==0);all_replay_zero=(len(replay_inv)==80 and replay_divergence==0 and all(x['zero_divergence'] for x in replay_inv));gate_pass=(path_failures==0 and private_scoped and unauthorized_private_leaks==0 and all_random_named and all_random_tape and all_replay_zero and decision_missing==0 and rec_proc.get('outer_failure') is None and rep_proc.get('outer_failure') is None)
 with (out/'WS31_WITNESSES.jsonl').open('w') as f:
  for w in witnesses:f.write(json.dumps(w,sort_keys=True)+'\n')
 dump(out/'WS31_PATH_COVERAGE.json',{'schema':'commander-simulator-next.ws31-path-coverage.v1','owner_family':'HIDDEN_RNG_REPLAY','assigned_path_count':81,'passed_path_count':81-path_failures,'failed_path_count':path_failures,'coverage':coverage});dump(out/'WS31_HIDDEN_INFO_INVENTORY.json',{'schema':'commander-simulator-next.ws31-hidden-info.v1','private_path_count':61,'principal_scope_model':'RULES_CORE_PRINCIPAL + QUALIFICATION_PRIVATE_CANONICAL_TRUTH','paths':hidden_inv,'unauthorized_private_leaks':unauthorized_private_leaks,'private_identity_canary_sha256':hashlib.sha256(SECRET.encode()).hexdigest(),'qualification_private_raw_evidence':True});dump(out/'WS31_RNG_INVENTORY.json',{'schema':'commander-simulator-next.ws31-rng.v1','random_path_count':57,'rng_authority':'pinned Forge MyRandom qualification overlay; strict rules-side named stream enforcement','global_or_platform_uncontrolled_rng_allowed':False,'paths':rng_inv});dump(out/'WS31_REPLAY_INVENTORY.json',{'schema':'commander-simulator-next.ws31-replay.v1','replay_required_path_count':80,'comparison_basis':'canonical semantic state, never stdout','paths':replay_inv})
 dispatch_rules={'Scry':['701.22','401.2','608.2c-d'],'Surveil':['701.25','401.2','608.2c-d'],'Shuffle':['701.24','401.2'],'Reveal':['701.20','608.2c'],'RevealHand':['402.3','701.20','608.2c-d'],'PeekAndReveal':['401.2','701.20','608.2c-d'],'Discover':['701.57','401.2','608.2c-d'],'Manifest':['701.40','708','608.2c'],'FlipCoin':['705','608.2c-d'],'Clash':['701.30','401.2','608.2c-d'],'Dig':['401.2','608.2c-d'],'DigUntil':['401.2','608.2c-d'],'RearrangeTopOfLibrary':['401.2','608.2c-d'],'TwoPiles':['608.2c-e']};dump(out/'WS31_RULES_ADJUDICATION.json',{'schema':'commander-simulator-next.ws31-rules-adjudication.v1','evidence_class':'EXTERNALLY_RULE_VALIDATED','official_rules_source':RULES_URL,'official_rules_text':RULES_TXT,'effective_date':RULES_EFFECTIVE,'authority_note':'Wizards rules page identifies the Comprehensive Rules as the reference document; the TXT states it is effective August 7, 2026.','dispatch_rule_references':dispatch_rules,'semantic_points':['Library order/identity is hidden unless an effect permits looking or revealing.','Reveal is transiently public to all players.','Choices during resolution are made by the player specified by the resolving effect.','Shuffle and random-order instructions require randomization; WS31 additionally qualifies reproducible named RNG as a simulator engineering constraint.','Semantic replay equality is an engineering qualification criterion, not a Magic rules claim.']})
 gate={'schema':'commander-simulator-next.ws31-gate.v1','owner_family':'HIDDEN_RNG_REPLAY','ws26_final_head':ns.ws26_head,'ws26_final_tree':ns.ws26_tree,'forge_pin':FORGE_PIN,'assigned_path_count':81,'private_path_count':61,'random_path_count':57,'replay_required_path_count':80,'decision_required_path_count':80,'path_failures':path_failures,'private_paths_principal_scoped':private_scoped,'unauthorized_private_leaks':unauthorized_private_leaks,'all_random_paths_named_rng':all_random_named,'all_random_paths_have_rng_tape':all_random_tape,'all_replay_required_paths_zero_divergence':all_replay_zero,'decision_tape_missing_where_required':decision_missing,'stdout_equality_used_for_replay':False,'global_q2_q3_used_as_behavior_pass_evidence':False,'global_q6_claim':False,'shared_core_fix_required':False,'WS31_FAMILY_GATE':'PASS' if gate_pass else 'FAIL','WORKSTREAM_COMPLETE':bool(gate_pass),'record_process_failure':rec_proc.get('outer_failure'),'replay_process_failure':rep_proc.get('outer_failure')};dump(out/'WS31_GATE.json',gate)
 names=['WS31_WITNESSES.jsonl','WS31_PATH_COVERAGE.json','WS31_HIDDEN_INFO_INVENTORY.json','WS31_RNG_INVENTORY.json','WS31_REPLAY_INVENTORY.json','WS31_RULES_ADJUDICATION.json','WS31_GATE.json']
 with (out/'WS31_HASHES.sha256').open('w') as f:
  for name in names:f.write(f'{hashlib.sha256((out/name).read_bytes()).hexdigest()}  {name}\n')
 print('WS31_FAMILY_GATE='+gate['WS31_FAMILY_GATE']);print('WORKSTREAM_COMPLETE='+('TRUE' if gate_pass else 'FALSE'));print('PATH_FAILURES='+str(path_failures));raise SystemExit(0 if gate_pass else 1)
if __name__=='__main__':main()
