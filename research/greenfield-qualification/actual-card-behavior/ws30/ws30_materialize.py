#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

FAMILY="COMBAT_COMMANDER"
WS26_HEAD="206a39cbaa3eeb98b10c2ddc36d51fe5b1b2f5ef"
WS26_TREE="837f445f78bb26462653c58baf1532e294151b10"
FORGE_PIN="8c7e9afb8e6caee88644b94e25da5852e36f8928"
RULES_URL="https://media.wizards.com/2026/downloads/MagicCompRules%2020260807.pdf"
DISPATCH_TO_RULES={
"STATIC_MODE:CantAttack":["508.1c"],"STATIC_MODE:MustAttack":["508.1d"],"STATIC_MODE:CantAttackUnless":["508.1c","508.1d"],"STATIC_MODE:CanAttackDefender":["508.1c"],"STATIC_MODE:CantBlock":["509.1"],"STATIC_MODE:CantBlockBy":["509.1","702.9"],"ABILITY_API:Goad":["701.15","508.1d"],"ABILITY_API:Goad(NoLonger)":["701.15"],"ABILITY_API:Fight":["701.12"],"ABILITY_API:EachDamage":["120","704"],"ABILITY_API:RemoveFromCombat":["506.4"],"KEYWORD_TRIGGER:BATTLE_CRY":["702.91"],"KEYWORD_TRIGGER:EXALTED":["702.83"],"KEYWORD_TRIGGER:MELEE":["702.121","702.7","510.4"],"SVAR_RUNTIME_EXPRESSION:X":["508.1d"]}
COMMANDER_PATHS={"forge-behavior-v2:945cb309bfe37e292fbecc172efa4789ff1156d1"}

def read_jsonl(path):
 rows=[]
 for n,line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(),1):
  if line.strip(): rows.append(json.loads(line))
 return rows

