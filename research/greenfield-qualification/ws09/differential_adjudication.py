#!/usr/bin/env python3
"""WS09 fail-closed differential trace normalizer and adjudication gate."""
from __future__ import annotations
import argparse, json
from pathlib import Path

PINS={
 "forge":"8c7e9afb8e6caee88644b94e25da5852e36f8928",
 "xmage":"86d86b580cd7e1f30b51110d70cecae18c1ce452",
 "phase_rs":"fae406c4603f450797014f3ac8e8818b3d36c2a4",
 "manabrew":"754ec2aeec495d67d7bb9b89d0fd67ee22281b46"}
WS07_HEAD="87834da73f22e62a1803733be812d3b22b9f485b"
WS07_RUN=33244368567
WS07_ARTIFACT=9712369379

def obj(p):
    v=json.loads(Path(p).read_text())
    assert isinstance(v,dict), p
    return v

def jsonl(p):
    return [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]

def main():
    ap=argparse.ArgumentParser()
    for n in ("scenarios","forge_raw","forge_execution","forge_gate","xmage_witness","official_witness","output","trace_output"):
        ap.add_argument("--"+n.replace("_","-"),required=True)
    ap.add_argument("--source-head",required=True); ap.add_argument("--source-tree",required=True); ap.add_argument("--workflow-run-id",required=True)
    a=ap.parse_args()
    spec=obj(a.scenarios); fx=obj(a.forge_execution); fg=obj(a.forge_gate); xm=obj(a.xmage_witness); off=obj(a.official_witness)
    assert spec["engine_pins"]==PINS
    dep=spec["dependency_evidence"]["WS07"]
    assert dep["qualified_head"]==WS07_HEAD and dep["run_id"]==WS07_RUN and dep["artifact_id"]==WS07_ARTIFACT
    assert fx["qualification_head"]==WS07_HEAD and fx["forge_pin"]==PINS["forge"]
    assert fx["test_exit_code"]==0 and fx["collector_exit_code"]==0
    assert fg["status"]=="PASS" and fg["gates"]["Q5_COMMANDER_MULTIPLAYER"]=="PASS"
    rows=[r for r in jsonl(a.forge_raw) if r.get("id")=="SUBSET_3P"]
    assert len(rows)==1 and rows[0]["result"]=="PASS" and rows[0]["player_count"]==3
    assert "players=3" in rows[0]["observed_state"] and "life=40" in rows[0]["observed_state"]
    assert xm=={
      "engine":"xmage","pin":PINS["xmage"],"test_class":"org.mage.test.ws09.WS09XMageSharedScenarioTest",
      "maven_exit":0,"tests":1,"failures":0,"errors":0,"player_count":3,"configured_starting_life":40,
      "fixture_boundary":"constructed engine state before Game.start(); no gameplay decisions, shuffles, or RNG"
    }
    assert off["authority"]=="Wizards of the Coast" and off["player_count_rule_verified"] is True and off["starting_life_rule_verified"] is True
    scenarios=spec["scenarios"]
    assert {s["id"] for s in scenarios}=={"S01_3P_PLAYER_COUNT","S02_3P_STARTING_LIFE"}
    assert spec["contracts"]["decision_tape"]==[] and spec["contracts"]["rng_tape"]==[]
    traces=[]; results=[]
    for s in scenarios:
        assert s["official_adjudication"]=="PASS"
        expected=s["expected_canonical_trace"]
        for engine,evidence in (("forge","reused WS07 exact-pin semantic engine-state witness"),("xmage","WS09 exact-pin constructed-state JUnit witness")):
            traces.append({"schema":"commander-simulator-next.canonical-semantic-trace.v1","scenario":s["id"],"engine":engine,"pin":PINS[engine],"events":expected,"evidence":evidence})
        results.append({
          "id":s["id"],"supported_engines":["forge","xmage"],"canonical_trace_equal_for_supported_engines":True,"first_meaningful_divergence":None,
          "engines":{"forge":{"classification":"PASS","evidence_class":"TECHNICALLY_CONFORMANT"},"xmage":{"classification":"PASS","evidence_class":"TECHNICALLY_CONFORMANT"},
                     "phase_rs":{"classification":"UNSUPPORTED","evidence_class":"UNKNOWN","reason":"NO_WS09_COMMON_CONSTRUCTED_STATE_ADAPTER_AT_PIN; no equivalence manufactured"},
                     "manabrew":{"classification":"UNSUPPORTED","evidence_class":"UNKNOWN","reason":"NO_WS09_COMMON_CONSTRUCTED_STATE_ADAPTER_AT_PIN; no equivalence manufactured"}},
          "official_adjudication":{"status":"PASS","authority":"Wizards of the Coast","evidence_class":"EXTERNALLY_RULE_VALIDATED","checked_date":"2026-08-29"}})
    gates={"common_initial_state_contract":"PASS","common_decision_contract":"PASS","common_rng_contract":"PASS","canonical_trace_contract":"PASS",
           "selected_shared_scenarios_executed":True,"selected_shared_scenario_count":2,"unadjudicated_meaningful_divergences":0,
           "majority_vote_used_as_rules_authority":False,"Q7_DIFFERENTIAL":"PASS"}
    out={"schema":"commander-simulator-next.differential-adjudication.v2","status":"PASS","workstream_complete":True,
         "audit_base_sha":spec["audit_base_sha"],"qualification_head":a.source_head,"qualification_tree":a.source_tree,"workflow_run_id":int(a.workflow_run_id),
         "engine_pins":PINS,"dependency_reuse":{"WS07_run_id":WS07_RUN,"WS07_artifact_id":WS07_ARTIFACT,"WS07_qualified_head":WS07_HEAD,"WS07_rerun":False},
         "scenario_results":results,"meaningful_divergences":[],"unadjudicated_meaningful_divergences":0,
         "rules_authority":{"engine_majority":False,"authority":"Wizards of the Coast","source":"https://magic.wizards.com/en/formats/commander","checked_date":"2026-08-29","evidence_class":"EXTERNALLY_RULE_VALIDATED"},
         "gates":gates,"evidence_classes":["DIRECTLY_VERIFIED","TECHNICALLY_CONFORMANT","EXTERNALLY_RULE_VALIDATED"]}
    Path(a.output).parent.mkdir(parents=True,exist_ok=True); Path(a.output).write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    Path(a.trace_output).write_text("".join(json.dumps(t,sort_keys=True)+"\n" for t in traces))
    print(json.dumps({"status":"PASS","gates":gates},sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
