#!/usr/bin/env bash
# PostToolUse hook: whenever a conservation-critical file is edited, run the
# conservation gate. Exit 2 feeds stderr back to Claude as a blocking error so
# it must address the failure immediately.
#
# Receives the tool-use event as JSON on stdin.

set -u

input="$(cat)"

file_path="$(printf '%s' "$input" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
    print(d.get("tool_input", {}).get("file_path", ""))
except Exception:
    print("")
' 2>/dev/null)"

[ -z "$file_path" ] && exit 0

case "$file_path" in
  *src/conservation/*|*export_stoich_matrix.py|*data/stoich/*|*test_conservation.py)
    echo "[conservation-gate] critical file changed: $file_path" >&2
    if ! uv run pytest tests/test_conservation.py -q >&2; then
      echo "[conservation-gate] FAILED: baryon/charge/lepton conservation gate is broken." >&2
      echo "[conservation-gate] Per CLAUDE.md invariant #1, fix this before anything else." >&2
      exit 2
    fi
    echo "[conservation-gate] PASSED" >&2
    ;;
esac

exit 0
