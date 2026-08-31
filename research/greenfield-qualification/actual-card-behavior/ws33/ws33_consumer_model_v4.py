#!/usr/bin/env python3
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import ws33_consumer_model_v3 as base

PIN = base.PIN
DOMAIN = base.DOMAIN
# RandomCompareSVar is a direct Amount consumer in CharmEffect.makeChoices.
base.AMOUNT.add("RandomCompareSVar")


def java_direct_key_index(root: Path) -> dict[str, list[dict]]:
    result = collections.defaultdict(list)
    pat = re.compile(r'\b(?:getSVar|hasSVar)\(\s*"([A-Za-z0-9_]+)"')
    for module in ("forge-game", "forge-core", "forge-gui", "forge-ai"):
        src = root / module / "src/main/java"
        if not src.exists():
            continue
        for path in sorted(src.rglob("*.java")):
            rel = path.relative_to(root).as_posix()
            for line_no, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                for key in pat.findall(line):
                    result[key].append({
                        "path": rel,
                        "line": line_no,
                        "source": re.sub(r"\s+", " ", line.strip())[:300],
                        "rules_core": rel.startswith("forge-game/"),
                    })
    return result


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--forge-root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    head = subprocess.check_output(["git", "-C", str(args.forge_root), "rev-parse", "HEAD"], text=True).strip()
    if head != PIN:
        raise SystemExit("Forge pin mismatch " + head)

    contract = base.forge_contract(args.forge_root)
    charm = args.forge_root / "forge-game/src/main/java/forge/game/ability/effects/CharmEffect.java"
    charm_text = charm.read_text(encoding="utf-8")
    if 'AbilityUtils.calculateAmount(source, sa.getParam("RandomCompareSVar"), sa)' not in charm_text:
        raise SystemExit("RandomCompareSVar consumer contract mismatch")
    contract["checks"]["random_compare_svar_is_amount"] = True
    contract["source_sha256"]["charm"] = sha(charm)

    statics = base.static_modes(args.forge_root)
    raw = base.load(args.manifest)["paths"]
    svar_paths = [p for p in raw if p.get("dispatch_domain") == DOMAIN]
    direct_java = java_direct_key_index(args.forge_root)
    cache = {}
    new_paths = {}
    old_to_new = collections.defaultdict(set)
    non_rules = {}
    unresolved = []
    signatures = collections.Counter()

    for old in svar_paths:
        old_id = old["v2_path_id"]
        for prov in old.get("source_provenance", []):
            if prov.get("source_directive") != "SVAR":
                continue
            rel = prov["forge_source_path"]
            line_no = int(prov["source_line"])
            token = prov["source_token"]
            value = prov["source_value"]
            source = args.forge_root / rel
            if rel not in cache:
                cache[rel] = base.index_card(source)
            card = cache[rel]
            declaration = card["svars"].get(token)
            if not declaration or declaration["line"] != line_no or declaration["value"] != value:
                unresolved.append({
                    "old_effective_v2_path_id": old_id,
                    "reason": "SVAR_PROVENANCE_MISMATCH",
                    "source": rel,
                    "line": line_no,
                    "token": token,
                })
                continue

            consumers = base.direct(token, line_no, card, base.kind(value, statics), statics)
            if not consumers:
                java_refs = direct_java.get(token, [])
                rules_refs = [x for x in java_refs if x["rules_core"]]
                non_rules_refs = [x for x in java_refs if not x["rules_core"]]
                if java_refs and not rules_refs:
                    row = non_rules.setdefault(old_id, {
                        "old_effective_v2_path_id": old_id,
                        "disposition": "PROVEN_NON_RULES_METADATA",
                        "source_token": token,
                        "source_value": value,
                        "source_provenance": [],
                        "direct_java_consumers": non_rules_refs,
                        "reason": "No card-script rules consumer and all exact direct Java SVar-key consumers are outside forge-game Rules Core.",
                    })
                    row["source_provenance"].append(prov)
                    continue
                unresolved.append({
                    "old_effective_v2_path_id": old_id,
                    "reason": "NO_ACTUAL_FIRST_CONSUMER",
                    "source": rel,
                    "line": line_no,
                    "token": token,
                    "value": value,
                    "direct_java_consumers": java_refs,
                })
                continue

            for consumer in consumers:
                desc = base.descriptor(old, consumer, token, value)
                desc["semantic_selector_profile"]["consumer_model"] = "WS33_CONSUMER_AWARE_SVAR_V4"
                new_id = base.vid(desc)
                signatures[(consumer["consumer_kind"], consumer["implementation_target"], consumer["owner_family"], consumer["consumer_field"])] += 1
                target = new_paths.setdefault(new_id, {
                    "v2_path_id": new_id,
                    **desc,
                    "cross_family_dependencies": list(old.get("cross_family_dependencies", [])),
                    "source_provenance": [],
                    "representative_actual_oracle_identities": [],
                    "source_occurrence_count": 0,
                    "required_decision_evidence": bool(old.get("required_decision_evidence")),
                    "required_rng_evidence": bool(old.get("required_rng_evidence")),
                    "required_hidden_info_evidence": bool(old.get("required_hidden_info_evidence")),
                    "required_replay_evidence": bool(old.get("required_replay_evidence")),
                    "evidence_class": "CODE_DERIVED",
                    "current_witness_status": "UNPROVED",
                    "consumer_evidence": [],
                    "historical_ws26_v2_path_ids": [],
                })
                if prov not in target["source_provenance"]:
                    target["source_provenance"].append(prov)
                target["representative_actual_oracle_identities"] = sorted(set(
                    target["representative_actual_oracle_identities"] + [prov["oracle_identity"]]
                ))[:12]
                target["historical_ws26_v2_path_ids"] = sorted(set(
                    target["historical_ws26_v2_path_ids"] + [old_id]
                ))
                evidence = {k: v for k, v in consumer.items() if k != "consumer_text"}
                evidence.update({
                    "forge_source_path": rel,
                    "source_line": line_no,
                    "source_token": token,
                    "source_value": value,
                    "consumer_text": consumer["consumer_text"],
                })
                if evidence not in target["consumer_evidence"]:
                    target["consumer_evidence"].append(evidence)
                old_to_new[old_id].add(new_id)

    for row in new_paths.values():
        row["source_provenance"].sort(key=lambda x: (x["forge_source_path"], x["source_line"], x["oracle_identity"]))
        row["consumer_evidence"].sort(key=lambda x: (x["forge_source_path"], x["source_line"], x["consumer_line"], x["consumer_field"]))
        row["source_occurrence_count"] = len(row["source_provenance"])
    for row in non_rules.values():
        row["source_provenance"].sort(key=lambda x: (x["forge_source_path"], x["source_line"], x["oracle_identity"]))

    by_old = {p["v2_path_id"]: p for p in svar_paths}
    migrations = []
    for old_id in sorted(by_old):
        old = by_old[old_id]
        if old_id in non_rules:
            migrations.append({
                "old_effective_v2_path_id": old_id,
                "new_effective_v2_path_id": None,
                "old_implementation_target": old.get("implementation_target"),
                "new_implementation_target": None,
                "old_owner_family": old.get("owner_family"),
                "new_owner_family": None,
                "migration_reason": "PROVEN_NON_RULES_METADATA",
                "historical_erratum_alias": old_id in base.ERRATA,
                "status_before": None,
                "status_after": None,
            })
        for new_id in sorted(old_to_new.get(old_id, [])):
            new = new_paths[new_id]
            migrations.append({
                "old_effective_v2_path_id": old_id,
                "new_effective_v2_path_id": new_id,
                "old_implementation_target": old.get("implementation_target"),
                "new_implementation_target": new["implementation_target"],
                "old_owner_family": old.get("owner_family"),
                "new_owner_family": new["owner_family"],
                "migration_reason": "CONSUMER_AWARE_FIRST_RUNTIME_USE",
                "historical_erratum_alias": old_id in base.ERRATA,
                "status_before": None,
                "status_after": "UNKNOWN",
            })

    resolved_old = set(old_to_new) | set(non_rules)
    result = {
        "schema": "commander-simulator-next.ws33-consumer-aware-svar-model.v4",
        "forge_pin": PIN,
        "forge_consumer_contract": contract,
        "raw_svar_path_count": len(svar_paths),
        "resolved_old_path_count": len(resolved_old),
        "production_reachable_old_path_count": len(old_to_new),
        "non_rules_metadata_old_path_count": len(non_rules),
        "unresolved_old_path_count": len({x["old_effective_v2_path_id"] for x in unresolved}),
        "unresolved_occurrence_count": len(unresolved),
        "new_consumer_path_count": len(new_paths),
        "historical_erratum_aliases": sorted(base.ERRATA),
        "old_to_new": {k: sorted(v) for k, v in sorted(old_to_new.items())},
        "non_rules_metadata": [non_rules[k] for k in sorted(non_rules)],
        "new_paths": [new_paths[k] for k in sorted(new_paths)],
        "migrations": migrations,
        "unresolved": unresolved,
        "consumer_signature_counts": [
            {
                "consumer_kind": key[0],
                "implementation_target": key[1],
                "owner_family": key[2],
                "consumer_field": key[3],
                "count": count,
            }
            for key, count in sorted(signatures.items(), key=lambda item: (-item[1], item[0]))
        ],
    }
    base.write(args.out, result)
    print(json.dumps({
        "RAW_SVAR_PATHS": len(svar_paths),
        "RESOLVED_OLD_PATHS": len(resolved_old),
        "PRODUCTION_REACHABLE_OLD_PATHS": len(old_to_new),
        "NON_RULES_METADATA_OLD_PATHS": len(non_rules),
        "UNRESOLVED_OLD_PATHS": result["unresolved_old_path_count"],
        "UNRESOLVED_OCCURRENCES": len(unresolved),
        "NEW_CONSUMER_PATHS": len(new_paths),
    }, sort_keys=True))
    if unresolved:
        for row in unresolved:
            print("UNRESOLVED " + json.dumps(row, sort_keys=True))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
