"""Kill-test harness (Step 6 — stub).

Will implement the Target A viability measurements on real bbq trajectories:
- active-set coverage: does {r : kappa_r > 0.1} carry >= 95% of |dYe| (and of
  |dX| for dominant isotopes) at the median timestep?
- spread failure: does net flow spread over >~30% of reactions near the
  kappa floor?
- conditioning: cond(S_active) < 1e6 pass, > 1e8 fail (between: judgement +
  RESULTS.md entry).

Priority window 3.3-5 GK; instrument the high-Ye bottleneck reaction
45Sc(p,gamma)46Ti. Entry point: scripts/run_killtest.py.
"""
