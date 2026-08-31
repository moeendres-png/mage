#!/usr/bin/env python3
from __future__ import annotations
import argparse, collections, hashlib, json, re, subprocess
from pathlib import Path

PIN='8c7e9afb8e6caee88644b94e25da5852e36f8928'
DOMAIN='SVAR_RUNTIME_EXPRESSION'
ACTION='ACTION_COST_DECISION'; TRZ='TRIGGER_REPLACEMENT_ZONE_SBA'; CONT='CONTINUOUS_COPY_CONTROL'
ERRATA={
'forge-behavior-v2:452495ff67d15f9989748411f5ec41067e039c7b',
'forge-behavior-v2:6dfbc7e6fb17a15e4445462f4383e6ebcf7ffedf',
'forge-behavior-v2:7caaed2bb9b0c5fe0f5dab44de04175ec1867a16',
'forge-behavior-v2:beee69a372f7b75417aa7fd9552cdfe6fae1a519'}
TEXT={'Description','SpellDescription','TriggerDescription','StackDescription','TgtPrompt','AILogic','PrecostDesc','CostDesc'}
REPL={'ReplacementEffects','Replacements','AddReplacements'}
TRIG={'Triggers','AddTrigger','AddTriggers','TriggersWhenSpent','ExtraPhaseDelayedTrigger'}
STATIC={'StaticAbilities','staticAbilities','AddStaticAbility','AddStaticAbilities','StaticEffect'}
ABILITY={'Execute','SubAbility','RepeatSubAbility','ReplaceWith','PreventionSubAbility','WinSubAbility','OtherwiseSubAbility','BidSubAbility','ChooseNumberSubAbility','Lowest','Highest','NotLowest','GuessCorrect','GuessWrong','MatchedAbility','UnmatchedAbility','HeadsSubAbility','TailsSubAbility','LoseSubAbility','TrueSubAbility','FalseSubAbility','ChosenPile','UnchosenPile','FallbackAbility','ChooseSubAbility','CantChooseSubAbility','RegenerationAbility','ReturnAbility','GiftAbility','VoteSubAbility','VoteTiedAbility','Abilities','AddAbilities','ExtraPhaseDelayedTriggerExcute'}
COST={'Cost','UnlessCost'}
AMOUNT={'Amount','AddPower','AddToughness','SetPower','SetToughness','Num','NumAtt','NumDef','NumDmg','NumCards','NumCopies','CounterNum','DigNum','RevealNumber','TokenAmount','TokenPower','TokenToughness','TargetMin','TargetMax','DividedAsYouChoose','ReduceCost','CheckSVar','ConditionCheckSVar','RepeatCheckSVar','LifeAmount','Announce','Count','Number','Max','Min','Power','Toughness','DamageAmount','CounterAmount','RemoveAmount','SacAmount','DiscardAmount','ExileAmount','DrawAmount','DiscardNum','PayLifeAmount','ManaAmount','CharmNum','CanBlockAmount','BranchConditionSVar','BranchConditionSVarCompare','ConditionSVarCompare','SVarCompare','VarValue','ScryNum','ValidTgts'}
SELECTOR={'Defined','DefinedCards','DefinedPlayers','DefinedObjects','AffectedDefined','RememberObjects','RememberLKI','ValidCard','ValidCards','ValidPlayer','ValidSource','ValidTarget','Choices'}
ASSIGN={'AddSVar','AddSVars','sVars'}

def canon(o): return (json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\n').encode()
def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p,o): Path(p).parent.mkdir(parents=True,exist_ok=True); Path(p).write_bytes(canon(o))
def vid(d): return 'forge-behavior-v2:'+hashlib.sha256(canon(d)).hexdigest()[:40]
def fields(s):
    out={}
    for x in s.split('|'):
        if '$' in x:
            k,v=x.strip().split('$',1); out[k.strip()]=v.strip()
    return out

def svar(line):
    s=line.strip()
    if not s.startswith('SVar:'): return None
    x=s[5:]
    if ':' not in x:return None
    return tuple(y.strip() for y in x.split(':',1))
def record(line):
    s=line.strip(); m=re.match(r'^([ASTR]):(.*)$',s)
    if m:return {'kind':m.group(1),'fields':fields(m.group(2)),'text':s}
    if s.startswith('K:'):return {'kind':'K','parts':s[2:].split(':'),'fields':{},'text':s}
    return None
def token_match(v,t):
    if re.search(r'(?<![A-Za-z0-9_])'+re.escape(t)+r'(?![A-Za-z0-9_])',v):return True
    return re.search(r'(?:EQ|NE|GE|GT|LE|LT)'+re.escape(t)+r'(?![A-Za-z0-9_])',v) is not None

