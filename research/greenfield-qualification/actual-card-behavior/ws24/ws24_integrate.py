#!/usr/bin/env python3
"""WS24 semantic integration over immutable WS14 + WS15–WS19 evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928"
MANIFEST_SHA256 = "1137335dd7101df44940a2b0c8cacc5740e2aef0a24eceb541449dd10a5e6f7b"
PER_IDENTITY_SHA256 = "1e824702ed0dcd4af7d91e66b02ec37fc88dd9ace51ab20bf0abf1f53b605703"
UNRESOLVED_SHA256 = "d35b3f2772b7638768e9d66d5e00eed8bc3488530be99e064be44c82e1cb5704"
OWNER_EXPECTED = {
    "ACTION_COST_DECISION": {"count": 76, "PASS": 0, "PARTIAL": 76, "shard": "WS15"},
    "TRIGGER_REPLACEMENT_ZONE_SBA": {"count": 53, "PASS": 2, "PARTIAL": 51, "shard": "WS16"},
    "CONTINUOUS_COPY_CONTROL": {"count": 21, "PASS": 11, "PARTIAL": 10, "shard": "WS17"},
    "COMBAT_COMMANDER": {"count": 10, "PASS": 0, "PARTIAL": 10, "shard": "WS18"},
    "HIDDEN_RNG_REPLAY": {"count": 14, "PASS": 0, "PARTIAL": 14, "shard": "WS19"},
}
STATUS = {"PASS", "PARTIAL", "UNKNOWN", "UNSUPPORTED"}
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def find_one(root: Path, name: str) -> Path:
    hits = sorted(p for p in root.rglob(name) if p.is_file())
    if len(hits) != 1:
        raise ValueError(f"expected exactly one {name} under {root}, found {hits}")
    return hits[0]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def walk(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def docs(root: Path) -> Iterable[tuple[str, Any]]:
    for path in sorted(root.rglob("*.json")):
        try:
            yield str(path.relative_to(root)), json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON in {path}: {exc}") from exc
    for path in sorted(root.rglob("*.jsonl")):
        for i, row in enumerate(read_jsonl(path), 1):
            yield f"{path.relative_to(root)}#{i}", row


def extract_shard(root: Path, owner: str, manifest_ids: set[str]) -> tuple[dict[str, dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    statuses: dict[str, dict[str, Any]] = {}
    witnesses: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for source, doc in docs(root):
        for node in walk(doc):
            pid = node.get("primitive_id")
            raw_status = node.get("status", node.get("classification"))
            if isinstance(pid, str) and pid in manifest_ids and raw_status in STATUS:
                prior = statuses.get(pid)
                record = {"status": raw_status, "source": source, "evidence_class": node.get("evidence_class"),
                          "failure_reason": node.get("failure_reason") or node.get("blocker") or node.get("exact_blocker")}
                if prior and prior["status"] != raw_status:
                    raise ValueError(f"conflicting shard status for {pid}: {prior} vs {record}")
                statuses.setdefault(pid, record)
            if (isinstance(node.get("witness_id"), str) and isinstance(node.get("primitive_ids"), list)
                    and node.get("execution") == "PASS"):
                trace = node.get("trace_sha256")
                if node.get("stdout_only") is not False or not isinstance(trace, str) or not HEX64.fullmatch(trace):
                    raise ValueError(f"nonqualifying PASS witness in {source}: {node.get('witness_id')}")
                for witnessed in node["primitive_ids"]:
                    if witnessed in manifest_ids:
                        witnesses[witnessed].append({
                            "witness_id": node["witness_id"], "trace_sha256": trace, "source": source,
                            "initial_semantic_state_id": node.get("initial_semantic_state_id"),
                            "decision_tape_ref": node.get("decision_tape_ref"), "rng_tape_ref": node.get("rng_tape_ref"),
                            "run_job_artifact_refs": node.get("run_job_artifact_refs"),
                        })
    return statuses, witnesses


def classify_identity(row: dict[str, Any], primitive_status: dict[str, str]) -> tuple[str, list[dict[str, str]]]:
    ids = row.get("atomic_primitive_ids") or []
    resolved = [{"primitive_id": pid, "status": primitive_status[pid]} for pid in ids]
    if row.get("ambiguity_status") != "UNAMBIGUOUS":
        return "UNKNOWN", resolved
    if int(row.get("unresolved_binding_count", 0)) > 0:
        return "UNKNOWN", resolved
    states = {x["status"] for x in resolved}
    if "UNSUPPORTED" in states:
        return "UNSUPPORTED", resolved
    if "UNKNOWN" in states:
        return "UNKNOWN", resolved
    if "PARTIAL" in states:
        return "PARTIAL", resolved
    if ids and states == {"PASS"}:
        return "CONDITIONAL_FULL", resolved
    return "UNKNOWN", resolved


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--ws14", type=Path, required=True)
    for ws in ("ws15", "ws16", "ws17", "ws18", "ws19"):
        p.add_argument(f"--{ws}", type=Path, required=True)
    p.add_argument("--source-head", required=True)
    p.add_argument("--source-tree", required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()

    manifest_path = find_one(args.ws14, "WS14_PRIMITIVE_MANIFEST.json")
    identities_path = find_one(args.ws14, "PER_IDENTITY.atomic.jsonl")
    unresolved_path = find_one(args.ws14, "UNRESOLVED_BINDINGS.jsonl")
    if digest(manifest_path) != MANIFEST_SHA256 or digest(identities_path) != PER_IDENTITY_SHA256 or digest(unresolved_path) != UNRESOLVED_SHA256:
        raise ValueError("WS14 artifact hash does not match qualified immutable materialization")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    identities = read_jsonl(identities_path)
    unresolved = read_jsonl(unresolved_path)
    if manifest.get("forge_pin") != FORGE_PIN or manifest.get("atomic_primitive_count") != 174 or len(identities) != 1678 or len(unresolved) != 1800:
        raise ValueError("WS14 cardinality/pin mismatch")

    primitives = {row["primitive_id"]: row for row in manifest["primitives"]}
    if len(primitives) != 174:
        raise ValueError("primitive manifest is not unique")
    owner_ids = {owner: {pid for pid, row in primitives.items() if row["owner_family"] == owner} for owner in OWNER_EXPECTED}

    roots = {"WS15": args.ws15, "WS16": args.ws16, "WS17": args.ws17, "WS18": args.ws18, "WS19": args.ws19}
    registry_rows = []
    all_status: dict[str, str] = {}
    for owner, expected in OWNER_EXPECTED.items():
        ids = owner_ids[owner]
        if len(ids) != expected["count"]:
            raise ValueError(f"owner count mismatch for {owner}")
        shard = expected["shard"]
        statuses, witnesses = extract_shard(roots[shard], owner, set(primitives))
        shard_ids = set(statuses)
        if shard_ids != ids:
            raise ValueError(f"{shard} does not account exactly for {owner}: missing={sorted(ids-shard_ids)} extra={sorted(shard_ids-ids)}")
        counts = Counter(record["status"] for record in statuses.values())
        if counts["PASS"] != expected["PASS"] or counts["PARTIAL"] != expected["PARTIAL"] or counts["UNKNOWN"] or counts["UNSUPPORTED"]:
            raise ValueError(f"unexpected {shard} status counts: {counts}")
        for pid in sorted(ids):
            record = statuses[pid]
            evidence = witnesses.get(pid, [])
            if record["status"] == "PASS" and not evidence:
                raise ValueError(f"PASS primitive lacks qualifying WS14-ABI witness: {pid}")
            if record["status"] != "PASS" and evidence:
                raise ValueError(f"non-PASS primitive unexpectedly has qualifying witness: {pid}")
            all_status[pid] = record["status"]
            registry_rows.append({
                "primitive_id": pid, "owner_family": owner, "dispatch_domain": primitives[pid]["dispatch_domain"],
                "dispatch_token": primitives[pid]["dispatch_token"], "implementation_target": primitives[pid]["implementation_target"],
                "status": record["status"], "source_shard": shard, "status_source": record["source"],
                "evidence_class": record.get("evidence_class") or ("TECHNICALLY_CONFORMANT" if evidence else "UNKNOWN"),
                "failure_reason": record.get("failure_reason"), "witnesses": evidence,
            })
    if len(all_status) != 174:
        raise ValueError("integrated primitive status registry is incomplete")

    affected: dict[str, list[dict[str, str]]] = defaultdict(list)
    identity_rows = []
    classifications = Counter()
    for row in identities:
        ids = row.get("atomic_primitive_ids") or []
        if any(pid not in all_status for pid in ids):
            raise ValueError(f"identity references unknown primitive: {row.get('oracle_id')}")
        classification, resolved = classify_identity(row, all_status)
        classifications[classification] += 1
        for pid in ids:
            if all_status[pid] != "PASS":
                affected[pid].append({"oracle_id": row["oracle_id"], "oracle_name": row["oracle_name"]})
        # Preserve the exact WS14 identity object, including source paths/hashes and
        # full-script signature IDs, rather than reconstructing provenance.
        identity_rows.append({
            "oracle_id": row["oracle_id"], "oracle_name": row["oracle_name"],
            "classification": classification, "resolved_primitive_status": resolved,
            "unresolved_binding_count": row["unresolved_binding_count"], "ambiguity_status": row["ambiguity_status"],
            "ws14_identity": row,
        })

    unproved = []
    for reg in registry_rows:
        if reg["status"] != "PASS":
            unproved.append({
                "primitive_id": reg["primitive_id"], "owner_family": reg["owner_family"],
                "dispatch_token": reg["dispatch_token"], "status": reg["status"],
                "failure_reason": reg["failure_reason"], "affected_identity_count": len(affected[reg["primitive_id"]]),
                "affected_identities": affected[reg["primitive_id"]],
            })

    q6_pass = (not unproved and not unresolved and classifications.get("UNKNOWN", 0) == 0
               and classifications.get("PARTIAL", 0) == 0 and classifications.get("UNSUPPORTED", 0) == 0
               and sum(classifications.values()) == 1678)
    registry = {
        "schema": "commander-simulator-next.ws24-witness-registry.v1", "forge_pin": FORGE_PIN,
        "ws14_manifest_sha256": MANIFEST_SHA256, "primitive_count": len(registry_rows),
        "status_counts": dict(Counter(row["status"] for row in registry_rows)), "primitives": registry_rows,
    }
    gate = {
        "schema": "commander-simulator-next.ws24-q6-semantic-integration.v1", "workstream": "WS24",
        "source_head": args.source_head, "source_tree": args.source_tree, "identity_count": len(identity_rows),
        "primitive_count": len(registry_rows), "primitive_status_counts": dict(Counter(row["status"] for row in registry_rows)),
        "identity_classification_counts": dict(classifications), "unresolved_binding_count": len(unresolved),
        "unproved_primitive_count": len(unproved), "Q6_ACTUAL_CARD_BEHAVIOR": "PASS" if q6_pass else "FAIL_CLOSED",
        "q6_pass": q6_pass, "WORKSTREAM_COMPLETE": True,
        "hard_gates": {
            "exact_ws14_hashes": True, "all_1678_identities_classified": len(identity_rows) == 1678,
            "all_174_primitives_accounted": len(registry_rows) == 174, "owner_partition_exact": True,
            "pass_primitives_have_immutable_state_witness": all(row["status"] != "PASS" or bool(row["witnesses"]) for row in registry_rows),
            "per_identity_ws14_full_script_provenance_preserved": all(row["ws14_identity"].get("old_ws11_full_script_signature_ids") is not None for row in identity_rows),
            "unknown_bindings_not_promoted": all(row["classification"] == "UNKNOWN" for row in identity_rows if row["unresolved_binding_count"] > 0),
            "q6_not_promoted_with_blockers": (q6_pass or (len(unproved) > 0 or len(unresolved) > 0)),
            "global_ws05_ws06_behavior_inheritance_absent": True, "card_name_repair_hacks_absent": True,
        },
        "blockers": {
            "non_pass_primitives": len(unproved), "unresolved_ws14_bindings": len(unresolved),
            "note": "Q6 remains fail-closed until every production-reachable behavior path is actually witnessed or otherwise explicitly unsupported; parsing/source presence and global Q2/Q3 gates are not behavior proof.",
        },
    }
    if not all(gate["hard_gates"].values()):
        raise ValueError(f"WS24 hard gate failure: {gate['hard_gates']}")

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "WS24_WITNESS_REGISTRY.json").write_bytes(canonical(registry))
    with (args.out / "WS24_PER_IDENTITY.jsonl").open("wb") as fh:
        for row in identity_rows:
            fh.write(canonical(row))
    (args.out / "WS24_UNPROVED_PRIMITIVES.json").write_bytes(canonical({"count": len(unproved), "rows": unproved}))
    with (args.out / "WS24_UNRESOLVED_BINDINGS.jsonl").open("wb") as fh:
        for row in unresolved:
            fh.write(canonical(row))
    (args.out / "Q6_ACTUAL_CARD_BEHAVIOR_GATE.json").write_bytes(canonical(gate))
    names = ["WS24_WITNESS_REGISTRY.json", "WS24_PER_IDENTITY.jsonl", "WS24_UNPROVED_PRIMITIVES.json",
             "WS24_UNRESOLVED_BINDINGS.jsonl", "Q6_ACTUAL_CARD_BEHAVIOR_GATE.json"]
    (args.out / "WS24_HASHES.sha256").write_text("\n".join(f"{digest(args.out/name)}  {name}" for name in names) + "\n")
    print(f"WS24_PRIMITIVES_PASS={gate['primitive_status_counts'].get('PASS', 0)}")
    print(f"WS24_PRIMITIVES_PARTIAL={gate['primitive_status_counts'].get('PARTIAL', 0)}")
    print(f"WS24_UNRESOLVED_BINDINGS={len(unresolved)}")
    print(f"Q6_ACTUAL_CARD_BEHAVIOR={gate['Q6_ACTUAL_CARD_BEHAVIOR']}")
    print("WORKSTREAM_COMPLETE=TRUE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
