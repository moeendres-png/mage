#!/usr/bin/env bash
set -euo pipefail

jar="$1"
deck="$2"
players="$3"
seed="$4"
timeout_s="${5:-90}"

args=(sim -f commander -d)
for ((i=0; i<players; i++)); do
  args+=("$deck")
done
args+=(-n 1 -s "$seed" -c "$timeout_s" -q)

set +e
output=$(xvfb-run -a java -jar "$jar" "${args[@]}" 2>&1)
rc=$?
set -e
printf '%s\n' "$output"

if [[ $rc -ne 0 ]]; then
  echo "FORGE_PROBE_ERROR=process_exit_$rc" >&2
  exit "$rc"
fi
if grep -Fq "Could not load deck" <<<"$output"; then
  echo "FORGE_PROBE_ERROR=deck_load" >&2
  exit 20
fi
if grep -Fq "Unknown mode" <<<"$output"; then
  echo "FORGE_PROBE_ERROR=entrypoint" >&2
  exit 21
fi
if ! grep -Fq "Game Result:" <<<"$output"; then
  echo "FORGE_PROBE_ERROR=no_terminal_result" >&2
  exit 22
fi

# Emit a timing-normalized semantic transcript on stderr for cross-process diff.
printf '%s\n' "$output" \
  | sed -E 's/Took [0-9]+ ms/Took <ms>/g; s/ended in [0-9]+ ms/ended in <ms>/g' \
  | sed -E '/^[[:space:]]*$/d' >&2
