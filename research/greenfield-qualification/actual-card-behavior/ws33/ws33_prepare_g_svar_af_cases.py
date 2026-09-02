#!/usr/bin/env python3
"""Materialize the source-proven AbilityFactory-compatible subset of the 53 G SVar paths.

This is deliberately a runtime-input generator, not qualification evidence.  It preserves
the target effective path identity while replacing the forbidden direct target-SVar entry
with the topology-proven parent script.  The generated 15-column TSV is compatible with
the existing WS33 G runtime harness ABI.
"""
from __future__ import annotations

import argparse
import base64
import json
import re
from pathlib import Path

API_RE = re.compile(r"(?:^|\s\|\s)(AB|SP|DB)\$\s*([^|]+)")


def fail(msg: str) -> None:
    raise SystemExit("WS33_G_SVAR_AF_CASES=FAIL " + msg)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--topology", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    topology = json.loads(args.topology.read_text(encoding="utf-8"))
    if topology.get("status") != "PASS" or topology.get("remaining_svar_count") != 53:
        fail("input topology is not the frozen green 53-path frontier")
    cases = [c for c in topology.get("cases", []) if c["selected_parent"]["ability_factory_compatible"]]
    cases.sort(key=lambda c: c["v2_path_id"])
    if len(cases) != 21:
        fail(f"expected 21 AbilityFactory-compatible parent paths, got {len(cases)}")
    if any(c.get("requires_all_selected_parent_entrypoints") for c in cases):
        fail("multi-parent path unexpectedly entered AbilityFactory-compatible subset")

    rows: list[str] = []
    ids: set[str] = set()
    for ordinal, case in enumerate(cases, 1):
        pid = case["v2_path_id"]
        if pid in ids:
            fail(f"duplicate path id {pid}")
        ids.add(pid)
        parent = case["selected_parent"]
        script = parent["script"]
        m = API_RE.search(script)
        if not m:
            fail(f"parent script has no AbilityFactory API token for {pid}")
        source_token = m.group(1) + "$"
        parent_dispatch = m.group(2).strip()
        if not parent_dispatch:
            fail(f"empty parent dispatch for {pid}")
        # The historical harness's implementation field is not used to choose legality;
        # retain the target implementation class for evidence/debugging.
        fields = [
            ordinal,
            pid,
            case["oracle_identity"],
            case["card_name"],
            parent_dispatch,
            case["implementation_target"],
            case["source_path"],
            int(parent["source_line"]),
            parent["directive"],
            source_token,
            int(bool(case["required_hidden_info_evidence"])),
            int(bool(case["required_rng_evidence"])),
            int(bool(case["required_replay_evidence"])),
            int(bool(case["required_decision_evidence"])),
            base64.b64encode(script.encode("utf-8")).decode("ascii"),
        ]
        rows.append("\t".join(map(str, fields)))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(
        "WS33_G_SVAR_AF_CASES=PASS paths=21 entry=SOURCE_PROVEN_PARENT "
        "target_svar_direct_entry=FALSE coverage_mutated=FALSE"
    )


if __name__ == "__main__":
    main()
