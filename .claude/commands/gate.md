---
description: Run the conservation gate and drift diagnostics, numbers only
argument-hint: [matrix file, e.g. data/stoich/nu_mesa80.npz]
---

Delegate to `physics-auditor`: run the conservation gate and drift diagnostics
for **$ARGUMENTS** (default: whatever ν exports exist under `data/stoich/`).

Required in the report:
- max baryon drift |Σ Aᵢ dYᵢ| and charge-to-lepton closure residual, against the
  ≤1e-12 per-step float64 gate;
- confirmation that dYₑ through weak columns is NONZERO under random flux — a run
  where it vanishes is a FAILURE even when every drift residual is clean;
- cond(S_active), against the 1e6 Target-A→Target-B switch trigger.

Numbers must come from commands executed in this session. If an input is missing,
name the script that generates it and stop.
