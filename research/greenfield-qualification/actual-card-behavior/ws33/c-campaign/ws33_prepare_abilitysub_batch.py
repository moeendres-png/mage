#!/usr/bin/env python3
"""Prepare the WS33-C batch case set (deterministic).

Runs the batch checker, then emits the flat TSV-v2 case file and plan
consumed by Ws33AbilitySubWitnessTest. The definitions JSON stays the
reviewed source; the TSV is a mechanical projection. Digest-bound.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def canon(o) -> bytes:
    return (json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def b64(v: str) -> str:
    return base64.b64encode(v.encode("utf-8")).decode("ascii")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--definitions", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--coverage", type=Path, required=True)
    ap.add_argument("--partition", type=Path, required=True)
    ap.add_argument("--forge-git", type=Path, required=True)
    ap.add_argument("--allow-rewitness", nargs="*", default=[])
    ap.add_argument("--out-tsv", type=Path, required=True)
    ap.add_argument("--out-plan", type=Path, required=True)
    args = ap.parse_args()

    checker = Path(__file__).resolve().parent / "ws33_check_batch_definitions.py"
    cmd = [sys.executable, str(checker), "--definitions", str(args.definitions),
           "--manifest", str(args.manifest), "--coverage", str(args.coverage),
           "--partition", str(args.partition), "--forge-git", str(args.forge_git)]
    if args.allow_rewitness:
        cmd += ["--allow-rewitness"] + list(args.allow_rewitness)
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(r.stdout, end="")
    if r.returncode != 0:
        print(r.stderr, end="")
        raise SystemExit("WS33_C_BATCH_PREPARE=FAIL checker rejected definitions")

    defs = json.loads(args.definitions.read_text(encoding="utf-8"))
    digest = hashlib.sha256(canon(defs)).hexdigest()
    header = ("#execution_id\tcard_b64\toracle\tsource_b64\tfixture_kind\tentering_b64\t"
              "setup\tlink_path\tparent_svar\tparent_api\tchild_sub\tchild_api\t"
              "parent_line\tassertions\tconsultations\tterminal\n")
    lines = [header]
    plan_execs = []
    for ex in defs["executions"]:
        fx = ex["fixture"]
        setup = ";".join(
            f"{b64(s['card_name'])}|{s['zone']}|{s['who']}|{s['count']}|{s.get('via', 'place')}"
            for s in ex.get("setup", []))
        asserts = []
        for a in ex["assertions"]:
            asserts.append("|".join([
                a["id"], a["type"], a.get("who", ""), b64(a.get("name", "")),
                b64(a.get("card", "")), a.get("counter", ""), a.get("keyword", ""),
                str(a["expected"])]))
        consultations = ";".join(
            f"{c['site']}|{c['options']}" for c in ex.get("expected_consultations", []))
        plan_execs.append({
            "execution_id": ex["execution_id"],
            "card_name": ex["card_name"],
            "oracle_identity": ex["oracle_identity"],
            "source_path": ex["source_path"],
            "fixture_kind": fx["kind"],
            "paths": [link["path_id"] for link in ex["links"]],
            "links": [{
                "path_id": link["path_id"],
                "parent_svar": link["parent_svar"],
                "parent_api": link["parent_api"],
                "child_sub": link["child_sub"],
                "child_api": link["child_api"],
                "terminal": bool(link.get("terminal", False)),
            } for link in ex["links"]],
            "assertions": [{
                "assertion_id": a["id"],
                "expected": a["expected"],
            } for a in ex["assertions"]],
            "expected_consultations": [{
                "site": c["site"],
                "options": c["options"],
            } for c in ex.get("expected_consultations", [])],
        })
        for link in ex["links"]:
            lines.append("\t".join([
                ex["execution_id"], b64(ex["card_name"]), ex["oracle_identity"],
                b64(ex["source_path"]), fx["kind"], b64(fx.get("entering_card", "")),
                setup, link["path_id"], link["parent_svar"], link["parent_api"],
                link["child_sub"], link["child_api"], str(link["parent_line"]),
                ";".join(asserts), consultations,
                "terminal" if link.get("terminal", False) else ""]) + "\n")
    args.out_tsv.parent.mkdir(parents=True, exist_ok=True)
    args.out_tsv.write_text("".join(lines), encoding="utf-8")
    plan = {"schema": "commander-simulator-next.ws33-c-batch-plan.v1",
            "batch": defs["batch_id"], "forge_pin": defs["forge_pin"],
            "batch_digest": digest, "executions": plan_execs,
            "case_rows": len(lines) - 1,
            "path_slots": sum(len(e["paths"]) for e in plan_execs)}
    args.out_plan.parent.mkdir(parents=True, exist_ok=True)
    args.out_plan.write_text(json.dumps(plan, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"WS33_C_BATCH_PREPARE": "PASS", "executions": len(plan_execs),
                      "case_rows": plan["case_rows"], "BATCH_DIGEST": digest}, sort_keys=True))


if __name__ == "__main__":
    main()
