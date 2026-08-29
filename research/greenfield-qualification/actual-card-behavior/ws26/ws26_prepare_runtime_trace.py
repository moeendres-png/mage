#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path


def rows(path: Path):
    for line in path.read_text(encoding='utf-8').splitlines():
        if line.strip():
            yield json.loads(line)


def forge_name(forge_root: Path, source_path: str) -> str:
    p = forge_root / source_path
    for line in p.read_text(encoding='utf-8', errors='strict').splitlines():
        if line.startswith('Name:'):
            return line.split(':', 1)[1].strip()
    raise SystemExit(f'no Name: in {source_path}')


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--unresolved', type=Path, required=True)
    ap.add_argument('--forge-root', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a=ap.parse_args()
    out=[]
    for i,r in enumerate(rows(a.unresolved)):
        if r['source_directive']!='KEYWORD':
            continue
        name=forge_name(a.forge_root,r['forge_source_path'])
        vals=[str(i),r['oracle_id'],name,r['forge_source_path'],str(r['source_line']),r['source_value']]
        if any('\t' in x or '\n' in x or '\r' in x for x in vals):
            raise SystemExit(f'unsafe TSV value for unresolved occurrence {i}')
        out.append('\t'.join(vals))
    if len(out)!=888:
        raise SystemExit(f'expected 888 keyword occurrences, got {len(out)}')
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text('\n'.join(out)+'\n',encoding='utf-8')
    print('WS26_KEYWORD_TRACE_INPUT=888')
if __name__=='__main__': main()
