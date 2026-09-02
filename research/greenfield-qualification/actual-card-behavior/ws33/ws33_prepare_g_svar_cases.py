#!/usr/bin/env python3
"""Derive the exact post-Direct-G SVar consumer topology from frozen WS33 inputs.

Source parsing here is provenance/case preparation only. Runtime behavior remains Forge-owned.
"""
from __future__ import annotations
import argparse, base64, json, re
from pathlib import Path

G='HIDDEN_RNG_REPLAY'
ABILITY_PREFIX=('AB$','SP$','DB$')
REF_RE_TEMPLATE=r'(?:^|\s\|\s)([A-Za-z][A-Za-z0-9_]*)\$\s*{name}(?=\s*(?:\||$))'

def fail(msg): raise SystemExit('WS33_G_SVAR_CASES=FAIL '+msg)
def read_json(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def extract_script(line,directive):
    if directive=='SVAR':
        parts=line.split(':',2)
        if len(parts)!=3 or parts[0] != 'SVar': fail('malformed SVar source line')
        return parts[2].strip(),parts[1].strip()
    if directive=='ABILITY':
        if ':' not in line: fail('malformed ability source line')
        return line.split(':',1)[1].strip(),None
    fail('unsupported source directive '+directive)
def card_name(lines):
    for x in lines:
        if x.startswith('Name:'): return x.split(':',1)[1].strip()
    fail('card name missing')
def parent_candidates(lines,target_name,target_line):
    rx=re.compile(REF_RE_TEMPLATE.format(name=re.escape(target_name)))
    out=[]
    for i,line in enumerate(lines,1):
        if i==target_line: continue
        m=rx.search(line)
        if not m: continue
        if line.startswith('SVar:'):
            parts=line.split(':',2); script=parts[2].strip(); directive='SVAR'; parent_token=parts[1].strip()
        elif ':' in line and line[0] in 'ATRS':
            script=line.split(':',1)[1].strip(); directive={'A':'ABILITY','T':'TRIGGER','R':'REPLACEMENT','S':'STATIC'}[line[0]]; parent_token=None
        else:
            continue
        out.append({'source_line':i,'directive':directive,'parent_svar':parent_token,'consumer_field':m.group(1),'script':script,'ability_factory_compatible':script.startswith(ABILITY_PREFIX)})
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--model-dir',type=Path,required=True); ap.add_argument('--forge-root',type=Path,required=True); ap.add_argument('--direct-ids',type=Path,required=True); ap.add_argument('--out-json',type=Path,required=True); ap.add_argument('--out-tsv',type=Path,required=True); a=ap.parse_args()
    man=read_json(a.model_dir/'WS33_EFFECTIVE_BEHAVIOR_PATH_MANIFEST.json'); cov=read_json(a.model_dir/'WS33_PATH_COVERAGE.json')
    by={x['v2_path_id']:x for x in man['paths']}; g=[x['effective_v2_path_id'] for x in cov['paths'] if x['owner_family']==G and x['status']=='UNKNOWN']
    direct={x.strip() for x in a.direct_ids.read_text().splitlines() if x.strip()}; rem=sorted(set(g)-direct)
    if len(g)!=81 or len(direct)!=28 or len(rem)!=53 or not direct.issubset(set(g)): fail(f'frontier mismatch g={len(g)} direct={len(direct)} remaining={len(rem)}')
    rows=[]; shapes={}
    for ordinal,pid in enumerate(rem,1):
        p=by[pid]; prov=p['source_provenance'][0]; src=a.forge_root/prov['forge_source_path']; ls=src.read_text(encoding='utf-8').splitlines(); ln=int(prov['source_line'])
        if not (1<=ln<=len(ls)): fail(pid+' source line out of range')
        target_script,target_name=extract_script(ls[ln-1],prov['source_directive'])
        if prov['source_directive']!='SVAR' or not target_name: fail(pid+' expected SVar target')
        cands=parent_candidates(ls,target_name,ln)
        if not cands: fail(pid+f' no source-proven parent references SVar {target_name}')
        compatible=[c for c in cands if c['ability_factory_compatible']]
        chosen=compatible[0] if len(compatible)==1 else cands[0] if len(cands)==1 else None
        row={'ordinal':ordinal,'v2_path_id':pid,'oracle_identity':prov['oracle_identity'],'card_name':card_name(ls),'implementation_target':p['implementation_target'],'dispatch_token':p['dispatch_token'],'source_path':prov['forge_source_path'],'source_line':ln,'target_svar':target_name,'target_script':target_script,'parent_candidates':cands,'selected_parent':chosen,'required_hidden_info_evidence':p['required_hidden_info_evidence'],'required_rng_evidence':p['required_rng_evidence'],'required_replay_evidence':p['required_replay_evidence'],'required_decision_evidence':p['required_decision_evidence']}
        rows.append(row)
        key='AMBIGUOUS' if chosen is None else f"{chosen['directive']}:{chosen['consumer_field']}:{'AF' if chosen['ability_factory_compatible'] else 'NON_AF'}"
        shapes[key]=shapes.get(key,0)+1
    unresolved=[r['v2_path_id'] for r in rows if r['selected_parent'] is None]
    out={'schema':'commander-simulator-next.ws33-g-svar-consumer-topology.v1','status':'PASS' if not unresolved else 'PARTIAL','effective_model_sha256':man['consumer_model_sha256'],'g_unknown_count':len(g),'direct_g_count':len(direct),'remaining_svar_count':len(rem),'consumer_shapes':dict(sorted(shapes.items())),'unresolved_parent_paths':unresolved,'cases':rows}
    a.out_json.parent.mkdir(parents=True,exist_ok=True); a.out_json.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    with a.out_tsv.open('w',encoding='utf-8') as f:
        for r in rows:
            c=r['selected_parent']; vals=[str(r['ordinal']),r['v2_path_id'],r['oracle_identity'],r['card_name'],r['implementation_target'],r['dispatch_token'],r['source_path'],str(r['source_line']),r['target_svar'],base64.b64encode(r['target_script'].encode()).decode(),'' if c is None else c['directive'],'' if c is None else c['consumer_field'],'' if c is None else str(c['source_line']),'' if c is None else base64.b64encode(c['script'].encode()).decode(),'1' if r['required_hidden_info_evidence'] else '0','1' if r['required_rng_evidence'] else '0','1' if r['required_replay_evidence'] else '0','1' if r['required_decision_evidence'] else '0']; f.write('\t'.join(vals)+'\n')
    print('WS33_G_SVAR_CASES='+out['status'],json.dumps({'remaining':53,'shapes':out['consumer_shapes'],'unresolved':len(unresolved)},sort_keys=True))
    if unresolved: raise SystemExit(2)
if __name__=='__main__': main()