def index_card(p):
    ss={}; rr=[]
    for n,line in enumerate(Path(p).read_text(encoding='utf-8').splitlines(),1):
        x=svar(line)
        if x:ss[x[0]]={'line':n,'value':x[1],'fields':fields(x[1]),'text':line.strip()}
        r=record(line)
        if r:r['line']=n;rr.append(r)
    return {'svars':ss,'records':rr}

def static_modes(root):
    t=(root/'forge-game/src/main/java/forge/game/staticability/StaticAbilityMode.java').read_text(encoding='utf-8')
    return {m.group(1) for line in t.splitlines() if (m:=re.match(r'\s*([A-Za-z][A-Za-z0-9_]*)\s*(?:\(|,|;)',line))}
def kind(v,statics):
    f=fields(v)
    if v.startswith(('AB$','SP$','DB$')):return 'ABILITY_DEFINITION'
    if v.startswith('ST$'):return 'STATIC_DEFINITION'
    if v.startswith('Event$'):return 'REPLACEMENT_DEFINITION'
    if v.startswith('Mode$'):return 'STATIC_DEFINITION' if f.get('Mode') in statics else 'TRIGGER_DEFINITION'
    if v.startswith('SVar:'):return 'SVAR_ASSIGNMENT'
    if v in {'TRUE','FALSE'}:return 'BOOLEAN_VALUE'
    return 'VALUE_EXPRESSION'

def forge_contract(root):
    files={
      'effect':root/'forge-game/src/main/java/forge/game/ability/effects/EffectEffect.java',
      'factory':root/'forge-game/src/main/java/forge/game/ability/AbilityFactory.java',
      'phase':root/'forge-game/src/main/java/forge/game/ability/effects/AddPhaseEffect.java',
      'animate':root/'forge-game/src/main/java/forge/game/ability/effects/AnimateEffect.java',
      'store':root/'forge-game/src/main/java/forge/game/ability/effects/StoreSVarEffect.java',
      'cond':root/'forge-game/src/main/java/forge/game/spellability/SpellAbilityCondition.java'}
    txt={k:p.read_text(encoding='utf-8') for k,p in files.items()}
    checks={
      'replacement_gets_svar_then_parser':'AbilityUtils.getSVar(sa, s)' in txt['effect'] and 'ReplacementHandler.parseReplacement' in txt['effect'],
      'trigger_gets_svar_then_parser':'TriggerHandler.parseTrigger(AbilityUtils.getSVar(sa, s)' in txt['effect'],
      'ability_factory_subability':'getSubAbility(state, name, sVarHolder)' in txt['factory'],
      'delayed_trigger_parser':'ExtraPhaseDelayedTrigger' in txt['phase'] and 'TriggerHandler.parseTrigger(sa.getSVar' in txt['phase'],
      'animate_svar_assignment':'sa.hasParam("sVars")' in txt['animate'] and 'AbilityUtils.getSVar(sa, s)' in txt['animate'],
      'store_svar_is_destination_key':'key = sa.getParam("SVar")' in txt['store'] and 'source.setSVar(key' in txt['store'],
      'condition_svar_is_amount':'AbilityUtils.calculateAmount(host, this.getsVarToCheck(), sa)' in txt['cond']}
    if not all(checks.values()):raise SystemExit('consumer contract mismatch '+json.dumps(checks,sort_keys=True))
    return {'forge_pin':PIN,'checks':checks,'source_sha256':{k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in files.items()}}

