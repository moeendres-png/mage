#!/usr/bin/env bash
set -euo pipefail

ROOT='research/greenfield-qualification/actual-card-behavior/ws33'
FORGE_PIN='8c7e9afb8e6caee88644b94e25da5852e36f8928'
TOPOLOGY_RUN_ID='34002894410'
TOPOLOGY_ARTIFACT_ID='9980023181'
TOPOLOGY_ARTIFACT_DIGEST='sha256:053ca7036eec2e13dd66022975a7f766e9c8c9ebc3cc30576ab03eaab99cb995'
TOPOLOGY_SOURCE_HEAD='60fa4ff1b224ede4983087a9c28bb6bbc89c728c'
TOPOLOGY_SOURCE_TREE='88f5d5460f10364a20d03e8c37854a7793eb00c0'
DIRECT_RUNTIME_SOURCE_HEAD='d8af15cb879bdfc3c40ce4cba3462da24ee3f272'
WS01_HEAD='bf089ea806f54a9bbb64ede205915729e3629684'
WS12_HEAD='80743bdbc2950b00e422f3deb38f04111f30a4d4'
WS32_HEAD='6ca2a7bbacd074cc84fa4a6019c4d26e5e3717a9'
WS31_HIST_HEAD='b09fe7c16845cddbbfe30fd1f855b59234bbf007'
: "${GITHUB_SHA:?GITHUB_SHA required}"
: "${GITHUB_REPOSITORY:?GITHUB_REPOSITORY required}"
: "${GITHUB_WORKSPACE:?GITHUB_WORKSPACE required}"
: "${GH_TOKEN:?GH_TOKEN required}"

rm -rf generated
mkdir -p generated/topology generated/source generated/record generated/replay generated/diagnostic generated/overlay-logs
printf '%s\n' "$GITHUB_SHA" > generated/diagnostic/workflow-source-head.txt
git rev-parse 'HEAD^{tree}' > generated/diagnostic/workflow-source-tree.txt

# Immutable topology input.
meta="$(gh api "repos/$GITHUB_REPOSITORY/actions/artifacts/$TOPOLOGY_ARTIFACT_ID")"
test "$(jq -r .digest <<<"$meta")" = "$TOPOLOGY_ARTIFACT_DIGEST"
test "$(jq -r .workflow_run.id <<<"$meta")" = "$TOPOLOGY_RUN_ID"
test "$(jq -r .workflow_run.head_sha <<<"$meta")" = "$TOPOLOGY_SOURCE_HEAD"
gh api -H 'Accept: application/vnd.github+json' "repos/$GITHUB_REPOSITORY/actions/artifacts/$TOPOLOGY_ARTIFACT_ID/zip" > generated/topology.zip
test "sha256:$(sha256sum generated/topology.zip | cut -d' ' -f1)" = "$TOPOLOGY_ARTIFACT_DIGEST"
unzip -q generated/topology.zip -d generated/topology
jq -e --arg h "$TOPOLOGY_SOURCE_HEAD" --arg t "$TOPOLOGY_SOURCE_TREE" '
  .status=="PASS" and .source_head==$h and .source_tree==$t and
  .a_rest_paths==57 and .direct_paths==31 and .svar_paths==26 and
  .coverage_mutated==false and .coverage_promotion==false
' generated/topology/out/A_REST_TOPOLOGY_GATE.json
cp generated/topology/out/a-rest-direct.tsv generated/source/a-rest-direct.tsv
python - <<'PY'
from pathlib import Path
rows=[x.split('\t') for x in Path('generated/source/a-rest-direct.tsv').read_text().splitlines() if x]
assert len(rows)==31 and all(len(x)==19 for x in rows) and len({x[1] for x in rows})==31
assert sum(x[6]=='SP' for x in rows)==24
assert sum(x[6]=='AB' for x in rows)==7
assert sum(x[15]=='1' for x in rows)==31
assert sum(x[16]=='1' for x in rows)==2
assert sum(x[17]=='1' for x in rows)==31
assert sum(x[18]=='1' for x in rows)==31
print('WS33_A_REST_DIRECT31_CASES=PASS paths=31 spells=24 activated=7 decision=31 rng=2 hidden=31 replay=31')
PY

# Exact retained source pins supplied by Actions checkout steps.
test "$(git -C forge rev-parse HEAD)" = "$FORGE_PIN"
test "$(git -C direct-source rev-parse HEAD)" = "$DIRECT_RUNTIME_SOURCE_HEAD"
test "$(git -C ws01 rev-parse HEAD)" = "$WS01_HEAD"
test "$(git -C ws12 rev-parse HEAD)" = "$WS12_HEAD"
test "$(git -C ws32 rev-parse HEAD)" = "$WS32_HEAD"
test "$(git -C ws31-historical rev-parse HEAD)" = "$WS31_HIST_HEAD"

