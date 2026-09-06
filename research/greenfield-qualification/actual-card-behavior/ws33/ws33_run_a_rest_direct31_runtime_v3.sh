#!/usr/bin/env bash
set -euo pipefail
src='research/greenfield-qualification/actual-card-behavior/ws33/ws33_run_a_rest_direct31_runtime_v2.sh'
tmp="${RUNNER_TEMP:-/tmp}/ws33-a-rest-direct31-runtime-v3.sh"
cp "$src" "$tmp"
python - "$tmp" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); t=p.read_text()
old="grep -Fx 'WS33_A_REST_DIRECT_CASE_ABI=PASS implementation=forge.game.spellability.TargetRestrictions rules_mutation=0' generated/diagnostic/case-abi-repair.log\n"
new="""grep -Fx 'WS33_A_REST_DIRECT_CASE_ABI=PASS' generated/diagnostic/case-abi-repair.log
grep -Fx 'WS33_A_REST_DIRECT_IMPLEMENTATION=forge.game.spellability.TargetRestrictions' generated/diagnostic/case-abi-repair.log
grep -Fx 'WS33_A_REST_DIRECT_CASE_ABI_RULES_MUTATION=0' generated/diagnostic/case-abi-repair.log
"""
if t.count(old)!=1:
    raise SystemExit('WS33_A_REST_DIRECT_V3_DRIVER=FAIL gate anchor count='+str(t.count(old)))
p.write_text(t.replace(old,new,1))
print('WS33_A_REST_DIRECT_V3_DRIVER=PASS change=ABI_ATTESTATION_GATE_ONLY runtime_semantics_mutated=FALSE')
PY
bash "$tmp"
