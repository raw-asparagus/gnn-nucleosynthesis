#!/usr/bin/env bash
# PostToolUse hook: whenever a conservation-critical artefact changes, run the
# conservation gate. Exit 2 feeds stderr back to Claude as a blocking error so
# it must address the failure immediately.
#
# Two trigger routes, because the ν matrix has two ways of changing:
#   1. Edit/Write/MultiEdit on a conservation-critical SOURCE file  -> tool_input.file_path
#   2. Bash regeneration of the exported matrix in data/stoich/     -> tool_input.command
# Route 2 exists because scripts/export_stoich_matrix.py rewrites data/stoich/*.npz
# through Bash, not through the Write tool — a path the file_path-only version of
# this hook missed entirely (CLAUDE.md invariant #1; physics-auditor trigger list).
#
# The routes are dispatched on tool_name and must NOT be merged into one pattern
# list: route 1's patterns are paths, and a Bash command line that merely mentions
# such a path (`ls data/stoich/`) is not a modification. Matching route-1 patterns
# against command strings makes every read-only mention pay for a pytest run and
# report a scary false trigger.
#
# Receives the tool-use event as JSON on stdin.

set -u

# The gate is a repo-relative pytest invocation, so it must run from the repo root.
# The session's cwd is not guaranteed to be anywhere in particular.
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0

input="$(cat)"

# Cheap pre-filter on the raw event JSON. Every trigger token below must appear
# somewhere in the payload for this event to be relevant, so a plain substring
# scan lets the overwhelmingly common irrelevant event skip the python3 spawn.
case "$input" in
  *gnn_nucleo/graph/*|*export_stoich_matrix*|*graph_metrics*|*data/stoich/*|*test_conservation*|*conftest.py*) ;;
  *) exit 0 ;;
esac

meta="$(printf '%s' "$input" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
    ti = d.get("tool_input", {}) or {}
    print(d.get("tool_name", ""))
    print(ti.get("file_path") or ti.get("command") or "")
except Exception:
    print("")
    print("")
' 2>/dev/null)"

tool_name="$(printf '%s\n' "$meta" | head -1)"
subject="$(printf '%s\n' "$meta" | tail -n +2)"

[ -z "$subject" ] && exit 0

trigger=""
case "$tool_name" in
  Edit|Write|MultiEdit|NotebookEdit)
    # Route 1 — a conservation-critical source file was modified in place.
    case "$subject" in
      *src/gnn_nucleo/graph/*|*export_stoich_matrix.py|*graph_metrics.py|*data/stoich/*|*test_conservation.py|*tests/conftest.py)
        trigger="critical file changed: $subject"
        ;;
    esac
    ;;
  Bash)
    # Route 2 — the export was regenerated through the shell. Add any new producer
    # of data/stoich/*.npz here; a producer missing from this list silently
    # bypasses the gate. Keep this list to things that WRITE the export: a
    # read-only command that merely names the path must not trigger a gate run.
    case "$subject" in
      *export_stoich_matrix.py*)
        trigger="stoichiometric export regenerated"
        ;;
    esac
    ;;
esac

[ -z "$trigger" ] && exit 0

echo "[conservation-gate] $trigger" >&2
if ! uv run pytest tests/test_conservation.py -q >&2; then
  echo "[conservation-gate] FAILED: baryon/charge/lepton conservation gate is broken." >&2
  echo "[conservation-gate] Per CLAUDE.md invariant #1, fix this before anything else." >&2
  exit 2
fi
echo "[conservation-gate] PASSED" >&2
exit 0
