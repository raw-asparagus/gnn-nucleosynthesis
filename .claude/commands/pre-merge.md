---
description: Full pre-merge verification chain before committing substantive changes
---

Run the pre-merge chain on the current working tree.

Sequential where a step's result changes the next, parallel where it does not.

1. **Scope it.** `git status` and `git diff` — establish exactly what changed. If
   nothing substantive changed, say so and stop; this chain is not free.
2. **In parallel:**
   - `test-runner` — full pytest suite. `tests/test_conservation.py` is the floor;
     a failure there stops everything else.
   - `physics-auditor` — conservation gate and drift diagnostics on the current tree.
3. **If behaviour changed** (conservation map, mask, feature set, loss, temporal head,
   or any gate/threshold): delegate to `docs-sync` with the changed paths and a
   one-line intent. CLAUDE.md requires the docs update in the SAME commit.
   A code↔docs conflict reported by `docs-sync` is blocking — resolve it explicitly,
   never by rewriting the doc to match the code.
4. **Then** `referee` over the resulting diff plus the docs edits. Run this after
   `docs-sync`, not alongside it, so the referee reviews what will actually land.
5. **If any number changed**, append a row to `RESULTS.md` with date, commit hash,
   producing script, and data provenance.

Report failures and blocking findings only. Do not commit — present the verdict and
let the user decide.
