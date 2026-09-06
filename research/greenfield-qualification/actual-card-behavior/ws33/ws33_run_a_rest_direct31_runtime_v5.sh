#!/usr/bin/env bash
set -euo pipefail

ROOT='research/greenfield-qualification/actual-card-behavior/ws33'
src="$ROOT/ws33_run_a_rest_direct31_runtime_v2.sh"
tmp="${RUNNER_TEMP:-/tmp}/ws33-a-rest-direct31-runtime-v5.sh"
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
    raise SystemExit('WS33_A_REST_DIRECT_V5_DRIVER=FAIL abi gate anchor count='+str(t.count(old)))
t=t.replace(old,new,1)

old2='python "$ROOT/ws33_bind_a_rest_direct_remote_actor.py" --harness "$dst" | tee generated/diagnostic/remote-actor.log\npython "$ROOT/ws33_instrument_a_rest_direct_observation.py" --harness "$dst" | tee generated/diagnostic/observation-instrument.log\n'
new2='python "$ROOT/ws33_bind_a_rest_direct_remote_actor.py" --harness "$dst" | tee generated/diagnostic/remote-actor.log\npython "$ROOT/ws33_refresh_a_rest_direct_mana_fixture.py" --harness "$dst" | tee generated/diagnostic/mana-fixture-refresh.log\npython "$ROOT/ws33_instrument_a_rest_direct_observation.py" --harness "$dst" | tee generated/diagnostic/observation-instrument.log\n'
if t.count(old2)!=1:
    raise SystemExit('WS33_A_REST_DIRECT_V5_DRIVER=FAIL mana fixture insertion anchor count='+str(t.count(old2)))
t=t.replace(old2,new2,1)

old3="grep -F 'WS33_A_REST_DIRECT_REMOTE_ACTOR=PASS' generated/diagnostic/remote-actor.log\n"
new3=old3+"grep -Fx 'WS33_A_REST_DIRECT_MANA_FIXTURE=PASS refresh=Card.untap per_case=true mana_pool_injection=0 cost_bypass=0' generated/diagnostic/mana-fixture-refresh.log\n"
if t.count(old3)!=1:
    raise SystemExit('WS33_A_REST_DIRECT_V5_DRIVER=FAIL mana fixture assertion anchor count='+str(t.count(old3)))
t=t.replace(old3,new3,1)

observer='python "$ROOT/runtime-overlays/apply-ws33-a-rest-play-stage-observer.py" --forge-root forge | tee generated/overlay-logs/ws33-a-rest-play-stage.log\n'
normalizer=observer+'python "$ROOT/runtime-overlays/apply-ws33-mana-cancel-boundary.py" --forge-root forge | tee generated/overlay-logs/ws33-mana-cancel-boundary.log\n'
if t.count(observer)!=1:
    raise SystemExit('WS33_A_REST_DIRECT_V5_DRIVER=FAIL cancel normalization insertion anchor count='+str(t.count(observer)))
t=t.replace(observer,normalizer,1)

observer_gate="grep -Fx 'WS33_A_REST_PLAY_STAGE_OBSERVER=PASS semantics_mutated=FALSE booleans_mutated=FALSE' generated/overlay-logs/ws33-a-rest-play-stage.log\n"
normalizer_gate=observer_gate+"grep -F 'WS33_MANA_CANCEL_BOUNDARY=PASS cancel_encoding=REQUEST_LEVEL ordinary_cancel_option=FALSE rail=TRACED' generated/overlay-logs/ws33-mana-cancel-boundary.log\ngrep -Fx 'WS33_MANA_CANCEL_RULES_MUTATION=0 payment_transition_filter=FORGE payment_revalidation=FORGE' generated/overlay-logs/ws33-mana-cancel-boundary.log\n! grep -F 'actions.add(\"CANCEL\")' forge/forge-gui/src/main/java/forge/gamemodes/match/input/InputPayMana.java\ngrep -F 'actions, 1, 1, !mandatory, false, \"MANA_PAYMENT\"' forge/forge-gui/src/main/java/forge/gamemodes/match/input/InputPayMana.java\ngrep -F 'isManaAbilityFor(saPaidFor, colorCanUse)' forge/forge-gui/src/main/java/forge/gamemodes/match/input/InputPayMana.java\n"
if t.count(observer_gate)!=1:
    raise SystemExit('WS33_A_REST_DIRECT_V5_DRIVER=FAIL cancel assertion insertion anchor count='+str(t.count(observer_gate)))
t=t.replace(observer_gate,normalizer_gate,1)

p.write_text(t)
print('WS33_A_REST_DIRECT_V5_DRIVER=PASS delta=MANA_CANCEL_ENCODING_ONLY mana_legality=FORGE cost_payment=FORGE')
PY

bash "$tmp"