# Qualified production boundary overlays. All are fail-closed and observation/externalization only.
bash ws01/research/greenfield-qualification/forge-patches/apply-strict-decision-boundary.sh forge ws01/research/greenfield-qualification/forge-patches/strict-decision-boundary.patch | tee generated/overlay-logs/ws01.log
python direct-source/research/greenfield-qualification/forge-patches/apply-ws05-hidden-info-overlay.py forge | tee generated/overlay-logs/ws05.log
cp direct-source/research/greenfield-qualification/hidden-info/Ws05HiddenInfoProbe.java forge/forge-gui-desktop/src/test/java/forge/net/Ws05HiddenInfoProbe.java
python direct-source/research/greenfield-qualification/forge-patches/apply-ws06-rng-replay-overlay.py forge --inventory generated/record/RNG_INVENTORY.json | tee generated/overlay-logs/ws06.log
python "$ROOT/runtime-overlays/apply-ws33-input-confirm.py" --forge-root forge | tee generated/overlay-logs/ws33-input-confirm.log
python "$ROOT/runtime-overlays/apply-ws33-observation-fanout.py" --forge-root forge | tee generated/overlay-logs/ws33-observation-fanout.log
python "$ROOT/runtime-overlays/apply-ws33-external-card-decision-lifetime.py" --forge-root forge | tee generated/overlay-logs/ws33-card-decision-lifetime.log
python "$ROOT/runtime-overlays/apply-ws33-stack-target.py" --forge-root forge | tee generated/overlay-logs/ws33-stack-target.log
python "$ROOT/runtime-overlays/apply-ws33-target-selection.py" --forge-root forge | tee generated/overlay-logs/ws33-target-selection.log
python "$ROOT/runtime-overlays/apply-ws33-stack-resolution-reachability.py" --forge-root forge | tee generated/overlay-logs/ws33-stack-resolution.log
python ws12/research/greenfield-qualification/failure-semantics/apply-ws12-forge-overlay.py --forge-root forge | tee generated/overlay-logs/ws12.log
python ws32/research/greenfield-qualification/actual-card-behavior/ws32/apply_ws32_card_behavior_production_binding.py --forge-root forge | tee generated/overlay-logs/ws32.log
grep -Fx 'WS33_OBSERVATION_FANOUT=PASS' generated/overlay-logs/ws33-observation-fanout.log
grep -Fx 'WS33_EXTERNAL_CARD_DECISION_LIFETIME=PASS' generated/overlay-logs/ws33-card-decision-lifetime.log
grep -Fx 'WS33_FORGE_TEMP_SHOW_RULES_MUTATION=0' generated/overlay-logs/ws33-card-decision-lifetime.log
grep -Fx 'WS33_FORGE_TEMP_SHOW_PILOT_FALLBACK=0' generated/overlay-logs/ws33-card-decision-lifetime.log

# Source-bound actual-card harness.
src='ws31-historical/research/greenfield-qualification/actual-card-behavior/ws31/forge-overlay/Ws31HiddenRngReplayQualificationTest.java'
dst='forge/forge-gui-desktop/src/test/java/forge/net/Ws33ARestDirectQualificationTest.java'
python "$ROOT/ws33_prepare_g_ability_harness.py" --source "$src" --out "$dst"
python "$ROOT/ws33_prepare_a_rest_direct_harness.py" --harness "$dst" | tee generated/diagnostic/harness-adapter.log
grep -F 'WS33_A_REST_DIRECT_HARNESS=PASS' generated/diagnostic/harness-adapter.log
grep -F 'PlaySpellAbility.playSpellAbility(actor.getController(),actor,sa)' "$dst"
grep -F 'resolveActualSourceAbility(spec,source)' "$dst"
grep -F 'MagicStack.setWs33ResolutionObserver' "$dst"
! grep -F 'sa.resolve()' "$dst"
! grep -F 'sa.getTargets().add(' "$dst"
! grep -F 'AbilityFactory.getAbility(spec.script,source)' "$dst"
sha256sum "$dst" | tee generated/diagnostic/harness.sha256

# Fresh record process.
(cd forge && xvfb-run -a mvn -B -pl forge-gui-desktop -am \
  -Dtest=forge.net.Ws33ARestDirectQualificationTest \
  -Dws31.cases="$GITHUB_WORKSPACE/generated/source/a-rest-direct.tsv" \
  -Dws31.outDir="$GITHUB_WORKSPACE/generated/record" -Dws31.mode=record \
  -Dsurefire.failIfNoSpecifiedTests=false -DfailIfNoTests=false test) 2>&1 | tee generated/record/runtime.log
test -s generated/record/case-summary.tsv
test -s generated/record/decision-tape.tsv
test -s generated/record/rng-tape.tsv
! grep -F "[Couldn't add to stack, failed to target]" generated/record/runtime.log

python - <<'PY'
import json
from pathlib import Path
cases={r[1]:r for r in (x.split('\t') for x in Path('generated/source/a-rest-direct.tsv').read_text().splitlines() if x)}
rows={r[0]:r for r in (x.split('\t') for x in Path('generated/record/case-summary.tsv').read_text().splitlines() if x)}
failures=[]
if len(cases)!=31 or len(rows)!=31 or set(cases)!=set(rows): failures.append('record_path_set_mismatch')
for pid,c in cases.items():
    r=rows.get(pid)
    if r is None: continue
    if len(r)<21: failures.append(pid+':summary_schema'); continue
    if r[4]!='PASS': failures.append(pid+':status='+r[4])
    if int(r[18])!=1 or int(r[19])!=1 or int(r[20])<1: failures.append(pid+':stack_or_source_root')
    if int(r[9])!=0 or int(r[10])!=0: failures.append(pid+':hidden_leak')
    if c[15]=='1' and int(r[7])<=0: failures.append(pid+':missing_decision')
    if c[16]=='1' and int(r[8])<=0: failures.append(pid+':missing_rng')