def consumer(field,value_kind,record_kind):
    if field in TEXT:return None
    if field in REPL:return ('REPLACEMENT_PARSER','forge.game.replacement.ReplacementHandler#parseReplacement',TRZ)
    if field in TRIG:return ('TRIGGER_PARSER','forge.game.trigger.TriggerHandler#parseTrigger',TRZ)
    if field in STATIC:return ('STATIC_ABILITY_PARSER','forge.game.staticability.StaticAbility#create',CONT)
    if field in ASSIGN:return ('SVAR_ASSIGNMENT','forge.game.ability.AbilityUtils#getSVar',CONT)
    if field in ABILITY:return ('ABILITY_FACTORY','forge.game.ability.AbilityFactory#getAbility',ACTION)
    if field in COST:return ('COST_PARSER','forge.game.cost.Cost',ACTION)
    if field in AMOUNT:return ('AMOUNT_EVALUATION','forge.game.ability.AbilityUtils#calculateAmount',ACTION)
    if field in SELECTOR:return ('DEFINED_SELECTOR','forge.game.ability.AbilityUtils#getDefined',ACTION)
    if record_kind=='K':
      if value_kind=='REPLACEMENT_DEFINITION':return ('KEYWORD_REPLACEMENT_PARSER','forge.game.replacement.ReplacementHandler#parseReplacement',TRZ)
      if value_kind=='TRIGGER_DEFINITION':return ('KEYWORD_TRIGGER_PARSER','forge.game.trigger.TriggerHandler#parseTrigger',TRZ)
      if value_kind=='STATIC_DEFINITION':return ('KEYWORD_STATIC_PARSER','forge.game.staticability.StaticAbility#create',CONT)
      if value_kind=='ABILITY_DEFINITION':return ('KEYWORD_ABILITY_FACTORY','forge.game.ability.AbilityFactory#getAbility',ACTION)
      if value_kind=='SVAR_ASSIGNMENT':return ('KEYWORD_SVAR_ASSIGNMENT','forge.game.ability.AbilityUtils#getSVar',CONT)
      return ('KEYWORD_AMOUNT_EVALUATION','forge.game.ability.AbilityUtils#calculateAmount',ACTION)
    return None

def direct(token,own,card,value_kind,statics):
    out=[]
    def add(c,field,rkind,line,parent,text,keyword=None):
      out.append({'consumer_kind':c[0],'implementation_target':c[1],'owner_family':c[2],'consumer_field':field,'consumer_record_kind':rkind,'consumer_line':line,'consumer_parent_svar':parent,'consumer_keyword':keyword,'consumer_text':text[:500]})
    for parent,d in card['svars'].items():
      if d['line']==own:continue
      pk=kind(d['value'],statics)
      if pk=='VALUE_EXPRESSION' and token_match(d['value'],token):add(('AMOUNT_SVAR_RECURSION','forge.game.ability.AbilityUtils#calculateAmount',ACTION),'<svar-expression>','SVAR',d['line'],parent,d['text'])
      for f,v in d['fields'].items():
        if not token_match(v,token):continue
        if f=='SVar' and pk=='VALUE_EXPRESSION':c=('AMOUNT_SVAR_RECURSION','forge.game.ability.AbilityUtils#calculateAmount',ACTION)
        elif f=='SVar':c=None
        else:c=consumer(f,value_kind,'SVAR')
        if c:add(c,f,'SVAR',d['line'],parent,d['text'])
    for r in card['records']:
      if r['kind']=='K':
        if any(token_match(x,token) for x in r['parts']):
          c=consumer(None,value_kind,'K')
          if c:add(c,'<keyword-argument>','K',r['line'],None,r['text'],r['parts'][0] if r['parts'] else None)
        continue
      for f,v in r['fields'].items():
        if token_match(v,token):
          c=consumer(f,value_kind,r['kind'])
          if c:add(c,f,r['kind'],r['line'],None,r['text'])
    uniq={json.dumps(x,sort_keys=True):x for x in out};return [uniq[k] for k in sorted(uniq)]
