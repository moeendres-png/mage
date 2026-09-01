#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
from collections import Counter, defaultdict
from pathlib import Path

FIELDS = {
    'decision':'required_decision_evidence',
    'rng':'required_rng_evidence',
    'hidden':'required_hidden_info_evidence',
    'replay':'required_replay_evidence',
}
SHARDS=('WS33A','WS33B','WS33C','WS33D','WS33E','WS33F','WS33G','WS33H')

def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def load_jsonl(p): return [json.loads(x) for x in Path(p).read_text(encoding='utf-8').splitlines() if x.strip()]
def write(p,v):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\n',encoding='utf-8')
def write_jsonl(p,rows):
    Path(p).write_text(''.join(json.dumps(r,sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def req(c,m):
    if not c: raise SystemExit('WS33_G_REQUIREMENT_ERRATA=FAIL '+m)
def profile(p):
    return '+'.join(n.upper() for n,k in FIELDS.items() if p.get(k)) or 'STATE_ONLY'
def shard_for(p):
    o,t=p['owner_family'],p['implementation_target']
    if o=='ACTION_COST_DECISION':
        if t=='forge.game.spellability.TargetRestrictions': return 'WS33A'
        if t in {'forge.game.cost.Cost','forge.game.ability.AbilityUtils#calculateAmount'}: return 'WS33B'
        if t in {'forge.game.spellability.AbilitySub','forge.game.spellability.SpellApiBased','forge.game.spellability.AbilityApiBased'}: return 'WS33C'
        return 'WS33D'
    return {'TRIGGER_REPLACEMENT_ZONE_SBA':'WS33E','CONTINUOUS_COPY_CONTROL':'WS33F','HIDDEN_RNG_REPLAY':'WS33G','COMBAT_COMMANDER':'WS33H'}[o]
def regen_hashes(root):
    hp=root/'WS33_HASHES.sha256'
    if hp.exists(): hp.unlink()
    files=sorted(p for p in root.rglob('*') if p.is_file() and p.name!='WS33_HASHES.sha256' and '__pycache__' not in p.parts)
    hp.write_text(''.join(f'{sha(p)}  {p.relative_to(root).as_posix()}\n' for p in files),encoding='utf-8')

def rebuild_indexes(root, paths, coverage, witnesses):
    bypath={}
    for w in witnesses:
        if w.get('status')!='PASS': continue
        for pid in w.get('v2_path_ids',[]):
            req(pid not in bypath,'duplicate PASS witness '+pid); bypath[pid]=w
    specs=(('decision','decision_tape_ref','WS33_DECISION_EVIDENCE_INDEX.json'),('rng','rng_tape_ref','WS33_RNG_EVIDENCE_INDEX.json'),('hidden','observation_evidence_ref','WS33_HIDDEN_INFO_EVIDENCE_INDEX.json'),('replay','semantic_replay_evidence_ref','WS33_REPLAY_EVIDENCE_INDEX.json'))
    for dim,ref,fn in specs:
        key=FIELDS[dim]
        required=sorted(pid for pid,p in paths.items() if p.get(key))
        entries=[]
        for pid in required:
            if coverage[pid]['status']!='PASS': continue
            w=bypath.get(pid); req(w is not None,'duplicate PASS lacks witness '+pid)
            r=w.get(ref); req(bool(r),'PASS lacks '+dim+' evidence '+pid); req((root/r).is_file(),'missing evidence '+r)
            entries.append({'effective_v2_path_id':pid,'witness_id':w['witness_id'],'evidence_ref':r,'trace_sha256':w['trace_sha256']})
        complete={x['effective_v2_path_id'] for x in entries}
        write(root/fn,{'schema':f'commander-simulator-next.ws33-{dim}-evidence-index.v2','ws33_parallel_base_generation':2,'required_path_ids':required,'required_count':len(required),'complete_pass_count':len(complete),'missing_count':len(set(required)-complete),'entries':entries})

def rebuild_templates_and_partition(root, paths, coverage):
    pass_ids={pid for pid,r in coverage.items() if r['status']=='PASS'}
    groups=defaultdict(list)
    for pid,p in paths.items(): groups[(p['owner_family'],p['implementation_target'],profile(p))].append(pid)
    templates=[]
    for i,(key,ids) in enumerate(sorted(groups.items()),1):
        owner,target,prof=key; ids=sorted(ids); adm=sorted(set(ids)&pass_ids); rem=sorted(set(ids)-pass_ids)
        templates.append({'template_id':f'ws33-g2e-template-{i:03d}','owner_family':owner,'implementation_target':target,'evidence_profile':prof,'path_ids':ids,'status':'FULLY_EXECUTED' if not rem else ('PARTIALLY_EXECUTED' if adm else 'MISSING_SCENARIO_TEMPLATE'),'admitted_path_ids':adm,'remaining_path_ids':rem})
    write(root/'WS33_SCENARIO_TEMPLATE_REGISTRY.json',{'schema':'commander-simulator-next.ws33-scenario-template-registry.v2','ws33_parallel_base_generation':2,'evidence_requirement_errata_generation':1,'templates':templates})
    casep=root/'WS33_CASE_LEDGER.jsonl'; cases=load_jsonl(casep); cb={r['effective_v2_path_id']:r for r in cases}
    for pid in paths: cb[pid]['evidence_profile']=profile(paths[pid])
    write_jsonl(casep,[cb[x] for x in sorted(cb)])
    unknown={pid for pid,r in coverage.items() if r['status']=='UNKNOWN'}
    shards={s:[] for s in SHARDS}
    for pid in sorted(unknown): shards[shard_for(paths[pid])].append(pid)
    template_shards={}; splits=[]
    for t in templates:
        rem=set(t['remaining_path_ids']); owners=sorted({s for s,ids in shards.items() if rem & set(ids)})
        if rem: template_shards[t['template_id']]=owners
        if len(owners)>1: splits.append({'template_id':t['template_id'],'shards':owners})
    pair=[]
    for i,l in enumerate(SHARDS):
        for r in SHARDS[i+1:]:
            inter=sorted(set(shards[l])&set(shards[r])); pair.append({'left':l,'right':r,'intersection_count':len(inter),'intersection':inter})
    union=set().union(*(set(x) for x in shards.values()))
    predicates={'WS33A':'ACTION_COST_DECISION + TargetRestrictions','WS33B':'ACTION_COST_DECISION + Cost or AbilityUtils#calculateAmount','WS33C':'ACTION_COST_DECISION + AbilitySub/SpellApiBased/AbilityApiBased','WS33D':'remaining ACTION_COST_DECISION','WS33E':'TRIGGER_REPLACEMENT_ZONE_SBA','WS33F':'CONTINUOUS_COPY_CONTROL','WS33G':'HIDDEN_RNG_REPLAY','WS33H':'COMBAT_COMMANDER'}
    part={'schema':'commander-simulator-next.ws33-parallel-rest-partition.v2','ws33_parallel_base_generation':2,'evidence_requirement_errata_generation':1,'basis':'effective_v2_path_id','effective_path_count':len(paths),'pass_count':len(pass_ids),'unknown_count':len(unknown),'scenario_group_count':len(templates),'incomplete_scenario_group_count':sum(t['status']!='FULLY_EXECUTED' for t in templates),'shards':{}}
    for s in SHARDS:
        groups_ids=sorted(tid for tid,owners in template_shards.items() if owners==[s])
        part['shards'][s]={'predicate':predicates[s],'path_count':len(shards[s]),'scenario_group_count':len(groups_ids),'effective_v2_path_ids':shards[s],'scenario_group_ids':groups_ids}
    write(root/'WS33_PARALLEL_REST_PARTITION.json',part)
    legacy=set(load(root/'WS33_MODEL_ERRATA.json').get('legacy_ws29_alias_ids',[]))
    inv={'schema':'commander-simulator-next.ws33-parallel-partition-invariants.v2','ws33_parallel_base_generation':2,'evidence_requirement_errata_generation':1,'basis':'effective_v2_path_id','pairwise_intersections':pair,'pairwise_intersection_count':sum(x['intersection_count'] for x in pair),'unknown_union_count':len(union),'authoritative_unknown_count':len(unknown),'missing_unknown_ids':sorted(unknown-union),'extra_partition_ids':sorted(union-unknown),'pass_overlap':sorted(pass_ids&union),'scenario_group_split_count':len(splits),'scenario_group_splits':splits,'legacy_ws29_alias_overlap':sorted(legacy&union),'every_remaining_path_exactly_one_shard':union==unknown and not any(x['intersection_count'] for x in pair),'PARTITION_DISJOINT':not any(x['intersection_count'] for x in pair),'PARTITION_COMPLETE':union==unknown and not splits and not(pass_ids&union) and not(legacy&union)}
    write(root/'WS33_PARALLEL_PARTITION_INVARIANTS.json',inv)
    req(inv['PARTITION_DISJOINT'] and inv['PARTITION_COMPLETE'],'partition rebuild failed')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,required=True); ap.add_argument('--projection',type=Path,required=True); ap.add_argument('--source-head',required=True); ap.add_argument('--source-tree',required=True); a=ap.parse_args()
    root=a.root.resolve(); mp=root/'WS33_EFFECTIVE_BEHAVIOR_PATH_MANIFEST.json'; oldsha=sha(mp); manifest=load(mp); projection=load(a.projection)
    req(projection.get('schema')=='commander-simulator-next.ws33-requirement-projection-audit.v4','wrong projection schema')
    req(projection.get('status')=='PASS','projection not PASS'); req(projection.get('forge_pin')==manifest.get('forge_pin'),'Forge pin mismatch')
    req(projection.get('manifest_sha256')==oldsha,'projection not bound to input manifest')
    req(projection.get('authoritative_projection_scope')=='HIDDEN_RNG_REPLAY','wrong projection scope')
    req(projection.get('authoritative_projection_scope_path_count')==81,'expected 81 G paths'); req(projection.get('candidate_row_count')==60,'expected 60 corrections')
    req(projection.get('changed_unknown_path_count')==60 and projection.get('pass_upgrade_candidate_count')==0,'projection touches PASS or wrong frontier')
    covdoc=load(root/'WS33_PATH_COVERAGE.json'); coverage={r['effective_v2_path_id']:r for r in covdoc['paths']}; paths={p['v2_path_id']:p for p in manifest['paths']}
    req(Counter(r['status'] for r in coverage.values())==Counter({'UNKNOWN':3903,'PASS':285}),'input is not H-complete 285/3903')
    g={pid for pid,p in paths.items() if p['owner_family']=='HIDDEN_RNG_REPLAY'}; req(len(g)==81,'G path count'); req(all(coverage[x]['status']=='UNKNOWN' for x in g),'G correction would touch PASS')
    corrections=[]
    for row in projection['candidates']:
        pid=row['effective_path_id']; req(pid in g,'candidate outside G '+pid); p=paths[pid]
        current={d:bool(p[k]) for d,k in FIELDS.items()}; req(current==row['current'],'projection current mismatch '+pid); req(coverage[pid]['status']=='UNKNOWN','candidate is not UNKNOWN '+pid)
        for d,k in FIELDS.items(): p[k]=bool(row['projected'][d])
        corrections.append({'effective_v2_path_id':pid,'implementation_target':p['implementation_target'],'current':row['current'],'projected':row['projected'],'classification':row['classification'],'basis':row['basis'],'projection_reasons':row['projection_reasons'],'forge_source_path':row['forge_source_path'],'forge_source_sha256':row['forge_source_sha256'],'verified_source_anchors':row['verified_source_anchors']})
    req(len(corrections)==60,'correction count')
    manifest['evidence_requirement_errata']={'generation':1,'scope':'HIDDEN_RNG_REPLAY','source_head':a.source_head,'source_tree':a.source_tree,'projection_artifact_manifest_sha256':oldsha,'corrected_path_count':60,'historical_artifacts_mutated':False}
    write(mp,manifest); newsha=sha(mp); req(newsha!=oldsha,'model digest did not change')
    wp=root/'WS33_WITNESSES.jsonl'; witnesses=load_jsonl(wp); req(len({pid for w in witnesses for pid in w['v2_path_ids']})==285,'expected 285 PASS paths before errata')
    for w in witnesses: w['effective_model_sha256']=newsha
    write_jsonl(wp,witnesses)
    abip=root/'abi/WS33_WITNESS_ABI_GATE.json'; abi=load(abip); validator=root/'abi/WS33_WITNESS_SEMANTIC_VALIDATOR.py'; schema=root/'abi/WS33_WITNESS_ABI_V2_1.schema.json'; provenance=root/'abi/WS33_SUCCESSOR_PROVENANCE.json'
    spec=importlib.util.spec_from_file_location('ws33_validator',validator); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    schema_doc=load(schema); provenance_doc=load(provenance); manifest_doc=load(mp)
    results=[]
    for old in abi['results']:
        fp=root/old['fixture']; w=load(fp)
        if old['expected_exit']==0 or old.get('expected_error')!='UNDECLARED_MODEL_MUTATION': w['effective_model_sha256']=newsha
        else: w['effective_model_sha256']='0'*64
        write(fp,w)
        try:
            mod.validate(w,manifest_doc,root,schema_doc,provenance_doc); actual_exit=0; stdout='WS33_WITNESS_VALIDATION=PASS'; code=None
        except mod.WitnessError as exc:
            actual_exit=2; code=exc.code; stdout=f'WS33_WITNESS_VALIDATION=FAIL code={exc.code} message={exc}'
        intended=actual_exit==old['expected_exit'] and (old.get('expected_error') is None or code==old['expected_error'])
        results.append({**old,'actual_exit':actual_exit,'stdout':stdout,'intended_result':intended})
    req(all(r['intended_result'] for r in results),'ABI revalidation failed')
    abi['results']=results; abi['WS33_WITNESS_ABI_V2_1_GATE']='PASS'; abi['negative_fixtures_rejected_for_intended_reason']=True; abi['campaign_positives_accepted']=True; abi['evidence_requirement_errata_generation']=1
    write(abip,abi)
    rebuild_indexes(root,paths,coverage,witnesses); rebuild_templates_and_partition(root,paths,coverage)
    errp=root/'WS33_MODEL_ERRATA.json'; err=load(errp); err['schema']='commander-simulator-next.ws33-model-errata.v3'; err['evidence_requirement_errata']={'generation':1,'scope':'HIDDEN_RNG_REPLAY','input_effective_model_sha256':oldsha,'successor_effective_model_sha256':newsha,'projection_sha256':sha(a.projection),'corrected_path_count':60,'upgrade_candidate_counts':projection['upgrade_candidate_counts'],'removal_candidate_counts':projection['removal_candidate_counts'],'pass_paths_changed':0,'historical_artifacts_mutated':False,'corrections':corrections}; write(errp,err)
    gatep=root/'WS33_MODEL_GATE.json'; gate=load(gatep); gate['evidence_requirement_errata_generation']=1; gate['evidence_requirement_corrected_path_count']=60; gate['evidence_requirement_pass_paths_changed']=0; gate['effective_model_sha256']=newsha; gate['WS33_MODEL_ERRATA_GATE']='PASS'; write(gatep,gate)
    migp=root/'WS33_MODEL_MIGRATION.json'; mig=load(migp); mig['evidence_requirement_errata']={'generation':1,'scope':'HIDDEN_RNG_REPLAY','corrected_path_count':60,'pass_paths_changed':0,'input_effective_model_sha256':oldsha,'successor_effective_model_sha256':newsha}; write(migp,mig)
    mergep=root/'WS33_CAMPAIGN_MERGE_GATE.json'; merge=load(mergep); merge['generation2_model_revalidated']=True; merge['generation2_effective_model_sha256']=newsha; merge['evidence_requirement_errata_generation']=1; write(mergep,merge)
    repairp=root/'WS33_PARALLEL_BASE_REPAIR_DIFF.json'; repair=load(repairp); repair['generation2_revalidated_pass_count']=285; repair['pass_revalidation_failures']=0; repair['evidence_requirement_errata_generation']=1; repair['evidence_requirement_pass_paths_changed']=[]; write(repairp,repair)
    q=root/'WS33_Q6_CANDIDATE_GATE.json'; qd=load(q); ts=Counter(t['status'] for t in load(root/'WS33_SCENARIO_TEMPLATE_REGISTRY.json')['templates']); qd['scenario_group_counts']={k:ts.get(k,0) for k in ('FULLY_EXECUTED','PARTIALLY_EXECUTED','MISSING_SCENARIO_TEMPLATE')}; qd['incomplete_scenario_group_count']=sum(v for k,v in ts.items() if k!='FULLY_EXECUTED'); qd['WS33_ACTUAL_CARD_CAMPAIGN']='FAIL_CLOSED'; qd['Q6_CANDIDATE_FOR_CROSS_QUALIFICATION']=False; qd['WS34_ELIGIBLE']=False; qd['WORKSTREAM_COMPLETE']=False; qd['evidence_requirement_errata_generation']=1; write(q,qd)
    regen_hashes(root)
    print(json.dumps({'WS33_G_REQUIREMENT_ERRATA':'PASS','input_model_sha256':oldsha,'successor_model_sha256':newsha,'corrected_paths':60,'revalidated_pass_paths':285,'abi_results':len(results),'unknown':3903},sort_keys=True))
if __name__=='__main__': main()
