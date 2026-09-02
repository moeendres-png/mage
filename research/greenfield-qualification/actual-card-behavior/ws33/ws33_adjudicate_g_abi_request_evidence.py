#!/usr/bin/env python3
"""Fail-closed WS33 G request/RNG ABI evidence adjudicator.

This validates retained authoritative request metadata. It does not infer Magic
legality: legal options come exclusively from ExternalDecisionRequest traces.
"""
from __future__ import annotations
import argparse, base64, json, re
from collections import defaultdict
from pathlib import Path

OPAQUE_OPTION = re.compile(r"^(?:card|player|entity|choice):[0-9]+$")

class EvidenceError(RuntimeError): pass

def need(c, m):
    if not c: raise EvidenceError(m)

def dec(s: str) -> str:
    try: return base64.b64decode(s, validate=True).decode("utf-8")
    except Exception as e: raise EvidenceError(f"invalid base64/utf8 field: {s!r}") from e

def lines(p: Path):
    need(p.is_file(), f"missing evidence file: {p}")
    return [x for x in p.read_text(encoding="utf-8").splitlines() if x]

def parse_cases(p: Path):
    out={}
    for n,line in enumerate(lines(p),1):
        f=line.split("\t")
        need(len(f) >= 14, f"cases row {n}: expected >=14 columns, got {len(f)}")
        path=f[1]; need(path and path not in out, f"cases row {n}: duplicate/empty path {path!r}")
        need(f[11] in {"0","1"} and f[13] in {"0","1"}, f"cases row {n}: invalid requirement flags")
        out[path]={"rng":f[11]=="1","decision":f[13]=="1"}
    return out

def parse_requests(p: Path, cases):
    by_identity={}; by_path=defaultdict(list)
    for n,line in enumerate(lines(p),1):
        f=line.split("\t",-1); need(len(f)==13, f"request row {n}: expected 13 columns, got {len(f)}")
        path=dec(f[0]); need(path in cases, f"request row {n}: unknown path {path}")
        decision_id=int(f[1]); token=int(f[2]); kind=dec(f[3]); actor=int(f[4]); principal=int(f[5]); visibility=dec(f[6])
        minimum=int(f[7]); maximum=int(f[8]); need(f[9] in {"true","false"}, f"request row {n}: invalid cancel flag")
        cancel=f[9]=="true"; response_schema=dec(f[10]); count=int(f[11])
        options=[] if count==0 else [dec(x) for x in f[12].split(",")]
        need(decision_id>0 and token>0, f"request row {n}: non-positive id/token")
        need(decision_id==token, f"request row {n}: decision/token contract mismatch {decision_id}/{token}")
        need(actor>=0 and principal>=0, f"request row {n}: invalid actor/principal")
        need(kind and response_schema, f"request row {n}: blank kind/schema")
        need(visibility=="PRINCIPAL_ONLY", f"request row {n}: visibility={visibility}")
        need(count>=0 and len(options)==count and len(set(options))==count, f"request row {n}: option cardinality/uniqueness")
        need(0<=minimum<=maximum<=count, f"request row {n}: selection bounds {minimum}/{maximum}/{count}")
        need(all(OPAQUE_OPTION.fullmatch(x) for x in options), f"request row {n}: non-opaque option id")
        ident=(principal,token)
        need(ident not in by_identity, f"request row {n}: duplicate principal-scoped token {ident}")
        row={"path_id":path,"decision_id":decision_id,"token":token,"decision_kind":kind,"actor":actor,"principal":principal,
             "visibility_scope":visibility,"minimum_selection":minimum,"maximum_selection":maximum,"cancel_allowed":cancel,
             "response_schema":response_schema,"authoritative_legal_options":options}
        by_identity[ident]=row; by_path[path].append(row)
    return by_identity,by_path

def parse_event_paths(p: Path):
    out={}
    for n,line in enumerate(lines(p),1):
        f=line.split("\t",-1); need(len(f)==7, f"decision-event row {n}: expected 7 columns")
        path=dec(f[0]); event_id=int(f[1]); kind=dec(f[2]); actor=int(f[3]); principal=int(f[4]); status=f[5]; error=dec(f[6])
        need(event_id>0 and event_id not in out, f"decision-event row {n}: duplicate/invalid event id")
        out[event_id]={"path":path,"kind":kind,"actor":actor,"principal":principal,"status":status,"error":error}
    return out

def correlate_tape(p: Path, event_paths, requests, cases):
    accepted=defaultdict(list)
    for n,line in enumerate(lines(p),1):
        f=line.split("\t",-1); need(len(f)==8, f"decision-tape row {n}: expected 8 columns")
        event_id=int(f[0]); decision_id=int(f[1]); token=int(f[2]); kind=dec(f[3]); actor=int(f[4]); principal=int(f[5]); count=int(f[6])
        selected=[] if count==0 else [dec(x) for x in f[7].split(",")]
        need(len(selected)==count and len(set(selected))==count, f"decision-tape row {n}: selected cardinality/uniqueness")
        ev=event_paths.get(event_id); need(ev is not None, f"decision-tape row {n}: event {event_id} missing path metadata")
        need((kind,actor,principal)==(ev['kind'],ev['actor'],ev['principal']), f"decision-tape row {n}: event metadata mismatch")
        if ev['path'] not in cases: continue
        need(ev['status']=="ACCEPTED" and ev['error']=="null", f"decision-tape row {n}: non-accepted campaign event")
        req=requests.get((principal,token)); need(req is not None, f"decision-tape row {n}: no request for principal/token {(principal,token)}")
        need((decision_id,kind,actor)==(req['decision_id'],req['decision_kind'],req['actor']), f"decision-tape row {n}: request envelope mismatch")
        need(ev['path']==req['path_id'], f"decision-tape row {n}: path/request mismatch {ev['path']} != {req['path_id']}")
        legal=set(req['authoritative_legal_options']); need(all(x in legal for x in selected), f"decision-tape row {n}: selected option outside authoritative set")
        need(req['minimum_selection']<=len(selected)<=req['maximum_selection'], f"decision-tape row {n}: selected count outside request bounds")
        accepted[ev['path']].append({"principal":principal,"token":token,"decision_id":decision_id,"selected":selected})
    return accepted

