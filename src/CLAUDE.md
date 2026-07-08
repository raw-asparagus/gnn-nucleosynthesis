# src/ — implementation notes for Claude Code

- Everything runs under `uv run`; never conda, never pip.
- float64 for anything touching conservation, the constraint matrices, or the
  X_{t+dt} = X_t + dX update. float32 is allowed inside model internals only.
- `src/gnn_nucleo/graph/` is conservation-critical (it superseded the old
  `src/conservation/` stub in Step 3, ADR 0002): any edit here triggers the
  PostToolUse hook that runs tests/test_conservation.py. Keep this module free
  of ML dependencies (numpy/pyyaml/pynucastro/networkx only — no torch) so the
  gate stays fast.
- Component boundaries follow docs/: backbone (Component A), output heads /
  conservation map / mask (Component B), temporal head + rollout (C/D).
- The equilibrium mask's eligible set must exclude weak columns structurally
  (a boolean built from weak_mask at construction time), not by convention.
