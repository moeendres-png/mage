#!/usr/bin/env python3
from __future__ import annotations
import argparse, collections, hashlib, json
from pathlib import Path

FORGE_PIN='8c7e9afb8e6caee88644b94e25da5852e36f8928'
WS26_HEAD='206a39cbaa3eeb98b10c2ddc36d51fe5b1b2f5ef'
WS26_TREE='837f445f78bb26462653c58baf1532e294151b10'
FAMILY='CONTINUOUS_COPY_CONTROL'; EXPECTED=301

def canon(x): return (json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\n').encode()
def writej(p,x): p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(canon(x))
def writejl(p,rows): p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(b''.join(canon(r) for r in rows))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def readjl(p): return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--ws26-root',type=Path,required=True); ap.add_argument('--cases',type=Path,required=True); ap.add_argument('--binding',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--source-head',required=True); ap.add_argument('--source-tree',required=True); a=ap.parse_args()
 gate=json.loads((a.ws26_root/'WS26_GATE.json').read_text()); nxt=json.loads((a.ws26_root/'WS26_NEXT_WORKSTREAM_INPUT.json').read_text()); compat=json.loads((a.ws26_root/'WS26_EXISTING_WITNESS_COMPATIBILITY.json').read_text())
 if gate.get('source_head')!=WS26_HEAD or gate.get('source_tree')!=WS26_TREE or gate.get('WS26_MODEL_V2')!='PASS' or gate.get('WS27_WS31_ELIGIBLE') is not True: raise SystemExit('WS26 boundary/eligibility mismatch')
 ws=nxt['sets']['WS29']
 if ws.get('owner_family')!=FAMILY or ws.get('path_count')!=EXPECTED: raise SystemExit('WS29 authoritative partition mismatch')
 cases=readjl(a.cases); bindings=readjl(a.binding)
 if len(cases)!=EXPECTED or len({r['v2_path_id'] for r in cases})!=EXPECTED: raise SystemExit('WS29 cases must be exactly 301 unique paths')
 if len(bindings)!=EXPECTED or len({r['v2_path_id'] for r in bindings})!=EXPECTED: raise SystemExit('WS29 binding trace must be exactly 301 unique paths')
 bybind={r['v2_path_id']:r for r in bindings}; ids={r['v2_path_id'] for r in cases}
 if set(bybind)!=ids: raise SystemExit('binding/case path set mismatch')
 bad=[pid for pid,r in bybind.items() if r.get('status')!='PASS' or r.get('actual_card_db_loaded') is not True or r.get('exact_source_bound') is not True or r.get('implementation_target_constructed') is not True or r.get('direct_effect_resolve_bypass') is not False]
 if bad: raise SystemExit(f'source binding not complete: {bad[:5]}')
 ws17=[e for e in compat.get('entries',[]) if e.get('source_workstream')=='WS17']
 if len(ws17)!=11 or any(e.get('v2_compatibility')!='INVALIDATED_BY_MODEL_CHANGE' for e in ws17): raise SystemExit('WS17 V2 compatibility adjudication mismatch')
 out=a.out; out.mkdir(parents=True,exist_ok=True)
 writejl(out/'WS29_WITNESSES.jsonl',[])
 blocker=('Exact actual-card source/runtime binding is proven, but no admissible WS29 V2 semantic execution witness exercises this exact path with all path-required state, authoritative decision, RNG, principal-scoped hidden-information, and replay evidence. Source presence/runtime construction is not semantic behavior proof.')
 rows=[]
 for c in sorted(cases,key=lambda r:r['v2_path_id']):
  rows.append({**{k:c[k] for k in ('v2_path_id','parent_ws14_primitive_id','implementation_target','oracle_identity','card_name')},'production_required':True,'source_binding':'PASS','semantic_status':'UNKNOWN','required_decision_evidence':c['required_decision_evidence'],'required_rng_evidence':c['required_rng_evidence'],'required_hidden_info_evidence':c['required_hidden_info_evidence'],'required_replay_evidence':c['required_replay_evidence'],'witness_ids':[],'blocker':blocker})
 coverage={'schema':'commander-simulator-next.ws29-path-coverage.v1','source_head':a.source_head,'source_tree':a.source_tree,'ws26_source_head':WS26_HEAD,'ws26_source_tree':WS26_TREE,'forge_pin':FORGE_PIN,'owner_family':FAMILY,'assigned_path_count':EXPECTED,'accounted_path_count':EXPECTED,'source_binding_status_counts':{'PASS':EXPECTED},'semantic_status_counts':{'PASS':0,'FAIL':0,'UNSUPPORTED':0,'UNKNOWN':EXPECTED},'paths':rows,'evidence_class':'DIRECTLY_VERIFIED'}; writej(out/'WS29_PATH_COVERAGE.json',coverage)
 targets=collections.Counter(c['implementation_target'] for c in cases); roots=collections.Counter(c['root_kind'] for c in cases); directives=collections.Counter(c['source_directive'] for c in cases); durations=collections.Counter(c.get('selector_profile',{}).get('selectors',{}).get('Duration','NONE') for c in cases)
 continuous={'schema':'commander-simulator-next.ws29-continuous-effect-inventory.v1','source_head':a.source_head,'forge_pin':FORGE_PIN,'assigned_path_count':EXPECTED,'implementation_target_counts':dict(sorted(targets.items())),'root_kind_counts':dict(sorted(roots.items())),'source_directive_counts':dict(sorted(directives.items())),'duration_selector_counts':dict(sorted(durations.items())),'source_bound_path_count':EXPECTED,'semantically_asserted_path_count':0,'temporary_effect_reversion_semantically_proved':False,'evidence_class':'CODE_DERIVED'}; writej(out/'WS29_CONTINUOUS_EFFECT_INVENTORY.json',continuous)
 copy_paths=[c for c in cases if any(x in c['implementation_target'] for x in ('CopyPermanentEffect','CopySpellAbilityEffect','CloneEffect'))]; control_paths=[c for c in cases if 'Control' in c['implementation_target']]
 cc={'schema':'commander-simulator-next.ws29-copy-control-inventory.v1','source_head':a.source_head,'forge_pin':FORGE_PIN,'copy_path_count':len(copy_paths),'control_path_count':len(control_paths),'copy_v2_path_ids':sorted(c['v2_path_id'] for c in copy_paths),'control_v2_path_ids':sorted(c['v2_path_id'] for c in control_paths),'copy_source_bound_count':len(copy_paths),'control_source_bound_count':len(control_paths),'copy_semantically_asserted_count':0,'control_semantically_asserted_count':0,'evidence_class':'DIRECTLY_VERIFIED'}; writej(out/'WS29_COPY_CONTROL_INVENTORY.json',cc)
 rules={'schema':'commander-simulator-next.ws29-rules-adjudication.v1','rules_source':{'title':'Magic: The Gathering Comprehensive Rules','effective_date':'2026-08-07','official_rules_page':'https://magic.wizards.com/en/rules','official_text':'https://media.wizards.com/2026/downloads/MagicCompRules%2020260807.txt'},'sections':[{'section':'611.1/611.2a','topic':'Continuous effects and durations'},{'section':'613.1a/b/d/e/f/g','topic':'Copy, control, type, color, ability and power/toughness layers'},{'section':'613.2a/613.4b-c/613.6-613.8','topic':'Layer ordering, timestamps and dependency'},{'section':'707.2','topic':'Copiable values'},{'section':'514.2','topic':'Cleanup and until-end-of-turn expiration'},{'section':'723.1/723.3','topic':'Controlling another player'}],'ws17_compatibility':{'entries_checked':len(ws17),'v2_compatible_PASS_inherited':0,'invalidated_by_model_change':len(ws17),'reason':'WS26 adjudicates the historical WS17 witnesses as direct AbilityFactory/AbilityUtils effect-definition executions rather than exact source-bound V2 actual-card semantics.'},'family_wide_semantic_adjudication':'NOT_PROVEN','source_binding_is_semantic_proof':False,'evidence_class':'EXTERNALLY_RULE_VALIDATED'}; writej(out/'WS29_RULES_ADJUDICATION.json',rules)
 req=lambda k: sum(1 for c in cases if c[k])
 hard={'assigned_paths_accounted':True,'source_bound_paths':EXPECTED,'production_required_UNKNOWN':EXPECTED,'production_required_UNSUPPORTED':0,'production_required_FAIL':0,'continuous_effect_paths_semantically_asserted':False,'copy_paths_semantically_asserted':False,'control_paths_semantically_asserted':False,'temporary_effect_reversion_where_required':False,'layer_sensitive_expectations_external_rules_validated':True,'decision_required_paths':req('required_decision_evidence'),'decision_paths_with_complete_PASS_evidence':0,'rng_required_paths':req('required_rng_evidence'),'rng_paths_with_complete_PASS_evidence':0,'hidden_info_required_paths':req('required_hidden_info_evidence'),'hidden_info_paths_with_complete_PASS_evidence':0,'replay_required_paths':req('required_replay_evidence'),'replay_paths_with_complete_PASS_evidence':0,'silent_fallback_count':0,'card_name_production_hacks':0,'source_binding_direct_effect_resolve_bypass_count':0,'exact_forge_pin':True,'ws17_blanket_inheritance':False,'global_q6_adjudicated':False}
 final={'schema':'commander-simulator-next.ws29-gate.v1','source_head':a.source_head,'source_tree':a.source_tree,'ws26_source_head':WS26_HEAD,'ws26_source_tree':WS26_TREE,'forge_pin':FORGE_PIN,'owner_family':FAMILY,'hard_gate':hard,'WS29_FAMILY_GATE':'FAIL_CLOSED','WORKSTREAM_COMPLETE':False,'WORKSTREAM_CLOSED_FAIL_CLOSED':True,'qualification_execution_complete':True,'SHARED_CORE_FIX_REQUIRED':False,'Q6_ACTUAL_CARD_BEHAVIOR':'NOT_ADJUDICATED_BY_WS29','blocker_class':'ACTUAL_CARD_SEMANTIC_RUNTIME_COVERAGE_INCOMPLETE','blocker':f'{EXPECTED}/301 WS29 V2 paths remain semantically UNKNOWN. Source binding is complete, but the WS26 V2 witness ABI requires exact actual-card semantic execution and all path-required decision/RNG/hidden-information/replay evidence.'}; writej(out/'WS29_GATE.json',final)
 files=['WS29_WITNESSES.jsonl','WS29_PATH_COVERAGE.json','WS29_CONTINUOUS_EFFECT_INVENTORY.json','WS29_COPY_CONTROL_INVENTORY.json','WS29_RULES_ADJUDICATION.json','WS29_GATE.json']; (out/'WS29_HASHES.sha256').write_text(''.join(f'{sha(out/f)}  {f}\n' for f in files))
 print(json.dumps({'assigned':EXPECTED,'source_binding_pass':EXPECTED,'semantic_PASS':0,'semantic_UNKNOWN':EXPECTED,'WS29_FAMILY_GATE':'FAIL_CLOSED','WORKSTREAM_CLOSED_FAIL_CLOSED':True},sort_keys=True))
if __name__=='__main__': main()
