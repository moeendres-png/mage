#!/usr/bin/env python3
from __future__ import annotations
import argparse, base64, json, pathlib, re

FAMILY='HIDDEN_RNG_REPLAY'
FORGE_PIN='8c7e9afb8e6caee88644b94e25da5852e36f8928'

def extract_script(line: str, directive: str) -> str:
    line=line.rstrip('\n\r')
    if directive == 'SVAR':
        if not line.startswith('SVar:') or line.count(':') < 2:
            raise ValueError(f'expected SVar line, got {line!r}')
        return line.split(':',2)[2].strip()
    if directive == 'ABILITY':
        if ':' not in line:
            raise ValueError(f'expected ability line, got {line!r}')
        return line.split(':',1)[1].strip()
    raise ValueError(f'unsupported source directive {directive}')

def card_name(lines: list[str], path: pathlib.Path) -> str:
    for line in lines:
        if line.startswith('Name:'):
            return line.split(':',1)[1].strip()
    raise ValueError(f'Name: missing in {path}')

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--ws26-dir', required=True)
    ap.add_argument('--forge-root', required=True)
    ap.add_argument('--out-json', required=True)
    ap.add_argument('--out-tsv', required=True)
    ns=ap.parse_args()
    ws26=pathlib.Path(ns.ws26_dir)
    forge=pathlib.Path(ns.forge_root)
    if (forge/'.git').exists():
        import subprocess
        pin=subprocess.check_output(['git','-C',str(forge),'rev-parse','HEAD'],text=True).strip()
        if pin != FORGE_PIN: raise SystemExit(f'Forge pin mismatch: {pin}')
    manifest=json.loads((ws26/'WS26_BEHAVIOR_PATH_MANIFEST_V2.json').read_text())
    paths=manifest['paths'] if isinstance(manifest,dict) else manifest
    partitions=json.loads((ws26/'WS26_OWNER_PARTITIONS.json').read_text())
    ids=partitions['families'][FAMILY]['v2_path_ids']
    by={p['v2_path_id']:p for p in paths}
    if len(ids)!=81: raise SystemExit(f'expected 81 {FAMILY} paths, got {len(ids)}')
    rows=[]
    for ordinal,vid in enumerate(ids,1):
        p=by[vid]
        prov=p['source_provenance'][0]
        src=forge/prov['forge_source_path']
        lines=src.read_text(encoding='utf-8').splitlines()
        ln=int(prov['source_line'])
        if ln<1 or ln>len(lines): raise SystemExit(f'{vid}: source line out of range')
        line=lines[ln-1]
        script=extract_script(line,prov['source_directive'])
        token=prov['source_token']
        if not script.startswith(token):
            raise SystemExit(f'{vid}: exact source script does not start with {token}: {script}')
        # Dispatch token must be the first API field in the exact script.
        m=re.search(r'(?:^|\s\|\s)(?:AB|SP|DB)\$\s*([^|]+)',script)
        if not m or m.group(1).strip()!=p['dispatch_token']:
            raise SystemExit(f'{vid}: dispatch mismatch exact source={m.group(1).strip() if m else None} manifest={p["dispatch_token"]}')
        row={
            'ordinal':ordinal,
            'v2_path_id':vid,
            'parent_ws14_primitive_id':p['parent_ws14_primitive_id'],
            'oracle_identity':prov['oracle_identity'],
            'representative_actual_oracle_identities':p['representative_actual_oracle_identities'],
            'card_name':card_name(lines,src),
            'dispatch_token':p['dispatch_token'],
            'implementation_target':p['implementation_target'],
            'source_path':prov['forge_source_path'],
            'source_line':ln,
            'source_directive':prov['source_directive'],
            'source_token':token,
            'exact_script':script,
            'semantic_selector_profile':p['semantic_selector_profile'],
            'required_hidden_info_evidence':bool(p['required_hidden_info_evidence']),
            'required_rng_evidence':bool(p['required_rng_evidence']),
            'required_replay_evidence':bool(p['required_replay_evidence']),
            'required_decision_evidence':bool(p['required_decision_evidence']),
            'evidence_class':'CODE_DERIVED_INPUT',
        }
        rows.append(row)
    out={'schema':'commander-simulator-next.ws31-cases.v1','forge_pin':FORGE_PIN,'owner_family':FAMILY,'path_count':len(rows),'cases':rows}
    pathlib.Path(ns.out_json).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    with pathlib.Path(ns.out_tsv).open('w',encoding='utf-8') as f:
        for r in rows:
            vals=[str(r['ordinal']),r['v2_path_id'],r['oracle_identity'],r['card_name'],r['dispatch_token'],r['implementation_target'],r['source_path'],str(r['source_line']),r['source_directive'],r['source_token'],
                  '1' if r['required_hidden_info_evidence'] else '0','1' if r['required_rng_evidence'] else '0','1' if r['required_replay_evidence'] else '0','1' if r['required_decision_evidence'] else '0',
                  base64.b64encode(r['exact_script'].encode()).decode()]
            f.write('\t'.join(vals)+'\n')
    print(f'WS31_CASES={len(rows)}')
    print('WS31_PARTITION_UNCHANGED=TRUE')
    return 0
if __name__=='__main__': raise SystemExit(main())
