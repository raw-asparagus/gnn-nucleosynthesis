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

from .coeffs import EXP_CLIP, NseInputs, nse_log_coeffs, nse_log_coeffs_batch

__all__ = [
    "NSEResult",
    "QSEResult",
    "NSEBatchResult",
    "QSEBatchResult",
    "solve_nse",
    "solve_qse",
    "solve_nse_batch",
    "solve_qse_batch",
]

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


# ---------------------------------------------------------------------------
# Batched solvers
#
# The Newton kernels above are already vectorized over the species axis; the
# only per-state scalars are (T, ρ, Yₑ, group_mass) and the unknowns u. The
# batched entry points stack those to a leading state axis and run one
# vectorized damped-Newton loop over ALL states at once (per-row convergence
# masking + per-row damping), then hand any state that fails to converge in the
# Newton phase to the proven SCALAR solver (which retries Newton and applies its
# bisection fallback) — so the result is identical to a per-state loop while the
# hot, well-conditioned majority is computed in a handful of array ops. Same
# constants (EXP_CLIP, _MAX_STEP_MEV, _MAX_ITER), same float64, same tol.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class NSEBatchResult:
    """Stacked :class:`NSEResult` over M states (see solve_nse_batch)."""

    X: np.ndarray  # (M, n) mass fractions
    u_p: np.ndarray  # (M,)
    u_n: np.ndarray  # (M,)
    converged: np.ndarray  # (M,) bool
    n_iter: np.ndarray  # (M,) int
    method: np.ndarray  # (M,) object ("newton" | "bisection")
    residual: np.ndarray  # (M,)

    def __len__(self) -> int:
        return self.X.shape[0]

    def row(self, i: int) -> NSEResult:
        """The i-th state as a scalar :class:`NSEResult` (drop-in for callers
        that consume per-row ``.converged`` / ``.X``)."""
        return NSEResult(
            self.X[i],
            float(self.u_p[i]),
            float(self.u_n[i]),
            bool(self.converged[i]),
            int(self.n_iter[i]),
            str(self.method[i]),
            float(self.residual[i]),
        )


@dataclass(frozen=True)
class QSEBatchResult:
    """Stacked :class:`QSEResult` over M states (see solve_qse_batch)."""

    X: np.ndarray
    u_p: np.ndarray
    u_n: np.ndarray
    u_group: np.ndarray
    converged: np.ndarray
    n_iter: np.ndarray
    method: np.ndarray
    residual: np.ndarray

    def __len__(self) -> int:
        return self.X.shape[0]

    def row(self, i: int) -> QSEResult:
        return QSEResult(
            self.X[i],
            float(self.u_p[i]),
            float(self.u_n[i]),
            float(self.u_group[i]),
            bool(self.converged[i]),
            int(self.n_iter[i]),
            str(self.method[i]),
            float(self.residual[i]),
        )


def _mass_fractions_batch(logC, Z, N, u_p, u_n, kT, group=None, u_g=None):
    """Vectorized :func:`_mass_fractions`: logC (M, n); Z, N (n,);
    u_p, u_n, kT (M,) → X (M, n). ``group`` (n,) bool + ``u_g`` (M,) add the
    silicon-cluster offset (QSE)."""
    num = Z[None, :] * u_p[:, None] + N[None, :] * u_n[:, None]
    if group is not None:
        num = num + group[None, :].astype(np.float64) * u_g[:, None]
    expo = logC + num / kT[:, None]
    return np.exp(np.minimum(expo, EXP_CLIP))


def _batched_2x2_step(a, b, c, d, F0, F1):
    """Per-row Cramer solve of J·δ = −F for 2×2 J = [[a, b], [c, d]].

    Closed form (never raises — a batched ``np.linalg.solve`` aborts the whole
    batch if any single row is LAPACK-singular). Rows with a singular or
    non-finite solve are flagged; the caller drops them to the scalar fallback.
    """
    det = a * d - b * c
    with np.errstate(divide="ignore", invalid="ignore"):
        d0 = (-d * F0 + b * F1) / det
        d1 = (c * F0 - a * F1) / det
    singular = ~np.isfinite(d0) | ~np.isfinite(d1) | (np.abs(det) < 1e-300)
    d0 = np.where(singular, 0.0, d0)
    d1 = np.where(singular, 0.0, d1)
    return d0, d1, singular


