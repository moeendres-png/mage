#!/usr/bin/env python3
"""Fail-closed Actual-Card Oracle-ID corpus materializer."""
from __future__ import annotations
import argparse, base64, gzip, hashlib, json, uuid
from pathlib import Path
from typing import Any

SCHEMA="commander-simulator-next.actual-card-requirement-union.v2"
def sha256(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p:Path)->Any:
 v=json.loads(p.read_text(encoding="utf-8"))
 if isinstance(v,dict) and v.get("schema")=="commander-simulator-next.json-gzip-envelope.v1":
  if v.get("encoding")!="gzip+base64":raise ValueError(f"{p}: unsupported envelope encoding")
  try:r=gzip.decompress(base64.b64decode(v["payload_base64"],validate=True))
  except Exception as e:raise ValueError(f"{p}: invalid compressed envelope: {e!r}") from e
  if hashlib.sha256(r).hexdigest()!=v.get("payload_sha256"):raise ValueError(f"{p}: envelope payload hash mismatch")
  return json.loads(r.decode())
 return v
def fail(a:list[str],s:str):a.append(s)

def chunk_members(f:dict,p:Path,problems:list[str])->tuple[set[str],list[int]]:
 ids:list[str]=[]; qty:list[int]=[]; chunks=f.get("membership_chunks")
 if not isinstance(chunks,list) or not chunks:fail(problems,f"{p.name}: missing membership_chunks");return set(),[]
 for c in chunks:
  cp=p.parent/c.get("path","") if isinstance(c,dict) else p
  if not cp.exists():fail(problems,f"{p.name}: absent membership chunk {cp.name}");continue
  if sha256(cp)!=c.get("sha256"):fail(problems,f"{p.name}: chunk hash mismatch {cp.name}");continue
  try:r=base64.b64decode(cp.read_text().strip(),validate=True)
  except Exception as e:fail(problems,f"{p.name}: invalid chunk {cp.name}: {e!r}");continue
  if c.get("encoding")!="uuid16+uint16-quantity-base64-v1" or len(r)%18:fail(problems,f"{p.name}: invalid chunk encoding {cp.name}");continue
  pairs=[r[i:i+18] for i in range(0,len(r),18)]
  if c.get("count")!=len(pairs):fail(problems,f"{p.name}: chunk count mismatch {cp.name}")
  for x in pairs:ids.append(str(uuid.UUID(bytes=x[:16])));qty.append(int.from_bytes(x[16:],"big"))
 if ids!=sorted(ids) or len(ids)!=len(set(ids)):fail(problems,f"{p.name}: compact Oracle IDs are not sorted unique")
 return set(ids),qty

def canonical_union_members(cfg:dict, manifest_path:Path, byid:dict[str,Any], problems:list[str])->tuple[list[list[Any]],dict[str,set[str]]]:
 chunks=cfg.get("canonical_union_chunks")
 bits={"operational_own":1,"rogshai":2,"kaervek":4,"dargo_tymna":8,"official_precons":16}
 if not isinstance(chunks,list) or not chunks: fail(problems,"manifest missing canonical_union_chunks"); return [],{k:set() for k in bits}
 members=[]; prev=""; seen=set(); allowed=sum(bits.values())
 for c in chunks:
  cp=manifest_path.parent/c.get("path","") if isinstance(c,dict) else manifest_path
  if not cp.exists(): fail(problems,f"absent union chunk {cp.name}"); continue
  if sha256(cp)!=c.get("sha256"): fail(problems,f"union chunk hash mismatch {cp.name}"); continue
  try:r=base64.b64decode(cp.read_text().strip(),validate=True)
  except Exception as e: fail(problems,f"invalid union chunk {cp.name}: {e!r}"); continue
  if c.get("encoding")!="uuid16-mask8-base64-v1" or len(r)%17: fail(problems,f"invalid union chunk encoding {cp.name}"); continue
  rows=[r[i:i+17] for i in range(0,len(r),17)]
  if c.get("count")!=len(rows): fail(problems,f"union chunk count mismatch {cp.name}")
  for x in rows:
   oid=str(uuid.UUID(bytes=x[:16])); mask=x[16]
   if oid in seen or oid<=prev: fail(problems,"canonical union IDs not globally sorted unique")
   if oid not in byid: fail(problems,f"canonical union oracle_id not in pinned index: {oid}")
   if mask==0 or mask & ~allowed: fail(problems,f"invalid source mask for {oid}: {mask}")
   seen.add(oid); prev=oid; members.append([oid,mask])
 sets={sc:{oid for oid,mask in members if mask & bit} for sc,bit in bits.items()}
 return members,sets

