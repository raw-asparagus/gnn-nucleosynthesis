# 0001 — Target A (signed net flux through fixed stoichiometric matrix) is the default head
Date: 2026-07-05    Status: accepted (conditional on Phase-0 kill-test)

## Decision
Primary output head predicts signed net per-reaction flux phi in an internal asinh
latent; dY = nu @ phi through the FIXED pynucastro stoichiometric matrix. Target B
(direct dY + null-space projection, linear output space only) is built as benchmark
and fallback.

## Basis
- sourced: QSE cancellation pathology (Hix & Thielemann 1996/1999; Guidry 2011/2013);
  flux-target machine-precision conservation (Sturm & Wexler 2020/2022); asinh latent
  (Doeppel & Votsmeier 2023); NuGNN documented log-space conservation instability
  (Kim et al. 2026, arXiv:2606.04491).
- assumed: asinh latent trains stably at silicon-burning dynamic range (no prior work
  at this scale) — retired by Phase-0 training runs.

## Switch condition
Switch to Target B if cond(S_active) > 1e6, or if > ~90% of reactions carry net flux
below the Ye floor at the median timestep, or if Target B matches A rollout stability
with per-step |dYe| <= 2x A and is materially simpler to train.
