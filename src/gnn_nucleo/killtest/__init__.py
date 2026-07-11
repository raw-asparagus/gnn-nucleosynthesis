"""QSE-cancellation kill-test measurement package (Step 6, Task 2).

Measures — never concludes: thresholds live in docs/phase0-checklist.md and
docs/phase0-killtest-verdict.md. Driven by scripts/run_killtest.py.

Submodules: strata (T9/Yₑ bins), distributions (streaming κ over FluxStore
runs), active_set (Guidry masks / cond(S_active) / top-k / churn /
timescale-separation primitives), manifold (relaxed-row assembly with δ_r
and the pre-stall guard).
"""

from . import active_set, distributions, manifold, strata

__all__ = ["active_set", "distributions", "manifold", "strata"]
