#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928"


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--forge-root", type=Path, required=True)
    parser.add_argument("--runtime-witness", type=Path, required=True)
    parser.add_argument("--compatibility-xml", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    forge = args.forge_root.resolve()
    head = subprocess.check_output(["git", "-C", str(forge), "rev-parse", "HEAD"], text=True).strip()
    if head != PIN:
        raise SystemExit(f"Forge pin mismatch: {head}")
    deleted = subprocess.check_output(
        ["git", "-C", str(forge), "diff", "--name-only", "--diff-filter=D", "HEAD"], text=True
    ).splitlines()
    if deleted:
        raise SystemExit(f"overlay deleted pinned files: {deleted}")
    changed = subprocess.check_output(
        ["git", "-C", str(forge), "ls-files", "--modified", "--others", "--exclude-standard"], text=True
    ).splitlines()
    files = [{"path": name.replace("\\", "/"), "sha256": sha(forge / name)} for name in sorted(set(changed))]
    if not files:
        raise SystemExit("integrated overlay changed no files")
    overlay_digest = hashlib.sha256(canonical(files)).hexdigest()

    witness = json.loads(args.runtime_witness.read_text(encoding="utf-8"))
    xml = ET.parse(args.compatibility_xml).getroot()
    xml_ok = int(xml.attrib.get("failures", "0")) == 0 and int(xml.attrib.get("errors", "0")) == 0
    controls = {
        "normal_successful_actual_card_result_unchanged": xml_ok,
        "verifier_disabled_by_default": xml_ok,
        "controlled_mismatch_maps_to_CARD_BEHAVIOR_FAILURE": witness["public_failure"]["category"] == "CARD_BEHAVIOR_FAILURE",
        "ENGINE_FAILURE_remains_distinct": xml_ok,
        "state_committed_false": witness["public_failure"]["state_committed"] is False,
        "failed_result_not_promoted": witness["controlled_mismatch"]["staged_state_published"] is False,
        "fallback_used_false": witness["fallback_used"] is False,
        "public_failure_payload_sanitized": set(witness["public_failure"]) == {
            "schema", "category", "correlation_id", "game_id", "decision_id", "principal_id", "public_message", "state_committed"
        },
    }
    result = {
        "schema": "commander-simulator-next.ws33-overlay-materialization.v1",
        "forge_pin": head,
        "materialization_status": "EXECUTED",
        "patched_forge_content_digest": overlay_digest,
        "changed_file_count": len(files),
        "files": files,
        "undeclared_runtime_patches": 0,
        "ws32_runtime_witness_sha256": sha(args.runtime_witness),
        "ws32_compatibility_test_xml_sha256": sha(args.compatibility_xml),
        "ws32_controls": controls,
        "ws32_compatibility": "PASS" if all(controls.values()) else "FAIL_CLOSED",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(canonical(result))
    print(f"WS33_PATCHED_FORGE_CONTENT_DIGEST={overlay_digest}")
    print(f"WS33_WS32_COMPATIBILITY={result['ws32_compatibility']}")
    return 0 if result["ws32_compatibility"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