def _batched_3x3_step(J, F):
    """Per-row closed-form solve of J·δ = −F for 3×3 J (adjugate / det, never
    raises). ``J`` is (M, 3, 3), ``F`` is (M, 3). Returns (step (M, 3),
    singular_mask (M,))."""
    a, b, c = J[:, 0, 0], J[:, 0, 1], J[:, 0, 2]
    d, e, f = J[:, 1, 0], J[:, 1, 1], J[:, 1, 2]
    g, h, i = J[:, 2, 0], J[:, 2, 1], J[:, 2, 2]
    A = e * i - f * h
    B = -(d * i - f * g)
    C = d * h - e * g
    det = a * A + b * B + c * C
    # inverse = adjugate / det (adjugate = transpose of the cofactor matrix)
    inv = np.stack(
        [
            np.stack([A, -(b * i - c * h), b * f - c * e], axis=1),
            np.stack([B, a * i - c * g, -(a * f - c * d)], axis=1),
            np.stack([C, -(a * h - b * g), a * e - b * d], axis=1),
        ],
        axis=1,
    )  # (M, 3, 3)
    with np.errstate(divide="ignore", invalid="ignore"):
        step = (inv @ (-F)[:, :, None])[:, :, 0] / det[:, None]
    singular = ~np.isfinite(step).all(axis=1) | (np.abs(det) < 1e-300)
    step = np.where(singular[:, None], 0.0, step)
    return step, singular


def solve_nse_batch(
    inputs: NseInputs,
    T: np.ndarray,
    rho: np.ndarray,
    ye: np.ndarray,
    init: tuple[float, float] = (-3.5, -15.0),
    tol: float = 1.0e-11,
) -> NSEBatchResult:
    """Solve NSE for a batch of states. ``T, rho, ye`` are ``(M,)`` [K, g/cm³,
    dimensionless]; returns a :class:`NSEBatchResult` (row order preserved).

    Vectorized damped Newton over all states; any state not converged in the
    Newton phase is delegated to the scalar :func:`solve_nse` (Newton retry +
    bisection fallback), so the output matches a per-state loop.
    """
    from pynucastro.constants import constants

    T = np.asarray(T, dtype=np.float64).ravel()
    rho = np.asarray(rho, dtype=np.float64).ravel()
    ye = np.asarray(ye, dtype=np.float64).ravel()
    M, n = T.shape[0], inputs.n
    kT = constants.k_MeV * T
    logC = nse_log_coeffs_batch(inputs, T, rho)
    Z, N, A = inputs.Z, inputs.N, inputs.A
    ZA = Z / A

    u_p = np.full(M, float(init[0]))
    u_n = np.full(M, float(init[1]))
    Xout = np.zeros((M, n), dtype=np.float64)
    converged = np.zeros(M, dtype=bool)
    n_iter = np.zeros(M, dtype=int)
    method = np.empty(M, dtype=object)
    residual = np.full(M, np.inf)
    active = np.ones(M, dtype=bool)

    for it in range(_MAX_ITER):
        X = _mass_fractions_batch(logC, Z, N, u_p, u_n, kT)
        F0 = X.sum(1) - 1.0
        F1 = (ZA[None, :] * X).sum(1) - ye
        r = np.maximum(np.abs(F0), np.abs(F1))
        newly = active & (r < tol)
        if newly.any():
            converged[newly] = True
            n_iter[newly] = it
            method[newly] = "newton"
            residual[newly] = r[newly]
            Xout[newly] = X[newly]
            active[newly] = False
        if not active.any():
            break
        J00 = (X * Z).sum(1)
        J01 = (X * N).sum(1)
        J10 = (X * Z * Z / A).sum(1)
        J11 = (X * Z * N / A).sum(1)
        d0, d1, singular = _batched_2x2_step(
            J00 / kT, J01 / kT, J10 / kT, J11 / kT, F0, F1
        )
        norm = np.maximum(np.abs(d0), np.abs(d1))
        scale = np.where(
            norm > _MAX_STEP_MEV, _MAX_STEP_MEV / np.where(norm > 0, norm, 1.0), 1.0
        )
        upd = active & ~singular
        u_p = np.where(upd, u_p + d0 * scale, u_p)
        u_n = np.where(upd, u_n + d1 * scale, u_n)
        bad = ~np.isfinite(u_p) | ~np.isfinite(u_n)
        active &= ~singular & ~bad

    for i in np.nonzero(~converged)[0]:
        res = solve_nse(
            inputs, float(T[i]), float(rho[i]), float(ye[i]), init=init, tol=tol
        )
        Xout[i] = res.X
        u_p[i] = res.u_p
        u_n[i] = res.u_n
        converged[i] = res.converged
        n_iter[i] = res.n_iter
        method[i] = res.method
        residual[i] = res.residual

    return NSEBatchResult(Xout, u_p, u_n, converged, n_iter, method, residual)


