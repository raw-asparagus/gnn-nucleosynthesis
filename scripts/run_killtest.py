#!/usr/bin/env python3
"""Phase-0 QSE-cancellation kill-test skeleton.

Measures, per (T9, rho, Ye, dt) grid point and per reaction r:
  kappa_r = |phi_r| / (f_r+ + f_r-)         cancellation ratio (0 = equilibrated)
  delta_r = max_i |Y_i - Ybar_i| / Ybar_i   Guidry equilibrium deviation
plus the fraction of |dYe| carried by the top-k reactions and cond(S_active).

Pass/fail thresholds live in docs/phase0-checklist.md; do NOT hardcode
conclusions here — this script only measures.

DATA-PROVENANCE DEPENDENCIES (must be resolved before conclusions are drawn;
see docs — 'The QSE-cancellation kill-test'):
  1. Gross fluxes f+ / f- are NOT in the Zenodo record; recompute externally from
     REACLIB rates x abundances x screening.
  2. Equilibrium abundances Ybar require an independent C(A,Z) QSE solver
     (Hix & Thielemann Eqs. 2-7) — implement in src/ and import here.
  3. Screen for detailed-balance/multi-body rate artifacts (the Grichener
     Appendix-B class of bug) BEFORE trusting any kappa_r near the floor.
"""
from __future__ import annotations

import argparse
import itertools

T9_GRID  = [1.6, 2.5, 3.3, 4.0, 5.0, 6.3, 7.9]
RHO_GRID = [1e7, 1e8, 1e9]
YE_GRID  = [0.45, 0.48, 0.498]
DT_GRID  = [1e-6, 1e-3, 1.0, 1e2]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stoich", default="data/stoich/nu_mesa80.npz")
    ap.add_argument("--states", default=None,
                    help="path to sampled composition states (Zenodo Sobol or new bbq runs)")
    ap.add_argument("--out", default="data/killtest/")
    ap.parse_args()  # skeleton: CLI validated; args consumed once Step 6 lands

    grid = list(itertools.product(T9_GRID, RHO_GRID, YE_GRID, DT_GRID))
    print(f"kill-test grid: {len(grid)} (T9, rho, Ye, dt) points")
    print("NOT IMPLEMENTED YET — blocked on:")
    print("  [ ] gross-flux recomputation module (src/killtest/gross_fluxes.py)")
    print("  [ ] independent C(A,Z) QSE solver (src/killtest/qse_solver.py)")
    print("  [ ] detailed-balance artifact screen")
    print("  [ ] composition states (--states): Zenodo Sobol grids or new bbq runs")
    raise SystemExit(2)


if __name__ == "__main__":
    main()
