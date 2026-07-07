#!/usr/bin/env python3
"""Drift diagnostics on an exported stoichiometric matrix.

Usage: uv run python scripts/check_conservation.py data/stoich/nu_mesa80.npz

Reports (per root CLAUDE.md invariants):
  D_A   = max_j |A . nu_j|                (baryon drift, must be <= 1e-12 scaled)
  D_Q   = max weak-column lepton-closure residual |Z . nu_j - d_electron_j|
  dYe   = Z . (nu @ phi_weak) under random flux  (MUST be nonzero — the physics)
  cond  = condition number of full nu
"""
from __future__ import annotations

import sys

import numpy as np


def main(path: str) -> int:
    d = np.load(path, allow_pickle=False)
    nu, A, Z = (np.asarray(d[k], dtype=np.float64) for k in ("nu", "A", "Z"))
    weak = np.asarray(d["weak_mask"], dtype=bool)
    d_e = np.asarray(d["d_electron"], dtype=np.float64)
    n_s, n_r = nu.shape

    D_A = max(abs(float(A @ nu[:, j])) for j in range(n_r))
    D_Q = max((abs(float(Z @ nu[:, j]) - d_e[j]) for j in np.flatnonzero(weak)), default=0.0)
    D_Q_strong = max((abs(float(Z @ nu[:, j])) for j in np.flatnonzero(~weak)), default=0.0)

    rng = np.random.default_rng(0)
    phi = rng.standard_normal(n_r) * 10.0 ** rng.uniform(-12, 0, n_r)
    dYe_weak = float(Z @ (nu @ np.where(weak, phi, 0.0)))

    print(f"matrix: {n_s} species x {n_r} reactions, {int(weak.sum())} weak columns")
    print(f"D_A (baryon drift, max col)        = {D_A:.3e}   [<= 1e-12 required]")
    print(f"D_Q (weak lepton closure, max col) = {D_Q:.3e}   [<= 1e-12 required]")
    print(f"charge leak, strong cols (max)     = {D_Q_strong:.3e}   [<= 1e-12 required]")
    print(f"dYe through weak cols (rand flux)  = {dYe_weak:.6e}   [must be NONZERO]")
    cond_nu = np.linalg.cond(nu)
    print(f"cond(nu) full                      = {cond_nu:.3e}"
          "   [active-set cond > 1e6 => Target-B switch trigger]")

    ok = (D_A <= 1e-12 and D_Q <= 1e-12 and D_Q_strong <= 1e-12
          and (not weak.any() or dYe_weak != 0.0))
    print("VERDICT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