def materialize(manifest_path:Path,index_path:Path,head:str,tree:str,forge:str)->dict[str,Any]:
 m=load(manifest_path); cfg=m.get("oracle_union") or {}; target=cfg.get("target_count")
 if not isinstance(target,int):raise ValueError("manifest must define oracle_union.target_count")
 required=cfg.get("source_classes") or []; known=cfg.get("known_source_files") or []; unknown=cfg.get("unknown_source_files") or []
 if not all(isinstance(x,str) for x in required+known+unknown):raise ValueError("manifest source lists must contain strings")
 idx=load(index_path); cards=idx.get("cards")
 if not isinstance(cards,list) or idx.get("oracle_identity_count")!=len(cards):raise ValueError("Scryfall index count mismatch")
 if idx.get("source_head")!=head or idx.get("source_tree")!=tree:raise ValueError("Scryfall index provenance mismatch")
 byid={r.get("oracle_id"):r for r in cards if isinstance(r,dict) and isinstance(r.get("oracle_id"),str)}
 if len(byid)!=len(cards):raise ValueError("Scryfall index duplicate/invalid IDs")
 problems:list[str]=[]; absent:list[str]=[]; canonical_members,mask_sets=canonical_union_members(cfg,manifest_path,byid,problems); sets:dict[str,set[str]]={}; rows=[]; seen=set(); unknown_slots=0
 for rel in known:
  p=manifest_path.parent/rel
  if not p.exists():absent.append(rel);continue
  f=load(p); sc=f.get("source_class")
  if not isinstance(sc,str) or sc in seen:fail(problems,f"{rel}: invalid/duplicate source_class");continue
  seen.add(sc)
  if f.get("status")!="PASS" or not f.get("provenance"):fail(problems,f"{rel}: status/provenance invalid")
  pol=f.get("resolution_policy") or {}
  if pol.get("fuzzy_matching") is not False or pol.get("synthetic_promotion") is not False:fail(problems,f"{rel}: forbidden fuzzy/synthetic policy")
  ids:set[str]=set(); rec=f.get("records"); qty=[]
  if isinstance(rec,list):
   if f.get("record_count")!=len(rec) or f.get("expected_record_count")!=len(rec):fail(problems,f"{rel}: record count mismatch")
   for i,r in enumerate(rec):
    oid=r.get("oracle_id") if isinstance(r,dict) else None
    if oid not in byid:fail(problems,f"{rel}: oracle_id not in pinned index at {i}");continue
    if r.get("oracle_name")!=byid[oid].get("name"):fail(problems,f"{rel}: canonical name mismatch {oid}")
    ids.add(oid);qty.append(r.get("quantity",1))
  else:
   ev=f.get("resolution_evidence") or {}
   if ev.get("missing")!=0 or ev.get("ambiguous")!=0 or ev.get("resolved_records")!=f.get("record_count") or f.get("record_count")!=f.get("expected_record_count"):fail(problems,f"{rel}: compact resolution evidence incomplete")
   if f.get("membership_authority")!="ACTUAL_CARD_REQUIREMENT_UNION.source_class_mask":fail(problems,f"{rel}: missing union-mask membership authority")
   ids=set(mask_sets.get(sc,set()));qty=[]
  if f.get("distinct_oracle_ids")!=len(ids):fail(problems,f"{rel}: distinct_oracle_ids mismatch")
  if isinstance(rec,list) and ids!=mask_sets.get(sc,set()):fail(problems,f"{rel}: record membership differs from canonical union mask")
  if "expected_slot_count" in f and (f.get("slot_count")!=f.get("expected_slot_count") or (qty and sum(qty)!=f.get("slot_count"))):fail(problems,f"{rel}: slot count mismatch")
  for oid in ids:
   if oid not in byid:fail(problems,f"{rel}: oracle_id not in pinned index: {oid}")
  sets[sc]=ids;rows.append({"path":rel,"sha256":sha256(p),"source_class":sc,"oracle_id_count":len(ids)})
 for rel in unknown:
  p=manifest_path.parent/rel
  if not p.exists():absent.append(rel);continue
  f=load(p);sc=f.get("source_class")
  if not isinstance(sc,str) or sc in seen:fail(problems,f"{rel}: invalid/duplicate source_class");continue
  seen.add(sc); slots=f.get("slots")
  if f.get("status")!="PASS" or not f.get("provenance") or f.get("synthetic_promotion") is not False or f.get("oracle_id_promotion_performed") is not False:fail(problems,f"{rel}: UNKNOWN fragment invalid")
  if not isinstance(slots,list) or f.get("slot_count")!=len(slots):fail(problems,f"{rel}: UNKNOWN slot count mismatch");slots=[]
  sids=set()
  for s in slots:
   sid=s.get("slot_id") if isinstance(s,dict) else None
   if not sid or sid in sids or s.get("resolution_status")!="UNKNOWN" or s.get("oracle_id") is not None:fail(problems,f"{rel}: invalid/promoted UNKNOWN slot")
   sids.add(sid)
  unknown_slots+=len(slots);sets[sc]=set();rows.append({"path":rel,"sha256":sha256(p),"source_class":sc,"unknown_slot_count":len(slots),"oracle_id_count":0})
 if seen!=set(required):fail(problems,f"source classes mismatch: seen={sorted(seen)} required={sorted(required)}")
 recon="MISSING"; rr=cfg.get("official_precon_reconciliation")
 if isinstance(rr,str) and (manifest_path.parent/rr).exists():
  r=load(manifest_path.parent/rr);recon=str(r.get("status"))
  if recon!="PASS" or r.get("deck_count")!=11 or r.get("all_100_slots") is not True:fail(problems,"official precon reconciliation is not PASS/11x100")
 else: absent.append(str(rr));fail(problems,"manifest/reconciliation missing")
 ids={oid for oid,_ in canonical_members}
 bits={"operational_own":1,"rogshai":2,"kaervek":4,"dargo_tymna":8,"official_precons":16}; members=canonical_members
 derived=set().union(*(v for k,v in sets.items() if k!="unknown_real_opponents")) if sets else set()
 if derived!=ids:fail(problems,"source fragments do not account for canonical union membership")
 if len(ids)!=target:fail(problems,f"computed Oracle-ID count {len(ids)} != target {target}")
 status="NOT_RUN" if absent else ("PASS" if not problems else "FAIL")
 gate={"target_count_equal":len(ids)==target,"all_required_source_classes_accounted_for":seen==set(required),"source_provenance_complete":not any("provenance" in x for x in problems),"all_ids_in_pinned_index":not any("pinned index" in x for x in problems),"ambiguous_promotions":0,"fuzzy_matching":False,"synthetic_promotion":False,"known_source_missing_or_ambiguous":0 if not problems else sum("oracle_id" in x or "canonical name" in x for x in problems),"official_precon_reconciliation":recon,"explicit_unknown_slots_accounted_for":unknown_slots>0 and not any("UNKNOWN" in x for x in problems)}
 return {"schema":SCHEMA,"status":status,"complete":status=="PASS","source_head":head,"source_tree":tree,"external_pins":{"forge":forge,"scryfall_index_sha256":sha256(index_path)},"target_count":target,"computed_oracle_id_count":len(ids),"source_class_mask_bits":bits,"unknown_real_opponent_slots":unknown_slots,"unknown_slots_promoted_to_oracle_ids":0,"target_correction":cfg.get("historical_target_correction"),"source_rows":rows,"missing_sources":absent,"problems":problems,"members":members,"member_chunks":cfg.get("canonical_union_chunks",[]),"gate":gate}

def main()->int:
 a=argparse.ArgumentParser();a.add_argument("--manifest",required=True,type=Path);a.add_argument("--oracle-index",required=True,type=Path);a.add_argument("--source-head",required=True);a.add_argument("--source-tree",required=True);a.add_argument("--forge-pin",required=True);a.add_argument("--out",required=True,type=Path);x=a.parse_args()
 r=materialize(x.manifest,x.oracle_index,x.source_head,x.source_tree,x.forge_pin);x.out.parent.mkdir(parents=True,exist_ok=True);x.out.write_text(json.dumps(r,sort_keys=True,separators=(",",":"))+"\n");print(json.dumps({"status":r["status"],"target_count":r["target_count"],"computed_oracle_id_count":r["computed_oracle_id_count"],"problems":len(r["problems"])},sort_keys=True));return {"PASS":0,"FAIL":1,"NOT_RUN":2}[r["status"]]
if __name__=="__main__":raise SystemExit(main())