def solve_qse_batch(
    inputs: NseInputs,
    T: np.ndarray,
    rho: np.ndarray,
    ye: np.ndarray,
    group: np.ndarray,
    group_mass: np.ndarray,
    init: tuple[float, float, float] | None = None,
    tol: float = 1.0e-11,
) -> QSEBatchResult:
    """Solve QSE for a batch of states (silicon-group cluster; see
    :func:`solve_qse`). ``T, rho, ye, group_mass`` are ``(M,)``; ``group`` is
    the shared ``(n,)`` bool mask. Non-converged rows fall back to the scalar
    :func:`solve_qse`."""
    from pynucastro.constants import constants

    T = np.asarray(T, dtype=np.float64).ravel()
    rho = np.asarray(rho, dtype=np.float64).ravel()
    ye = np.asarray(ye, dtype=np.float64).ravel()
    group_mass = np.asarray(group_mass, dtype=np.float64).ravel()
    M, n = T.shape[0], inputs.n
    if np.any((group_mass <= 0.0) | (group_mass >= 1.0)):
        raise ValueError("group_mass outside (0, 1) for at least one state")
    kT = constants.k_MeV * T
    logC = nse_log_coeffs_batch(inputs, T, rho)
    Z, N, A = inputs.Z, inputs.N, inputs.A
    ZA = Z / A
    g = np.asarray(group, dtype=bool)
    dg = g.astype(np.float64)

    if init is None:
        seed = solve_nse_batch(inputs, T, rho, ye, tol=tol)
        u_p, u_n = seed.u_p.copy(), seed.u_n.copy()
        u_g = np.zeros(M)
    else:
        u_p = np.full(M, float(init[0]))
        u_n = np.full(M, float(init[1]))
        u_g = np.full(M, float(init[2]))

    Xout = np.zeros((M, n), dtype=np.float64)
    converged = np.zeros(M, dtype=bool)
    n_iter = np.zeros(M, dtype=int)
    method = np.empty(M, dtype=object)
    residual = np.full(M, np.inf)
    active = np.ones(M, dtype=bool)

    for it in range(_MAX_ITER):
        X = _mass_fractions_batch(logC, Z, N, u_p, u_n, kT, group=g, u_g=u_g)
        F0 = X.sum(1) - 1.0
        F1 = (ZA[None, :] * X).sum(1) - ye
        F2 = X[:, g].sum(1) - group_mass
        r = np.maximum(np.maximum(np.abs(F0), np.abs(F1)), np.abs(F2))
        newly = active & (r < tol)
        if newly.any():
            converged[newly] = True
            n_iter[newly] = it
            method[newly] = "newton"
            residual[newly] = r[newly]
            Xout[newly] = X[newly]
            active[newly] = False
        if not active.any():
            break
        # 3×3 Jacobian per row (mirrors scalar solve_qse), all entries / kT
        XZ, XN, Xdg = X * Z, X * N, X * dg
        J = np.empty((M, 3, 3))
        J[:, 0, 0] = XZ.sum(1)
        J[:, 0, 1] = XN.sum(1)
        J[:, 0, 2] = Xdg.sum(1)
        J[:, 1, 0] = (XZ * Z / A).sum(1)
        J[:, 1, 1] = (XZ * N / A).sum(1)
        J[:, 1, 2] = (XZ * dg / A).sum(1)
        J[:, 2, 0] = (XZ * dg).sum(1)
        J[:, 2, 1] = (XN * dg).sum(1)
        J[:, 2, 2] = Xdg.sum(1)
        J /= kT[:, None, None]
        F = np.stack([F0, F1, F2], axis=1)  # (M, 3)
        step, singular = _batched_3x3_step(J, F)
        norm = np.abs(step).max(1)
        scale = np.where(
            norm > _MAX_STEP_MEV, _MAX_STEP_MEV / np.where(norm > 0, norm, 1.0), 1.0
        )
        step = step * scale[:, None]
        upd = active & ~singular
        u_p = np.where(upd, u_p + step[:, 0], u_p)
        u_n = np.where(upd, u_n + step[:, 1], u_n)
        u_g = np.where(upd, u_g + step[:, 2], u_g)
        bad = ~np.isfinite(u_p) | ~np.isfinite(u_n) | ~np.isfinite(u_g)
        active &= ~singular & ~bad

    for i in np.nonzero(~converged)[0]:
        res = solve_qse(
            inputs,
            float(T[i]),
            float(rho[i]),
            float(ye[i]),
            g,
            float(group_mass[i]),
            init=init,
            tol=tol,
        )
        Xout[i] = res.X
        u_p[i] = res.u_p
        u_n[i] = res.u_n
        u_g[i] = res.u_group
        converged[i] = res.converged
        n_iter[i] = res.n_iter
        method[i] = res.method
        residual[i] = res.residual

    return QSEBatchResult(
        Xout, u_p, u_n, u_g, converged, n_iter, method, residual
    )
