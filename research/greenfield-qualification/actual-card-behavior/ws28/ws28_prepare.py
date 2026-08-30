#!/usr/bin/env python3
from __future__ import annotations
import argparse, base64, json, re
from pathlib import Path
from collections import defaultdict, Counter

OWNER="TRIGGER_REPLACEMENT_ZONE_SBA"
FORGE_PIN="8c7e9afb8e6caee88644b94e25da5852e36f8928"
WS26_HEAD="206a39cbaa3eeb98b10c2ddc36d51fe5b1b2f5ef"
WS26_TREE="837f445f78bb26462653c58baf1532e294151b10"
REUSE={
"forge-behavior-v2:54347338c1bf4c71f825a53f10e281dabedc7f31":"forge-primitive-v1:5f99c3f437013e47c874b90e66bc3074",
"forge-behavior-v2:4baa2f32c0c4c3af046a54fb027ef824bb6d33b4":"forge-primitive-v1:affff0f8993d9b11ad9f1fb7cae35907",
}

def load(p:Path): return json.loads(p.read_text(encoding="utf-8"))
def b64(s:str)->str: return base64.b64encode(s.encode()).decode()

def parse_params(body:str):
    out={}
    for part in body.split(" | "):
        if "$" not in part: continue
        k,v=part.split("$",1)
        out[k.strip()]=v.strip()
    return out

def parse_records(lines):
    recs=[]
    for i,line in enumerate(lines,1):
        raw=line.strip()
        if not raw or raw.startswith("#"): continue
        kind=None; name=None; body=None
        if raw.startswith("SVar:"):
            bits=raw.split(":",2)
            if len(bits)==3:
                kind="SVAR"; name=bits[1].strip(); body=bits[2].strip()
        elif len(raw)>=2 and raw[1]==":" and raw[0] in "ASTRK":
            kind=raw[0]; body=raw[2:].strip()
        if kind:
            recs.append({"line":i,"raw":raw,"kind":kind,"name":name,"body":body,"params":parse_params(body)})
    return recs

def root_for(target,recs):
    if target["kind"]!="SVAR": return target, [target["line"]]
    by_name={r["name"]:r for r in recs if r["kind"]=="SVAR" and r["name"]}
    symbols=set(by_name)
    rev=defaultdict(list)
    for r in recs:
        refs=set(re.findall(r"[A-Za-z][A-Za-z0-9_]*", r["body"])) & symbols
        for sym in refs:
            if r["kind"]=="SVAR" and r.get("name")==sym:
                continue
            rev[sym].append((r,"TOKEN_REFERENCE"))
    seen=set()
    q=[(target["name"],[target["line"]])]
    candidates=[]
    while q:
        sym,chain=q.pop(0)
        if sym in seen: continue
        seen.add(sym)
        for parent,key in rev.get(sym,[]):
            ch=chain+[parent["line"]]
            if parent["kind"]!="SVAR":
                candidates.append((parent,ch,key))
            elif parent["name"]:
                q.append((parent["name"],ch))
    if not candidates: return None,[target["line"]]
    candidates.sort(key=lambda x:(len(x[1]),x[0]["line"]))
    return candidates[0][0], candidates[0][1]

