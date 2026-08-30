#!/usr/bin/env python3
import argparse,json,re
from pathlib import Path
EXPECTED_HEAD="206a39cbaa3eeb98b10c2ddc36d51fe5b1b2f5ef"; EXPECTED_TREE="837f445f78bb26462653c58baf1532e294151b10"; EXPECTED_FORGE="8c7e9afb8e6caee88644b94e25da5852e36f8928"
REQ=["path_id","card","dispatch","forge_pin","initial_state","legal_attackers","legal_blockers","restrictions_requirements","selected_declaration","validation_result","combat_state","damage_assignment","post_damage_state","semantic_assertion","result","evidence_class","actual_card_execution","rules_core_authority","manual_legality","official_rule_refs"]
def load(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def rows(p): return [json.loads(x) for x in Path(p).read_text(encoding="utf-8").splitlines() if x.strip()]
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--dir",required=True); ap.add_argument("--java-source",required=True); a=ap.parse_args(); d=Path(a.dir)
 cov=load(d/"WS30_PATH_COVERAGE.json"); combat=load(d/"WS30_COMBAT_INVENTORY.json"); commander=load(d/"WS30_COMMANDER_INVENTORY.json"); rules=load(d/"WS30_RULES_ADJUDICATION.json"); wit=rows(d/"WS30_WITNESSES.jsonl"); src=Path(a.java_source).read_text(encoding="utf-8"); fail=[]
 if cov["source_boundary"]["ws26_final_head"]!=EXPECTED_HEAD: fail.append("WS26 head mismatch")
 if cov["source_boundary"]["ws26_final_tree"]!=EXPECTED_TREE: fail.append("WS26 tree mismatch")
 if cov["source_boundary"]["forge_pin"]!=EXPECTED_FORGE: fail.append("Forge pin mismatch")
 if cov["assigned_path_count"]!=27 or cov["witness_path_count"]!=27: fail.append("coverage count !=27")
 if cov["missing"] or cov["extra"] or cov["duplicates"]: fail.append("coverage mismatch")
 if cov["inherited_pass_count"]!=0 or cov["ws07_role"]!="supporting_semantics_only": fail.append("invalid inherited evidence")
 if len(wit)!=27 or len({r["path_id"] for r in wit})!=27: fail.append("witness cardinality invalid")
 for r in wit:
  miss=[k for k in REQ if k not in r]
  if miss: fail.append(f"{r.get('path_id')}: missing {miss}")
  if r.get("result")!="PASS" or r.get("evidence_class")!="TECHNICALLY_CONFORMANT": fail.append(f"{r.get('path_id')}: result/evidence")
  if not r.get("actual_card_execution") or not r.get("rules_core_authority") or r.get("manual_legality"): fail.append(f"{r.get('path_id')}: boundary flag")
  if not r.get("official_rule_refs"): fail.append(f"{r.get('path_id')}: no official rules")
  for k in ("initial_state","selected_declaration","validation_result","combat_state","damage_assignment","post_damage_state"):
   if not str(r.get(k,"")).strip(): fail.append(f"{r.get('path_id')}: empty {k}")
 m=re.search(r'class Ws30Controller.*?private static final class Ws30LobbyPlayer',src,re.S); controller=m.group(0) if m else ""
 for token in ("getAttackConstraints().getLegalAttackers()","CombatUtil.validateAttackers(combat)","CombatUtil.validateBlocks(combat, defender)"):
  if token not in controller: fail.append("controller missing rules-core token "+token)
 patterns=[r'hasKeyword\s*\(',r'getNetPower\s*\(',r'isFlying\s*\(',r'powerGE',r'withoutFlying',r'withFlying',r'CantAttack',r'CantBlock']; manual=sum(len(re.findall(p,controller)) for p in patterns)
 if manual: fail.append(f"manual legality patterns={manual}")
 if "CombatUtil.canBlock(attacker,blocker,combat)" not in src: fail.append("missing rules-core blocker enumeration")
 if "combat.addBlocker" in src: fail.append("manual blocker addition")
 core=not any(("rules-core token" in x or "manual legality" in x or "blocker enumeration" in x or "blocker addition" in x) for x in fail)
 state=all(str(r.get("validation_result","")).strip() and str(r.get("combat_state","")).strip() and str(r.get("damage_assignment","")).strip() and str(r.get("post_damage_state","")).strip() for r in wit)
 cmd=(commander.get("status")=="PASS" and commander.get("commander_identity_preserved") is True and commander.get("commander_damage_by_same_card_identity") is True and rules.get("commander_specific_paths_rules_validated") is True and any(x.get("topic")=="commander_damage" and "903.10a" in x.get("rules",[]) for x in rules.get("adjudications",[])))
 if not cmd: fail.append("commander-specific rules gate")
 for k in ("first_strike_qualified","double_strike_qualified","removal_from_combat_qualified","goad_qualified","blocking_evasion_qualified"):
  if combat.get(k) is not True: fail.append(k+" false")
 if combat.get("manual_combat_legality") is not False: fail.append("inventory manual legality")
 gate={"schema":"ws30-gate-v1","owner_family":"COMBAT_COMMANDER","ws26_final_head":EXPECTED_HEAD,"ws26_final_tree":EXPECTED_TREE,"forge_pin":EXPECTED_FORGE,"assigned_path_count":27,"actual_card_pass_count":sum(r.get("result")=="PASS" for r in wit),"inherited_pass_count":0,"combat_legality_from_rules_core":core,"manual_combat_legality_in_harness":manual,"combat_state_assertions_complete":state,"commander_specific_paths_rules_validated":cmd,"first_strike_qualified":combat.get("first_strike_qualified"),"double_strike_qualified":combat.get("double_strike_qualified"),"goad_qualified":combat.get("goad_qualified"),"blocking_evasion_qualified":combat.get("blocking_evasion_qualified"),"removal_from_combat_qualified":combat.get("removal_from_combat_qualified"),"global_q6_claim":False,"global_q5_rerun":False,"failure_count":len(fail),"failures":fail}
 ok=not fail and gate["actual_card_pass_count"]==27 and core and manual==0 and state and cmd; gate["WS30_FAMILY_GATE"]="PASS" if ok else "FAIL"; gate["WORKSTREAM_COMPLETE"]=ok
 (d/"WS30_GATE.json").write_text(json.dumps(gate,indent=2,sort_keys=True)+"\n",encoding="utf-8"); print(json.dumps(gate,indent=2,sort_keys=True)); raise SystemExit(0 if ok else 1)
if __name__=="__main__": main()
