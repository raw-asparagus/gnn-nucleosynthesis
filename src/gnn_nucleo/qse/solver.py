"""Independent NSE and QSE solvers (log-space damped Newton + bisection fallback).

NSE: 2 unknowns u = (u_p, u_n) [MeV] under ΣX = 1 and ΣZX/A = Yₑ.
QSE: +1 unknown u_G — the group chemical-potential offset for a silicon-group
membership set G anchored on ²⁸Si (Hix & Thielemann 1996 Eqs. 2–7 structure):
group members satisfy μ_i = Z_i μ_p + N_i μ_n + u_G (u_G = μ_G^offset shared
by the cluster; u_G = 0 recovers NSE), non-members are in NSE with the free
nucleons. Third constraint: the group mass fraction Σ_{i∈G} X_i equals the
measured value from the actual composition.

Robustness: analytic-Jacobian Newton in u with step damping (‖δu‖ ≤ 2 MeV),
exponent clipped at EXP_CLIP like pynucastro; on failure, a nested bisection
fallback exploiting monotonicity (ΣX strictly increasing in u_n at fixed u_p;
Yₑ of the solution increasing in u_p).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .coeffs import EXP_CLIP, NseInputs, nse_log_coeffs

__all__ = ["NSEResult", "QSEResult", "solve_nse", "solve_qse"]

_MAX_STEP_MEV = 2.0
_MAX_ITER = 200


@dataclass(frozen=True)
class NSEResult:
    X: np.ndarray  # (n,) mass fractions
    u_p: float
    u_n: float
    converged: bool
    n_iter: int
    method: str  # "newton" | "bisection"
    residual: float


@dataclass(frozen=True)
class QSEResult:
    X: np.ndarray
    u_p: float
    u_n: float
    u_group: float
    converged: bool
    n_iter: int
    method: str
    residual: float


def _mass_fractions(logC, Z, N, u_p, u_n, kT, group=None, u_g=0.0):
    expo = logC + (Z * u_p + N * u_n) / kT
    if group is not None:
        expo = expo + np.where(group, u_g / kT, 0.0)
    return np.exp(np.minimum(expo, EXP_CLIP))


def solve_nse(
    inputs: NseInputs,
    T: float,
    rho: float,
    ye: float,
    init: tuple[float, float] = (-3.5, -15.0),
    tol: float = 1.0e-11,
) -> NSEResult:
    """Solve NSE for (u_p, u_n) and return the composition."""
    from pynucastro.constants import constants

    kT = constants.k_MeV * T
    logC = nse_log_coeffs(inputs, T, rho)
    Z, N, A = inputs.Z, inputs.N, inputs.A

    def residuals(u_p, u_n):
        X = _mass_fractions(logC, Z, N, u_p, u_n, kT)
        return np.array([X.sum() - 1.0, ((Z / A) * X).sum() - ye]), X

    # --- damped Newton ------------------------------------------------------
    u_p, u_n = init
    for it in range(_MAX_ITER):
        F, X = residuals(u_p, u_n)
        r = np.abs(F).max()
        if r < tol:
            return NSEResult(X, u_p, u_n, True, it, "newton", r)
        # dX/du_p = X·Z/kT ; dX/du_n = X·N/kT
        J = (
            np.array(
                [
                    [(X * Z).sum(), (X * N).sum()],
                    [(X * Z * Z / A).sum(), (X * Z * N / A).sum()],
                ]
            )
            / kT
        )
        try:
            step = np.linalg.solve(J, -F)
        except np.linalg.LinAlgError:
            break
        norm = np.abs(step).max()
        if norm > _MAX_STEP_MEV:
            step *= _MAX_STEP_MEV / norm
        u_p, u_n = u_p + step[0], u_n + step[1]
        if not (np.isfinite(u_p) and np.isfinite(u_n)):
            break

    # --- bisection fallback -------------------------------------------------
    def u_n_for_mass(u_p, lo=-60.0, hi=10.0):
        """ΣX(u_n) = 1 is monotone increasing in u_n at fixed u_p."""
        for _ in range(200):
            mid = 0.5 * (lo + hi)
            X = _mass_fractions(logC, Z, N, u_p, mid, kT)
            if X.sum() > 1.0:
                hi = mid
            else:
                lo = mid
            if hi - lo < 1e-14 * max(1.0, abs(mid)):
                break
        return 0.5 * (lo + hi)

    lo_p, hi_p = -60.0, 10.0
    for it in range(300):
        u_p = 0.5 * (lo_p + hi_p)
        u_n = u_n_for_mass(u_p)
        F, X = residuals(u_p, u_n)
        if abs(F[0]) < 1e-9 and abs(F[1]) < tol:
            return NSEResult(X, u_p, u_n, True, it, "bisection", np.abs(F).max())
        if F[1] > 0:  # Ye too high → lower u_p
            hi_p = u_p
        else:
            lo_p = u_p
    F, X = residuals(u_p, u_n)
    return NSEResult(X, u_p, u_n, False, _MAX_ITER + 300, "bisection", np.abs(F).max())


def solve_qse(
    inputs: NseInputs,
    T: float,
    rho: float,
    ye: float,
    group: np.ndarray,
    group_mass: float,
    init: tuple[float, float, float] | None = None,
    tol: float = 1.0e-11,
) -> QSEResult:
    """Solve QSE with a silicon-group cluster (see module docstring).

    Parameters
    ----------
    group : (n,) bool — cluster membership (must include ²⁸Si for the
        canonical anchor; the solver itself only needs the mask)
    group_mass : Σ_{i∈G} X_i measured from the actual composition
    """
    from pynucastro.constants import constants

    kT = constants.k_MeV * T
    logC = nse_log_coeffs(inputs, T, rho)
    Z, N, A = inputs.Z, inputs.N, inputs.A
    g = np.asarray(group, dtype=bool)
    if not 0.0 < group_mass < 1.0:
        raise ValueError(f"group_mass {group_mass} outside (0, 1)")

    if init is None:
        nse = solve_nse(inputs, T, rho, ye)
        init = (nse.u_p, nse.u_n, 0.0)

    def residuals(u_p, u_n, u_g):
        X = _mass_fractions(logC, Z, N, u_p, u_n, kT, group=g, u_g=u_g)
        return (
            np.array(
                [
                    X.sum() - 1.0,
                    ((Z / A) * X).sum() - ye,
                    X[g].sum() - group_mass,
                ]
            ),
            X,
        )

    u_p, u_n, u_g = init
    for it in range(_MAX_ITER):
        F, X = residuals(u_p, u_n, u_g)
        r = np.abs(F).max()
        if r < tol:
            return QSEResult(X, u_p, u_n, u_g, True, it, "newton", r)
        dg = g.astype(np.float64)
        J = (
            np.array(
                [
                    [(X * Z).sum(), (X * N).sum(), (X * dg).sum()],
                    [
                        (X * Z * Z / A).sum(),
                        (X * Z * N / A).sum(),
                        (X * Z * dg / A).sum(),
                    ],
                    [(X * Z * dg).sum(), (X * N * dg).sum(), (X * dg).sum()],
                ]
            )
            / kT
        )
        try:
            step = np.linalg.solve(J, -F)
        except np.linalg.LinAlgError:
            break
        norm = np.abs(step).max()
        if norm > _MAX_STEP_MEV:
            step *= _MAX_STEP_MEV / norm
        u_p, u_n, u_g = u_p + step[0], u_n + step[1], u_g + step[2]
        if not np.all(np.isfinite([u_p, u_n, u_g])):
            break

    # fallback: outer bisection on u_g; inner NSE-style solve at fixed u_g
    def inner(u_g, lo_p=-60.0, hi_p=10.0):
        for _ in range(200):
            u_p = 0.5 * (lo_p + hi_p)
            lo_n, hi_n = -60.0, 10.0
            for _ in range(200):
                u_n = 0.5 * (lo_n + hi_n)
                X = _mass_fractions(logC, Z, N, u_p, u_n, kT, group=g, u_g=u_g)
                if X.sum() > 1.0:
                    hi_n = u_n
                else:
                    lo_n = u_n
                if hi_n - lo_n < 1e-14 * max(1.0, abs(u_n)):
                    break
            F, X = residuals(u_p, u_n, u_g)
            if abs(F[1]) < tol:
                break
            if F[1] > 0:
                hi_p = u_p
            else:
                lo_p = u_p
        return u_p, u_n, F, X

    lo_g, hi_g = -30.0, 30.0
    for it in range(200):
        u_g = 0.5 * (lo_g + hi_g)
        u_p, u_n, F, X = inner(u_g)
        if np.abs(F).max() < max(tol, 1e-9):
            return QSEResult(X, u_p, u_n, u_g, True, it, "bisection", np.abs(F).max())
        if F[2] > 0:  # too much group mass → lower u_g
            hi_g = u_g
        else:
            lo_g = u_g
    return QSEResult(
        X, u_p, u_n, u_g, False, _MAX_ITER + 200, "bisection", np.abs(F).max()
    )
