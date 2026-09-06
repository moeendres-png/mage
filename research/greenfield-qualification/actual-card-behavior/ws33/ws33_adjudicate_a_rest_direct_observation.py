#!/usr/bin/env python3
"""Adjudicate principal-scoped hidden observation for exact A-rest Direct31 evidence.

This verifier never infers target legality. It validates only runtime evidence emitted by
pinned Forge: exact path coverage, zero leak/cross-principal deltas, strict temporary
identity lifecycles when Forge actually grants hidden identity, and fresh record/replay
equality. No positive observation is manufactured for public-zone target paths.
"""
from __future__ import annotations
import argparse, json
from collections import Counter, defaultdict
from pathlib import Path


def fail(msg: str) -> None:
    raise SystemExit("WS33_A_REST_DIRECT_OBSERVATION_GATE=FAIL " + msg)


def load_jsonl(p: Path) -> list[dict]:
    if not p.is_file(): return []
    return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]


def load_cases(p: Path) -> dict[str,list[str]]:
    out={}
    for n,line in enumerate(p.read_text(encoding='utf-8').splitlines(),1):
        if not line.strip(): continue
        f=line.split('\t')
        if len(f)!=19: fail(f'case ABI line={n} columns={len(f)}')
        pid=f[1]
        if pid in out: fail('duplicate case '+pid)
        if f[15]!='1' or f[17]!='1' or f[18]!='1': fail('case evidence flags not decision+hidden+replay '+pid)
        out[pid]=f
    if len(out)!=31: fail(f'case count={len(out)}')
    return out


def load_summary(p: Path) -> dict[str,list[str]]:
    out={}
    for line in p.read_text(encoding='utf-8').splitlines():
        if not line.strip(): continue
        f=line.split('\t'); pid=f[0]
        if pid in out: fail('duplicate summary '+pid)
        out[pid]=f
    return out


def summary_gate(label: str, rows: dict[str,list[str]], cases: dict[str,list[str]], failures:list[str]) -> None:
    if set(rows)!=set(cases): failures.append(label+':path_set_mismatch')
    for pid in sorted(set(rows)&set(cases)):
        r=rows[pid]; c=cases[pid]
        if len(r)<21: failures.append(f'{pid}:{label}:summary_columns={len(r)}'); continue
        if r[4]!='PASS': failures.append(f'{pid}:{label}:status={r[4]}')
        if int(r[9])!=0: failures.append(f'{pid}:{label}:pilot_visible_leak={r[9]}')
        if int(r[10])!=0: failures.append(f'{pid}:{label}:cross_principal_leak={r[10]}')
        if int(r[18])!=1 or int(r[19])!=1 or int(r[20])<1: failures.append(f'{pid}:{label}:stack_source_root')
        if c[15]=='1' and int(r[7])<=0: failures.append(f'{pid}:{label}:missing_decision')
        if c[16]=='1' and int(r[8])<=0: failures.append(f'{pid}:{label}:missing_rng')
        if r[14] or r[15]: failures.append(f'{pid}:{label}:runtime_failure')


def event_gate(label: str, events:list[dict], cases:dict[str,list[str]], failures:list[str]) -> Counter:
    kinds=Counter(); streams=defaultdict(list)
    for e in events:
        pid=e.get('path_id')
        if pid not in cases: failures.append(f'{label}:unknown_path={pid}'); continue
        if e.get('identity_match') is not True: failures.append(f'{label}:identity_mismatch={pid}:{e.get("principal_id")}:{e.get("card_id")}')
        kind=e.get('kind'); kinds[kind]+=1
        if kind in {'SERVER_GRANT','CLIENT_VISIBLE','SERVER_REVOKE','CLIENT_HIDDEN'}:
            try: key=(pid,int(e['principal_id']),int(e['card_id']))
            except Exception: failures.append(f'{label}:bad_stream_identity={pid}'); continue
            streams[key].append(e)
    for (pid,principal,card), stream in streams.items():
        state='HIDDEN'
        for e in sorted(stream,key=lambda x:int(x.get('sequence',-1))):
            kind=e.get('kind')
            expected={'HIDDEN':'SERVER_GRANT','GRANTED':'CLIENT_VISIBLE','VISIBLE':'SERVER_REVOKE','REVOKED':'CLIENT_HIDDEN'}[state]
            if kind!=expected:
                failures.append(f'{pid}:{label}:lifecycle:{principal}:{card}:expected={expected}:actual={kind}')
                break
            state={'HIDDEN':'GRANTED','GRANTED':'VISIBLE','VISIBLE':'REVOKED','REVOKED':'HIDDEN'}[state]
        if state!='HIDDEN': failures.append(f'{pid}:{label}:incomplete_lifecycle:{principal}:{card}:{state}')
    return kinds


def normalized(events:list[dict]) -> Counter:
    return Counter((e.get('path_id'),e.get('kind'),int(e.get('principal_id',-1)),int(e.get('card_id',-1)),e.get('decision_kind',''),bool(e.get('identity_match'))) for e in events)


def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument('--cases',type=Path,required=True); ap.add_argument('--record-dir',type=Path,required=True); ap.add_argument('--replay-dir',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    cases=load_cases(a.cases); recs=load_summary(a.record_dir/'case-summary.tsv'); reps=load_summary(a.replay_dir/'case-summary.tsv')
    failures=[]; summary_gate('record',recs,cases,failures); summary_gate('replay',reps,cases,failures)
    for pid in sorted(set(recs)&set(reps)&set(cases)):
        x,y=recs[pid],reps[pid]
        if len(x)>=21 and len(y)>=21:
            if x[5]!=y[5] or x[6]!=y[6]: failures.append(pid+':semantic_digest_mismatch')
            if x[7]!=y[7] or x[8]!=y[8]: failures.append(pid+':decision_rng_count_mismatch')
    rec=load_jsonl(a.record_dir/'PRINCIPAL_OBSERVATIONS.jsonl'); rep=load_jsonl(a.replay_dir/'PRINCIPAL_OBSERVATIONS.jsonl')
    if not rec: failures.append('record_observations_empty')
    if not rep: failures.append('replay_observations_empty')
    rk=event_gate('record',rec,cases,failures); pk=event_gate('replay',rep,cases,failures)
    if normalized(rec)!=normalized(rep): failures.append('record_replay_observation_multiset_mismatch')
    out={'schema':'commander-simulator-next.ws33-a-rest-direct31-principal-observation.v1','status':'PASS' if not failures else 'FAIL_CLOSED','expected_paths':31,'hidden_required_paths':31,'record_event_count':len(rec),'replay_event_count':len(rep),'record_event_kinds':dict(sorted(rk.items())),'replay_event_kinds':dict(sorted(pk.items())),'record_observed_path_count':len({e.get('path_id') for e in rec if e.get('path_id') in cases}),'replay_observed_path_count':len({e.get('path_id') for e in rep if e.get('path_id') in cases}),'positive_observation_policy':'ONLY_WHEN_FORGE_GRANTS_HIDDEN_IDENTITY','unauthorized_hidden_leak_required':0,'cross_principal_leak_required':0,'failure_count':len(failures),'failures':failures,'rules_mutation':False,'coverage_mutated':False,'coverage_promotion':False}
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(out,sort_keys=True))
    if failures: fail(';'.join(failures[:20]))
    print('WS33_A_REST_DIRECT_OBSERVATION_GATE=PASS')

if __name__=='__main__': main()
