#!/usr/bin/env bash
set -euo pipefail
src='research/greenfield-qualification/actual-card-behavior/ws33/ws33_run_a_rest_direct31_runtime_v2.sh'
tmp="${RUNNER_TEMP:-/tmp}/ws33-a-rest-direct31-runtime-v4.sh"
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
    raise SystemExit('WS33_A_REST_DIRECT_V4_DRIVER=FAIL abi gate anchor count='+str(t.count(old)))
t=t.replace(old,new,1)
old2='python "$ROOT/ws33_bind_a_rest_direct_remote_actor.py" --harness "$dst" | tee generated/diagnostic/remote-actor.log\npython "$ROOT/ws33_instrument_a_rest_direct_observation.py" --harness "$dst" | tee generated/diagnostic/observation-instrument.log\n'
new2='python "$ROOT/ws33_bind_a_rest_direct_remote_actor.py" --harness "$dst" | tee generated/diagnostic/remote-actor.log\npython "$ROOT/ws33_refresh_a_rest_direct_mana_fixture.py" --harness "$dst" | tee generated/diagnostic/mana-fixture-refresh.log\npython "$ROOT/ws33_instrument_a_rest_direct_observation.py" --harness "$dst" | tee generated/diagnostic/observation-instrument.log\n'
if t.count(old2)!=1:
    raise SystemExit('WS33_A_REST_DIRECT_V4_DRIVER=FAIL mana patch insertion anchor count='+str(t.count(old2)))
t=t.replace(old2,new2,1)
old3="grep -F 'WS33_A_REST_DIRECT_REMOTE_ACTOR=PASS' generated/diagnostic/remote-actor.log\n"
new3=old3+"grep -Fx 'WS33_A_REST_DIRECT_MANA_FIXTURE=PASS refresh=Card.untap per_case=true mana_pool_injection=0 cost_bypass=0' generated/diagnostic/mana-fixture-refresh.log\n"
if t.count(old3)!=1:
    raise SystemExit('WS33_A_REST_DIRECT_V4_DRIVER=FAIL mana assertion insertion anchor count='+str(t.count(old3)))
t=t.replace(old3,new3,1)
p.write_text(t)
print('WS33_A_REST_DIRECT_V4_DRIVER=PASS change=PER_CASE_REAL_LAND_UNTAP_ONLY runtime_rules_mutation=FALSE')
PY
bash "$tmp"