def root_token(root):
    if not root: return "",""
    p=root["params"]
    if root["kind"]=="A":
        if "SP" in p: return "SP",p["SP"]
        if "AB" in p: return "AB",p["AB"]
        if "DB" in p: return "DB",p["DB"]
    if root["kind"]=="S":
        for key in ("AddAbility","AddTrigger","AddReplacementEffect","AddStaticAbility","AddSVar","Mode"):
            if key in p:
                return key,p[key]
    if root["kind"]=="T": return "Mode",p.get("Mode","")
    if root["kind"]=="R": return "Event",p.get("Event","")
    if root["kind"]=="K": return "Keyword",root["body"]
    return "",""

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--ws26-dir",type=Path,required=True)
    ap.add_argument("--forge-root",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    m=load(a.ws26_dir/"WS26_BEHAVIOR_PATH_MANIFEST_V2.json")
    part=load(a.ws26_dir/"WS26_OWNER_PARTITIONS.json")
    compat=load(a.ws26_dir/"WS26_EXISTING_WITNESS_COMPATIBILITY.json")
    if m["forge_pin"]!=FORGE_PIN or m["source_head"]!=WS26_HEAD or m["source_tree"]!=WS26_TREE or m["path_count"]!=4280:
        raise SystemExit("WS26 boundary mismatch")
    ids=part["families"][OWNER]["v2_path_ids"]
    if part["families"][OWNER]["path_count"]!=1174 or len(ids)!=1174 or len(set(ids))!=1174:
        raise SystemExit("owner partition mismatch")
    paths={x["v2_path_id"]:x for x in m["paths"]}
    if set(ids)!={x["v2_path_id"] for x in m["paths"] if x["owner_family"]==OWNER}:
        raise SystemExit("owner partition not exact")
    reusable={}
    for e in compat["entries"]:
        if e.get("v2_compatibility")=="REUSED_FOR_ONE_CHILD_PATH":
            pid=e.get("exact_v2_path_exercised")
            if pid:
                reusable[pid]=e
    if set(REUSE)!=set(reusable):
        raise SystemExit(f"unexpected compatibility reuse set: {sorted(reusable)}")
    for pid,parent in REUSE.items():
        if paths[pid]["parent_ws14_primitive_id"]!=parent:
            raise SystemExit("reused parent mismatch "+pid)
    names={}
    with (a.ws26_dir/"WS26_PER_IDENTITY_V2.jsonl").open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                r=json.loads(line); names[r["oracle_identity"]]=r["oracle_name"]

    a.out.mkdir(parents=True,exist_ok=True)
    rows=[]; unresolved=[]; kindc=Counter(); rootc=Counter()
    for pid in ids:
        path=paths[pid]
        if pid in REUSE: continue
        provs=path.get("source_provenance") or []
        if not provs:
            raise SystemExit("path lacks provenance "+pid)
        reps=set(path.get("representative_actual_oracle_identities") or [])
        prov=next((x for x in provs if x.get("oracle_identity") in reps),provs[0])
        oid=prov["oracle_identity"]; name=names.get(oid)
        if not name:
            raise SystemExit("missing oracle name "+oid)
        rel=prov["forge_source_path"]
        src=a.forge_root/rel
        if not src.is_file():
            raise SystemExit(f"missing pinned Forge source {rel}")
        lines=src.read_text(encoding="utf-8",errors="strict").splitlines()
        ln=int(prov["source_line"])
        if ln<1 or ln>len(lines): raise SystemExit("source line out of bounds")
        recs=parse_records(lines)
        target=next((r for r in recs if r["line"]==ln),None)
        if target is None:
            unresolved.append({"v2_path_id":pid,"reason":"SOURCE_LINE_NOT_RECORD","path":rel,"line":ln,"raw":lines[ln-1]})
            target={"line":ln,"raw":lines[ln-1].strip(),"kind":"UNKNOWN","name":None,"body":"","params":{}}
        root,chain=root_for(target,recs) if target["kind"]!="UNKNOWN" else (None,[ln])
        rk=root["kind"] if root else "UNKNOWN"
        rkey,rtok=root_token(root)
        kindc[target["kind"]]+=1; rootc[rk]+=1
        if root is None:
            unresolved.append({"v2_path_id":pid,"reason":"NO_PRODUCTION_ROOT","path":rel,"line":ln,"raw":target["raw"]})
        cols=[
            pid,path.get("parent_ws14_primitive_id") or "",oid,b64(name),
            path["dispatch_domain"],path["dispatch_token"],b64(path["implementation_target"]),
            "1" if path.get("required_decision_evidence") else "0",
            "1" if path.get("required_rng_evidence") else "0",
            "1" if path.get("required_hidden_info_evidence") else "0",
            "1" if path.get("required_replay_evidence") else "0",
            b64(rel),str(ln),b64(target["raw"]),target["kind"],b64(target.get("name") or ""),
            rk,b64(root["raw"] if root else ""),rkey,b64(rtok),
            ",".join(str(x) for x in chain),b64(json.dumps(path["semantic_selector_profile"],sort_keys=True,separators=(",",":")))
        ]
        rows.append("\t".join(cols))
    if len(rows)!=1172:
        raise SystemExit(f"expected 1172 non-reuse cases, got {len(rows)}")
    (a.out/"WS28_CASES.tsv").write_text("\n".join(rows)+"\n",encoding="utf-8")
    (a.out/"WS28_PREPARE_SUMMARY.json").write_text(json.dumps({
        "schema":"commander-simulator-next.ws28.prepare.v1",
        "owner_family":OWNER,
        "family_path_count":1174,
        "reused_exact_ws16_child_count":2,
        "new_execution_case_count":len(rows),
        "reuse_v2_path_ids":sorted(REUSE),
        "unresolved_root_count":len(unresolved),
        "target_record_kind_counts":dict(sorted(kindc.items())),
        "root_kind_counts":dict(sorted(rootc.items())),
        "unresolved":unresolved,
    },sort_keys=True,indent=2)+"\n",encoding="utf-8")
    if unresolved:
        raise SystemExit(f"WS28 production-root binding incomplete: {len(unresolved)} unresolved")
    print("WS28_PREPARE=PASS cases=1172 unresolved_roots=0")
if __name__=="__main__": main()