def parse_rng(p: Path, cases):
    out=defaultdict(list); last={}
    for n,line in enumerate(lines(p),1):
        f=line.split("\t",-1); need(len(f)==7, f"rng row {n}: expected 7 columns")
        path=dec(f[0]); idx=int(f[1]); game=dec(f[2]); stream=dec(f[3]); draw=int(f[4]); bits=int(f[5]); result=int(f[6])
        need(idx>0 and game and stream and draw>=0 and bits>0, f"rng row {n}: invalid event fields")
        key=(game,stream); prev=last.get(key)
        if prev is not None: need(draw==prev+1, f"rng row {n}: non-contiguous draw position for {key}: {prev}->{draw}")
        last[key]=draw
        if path in cases:
            out[path].append({"event_index":idx,"game_id":game,"stream":stream,"draw_index":draw,"bits":bits,"result":result,
                              "pre_state":f"{game}|{stream}|draw={draw}","post_state":f"{game}|{stream}|draw={draw+1}","operation":f"next({bits})"})
    return out

def adjudicate(a):
    cases=parse_cases(a.cases); need(len(cases)==a.expected_paths, f"expected {a.expected_paths} cases, got {len(cases)}")
    req_dec={p for p,x in cases.items() if x['decision']}; req_rng={p for p,x in cases.items() if x['rng']}
    need(len(req_dec)==a.expected_decision_paths, f"expected {a.expected_decision_paths} decision-required paths, got {len(req_dec)}")
    need(len(req_rng)==a.expected_rng_paths, f"expected {a.expected_rng_paths} rng-required paths, got {len(req_rng)}")
    need(a.record_requests.read_bytes()==a.replay_requests.read_bytes(), "Record/Replay request traces differ")
    requests,path_requests=parse_requests(a.record_requests,cases)
    accepted=correlate_tape(a.decision_tape,parse_event_paths(a.decision_events),requests,cases)
    missing=sorted(p for p in req_dec if not accepted[p]); need(not missing, f"decision-required paths without accepted request/tape evidence: {missing}")
    need(all(path_requests[p] for p in req_dec), "decision-required path without authoritative request trace")
    rng=parse_rng(a.rng_events,cases); missing_rng=sorted(p for p in req_rng if not rng[p]); need(not missing_rng, f"rng-required paths without events: {missing_rng}")
    out={"schema":"commander-simulator-next.ws33-g-abi-request-evidence.v2","status":"PASS","behavior_artifact_id":a.behavior_artifact_id,
         "behavior_artifact_digest":a.behavior_artifact_digest,"behavior_source_head":a.behavior_source_head,"model_artifact_id":a.model_artifact_id,
         "effective_model_sha256":a.effective_model_sha256,"path_count":len(cases),"decision_required_path_count":len(req_dec),
         "decision_required_paths_observed":sum(bool(accepted[p]) for p in req_dec),"rng_required_path_count":len(req_rng),
         "rng_required_paths_observed":sum(bool(rng[p]) for p in req_rng),"request_event_count":sum(map(len,path_requests.values())),
         "record_replay_request_trace_equal":True,"authoritative_legal_options_captured_from_request":True,"request_identity_scope":"principal_id+token",
         "request_envelope_cross_checked":["decision_id","decision_kind","actor_id","principal_id","token"],"hidden_identity_payload_retained":False,
         "minimum_requirement_semantics":True,"rng_pre_post_state_basis":"CODE_DERIVED_NAMED_STREAM_DRAW_POSITION","coverage_mutated":False,
         "silent_fallback":False}
    a.out_dir.mkdir(parents=True,exist_ok=True)
    (a.out_dir/'WS33_G_ABI_REQUEST_EVIDENCE.json').write_text(json.dumps(out,sort_keys=True,separators=(',',':'))+'\n')
    (a.out_dir/'decision-requests.json').write_text(json.dumps({'schema':'commander-simulator-next.ws33-g-authoritative-requests.v2','events':[x for p in sorted(path_requests) for x in path_requests[p]]},sort_keys=True,separators=(',',':'))+'\n')
    (a.out_dir/'rng-abi-events.json').write_text(json.dumps({'events':[{'path_id':p,**e} for p in sorted(rng) for e in rng[p]]},sort_keys=True,separators=(',',':'))+'\n')
    return out

def cli():
    p=argparse.ArgumentParser()
    for name in ('cases','record_requests','replay_requests','decision_events','decision_tape','rng_events','out_dir'): p.add_argument('--'+name.replace('_','-'),type=Path,required=True)
    p.add_argument('--expected-paths',type=int,required=True); p.add_argument('--expected-decision-paths',type=int,required=True); p.add_argument('--expected-rng-paths',type=int,required=True)
    for name in ('behavior_artifact_id','behavior_artifact_digest','behavior_source_head','model_artifact_id','effective_model_sha256'): p.add_argument('--'+name.replace('_','-'),required=True)
    a=p.parse_args()
    try: out=adjudicate(a)
    except (EvidenceError,ValueError) as e: raise SystemExit(f"WS33_G_ABI_REQUEST_EVIDENCE=FAIL {e}")
    print('WS33_G_ABI_REQUEST_EVIDENCE=PASS '+json.dumps(out,sort_keys=True))
if __name__=='__main__': cli()
