#!/usr/bin/env bash
set -euo pipefail

forge_root=${1:?Forge checkout path required}
patch_file=${2:?Patch file required}
expected_pin=8c7e9afb8e6caee88644b94e25da5852e36f8928

forge_root=$(cd "$forge_root" && pwd)
patch_file=$(cd "$(dirname "$patch_file")" && pwd)/$(basename "$patch_file")
patch_dir=$(dirname "$patch_file")

actual_pin=$(git -C "$forge_root" rev-parse HEAD)
test "$actual_pin" = "$expected_pin"
git -C "$forge_root" apply --check "$patch_file"
git -C "$forge_root" apply "$patch_file"
test -f "$forge_root/forge-gui/src/main/java/forge/gamemodes/match/input/ExternalDecisionRequest.java"
test -f "$forge_root/forge-gui/src/main/java/forge/gamemodes/match/input/ExternalDecisionValidator.java"

for patcher in \
  apply-ws01-full-decision-boundary.py \
  apply-ws01-compile-fixes.py \
  apply-ws01-production-decision-bridge.py \
  apply-ws01-combat-damage-bridge.py \
  apply-ws01-target-decision-bridge.py \
  apply-ws01-synchronized-input-bridge.py \
  apply-ws01-ability-choice-bridge.py \
  apply-ws01-mana-convoke-bridge.py \
  apply-ws01-full-game-closeout.py \
  apply-ws01-full-game-test.py
do
  if [[ -f "$patch_dir/$patcher" ]]; then
    python3 "$patch_dir/$patcher" "$forge_root"
  fi
done

echo "STRICT_DECISION_PATCH_APPLIED=TRUE"
echo "FORGE_PIN=$actual_pin"