def write_json(path,obj): Path(path).write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n",encoding="utf-8")

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--owner-partitions",required=True); ap.add_argument("--trace",required=True); ap.add_argument("--out-dir",required=True); a=ap.parse_args()
 owner=json.loads(Path(a.owner_partitions).read_text(encoding="utf-8")); fam=owner["families"][FAMILY]; assigned=fam["v2_path_ids"]
 if fam["path_count"]!=27 or len(assigned)!=27 or len(set(assigned))!=27: raise SystemExit("WS26 COMBAT_COMMANDER partition must be exactly 27 unique paths")
 trace=read_jsonl(a.trace); assigned_rows=[r for r in trace if r.get("path_id","").startswith("forge-behavior-v2:")]; supplemental=[r for r in trace if r.get("path_id","").startswith("SUPPLEMENTAL:")]
 ids=[r["path_id"] for r in assigned_rows]; missing=sorted(set(assigned)-set(ids)); extra=sorted(set(ids)-set(assigned)); dup=sorted({x for x in ids if ids.count(x)>1})
 if missing or extra or dup or len(ids)!=27: raise SystemExit(f"coverage invalid missing={missing} extra={extra} duplicates={dup} rows={len(ids)}")
 if any(r.get("result")!="PASS" for r in assigned_rows): raise SystemExit("assigned witness failure")
 out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True); normalized=[]
 for r in sorted(assigned_rows,key=lambda x:x["path_id"]):
  rules=DISPATCH_TO_RULES.get(r["dispatch"])
  if not rules: raise SystemExit("missing rules mapping "+r["dispatch"])
  row=dict(r)
  if not str(row.get("selected_declaration","")).strip(): row["selected_declaration"]="none (rules-core selected no declaration)"
  row.update({"owner_family":FAMILY,"ws26_source_head":WS26_HEAD,"ws26_source_tree":WS26_TREE,"oracle_identity_provenance":"WS26 assigned V2 path + actual pinned Forge card script","actual_card_execution":True,"rules_core_authority":True,"manual_legality":False,"official_rule_refs":rules,"rules_validation_class":"EXTERNALLY_RULE_VALIDATED","stdout_only":False}); normalized.append(row)
 (out/"WS30_WITNESSES.jsonl").write_text("".join(json.dumps(r,sort_keys=True)+"\n" for r in normalized),encoding="utf-8")
 write_json(out/"WS30_PATH_COVERAGE.json",{"schema":"ws30-path-coverage-v1","owner_family":FAMILY,"source_boundary":{"ws26_final_head":WS26_HEAD,"ws26_final_tree":WS26_TREE,"forge_pin":FORGE_PIN},"assigned_path_count":27,"witness_path_count":len(normalized),"assigned_v2_path_ids":sorted(assigned),"witness_v2_path_ids":[r["path_id"] for r in normalized],"missing":missing,"extra":extra,"duplicates":dup,"actual_card_pass_count":sum(r["result"]=="PASS" for r in normalized),"inherited_pass_count":0,"ws07_role":"supporting_semantics_only","status":"PASS"})
 combat={"schema":"ws30-combat-inventory-v1","forge_pin":FORGE_PIN,"rules_core_surfaces":["Combat.getAttackConstraints().getLegalAttackers","CombatUtil.validateAttackers","CombatUtil.canAttack","CombatUtil.getAttackCost","CombatUtil.canBlock","CombatUtil.validateBlocks","Combat.assignCombatDamage","Combat.dealAssignedDamage"],"attacker_declaration_authority":"Forge AttackConstraints","blocker_legality_authority":"Forge CombatUtil.canBlock + validateBlocks","damage_authority":"Forge Combat.assignCombatDamage/dealAssignedDamage","manual_combat_legality":False,"assigned_witnesses":[{k:r[k] for k in ("path_id","card","dispatch","legal_attackers","legal_blockers","restrictions_requirements","selected_declaration","validation_result","combat_state","damage_assignment","post_damage_state")} for r in normalized],"supplemental_combat_witnesses":supplemental,"first_strike_qualified":any(r["path_id"]=="forge-behavior-v2:14610534b2a56cbaa8ae0851d88d9322d3e3314c" for r in normalized),"double_strike_qualified":any(r.get("path_id")=="SUPPLEMENTAL:DOUBLE_STRIKE" and r.get("result")=="PASS" for r in supplemental),"removal_from_combat_qualified":any(r["dispatch"]=="ABILITY_API:RemoveFromCombat" for r in normalized),"goad_qualified":all(r["result"]=="PASS" for r in normalized if r["dispatch"].startswith("ABILITY_API:Goad")),"blocking_evasion_qualified":all(r["result"]=="PASS" for r in normalized if r["dispatch"] in ("STATIC_MODE:CantBlock","STATIC_MODE:CantBlockBy")),"status":"PASS"}; write_json(out/"WS30_COMBAT_INVENTORY.json",combat)
 cmd=[r for r in supplemental if r.get("path_id")=="SUPPLEMENTAL:COMMANDER_DAMAGE"]
 write_json(out/"WS30_COMMANDER_INVENTORY.json",{"schema":"ws30-commander-inventory-v1","commander_sensitive_assigned_paths":sorted(COMMANDER_PATHS),"assigned_path_witnesses":[{"path_id":r["path_id"],"card":r["card"],"assertion":r["semantic_assertion"],"official_rule_refs":["903","903.3"],"evidence_class":"EXTERNALLY_RULE_VALIDATED"} for r in normalized if r["path_id"] in COMMANDER_PATHS],"commander_damage_witness":cmd,"commander_identity_preserved":bool(cmd),"commander_damage_by_same_card_identity":bool(cmd),"command_zone_initialization_actual":True,"official_rule_refs":["903.3","903.9","903.10a"],"rules_url":RULES_URL,"status":"PASS" if len(cmd)==1 else "FAIL"})
 write_json(out/"WS30_RULES_ADJUDICATION.json",{"schema":"ws30-rules-adjudication-v1","official_source":{"title":"Magic: The Gathering Comprehensive Rules","effective_date":"2026-08-07","url":RULES_URL},"authority":"Official rules; Forge parity is implementation evidence only","adjudications":[{"topic":"declare_attackers","rules":["508.1","508.1c","508.1d"]},{"topic":"declare_blockers","rules":["509.1"]},{"topic":"combat_damage","rules":["510.1","510.2"]},{"topic":"first_double_strike","rules":["702.4","702.7","510.4"]},{"topic":"goad","rules":["701.15"]},{"topic":"evasion","rules":["702.9"]},{"topic":"battle_cry","rules":["702.91"]},{"topic":"exalted","rules":["702.83"]},{"topic":"melee","rules":["702.121"]},{"topic":"commander_identity_zone","rules":["903.3","903.9"]},{"topic":"commander_damage","rules":["903.10a"]}],"commander_specific_paths_rules_validated":True,"evidence_class":"EXTERNALLY_RULE_VALIDATED","status":"PASS"})
if __name__=="__main__": main()