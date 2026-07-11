"""Stiff reference integrator over the reconciled network (Step 6 Task 3).

Produces Target-A supervision pairs from arbitrary initial states over
arbitrary dt: per-reaction cumulative GROSS fluxes Φⱼ = ∫Rⱼ dt (augmented
ODE state) together with the composition update, integrating

    dY/dt = ν R(Y; T, ρ),      dΦ/dt = R(Y; T, ρ)

with scipy BDF (Radau available for cross-checks) at constant (T, ρ). The
gross per-column convention matches the flux engine (ydot = νR exactly;
net φ/κ recovered downstream via pair_col as in store.py), so ΔY = νΔΦ is
an identity of the dynamics — and the RETURNED composition is defined as
Y0 + ν(Φ − Φ0): the identity and baryon/charge conservation hold BY
CONSTRUCTION (Cν = 0), while the solver's error-controlled Y is exposed as
a consistency diagnostic (``identity_resid``).

Rates: the exact arithmetic of ``engine.evaluate_lambda`` /
``evaluate_fluxes`` with the Y-independent parts hoisted per (T, ρ)
(``StatePoint``): ReacLib set sums + pf corrections are cached; screening
(chugunov_2007, Y-dependent through the plasma state), tabular-weak ρYₑ
inputs, and the reactant product are re-evaluated per RHS call. Y is
clipped at 0 inside rate evaluation (transient small negatives from the
linear multistep are not propagated into powers).

Jacobian (ADR 0006): analytic dominant term D = ∂R/∂Y from the reactant
product rule (exact, no division — slot products with the differentiated
factor removed), assembled sparse as [[νD, 0], [D, 0]]. The ∂λ/∂Y chain
through screening and the Yₑ-weighting/tabular inputs is deliberately
neglected — an approximate Jacobian only affects BDF step efficiency, not
correctness (measured: the neglected chain is ≲1% of entries;
tests/test_integrate.py).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import scipy.sparse as sp
from scipy.integrate import solve_ivp

from .compile import CompiledNetwork
from .engine import _bilinear_vec
from .screening import chugunov_2007_vec, plasma_arrays

__all__ = ["StatePoint", "IntegrationResult", "integrate_state"]


class StatePoint:
    """Y-independent rate machinery hoisted for one (T, ρ) point."""

    def __init__(self, cn: CompiledNetwork, T: float, rho: float):
        self.cn = cn
        self.T = float(T)
        self.rho = float(rho)
        n_rxn = cn.n_reactions

        T9 = self.T / 1.0e9
        Tpow = np.array(
            [
                1.0,
                1.0 / T9,
                (1.0 / T9) ** (1.0 / 3.0),
                T9 ** (1.0 / 3.0),
                T9,
                T9 ** (5.0 / 3.0),
                np.log(T9),
            ]
        )
        lam = np.zeros(n_rxn, dtype=np.float64)
        if cn.coeffs.size:
            log_sets = cn.coeffs @ Tpow
            lam[cn.owned_cols] = np.add.reduceat(np.exp(log_sets), cn.set_starts)
            if cn.pf_matrix.nnz:
                log_pf = np.array([spl(T9) for spl in cn.pf_splines])
                lam *= np.exp(cn.pf_matrix @ log_pf)
        #: reaclib/derived λ at (T, ρ), pf-corrected, UNSCREENED; tabular
        #: columns filled per call
        self.lam_base = lam
        self.prefac_rho = cn.prefactor * self.rho ** cn.dens_exp
        self._T_arr = np.array([self.T])
        self._rho_arr = np.array([self.rho])
        self._logT10 = np.log10(self.T)
        self._Z = cn.stoich.Z.astype(np.float64)
        self._A = cn.stoich.A.astype(np.float64)
        self._nu_csr = sp.csr_matrix(cn.stoich.nu)
        self._n_s = cn.stoich.n_species

    def _lam(self, Yc: np.ndarray) -> np.ndarray:
        cn = self.cn
        lam = self.lam_base.copy()
        if cn.screening is not None and cn.screen_map.nnz:
            n_e, gamma_e_fac = plasma_arrays(self._rho_arr, Yc[:, None], cn.stoich.Z)
            log_scor = chugunov_2007_vec(
                self._T_arr,
                n_e,
                gamma_e_fac,
                cn.screen_pairs[:, 0],
                cn.screen_pairs[:, 1],
                cn.screen_pairs[:, 2],
                cn.screen_pairs[:, 3],
            )
            lam *= np.exp(cn.screen_map @ log_scor)[:, 0]
        if len(cn.tab_cols):
            ye = float(self._Z @ Yc) / float(self._A @ Yc)
            logrhoy = np.array([np.log10(self.rho * ye)])
            logT = np.array([self._logT10])
            for i, col in enumerate(cn.tab_cols):
                r = _bilinear_vec(
                    cn.tab_rhoy[i], cn.tab_temp[i], cn.tab_rate2d[i], logrhoy, logT
                )
                lam[col] = 10.0 ** r[0]
        return lam

    def _base_and_pad(self, Y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """(R without the reactant product, Ypad) at clipped Y."""
        cn = self.cn
        Yc = np.maximum(np.asarray(Y, dtype=np.float64), 0.0)
        base = self._lam(Yc) * self.prefac_rho
        if cn.ye_weighted.any():
            ye = float(self._Z @ Yc) / float(self._A @ Yc)
            base = base.copy()
            base[cn.ye_weighted] *= ye
        Ypad = np.append(Yc, 1.0)
        return base, Ypad

    def gross_rates(self, Y: np.ndarray) -> np.ndarray:
        """Per-column gross rates R (engine f⁺ arithmetic, one state)."""
        cn = self.cn
        R, Ypad = self._base_and_pad(Y)
        for k in range(cn.reactant_idx.shape[1]):
            R = R * Ypad[cn.reactant_idx[:, k]]
        return R

    def rate_jacobian(self, Y: np.ndarray) -> sp.csr_matrix:
        """D = ∂R/∂Y, dominant (reactant-product) term, sparse
        (n_rxn × n_species). Repeated reactants are handled by the slot sum
        (product rule)."""
        cn = self.cn
        base, Ypad = self._base_and_pad(Y)
        K = cn.reactant_idx.shape[1]
        rows: list[np.ndarray] = []
        cols: list[np.ndarray] = []
        data: list[np.ndarray] = []
        for k in range(K):
            pe = base.copy()
            for k2 in range(K):
                if k2 != k:
                    pe *= Ypad[cn.reactant_idx[:, k2]]
            idx = cn.reactant_idx[:, k]
            valid = idx < self._n_s
            j = np.nonzero(valid)[0]
            rows.append(j)
            cols.append(idx[valid])
            data.append(pe[valid])
        D = sp.coo_matrix(
            (np.concatenate(data), (np.concatenate(rows), np.concatenate(cols))),
            shape=(cn.n_reactions, self._n_s),
        )
        return D.tocsr()


@dataclass(frozen=True)
class IntegrationResult:
    """Result of one constant-(T, ρ) integration.

    ``Y`` is Y0 + ν(Φ − Φ0) — conservation-exact by construction. With
    ``t_eval`` the arrays gain a leading time axis. ``identity_resid`` is
    max |Y_solver − Y| over the final state (molar), the solver-vs-identity
    consistency diagnostic.
    """

    Y: np.ndarray
    Phi: np.ndarray
    Y_solver: np.ndarray
    identity_resid: float
    success: bool
    message: str
    nfev: int
    njev: int
    t: np.ndarray | None = None


def integrate_state(
    cn: CompiledNetwork,
    T: float,
    rho: float,
    Y0: np.ndarray,
    dt: float,
    *,
    t_eval: np.ndarray | None = None,
    method: str = "BDF",
    rtol: float = 1e-8,
    atol_y: float = 1e-18,
    atol_phi: float = 1e-18,
    max_step: float = np.inf,
) -> IntegrationResult:
    """Integrate one state over [0, dt] at constant (T, ρ).

    Parameters
    ----------
    Y0 : (n_species,) molar fractions.
    t_eval : optional snapshot times within (0, dt] (e.g. the nine label
        dts) — one integration serves them all.

    Returns
    -------
    IntegrationResult with Φ (cumulative gross per-column fluxes) and the
    conservation-exact composition Y0 + νΦ.
    """
    spoint = StatePoint(cn, T, rho)
    n_s = cn.stoich.n_species
    n_rxn = cn.n_reactions
    nu = spoint._nu_csr
    zeros_sr = sp.csr_matrix((n_s, n_rxn))
    zeros_rr = sp.csr_matrix((n_rxn, n_rxn))

    def rhs(_t: float, u: np.ndarray) -> np.ndarray:
        R = spoint.gross_rates(u[:n_s])
        return np.concatenate([nu @ R, R])

    def jac(_t: float, u: np.ndarray):
        D = spoint.rate_jacobian(u[:n_s])
        return sp.bmat([[nu @ D, zeros_sr], [D, zeros_rr]], format="csc")

    u0 = np.concatenate([np.asarray(Y0, dtype=np.float64), np.zeros(n_rxn)])
    atol = np.concatenate([np.full(n_s, atol_y), np.full(n_rxn, atol_phi)])
    te = None
    if t_eval is not None:
        te = np.sort(np.asarray(t_eval, dtype=np.float64))
        if te[-1] > dt:
            raise ValueError("t_eval beyond dt")
    sol = solve_ivp(
        rhs,
        (0.0, float(dt)),
        u0,
        method=method,
        jac=jac,
        rtol=rtol,
        atol=atol,
        t_eval=te,
        max_step=max_step,
    )
    Y0 = np.asarray(Y0, dtype=np.float64)
    if te is None:
        Phi = sol.y[n_s:, -1]
        Y_solver = sol.y[:n_s, -1]
        Y = Y0 + cn.stoich.nu @ Phi
        resid = float(np.abs(Y_solver - Y).max())
    else:
        Phi = sol.y[n_s:, :].T  # (n_t, n_rxn)
        Y_solver = sol.y[:n_s, :].T
        Y = Y0[None, :] + Phi @ cn.stoich.nu.T
        resid = float(np.abs(Y_solver[-1] - Y[-1]).max()) if len(Phi) else np.nan
    return IntegrationResult(
        Y=Y,
        Phi=Phi,
        Y_solver=Y_solver,
        identity_resid=resid,
        success=bool(sol.success),
        message=str(sol.message),
        nfev=int(sol.nfev),
        njev=int(sol.njev),
        t=te,
    )
