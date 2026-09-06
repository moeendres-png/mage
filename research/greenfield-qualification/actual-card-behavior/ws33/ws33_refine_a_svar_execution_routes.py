#!/usr/bin/env python3
"""Refine the immutable A SVar26 case ABI into actual production-root runtime routes.

The original projector stops at the immediate selected parent of each target SVar. That is
sufficient for ABILITY parents and direct TRIGGER parents, but a selected `SVAR:DB$`
parent is a nested subability, not necessarily a standalone production root. This tool
uses only pinned Forge card source provenance to resolve that nested parent one step
upstream to every exact Trigger `Execute$ <parentSVar>` consumer.

No Magic legality is inferred. Effective path identity is unchanged. The output merely
chooses the runtime mechanism that can reach the already-modeled target from an actual
card production entrypoint.
"""
from __future__ import annotations
import argparse, base64, json
from pathlib import Path

FORGE_PIN='8c7e9afb8e6caee88644b94e25da5852e36f8928'
TARGET_IMPL='forge.game.spellability.TargetRestrictions'


def fail(m: str) -> None: raise SystemExit('WS33_A_SVAR_ROUTE_REFINE=FAIL '+m)
def req(c: bool,m: str) -> None:
    if not c: fail(m)
def dec(s: str) -> str: return base64.b64decode(s).decode('utf-8')
def enc(s: str) -> str: return base64.b64encode(s.encode('utf-8')).decode('ascii')

def fields(script: str) -> dict[str,str]:
    out={}
    for part in script.split('|'):
        p=part.strip()
        if '$' not in p: continue
        k,v=p.split('$',1); out[k.strip()]=v.strip()
    return out

def trigger_consumers(source: Path, parent_svar: str) -> list[tuple[int,str,str]]:
    out=[]
    for n,line in enumerate(source.read_text(encoding='utf-8').splitlines(),1):
        if not line.startswith('T:'): continue
        script=line.split(':',1)[1].strip(); f=fields(script)
        if f.get('Execute')==parent_svar:
            mode=f.get('Mode',''); req(bool(mode),f'{source}: trigger line {n} missing Mode')
            out.append((n,mode,script))
    return out

def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument('--cases-dir',type=Path,required=True); ap.add_argument('--forge-root',type=Path,required=True); ap.add_argument('--out-dir',type=Path,required=True); a=ap.parse_args()
    gate=json.loads((a.cases_dir/'out/A_REST_SVAR_CASE_GATE.json').read_text())
    req(gate.get('status')=='PASS' and gate.get('svar_paths')==26 and gate.get('nontrigger_paths')==9 and gate.get('trigger_paths')==17,'input case gate mismatch')
    nrows=[x.split('\t') for x in (a.cases_dir/'out/a-rest-svar-nontrigger9.tsv').read_text().splitlines() if x]
    trows=[x.split('\t') for x in (a.cases_dir/'out/a-rest-svar-trigger17.tsv').read_text().splitlines() if x]
    req(len(nrows)==9 and all(len(x)==19 for x in nrows),'NonTrigger9 ABI mismatch')
    req(len(trows)==17 and all(len(x)==21 for x in trows),'Trigger17 ABI mismatch')

    af=[]; nested=[]; nested_paths=set()
    for r in nrows:
        pid=r[1]; directive=r[8]; token=r[9]
        if directive=='ABILITY': af.append(r); continue
        req(directive=='SVAR' and token=='DB$',f'{pid}: unsupported nested nontrigger shape {directive}:{token}')
        parent_svar=r[15]; req(bool(parent_svar),f'{pid}: nested parent SVar missing')
        parent_script=dec(r[14]); pf=fields(parent_script)
        req(pf.get('DB')=='Charm' and pf.get('Choices'),f'{pid}: nested DB parent is not Charm Choices')
        src=a.forge_root/r[6]; req(src.is_file(),f'{pid}: source missing {r[6]}')
        consumers=trigger_consumers(src,parent_svar)
        req(bool(consumers),f'{pid}: no Trigger Execute consumer for nested parent {parent_svar}')
        nested_paths.add(pid)
        for ix,(line,mode,trig) in enumerate(consumers):
            nested.append('\t'.join(map(str,[
                r[0],pid,ix,len(consumers),r[2],r[3],parent_svar,pf['DB'],r[16],r[17],r[5],r[6],line,'TRIGGER','Execute',mode,
                r[10],r[11],r[12],r[13],r[18],enc(parent_script),enc(trig)
            ])))

    req(len(af)==8,'AF effective path count !=8')
    req(len(nested_paths)==1,'nested effective path count !=1')
    req(len(nested)==2,'nested trigger entrypoint count !=2')
    modes=sorted(x.split('\t')[15] for x in nested)
    req(modes==['Attacks','ChangesZone'],'nested trigger mode set mismatch '+repr(modes))
    all_ids={x[1] for x in af}|nested_paths|{x[1] for x in trows}
    req(len(all_ids)==26,'effective route union !=26')
    req(({x[1] for x in af}&nested_paths)==set() and ({x[1] for x in af}&{x[1] for x in trows})==set() and (nested_paths&{x[1] for x in trows})==set(),'route overlap')

    a.out_dir.mkdir(parents=True,exist_ok=True)
    (a.out_dir/'a-rest-svar-af8.tsv').write_text('\n'.join('\t'.join(x) for x in af)+'\n')
    (a.out_dir/'a-rest-svar-nested-trigger1.tsv').write_text('\n'.join(nested)+'\n')
    (a.out_dir/'a-rest-svar-trigger17.tsv').write_text('\n'.join('\t'.join(x) for x in trows)+'\n')
    out={
      'schema':'commander-simulator-next.ws33-a-svar-production-root-routes.v1','status':'PASS','forge_pin':FORGE_PIN,
      'effective_paths':26,'af_effective_paths':8,'nested_trigger_effective_paths':1,'nested_trigger_parent_entrypoints':2,
      'direct_trigger_effective_paths':17,'direct_trigger_parent_entrypoints':17,'total_runtime_parent_entrypoints':27,
      'nested_trigger_modes':modes,'effective_path_overlap':0,'runtime_root_refinement_performed':True,
      'magic_legality_inference':False,'coverage_mutated':False,'coverage_promotion':False
    }
    (a.out_dir/'A_REST_SVAR_EXECUTION_ROUTE_GATE.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print('WS33_A_SVAR_ROUTE_REFINE=PASS effective=26 af=8 nested=1 nested_parents=2 trigger=17 runtime_parents=27')
    print('WS33_A_SVAR_ROUTE_MAGIC_LEGALITY_INFERENCE=FALSE')

if __name__=='__main__': main()
