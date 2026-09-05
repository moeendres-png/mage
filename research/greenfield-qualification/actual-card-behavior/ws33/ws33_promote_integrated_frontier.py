#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from collections import Counter,defaultdict
from pathlib import Path
SHARDS=('WS33A','WS33B','WS33C','WS33D','WS33E','WS33F','WS33G','WS33H')
def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def loadl(p): return [json.loads(x) for x in Path(p).read_text(encoding='utf-8').splitlines() if x.strip()]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x): Path(p).parent.mkdir(parents=True,exist_ok=True); Path(p).write_text(json.dumps(x,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def writel(p,rows): Path(p).write_text(''.join(json.dumps(x,sort_keys=True,separators=(',',':'))+'\n' for x in rows),encoding='utf-8')
def req(c,m):
    if not c: raise SystemExit('WS33_PROMOTED_FRONTIER=FAIL '+m)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--ledger',type=Path,required=True); ap.add_argument('--queue',type=Path,required=True); ap.add_argument('--gate',type=Path,required=True); ap.add_argument('--promotion-index',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--a1-scenario-id',default='ws33-g2-template-123'); a=ap.parse_args()
    rows=loadl(a.ledger); queue=load(a.queue); oldgate=load(a.gate); promotion=load(a.promotion_index); req(len(rows)==4188,'ledger count')
    byid={r['effective_path_id']:r for r in rows}; req(len(byid)==4188,'duplicate ledger identity'); before=Counter(r['current_status'] for r in rows); req(before==Counter({'UNKNOWN':3903,'PASS':285}),'old ledger counts')
    aids=set(promotion['a1']['effective_path_ids']); gids=set(promotion['g3']['effective_path_ids']); targets=aids|gids; req(len(aids)==122 and len(gids)==81 and aids.isdisjoint(gids),'promotion sets')
    aitems=[x for x in queue['items'] if x.get('logical_bucket')=='WS33A' and x.get('runtime_subsystem')=='forge.game.spellability.TargetRestrictions' and x.get('scenario_group_id')==a.a1_scenario_id and x.get('evidence_profile')=='DECISION+REPLAY']
    req(len(aitems)==1 and set(aitems[0]['effective_path_ids'])==aids and aitems[0]['unresolved_path_count']==122,'canonical A1 queue mismatch')
    queue_g={i for x in queue['items'] if x.get('logical_bucket')=='WS33G' for i in x['effective_path_ids']}; req(queue_g==gids,'canonical G queue mismatch')
    for pid in targets:
        req(byid[pid]['current_status']=='UNKNOWN','promoted ledger path not unknown '+pid); byid[pid]['current_status']='PASS'; byid[pid]['blocker_classification']=None; byid[pid]['campaign_id']='G3_COMPLETE_CROSS_QUALIFICATION' if pid in gids else 'WS33_ABC_A1_CERTIFIED_ARTIFACT'; byid[pid]['promotion_evidence']='WS33_POST_G3_A1_PROMOTION_EVIDENCE.json'
    outrows=[byid[i] for i in sorted(byid)]; after=Counter(r['current_status'] for r in outrows); req(after==Counter({'UNKNOWN':3700,'PASS':488}),'new ledger counts')
    groups=defaultdict(list)
    for row in outrows:
        if row['current_status']=='PASS': continue
        key=(row['logical_bucket'],row['owner_family'],row['runtime_subsystem'],row['scenario_group_id'],row['evidence_profile']); groups[key].append(row['effective_path_id'])
    items=[]
    for (bucket,owner,subsystem,scenario,profile),ids in groups.items():
        items.append({'logical_bucket':bucket,'owner_family':owner,'runtime_subsystem':subsystem,'scenario_group_id':scenario,'evidence_profile':profile,'unresolved_path_count':len(ids),'effective_path_ids':sorted(ids),'priority_basis':'DESCENDING_UNRESOLVED_PATH_COUNT_THEN_STABLE_KEYS'})
    items.sort(key=lambda r:(-r['unresolved_path_count'],r['logical_bucket'],r['runtime_subsystem'],r['scenario_group_id']))
    out=a.out; out.mkdir(parents=True,exist_ok=True); ledger_path=out/'WS33_INTEGRATED_CLOSURE_LEDGER.jsonl'; queue_path=out/'WS33_INTEGRATED_WORK_QUEUE.json'; writel(ledger_path,outrows); write(queue_path,{'schema':'commander-simulator-next.ws33-integrated-work-queue.v1','basis':'effective_path_id','unresolved_path_count':3700,'work_item_count':len(items),'items':items})
    unknown=Counter(r['logical_bucket'] for r in outrows if r['current_status']=='UNKNOWN'); expected={'WS33A':57,'WS33B':675,'WS33C':700,'WS33D':920,'WS33E':1029,'WS33F':319,'WS33G':0,'WS33H':0}; req({k:unknown.get(k,0) for k in SHARDS}==expected,'unknown shards')
    gate=dict(oldgate); gate.update({'path_status_counts':{'PASS':488,'FAIL':0,'UNSUPPORTED':0,'UNKNOWN':3700},'unresolved_path_count':3700,'work_item_count':len(items),'ledger_sha256':sha(ledger_path),'queue_sha256':sha(queue_path),'status':'PASS','GLOBAL_Q6_PASS':False,'WS34_ELIGIBLE':False,'ARCHITECTURE_FREEZE_ELIGIBLE':False,'promotion_evidence_sha256':sha(a.promotion_index)})
    write(out/'WS33_INTEGRATED_FRONTIER_GATE.json',gate)
    unresolved={pid for item in items for pid in item['effective_path_ids']}; req(not (unresolved & targets),'promoted IDs remain queued'); req(len(unresolved)==3700,'queue union')
    print(json.dumps({'WS33_PROMOTED_FRONTIER':'PASS','pass':488,'unknown':3700,'work_items':len(items),'a_unknown':57},sort_keys=True))
if __name__=='__main__': main()