def descriptor(old,c,token,value):
    op=old.get('semantic_selector_profile') or {}
    return {'parent_ws14_primitive_id':old.get('parent_ws14_primitive_id'),'dispatch_domain':DOMAIN,'dispatch_token':token,'implementation_target':c['implementation_target'],'semantic_selector_profile':{'consumer_model':'WS33_CONSUMER_AWARE_SVAR_V3','svar_token':token,'svar_expression_shape':op.get('svar_expression_shape',value[:180]),'first_consumer_kind':c['consumer_kind'],'first_consumer_field':c['consumer_field'],'first_consumer_record_kind':c['consumer_record_kind']},'owner_family':c['owner_family'],'model_origin':'WS33_SHARED_CONSUMER_REPAIR_V2'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--manifest',type=Path,required=True);ap.add_argument('--forge-root',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    head=subprocess.check_output(['git','-C',str(a.forge_root),'rev-parse','HEAD'],text=True).strip()
    if head!=PIN:raise SystemExit('Forge pin mismatch '+head)
    contract=forge_contract(a.forge_root);statics=static_modes(a.forge_root);raw=load(a.manifest)['paths'];sv=[p for p in raw if p.get('dispatch_domain')==DOMAIN]
    cache={};new={};oldnew=collections.defaultdict(set);unresolved=[];sigs=collections.Counter()
    for old in sv:
      oid=old['v2_path_id']
      for prov in old.get('source_provenance',[]):
        if prov.get('source_directive')!='SVAR':continue
        rel=prov['forge_source_path']; n=int(prov['source_line']); tok=prov['source_token']; val=prov['source_value']; src=a.forge_root/rel
        if rel not in cache:cache[rel]=index_card(src)
        card=cache[rel]; decl=card['svars'].get(tok)
        if not decl or decl['line']!=n or decl['value']!=val:unresolved.append({'old_effective_v2_path_id':oid,'reason':'SVAR_PROVENANCE_MISMATCH','source':rel,'line':n,'token':tok});continue
        cs=direct(tok,n,card,kind(val,statics),statics)
        if not cs:unresolved.append({'old_effective_v2_path_id':oid,'reason':'NO_ACTUAL_FIRST_CONSUMER','source':rel,'line':n,'token':tok,'value':val});continue
        for c in cs:
          d=descriptor(old,c,tok,val); nid=vid(d);sigs[(c['consumer_kind'],c['implementation_target'],c['owner_family'],c['consumer_field'])]+=1
          q=new.setdefault(nid,{'v2_path_id':nid,**d,'cross_family_dependencies':list(old.get('cross_family_dependencies',[])),'source_provenance':[],'representative_actual_oracle_identities':[],'source_occurrence_count':0,'required_decision_evidence':bool(old.get('required_decision_evidence')),'required_rng_evidence':bool(old.get('required_rng_evidence')),'required_hidden_info_evidence':bool(old.get('required_hidden_info_evidence')),'required_replay_evidence':bool(old.get('required_replay_evidence')),'evidence_class':'CODE_DERIVED','current_witness_status':'UNPROVED','consumer_evidence':[],'historical_ws26_v2_path_ids':[]})
          if prov not in q['source_provenance']:q['source_provenance'].append(prov)
          q['representative_actual_oracle_identities']=sorted(set(q['representative_actual_oracle_identities']+[prov['oracle_identity']]))[:12];q['historical_ws26_v2_path_ids']=sorted(set(q['historical_ws26_v2_path_ids']+[oid]))
          ev={k:v for k,v in c.items() if k!='consumer_text'}|{'forge_source_path':rel,'source_line':n,'source_token':tok,'source_value':val,'consumer_text':c['consumer_text']}
          if ev not in q['consumer_evidence']:q['consumer_evidence'].append(ev)
          oldnew[oid].add(nid)
    for q in new.values():q['source_provenance'].sort(key=lambda x:(x['forge_source_path'],x['source_line'],x['oracle_identity']));q['consumer_evidence'].sort(key=lambda x:(x['forge_source_path'],x['source_line'],x['consumer_line'],x['consumer_field']));q['source_occurrence_count']=len(q['source_provenance'])
    migrations=[]
    by={p['v2_path_id']:p for p in sv}
    for oid in sorted(by):
      for nid in sorted(oldnew.get(oid,[])):
        o=by[oid];q=new[nid];migrations.append({'old_effective_v2_path_id':oid,'new_effective_v2_path_id':nid,'old_implementation_target':o['implementation_target'],'new_implementation_target':q['implementation_target'],'old_owner_family':o['owner_family'],'new_owner_family':q['owner_family'],'migration_reason':'CONSUMER_AWARE_FIRST_RUNTIME_USE','historical_erratum_alias':oid in ERRATA,'status_before':None,'status_after':'UNKNOWN'})
    result={'schema':'commander-simulator-next.ws33-consumer-aware-svar-model.v3','forge_pin':PIN,'forge_consumer_contract':contract,'raw_svar_path_count':len(sv),'resolved_old_path_count':len(oldnew),'unresolved_old_path_count':len({x['old_effective_v2_path_id'] for x in unresolved}),'unresolved_occurrence_count':len(unresolved),'new_consumer_path_count':len(new),'historical_erratum_aliases':sorted(ERRATA),'old_to_new':{k:sorted(v) for k,v in sorted(oldnew.items())},'new_paths':[new[k] for k in sorted(new)],'migrations':migrations,'unresolved':unresolved,'consumer_signature_counts':[{'consumer_kind':k[0],'implementation_target':k[1],'owner_family':k[2],'consumer_field':k[3],'count':n} for k,n in sorted(sigs.items(),key=lambda z:(-z[1],z[0]))]}
    write(a.out,result);print(json.dumps({'RAW_SVAR_PATHS':len(sv),'RESOLVED_OLD_PATHS':len(oldnew),'UNRESOLVED_OLD_PATHS':result['unresolved_old_path_count'],'UNRESOLVED_OCCURRENCES':len(unresolved),'NEW_CONSUMER_PATHS':len(new)},sort_keys=True))
    if unresolved:
      for x in unresolved:print('UNRESOLVED '+json.dumps(x,sort_keys=True))
      return 2
    return 0
if __name__=='__main__':raise SystemExit(main())
