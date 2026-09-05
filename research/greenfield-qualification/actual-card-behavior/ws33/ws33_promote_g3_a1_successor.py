#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, shutil
from collections import Counter, defaultdict
from pathlib import Path

FORGE_PIN='8c7e9afb8e6caee88644b94e25da5852e36f8928'
MANIFEST_SHA='cd48f4279d682ab944e2534bf937d87e5311e83989e97179ae73c5c7d1bb6224'
CONSUMER_SHA='82638e6b3e4408cc5bddedc49372b6357d3c2bdce6fba7bfab7ed119678f9a48'
A1_ARTIFACT_ID='9979087306'
A1_ARTIFACT_DIGEST='sha256:a414f73b2f7d259dce19e64733fcb000a10b00ac4ca579f36190c1ba3064d11b'
A1_SOURCE_HEAD='5f81b489541d1638758b201916b8dc9f9544987f'
STATUS_KEYS=('PASS','FAIL','UNSUPPORTED','UNKNOWN')

def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def load_jsonl(p): return [json.loads(x) for x in Path(p).read_text(encoding='utf-8').splitlines() if x.strip()]
def canon(x): return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\n'
def write(p,x): Path(p).parent.mkdir(parents=True,exist_ok=True); Path(p).write_text(canon(x),encoding='utf-8')
def write_jsonl(p,rows): Path(p).write_text(''.join(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\n' for x in rows),encoding='utf-8')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def req(c,m):
    if not c: raise SystemExit('WS33_G3_A1_SUCCESSOR=FAIL '+m)

def verify_hash_manifest(root, manifest):
    n=0
    for line in Path(manifest).read_text().splitlines():
        if not line.strip(): continue
        exp, sep, rel = line.partition('  ')
        req(sep=='  ' and len(exp)==64,'bad A1 hash row')
        p=Path(root)/rel
        req(p.is_file(),f'missing A1 hashed file {rel}')
        req(sha(p)==exp,f'A1 hash mismatch {rel}')
        n+=1
    return n

def recompute_derived(root:Path):
    covdoc=load(root/'WS33_PATH_COVERAGE.json'); cov=covdoc['paths']; byid={r['effective_v2_path_id']:r for r in cov}
    pass_ids={i for i,r in byid.items() if r['status']=='PASS'}
    covdoc['status_counts']=dict(Counter(r['status'] for r in cov)); write(root/'WS33_PATH_COVERAGE.json',covdoc)
    cases=load_jsonl(root/'WS33_CASE_LEDGER.jsonl'); cby={r['effective_v2_path_id']:r for r in cases}
    exes=load_jsonl(root/'WS33_EXECUTION_LEDGER.jsonl'); eby={r['effective_v2_path_id']:r for r in exes}
    write_jsonl(root/'WS33_CASE_LEDGER.jsonl',[cby[i] for i in sorted(cby)])
    write_jsonl(root/'WS33_EXECUTION_LEDGER.jsonl',[eby[i] for i in sorted(eby)])
    td=load(root/'WS33_SCENARIO_TEMPLATE_REGISTRY.json')
    for t in td['templates']:
        ids=set(t['path_ids']); admitted=sorted(ids&pass_ids); remaining=sorted(ids-pass_ids)
        t['admitted_path_ids']=admitted; t['remaining_path_ids']=remaining
        t['status']='FULLY_EXECUTED' if not remaining else ('PARTIALLY_EXECUTED' if admitted else 'MISSING_SCENARIO_TEMPLATE')
    write(root/'WS33_SCENARIO_TEMPLATE_REGISTRY.json',td)
    target=load(root/'WS33_IMPLEMENTATION_TARGET_REGISTRY.json')
    for t in target['targets']:
        unproved=sum(i not in pass_ids for i in t['path_ids']); t['unproved_path_count']=unproved; t['priority_score']=unproved*t['cross_family_dependency_fanout']
    target['targets'].sort(key=lambda x:(-x['priority_score'],x['owner_family'],x['implementation_target'])); write(root/'WS33_IMPLEMENTATION_TARGET_REGISTRY.json',target)
    identities=load_jsonl(root/'WS33_PER_IDENTITY.jsonl')
    for x in identities:
        eff=set(x['effective_v2_path_ids']); x['pass_path_ids']=sorted(eff&pass_ids); x['unresolved_path_ids']=sorted(eff-pass_ids); x['status']='FULL' if not x['unresolved_path_ids'] else 'PARTIAL'
    write_jsonl(root/'WS33_PER_IDENTITY.jsonl',identities)
    status=Counter(r['status'] for r in cov); template_counts=Counter(t['status'] for t in td['templates']); identity_counts=Counter(x['status'] for x in identities); fam=defaultdict(list)
    for r in cov: fam[r['owner_family']].append(r)
    family_gates={}
    for family,rows in sorted(fam.items()):
        counts=Counter(r['status'] for r in rows); family_gates[family]={'gate':'PASS' if counts.get('PASS')==len(rows) else 'FAIL_CLOSED','counts':dict(counts),'effective_path_count':len(rows)}
    q=load(root/'WS33_Q6_CANDIDATE_GATE.json'); complete=status==Counter({'PASS':len(cov)})
    q.update({'WORKSTREAM_COMPLETE':False,'WS33_ACTUAL_CARD_CAMPAIGN':'PASS' if complete else 'FAIL_CLOSED','Q6_CANDIDATE_FOR_CROSS_QUALIFICATION':False,'WS34_ELIGIBLE':False,
      'identity_counts':dict(identity_counts),'path_status_counts':{k:status.get(k,0) for k in STATUS_KEYS},'family_gates':family_gates,
      'scenario_group_counts':{k:template_counts.get(k,0) for k in ('FULLY_EXECUTED','PARTIALLY_EXECUTED','MISSING_SCENARIO_TEMPLATE')},
      'incomplete_scenario_group_count':sum(v for k,v in template_counts.items() if k!='FULLY_EXECUTED')})
    blockers=[]
    if status.get('UNKNOWN'): blockers.append({'class':'MISSING_SCENARIO_TEMPLATE','path_count':status['UNKNOWN'],'incomplete_group_count':q['incomplete_scenario_group_count']})
    if status.get('FAIL'): blockers.append({'class':'ACTUAL_CARD_CAMPAIGN_FAILURE','path_count':status['FAIL']})
    if status.get('UNSUPPORTED'): blockers.append({'class':'UNSUPPORTED_PRODUCTION_PATH','path_count':status['UNSUPPORTED']})
    q['remaining_blockers']=blockers; write(root/'WS33_Q6_CANDIDATE_GATE.json',q)
    return status

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--base-root',type=Path,required=True); ap.add_argument('--a1-root',type=Path,required=True); ap.add_argument('--checkpoint',type=Path,required=True); ap.add_argument('--out-root',type=Path,required=True); ap.add_argument('--source-head',required=True); ap.add_argument('--source-tree',required=True); a=ap.parse_args()
    base=a.base_root.resolve(); a1=a.a1_root.resolve(); out=a.out_root.resolve(); cp=a.checkpoint.resolve()
    req(base.is_dir() and a1.is_dir() and cp.is_file(),'missing inputs')
    if out.exists(): shutil.rmtree(out)
    shutil.copytree(base,out)
    manifest=load(out/'WS33_EFFECTIVE_BEHAVIOR_PATH_MANIFEST.json'); req(sha(out/'WS33_EFFECTIVE_BEHAVIOR_PATH_MANIFEST.json')==MANIFEST_SHA,'manifest sha'); req(manifest['forge_pin']==FORGE_PIN and manifest['consumer_model_sha256']==CONSUMER_SHA,'model lineage')
    mp={p['v2_path_id']:p for p in manifest['paths']}; req(len(mp)==4188,'path count or duplicate path identity')
    covdoc=load(out/'WS33_PATH_COVERAGE.json'); cb={r['effective_v2_path_id']:r for r in covdoc['paths']}; req(len(cb)==4188,'duplicate coverage identity'); before_status={i:r['status'] for i,r in cb.items()}; before=Counter(before_status.values()); req(before==Counter({'UNKNOWN':3903,'PASS':285}),'base coverage not 285/3903')
    cptext=cp.read_text(encoding='utf-8')
    for marker in ['G_TOTAL = 81','G_PASS = 81','G_UNKNOWN = 0','G_FAIL = 0','G_UNSUPPORTED = 0','G3_COMPLETE = TRUE','artifact `9866293827`','artifact `9803814288`','artifact `9957712911`']:
        req(marker in cptext,'G3 checkpoint marker '+marker)
    gids=sorted(i for i,p in mp.items() if p['owner_family']=='HIDDEN_RNG_REPLAY'); req(len(gids)==81,'G partition cardinality'); req(all(cb[i]['status']=='UNKNOWN' for i in gids),'G base not all UNKNOWN')
    gate=load(a1/'ABC_A1_GATE.json'); req(gate['result']=='PASS' and gate['path_count']==122,'A1 gate'); req(gate['forge_pin']==FORGE_PIN and gate['manifest_sha256']==MANIFEST_SHA and gate['consumer_model_sha256']==CONSUMER_SHA and gate['source_head']==A1_SOURCE_HEAD,'A1 lineage')
    hash_entries=verify_hash_manifest(a1,a1/'ABC_A1_HASHES.sha256'); req(hash_entries==862,'A1 hash entry count')
    recroot=a1/'records'; recs={}
    for d in recroot.iterdir():
        if not d.is_dir(): continue
        r=load(d/'record.json'); req(len(r['v2_path_ids'])==1,'A1 record multi-path'); pid=r['v2_path_ids'][0]; req(pid not in recs,'duplicate A1 record'); recs[pid]=(d,r)
    aids=sorted(recs); req(len(aids)==122,'A1 record cardinality'); req(set(aids).isdisjoint(gids),'A1/G overlap')
    scenarios=load(out/'WS33_SCENARIO_TEMPLATE_REGISTRY.json'); sc_by={i:t for t in scenarios['templates'] for i in t['path_ids']}
    for pid,(d,r) in recs.items():
        p=mp[pid]; req(cb[pid]['status']=='UNKNOWN','A1 non-UNKNOWN '+pid); req(p['owner_family']=='ACTION_COST_DECISION' and p['implementation_target']=='forge.game.spellability.TargetRestrictions','A1 wrong path '+pid); req(sc_by[pid]['template_id'] in {'ws33-g2-template-123','ws33-g2e-template-123'},'A1 wrong predecessor scenario '+pid)
        ex=r['execution']; req(ex['actual_card_execution']=='PASS' and ex['actual_rules_core_path'] is True and ex['silent_fallbacks']==0 and ex['direct_effect_resolution'] is False,'A1 execution '+pid)
        decision=load(d/'decision-tape.json'); req(decision.get('events'),'A1 empty tape '+pid)
        for event in decision['events']:
            legal={o['option_id'] for o in event['authoritative_legal_options']}; req(event['validation_result']=='ACCEPTED' and not event.get('fallback_used',False) and set(event['response_option_ids'])<=legal,'A1 decision '+pid)
        replay=load(d/'semantic-replay.json'); req(replay['semantic_divergence']==0 and replay['comparison_basis']=='CANONICAL_SEMANTIC_STATE','A1 replay '+pid)
    ev=out/'promotion-evidence'/'abc-a1'/'run-33999460235'; ev.mkdir(parents=True,exist_ok=True)
    for name in ['ABC_A1_GATE.json','ABC_A1_PLAN.json','ABC_A1_HASHES.sha256','campaign-index.json','target-record-diagnostics.jsonl','target-replay-diagnostics.jsonl']:
        if (a1/name).is_file(): shutil.copy2(a1/name,ev/name)
    shutil.copytree(a1/'records',ev/'records')
    cases=load_jsonl(out/'WS33_CASE_LEDGER.jsonl'); cby={r['effective_v2_path_id']:r for r in cases}; exes=load_jsonl(out/'WS33_EXECUTION_LEDGER.jsonl'); eby={r['effective_v2_path_id']:r for r in exes}
    promotion_ref='WS33_POST_G3_A1_PROMOTION_EVIDENCE.json'
    for pid in gids:
        cb[pid].update({'status':'PASS','evidence_classification':'TECHNICALLY_CONFORMANT','execution_source':'G3_COMPLETE_CROSS_QUALIFICATION','state_evidence':True,'promotion_evidence':promotion_ref})
        cby[pid]['scenario_status']='G3_COMPLETE_CROSS_QUALIFICATION'; eby[pid].update({'status':'PASS','execution_source':'G3_COMPLETE_CROSS_QUALIFICATION','blocker_class':None,'promotion_evidence':promotion_ref})
    for pid,(d,r) in recs.items():
        relbase=f'promotion-evidence/abc-a1/run-33999460235/records/{d.name}'
        cb[pid].update({'status':'PASS','evidence_classification':r['evidence_class'],'execution_source':'WS33_ABC_A1_CERTIFIED_ARTIFACT','state_evidence':True,'decision_tape':relbase+'/decision-tape.json','replay_evidence':relbase+'/semantic-replay.json','trace_sha':sha(d/'trace.json'),'rules_refs':r['rules_authority_refs'],'promotion_evidence':promotion_ref})
        cby[pid]['scenario_status']='WS33_ABC_A1_CERTIFIED_ARTIFACT'; eby[pid].update({'status':'PASS','execution_source':'WS33_ABC_A1_CERTIFIED_ARTIFACT','trace_sha':sha(d/'trace.json'),'blocker_class':None,'promotion_evidence':promotion_ref})
    covdoc['paths']=[cb[i] for i in sorted(cb)]; write(out/'WS33_PATH_COVERAGE.json',covdoc); write_jsonl(out/'WS33_CASE_LEDGER.jsonl',[cby[i] for i in sorted(cby)]); write_jsonl(out/'WS33_EXECUTION_LEDGER.jsonl',[eby[i] for i in sorted(eby)])
    promotion={'schema':'commander-simulator-next.ws33-post-g3-a1-promotion.v1','status':'PASS','source_head':a.source_head,'source_tree':a.source_tree,'forge_pin':FORGE_PIN,'manifest_sha256':MANIFEST_SHA,'consumer_model_sha256':CONSUMER_SHA,'predecessor_counts':{k:before.get(k,0) for k in STATUS_KEYS},'g3':{'classification':'TECHNICALLY_CONFORMANT','checkpoint':'checkpoints/G3_COMPLETE_CROSS_QUALIFICATION_20260905.md','path_count':81,'effective_path_ids':gids,'constituent_artifacts':[9866293827,9803814288,9818304005,9900656730,9901008043,9901438964,9958136895,9957712911,9957878386,9958147261]},'a1':{'classification':'EXTERNALLY_RULE_VALIDATED','artifact_id':A1_ARTIFACT_ID,'artifact_digest':A1_ARTIFACT_DIGEST,'source_head':A1_SOURCE_HEAD,'path_count':122,'effective_path_ids':aids,'internal_hash_entries':hash_entries},'promoted_path_count':203,'unrelated_path_changes':0,'previous_pass_regressions':0,'duplicate_effective_identity':False,'coverage_mutated_during_witness':False}
    write(out/promotion_ref,promotion)
    after=recompute_derived(out); req(after==Counter({'UNKNOWN':3700,'PASS':488}),'successor counts')
    expected_promoted=set(gids)|set(aids); transitions={i:(before_status[i],cb[i]['status']) for i in cb if before_status[i]!=cb[i]['status']}; req(set(transitions)==expected_promoted,'unrelated status transition'); req(all(v==('UNKNOWN','PASS') for v in transitions.values()),'non UNKNOWN->PASS transition'); req(all(cb[i]['status']=='PASS' for i in gids+aids),'promotion missing')
    def shard(p):
        owner=p['owner_family']; target=p['implementation_target']
        if owner=='ACTION_COST_DECISION':
            if target=='forge.game.spellability.TargetRestrictions': return 'WS33A'
            if target in {'forge.game.cost.Cost','forge.game.ability.AbilityUtils#calculateAmount'}: return 'WS33B'
            if target in {'forge.game.spellability.AbilitySub','forge.game.spellability.SpellApiBased','forge.game.spellability.AbilityApiBased'}: return 'WS33C'
            return 'WS33D'
        return {'TRIGGER_REPLACEMENT_ZONE_SBA':'WS33E','CONTINUOUS_COPY_CONTROL':'WS33F','HIDDEN_RNG_REPLAY':'WS33G','COMBAT_COMMANDER':'WS33H'}[owner]
    unknown=Counter(shard(mp[i]) for i,r in cb.items() if r['status']=='UNKNOWN'); expected={'WS33A':57,'WS33B':675,'WS33C':700,'WS33D':920,'WS33E':1029,'WS33F':319,'WS33G':0,'WS33H':0}; req({k:unknown.get(k,0) for k in expected}==expected,'shard frontier')
    promotion['successor_counts']={k:after.get(k,0) for k in STATUS_KEYS}; promotion['unknown_by_shard']=expected; write(out/promotion_ref,promotion)
    hp=out/'WS33_HASHES.sha256'; hp.unlink(missing_ok=True); files=sorted(p for p in out.rglob('*') if p.is_file() and p.name!='WS33_HASHES.sha256' and '__pycache__' not in p.parts); hp.write_text(''.join(f'{sha(p)}  {p.relative_to(out).as_posix()}\n' for p in files),encoding='utf-8')
    print(json.dumps({'WS33_G3_A1_SUCCESSOR':'PASS','pass':488,'unknown':3700,'g_promoted':81,'a1_promoted':122,'a_unknown':57,'hash_entries':len(files)},sort_keys=True))
if __name__=='__main__': main()
