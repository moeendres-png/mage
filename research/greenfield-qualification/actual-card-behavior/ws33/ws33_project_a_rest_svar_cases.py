#!/usr/bin/env python3
"""Project immutable A-rest topology into fresh runtime case ABIs.

This tool performs no consumer inference and no Magic legality logic. It accepts only the
already-selected one-parent-per-path topology emitted by the qualified A-rest topology
gate, validates its exact 26-path partition, and serializes those selected parents into
ABIs consumed by the existing source-parent/trigger runtime harness mechanisms.
"""
from __future__ import annotations
import argparse, base64, json
from pathlib import Path

TARGET_IMPL = "forge.game.spellability.TargetRestrictions"
EXPECTED_FORGE = "8c7e9afb8e6caee88644b94e25da5852e36f8928"


def require(c: bool, m: str) -> None:
    if not c:
        raise SystemExit("WS33_A_REST_SVAR_PROJECT=FAIL " + m)


def b64(s: str) -> str:
    return base64.b64encode(s.encode("utf-8")).decode("ascii")


def api(script: str) -> tuple[str, str]:
    first = script.split("|", 1)[0].strip()
    require("$" in first, "script first token lacks $: " + first)
    prefix, name = first.split("$", 1)
    prefix = prefix.strip(); name = name.strip()
    require(prefix in {"SP", "AB", "DB"} and bool(name), "unsupported first token: " + first)
    return name, prefix + "$"


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--topology",type=Path,required=True)
    ap.add_argument("--out-dir",type=Path,required=True)
    a=ap.parse_args()
    top=json.loads(a.topology.read_text(encoding="utf-8"))
    require(top.get("status")=="PASS", "topology status is not PASS")
    require(top.get("forge_pin")==EXPECTED_FORGE, "Forge pin mismatch")
    require(top.get("a_rest_path_count")==57, "A-rest cardinality mismatch")
    require(top.get("direct_ability_path_count")==31, "Direct31 cardinality mismatch")
    require(top.get("svar_path_count")==26, "SVar26 cardinality mismatch")
    require(top.get("svar_parent_entrypoint_count")==26, "parent entrypoint cardinality mismatch")
    require(top.get("unresolved_svar_paths")==[], "unresolved SVar paths present")
    require(top.get("coverage_mutated") is False, "topology reports coverage mutation")

    cases=top.get("svar_cases") or []
    require(len(cases)==26, "svar_cases cardinality mismatch")
    require(len({x.get("v2_path_id") for x in cases})==26, "duplicate SVar path id")
    nontrigger=[]; trigger=[]
    for c in cases:
        parents=c.get("selected_parents") or []
        require(len(parents)==1, f"selected parent count !=1 for {c.get('v2_path_id')}")
        p=parents[0]
        require(c.get("source_directive")=="SVAR", f"target source directive mismatch {c.get('v2_path_id')}")
        require(c.get("target_svar"), f"missing target SVar {c.get('v2_path_id')}")
        target_api,_=api(c["exact_script"])
        parent_api,parent_token=api(p["script"])
        common={
            "ordinal":int(c["ordinal"]), "path":c["v2_path_id"], "oracle":c["oracle_identity"],
            "card":c["card_name"], "source_path":c["source_path"], "source_line":int(p["source_line"]),
            "directive":p["directive"], "parent_svar":p.get("parent_svar") or "",
            "consumer":p.get("consumer_field") or "", "mode":p.get("event_mode") or "",
            "hidden":"1" if c.get("required_hidden_info_evidence") else "0",
            "rng":"1" if c.get("required_rng_evidence") else "0",
            "replay":"1" if c.get("required_replay_evidence") else "0",
            "decision":"1" if c.get("required_decision_evidence") else "0",
            "target_api":target_api, "target_script":c["exact_script"],
            "parent_api":parent_api, "parent_token":parent_token, "parent_script":p["script"],
        }
        if p["directive"]=="TRIGGER":
            require(common["consumer"]=="Execute", f"trigger parent is not Execute {common['path']}")
            require(bool(common["mode"]), f"trigger mode missing {common['path']}")
            trigger.append(common)
        else:
            require(p.get("ability_factory_compatible") is True, f"nontrigger parent not AbilityFactory-compatible {common['path']}")
            require(common["consumer"] in {"Choices","SubAbility"}, f"unsupported nontrigger consumer {common['path']}")
            require(p["directive"] in {"ABILITY","SVAR"}, f"unsupported nontrigger directive {common['path']}")
            nontrigger.append(common)

    require(len(nontrigger)==9, f"nontrigger count={len(nontrigger)}")
    require(len(trigger)==17, f"trigger count={len(trigger)}")
    require(sum(x["consumer"]=="Choices" and x["directive"]=="ABILITY" for x in nontrigger)==7, "ABILITY:Choices !=7")
    require(sum(x["consumer"]=="Choices" and x["directive"]=="SVAR" for x in nontrigger)==1, "SVAR:Choices !=1")
    require(sum(x["consumer"]=="SubAbility" and x["directive"]=="ABILITY" for x in nontrigger)==1, "ABILITY:SubAbility !=1")
    modes={m:sum(x["mode"]==m for x in trigger) for m in {x["mode"] for x in trigger}}
    require(modes=={"ChangesZone":14,"DamageDone":1,"SpellCast":1,"Phase":1}, "trigger mode partition mismatch: "+repr(modes))
    require(sum(x["rng"]=="1" for x in trigger)==2 and sum(x["rng"]=="1" for x in nontrigger)==0, "RNG partition mismatch")

    a.out_dir.mkdir(parents=True,exist_ok=True)
    af=[]
    for x in sorted(nontrigger,key=lambda z:(z["ordinal"],z["path"])):
        af.append("\t".join(map(str,[
            x["ordinal"],x["path"],x["oracle"],x["card"],x["parent_api"],TARGET_IMPL,
            x["source_path"],x["source_line"],x["directive"],x["parent_token"],
            x["hidden"],x["rng"],x["replay"],x["decision"],b64(x["parent_script"]),
            x["parent_svar"],next(c["target_svar"] for c in cases if c["v2_path_id"]==x["path"]),
            x["target_api"],b64(x["target_script"])
        ])))
    ev=[]
    for x in sorted(trigger,key=lambda z:(z["ordinal"],z["path"])):
        target_svar=next(c["target_svar"] for c in cases if c["v2_path_id"]==x["path"])
        ev.append("\t".join(map(str,[
            x["ordinal"],x["path"],0,1,x["oracle"],x["card"],target_svar,x["target_api"],TARGET_IMPL,
            x["source_path"],x["source_line"],x["directive"],x["parent_svar"],x["consumer"],x["mode"],
            x["hidden"],x["rng"],x["replay"],x["decision"],b64(x["target_script"]),b64(x["parent_script"])
        ])))

    (a.out_dir/"a-rest-svar-nontrigger9.tsv").write_text("\n".join(af)+"\n",encoding="utf-8")
    (a.out_dir/"a-rest-svar-trigger17.tsv").write_text("\n".join(ev)+"\n",encoding="utf-8")
    gate={
        "schema":"commander-simulator-next.ws33-a-rest-svar-runtime-cases.v1","status":"PASS",
        "svar_paths":26,"nontrigger_paths":9,"trigger_paths":17,"selected_parent_entrypoints":26,
        "nontrigger_abi_columns":19,"trigger_abi_columns":21,"consumer_inference_performed":False,
        "target_implementation":TARGET_IMPL,"trigger_modes":modes,"rng_nontrigger":0,"rng_trigger":2,
        "coverage_mutated":False,"coverage_promotion":False,
    }
    (a.out_dir/"A_REST_SVAR_CASE_GATE.json").write_text(json.dumps(gate,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("WS33_A_REST_SVAR_PROJECT=PASS paths=26 nontrigger=9 trigger=17 inference=FALSE")

if __name__=="__main__": main()
