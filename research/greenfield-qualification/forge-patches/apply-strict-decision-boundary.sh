#!/usr/bin/env bash
set -euo pipefail

forge_root=${1:?Forge checkout path required}
patch_file=${2:?Patch file required}
expected_pin=8c7e9afb8e6caee88644b94e25da5852e36f8928

# Resolve both inputs before invoking `git -C`. Git resolves a relative
# --patch path from the selected repository, not from the caller's directory.
forge_root=$(cd "$forge_root" && pwd)
patch_file=$(cd "$(dirname "$patch_file")" && pwd)/$(basename "$patch_file")
patch_dir=$(dirname "$patch_file")

actual_pin=$(git -C "$forge_root" rev-parse HEAD)
test "$actual_pin" = "$expected_pin"
git -C "$forge_root" apply --check "$patch_file"
git -C "$forge_root" apply "$patch_file"
test -f "$forge_root/forge-gui/src/main/java/forge/gamemodes/match/input/ExternalDecisionRequest.java"
test -f "$forge_root/forge-gui/src/main/java/forge/gamemodes/match/input/ExternalDecisionValidator.java"

ws01_patcher="$patch_dir/apply-ws01-full-decision-boundary.py"
if [[ -f "$ws01_patcher" ]]; then
  python3 "$ws01_patcher" "$forge_root"
fi

echo "STRICT_DECISION_PATCH_APPLIED=TRUE"
echo "FORGE_PIN=$actual_pin"
