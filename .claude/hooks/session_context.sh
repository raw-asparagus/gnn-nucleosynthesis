#!/usr/bin/env bash
# SessionStart hook: surface just enough project state that the first plan of a
# session is anchored to where the work actually is, rather than to whatever the
# prompt happens to mention. Deliberately terse — this cost is paid every session.

set -u
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0

last_result="$(grep -oE '^\| 20[0-9]{2}-[0-9]{2}-[0-9]{2} \|' RESULTS.md 2>/dev/null | tail -1 | tr -d '|' | xargs)"
open_items="$(grep -cE '^[[:space:]]*[-*] \[ \]' docs/phase0-checklist.md 2>/dev/null || echo 0)"
last_adr="$(ls docs/decisions/[0-9]*.md 2>/dev/null | tail -1 | xargs -r basename)"

python3 - "$last_result" "$open_items" "$last_adr" <<'PY'
import json, sys
last_result, open_items, last_adr = (sys.argv[1:4] + ["", "", ""])[:3]
lines = [
    f"Project state: last RESULTS.md row {last_result or 'none'}; "
    f"{open_items or '0'} open phase-0 checklist items; latest ADR {last_adr or 'none'}.",
    "Before implementing against a physics invariant or gate, plan first and "
    "delegate per the 'Delegation and planning policy' section of CLAUDE.md.",
]
print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": " ".join(lines),
    }
}))
PY
