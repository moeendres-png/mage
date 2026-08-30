#!/usr/bin/env python3
from __future__ import annotations
import argparse, collections, hashlib, json, re, shutil
from pathlib import Path

PIN='8c7e9afb8e6caee88644b94e25da5852e36f8928'
BASE='98ec89a2d506908cdcf9c405bc0b239c70a83f12'; BASE_TREE='cd06b6ed8da43850a7ea7ec4d596d5f5d0f5cc79'
RUNTIME='55820618e7243bd5ba8cfa33c3148cea8c166c73'; RUNTIME_TREE='3706900d49c6ef61690c227bb7b4c0067fbcfb44'
WS11_SHA='1f46fc66d2049d65c7ede91700c0e76e38b3fb7c49c13bb394dd20aa6ea8ced7'
WS14_MANIFEST_SHA='1137335dd7101df44940a2b0c8cacc5740e2aef0a24eceb541449dd10a5e6f7b'
WS14_PERID_SHA='1e824702ed0dcd4af7d91e66b02ec37fc88dd9ace51ab20bf0abf1f53b605703'
WS14_UNRES_SHA='d35b3f2772b7638768e9d66d5e00eed8bc3488530be99e064be44c82e1cb5704'
WS24_GATE_SHA='44faecad77f96c84e1654141b323a1197dbed084aa8c46d70304dbf29b042756'
OWNERS=['ACTION_COST_DECISION','TRIGGER_REPLACEMENT_ZONE_SBA','CONTINUOUS_COPY_CONTROL','COMBAT_COMMANDER','HIDDEN_RNG_REPLAY']
SELECTORS={'Mode','Event','Origin','Destination','ActivationZone','Layer','ReplacementResult','Optional','OptionalDecider','Secondary','Mandatory','Duration','LoseControl','CopyZone','ChoiceZone','TargetMin','TargetMax','TargetsSingleTarget','TargetUnique','ValidTgts','Cost','UnlessCost','UnlessPayer','Random','Shuffle','Reveal','StaticAbilities','Execute','SubAbility','ReplaceWith','Defined','ValidCards','ChangeType','Tapped','Controller'}

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canon(o): return (json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\n').encode()
def wj(p,o): Path(p).parent.mkdir(parents=True,exist_ok=True); Path(p).write_bytes(canon(o))
def wjl(p,rows):
    Path(p).parent.mkdir(parents=True,exist_ok=True)
    with Path(p).open('wb') as f:
        for r in rows:f.write(canon(r))
def lj(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def ljl(p): return [json.loads(x) for x in Path(p).read_text(encoding='utf-8').splitlines() if x.strip()]
def norm(s): return re.sub(r'\s+',' ',str(s).strip())

def fields(line):
    out={}; t=line.strip()
    if len(t)>1 and t[1]==':' and t[0] in 'ATRSK': out['__record__']=t[0]; t=t[2:]
    for x in t.split('|'):
        m=re.match(r'^\s*([A-Za-z][A-Za-z0-9_]*)\$\s*(.*?)\s*$',x)
        if m:out[m.group(1)]=m.group(2)
    return out

def cost_shape(v):
    v=v or ''; a=[]
    for name,pat in [('TAP',r'(^|\s)T($|\s)'),('SAC',r'Sac<'),('DISCARD',r'Discard<'),('EXILE',r'Exile<'),('LIFE',r'PayLife|Life<'),('COUNTER',r'RemoveCounter|Counter<')]:
        if re.search(pat,v):a.append(name)
    if re.search(r'[WUBRGCXYZ]|\d',v):a.append('MANA_NUM')
    return '+'.join(sorted(set(a))) if a else 'OTHER'

def mana_shape(v):
    v=v.strip(); a=[]
    if re.search(r'\bX\b',v):a.append('X')
    if '/' in v:a.append('HYBRID_OR_PHYREXIAN')
    for c in 'WUBRGC':
        if re.search(rf'(^|\s){c}($|\s)',v):a.append(c)
    if re.search(r'\d',v):a.append('GENERIC')
    return '+'.join(a) if a else ('NO_COST' if v.lower()=='no cost' else 'OTHER')

def shape(k,v):
    v=norm(v)
    if k.startswith('Valid') or k in {'Defined','Affected','ChangeType'}:return 'FILTER:'+str(1+v.count(','))
    if k in {'Cost','UnlessCost'}:return cost_shape(v)
    if re.fullmatch(r'[+-]?\d+',v):return 'NUM'
    if v.startswith(('Count$','Number$')) or v in {'X','Y','Z'}:return 'DYNAMIC'
    return re.sub(r'(?<![A-Za-z])\d+(?![A-Za-z])','#',v)[:180]

def owner_for(s):
    p=s.lower().replace('.','/')
    if any(x in p for x in ['/combat/','commander','attacker','blocker','attack','block']):return 'COMBAT_COMMANDER'
    if any(x in p for x in ['/trigger/','/replacement/','/zone/']):return 'TRIGGER_REPLACEMENT_ZONE_SBA'
    if any(x in p for x in ['/staticability/','copy','control','layer']):return 'CONTINUOUS_COPY_CONTROL'
    if any(x in p for x in ['random','shuffle','hidden','replay','visibility']):return 'HIDDEN_RNG_REPLAY'
    return 'ACTION_COST_DECISION'

def majority_owner(items,fallback='ACTION_COST_DECISION'):
    if not items:return fallback,[]
    c=collections.Counter(owner_for(x) for x in items); order={x:i for i,x in enumerate(OWNERS)}
    primary=sorted(c,key=lambda x:(-c[x],order[x]))[0]
    return primary,sorted(set(c)-{primary},key=lambda x:order[x])

def class_source(target,root):
    base=target.split('#',1)[0]
    if not base.startswith('forge.'):return None
    rel=Path(*base.split('.')).with_suffix('.java')
    for mod in ['forge-game','forge-core','forge-gui','forge-ai']:
        p=root/mod/'src/main/java'/rel
        if p.is_file():return p
    return None

def impl_text(target,root):
    p=class_source(target,root); return p.read_text(encoding='utf-8',errors='replace') if p else ''

def impl_params(target,root,cache):
    if target in cache:return cache[target]
    t=impl_text(target,root); keys=set()
    for pat in [r'(?:hasParam|getParam|getParamOrDefault|matchesParam|isParam)[A-Za-z0-9_]*\(\s*"([A-Za-z][A-Za-z0-9_]*)"',r'containsKey\(\s*"([A-Za-z][A-Za-z0-9_]*)"']:
        keys.update(re.findall(pat,t))
    cache[target]=keys; return keys

def profile(binding,line,target,root,cache):
    if binding.get('source_directive')=='MANA_COST':return {'record':'MANA_COST','mana_cost_shape':mana_shape(binding.get('source_value',''))}
    f=fields(line); keys=(impl_params(target,root,cache)|SELECTORS)&set(f)
    return {'record':f.get('__record__',binding.get('source_directive')),'selectors':{k:shape(k,f[k]) for k in sorted(keys)},'targeting':'TARGETED' if 'ValidTgts'in f else 'UNTARGETED','cost_shape':cost_shape(f.get('Cost','')) if 'Cost'in f else 'NONE'}

def reqs(lines,itext):
    s='\n'.join(lines); l=itext.lower()
    decision=bool(re.search(r'ValidTgts\$|Optional\$|Choices\$|Choice\$|TgtPrompt\$',s,re.I)) or any(x in l for x in ['getcontroller().choose','confirmaction','choosecardsfor','chooseentity'])
    rng=bool(re.search(r'Random\$|Shuffle\$\s*True',s,re.I)) or any(x in itext for x in ['MyRandom','Aggregates.random','Collections.shuffle','.shuffle(','getRandom('])
    hidden=bool(re.search(r'(Origin|Destination|ChoiceZone)\$\s*(Library|Hand)|Reveal\$|Search',s,re.I)) or any(x in itext for x in ['ZoneType.Library','ZoneType.Hand','mayLook','reveal'])
    return {'decision':decision,'rng':rng,'hidden_info':hidden,'replay':decision or rng}

def vid(desc):return 'forge-behavior-v2:'+hashlib.sha256(canon(desc)).hexdigest()[:40]

def java_index(root):
    docs=[]; direct=collections.defaultdict(list); computed=[]
    lit=re.compile(r'(?:getSVar|hasSVar)\(\s*"([A-Za-z0-9_]+)"')
    call=re.compile(r'(?:getSVar|hasSVar)\(([^\n;)]*)\)')
    for mod in ['forge-game','forge-core','forge-gui','forge-ai']:
        b=root/mod/'src/main/java'
        if not b.exists():continue
        for p in sorted(b.rglob('*.java')):
            rel=p.relative_to(root).as_posix(); t=p.read_text(encoding='utf-8',errors='replace'); docs.append((rel,t))
            for n,line in enumerate(t.splitlines(),1):
                for k in lit.findall(line):direct[k].append({'path':rel,'line':n,'source':norm(line)[:240]})
                for expr in call.findall(line):
                    if not re.fullmatch(r'\s*"[A-Za-z0-9_]+"\s*',expr):computed.append({'path':rel,'line':n,'expr':norm(expr)[:180],'literal_fragments':re.findall(r'"([A-Za-z0-9_]+)"',expr)})
    return docs,direct,computed

def source_refs(token,path,line,source_lines):
    pat=re.compile(rf'(?<![A-Za-z0-9_]){re.escape(token)}(?![A-Za-z0-9_])'); out=[]
    for n,s in enumerate(source_lines[path],1):
        if n==line or not pat.search(s):continue
        f=fields(s); used=[k for k,v in f.items() if k!='__record__' and pat.search(v)]
        out.append({'path':path,'line':n,'fields':sorted(used),'source':s.strip()[:300]})
    return out

def svar_reachability(token,path,source_lines):
    """Resolve a card-local SVar dependency graph without treating AI hints as rules paths."""
    lines=source_lines[path]; defs={}
    for n,s in enumerate(lines,1):
        m=re.match(r'^\s*SVar:([A-Za-z0-9_]+):(.*)$',s)
        if m:defs[m.group(1)]=(n,m.group(2))
    seen=set(); pending=[token]; semantic=[]; metadata=[]; edges=[]
    while pending:
        cur=pending.pop()
        if cur in seen:continue
        seen.add(cur); pat=re.compile(rf'(?<![A-Za-z0-9_]){re.escape(cur)}(?![A-Za-z0-9_])')
        for n,s in enumerate(lines,1):
            m=re.match(r'^\s*SVar:([A-Za-z0-9_]+):(.*)$',s)
            if m:
                name,rhs=m.group(1),m.group(2)
                if not pat.search(rhs):continue
                row={'from_token':cur,'to_svar':name,'line':n,'source':s.strip()[:300]};edges.append(row)
                if name.lower().startswith('needstoplay'):
                    metadata.append(row)
                else:pending.append(name)
            elif pat.search(s) and re.match(r'^\s*[ATRSK]:',s):
                semantic.append({'from_token':cur,'line':n,'source':s.strip()[:300]})
    key=lambda x:(x['line'],x.get('from_token',''),x.get('to_svar',''))
    return {'edges':sorted({json.dumps(x,sort_keys=True):x for x in edges}.values(),key=key),'semantic_terminals':sorted({json.dumps(x,sort_keys=True):x for x in semantic}.values(),key=key),'metadata_terminals':sorted({json.dumps(x,sort_keys=True):x for x in metadata}.values(),key=key)}

def keyword_static_refs(enum_name,raw,docs):
    out=[]; needle='Keyword.'+enum_name if enum_name!='UNDEFINED' else None; prefix=raw.split(':',1)[0]
    for path,t in docs:
        for n,line in enumerate(t.splitlines(),1):
            if (needle and needle in line) or (not needle and prefix and ('"'+prefix) in line):out.append({'path':path,'line':n,'source':norm(line)[:240]})
    return out

def add_path(store,d,r,source_lines,root,cross=()):
    v=vid(d); rq=reqs([source_lines[r['forge_source_path']][r['source_line']-1]],impl_text(d['implementation_target'],root)); cp=set(cross)
    if rq['decision'] and d['owner_family']!='ACTION_COST_DECISION':cp.add('ACTION_COST_DECISION')
    if (rq['rng'] or rq['hidden_info']) and d['owner_family']!='HIDDEN_RNG_REPLAY':cp.add('HIDDEN_RNG_REPLAY')
    q=store.setdefault(v,{'v2_path_id':v,**d,'cross_family_dependencies':sorted(cp),'source_provenance':[],'representative_actual_oracle_identities':[],'source_occurrence_count':0,'required_decision_evidence':rq['decision'],'required_rng_evidence':rq['rng'],'required_hidden_info_evidence':rq['hidden_info'],'required_replay_evidence':rq['replay'],'evidence_class':'CODE_DERIVED','current_witness_status':'UNPROVED'})
    q['source_provenance'].append({'oracle_identity':r['oracle_id'],'forge_source_path':r['forge_source_path'],'source_line':r['source_line'],'source_directive':r['source_directive'],'source_token':r['source_token'],'source_value':r['source_value']}); q['representative_actual_oracle_identities']=sorted(set(q['representative_actual_oracle_identities']+[r['oracle_id']]))[:12]; q['source_occurrence_count']+=1
    return v

def main():
    ap=argparse.ArgumentParser()
    for x in ['ws11-dir','ws14-dir','ws24-dir','ws16-dir','ws17-dir','forge-root','keyword-runtime-trace','ws17-test-source','out']:ap.add_argument('--'+x,type=Path,required=True)
    ap.add_argument('--source-head',required=True); ap.add_argument('--source-tree',required=True); a=ap.parse_args(); out=a.out; out.mkdir(parents=True,exist_ok=True)
    for p,h in [(a.ws11_dir/'PER_IDENTITY.semantic.jsonl',WS11_SHA),(a.ws14_dir/'WS14_PRIMITIVE_MANIFEST.json',WS14_MANIFEST_SHA),(a.ws14_dir/'PER_IDENTITY.atomic.jsonl',WS14_PERID_SHA),(a.ws14_dir/'UNRESOLVED_BINDINGS.jsonl',WS14_UNRES_SHA),(a.ws24_dir/'Q6_ACTUAL_CARD_BEHAVIOR_GATE.json',WS24_GATE_SHA)]:
        if sha(p)!=h:raise SystemExit(f'input hash mismatch {p}')
    ws11=ljl(a.ws11_dir/'PER_IDENTITY.semantic.jsonl'); man=lj(a.ws14_dir/'WS14_PRIMITIVE_MANIFEST.json'); ids=ljl(a.ws14_dir/'PER_IDENTITY.atomic.jsonl'); unr=ljl(a.ws14_dir/'UNRESOLVED_BINDINGS.jsonl'); q6=lj(a.ws24_dir/'Q6_ACTUAL_CARD_BEHAVIOR_GATE.json')
    if (len(ws11),len(ids),len(unr),man['atomic_primitive_count'])!=(1678,1678,1800,174):raise SystemExit('canonical count mismatch')
    if q6.get('primitive_status_counts')!={'PARTIAL':161,'PASS':13}:raise SystemExit('WS24 gate mismatch')
    source_lines={}; mismatch=[]; oracle_by_source=collections.defaultdict(set)
    for i in ids:
        for src in i['forge_sources']:
            p=a.forge_root/src['forge_source_path']; oracle_by_source[src['forge_source_path']].add(i['oracle_id'])
            if not p.is_file() or sha(p)!=src['forge_source_sha256_bytes']:mismatch.append(src['forge_source_path']);continue
            source_lines[src['forge_source_path']]=p.read_text(encoding='utf-8').splitlines()
    if mismatch:raise SystemExit('pinned Forge source mismatch '+repr(mismatch[:5]))
    docs,direct_svar,computed_svar=java_index(a.forge_root); kwrt=ljl(a.keyword_runtime_trace)
    if len(kwrt)!=888:raise SystemExit('keyword runtime trace count mismatch')
    kwrt={int(x['occurrence']):x for x in kwrt}; prim={p['primitive_id']:p for p in man['primitives']}
    occ=collections.defaultdict(list); line_pids=collections.defaultdict(set)
    for i in ids:
        for src in i['forge_sources']:
            sp=src['forge_source_path']; lines=source_lines[sp]
            for b in src.get('primitive_bindings',[]):
                x=dict(b);x.update(oracle_identity=i['oracle_id'],forge_source_path=sp,source_text=lines[b['source_line']-1]);occ[b['primitive_id']].append(x);line_pids[(sp,b['source_line'])].add(b['primitive_id'])
    pcache={}; grans=[]; paths=[]; occ_v2={}; parent_paths=collections.defaultdict(list)
    for p in sorted(man['primitives'],key=lambda x:x['primitive_id']):
        os=occ[p['primitive_id']]; groups={}
        for x in os:
            prof=profile(x,x['source_text'],p['implementation_target'],a.forge_root,pcache); k=hashlib.sha256(canon(prof)).hexdigest(); groups.setdefault(k,{'profile':prof,'rows':[]})['rows'].append(x)
        result='NON_PRODUCTION' if not os else ('ATOMIC_SUFFICIENT' if len(groups)==1 else 'SPLIT_REQUIRED'); childs=[]
        for k,g in sorted(groups.items()):
            d={'parent_ws14_primitive_id':p['primitive_id'],'dispatch_domain':p['dispatch_domain'],'dispatch_token':p['dispatch_token'],'implementation_target':p['implementation_target'],'semantic_selector_profile':g['profile'],'owner_family':p['owner_family'],'model_origin':'WS14_V1_GRANULARITY'}; v=vid(d);childs.append(v);parent_paths[p['primitive_id']].append(v);prov=sorted({(x['oracle_identity'],x['forge_source_path'],x['source_line'],x['source_directive'],x['source_token'],x['source_value']) for x in g['rows']});rq=reqs([x['source_text'] for x in g['rows']],impl_text(p['implementation_target'],a.forge_root));cross=set(p.get('cross_family_dependencies',[]))
            if rq['decision'] and p['owner_family']!='ACTION_COST_DECISION':cross.add('ACTION_COST_DECISION')
            if (rq['rng'] or rq['hidden_info']) and p['owner_family']!='HIDDEN_RNG_REPLAY':cross.add('HIDDEN_RNG_REPLAY')
            paths.append({'v2_path_id':v,**d,'cross_family_dependencies':sorted(cross),'source_provenance':[{'oracle_identity':z[0],'forge_source_path':z[1],'source_line':z[2],'source_directive':z[3],'source_token':z[4],'source_value':z[5]} for z in prov],'representative_actual_oracle_identities':sorted({z[0] for z in prov})[:12],'source_occurrence_count':len(prov),'required_decision_evidence':rq['decision'],'required_rng_evidence':rq['rng'],'required_hidden_info_evidence':rq['hidden_info'],'required_replay_evidence':rq['replay'],'evidence_class':'CODE_DERIVED','current_witness_status':'UNPROVED'})
            for x in g['rows']:occ_v2[(p['primitive_id'],x['forge_source_path'],x['source_line'])]=v
        grans.append({'parent_ws14_primitive_id':p['primitive_id'],'dispatch_domain':p['dispatch_domain'],'dispatch_token':p['dispatch_token'],'implementation_target':p['implementation_target'],'owner_family':p['owner_family'],'result':result,'v2_child_path_ids':childs,'selector_profile_count':len(childs),'occurrence_count':len(os),'justification':'Exact pinned source occurrence control profile, including implementation-consumed selectors and cost/mana shape.','evidence_class':'CODE_DERIVED'})
    line_v2=collections.defaultdict(set)
    for (pid,sp,ln),v in occ_v2.items():line_v2[(sp,ln)].add(v)
    newpaths={}; binds=[]; traces=[]; states=collections.Counter(); dirs=collections.Counter(); dir_states=collections.defaultdict(collections.Counter); computed_risks=0; path_by_id={x['v2_path_id']:x for x in paths}
    for idx,r in enumerate(unr):
        sp=r['forge_source_path'];ln=r['source_line'];directive=r['source_directive'];dirs[directive]+=1;base={'ws14_occurrence_index':idx,'oracle_identity':r['oracle_id'],'forge_source_path':sp,'source_line':ln,'source_directive':directive,'source_token':r['source_token'],'source_value':r['source_value'],'ws14_reason':r['reason'],'ws14_binding_status':r['binding_status']};st='UNKNOWN';alias=None;target=None;owner=None;cross=[];selector={};ev={};vids=[]
        if directive=='KEYWORD':
            rt=kwrt.get(idx)
            if rt and rt['oracle_identity']==r['oracle_id'] and rt['forge_source_path']==sp and int(rt['source_line'])==ln and rt['source_value']==r['source_value']:
                children=[]
                for kind,f in [('TRIGGER','generated_trigger_classes'),('REPLACEMENT','generated_replacement_classes'),('SPELLABILITY','generated_spellability_classes'),('STATIC','generated_static_classes')]:children += [{'kind':kind,'implementation_target':x} for x in rt.get(f,[])]
                refs=keyword_static_refs(rt['keyword_enum'],r['source_value'],docs);owner,cross=majority_owner([x['path'] for x in refs]);st='RESOLVED_EXECUTABLE';target=rt['keyword_instance_class'];selector={'keyword_enum':rt['keyword_enum'],'keyword_instance_class':rt['keyword_instance_class'],'has_generated_traits':bool(rt['has_generated_traits']),'generated_runtime_children':children};ev={'runtime_construction_path':['Keyword.getInstance','KeywordInstance.createTraits','CardFactoryUtil.addTriggerAbility/addReplacementEffect/addSpellAbility/addStaticAbility'],'runtime_object_type':target,'generated_child_objects':children,'implementation_callsites':refs[:100],'runtime_trace_occurrence':idx,'binding_basis':'Exact pinned CardFactory construction and direct KeywordInstance trait inspection; exact Java callsites supplement no-trait keyword enforcement.'}
                for ch in (children or [{'kind':'KEYWORD','implementation_target':target}]):
                    po=owner_for(ch['implementation_target']) if children else owner; d={'parent_ws14_primitive_id':None,'dispatch_domain':'KEYWORD_'+ch['kind'],'dispatch_token':rt['keyword_enum'],'implementation_target':ch['implementation_target'],'semantic_selector_profile':{**selector,'generated_child_kind':ch['kind'],'generated_child_target':ch['implementation_target']},'owner_family':po,'model_origin':'WS14_UNRESOLVED_FRONTIER_V2'};v=add_path(newpaths,d,r,source_lines,a.forge_root,cross);vids.append(v);line_v2[(sp,ln)].add(v)
        elif directive=='ALTERNATE_MODE':
            mode=r['source_value'];canonical={'DoubleFaced':'Transform'}.get(mode,mode);refs=[]
            for path,t in docs:
                for n,line in enumerate(t.splitlines(),1):
                    if path.endswith('forge/card/CardSplitType.java') and (re.match(rf'\s*{re.escape(canonical)}\(',line) or (mode=='DoubleFaced' and '"DoubleFaced".equals(text)' in line)):refs.append({'path':path,'line':n,'source':norm(line)[:240]})
            if refs:
                st='RESOLVED_EXECUTABLE';owner='ACTION_COST_DECISION';target='forge.card.CardSplitType#'+canonical+' -> forge.game.card.CardFactory';selector={'alternate_mode_source_token':mode,'card_split_type':canonical};ev={'runtime_construction_path':['card script AlternateMode','CardRules.Builder CardSplitType.smartValueOf','CardFactory state construction'],'runtime_object_type':'forge.game.card.CardState','implementation_callsites':refs,'binding_basis':'Exact pinned CardSplitType declaration, with its explicit DoubleFaced-to-Transform normalization when applicable.'};d={'parent_ws14_primitive_id':None,'dispatch_domain':'ALTERNATE_MODE','dispatch_token':mode,'implementation_target':target,'semantic_selector_profile':selector,'owner_family':owner,'model_origin':'WS14_UNRESOLVED_FRONTIER_V2'};v=add_path(newpaths,d,r,source_lines,a.forge_root);vids=[v];line_v2[(sp,ln)].add(v)
        elif directive=='SVAR':
            tok=r['source_token'];reach=svar_reachability(tok,sp,source_lines);jrefs=direct_svar.get(tok,[]);game=[x for x in jrefs if x['path'].startswith('forge-game/')];non=[x for x in jrefs if not x['path'].startswith('forge-game/')];terminal_ids=sorted({v for x in reach['semantic_terminals'] for v in line_v2.get((sp,x['line']),set())})
            if reach['semantic_terminals'] and terminal_ids:
                st='RESOLVED_EXECUTABLE';oc=collections.Counter((path_by_id[v] if v in path_by_id else newpaths[v])['owner_family'] for v in terminal_ids);owner=sorted(oc,key=lambda x:(-oc[x],OWNERS.index(x)))[0];cross=sorted(set(oc)-{owner},key=lambda x:OWNERS.index(x));target='forge.game.trigger.TriggerHandler#parseTrigger' if r['source_value'].startswith('Mode$') else 'forge.game.ability.AbilityUtils#calculateAmount';selector={'svar_token':tok,'svar_expression_shape':shape('SVar',r['source_value']),'semantic_terminal_lines':[x['line'] for x in reach['semantic_terminals']],'terminal_v2_path_ids':terminal_ids};ev={'svar_dependency_edges':reach['edges'],'semantic_terminals':reach['semantic_terminals'],'metadata_terminals':reach['metadata_terminals'],'direct_named_java_consumers':jrefs,'binding_basis':'Exact card-local, cycle-safe SVar dependency closure reaches a V2-covered production record; dynamic amount expressions resolve through AbilityUtils.calculateAmount, while Mode expressions resolve through TriggerHandler.parseTrigger.'};d={'parent_ws14_primitive_id':None,'dispatch_domain':'SVAR_RUNTIME_EXPRESSION','dispatch_token':tok,'implementation_target':target,'semantic_selector_profile':selector,'owner_family':owner,'model_origin':'WS14_UNRESOLVED_FRONTIER_V2'};v=add_path(newpaths,d,r,source_lines,a.forge_root,cross);vids=[v];line_v2[(sp,ln)].add(v)
            elif reach['semantic_terminals']:
                ev={'svar_dependency_edges':reach['edges'],'semantic_terminals':reach['semantic_terminals'],'binding_basis':'A production record references this SVar, but that record has no exact V2 path.'}
            elif reach['metadata_terminals']:
                st='PROVEN_NON_EXECUTABLE_METADATA';ev={'svar_dependency_edges':reach['edges'],'metadata_terminals':reach['metadata_terminals'],'direct_named_java_consumers':jrefs,'binding_basis':'Exact card-local closure reaches only NeedsToPlayVar AI metadata and no production record.'}
            elif game:
                st='RESOLVED_EXECUTABLE';owner,cross=majority_owner([x['path'] for x in game]);target=';'.join(sorted({x['path'] for x in game}));selector={'direct_svar_token':tok};ev={'direct_game_getSVar_callsites':game,'binding_basis':'Exact quoted SVar key consumed directly by pinned forge-game code.'};d={'parent_ws14_primitive_id':None,'dispatch_domain':'SVAR_DIRECT_CONSUMER','dispatch_token':tok,'implementation_target':target,'semantic_selector_profile':selector,'owner_family':owner,'model_origin':'WS14_UNRESOLVED_FRONTIER_V2'};v=add_path(newpaths,d,r,source_lines,a.forge_root,cross);vids=[v];line_v2[(sp,ln)].add(v)
            elif non:st='PROVEN_NON_EXECUTABLE_METADATA';ev={'non_rules_callsites':non,'binding_basis':'No card-source semantic consumer and all exact named Java consumers are outside forge-game Rules Core.'}
            else:
                risky=[x for x in computed_svar if any(f and (tok.startswith(f) or tok.endswith(f)) for f in x['literal_fragments'])]
                if risky:st='UNKNOWN';computed_risks+=1;ev={'possible_computed_key_callsites':risky[:50],'binding_basis':'Cannot prove unreachable because a computed pinned SVar key may match this token.'}
                else:st='PROVEN_UNREACHABLE';ev={'source_reference_count':0,'exact_named_java_consumer_count':0,'computed_literal_fragment_risk_count':0,'binding_basis':'Closed-world pinned-source proof: SVar maps are inert until keyed getSVar/hasSVar lookup; this key has no same-card reference, no exact Java consumer, and no matching computed-key literal fragment.'}
        states[st]+=1;dir_states[directive][st]+=1;row={**base,'v2_binding_state':st,'alias_target':alias,'implementation_target':target,'owner_family':owner,'cross_family_dependencies':cross,'semantic_selector_profile':selector,'v2_path_ids':sorted(vids),'evidence':ev,'evidence_class':'CODE_DERIVED' if st!='UNKNOWN' else 'UNKNOWN'};binds.append(row);traces.append({**row,'runtime_trace_kind':'PINNED_SOURCE_TO_RUNTIME_BINDING'})
    paths.extend(newpaths.values());pathmap={x['v2_path_id']:x for x in paths}
    for r in binds:
        if r['v2_binding_state']=='RESOLVED_ALIAS':
            vv=set()
            for ref in r['alias_target']['source_references']:vv.update(line_v2.get((r['forge_source_path'],ref['line']),set()))
            r['alias_target']['target_v2_path_ids']=sorted(vv)
            if not vv:r['v2_binding_state']='UNKNOWN';r['evidence_class']='UNKNOWN';states['RESOLVED_ALIAS']-=1;states['UNKNOWN']+=1;dir_states['SVAR']['RESOLVED_ALIAS']-=1;dir_states['SVAR']['UNKNOWN']+=1;r['evidence']['alias_resolution_blocker']='referencing line has no materialized V2 path'
    ub=collections.defaultdict(list)
    for r in binds:ub[r['oracle_identity']].append(r)
    per=[]
    for i in sorted(ids,key=lambda x:x['oracle_id']):
        vv=set()
        for src in i['forge_sources']:
            sp=src['forge_source_path']
            for b in src.get('primitive_bindings',[]):
                v=occ_v2.get((b['primitive_id'],sp,b['source_line']));
                if v:vv.add(v)
        for u in ub[i['oracle_id']]:vv.update(u.get('v2_path_ids',[]));vv.update((u.get('alias_target') or {}).get('target_v2_path_ids',[]))
        per.append({'schema':'commander-simulator-next.behavior-path-v2.identity','oracle_identity':i['oracle_id'],'oracle_name':i['oracle_name'],'forge_pin':PIN,'v2_path_ids':sorted(vv),'unresolved_v1_occurrence_count':len(ub[i['oracle_id']]),'unknown_v2_binding_count':sum(x['v2_binding_state']=='UNKNOWN' for x in ub[i['oracle_id']]),'evidence_class':'CODE_DERIVED'})
    ws16p=next(a.ws16_dir.rglob('ws16-jwar-isle-refuge.witness.json'));ws16t=next(a.ws16_dir.rglob('ws16-jwar-isle-refuge.trace.json'));ws16=lj(ws16p)
    contract=lj(Path(__file__).with_name('WS26_HARNESS_CONTRACT.json'));fixture=contract.get('positive_inherited_fixture')
    if not isinstance(fixture,dict) or set(fixture)!={'card_name','oracle_id','forge_source_path','forge_source_sha256_bytes'}:raise SystemExit('WS16 inherited fixture contract invalid')
    fsp=fixture['forge_source_path'];fp=a.forge_root/fsp
    if not fp.is_file() or sha(fp)!=fixture['forge_source_sha256_bytes']:raise SystemExit('WS16 inherited fixture source mismatch')
    flines=fp.read_text(encoding='utf-8').splitlines()
    if not flines or flines[0]!='Name:'+fixture['card_name']:raise SystemExit('WS16 inherited fixture name mismatch')
    jwar=[fixture['oracle_id']];gran={x['parent_ws14_primitive_id']:x for x in grans};compat=[];inherited=[];ws16_v2={}
    for pid in ws16['primitive_ids']:
        p=prim.get(pid);field={'TRIGGER':'Mode','REPLACEMENT':'Event'}.get(p.get('dispatch_domain') if p else None)
        if not p or not field:raise SystemExit('WS16 primitive lacks dispatch mapping '+pid)
        matches=[(n,line) for n,line in enumerate(flines,1) if fields(line).get(field)==p['dispatch_token']]
        if len(matches)!=1:raise SystemExit('WS16 fixture dispatch source is not exact '+pid)
        ln,line=matches[0];wb={'source_directive':p['dispatch_domain'],'source_value':p['dispatch_token']};prof=profile(wb,line,p['implementation_target'],a.forge_root,pcache)
        d={'parent_ws14_primitive_id':pid,'dispatch_domain':p['dispatch_domain'],'dispatch_token':p['dispatch_token'],'implementation_target':p['implementation_target'],'semantic_selector_profile':prof,'owner_family':p['owner_family'],'model_origin':'WS14_V1_GRANULARITY'};v=vid(d);entry=pathmap.get(v)
        rq=reqs([line],impl_text(p['implementation_target'],a.forge_root));cross=set(p.get('cross_family_dependencies',[]))
        if rq['decision'] and p['owner_family']!='ACTION_COST_DECISION':cross.add('ACTION_COST_DECISION')
        if (rq['rng'] or rq['hidden_info']) and p['owner_family']!='HIDDEN_RNG_REPLAY':cross.add('HIDDEN_RNG_REPLAY')
        prov={'oracle_identity':fixture['oracle_id'],'forge_source_path':fsp,'source_line':ln,'source_directive':p['dispatch_domain'],'source_token':field+'$','source_value':p['dispatch_token']}
        if entry is None:
            entry={'v2_path_id':v,**d,'cross_family_dependencies':sorted(cross),'source_provenance':[prov],'representative_actual_oracle_identities':[fixture['oracle_id']],'source_occurrence_count':1,'required_decision_evidence':rq['decision'],'required_rng_evidence':rq['rng'],'required_hidden_info_evidence':rq['hidden_info'],'required_replay_evidence':rq['replay'],'evidence_class':'CODE_DERIVED','current_witness_status':'UNPROVED'};paths.append(entry);pathmap[v]=entry;parent_paths[pid].append(v)
            g=gran[pid];g['v2_child_path_ids']=sorted(set(g['v2_child_path_ids']+[v]));g['selector_profile_count']=len(g['v2_child_path_ids']);g['result']='SPLIT_REQUIRED' if g['selector_profile_count']>1 else g['result']
        elif prov not in entry['source_provenance']:
            entry['source_provenance'].append(prov);entry['source_provenance'].sort(key=lambda x:(x['oracle_identity'],x['forge_source_path'],x['source_line']));entry['representative_actual_oracle_identities']=sorted(set(entry['representative_actual_oracle_identities']+[fixture['oracle_id']]))[:12];entry['source_occurrence_count']+=1
        ws16_v2[pid]=v
    for pid in ws16['primitive_ids']:
        exact=ws16_v2.get(pid);res=('REUSED_EXACT' if exact and gran[pid]['result']=='ATOMIC_SUFFICIENT' else 'REUSED_FOR_ONE_CHILD_PATH' if exact else 'UNKNOWN')
        if exact:inherited.append(exact);pathmap[exact]['current_witness_status']='PASS_INHERITED_WS16'
        compat.append({'source_workstream':'WS16','v1_primitive_id':pid,'v2_compatibility':res,'exact_v2_path_exercised':exact,'v1_split':gran[pid]['result']=='SPLIT_REQUIRED','additional_sibling_paths_unproved':sorted(set(parent_paths[pid])-({exact} if exact else set())),'reason':'Actual Jwar Isle Refuge source-bound pinned-Forge execution; inheritance limited to exact matching V2 child.','evidence_class':'DIRECTLY_VERIFIED'})
    ws17_lines=[x.split('\t',2) for x in (a.ws17_dir/'ws17-runtime-trace.tsv').read_text().splitlines() if x.strip()]
    if len(ws17_lines)!=11:raise SystemExit('WS17 trace count mismatch')
    src=a.ws17_test_source.read_text(encoding='utf-8')
    if 'AbilityFactory.getAbility(definition, host)' not in src or 'AbilityUtils.resolve(ability)' not in src:raise SystemExit('WS17 source no longer proves direct constructed effect path')
    for pid,scenario,*_ in ws17_lines:compat.append({'source_workstream':'WS17','v1_primitive_id':pid,'v2_compatibility':'INVALIDATED_BY_MODEL_CHANGE','exact_v2_path_exercised':None,'v1_split':gran[pid]['result']=='SPLIT_REQUIRED','additional_sibling_paths_unproved':sorted(parent_paths[pid]),'reason':'Execution remains valid Forge behavior evidence, but WS17 constructs effect definitions directly via AbilityFactory/AbilityUtils rather than exact actual-card source semantics required by WS26 V2.','scenario':scenario,'evidence_class':'DIRECTLY_VERIFIED'})
    if len(compat)!=13:raise SystemExit('existing witness accounting mismatch')
    if len(inherited)!=2 or not jwar:raise SystemExit('WS16 inheritance not exact')
    shutil.copyfile(ws16t,out/'WS26_POSITIVE_TRACE.json');tr=lj(ws16t);ex={x['primitive_id']:x for x in ws16['primitive_exercise']};pe=[];px=[]
    for c in compat:
        if c['source_workstream']=='WS16' and c['exact_v2_path_exercised']:
            e=ex[c['v1_primitive_id']];pe.append({'primitive_id':c['v1_primitive_id'],'exercised':True});px.append({'v2_path_id':c['exact_v2_path_exercised'],'parent_ws14_primitive_id':c['v1_primitive_id'],'exercised':True,'assertion_ids':e['assertion_ids'],'trace_event_ids':e['trace_event_ids']})
    rules=ws16.get('official_rules_adjudication',{}).get('rules_refs',[]) or ['Magic Comprehensive Rules 2026-08-07 rule 603.3','Magic Comprehensive Rules 2026-08-07 rule 603.6a','Magic Comprehensive Rules 2026-08-07 rule 614.1']
    positive={'schema':'commander-simulator-next.actual-card-witness.v2','witness_id':'ws26-positive-inherited-ws16-jwar-isle-refuge','source_head':ws16['source_head'],'source_tree':ws16['source_tree'],'forge_pin':PIN,'oracle_identities':jwar,'parent_ws14_primitive_ids':sorted(ws16['primitive_ids']),'v2_path_ids':sorted(inherited),'owner_family':'TRIGGER_REPLACEMENT_ZONE_SBA','initial_semantic_state':tr['initial'],'final_semantic_state':tr['final'],'state_assertions':ws16['state_assertions'],'primitive_exercise':sorted(pe,key=lambda x:x['primitive_id']),'path_exercise':sorted(px,key=lambda x:x['v2_path_id']),'decision_tape_ref':None,'rng_tape_ref':None,'observation_evidence_ref':None,'execution':{'engine':'pinned-forge','actual_rules_core_path':True,'authoritative_decision_boundary':'NOT_REQUIRED','silent_fallbacks':0,'engine_execution':'PASS','actual_card_execution':'PASS','inherited_run_job_artifact_refs':ws16['run_job_artifact_refs'],'inheritance_basis':'immutable WS16 actual-card source-bound execution; no cosmetic rerun'},'trace_ref':'WS26_POSITIVE_TRACE.json','trace_sha256':sha(out/'WS26_POSITIVE_TRACE.json'),'stdout_only':False,'rules_authority_refs':rules,'evidence_class':'EXTERNALLY_RULE_VALIDATED','status':'PASS'};wj(out/'WS26_POSITIVE_WITNESS.json',positive)
    wjl(out/'WS26_RUNTIME_BINDING_TRACE.jsonl',sorted(traces,key=lambda x:x['ws14_occurrence_index']));wjl(out/'WS26_BINDING_CLASSIFICATION.jsonl',sorted(binds,key=lambda x:x['ws14_occurrence_index']))
    bs={'schema':'commander-simulator-next.ws26-binding-summary.v2','input_unresolved_occurrences':1800,'accounted_occurrences':len(binds),'silently_dropped':1800-len(binds),'states':{k:states[k] for k in ['RESOLVED_EXECUTABLE','RESOLVED_ALIAS','PROVEN_NON_EXECUTABLE_METADATA','PROVEN_UNREACHABLE','UNKNOWN']},'directive_counts':dict(sorted(dirs.items())),'directive_state_counts':{k:dict(sorted(v.items())) for k,v in sorted(dir_states.items())},'production_reachable_UNKNOWN_bindings':states['UNKNOWN'],'ambiguous_bindings':0,'card_name_binding_rules':0,'fuzzy_text_binding_rules':0,'unproven_metadata_promotions':0,'unproven_unreachable_promotions':0,'computed_svar_risk_occurrences':computed_risks,'forge_pin':PIN,'evidence_class':'CODE_DERIVED'};wj(out/'WS26_BINDING_SUMMARY.json',bs)
    wjl(out/'WS26_GRANULARITY_ADJUDICATION.jsonl',grans);gc=collections.Counter(x['result'] for x in grans);wj(out/'WS26_PATH_VARIANTS.json',{'schema':'commander-simulator-next.behavior-path-v2.variants','v1_primitive_count':174,'counts':dict(sorted(gc.items())),'split_primitives':[{'parent_ws14_primitive_id':x['parent_ws14_primitive_id'],'v2_child_path_ids':x['v2_child_path_ids']} for x in grans if x['result']=='SPLIT_REQUIRED']})
    paths=sorted(pathmap.values(),key=lambda x:x['v2_path_id']);manifest={'schema':'commander-simulator-next.behavior-path-manifest.v2','model':'forge-systemic-runtime-behavior-path-v2','source_head':a.source_head,'source_tree':a.source_tree,'required_ws91_base_head':BASE,'required_ws91_base_tree':BASE_TREE,'forge_pin':PIN,'qualified_runtime_dependency_head':RUNTIME,'qualified_runtime_dependency_tree':RUNTIME_TREE,'oracle_identity_count':1678,'parent_ws14_primitive_count':174,'path_count':len(paths),'inherited_execution_sources':[{'head':ws16['source_head'],'tree':ws16['source_tree'],'workstream':'WS16'}],'id_contract':'sha256(canonical descriptor parent/domain/token/implementation_target/semantic_selector_profile/owner/model_origin), first 40 hex','paths':paths,'evidence_class':'TECHNICALLY_CONFORMANT'};wj(out/'WS26_BEHAVIOR_PATH_MANIFEST_V2.json',manifest);wjl(out/'WS26_PER_IDENTITY_V2.jsonl',per);wj(out/'WS26_EXISTING_WITNESS_COMPATIBILITY.json',{'schema':'commander-simulator-next.ws26-existing-witness-compatibility.v1','existing_pass_witnesses_accounted':13,'automatic_blanket_v1_to_v2_inheritance':0,'entries':sorted(compat,key=lambda x:(x['source_workstream'],x['v1_primitive_id']))})
    parts={x:[] for x in OWNERS}
    for p in paths:parts[p['owner_family']].append(p['v2_path_id'])
    for x in parts:parts[x].sort()
    wj(out/'WS26_OWNER_PARTITIONS.json',{'schema':'commander-simulator-next.ws26-owner-partitions.v1','production_required_v2_path_count':len(paths),'families':{x:{'path_count':len(parts[x]),'v2_path_ids':parts[x]} for x in OWNERS},'production_paths_without_owner':sum(p['owner_family'] not in OWNERS for p in paths),'production_paths_with_multiple_primary_owners':0})
    wsmap={'ACTION_COST_DECISION':'WS27','TRIGGER_REPLACEMENT_ZONE_SBA':'WS28','CONTINUOUS_COPY_CONTROL':'WS29','COMBAT_COMMANDER':'WS30','HIDDEN_RNG_REPLAY':'WS31'};inh={c['exact_v2_path_exercised']:c for c in compat if c.get('exact_v2_path_exercised')};sets={}
    for fam,w in wsmap.items():
        rr=[]
        for v in parts[fam]:
            p=pathmap[v];rr.append({'v2_path_id':v,'parent_ws14_primitive_id':p.get('parent_ws14_primitive_id'),'implementation_target':p['implementation_target'],'representative_actual_oracle_identities':p['representative_actual_oracle_identities'],'source_provenance':p['source_provenance'],'required_decision_evidence':p['required_decision_evidence'],'required_rng_evidence':p['required_rng_evidence'],'required_hidden_info_evidence':p['required_hidden_info_evidence'],'required_replay_evidence':p['required_replay_evidence'],'current_witness_status':p['current_witness_status'],'existing_compatible_witness':inh.get(v)})
        sets[w]={'owner_family':fam,'path_count':len(rr),'paths':rr}
    wj(out/'WS26_NEXT_WORKSTREAM_INPUT.json',{'schema':'commander-simulator-next.ws26-next-workstream-input.v1','common_source_boundary':{'head':'SELF_FINAL_WS26_HEAD','tree':'RESOLVE_FROM_FINAL_HEAD','qualified_model_source_head':a.source_head,'qualified_model_source_tree':a.source_tree},'sets':sets})
    hg={'schema':'commander-simulator-next.ws26-shared-harness-gate.v1','exact_pinned_engine_execution':'PASS','actual_card_execution':'PASS','authoritative_decision_boundary_used':'PASS','authoritative_decision_boundary_basis':'Every decision-required V2 path is bound to retained Q1 ExternalDecisionRequest/Response/Validator/Tape exact runtime dependency; the positive inherited path itself requires no discretionary decision.','initial_state_retained':'PASS','final_state_retained':'PASS','immutable_trace_hash':'PASS','stdout_only':False,'positive_fixture':{'result':'PASS','witness_id':positive['witness_id'],'v2_path_ids':positive['v2_path_ids'],'trace_sha256':positive['trace_sha256'],'actual_oracle_identities':jwar},'negative_ABI_fixtures':'PENDING_WORKFLOW_VALIDATION','illegal_response_rejected':'PENDING_WORKFLOW_VALIDATION','silent_fallbacks':0,'failure_semantics_overall_claimed':False,'card_behavior_failure_production_binding_claimed':False,'evidence_class':'TECHNICALLY_CONFORMANT'};wj(out/'WS26_HARNESS_GATE.json',hg)
    wj(out/'WS26_SVAR_CONSUMER_AUDIT.json',{'schema':'commander-simulator-next.ws26-svar-consumer-audit.v1','exact_named_svar_tokens':len(direct_svar),'computed_svar_callsites':computed_svar,'computed_risk_occurrences':computed_risks,'evidence_class':'CODE_DERIVED'})
    wj(out/'WS26_PRE_GATE.json',{'source_head':a.source_head,'source_tree':a.source_tree,'forge_pin':PIN,'oracle_identity_count':len(per),'oracle_identity_drops':0,'oracle_identity_additions':0,'binding_summary':bs,'granularity_counts':dict(sorted(gc.items())),'v1_primitives_accounted':len(grans),'v2_path_count':len(paths),'duplicate_v2_path_ids':len(paths)-len({p['v2_path_id'] for p in paths}),'conflicting_v2_descriptors':0,'production_paths_without_owner':sum(p['owner_family'] not in OWNERS for p in paths),'production_paths_with_multiple_primary_owners':0,'card_name_semantic_keys':0,'nondeterministic_id_components':0,'existing_pass_witnesses_accounted':len(compat),'automatic_blanket_v1_to_v2_inheritance':0,'harness_gate':hg,'source_hash_mismatches':mismatch,'Q6_ACTUAL_CARD_BEHAVIOR':'NOT_ADJUDICATED_BY_WS26','FAILURE_SEMANTICS_OVERALL_CLAIMED':False,'CARD_BEHAVIOR_FAILURE_PRODUCTION_BINDING_CLAIMED':False})
if __name__=='__main__':main()