out={'schema':'commander-simulator-next.ws33-a-rest-direct31-record.v1','status':'PASS' if not failures else 'FAIL_CLOSED','path_count':31,'failure_count':len(failures),'failures':failures,'coverage_mutated':False,'coverage_promotion':False}
Path('generated/diagnostic/DIRECT31_RECORD_GATE.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,sort_keys=True))
assert not failures, failures[:30]
PY

# Fresh replay process using only recorded Decision/RNG tapes.
(cd forge && xvfb-run -a mvn -B -pl forge-gui-desktop -am \
  -Dtest=forge.net.Ws33ARestDirectQualificationTest \
  -Dws31.cases="$GITHUB_WORKSPACE/generated/source/a-rest-direct.tsv" \
  -Dws31.outDir="$GITHUB_WORKSPACE/generated/replay" -Dws31.mode=replay \
  -Dws31.decisionReplay="$GITHUB_WORKSPACE/generated/record/decision-tape.tsv" \
  -Dws31.rngReplay="$GITHUB_WORKSPACE/generated/record/rng-tape.tsv" \
  -Dsurefire.failIfNoSpecifiedTests=false -DfailIfNoTests=false test) 2>&1 | tee generated/replay/runtime.log
test -s generated/replay/case-summary.tsv
! grep -F "[Couldn't add to stack, failed to target]" generated/replay/runtime.log

python - <<'PY'
import json
from pathlib import Path
cases={r[1]:r for r in (x.split('\t') for x in Path('generated/source/a-rest-direct.tsv').read_text().splitlines() if x)}
rec={r[0]:r for r in (x.split('\t') for x in Path('generated/record/case-summary.tsv').read_text().splitlines() if x)}
rep={r[0]:r for r in (x.split('\t') for x in Path('generated/replay/case-summary.tsv').read_text().splitlines() if x)}
failures=[]
if len(rep)!=31 or set(rep)!=set(cases): failures.append('replay_path_set_mismatch')
for pid,c in cases.items():
    a=rec.get(pid); b=rep.get(pid)
    if a is None or b is None: continue
    if len(a)<21 or len(b)<21: failures.append(pid+':summary_schema'); continue
    if b[4]!='PASS': failures.append(pid+':replay_status='+b[4])
    if int(b[18])!=1 or int(b[19])!=1 or int(b[20])<1: failures.append(pid+':replay_stack_or_source_root')
    if int(b[9])!=0 or int(b[10])!=0: failures.append(pid+':replay_hidden_leak')
    if c[15]=='1' and int(b[7])<=0: failures.append(pid+':replay_missing_decision')
    if c[16]=='1' and int(b[8])<=0: failures.append(pid+':replay_missing_rng')
    if a[5]!=b[5] or a[6]!=b[6]: failures.append(pid+':semantic_digest_mismatch')
out={'schema':'commander-simulator-next.ws33-a-rest-direct31-runtime.v1','status':'PASS' if not failures else 'FAIL_CLOSED','path_count':31,'spell_paths':24,'activated_paths':7,'decision_required':31,'rng_required':2,'hidden_required':31,'replay_required':31,'actual_card_source_bound':True,'play_spell_ability_authoritative':True,'manual_target_injection':False,'direct_effect_resolution':False,'semantic_replay_equal':not failures,'failure_count':len(failures),'failures':failures,'coverage_mutated':False,'coverage_promotion':False}
Path('generated/diagnostic/DIRECT31_RUNTIME_GATE.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,sort_keys=True))
assert not failures, failures[:30]
PY

jq -n \
  --arg head "$(cat generated/diagnostic/workflow-source-head.txt)" \
  --arg tree "$(cat generated/diagnostic/workflow-source-tree.txt)" \
  --arg forge "$FORGE_PIN" --arg topo "$TOPOLOGY_ARTIFACT_DIGEST" \
  '{schema:"commander-simulator-next.ws33-a-rest-direct31-source-chain.v1",workflow_source_head:$head,workflow_source_tree:$tree,forge_pin:$forge,topology_artifact_id:9980023181,topology_artifact_digest:$topo,coverage_mutated:false,coverage_promotion:false}' \
  > generated/diagnostic/SOURCE_CHAIN.json
(cd generated && find source record replay diagnostic overlay-logs -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum) > generated/SHA256SUMS
echo 'WS33_A_REST_DIRECT31_RUNTIME=PASS'
echo 'WS33_A_REST_DIRECT31_COVERAGE_MUTATED=FALSE'
echo 'WS33_A_REST_DIRECT31_COVERAGE_PROMOTION=FALSE'
